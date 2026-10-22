from t_tech.invest import PortfolioPosition
from t_tech.invest.utils import quotation_to_decimal

from russian_bonds._entities.account_position import AccountPosition
from russian_bonds._stateless_computations.to_rub_money import to_rub_money


def to_account_position(position: PortfolioPosition) -> AccountPosition:
    # validation rejects a fractional quantity
    return AccountPosition.model_validate(
        {
            "ticker": position.ticker,
            "quantity": quotation_to_decimal(position.quantity),
            "average_price": to_rub_money(position.average_position_price),
            "current_price": to_rub_money(position.current_price),
            "current_nkd": to_rub_money(position.current_nkd),
        }
    )
