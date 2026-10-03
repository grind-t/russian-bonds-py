from collections.abc import Iterable
from typing import Protocol

from .net_quantities import get_net_quantities_by_ticker


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
    initial_positions: dict[str, int] = {}
    for ticker, net in get_net_quantities_by_ticker(operations).items():
        if net > 0:
            raise ValueError(f"Unclosed position for {ticker}")
        initial_positions[ticker] = -net
    return initial_positions
