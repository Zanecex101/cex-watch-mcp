"""Bybit adapter — uses v5 unified API."""

from __future__ import annotations

import time

from cex_watch_mcp.exchanges.base import (
    ExchangeAdapter,
    ExchangeStatus,
    FeeQuote,
    Listing,
)


class BybitAdapter(ExchangeAdapter):
    id = "bybit"
    name = "Bybit"
    base_url = "https://api.bybit.com"

    async def list_spot_pairs(self) -> list[Listing]:
        r = await self.client.get(
            f"{self.base_url}/v5/market/instruments-info",
            params={"category": "spot"},
        )
        r.raise_for_status()
        data = r.json()
        items = data.get("result", {}).get("list", [])
        out: list[Listing] = []
        for s in items:
            if s.get("status") != "Trading":
                continue
            out.append(
                Listing(
                    exchange=self.id,
                    symbol=s["symbol"],
                    base=s["baseCoin"],
                    quote=s["quoteCoin"],
                    status="trading",
                )
            )
        return out

    async def get_status(self) -> ExchangeStatus:
        t0 = time.monotonic()
        try:
            r = await self.client.get(f"{self.base_url}/v5/market/time")
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
        # Public default tier (Vip 0): 10 bps maker / 10 bps taker for spot.
        # Source: https://www.bybit.com/en/help-center/article/Trading-Fee-Structure
        return FeeQuote(
            exchange=self.id,
            pair="*",
            maker_bps=10.0,
            taker_bps=10.0,
            notes="Vip 0 spot. From published fee schedule.",
        )
