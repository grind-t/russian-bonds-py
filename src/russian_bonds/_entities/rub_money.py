from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_serializer


class RubMoney(BaseModel):
    currency: Literal["rub"] = "rub"
    amount: Decimal = Field(allow_inf_nan=False)

    @property
    def float_amount(self) -> float:
        return float(self.amount)

    @field_serializer("amount", when_used="json")
    def _serialize_amount(self, _: Decimal) -> float:
        return self.float_amount
