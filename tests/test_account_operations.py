from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from t_tech.invest import OperationType

from russian_bonds.operations.account_operations import (
    AccountOperation,
    group_account_operations_by_ticker,
)

BUY = OperationType.OPERATION_TYPE_BUY


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


def _op(id_: str, ticker: str) -> AccountOperation:
    return AccountOperation(
        id=id_,
        parent_operation_id="",
        ticker=ticker,
        name="Операция",
        description="Операция с ценными бумагами",
        type=BUY,
        payment=-1000.0,
        quantity_delta=1,
        date=datetime(2026, 1, 1, tzinfo=UTC),
        virtual=False,
    )


def test_groups_by_ticker_preserving_order():
    operations = (_op("a1", "A"), _op("b1", "B"), _op("a2", "A"))
    grouped = group_account_operations_by_ticker(operations)
    assert {ticker: [op.id for op in ops] for ticker, ops in grouped.items()} == {
        "A": ["a1", "a2"],
        "B": ["b1"],
    }


def test_empty_operations():
    assert group_account_operations_by_ticker(()) == {}
