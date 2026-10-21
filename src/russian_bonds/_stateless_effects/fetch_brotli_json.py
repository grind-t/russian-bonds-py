import brotli
import httpx
from pydantic import TypeAdapter


async def fetch_brotli_json[T](
    url: str, type_: type[T], client: httpx.AsyncClient
) -> T:
    response = await client.get(url)
    response.raise_for_status()
    return TypeAdapter(type_).validate_json(brotli.decompress(response.content))
