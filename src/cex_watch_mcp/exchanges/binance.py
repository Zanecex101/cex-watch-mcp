"""Binance adapter — uses public spot REST API."""

from __future__ import annotations

import time

from cex_watch_mcp.exchanges.base import (
    ExchangeAdapter,
    ExchangeStatus,
    FeeQuote,
    Listing,
)


class BinanceAdapter(ExchangeAdapter):
    id = "binance"
    name = "Binance"
    base_url = "https://api.binance.com"

    async def list_spot_pairs(self) -> list[Listing]:
        r = await self.client.get(f"{self.base_url}/api/v3/exchangeInfo")
        r.raise_for_status()
        data = r.json()
        out: list[Listing] = []
        for s in data.get("symbols", []):
            if s.get("status") != "TRADING":
                continue
            out.append(
                Listing(
                    exchange=self.id,
                    symbol=s["symbol"],
                    base=s["baseAsset"],
                    quote=s["quoteAsset"],
                    status="trading",
                )
            )
        return out

    async def get_status(self) -> ExchangeStatus:
        t0 = time.monotonic()
        try:
            r = await self.client.get(f"{self.base_url}/api/v3/ping")
            r.raise_for_status()
            latency = int((time.monotonic() - t0) * 1000)
            pairs = await self.list_spot_pairs()
            return ExchangeStatus(
                exchange=self.id,
                healthy=True,
                api_latency_ms=latency,
                spot_pair_count=len(pairs),
            )
        except Exception as e:
            return ExchangeStatus(
                exchange=self.id,
                healthy=False,
                api_latency_ms=None,
                spot_pair_count=None,
                error=str(e),
            )

    async def get_default_fee(self) -> FeeQuote:
        # Public default tier (VIP 0): 10 bps maker / 10 bps taker for spot.
        # Source: https://www.binance.com/en/fee/schedule (fixed at API level for spot VIP0)
        return FeeQuote(
            exchange=self.id,
            pair="*",
            maker_bps=10.0,
            taker_bps=10.0,
            notes="VIP 0 spot, no BNB discount. From published fee schedule.",
        )
