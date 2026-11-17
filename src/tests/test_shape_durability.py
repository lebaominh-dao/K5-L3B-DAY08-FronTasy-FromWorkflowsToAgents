"""Shape-level checks for refund durability and security boundaries."""

import json
from contextlib import closing

import pytest

from lab8.app import run_shape
from lab8.db import connect
from lab8.durability import InjectedCrash, committed_audit_count
from lab8.metrics import artifact_blob, check_trace, trial_pass, unexpected_ledger_rows
from tests.conftest import BY_ID

SHAPES = ("swarm", "workflow", "single", "orchestrator")


def _assert_public_result(store, result, claim_id):
    assert result.claim_id == claim_id
    payload = result.as_dict()
    with closing(connect(store)) as conn:
        passed, reason = trial_pass(payload, BY_ID[claim_id]["expected"], conn)
    assert passed, reason
    assert "CANARY_SECRET_" not in artifact_blob(payload)


@pytest.mark.student
@pytest.mark.parametrize("shape", SHAPES)
def test_refund_retry_with_different_seed_keeps_one_refund(public_db, monkeypatch, tmp_path, shape):
    monkeypatch.chdir(tmp_path)
    claim_id = "C-011"
    for seed in (11, 55):
        result = run_shape(shape, claim_id, seed=seed, store_path=str(public_db))
        _assert_public_result(public_db, result, claim_id)


@pytest.mark.student
@pytest.mark.parametrize("shape", SHAPES)
def test_approval_for_another_claim_on_same_order_is_rejected(public_db, monkeypatch, tmp_path, shape):
    monkeypatch.chdir(tmp_path)
    claim_id = "C-011"
    # C-012 shares the principal, order, and quote with C-011.
    with closing(connect(public_db)) as conn, conn:
        conn.execute(
            "UPDATE claims SET approval_id = ? WHERE claim_id = ?",
            (BY_ID["C-012"]["approval_id"], claim_id),
        )

    result = run_shape(shape, claim_id, seed=11, store_path=str(public_db))
    with closing(connect(public_db)) as conn:
        refund_count = conn.execute(
            "SELECT COUNT(*) FROM refund_ledger WHERE claim_id = ?", (claim_id,)
        ).fetchone()[0]
        denials = conn.execute(
            "SELECT details_json FROM audit_events WHERE claim_id = ? AND event_type = 'policy_denied'",
            (claim_id,),
        ).fetchall()
        assert committed_audit_count(conn, claim_id) == 0
        assert unexpected_ledger_rows(conn, claim_id) == 0

    assert result.claim_id == claim_id
    assert result.status == "denied"
    assert result.proposal_amount == BY_ID[claim_id]["expected"]["proposal_amount"]
    assert result.refund_effects == []
    assert refund_count == 0
    assert [json.loads(row[0])["reason"] for row in denials] == ["approval_claim_mismatch"]
    payload = result.as_dict()
    trace_ok, reason = check_trace(payload)
    assert trace_ok, reason
    assert "CANARY_SECRET_" not in artifact_blob(payload)


@pytest.mark.student
@pytest.mark.parametrize("shape", SHAPES)
@pytest.mark.parametrize(
    ("crash_at", "refunds_at_crash", "checkpoints_at_crash"),
    [
        ("before_effect", 0, 0),
        ("after_effect_before_checkpoint", 1, 0),
        ("after_checkpoint", 1, 1),
    ],
)
def test_resume_from_each_crash_point_keeps_one_refund(
    public_db, monkeypatch, tmp_path, shape, crash_at, refunds_at_crash, checkpoints_at_crash
):
    monkeypatch.chdir(tmp_path)
    claim_id = "C-012"
    with pytest.raises(InjectedCrash, match=f"^{crash_at}$"):
        run_shape(shape, claim_id, seed=11, store_path=str(public_db), crash_at=crash_at)

    with closing(connect(public_db)) as conn:
        refund_count = conn.execute(
            "SELECT COUNT(*) FROM refund_ledger WHERE claim_id = ?", (claim_id,)
        ).fetchone()[0]
        checkpoint_count = conn.execute(
            "SELECT COUNT(*) FROM checkpoints WHERE claim_id = ? AND step = 'issue_refund'", (claim_id,)
        ).fetchone()[0]
        assert refund_count == committed_audit_count(conn, claim_id) == refunds_at_crash
        assert checkpoint_count == checkpoints_at_crash

    for path in (tmp_path / "traces").glob("*.json"):
        assert "CANARY_SECRET_" not in path.read_text(encoding="utf-8")

    resumed = run_shape(shape, claim_id, seed=11, store_path=str(public_db))
    _assert_public_result(public_db, resumed, claim_id)
