from dataclasses import dataclass
from datetime import datetime

from t_tech.invest import OperationType


@dataclass(frozen=True)
class CashFlow:
    ticker: str
    bond_name: str
    operation_name: str
    description: str
    type: OperationType
    payment: float
    face_unit: str
    date: datetime
    virtual: bool
