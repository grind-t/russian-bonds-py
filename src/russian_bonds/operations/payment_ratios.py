from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from t_tech.invest import OperationType
from toolkit.boolean import ensure

from .initial_positions import get_initial_positions
from .quantity_delta import BUY_TYPES, quantity_delta

BROKER_FEE = OperationType.OPERATION_TYPE_BROKER_FEE


class _Operation(Protocol):
    id: str
    parent_operation_id: str
    ticker: str
    type: OperationType
    quantity_done: int
    date: datetime


def _validate_ids(operations: Sequence[_Operation]) -> None:
    ids = [op.id for op in operations]
    ensure("" not in ids, "Operation ids must be nonempty")
    ensure(len(set(ids)) == len(ids), "Operation ids must be unique")


def get_payment_ratios(operations: Sequence[_Operation]) -> dict[str, float]:
    _validate_ids(operations)

    total_positions = get_initial_positions(operations)
    window_positions = dict.fromkeys(total_positions, 0.0)
    window_shares = dict.fromkeys(total_positions, 0.0)

    fees = [op for op in operations if op.type == BROKER_FEE]
    rest = [op for op in operations if op.type != BROKER_FEE]

    ratios: dict[str, float] = {}
    # the API returns operations newest first
    for op in sorted(rest, key=lambda op: op.date):
        ticker = op.ticker
        ratios[op.id] = 1.0 if op.type in BUY_TYPES else window_shares[ticker]
        delta = quantity_delta(op.type, op.quantity_done)
        total_positions[ticker] += delta
        window_positions[ticker] += delta * ratios[op.id]
        # sells keep the share, so it carries over to payments after the position
        # is closed
        if total_positions[ticker] > 0:
            window_shares[ticker] = window_positions[ticker] / total_positions[ticker]
        else:
            window_positions[ticker] = 0.0

    for op in fees:
        # a fee whose deal is outside the window is dropped
        ratios[op.id] = ratios.get(op.parent_operation_id, 0.0)

    return ratios
