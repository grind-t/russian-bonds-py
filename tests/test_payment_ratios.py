from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from t_tech.invest import OperationType

from russian_bonds.operations.payment_ratios import get_payment_ratios

BOND_REPAYMENT_FULL = OperationType.OPERATION_TYPE_BOND_REPAYMENT_FULL
BUY = OperationType.OPERATION_TYPE_BUY
BROKER_FEE = OperationType.OPERATION_TYPE_BROKER_FEE
SELL = OperationType.OPERATION_TYPE_SELL
COUPON = OperationType.OPERATION_TYPE_COUPON

T0 = datetime(2026, 1, 1, tzinfo=UTC)


@dataclass
class Op:
    id: str
    type: OperationType
    quantity_delta: int
    date: datetime
    parent_operation_id: str = ""
    ticker: str = "A"


def day(n: int) -> datetime:
    return T0 + timedelta(days=n)


def test_closed_history_is_counted_fully():
    operations = [
        Op("buy", BUY, 10, day(0)),
        Op("coupon", COUPON, 0, day(1)),
        Op("sell", SELL, -10, day(2)),
    ]
    assert get_payment_ratios(operations) == {"buy": 1.0, "coupon": 1.0, "sell": 1.0}


def test_counts_only_bonds_bought_in_window():
    # 5 held before the window, 5 bought in it
    operations = [
        Op("coupon-1", COUPON, 0, day(0)),
        Op("buy", BUY, 5, day(1)),
        Op("coupon-2", COUPON, 0, day(2)),
        Op("sell", SELL, -10, day(3)),
    ]
    assert get_payment_ratios(operations) == {
        "coupon-1": 0.0,
        "buy": 1.0,
        "coupon-2": 0.5,
        "sell": 0.5,
    }


def test_sells_keep_ratio():
    operations = [
        Op("buy", BUY, 5, day(0)),
        Op("sell", SELL, -4, day(1)),
        Op("coupon-1", COUPON, 0, day(2)),
        Op("repayment", BOND_REPAYMENT_FULL, -6, day(3)),
        # coupon paid after the position is closed
        Op("coupon-2", COUPON, 0, day(4)),
    ]
    assert get_payment_ratios(operations) == {
        "buy": 1.0,
        "sell": 0.5,
        "coupon-1": 0.5,
        "repayment": 0.5,
        "coupon-2": 0.5,
    }


def test_rebuy_after_close_starts_over():
    operations = [
        Op("sell-1", SELL, -5, day(0)),
        Op("buy", BUY, 5, day(1)),
        Op("sell-2", SELL, -5, day(2)),
    ]
    assert get_payment_ratios(operations) == {"sell-1": 0.0, "buy": 1.0, "sell-2": 1.0}


def test_sorts_newest_first_operations():
    operations = [
        Op("sell", SELL, -10, day(3)),
        Op("coupon", COUPON, 0, day(2)),
        Op("buy", BUY, 5, day(1)),
    ]
    assert get_payment_ratios(operations) == {"sell": 0.5, "coupon": 0.5, "buy": 1.0}


def test_fee_takes_ratio_of_its_deal():
    operations = [
        Op("buy", BUY, 5, day(0)),
        Op("buy-fee", BROKER_FEE, 0, day(0), parent_operation_id="buy"),
        Op("sell", SELL, -10, day(1)),
        Op("sell-fee", BROKER_FEE, 0, day(1), parent_operation_id="sell"),
        Op("old-fee", BROKER_FEE, 0, day(0), parent_operation_id="old-buy"),
    ]
    assert get_payment_ratios(operations) == {
        "buy": 1.0,
        "buy-fee": 1.0,
        "sell": 0.5,
        "sell-fee": 0.5,
        "old-fee": 0.0,
    }
