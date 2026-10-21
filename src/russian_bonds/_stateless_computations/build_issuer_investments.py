from t_tech.invest import PortfolioPosition
from t_tech.invest.utils import money_to_decimal, quotation_to_decimal

from russian_bonds._entities.screener_bond import ScreenerBond


def build_issuer_investments(
    *, positions: list[PortfolioPosition], bonds: list[ScreenerBond]
) -> dict[str, float]:
    # sums prices as is, without converting currencies
    issuer_inn_by_isin = {bond.isin: bond.issuer_inn for bond in bonds}
    result: dict[str, float] = {}
    for pos in positions:
        if pos.instrument_type != "bond":
            continue
        # t-invest bond tickers are isins
        issuer_inn = issuer_inn_by_isin.get(pos.ticker)
        if issuer_inn is None:
            continue
        investment = quotation_to_decimal(pos.quantity) * money_to_decimal(
            pos.average_position_price
        )
        result[issuer_inn] = result.get(issuer_inn, 0.0) + float(investment)
    return result
