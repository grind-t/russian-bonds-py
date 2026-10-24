from t_tech.invest import MoneyValue
from t_tech.invest.utils import money_to_decimal

from russian_bonds._entities.rub_money import RubMoney


def to_rub_money(money: MoneyValue) -> RubMoney:
    # validation rejects any currency but rubles
    return RubMoney.model_validate(
        {"currency": money.currency, "amount": money_to_decimal(money)}
    )
