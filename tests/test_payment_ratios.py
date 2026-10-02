from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pytest

from russian_bonds.operations.payment_ratios import get_payment_ratios

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


@dataclass
class Op:
    id: str
    type: int
    quantity_done: int
    date: datetime
    parent_operation_id: str = ""
    ticker: str = "A"


def day(n: int) -> datetime:
    return T0 + timedelta(days=n)


def test_closed_history_is_counted_fully():
    operations = [
        Op("buy", 15, 10, day(0)),
        Op("coupon", 23, 0, day(1)),
        Op("sell", 22, 10, day(2)),
    ]
    assert get_payment_ratios(operations) == {"buy": 1.0, "coupon": 1.0, "sell": 1.0}


def test_counts_only_bonds_bought_in_window():
    # 5 held before the window, 5 bought in it
    operations = [
        Op("coupon-1", 23, 0, day(0)),
        Op("buy", 15, 5, day(1)),
        Op("coupon-2", 23, 0, day(2)),
        Op("sell", 22, 10, day(3)),
    ]
    assert get_payment_ratios(operations) == {
        "coupon-1": 0.0,
        "buy": 1.0,
        "coupon-2": 0.5,
        "sell": 0.5,
    }


def test_sells_keep_ratio():
    operations = [
        Op("buy", 15, 5, day(0)),
        Op("sell", 22, 4, day(1)),
        Op("coupon-1", 23, 0, day(2)),
        Op("repayment", 6, 6, day(3)),
        # coupon paid after the position is closed
        Op("coupon-2", 23, 0, day(4)),
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
        Op("sell-1", 22, 5, day(0)),
        Op("buy", 15, 5, day(1)),
        Op("sell-2", 22, 5, day(2)),
    ]
    assert get_payment_ratios(operations) == {"sell-1": 0.0, "buy": 1.0, "sell-2": 1.0}


def test_sorts_newest_first_operations():
    operations = [
        Op("sell", 22, 10, day(3)),
        Op("coupon", 23, 0, day(2)),
        Op("buy", 15, 5, day(1)),
    ]
    assert get_payment_ratios(operations) == {"sell": 0.5, "coupon": 0.5, "buy": 1.0}


def test_fee_takes_ratio_of_its_deal():
    operations = [
        Op("buy", 15, 5, day(0)),
        Op("buy-fee", 19, 0, day(0), parent_operation_id="buy"),
        Op("sell", 22, 10, day(1)),
        Op("sell-fee", 19, 0, day(1), parent_operation_id="sell"),
        Op("old-fee", 19, 0, day(0), parent_operation_id="old-buy"),
    ]
    assert get_payment_ratios(operations) == {
        "buy": 1.0,
        "buy-fee": 1.0,
        "sell": 0.5,
        "sell-fee": 0.5,
        "old-fee": 0.0,
    }


def test_fee_without_parent_raises():
    operations = [
        Op("buy", 15, 5, day(0)),
        Op("fee", 19, 0, day(0)),
        Op("sell", 22, 5, day(1)),
    ]
    with pytest.raises(ValueError, match="No parent operation"):
        get_payment_ratios(operations)
