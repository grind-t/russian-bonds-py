from russian_bonds._entities.account_position import AccountPosition
from russian_bonds._entities.screener_bond import ScreenerBond


def build_issuer_investments(
    *, positions: list[AccountPosition], bonds: list[ScreenerBond]
) -> dict[str, float]:
    """Rubles invested in each issuer."""
    issuer_inn_by_isin = {bond.isin: bond.issuer_inn for bond in bonds}
    result: dict[str, float] = {}
    for pos in positions:
        # t-invest bond tickers are isins
        issuer_inn = issuer_inn_by_isin.get(pos.ticker)
        if issuer_inn is None:
            continue
        investment = pos.quantity * pos.average_price.float_amount
        result[issuer_inn] = result.get(issuer_inn, 0.0) + investment
    return result
