from pydantic import BaseModel, Field


class Bond(BaseModel):
    ticker: str = Field(min_length=1)
    name: str = Field(min_length=1)
    face_unit: str = Field(min_length=1)
