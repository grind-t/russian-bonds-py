import asyncio
from typing import Self

import httpx
from pydantic import BaseModel, model_validator
from toolkit.boolean import ensure

from .bonds import Bond
from .operations.account_operations import AccountOperation


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
