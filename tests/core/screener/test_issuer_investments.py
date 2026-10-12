from t_tech.invest import MoneyValue, PortfolioPosition, Quotation

from russian_bonds._core.screener.issuer_investments import build_issuer_investments
from russian_bonds._core.screener.screener_bond import ScreenerBond


def _bond(isin: str, issuer_inn: str | None) -> ScreenerBond:
    # only the fields the issuer investments read
    return ScreenerBond.model_construct(isin=isin, issuer_inn=issuer_inn)


def position(ticker: str, quantity: int, price: float, type_: str = "bond"):
    units = int(price)
    nano = round((price - units) * 1e9)
    return PortfolioPosition(
        ticker=ticker,
        instrument_type=type_,
        quantity=Quotation(units=quantity, nano=0),
        average_position_price=MoneyValue(currency="rub", units=units, nano=nano),
    )


def test_issuer_investments():
    bonds = [
        _bond("A1", issuer_inn="1"),
        _bond("A2", issuer_inn="1"),
        _bond("B1", issuer_inn="2"),
        _bond("NO_INN", issuer_inn=None),
    ]
    positions = [
        position("A1", 10, 1000.5),
        position("A2", 5, 990.0),
        position("B1", 1, 1010.0),
        position("NO_INN", 3, 1000.0),
        position("NOT_LISTED", 2, 1000.0),
        position("A1", 100, 50.0, type_="share"),
    ]
    assert build_issuer_investments(positions=positions, bonds=bonds) == {
        "1": 10 * 1000.5 + 5 * 990.0,
        "2": 1010.0,
    }
