from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from t_tech.invest import OperationType

from russian_bonds._core.cash_flows.account_operation import (
    AccountOperation,
    group_operations_by_ticker,
)

BUY = OperationType.OPERATION_TYPE_BUY
COUPON = OperationType.OPERATION_TYPE_COUPON


def test_fee_without_parent_raises():
    with pytest.raises(ValidationError, match="No parent operation"):
        AccountOperation(
            id="fee",
            parent_operation_id="",
            ticker="A",
            name="Комиссия",
            description="Удержание комиссии",
            type=OperationType.OPERATION_TYPE_BROKER_FEE,
            payment=-1.0,
            quantity_delta=0,
            date=datetime(2026, 1, 1, tzinfo=UTC),
            virtual=False,
        )


def _op(id_: str, ticker: str, type_: OperationType) -> AccountOperation:
    return AccountOperation(
        id=id_,
        parent_operation_id="",
        ticker=ticker,
        name="Операция",
        description="Операция с ценными бумагами",
        type=type_,
        payment=-1000.0,
        quantity_delta=0,
        date=datetime(2026, 1, 1, tzinfo=UTC),
        virtual=False,
    )


def test_groups_operations_by_ticker():
    a1, b1, a2 = _op("a1", "A", BUY), _op("b1", "B", BUY), _op("a2", "A", COUPON)
    assert group_operations_by_ticker([a1, b1, a2]) == {"A": [a1, a2], "B": [b1]}
