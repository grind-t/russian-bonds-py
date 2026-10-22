from t_tech.invest.async_services import AsyncServices

from russian_bonds._entities.account_position import AccountPosition
from russian_bonds._stateless_computations.to_account_position import (
    to_account_position,
)


async def fetch_account_positions(
    client: AsyncServices, account_id: str
) -> list[AccountPosition]:
    portfolio = await client.operations.get_portfolio(account_id=account_id)
    return [
        to_account_position(pos)
        for pos in portfolio.positions
        if pos.instrument_type == "bond"
    ]
