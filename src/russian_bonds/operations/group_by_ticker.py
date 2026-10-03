from dataclasses import dataclass

from .normalized_operations import NormalizedOperation, NormalizedOperations
from .quantity_delta import quantity_delta


@dataclass(frozen=True)
class NormalizedOperationGroup:
    operations: NormalizedOperations
    net_quantity: int


def group_operations_by_ticker(
    operations: NormalizedOperations,
) -> dict[str, NormalizedOperationGroup]:
    operations_by_ticker: dict[str, list[NormalizedOperation]] = {}
    for op in operations:
        operations_by_ticker.setdefault(op.ticker, []).append(op)
    return {
        ticker: NormalizedOperationGroup(
            operations=NormalizedOperations(ops),
            net_quantity=sum(quantity_delta(op.type, op.quantity) for op in ops),
        )
        for ticker, ops in operations_by_ticker.items()
    }
