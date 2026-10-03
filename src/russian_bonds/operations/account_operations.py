from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Self

import httpx
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
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
from t_tech.invest.utils import money_to_decimal

from .last_amortization import get_last_amortization
from .quantity_by_payment import get_quantity_by_payment
from .quantity_delta import BOND_REPAYMENT_FULL, quantity_delta


# the SDK schema omits the ticker field that the API does return
@dataclass(eq=False, repr=True)
class _TInvestOperationItem(OperationItem):
    ticker: str = _grpc_helpers.string_field(36)


class AccountOperation(BaseModel):
    model_config = ConfigDict(frozen=True)
    
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


class AccountOperations(RootModel[tuple[AccountOperation, ...]]):
    model_config = ConfigDict(frozen=True)

    def __iter__(self) -> Iterator[AccountOperation]:  # ty: ignore[invalid-method-override]
        return iter(self.root)

    def __len__(self) -> int:
        return len(self.root)

    def __add__(self, other: Self) -> Self:
        return type(self)((*self.root, *other.root))

    @classmethod
    async def fetch_from_t_invest(
        cls,
        t_invest_client: AsyncServices,
        moex_client: httpx.AsyncClient,
        account_id: str,
        from_: datetime | None = None,
        to: datetime | None = None,
    ) -> Self:
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
            # API has no instrument type filter, so bonds are picked client-side
            if raw.instrument_type != "bond":
                continue
            item = _grpc_helpers.protobuf_to_dataclass(raw, _TInvestOperationItem)
            if item.state != OperationState.OPERATION_STATE_EXECUTED:
                continue
            operations.append(
                await AccountOperation.from_t_invest_item(item, moex_client)
            )
        return cls(operations)
