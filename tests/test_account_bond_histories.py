from datetime import UTC, datetime

from t_tech.invest import OperationType

from russian_bonds.account_bond_histories import AccountBondHistory
from russian_bonds.bonds import Bond
from russian_bonds.operations.account_operations import AccountOperation

BUY = OperationType.OPERATION_TYPE_BUY
SELL = OperationType.OPERATION_TYPE_SELL
COUPON = OperationType.OPERATION_TYPE_COUPON


def _op(id_: str, type_: OperationType, quantity_delta: int) -> AccountOperation:
    return AccountOperation(
        id=id_,
        parent_operation_id="",
        ticker="A",
        name="Операция",
        description="Операция с ценными бумагами",
        type=type_,
        payment=-1000.0,
        quantity_delta=quantity_delta,
        date=datetime(2026, 1, 1, tzinfo=UTC),
        virtual=False,
    )


def test_sums_quantity_deltas():
    history = AccountBondHistory(
        bond=Bond(ticker="A", face_value=1000.0, face_unit="RUB"),
        operations=[_op("a1", BUY, 10), _op("a2", COUPON, 0), _op("a3", SELL, -4)],
    )
    assert history.net_quantity == 6
