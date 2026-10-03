from collections.abc import Iterable
from dataclasses import dataclass

from .account_operations import AccountOperation, AccountOperations


@dataclass(frozen=True)
class AccountOperationGroup:
    operations: AccountOperations
    net_quantity: int


def group_operations_by_ticker(
    operations: Iterable[AccountOperation],
) -> dict[str, AccountOperationGroup]:
    operations_by_ticker: dict[str, list[AccountOperation]] = {}
    for op in operations:
        operations_by_ticker.setdefault(op.ticker, []).append(op)
    return {
        ticker: AccountOperationGroup(
            operations=AccountOperations(tuple(ops)),
            net_quantity=sum(op.quantity_delta for op in ops),
        )
        for ticker, ops in operations_by_ticker.items()
    }
