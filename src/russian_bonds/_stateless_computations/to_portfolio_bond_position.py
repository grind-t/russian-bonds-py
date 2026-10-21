from t_tech.invest import PortfolioPosition
from t_tech.invest.utils import quotation_to_decimal

from russian_bonds._entities.portfolio_bond_position import PortfolioBondPosition
from russian_bonds._stateless_computations.to_rub_money import to_rub_money


def to_portfolio_bond_position(position: PortfolioPosition) -> PortfolioBondPosition:
    # validation rejects a fractional quantity
    return PortfolioBondPosition.model_validate(
        {
            "ticker": position.ticker,
            "quantity": quotation_to_decimal(position.quantity),
            "average_price": to_rub_money(position.average_position_price),
            "current_price": to_rub_money(position.current_price),
            "current_nkd": to_rub_money(position.current_nkd),
        }
    )
