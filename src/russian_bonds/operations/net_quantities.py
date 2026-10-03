from collections.abc import Iterable
from typing import Protocol


class _Operation(Protocol):
    @property
    def ticker(self) -> str: ...

    @property
    def quantity_delta(self) -> int: ...


def get_net_quantities_by_ticker(operations: Iterable[_Operation]) -> dict[str, int]:
    net_quantities: dict[str, int] = {}
    for op in operations:
        net_quantities[op.ticker] = net_quantities.get(op.ticker, 0) + op.quantity_delta
    return net_quantities
