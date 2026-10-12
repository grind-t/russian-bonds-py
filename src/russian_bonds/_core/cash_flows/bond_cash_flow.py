from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from t_tech.invest import OperationType

from russian_bonds._core.cash_flows.account_bond_history import AccountBondHistory


@dataclass(frozen=True)
class BondCashFlow:
    ticker: str
    bond_name: str
    name: str
    description: str
    type: OperationType
    value: float
    face_unit: str
    date: datetime
    virtual: bool


def bond_cash_flows(histories: Iterable[AccountBondHistory]) -> list[BondCashFlow]:
    """Cash flows of the bonds bought within the histories."""
    cash_flows: list[BondCashFlow] = []
    for history in histories:
        operations = history.without_initial_bonds().operations
        cash_flows.extend(
            BondCashFlow(
                ticker=op.ticker,
                bond_name=history.bond.name,
                name=op.name,
                description=op.description,
                type=op.type,
                value=op.payment,
                face_unit=history.bond.face_unit,
                date=op.date,
                virtual=op.virtual,
            )
            for op in operations
        )
    return cash_flows
