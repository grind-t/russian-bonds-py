from t_tech.invest import PortfolioPosition
from t_tech.invest.async_services import AsyncServices


async def get_account_bonds(
    client: AsyncServices, account_id: str
) -> list[PortfolioPosition]:
    portfolio = await client.operations.get_portfolio(account_id=account_id)
    return [pos for pos in portfolio.positions if pos.instrument_type == "bond"]
