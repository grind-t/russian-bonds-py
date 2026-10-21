from datetime import date, timedelta
from typing import Any

from cbr_ratings import KraCode, Prediction

from russian_bonds._entities.screener_bond import ScreenerBond

TODAY = date(2026, 1, 1)


def agency(
    code: KraCode, value: int, prediction: Prediction | None = None
) -> dict[str, Any]:
    return {"agency_ratings": {code: {"value": value, "prediction": prediction}}}


def ifrs(value: int, prediction: Prediction | None = None) -> dict[str, Any]:
    return {"ifrs_rating": {"value": value, "prediction": prediction}}


def screener_bond(**fields) -> ScreenerBond:
    # a bond that fits the ruble screener, so each test breaks one condition
    defaults = {
        "isin": "RU000A000001",
        "name": "Облигация",
        "maturity_date": TODAY + timedelta(days=365),
        "ytm": 20.0,
        "last_price": None,
        "best_ask_price": None,
        "t_invest_rating": None,
        **agency("AKRA", 19),
        "ifrs_rating": None,
        "face_value": 1000.0,
        "currency": "rub",
        "sector": "financial",
        "issuer_inn": "7700000001",
        "is_floater": False,
        "has_amortization": False,
        "has_offer": False,
        "is_for_qualified_investors": False,
    }
    return ScreenerBond.model_validate(defaults | fields)


def test_rub_candidate(subtests):
    floater = {"is_floater": True, "maturity_date": TODAY + timedelta(400)}
    cases = {
        "fits all filters": ({}, True),
        "non-ruble currency": ({"currency": "usd"}, False),
        "ytm at minimum": ({"ytm": 15.0}, True),
        "ytm below minimum": ({"ytm": 14.9}, False),
        "no ytm": ({"ytm": None}, False),
        "has offer": ({"has_offer": True}, False),
        "no maturity date": ({"maturity_date": None}, False),
        "matures too soon": ({"maturity_date": TODAY + timedelta(days=91)}, False),
        "matures soon enough": ({"maturity_date": TODAY + timedelta(days=92)}, True),
        "matures late enough": ({"maturity_date": TODAY + timedelta(days=729)}, True),
        "matures too late": ({"maturity_date": TODAY + timedelta(days=730)}, False),
        # a floater maturing in 400 days needs 15 + 400 * 0.00275 = 16.1
        "floater ytm at minimum": (floater | {"ytm": 16.1}, True),
        "floater ytm below minimum": (floater | {"ytm": 16.0}, False),
    }
    for name, (fields, expected) in cases.items():
        with subtests.test(name):
            assert screener_bond(**fields).is_rub_candidate(0, TODAY) is expected


def test_rub_candidate_issuer_investment_limit():
    bond = screener_bond()
    assert bond.is_rub_candidate(99_999.99, TODAY)
    assert not bond.is_rub_candidate(100_000, TODAY)


def test_foreign_currency_candidate(subtests):
    cases = {
        "ytm at minimum": ({"currency": "usd", "ytm": 7.0}, True),
        "ytm below minimum": ({"currency": "cny", "ytm": 6.9}, False),
        "ruble currency": ({"currency": "rub", "ytm": 20.0}, False),
        "has offer": ({"currency": "usd", "has_offer": True}, False),
        "matures too soon": (
            {"currency": "usd", "maturity_date": TODAY + timedelta(days=30)},
            False,
        ),
    }
    for name, (fields, expected) in cases.items():
        with subtests.test(name):
            assert (
                screener_bond(**fields).is_foreign_currency_candidate(TODAY) is expected
            )


def test_ratings(subtests):
    no_agency = {"agency_ratings": {}}
    cases = {
        "no rating": (no_agency, False),
        "high rating with stable prediction": (
            agency("AKRA", 18, "STA"),
            True,
        ),
        "high rating with negative prediction": (
            agency("AKRA", 18, "NEG"),
            False,
        ),
        "medium rating with positive prediction": (
            agency("AKRA", 16, "POS"),
            True,
        ),
        "medium rating under review": (
            agency("AKRA", 16, "DEV"),
            False,
        ),
        # a missing prediction counts as the best one the rating allows
        "low rating without prediction": (agency("AKRA", 15), True),
        "low rating with stable prediction": (
            agency("AKRA", 15, "STA"),
            False,
        ),
        "low rating with positive prediction": (
            agency("AKRA", 15, "POS"),
            True,
        ),
        "too low rating": (agency("AKRA", 14), False),
        "top nkr rating with negative prediction": (
            agency("NKR", 19, "NEG"),
            True,
        ),
        "expert ra rating": (agency("EXPERT_RA", 17), True),
        "nra rating": (agency("NRA", 16, "STA"), True),
        "acceptable t-invest rating": (
            no_agency | {"t_invest_rating": 2},
            True,
        ),
        "poor t-invest rating": (no_agency | {"t_invest_rating": 1}, False),
        # an ifrs rating alone is enough
        "acceptable ifrs rating alone": (no_agency | ifrs(15), True),
        "poor ifrs rating alone": (no_agency | ifrs(14), False),
        # a poor ifrs rating rules out good agency ratings
        "poor ifrs rating with agency rating": (
            ifrs(16, "NEG"),
            False,
        ),
        "top ifrs rating with negative prediction": (
            ifrs(19, "NEG"),
            True,
        ),
    }
    for name, (ratings, expected) in cases.items():
        with subtests.test(name):
            assert screener_bond(**ratings).is_rub_candidate(0, TODAY) is expected
