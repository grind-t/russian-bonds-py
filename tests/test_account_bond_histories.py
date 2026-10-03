from datetime import UTC, datetime

import httpx
from t_tech.invest import OperationType

from russian_bonds.account_bond_histories import (
    get_account_bond_histories_from_operations,
)
from russian_bonds.bonds import Bond
from russian_bonds.operations.account_operations import AccountOperation

BUY = OperationType.OPERATION_TYPE_BUY
COUPON = OperationType.OPERATION_TYPE_COUPON


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


async def test_groups_operations_by_ticker(monkeypatch):
    async def fake_fetch_from_moex(ticker: str, client: httpx.AsyncClient) -> Bond:
        return Bond(ticker=ticker, face_value=1000.0, face_unit="RUB")

    monkeypatch.setattr(Bond, "fetch_from_moex", fake_fetch_from_moex)
    a1, b1, a2 = _op("a1", "A", BUY), _op("b1", "B", BUY), _op("a2", "A", COUPON)

    async with httpx.AsyncClient() as client:
        histories = await get_account_bond_histories_from_operations(
            [a1, b1, a2], client
        )

    assert list(histories) == ["A", "B"]
    assert histories["A"].bond.ticker == "A"
    assert histories["A"].operations == [a1, a2]
    assert histories["B"].bond.ticker == "B"
    assert histories["B"].operations == [b1]


async def test_empty_operations_give_empty_dict():
    async with httpx.AsyncClient() as client:
        assert await get_account_bond_histories_from_operations([], client) == {}
