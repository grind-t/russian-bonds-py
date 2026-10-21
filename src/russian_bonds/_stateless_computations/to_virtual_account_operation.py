from datetime import datetime

from t_tech.invest import OperationType, PortfolioPosition
from t_tech.invest.utils import money_to_decimal, quotation_to_decimal
from toolkit.boolean import ensure

from russian_bonds._entities.account_operation import AccountOperation


def to_virtual_account_operation(
    position: PortfolioPosition, now: datetime
) -> AccountOperation:
    """Sells an open position at the market price to close its history."""
    quantity_decimal = quotation_to_decimal(position.quantity)
    ensure(
        quantity_decimal == quantity_decimal.to_integral_value(),
        f"Fractional position quantity for {position.ticker}",
    )
    quantity = int(quantity_decimal)
    current_price = float(money_to_decimal(position.current_price))
    current_nkd = float(money_to_decimal(position.current_nkd))
    return AccountOperation(
        id=f"virtual:{position.ticker}",
        parent_operation_id="",
        ticker=position.ticker,
        name="Продажа",
        description="Виртуальная продажа по рыночной цене",
        type=OperationType.OPERATION_TYPE_SELL,
        payment=(current_price + current_nkd) * quantity,
        quantity_delta=-quantity,
        date=now,
        virtual=True,
    )
