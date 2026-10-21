from t_tech.invest import PortfolioPosition
from t_tech.invest.async_services import AsyncServices


async def fetch_portfolio_positions(
    client: AsyncServices, account_id: str
) -> list[PortfolioPosition]:
    portfolio = await client.operations.get_portfolio(account_id=account_id)
    return portfolio.positions
