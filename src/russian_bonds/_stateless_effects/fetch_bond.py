import httpx
from moex import get_moex_security_description

from russian_bonds._entities.bond import Bond


async def fetch_bond(ticker: str, client: httpx.AsyncClient) -> Bond:
    description = await get_moex_security_description(ticker, client=client)
    # validation rejects the fields moex leaves empty
    return Bond.model_validate(
        {
            "ticker": ticker,
            "name": description.SHORTNAME,
            "face_unit": description.FACEUNIT,
        }
    )
