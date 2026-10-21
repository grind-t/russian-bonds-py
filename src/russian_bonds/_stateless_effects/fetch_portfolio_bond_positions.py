from t_tech.invest.async_services import AsyncServices

from russian_bonds._entities.portfolio_bond_position import PortfolioBondPosition
from russian_bonds._stateless_computations.to_portfolio_bond_position import (
    to_portfolio_bond_position,
)


async def fetch_portfolio_bond_positions(
    client: AsyncServices, account_id: str
) -> list[PortfolioBondPosition]:
    portfolio = await client.operations.get_portfolio(account_id=account_id)
    return [
        to_portfolio_bond_position(pos)
        for pos in portfolio.positions
        if pos.instrument_type == "bond"
    ]
