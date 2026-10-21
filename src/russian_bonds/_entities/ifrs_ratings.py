from cbr_ratings import Prediction
from pydantic import BaseModel, Field


class _IfrsRating(BaseModel):
    value: int | None = None
    prediction: Prediction | None = Field(default=None, alias="outlook")


IfrsRatings = dict[str, _IfrsRating]  # keyed by inn
