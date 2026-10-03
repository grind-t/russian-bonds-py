from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Self

import httpx
from pydantic import (
    AwareDatetime,
    BaseModel,
    Field,
    model_validator,
)
from t_tech.invest import (
    GetOperationsByCursorRequest,
    OperationItem,
    OperationState,
    OperationType,
    _grpc_helpers,
)
from t_tech.invest.async_services import AsyncServices
from t_tech.invest.grpc import operations_pb2
from t_tech.invest.utils import money_to_decimal, quotation_to_decimal
from toolkit.boolean import ensure

from .last_amortization import get_last_amortization
from .quantity_by_payment import get_quantity_by_payment
from .quantity_delta import BOND_REPAYMENT_FULL, quantity_delta


# the SDK schema omits the ticker field that the API does return
@dataclass(eq=False, repr=True)
class _TInvestOperationItem(OperationItem):
    ticker: str = _grpc_helpers.string_field(36)


class AccountOperation(BaseModel):
    id: str = Field(min_length=1)
    parent_operation_id: str
    ticker: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    type: OperationType
    payment: float = Field(allow_inf_nan=False)
    quantity_delta: int
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

    @classmethod
    async def from_t_invest_item(
        cls, item: _TInvestOperationItem, moex_client: httpx.AsyncClient
    ) -> Self:
        payment = float(money_to_decimal(item.payment))
        quantity = item.quantity_done
        if item.type == BOND_REPAYMENT_FULL:
            # the last amortization is the final repayment
            amortization = await get_last_amortization(item.ticker, client=moex_client)
            if amortization is None or amortization.value_rub is None:
                raise ValueError(f"No final amortization for {item.ticker}")
            # full repayment comes with zero quantity, so derive it from the payment,
            # which is in rubles even for currency bonds
            quantity = get_quantity_by_payment(payment, amortization.value_rub)
        return cls(
            id=item.id,
            parent_operation_id=item.parent_operation_id,
            ticker=item.ticker,
            name=item.name,
            description=item.description,
            type=item.type,
            payment=payment,
            quantity_delta=quantity_delta(item.type, quantity),
            date=item.date,
            virtual=False,
        )


async def fetch_account_operations_from_t_invest(
    t_invest_client: AsyncServices,
    moex_client: httpx.AsyncClient,
    account_id: str,
    from_: datetime | None = None,
    to: datetime | None = None,
) -> list[AccountOperation]:
    raw_items: list[operations_pb2.OperationItem] = []
    cursor: str | None = None
    while True:
        # the stub is called directly to get raw items that still carry the ticker
        res = await t_invest_client.operations.stub.GetOperationsByCursor(
            request=_grpc_helpers.dataclass_to_protobuf(
                GetOperationsByCursorRequest(
                    account_id=account_id,
                    from_=from_,
                    to=to,
                    cursor=cursor,
                    limit=1000,  # API maximum
                ),
                operations_pb2.GetOperationsByCursorRequest(),
            ),
            metadata=t_invest_client.operations.metadata,
        )
        raw_items.extend(res.items)
        if not res.has_next:
            break
        cursor = res.next_cursor

    operations: list[AccountOperation] = []
    for raw in raw_items:
        if raw.instrument_type != "bond":
            continue
        item = _grpc_helpers.protobuf_to_dataclass(raw, _TInvestOperationItem)
        if item.state != OperationState.OPERATION_STATE_EXECUTED:
            continue
        operations.append(await AccountOperation.from_t_invest_item(item, moex_client))
    return operations


async def fetch_virtual_operations_from_t_invest(
    t_invest_client: AsyncServices, account_id: str, now: datetime
) -> list[AccountOperation]:
    portfolio = await t_invest_client.operations.get_portfolio(account_id=account_id)
    operations: list[AccountOperation] = []
    for pos in portfolio.positions:
        if pos.instrument_type != "bond":
            continue
        quantity_decimal = quotation_to_decimal(pos.quantity)
        ensure(
            quantity_decimal == quantity_decimal.to_integral_value(),
            f"Fractional position quantity for {pos.ticker}",
        )
        quantity = int(quantity_decimal)
        current_price = float(money_to_decimal(pos.current_price))
        current_nkd = float(money_to_decimal(pos.current_nkd))
        operations.append(
            AccountOperation(
                id=f"virtual:{pos.ticker}",
                parent_operation_id="",
                ticker=pos.ticker,
                name="Продажа",
                description="Виртуальная продажа по рыночной цене",
                type=OperationType.OPERATION_TYPE_SELL,
                payment=(current_price + current_nkd) * quantity,
                quantity_delta=-quantity,
                date=now,
                virtual=True,
            )
        )
    return operations


def group_account_operations_by_ticker(
    operations: Iterable[AccountOperation],
) -> dict[str, list[AccountOperation]]:
    operations_by_ticker: dict[str, list[AccountOperation]] = {}
    for op in operations:
        operations_by_ticker.setdefault(op.ticker, []).append(op)
    return operations_by_ticker
