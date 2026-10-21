from typing import Self

from pydantic import BaseModel, computed_field, model_validator
from toolkit.boolean import ensure

from russian_bonds._entities.account_operation import AccountOperation
from russian_bonds._entities.bond import Bond


class AccountBondHistory(BaseModel):
    bond: Bond
    operations: list[AccountOperation]

    @model_validator(mode="after")
    def _check_tickers(self) -> Self:
        for op in self.operations:
            ensure(
                op.ticker == self.bond.ticker,
                f"Operation {op.id} of {op.ticker} for {self.bond.ticker}",
            )
        return self

    @model_validator(mode="after")
    def _check_closed(self) -> Self:
        net = sum(op.quantity_delta for op in self.operations)
        ensure(net <= 0, f"Unclosed position for {self.bond.ticker}")
        return self

    @computed_field
    @property
    def initial_bond_quantity(self) -> int:
        # history always ends at zero (virtual sell or full repayment),
        # so a negative sum is the quantity held before the operations
        return -sum(op.quantity_delta for op in self.operations)
