from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from t_tech.invest import (
    OperationItem,
    OperationState,
    OperationType,
    PortfolioPosition,
    _grpc_helpers,
)
from t_tech.invest.grpc import operations_pb2
from t_tech.invest.utils import money_to_decimal, quotation_to_decimal
from toolkit.boolean import ensure

from russian_bonds._core.cash_flows.account_operation import AccountOperation
from russian_bonds._core.cash_flows.operation_quantity import (
    BOND_REPAYMENT_FULL,
    quantity_by_payment,
    quantity_delta,
)


# the SDK schema omits the ticker field that the API does return
@dataclass(eq=False, repr=True)
class _TInvestOperationItem(OperationItem):
    ticker: str = _grpc_helpers.string_field(36)


def executed_bond_operation_items(
    raw_items: Iterable[operations_pb2.OperationItem],
) -> list[_TInvestOperationItem]:
    """Executed bond operations, oldest first."""
    items: list[_TInvestOperationItem] = []
    # the API returns items newest first
    for raw in reversed(list(raw_items)):
        if raw.instrument_type != "bond":
            continue
        item = _grpc_helpers.protobuf_to_dataclass(raw, _TInvestOperationItem)
        if item.state == OperationState.OPERATION_STATE_EXECUTED:
            items.append(item)
    return items


def account_operation_from_t_invest_item(
    item: _TInvestOperationItem, final_amortization_rub: float | None
) -> AccountOperation:
    payment = float(money_to_decimal(item.payment))
    quantity = item.quantity_done
    if item.type == BOND_REPAYMENT_FULL:
        if final_amortization_rub is None:
            raise ValueError(f"No final amortization for {item.ticker}")
        # full repayment comes with zero quantity, so derive it from the payment,
        # which is in rubles even for currency bonds
        quantity = quantity_by_payment(payment, final_amortization_rub)
    return AccountOperation(
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


def virtual_sells(
    positions: list[PortfolioPosition], now: datetime
) -> list[AccountOperation]:
    """Sells open bond positions at the market price to close their histories."""
    operations: list[AccountOperation] = []
    for pos in positions:
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
