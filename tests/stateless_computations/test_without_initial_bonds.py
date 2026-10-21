from datetime import UTC, datetime, timedelta

from factories import account_operation, bond
from t_tech.invest import OperationType

from russian_bonds._entities.account_bond_history import AccountBondHistory
from russian_bonds._entities.account_operation import AccountOperation
from russian_bonds._stateless_computations.without_initial_bonds import (
    without_initial_bonds,
)

BOND_REPAYMENT_FULL = OperationType.OPERATION_TYPE_BOND_REPAYMENT_FULL
BROKER_FEE = OperationType.OPERATION_TYPE_BROKER_FEE
BUY = OperationType.OPERATION_TYPE_BUY
COUPON = OperationType.OPERATION_TYPE_COUPON
SELL = OperationType.OPERATION_TYPE_SELL
T0 = datetime(2026, 1, 1, tzinfo=UTC)


def _history_op(
    id_: str,
    type_: OperationType,
    quantity_delta: int,
    days: int,
    payment: float = 600.0,
    parent_operation_id: str = "",
) -> AccountOperation:
    return account_operation(
        id=id_,
        parent_operation_id=parent_operation_id,
        type=type_,
        payment={"amount": payment},
        quantity_delta=quantity_delta,
        date=T0 + timedelta(days=days),
    )


def _history(*operations: AccountOperation) -> AccountBondHistory:
    return AccountBondHistory(bond=bond(), operations=list(operations))


def _adjusted(history: AccountBondHistory) -> dict[str, tuple[float, int]]:
    adjusted = without_initial_bonds(history)
    assert adjusted.initial_bond_quantity == 0
    return {op.id: (op.payment.amount, op.quantity_delta) for op in adjusted.operations}


def test_history_without_initial_bonds_is_unchanged():
    history = _history(
        _history_op("buy", BUY, 10, 0, payment=-600.0),
        _history_op("coupon", COUPON, 0, 1),
        _history_op("sell", SELL, -10, 2),
    )
    assert without_initial_bonds(history) == history


def test_sells_consume_initial_bonds_first():
    # 5 held before the operations, 5 bought in them
    history = _history(
        _history_op("coupon-1", COUPON, 0, 0),
        _history_op("buy", BUY, 5, 1, payment=-600.0),
        _history_op("coupon-2", COUPON, 0, 2),
        _history_op("sell-1", SELL, -6, 3),
        _history_op("coupon-3", COUPON, 0, 4),
        _history_op("repayment", BOND_REPAYMENT_FULL, -4, 5),
        # coupon paid after the position is closed
        _history_op("coupon-4", COUPON, 0, 6),
    )
    assert _adjusted(history) == {
        "buy": (-600.0, 5),
        "coupon-2": (300.0, 0),
        "sell-1": (100.0, -1),
        "coupon-3": (600.0, 0),
        "repayment": (600.0, -4),
        "coupon-4": (600.0, 0),
    }


def test_rebuy_after_close_starts_over():
    history = _history(
        _history_op("sell-1", SELL, -5, 0),
        _history_op("buy", BUY, 5, 1, payment=-600.0),
        _history_op("sell-2", SELL, -5, 2),
    )
    assert _adjusted(history) == {"buy": (-600.0, 5), "sell-2": (600.0, -5)}


def test_ties_are_processed_in_order():
    history = _history(
        _history_op("sell-1", SELL, -5, 0),
        _history_op("buy", BUY, 5, 0, payment=-600.0),
        _history_op("sell-2", SELL, -5, 1),
    )
    assert _adjusted(history) == {"buy": (-600.0, 5), "sell-2": (600.0, -5)}


def test_fee_follows_its_deal():
    history = _history(
        _history_op("buy", BUY, 5, 0, payment=-600.0),
        _history_op("buy-fee", BROKER_FEE, 0, 0, -6.0, parent_operation_id="buy"),
        _history_op("sell", SELL, -10, 1),
        _history_op("sell-fee", BROKER_FEE, 0, 1, -6.0, parent_operation_id="sell"),
        _history_op("old-fee", BROKER_FEE, 0, 0, -6.0, parent_operation_id="old"),
    )
    assert _adjusted(history) == {
        "buy": (-600.0, 5),
        "buy-fee": (-6.0, 0),
        "sell": (300.0, -5),
        "sell-fee": (-3.0, 0),
    }
