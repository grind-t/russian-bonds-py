# grind-t-russian-bonds

Russian bonds analytics on top of the [T-Invest API](https://developer.tbank.ru/invest/)
and the [MOEX ISS API](https://iss.moex.com/iss/reference/).
Python port of [`@grind-t/russian-bonds`](https://github.com/grind-t/russian-bonds).

## Installation

The official T-Invest SDK (`t-tech-investments`) is published only to the T-Bank
package index, which is configured in `pyproject.toml`:

```sh
uv sync
```

### Russian Trusted CA

The index certificate is issued by the Ministry of Digital Development's Russian Trusted CA,
which is not in the default trust stores. The server does not send the intermediate
certificate, so both the root and the 2024 SSL sub CA are needed
(the sub CA published on Gosuslugi is an older one and does not match).

On Ubuntu/Debian:

```sh
sudo curl -fsSL -o /usr/local/share/ca-certificates/russian_trusted_root_ca.crt \
  https://gu-st.ru/content/lending/russian_trusted_root_ca_pem.crt
sudo curl -fsSL -o /usr/local/share/ca-certificates/russian_trusted_sub_ca_2024.crt \
  http://nuc-cdp.digital.gov.ru/cdp/subca_ssl_rsa2024.crt
sudo update-ca-certificates
```

Check the SHA-256 fingerprints (`openssl x509 -noout -fingerprint -sha256 -in <file>`):

| Certificate | Valid until | SHA-256 |
| --- | --- | --- |
| Russian Trusted Root CA | 2032-02-27 | `D2:6D:2D:02:31:B7:C3:9F:92:CC:73:85:12:BA:54:10:35:19:E4:40:5D:68:B5:BD:70:3E:97:88:CA:8E:CF:31` |
| Russian Trusted Sub CA (SSL, 2024) | 2029-07-19 | `21:55:78:50:36:C9:00:DB:B5:F1:BB:2A:15:69:C8:0C:55:59:5B:D6:BF:94:86:7A:29:BB:DD:BC:7D:88:A3:F2` |

uv ships its own root certificates, so tell it to use the system store:

```sh
mkdir -p ~/.config/uv && echo 'system-certs = true' >> ~/.config/uv/uv.toml
```

(or set `UV_SYSTEM_CERTS=1`, or pass `--system-certs`).

## Usage

```python
import asyncio
from datetime import datetime, timedelta, timezone

from t_tech.invest import AsyncClient

from russian_bonds import get_account_bond_cash_flows


async def main():
    async with AsyncClient("<token>") as client:
        rows = await get_account_bond_cash_flows(
            client,
            "<account id>",
            from_=datetime.now(timezone.utc) - timedelta(days=730),
        )


asyncio.run(main())
```

## Functions

| Function | Description |
| --- | --- |
| `get_account_bond_cash_flows(client, account_id, from_=, to=)` | Bond cash flows of an account, closed with a virtual sell at market price |
| `get_account_bond_operations(client, account_id, from_=, to=)` | All bond operations of an account as `BondOperationItem` (SDK `OperationItem` + `ticker`) |
| `get_account_bonds(client, account_id)` | Bond positions of an account's portfolio |

`client` is the `AsyncServices` object returned by `async with AsyncClient(token)`.

## Development

```sh
uv run pytest -m "not e2e"
uv run --env-file .env pytest -m e2e   # needs T_INVEST_READONLY_TOKEN, T_INVEST_ACCOUNT_ID
uv run --env-file .env playground.py
```
