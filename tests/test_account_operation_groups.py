from datetime import UTC, datetime

from t_tech.invest import OperationType

from russian_bonds.operations.account_operation_groups import (
    group_account_operations_by_ticker,
)
from russian_bonds.operations.account_operations import AccountOperation

BUY = OperationType.OPERATION_TYPE_BUY
SELL = OperationType.OPERATION_TYPE_SELL
COUPON = OperationType.OPERATION_TYPE_COUPON


def _op(
    id_: str, ticker: str, type_: OperationType = BUY, quantity_delta: int = 1
) -> AccountOperation:
    return AccountOperation(
        id=id_,
        parent_operation_id="",
        ticker=ticker,
        name="Операция",
        description="Операция с ценными бумагами",
        type=type_,
        payment=-1000.0,
        quantity_delta=quantity_delta,
        date=datetime(2026, 1, 1, tzinfo=UTC),
        virtual=False,
    )


def test_groups_by_ticker_preserving_order():
    operations = (_op("a1", "A"), _op("b1", "B"), _op("a2", "A"))
    grouped = group_account_operations_by_ticker(operations)
    assert {
        ticker: [op.id for op in group.operations] for ticker, group in grouped.items()
    } == {
        "A": ["a1", "a2"],
        "B": ["b1"],
    }


def test_sums_quantity_deltas_per_ticker():
    operations = (
        _op("a1", "A", BUY, 10),
        _op("a2", "A", COUPON, 0),
        _op("a3", "A", SELL, -4),
        _op("b1", "B", BUY, 5),
        _op("b2", "B", SELL, -5),
    )
    grouped = group_account_operations_by_ticker(operations)
    assert {ticker: group.net_quantity for ticker, group in grouped.items()} == {
        "A": 6,
        "B": 0,
    }


def test_empty_operations():
    assert group_account_operations_by_ticker(()) == {}
