from cbr_ratings import Prediction
from pydantic import BaseModel


class CreditRating(BaseModel):
    value: int | None
    prediction: Prediction | None
