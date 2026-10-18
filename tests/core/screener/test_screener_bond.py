from datetime import date, timedelta

from russian_bonds._core.screener.screener_bond import ScreenerBond

TODAY = date(2026, 1, 1)


def screener_bond(**fields) -> ScreenerBond:
    # a bond that fits the ruble screener, so each test breaks one condition
    defaults = {
        "isin": "RU000A000001",
        "name": "Облигация",
        "maturity_date": TODAY + timedelta(days=365),
        "ytm": 20.0,
        "last_price": None,
        "best_offer": None,
        "rating_t_invest": None,
        "rating_akra": 19,
        "rating_nkr": None,
        "rating_expert_ra": None,
        "rating_nra": None,
        "rating_ifrs": None,
        "prediction_akra": None,
        "prediction_nkr": None,
        "prediction_expert_ra": None,
        "prediction_nra": None,
        "prediction_ifrs": None,
        "nominal": 1000.0,
        "currency": "rub",
        "sector": "financial",
        "issuer_inn": "7700000001",
        "is_floater": False,
        "has_amortization": False,
        "has_offer": False,
        "for_qual": False,
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
    no_akra = {"rating_akra": None}
    cases = {
        "no rating": (no_akra, False),
        "high rating with stable outlook": (
            {"rating_akra": 18, "prediction_akra": "STA"},
            True,
        ),
        "high rating with negative outlook": (
            {"rating_akra": 18, "prediction_akra": "NEG"},
            False,
        ),
        "medium rating with positive outlook": (
            {"rating_akra": 16, "prediction_akra": "POS"},
            True,
        ),
        "medium rating under review": (
            {"rating_akra": 16, "prediction_akra": "DEV"},
            False,
        ),
        # a missing outlook counts as the best one the rating allows
        "low rating without outlook": ({"rating_akra": 15}, True),
        "low rating with stable outlook": (
            {"rating_akra": 15, "prediction_akra": "STA"},
            False,
        ),
        "low rating with positive outlook": (
            {"rating_akra": 15, "prediction_akra": "POS"},
            True,
        ),
        "too low rating": ({"rating_akra": 14}, False),
        "top nkr rating with negative outlook": (
            no_akra | {"rating_nkr": 19, "prediction_nkr": "NEG"},
            True,
        ),
        "expert ra rating": (no_akra | {"rating_expert_ra": 17}, True),
        "nra rating": (no_akra | {"rating_nra": 16, "prediction_nra": "STA"}, True),
        "acceptable t-invest rating": (no_akra | {"rating_t_invest": 2}, True),
        "poor t-invest rating": (no_akra | {"rating_t_invest": 1}, False),
        # an ifrs rating alone is enough
        "acceptable ifrs rating alone": (no_akra | {"rating_ifrs": 15}, True),
        "poor ifrs rating alone": (no_akra | {"rating_ifrs": 14}, False),
        # a poor ifrs rating rules out good agency ratings
        "poor ifrs rating with agency rating": (
            {"rating_ifrs": 16, "prediction_ifrs": "NEG"},
            False,
        ),
        "top ifrs rating with negative outlook": (
            {"rating_ifrs": 19, "prediction_ifrs": "NEG"},
            True,
        ),
    }
    for name, (ratings, expected) in cases.items():
        with subtests.test(name):
            assert screener_bond(**ratings).is_rub_candidate(0, TODAY) is expected
