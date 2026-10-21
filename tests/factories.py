from datetime import UTC, datetime
from typing import Any

from t_tech.invest import OperationType

from russian_bonds._entities.account_operation import AccountOperation
from russian_bonds._entities.bond import Bond


def account_operation(**fields: Any) -> AccountOperation:
    defaults = {
        "id": "op",
        "parent_operation_id": "",
        "ticker": "A",
        "name": "Операция",
        "description": "Операция с ценными бумагами",
        "type": OperationType.OPERATION_TYPE_BUY,
        "payment": -1000.0,
        "quantity_delta": 0,
        "date": datetime(2026, 1, 1, tzinfo=UTC),
        "virtual": False,
    }
    return AccountOperation.model_validate(defaults | fields)


def bond(**fields: Any) -> Bond:
    defaults = {"ticker": "A", "name": "A", "face_unit": "RUB"}
    return Bond.model_validate(defaults | fields)
