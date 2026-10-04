from typing import Self

import httpx
from moex import get_moex_security_description
from pydantic import BaseModel, Field


class Bond(BaseModel):
    ticker: str = Field(min_length=1)
    name: str = Field(min_length=1)
    face_value: float = Field(allow_inf_nan=False)
    face_unit: str = Field(min_length=1)

    @classmethod
    async def fetch_from_moex(cls, ticker: str, client: httpx.AsyncClient) -> Self:
        description = await get_moex_security_description(ticker, client=client)
        return cls.model_validate(
            {
                "ticker": ticker,
                "name": description.SHORTNAME,
                "face_value": description.FACEVALUE,
                "face_unit": description.FACEUNIT,
            }
        )
