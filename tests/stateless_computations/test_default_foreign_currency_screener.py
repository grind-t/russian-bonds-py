from datetime import timedelta

from factories import TODAY, screener_bond

from russian_bonds._stateless_computations.default_foreign_currency_screener import (
    default_foreign_currency_screener,
)


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
                default_foreign_currency_screener(screener_bond(**fields), TODAY)
                is expected
            )
