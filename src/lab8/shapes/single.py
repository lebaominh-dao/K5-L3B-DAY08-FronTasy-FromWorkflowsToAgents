"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import Decide, ToolRejected, run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.trace import Trace

SHAPE = "single"
MAX_STEPS = 8


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def make_decide(
    claim_id: str,
    *,
    budget: Budget,
    seed: int,
    memory: dict[str, Any],
    trace: Trace,
) -> Decide:
    """The agent's brain: look at what it has seen, pick the next read tool or finish.

    run_react only hands back the LAST tool result, so earlier results are kept in
    `memory`. Every call to decide counts as one model call in the Budget.
    """

    def decide(seen: dict[str, Any]) -> dict[str, Any]:
        # One "thinking" step = one model call. The prompt is never written to the trace.
        complete(budget, seed=seed, purpose="react", prompt=json.dumps(seen, ensure_ascii=False, sort_keys=True))

        last_tool = seen.get("last_tool")
        if last_tool:
            memory[last_tool] = seen.get("last_result") or {}

        claim = memory.get("get_claim_view")
        if claim is None:
            return _call(trace, "get_claim_view", {"claim_id": claim_id})
        if not claim.get("found"):
            return {"final": {"status": "failed", "error_reason": "unknown_claim"}}
        # Order id comes from the claim row only, never from words in the ticket.
        if not claim.get("order_id"):
            return {"final": {"status": "needs_info", "error_reason": "missing_order_id"}}

        order_view = memory.get("lookup_order")
        if order_view is None:
            return _call(
                trace,
                "lookup_order",
                {"order_id": claim["order_id"], "principal_id": claim["principal_id"]},
            )
        if not order_view.get("visible"):
            trace.add("order", {"visible": False, "reason": order_view.get("reason")})
            return {"final": {"status": "escalated", "error_reason": order_view.get("reason")}}

        quote = memory.get("compute_compensation")
        if quote is None:
            # Delay, fee and damage come from the order row, not from the ticket text.
            trace.add("order", safe_dump(order_view["order"]))
            return _call(trace, "compute_compensation", {"order": order_view["order"]})
        return {"final": {"status": "quoted", "quote": quote}}

    return decide


def _call(trace: Trace, tool: str, args: dict[str, Any]) -> dict[str, Any]:
    trace.add("tool_call", {"tool": tool})
    return {"tool": tool, "args": args}


def _run(conn: sqlite3.Connection, claim_id: str, *, seed: int, crash_at: str | None) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id(SHAPE, claim_id, seed))

    def done(status: str, proposal: int, reason: str | None) -> RunResult:
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

    decide = make_decide(claim_id, budget=budget, seed=seed, memory={}, trace=trace)
    try:
        loop = run_react(
            conn,
            budget,
            observation={"claim": {"claim_id": claim_id}},
            decide=decide,
            max_steps=MAX_STEPS,
        )
    except ToolRejected as exc:
        return done("failed", 0, f"tool_rejected:{exc}")

    final = loop["final"]
    if loop["stopped"] == "step_cap" or final.get("status") != "quoted":
        return done(final.get("status", "failed"), 0, final.get("error_reason"))

    quote = final["quote"]
    proposal = int(quote["amount_vnd"])
    trace.add("quote", safe_dump(quote))
    if proposal <= 0:
        # Nothing to pay: do not call the host.
        return done("denied", 0, quote.get("reason"))

    # The model never writes money. The shape hands the FULL quote to the host gate.
    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    trace.add("refund", {"ok": outcome["ok"], "reason": outcome["reason"], "conflict": outcome["conflict"]})
    if outcome["ok"]:
        return done("resolved", proposal, None)
    return done("failed" if outcome["conflict"] else "denied", proposal, outcome["reason"])
