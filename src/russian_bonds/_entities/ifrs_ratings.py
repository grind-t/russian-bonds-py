from cbr_ratings import Prediction
from pydantic import BaseModel


class _IfrsRating(BaseModel):
    value: int | None = None
    outlook: Prediction | None = None


IfrsRatings = dict[str, _IfrsRating]  # keyed by inn
