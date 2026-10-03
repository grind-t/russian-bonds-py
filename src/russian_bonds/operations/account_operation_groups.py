from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, computed_field

from .account_operations import AccountOperation


class AccountOperationGroup(BaseModel):
    model_config = ConfigDict(frozen=True)

    operations: list[AccountOperation]

    @computed_field
    @property
    def net_quantity(self) -> int:
        return sum(op.quantity_delta for op in self.operations)


def group_account_operations_by_ticker(
    operations: Iterable[AccountOperation],
) -> dict[str, AccountOperationGroup]:
    operations_by_ticker: dict[str, list[AccountOperation]] = {}
    for op in operations:
        operations_by_ticker.setdefault(op.ticker, []).append(op)
    return {
        ticker: AccountOperationGroup(operations=ops)
        for ticker, ops in operations_by_ticker.items()
    }
