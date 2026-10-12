import httpx
from moex import get_moex_security_description

from russian_bonds._core.cash_flows.bond import Bond


async def fetch_bond(ticker: str, client: httpx.AsyncClient) -> Bond:
    description = await get_moex_security_description(ticker, client=client)
    # validation rejects the fields moex leaves empty
    return Bond.model_validate(
        {
            "ticker": ticker,
            "name": description.SHORTNAME,
            "face_value": description.FACEVALUE,
            "face_unit": description.FACEUNIT,
        }
    )
