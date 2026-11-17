from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.shapes import SHAPES

from conftest import CLAIMS, WORLD


@pytest.mark.parametrize("shape", ["workflow", "single", "orchestrator"])
@pytest.mark.parametrize("claim", CLAIMS, ids=lambda claim: claim["claim_id"])
def test_shape_trace_and_stdout_do_not_expose_parent_or_order_data(
    shape, claim, public_db, capsys
):
    result = SHAPES[shape](claim["claim_id"], seed=11, store_path=str(public_db))
    output = capsys.readouterr()
    trace = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))

    blob = json.dumps(trace, ensure_ascii=False) + output.out + output.err
    assert "CANARY_SECRET_" not in blob
    assert "Bearer " not in blob
    assert "parent_secret" not in blob
    assert "raw_headers" not in blob
    assert "ticket" not in blob
    assert "phone" not in blob
    assert "address" not in blob
    assert "internal_note" not in blob
    assert "item_name" not in blob

    # Check actual fixture values too, including phone numbers and free-text notes.
    private_order_values = {
        str(order[key])
        for order in WORLD["orders"]
        for key in ("phone", "address", "internal_note", "item_name")
        if order.get(key)
    }
    assert all(value not in blob for value in private_order_values)
    assert claim["ticket"] not in blob
    assert claim["parent_secret"] not in blob
