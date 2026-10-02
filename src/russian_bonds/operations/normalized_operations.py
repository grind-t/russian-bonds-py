from collections.abc import Iterator
from datetime import datetime
from typing import Self

import httpx
from pydantic import AwareDatetime, BaseModel, Field, RootModel, model_validator
from t_tech.invest import OperationState, OperationType
from t_tech.invest.utils import money_to_decimal

from ..clients import Clients
from .account_operations import BondOperationItem, get_account_bond_operations
from .last_amortization import get_last_amortization
from .quantity_by_payment import get_quantity_by_payment
from .quantity_delta import BOND_REPAYMENT_FULL


class NormalizedOperation(BaseModel):
    id: str = Field(min_length=1)
    parent_operation_id: str
    ticker: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    type: OperationType
    payment: float = Field(allow_inf_nan=False)
    quantity_done: int = Field(ge=0)
    date: AwareDatetime
    virtual: bool

    @model_validator(mode="after")
    def _check_fee_parent(self) -> Self:
        if (
            self.type == OperationType.OPERATION_TYPE_BROKER_FEE
            and not self.parent_operation_id
        ):
            raise ValueError(f"No parent operation for fee {self.id} of {self.ticker}")
        return self


class NormalizedOperations(RootModel[list[NormalizedOperation]]):
    @model_validator(mode="after")
    def _check_unique_ids(self) -> Self:
        seen: set[str] = set()
        for op in self.root:
            if op.id in seen:
                raise ValueError(f"Duplicate operation id {op.id}")
            seen.add(op.id)
        return self

    def __iter__(self) -> Iterator[NormalizedOperation]:  # type: ignore[override]
        return iter(self.root)

    def __len__(self) -> int:
        return len(self.root)


async def get_normalized_operations(
    clients: Clients,
    account_id: str,
    from_: datetime | None = None,
) -> NormalizedOperations:
    return NormalizedOperations(
        [
            await _normalize(op, clients.moex)
            for op in await get_account_bond_operations(
                clients.t_invest, account_id, from_
            )
            if op.state == OperationState.OPERATION_STATE_EXECUTED
        ]
    )


async def _normalize(
    op: BondOperationItem, moex_client: httpx.AsyncClient
) -> NormalizedOperation:
    payment = float(money_to_decimal(op.payment))
    quantity_done = op.quantity_done
    if op.type == BOND_REPAYMENT_FULL:
        # the last amortization is the final repayment
        amortization = await get_last_amortization(op.ticker, client=moex_client)
        if amortization is None or amortization.value_rub is None:
            raise ValueError(f"No final amortization for {op.ticker}")
        # full repayment comes with zero quantity, so derive it from the payment,
        # which is in rubles even for currency bonds
        quantity_done = get_quantity_by_payment(payment, amortization.value_rub)
    return NormalizedOperation(
        id=op.id,
        parent_operation_id=op.parent_operation_id,
        ticker=op.ticker,
        name=op.name,
        description=op.description,
        type=op.type,
        payment=payment,
        quantity_done=quantity_done,
        date=op.date,
        virtual=False,
    )
