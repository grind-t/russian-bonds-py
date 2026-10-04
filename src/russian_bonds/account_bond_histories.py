import asyncio
from typing import Self

import httpx
from pydantic import BaseModel, computed_field, model_validator
from t_tech.invest import OperationType
from toolkit.boolean import ensure

from .bonds import Bond
from .operations.account_operations import AccountOperation

BROKER_FEE = OperationType.OPERATION_TYPE_BROKER_FEE


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

    def without_initial_bonds(self) -> Self:
        # FIFO: sells consume the bonds held before the operations first
        initial_left = self.initial_bond_quantity
        total = initial_left
        current_fraction = 0.0  # fraction of the bonds bought within the operations
        op_fractions: dict[str, float] = {}  # fraction of each operation to keep
        # a stable sort keeps operations with the same date in order
        for op in sorted(self.operations, key=lambda op: op.date):
            if op.type == BROKER_FEE:
                continue
            delta = op.quantity_delta
            if delta < 0:
                initial_sold = min(initial_left, -delta)
                initial_left -= initial_sold
                op_fractions[op.id] = (delta + initial_sold) / delta
            else:
                # payments are made for the position at the payment date,
                # though the record date comes a few days earlier
                op_fractions[op.id] = 1.0 if delta > 0 else current_fraction
            total += delta
            # the fraction carries over to payments after the position is closed
            if total > 0:
                current_fraction = (total - initial_left) / total

        operations: list[AccountOperation] = []
        for op in self.operations:
            # a fee follows its deal and is dropped with a deal outside the operations
            key = op.parent_operation_id if op.type == BROKER_FEE else op.id
            op_fraction = op_fractions.get(key, 0.0)
            if op_fraction == 0:
                continue
            operations.append(
                op.model_copy(
                    update={
                        "payment": op.payment * op_fraction,
                        "quantity_delta": round(op.quantity_delta * op_fraction),
                    }
                )
            )
        return type(self)(bond=self.bond, operations=operations)

    @classmethod
    async def from_operations(
        cls, operations: list[AccountOperation], client: httpx.AsyncClient
    ) -> Self:
        first = ensure(operations, "No operations")[0]
        bond = await Bond.fetch_from_moex(first.ticker, client)
        return cls(bond=bond, operations=operations)


async def get_account_bond_histories_from_operations(
    operations: list[AccountOperation], client: httpx.AsyncClient
) -> dict[str, AccountBondHistory]:
    by_ticker: dict[str, list[AccountOperation]] = {}
    for op in operations:
        by_ticker.setdefault(op.ticker, []).append(op)
    histories = await asyncio.gather(
        *(AccountBondHistory.from_operations(ops, client) for ops in by_ticker.values())
    )
    return dict(zip(by_ticker, histories, strict=True))
