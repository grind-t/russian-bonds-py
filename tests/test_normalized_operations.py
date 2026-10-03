from datetime import UTC, datetime

import pytest
from t_tech.invest import MoneyValue, OperationState, OperationType

from russian_bonds.operations import normalized_operations
from russian_bonds.operations.account_operations import BondOperationItem
from russian_bonds.operations.normalized_operations import (
    NormalizedOperation,
    get_normalized_operations,
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


def _buy(id_: str) -> BondOperationItem:
    return BondOperationItem(
        id=id_,
        ticker="A",
        name="Покупка",
        description="Покупка ценных бумаг",
        type=OperationType.OPERATION_TYPE_BUY,
        state=OperationState.OPERATION_STATE_EXECUTED,
        payment=MoneyValue(currency="rub", units=-1000, nano=0),
        quantity_done=1,
        date=datetime(2026, 1, 1, tzinfo=UTC),
    )


async def _normalize(
    monkeypatch: pytest.MonkeyPatch, items: list[BondOperationItem]
) -> list[NormalizedOperation]:
    async def fake_get_account_bond_operations(*_args):
        return items

    monkeypatch.setattr(
        normalized_operations,
        "get_account_bond_operations",
        fake_get_account_bond_operations,
    )
    return await get_normalized_operations(
        t_invest_client=None,  # ty: ignore[invalid-argument-type]
        moex_client=None,  # ty: ignore[invalid-argument-type]
        account_id="account",
    )


async def test_duplicate_ids_raise(monkeypatch: pytest.MonkeyPatch):
    with pytest.raises(ValueError, match="Duplicate operation ids"):
        await _normalize(monkeypatch, [_buy("buy"), _buy("buy")])


async def test_unique_ids_pass(monkeypatch: pytest.MonkeyPatch):
    operations = await _normalize(monkeypatch, [_buy("a"), _buy("b")])
    assert [op.id for op in operations] == ["a", "b"]
