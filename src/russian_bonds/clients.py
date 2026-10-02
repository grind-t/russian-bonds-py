from dataclasses import dataclass

import httpx
from t_tech.invest.async_services import AsyncServices


@dataclass(frozen=True)
class Clients:
    t_invest: AsyncServices
    moex: httpx.AsyncClient
