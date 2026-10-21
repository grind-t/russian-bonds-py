from pydantic import BaseModel, Field

from russian_bonds._entities.rub_money import RubMoney


class PortfolioBondPosition(BaseModel):
    ticker: str = Field(min_length=1)
    quantity: int
    average_price: RubMoney
    current_price: RubMoney
    current_nkd: RubMoney
