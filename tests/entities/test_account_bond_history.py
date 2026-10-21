from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from t_tech.invest import OperationType

from russian_bonds._entities.account_bond_history import AccountBondHistory
from russian_bonds._entities.account_operation import AccountOperation
from russian_bonds._entities.bond import Bond


def test_unclosed_position_raises():
    buy = AccountOperation(
        id="buy",
        parent_operation_id="",
        ticker="A",
        name="Покупка",
        description="Покупка ценных бумаг",
        type=OperationType.OPERATION_TYPE_BUY,
        payment=-600.0,
        quantity_delta=5,
        date=datetime(2026, 1, 1, tzinfo=UTC),
        virtual=False,
    )
    bond = Bond(ticker="A", name="A", face_unit="RUB")
    with pytest.raises(ValidationError, match="Unclosed position for A"):
        AccountBondHistory(bond=bond, operations=[buy])
