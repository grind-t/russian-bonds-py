from dataclasses import dataclass
from datetime import datetime

from t_tech.invest import OperationType


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
