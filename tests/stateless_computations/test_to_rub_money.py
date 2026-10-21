import pytest
from pydantic import ValidationError
from t_tech.invest import MoneyValue

from russian_bonds._entities.rub_money import RubMoney
from russian_bonds._stateless_computations.to_rub_money import to_rub_money


def test_to_rub_money_keeps_rubles():
    money = MoneyValue(currency="rub", units=1000, nano=500_000_000)
    assert to_rub_money(money) == RubMoney(amount=1000.5)


def test_to_rub_money_rejects_other_currencies():
    with pytest.raises(ValidationError):
        to_rub_money(MoneyValue(currency="usd", units=10, nano=0))
