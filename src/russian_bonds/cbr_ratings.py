import re
from typing import Literal

# ported from @grind-t/cbr-ratings
Prediction = Literal["STA", "POS", "NEG", "DEV"]
Kra = Literal["AKRA", "NKR", "EXPERT_RA", "NRA"]

RATING_SCALE = (
    "D",
    "C",
    "CC-",
    "CC",
    "CC+",
    "CCC-",
    "CCC",
    "CCC+",
    "B-",
    "B",
    "B+",
    "BB-",
    "BB",
    "BB+",
    "BBB-",
    "BBB",
    "BBB+",
    "A-",
    "A",
    "A+",
    "AA-",
    "AA",
    "AA+",
    "AAA",
)

_RATING_RE = re.compile(r"[A-D]{1,3}[+-]?", re.IGNORECASE)
_PREDICTION_RE = re.compile(r"^([A-Z]+)")
_PREDICTIONS: tuple[Prediction, ...] = ("STA", "POS", "NEG", "DEV")


def rating_value_to_number(value: str) -> int | None:
    match = _RATING_RE.search(value)
    if match is None or match[0] not in RATING_SCALE:
        return None
    return RATING_SCALE.index(match[0])


def convert_prediction(value: str | None) -> Prediction | None:
    match = _PREDICTION_RE.match(value or "")
    code = match[1] if match else ""
    return next((p for p in _PREDICTIONS if p == code), None)
