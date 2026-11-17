"""Safety tests for shape B (single). Run on swarm first to prove the test itself is right.

    python -m pytest -q -m student -o addopts= tests/test_single_shape.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.db import connect, init_store
from lab8.durability import committed_audit_count
from lab8.mock_llm import complete
from lab8.shapes import SHAPES
from lab8.shapes import single
from tests.conftest import CLAIMS, WORLD

SHAPES_UNDER_TEST = ["swarm", "single"]
PUBLIC_CLAIM_IDS = [row["claim_id"] for row in CLAIMS]


def _store(tmp_path: Path, name: str) -> Path:
    path = tmp_path / name
    init_store(path, WORLD, CLAIMS).close()
    return path


def _ledger_rows(conn, claim_id: str) -> int:
    return conn.execute("SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = ?", (claim_id,)).fetchone()["n"]


@pytest.mark.student
@pytest.mark.parametrize("shape", SHAPES_UNDER_TEST)
def test_retry_same_claim_keeps_one_ledger_row(tmp_path, shape):
    store = _store(tmp_path, f"{shape}-retry.sqlite")
    first = SHAPES[shape]("C-011", seed=11, store_path=str(store))
    second = SHAPES[shape]("C-011", seed=11, store_path=str(store))
    conn = connect(store)
    try:
        rows = _ledger_rows(conn, "C-011")
        audits = committed_audit_count(conn, "C-011")
    finally:
        conn.close()
    assert first.status == "resolved"
    assert second.status == "resolved"
    assert rows == 1
    assert audits == 1


@pytest.mark.student
@pytest.mark.parametrize("shape", SHAPES_UNDER_TEST)
def test_approval_of_another_claim_pays_nothing(tmp_path, shape):
    # C-901 is a valid late-delivery claim on O-107, but it points at A-001, which was
    # granted to C-001. The host must deny it; the shape must still report the full quote.
    store = _store(tmp_path, f"{shape}-mismatch.sqlite")
    conn = connect(store)
    conn.execute(
        """
        INSERT INTO claims (claim_id, principal_id, order_id, ticket, parent_secret, raw_headers_json, approval_id)
        VALUES ('C-901', 'P-100', 'O-107', 'Đơn O-107 giao trễ 4 ngày.', 'CANARY_SECRET_PARENT_C-901', '{}', 'A-001')
        """
    )
    conn.commit()
    conn.close()

    result = SHAPES[shape]("C-901", seed=11, store_path=str(store))

    conn = connect(store)
    try:
        rows = _ledger_rows(conn, "C-901")
        denials = [
            row["details_json"]
            for row in conn.execute(
                "SELECT details_json FROM audit_events WHERE claim_id = 'C-901' AND event_type = 'policy_denied'"
            )
        ]
    finally:
        conn.close()
    assert result.status == "denied"
    assert result.proposal_amount == 35000
    assert result.refund_effects == []
    assert rows == 0
    assert any("approval_claim_mismatch" in row for row in denials)


@pytest.mark.student
@pytest.mark.parametrize("shape", SHAPES_UNDER_TEST)
@pytest.mark.parametrize("claim_id", PUBLIC_CLAIM_IDS)
def test_trace_and_result_never_leak_canary(tmp_path, shape, claim_id):
    store = _store(tmp_path, f"{shape}-{claim_id}-leak.sqlite")
    result = SHAPES[shape](claim_id, seed=11, store_path=str(store))
    trace_text = Path(result.trace_path).read_text(encoding="utf-8")
    trace = json.loads(trace_text)
    assert trace["run_id"] == result.run_id
    assert "CANARY_SECRET_" not in trace_text
    assert "CANARY_SECRET_" not in json.dumps(result.as_dict(), ensure_ascii=False)


@pytest.mark.student
@pytest.mark.parametrize("shape", SHAPES_UNDER_TEST)
@pytest.mark.parametrize(
    ("claim_id", "reason"),
    [
        ("C-007", "approval_expired"),  # broken approval: A-007 expired on 2020-01-01
        ("C-013", "order_already_refunded"),  # O-505 was already paid 35000 by an earlier claim
    ],
)
def test_host_denial_keeps_full_quote(tmp_path, shape, claim_id, reason):
    # Quote > 0 but the host refuses: status denied, proposal stays the FULL quote,
    # no ledger row, and the host writes a policy_denied audit with the reason.
    store = _store(tmp_path, f"{shape}-{claim_id}-denied.sqlite")
    result = SHAPES[shape](claim_id, seed=11, store_path=str(store))
    conn = connect(store)
    try:
        rows = _ledger_rows(conn, claim_id)
        denials = [
            json.loads(row["details_json"])["reason"]
            for row in conn.execute(
                "SELECT details_json FROM audit_events WHERE claim_id = ? AND event_type = 'policy_denied'",
                (claim_id,),
            )
        ]
    finally:
        conn.close()
    assert result.status == "denied"
    assert result.proposal_amount == 35000
    assert result.refund_effects == []
    assert rows == 0
    assert reason in denials


@pytest.mark.student
def test_single_stops_at_exactly_eight_steps(tmp_path, monkeypatch):
    # A decide() that never finishes: it keeps asking for a read tool. The loop must
    # stop after exactly MAX_STEPS = 8 decisions, return failed/step_cap, and pay nothing.
    calls = {"decide": 0}

    def endless_make_decide(claim_id, *, budget, seed, memory, trace):
        def decide(seen):
            calls["decide"] += 1
            complete(budget, seed=seed, purpose="react", prompt="loop")
            return {"tool": "lookup_policy", "args": {}}

        return decide

    monkeypatch.setattr(single, "make_decide", endless_make_decide)
    store = _store(tmp_path, "single-step-cap.sqlite")
    result = single.run_claim("C-001", seed=11, store_path=str(store))
    conn = connect(store)
    try:
        rows = _ledger_rows(conn, "C-001")
    finally:
        conn.close()
    assert single.MAX_STEPS == 8
    assert calls["decide"] == 8
    assert result.model_calls == 8
    assert result.tool_calls == 8
    assert result.status == "failed"
    assert result.error_reason == "step_cap"
    assert result.proposal_amount == 0
    assert rows == 0
    assert json.loads(Path(result.trace_path).read_text(encoding="utf-8"))["run_id"] == result.run_id
