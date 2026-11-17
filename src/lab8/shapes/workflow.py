"""Shape A — deterministic workflow. Student work.

Signature (do not change):

    run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult

Suggested steps. Money stays in code (`lab8.tools.compute_compensation`).

1. Open the store. Read the claim through `get_claim_view` (not SELECT *).
2. Missing order_id -> status `needs_info`. Do not write the ledger.
3. `lookup_order`. If not visible -> `escalated`. Do not copy phone, address, item, internal note.
4. Quote from the order row. Ignore delay numbers written in the ticket.
5. Quote amount 0 -> `denied`. Do not call issue_refund.
6. Quote amount > 0 -> `durability.issue_refund(conn, claim_id, <full quote>)`.
   Pass the FULL quote. The host checks the claim's own approval and subtracts
   what earlier claims already got for the same order (T13, T14). Do not
   subtract it yourself or the host subtracts twice.
   Auth failure or order already refunded -> `denied` (the host writes `policy_denied`).
   `proposal_amount` stays the full quote. Amount conflict -> `failed`.
7. Success -> `resolved`. One ledger row, one `refund_committed` audit.
8. Use MockLLM only to draft the reply text, if you want a model call at all.

The model must not choose the refund amount and must not commit the refund.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import compute_compensation, get_claim_view, lookup_order, tool_cost
from lab8.trace import Trace

SHAPE = "workflow"


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    # TODO CP3 (student): truyền crash_at vào durability.issue_refund, không bắt InjectedCrash.
    del crash_at
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed)
    finally:
        conn.close()


def _run(conn: sqlite3.Connection, claim_id: str, *, seed: int) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id(SHAPE, claim_id, seed))

    def end(status: str, proposal: int, reason: str | None) -> RunResult:
        # Every return path goes through here so the trace is always written.
        trace.add("decision", {"status": status, "proposal_amount": proposal, "reason": reason})
        return finish(
            conn,
            shape=SHAPE,
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=reason,
        )

    # Step 1: read the claim through the allowlisted view. The ticket text is user
    # data: it is never parsed for amounts or order ids, and never written to the trace.
    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    trace.add("claim", {"found": claim["found"], "has_order_id": bool(claim.get("order_id"))})
    if not claim["found"]:
        return end("failed", 0, "unknown_claim")

    # Step 2: no order id on the claim -> ask for it. Do not guess one from the ticket.
    if not claim["order_id"]:
        return end("needs_info", 0, "missing_order_id")

    # Step 3: the order must exist and belong to the claim's principal.
    budget.add_tool(tool_cost())
    order_view = lookup_order(conn, claim["order_id"], claim["principal_id"])
    trace.add("order", order_view)
    if not order_view["visible"]:
        return end("escalated", 0, order_view["reason"])

    # Step 4: money is computed by code from the order row and the current policy.
    budget.add_tool(tool_cost())
    quote = compute_compensation(conn, order_view["order"])
    trace.add("quote", quote)
    proposal = int(quote["amount_vnd"])

    # Step 5: nothing owed -> deny without touching the host gate.
    if proposal <= 0:
        return end("denied", 0, quote["reason"])

    # Step 6: hand the FULL quote to the host. It checks approval, the per-order cap
    # and idempotency, and writes the policy_denied audit when it refuses.
    outcome = issue_refund(conn, claim_id, proposal)
    trace.add("refund", {"ok": outcome["ok"], "reason": outcome["reason"], "conflict": outcome["conflict"]})
    if not outcome["ok"]:
        return end("failed" if outcome["conflict"] else "denied", proposal, outcome["reason"])

    # Step 7: one ledger row, one refund_committed audit.
    return end("resolved", proposal, None)
