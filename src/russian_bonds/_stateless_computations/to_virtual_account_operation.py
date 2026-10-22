from datetime import datetime

from t_tech.invest import OperationType

from russian_bonds._entities.account_operation import AccountOperation
from russian_bonds._entities.account_position import AccountPosition
from russian_bonds._entities.rub_money import RubMoney


def to_virtual_account_operation(
    position: AccountPosition, now: datetime
) -> AccountOperation:
    """Sells an open position at the market price to close its history."""
    price = position.current_price.amount + position.current_nkd.amount
    return AccountOperation(
        id=f"virtual:{position.ticker}",
        parent_operation_id="",
        ticker=position.ticker,
        name="Продажа",
        description="Виртуальная продажа по рыночной цене",
        type=OperationType.OPERATION_TYPE_SELL,
        payment=RubMoney(amount=price * position.quantity),
        quantity_delta=-position.quantity,
        date=now,
        virtual=True,
    )
