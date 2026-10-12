from typing import Self

from pydantic import AwareDatetime, BaseModel, Field, model_validator
from t_tech.invest import OperationType


class AccountOperation(BaseModel):
    id: str = Field(min_length=1)
    parent_operation_id: str
    ticker: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    type: OperationType
    payment: float = Field(allow_inf_nan=False)
    quantity_delta: int
    date: AwareDatetime
    virtual: bool

    @model_validator(mode="after")
    def _check_fee_parent(self) -> Self:
        if (
            self.type == OperationType.OPERATION_TYPE_BROKER_FEE
            and not self.parent_operation_id
        ):
            raise ValueError(f"No parent operation for fee {self.id} of {self.ticker}")
        return self
