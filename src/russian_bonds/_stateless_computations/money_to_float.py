from t_tech.invest import MoneyValue
from t_tech.invest.utils import money_to_decimal


def money_to_float(money: MoneyValue) -> float:
    return float(money_to_decimal(money))
