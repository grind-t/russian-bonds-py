from datetime import date, timedelta

import pytest
import time_machine
from t_tech.invest import MoneyValue, PortfolioPosition, Quotation

from russian_bonds.screener import ScreenerBond, build_issuer_investments

TODAY = date(2026, 1, 1)


def screener_bond(**fields) -> ScreenerBond:
    # a bond that fits the ruble screener, so each test breaks one condition
    defaults = dict(
        isin="RU000A000001",
        name="Облигация",
        maturity_date=TODAY + timedelta(days=365),
        ytm=20.0,
        rating_t_invest=None,
        rating_akra=19,
        rating_nkr=None,
        rating_expert_ra=None,
        rating_nra=None,
        rating_ifrs=None,
        prediction_akra=None,
        prediction_nkr=None,
        prediction_expert_ra=None,
        prediction_nra=None,
        prediction_ifrs=None,
        nominal=1000.0,
        currency="rub",
        sector="financial",
        issuer_inn="7700000001",
        is_floater=False,
        has_amortization=False,
        has_offer=False,
        for_qual=False,
    )
    return ScreenerBond.model_validate(defaults | fields)


@pytest.fixture(autouse=True)
def frozen_today():
    with time_machine.travel(TODAY, tick=False):
        yield


@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        ({}, True),
        ({"currency": "usd"}, False),
        ({"ytm": 15.5}, True),
        ({"ytm": 15.4}, False),
        ({"ytm": None}, False),
        ({"has_offer": True}, False),
        ({"maturity_date": None}, False),
        ({"maturity_date": TODAY + timedelta(days=91)}, False),
        ({"maturity_date": TODAY + timedelta(days=92)}, True),
        ({"maturity_date": TODAY + timedelta(days=729)}, True),
        ({"maturity_date": TODAY + timedelta(days=730)}, False),
        # a floater maturing in 400 days needs 15.5 + 400 * 0.00275 = 16.6
        (
            {"is_floater": True, "maturity_date": TODAY + timedelta(400), "ytm": 16.6},
            True,
        ),
        (
            {"is_floater": True, "maturity_date": TODAY + timedelta(400), "ytm": 16.5},
            False,
        ),
    ],
)
def test_rub_candidate(fields, expected):
    assert screener_bond(**fields).is_rub_candidate(0) is expected


def test_rub_candidate_issuer_investment_limit():
    bond = screener_bond()
    assert bond.is_rub_candidate(99_999.99)
    assert not bond.is_rub_candidate(100_000)


@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        ({"currency": "usd", "ytm": 7.0}, True),
        ({"currency": "cny", "ytm": 6.9}, False),
        ({"currency": "rub", "ytm": 20.0}, False),
        ({"currency": "usd", "has_offer": True}, False),
        ({"currency": "usd", "maturity_date": TODAY + timedelta(days=30)}, False),
    ],
)
def test_foreign_currency_candidate(fields, expected):
    assert screener_bond(**fields).is_foreign_currency_candidate() is expected


@pytest.mark.parametrize(
    ("ratings", "expected"),
    [
        ({"rating_akra": None}, False),
        ({"rating_akra": 18}, True),
        ({"rating_akra": 18, "prediction_akra": "STA"}, True),
        ({"rating_akra": 18, "prediction_akra": "NEG"}, False),
        ({"rating_akra": 16, "prediction_akra": "POS"}, True),
        ({"rating_akra": 16, "prediction_akra": "DEV"}, False),
        ({"rating_akra": 15}, True),
        ({"rating_akra": 15, "prediction_akra": "STA"}, False),
        ({"rating_akra": 15, "prediction_akra": "POS"}, True),
        ({"rating_akra": 14}, False),
        ({"rating_akra": None, "rating_nkr": 19, "prediction_nkr": "NEG"}, True),
        ({"rating_akra": None, "rating_expert_ra": 17}, True),
        ({"rating_akra": None, "rating_nra": 16, "prediction_nra": "STA"}, True),
        ({"rating_akra": None, "rating_t_invest": 2}, True),
        ({"rating_akra": None, "rating_t_invest": 1}, False),
        # an ifrs rating alone is enough
        ({"rating_akra": None, "rating_ifrs": 15}, True),
        ({"rating_akra": None, "rating_ifrs": 14}, False),
        # a poor ifrs rating rules out good agency ratings
        ({"rating_ifrs": 16, "prediction_ifrs": "NEG"}, False),
        ({"rating_ifrs": 19, "prediction_ifrs": "NEG"}, True),
    ],
)
def test_ratings(ratings, expected):
    assert screener_bond(**ratings).is_rub_candidate(0) is expected


def position(ticker: str, quantity: int, price: float, type_: str = "bond"):
    units = int(price)
    nano = round((price - units) * 1e9)
    return PortfolioPosition(
        ticker=ticker,
        instrument_type=type_,
        quantity=Quotation(units=quantity, nano=0),
        average_position_price=MoneyValue(currency="rub", units=units, nano=nano),
    )


def test_issuer_investments():
    bonds = [
        screener_bond(isin="A1", issuer_inn="1"),
        screener_bond(isin="A2", issuer_inn="1"),
        screener_bond(isin="B1", issuer_inn="2"),
        screener_bond(isin="NO_INN", issuer_inn=None),
    ]
    positions = [
        position("A1", 10, 1000.5),
        position("A2", 5, 990.0),
        position("B1", 1, 1010.0),
        position("NO_INN", 3, 1000.0),
        position("NOT_LISTED", 2, 1000.0),
        position("A1", 100, 50.0, type_="share"),
    ]
    assert build_issuer_investments(positions=positions, bonds=bonds) == {
        "1": 10 * 1000.5 + 5 * 990.0,
        "2": 1010.0,
    }
