from datetime import UTC, datetime

import pytest
from t_tech.invest import MoneyValue, OperationType

from russian_bonds.operations.account_operations import BondOperationItem
from russian_bonds.operations.normalized_operations import (
    NormalizedOperation,
    NormalizedOperations,
)


async def test_fee_without_parent_raises():
    op = BondOperationItem(
        id="fee",
        parent_operation_id="",
        ticker="A",
        name="Комиссия",
        description="Удержание комиссии",
        type=OperationType.OPERATION_TYPE_BROKER_FEE,
        payment=MoneyValue(currency="rub", units=-1, nano=0),
        date=datetime(2026, 1, 1, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="No parent operation"):
        await NormalizedOperation.from_operation_item(
            op,
            moex_client=None,  # ty: ignore[invalid-argument-type]
        )


def _buy(id_: str) -> NormalizedOperation:
    return NormalizedOperation(
        id=id_,
        parent_operation_id="",
        ticker="A",
        name="Покупка",
        description="Покупка ценных бумаг",
        type=OperationType.OPERATION_TYPE_BUY,
        payment=-1000.0,
        quantity_delta=1,
        date=datetime(2026, 1, 1, tzinfo=UTC),
        virtual=False,
    )


def test_duplicate_ids_raise():
    with pytest.raises(ValueError, match="Duplicate operation id buy"):
        NormalizedOperations([_buy("buy"), _buy("buy")])


def test_unique_ids_pass():
    assert [op.id for op in NormalizedOperations([_buy("a"), _buy("b")])] == ["a", "b"]
