from cbr_ratings import Prediction
from pydantic import BaseModel, Field


class IfrsRating(BaseModel):
    value: int | None = None
    prediction: Prediction | None = Field(default=None, alias="outlook")
