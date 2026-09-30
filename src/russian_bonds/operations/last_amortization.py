import httpx
from moex import MoexBondAmortization, get_moex_bond_amortizations


# the last amortization is the final repayment
async def get_last_amortization(
    ticker: str, *, client: httpx.AsyncClient | None = None
) -> MoexBondAmortization | None:
    amortizations = await get_moex_bond_amortizations(ticker, client=client)
    return amortizations[-1] if amortizations else None
