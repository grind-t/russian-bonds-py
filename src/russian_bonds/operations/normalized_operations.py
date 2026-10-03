from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Self

import httpx
from t_tech.invest import OperationState, OperationType
from t_tech.invest.async_services import AsyncServices
from t_tech.invest.utils import money_to_decimal
from toolkit.boolean import ensure

from .account_operations import BondOperationItem, get_account_bond_operations
from .last_amortization import get_last_amortization
from .quantity_by_payment import get_quantity_by_payment
from .quantity_delta import BOND_REPAYMENT_FULL, quantity_delta


@dataclass(frozen=True)
class NormalizedOperation:
    id: str
    parent_operation_id: str
    ticker: str
    name: str
    description: str
    type: OperationType
    payment: float
    quantity_delta: int
    date: datetime
    virtual: bool

    @classmethod
    async def from_operation_item(
        cls, op: BondOperationItem, moex_client: httpx.AsyncClient
    ) -> Self:
        ensure(op.id, "Empty operation id")
        ensure(op.ticker, f"Empty ticker of {op.id}")
        ensure(op.name, f"Empty name of {op.id}")
        ensure(op.description, f"Empty description of {op.id}")
        ensure(op.date.tzinfo, f"Naive date of {op.id}")
        ensure(
            op.type != OperationType.OPERATION_TYPE_BROKER_FEE
            or op.parent_operation_id,
            f"No parent operation for fee {op.id} of {op.ticker}",
        )
        payment = float(money_to_decimal(op.payment))
        quantity = op.quantity_done
        if op.type == BOND_REPAYMENT_FULL:
            # the last amortization is the final repayment
            amortization = await get_last_amortization(op.ticker, client=moex_client)
            if amortization is None or amortization.value_rub is None:
                raise ValueError(f"No final amortization for {op.ticker}")
            # full repayment comes with zero quantity, so derive it from the payment,
            # which is in rubles even for currency bonds
            quantity = get_quantity_by_payment(payment, amortization.value_rub)
        return cls(
            id=op.id,
            parent_operation_id=op.parent_operation_id,
            ticker=op.ticker,
            name=op.name,
            description=op.description,
            type=op.type,
            payment=payment,
            quantity_delta=quantity_delta(op.type, quantity),
            date=op.date,
            virtual=False,
        )


class NormalizedOperations(tuple[NormalizedOperation, ...]):
    def __new__(cls, operations: Iterable[NormalizedOperation] = ()) -> Self:
        self = super().__new__(cls, operations)
        seen: set[str] = set()
        for op in self:
            ensure(op.id not in seen, f"Duplicate operation id {op.id}")
            seen.add(op.id)
        return self


async def get_normalized_operations(
    t_invest_client: AsyncServices,
    moex_client: httpx.AsyncClient,
    account_id: str,
    from_: datetime | None = None,
) -> NormalizedOperations:
    return NormalizedOperations(
        [
            await NormalizedOperation.from_operation_item(op, moex_client)
            for op in await get_account_bond_operations(
                t_invest_client, account_id, from_
            )
            if op.state == OperationState.OPERATION_STATE_EXECUTED
        ]
    )
