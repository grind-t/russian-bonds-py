from collections.abc import Iterable
from typing import Protocol


class _Operation(Protocol):
    @property
    def ticker(self) -> str: ...

    @property
    def quantity_delta(self) -> int: ...


def get_initial_positions(
    operations: Iterable[_Operation],
) -> dict[str, int]:
    # history always ends at zero (virtual sell or full repayment), so a negative sum
    # is the quantity held before the operations
    net_quantities: dict[str, int] = {}
    for op in operations:
        net_quantities[op.ticker] = net_quantities.get(op.ticker, 0) + op.quantity_delta
    initial_positions: dict[str, int] = {}
    for ticker, net in net_quantities.items():
        if net > 0:
            raise ValueError(f"Unclosed position for {ticker}")
        initial_positions[ticker] = -net
    return initial_positions
