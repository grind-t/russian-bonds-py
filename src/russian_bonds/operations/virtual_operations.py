from datetime import datetime

from t_tech.invest import OperationType
from t_tech.invest.async_services import AsyncServices
from t_tech.invest.utils import money_to_decimal, quotation_to_decimal

from ..account_bonds import get_account_bonds
from .normalized_operations import NormalizedOperation


async def get_virtual_operations(
    client: AsyncServices, account_id: str, now: datetime
) -> list[NormalizedOperation]:
    operations: list[NormalizedOperation] = []
    for pos in await get_account_bonds(client, account_id):
        quantity_decimal = quotation_to_decimal(pos.quantity)
        if quantity_decimal != quantity_decimal.to_integral_value():
            raise ValueError(f"Fractional position quantity for {pos.ticker}")
        quantity = int(quantity_decimal)
        current_price = float(money_to_decimal(pos.current_price))
        current_nkd = float(money_to_decimal(pos.current_nkd))
        operations.append(
            NormalizedOperation(
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
