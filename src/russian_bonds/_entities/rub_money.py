from typing import Literal

from pydantic import BaseModel, Field


class RubMoney(BaseModel):
    currency: Literal["rub"] = "rub"
    amount: float = Field(allow_inf_nan=False)
