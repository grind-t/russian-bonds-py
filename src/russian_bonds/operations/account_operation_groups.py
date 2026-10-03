from collections.abc import Iterable
from typing import Self

from pydantic import BaseModel, ConfigDict, computed_field, model_validator

from .account_operations import AccountOperation


class AccountOperationGroup(BaseModel):
    model_config = ConfigDict(frozen=True)

    operations: tuple[AccountOperation, ...]

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
        ticker: AccountOperationGroup(operations=tuple(ops))
        for ticker, ops in operations_by_ticker.items()
    }
