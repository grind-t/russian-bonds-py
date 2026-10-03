from collections.abc import Iterable
from dataclasses import dataclass

from .normalized_operations import NormalizedOperation


@dataclass(frozen=True)
class NormalizedOperationGroup:
    operations: list[NormalizedOperation]
    net_quantity: int


def group_operations_by_ticker(
    operations: Iterable[NormalizedOperation],
) -> dict[str, NormalizedOperationGroup]:
    operations_by_ticker: dict[str, list[NormalizedOperation]] = {}
    for op in operations:
        operations_by_ticker.setdefault(op.ticker, []).append(op)
    return {
        ticker: NormalizedOperationGroup(
            operations=ops,
            net_quantity=sum(op.quantity_delta for op in ops),
        )
        for ticker, ops in operations_by_ticker.items()
    }
