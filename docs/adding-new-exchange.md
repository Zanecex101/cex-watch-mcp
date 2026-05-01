# Adding a new exchange

A new adapter is ~80 lines. Here's the playbook.

## 1. Find the public endpoints you need

You need three things from the exchange's public API:

| Need | What you're looking for |
|---|---|
| List spot pairs | An `exchangeInfo` / `instruments` / `products` endpoint |
| Health check | A `ping` / `time` / `status` endpoint |
| Default fee | The published fee schedule for the entry tier |

All three should be **unauthenticated** and **free**. If they're not, this exchange isn't a fit.

## 2. Copy an existing adapter

Pick the one whose API style most resembles yours:

- REST + symbol array → copy `binance.py`
- REST + nested `data.list` → copy `bybit.py`
- REST + map-of-pairs → copy `kraken.py`

## 3. Implement the three abstract methods

```python
class MyExchangeAdapter(ExchangeAdapter):
    id = "myexchange"
    name = "My Exchange"
    base_url = "https://api.myexchange.com"

    async def list_spot_pairs(self) -> list[Listing]: ...
    async def get_status(self) -> ExchangeStatus: ...
    async def get_default_fee(self) -> FeeQuote: ...
```

For `get_default_fee`, **cite the exchange's published fee schedule URL in a comment**, since fees change over time and we need to know what to verify.

## 4. Register in `exchanges/__init__.py`

```python
from cex_watch_mcp.exchanges.myexchange import MyExchangeAdapter

ALL_ADAPTERS["myexchange"] = MyExchangeAdapter
```

## 5. Verify locally

```bash
cex-watch-snapshot
```

Check that your exchange shows up in the output and the pair count looks right.

## 6. PR

Title: `feat: add <exchange> adapter`. Include in the description:
- The endpoints you used (with links to docs)
- The published fee schedule URL
- Whether the exchange supports WebSocket (relevant for v0.3 work)
