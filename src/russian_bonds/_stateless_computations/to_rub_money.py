from t_tech.invest import MoneyValue

from russian_bonds._entities.rub_money import RubMoney
from russian_bonds._stateless_computations.money_to_float import money_to_float


def to_rub_money(money: MoneyValue) -> RubMoney:
    # validation rejects any currency but rubles
    return RubMoney.model_validate(
        {"currency": money.currency, "amount": money_to_float(money)}
    )
