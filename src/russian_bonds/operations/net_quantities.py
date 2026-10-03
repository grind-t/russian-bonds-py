from collections.abc import Iterable
from typing import Protocol

from t_tech.invest import OperationType

from .quantity_delta import quantity_delta


class _Operation(Protocol):
    ticker: str
    type: OperationType
    quantity: int


def get_net_quantities_by_ticker(operations: Iterable[_Operation]) -> dict[str, int]:
    net_quantities: dict[str, int] = {}
    for op in operations:
        net_quantities[op.ticker] = net_quantities.get(op.ticker, 0) + quantity_delta(
            op.type, op.quantity
        )
    return net_quantities
