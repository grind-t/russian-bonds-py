from datetime import timedelta

from factories import TODAY, screener_bond

from russian_bonds._stateless_computations.is_foreign_currency_candidate import (
    is_foreign_currency_candidate,
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
                is_foreign_currency_candidate(screener_bond(**fields), TODAY)
                is expected
            )
