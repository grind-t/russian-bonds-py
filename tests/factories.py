from datetime import UTC, date, datetime, timedelta
from typing import Any

from cbr_ratings import KraCode, Prediction
from t_tech.invest import OperationType

from russian_bonds._entities.account_operation import AccountOperation
from russian_bonds._entities.bond import Bond
from russian_bonds._entities.screener_bond import ScreenerBond

TODAY = date(2026, 1, 1)


def account_operation(**fields: Any) -> AccountOperation:
    defaults = {
        "id": "op",
        "parent_operation_id": "",
        "ticker": "A",
        "name": "Операция",
        "description": "Операция с ценными бумагами",
        "type": OperationType.OPERATION_TYPE_BUY,
        "payment": {"amount": -1000.0},
        "quantity_delta": 0,
        "date": datetime(2026, 1, 1, tzinfo=UTC),
        "virtual": False,
    }
    return AccountOperation.model_validate(defaults | fields)


def bond(**fields: Any) -> Bond:
    defaults = {"ticker": "A", "name": "A", "face_unit": "RUB"}
    return Bond.model_validate(defaults | fields)


def agency(
    code: KraCode, value: int, prediction: Prediction | None = None
) -> dict[str, Any]:
    return {"agency_ratings": {code: {"value": value, "prediction": prediction}}}


def ifrs(value: int, prediction: Prediction | None = None) -> dict[str, Any]:
    return {"ifrs_rating": {"value": value, "prediction": prediction}}


def screener_bond(**fields) -> ScreenerBond:
    # a bond that fits the ruble fixed screener, so each test breaks one condition
    defaults = {
        "isin": "RU000A000001",
        "name": "Облигация",
        "maturity_date": TODAY + timedelta(days=365),
        "ytm": 20.0,
        "ask_ytm": None,
        "g_spread": None,
        "duration": None,
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
