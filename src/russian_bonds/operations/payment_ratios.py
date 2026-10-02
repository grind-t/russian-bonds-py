from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from toolkit.boolean import ensure

from .initial_quantities import get_initial_quantities_by_ticker
from .quantity_delta import BUY_TYPES, quantity_delta

BROKER_FEE = 19


class _Operation(Protocol):
    id: str
    parent_operation_id: str
    ticker: str
    type: int
    quantity_done: int
    date: datetime


def _validate_ids(operations: Sequence[_Operation]) -> None:
    ids = [op.id for op in operations]
    ensure("" not in ids, "Operation ids must be nonempty")
    ensure(len(set(ids)) == len(ids), "Operation ids must be unique")


def get_payment_ratios(operations: Sequence[_Operation]) -> dict[str, float]:
    _validate_ids(operations)

    held = get_initial_quantities_by_ticker(operations)
    window = dict.fromkeys(held, 0.0)
    ratio = dict.fromkeys(held, 0.0)

    fees = [op for op in operations if op.type == BROKER_FEE]
    rest = [op for op in operations if op.type != BROKER_FEE]

    ratios: dict[str, float] = {}
    # the API returns operations newest first
    for op in sorted(rest, key=lambda op: op.date):
        ticker = op.ticker
        ratios[op.id] = 1.0 if op.type in BUY_TYPES else ratio[ticker]
        delta = quantity_delta(op.type, op.quantity_done)
        held[ticker] += delta
        window[ticker] += delta * ratios[op.id]
        # sells keep the ratio, so it carries over to payments after the position
        # is closed
        if held[ticker] > 0:
            ratio[ticker] = window[ticker] / held[ticker]
        else:
            window[ticker] = 0.0

    for op in fees:
        ensure(
            op.parent_operation_id,
            f"No parent operation for fee {op.id} of {op.ticker}",
        )
        # a fee whose deal is outside the window is dropped
        ratios[op.id] = ratios.get(op.parent_operation_id, 0.0)

    return ratios
