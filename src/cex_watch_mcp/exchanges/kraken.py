"""Kraken adapter — public REST API."""

from __future__ import annotations

import time

from cex_watch_mcp.exchanges.base import (
    ExchangeAdapter,
    ExchangeStatus,
    FeeQuote,
    Listing,
)


class KrakenAdapter(ExchangeAdapter):
    id = "kraken"
    name = "Kraken"
    base_url = "https://api.kraken.com"

    async def list_spot_pairs(self) -> list[Listing]:
        r = await self.client.get(f"{self.base_url}/0/public/AssetPairs")
        r.raise_for_status()
        data = r.json()
        result = data.get("result", {})
        out: list[Listing] = []
        for symbol, info in result.items():
            status = info.get("status", "online")
            if status != "online":
                continue
            out.append(
                Listing(
                    exchange=self.id,
                    symbol=symbol,
                    base=info.get("base", ""),
                    quote=info.get("quote", ""),
                    status="trading",
                )
            )
        return out

    async def get_status(self) -> ExchangeStatus:
        t0 = time.monotonic()
        try:
            r = await self.client.get(f"{self.base_url}/0/public/SystemStatus")
            r.raise_for_status()
            data = r.json()
            latency = int((time.monotonic() - t0) * 1000)
            sys_status = data.get("result", {}).get("status")
            healthy = sys_status == "online"
            pairs = await self.list_spot_pairs() if healthy else []
            return ExchangeStatus(
                exchange=self.id,
                healthy=healthy,
                api_latency_ms=latency,
                spot_pair_count=len(pairs) if healthy else None,
                raw={"system_status": sys_status},
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
        # Default Pro tier: 25 bps maker / 40 bps taker for <$10k 30d volume.
        # Source: https://www.kraken.com/features/fee-schedule
        return FeeQuote(
            exchange=self.id,
            pair="*",
            maker_bps=25.0,
            taker_bps=40.0,
            notes="Pro default tier (<$10k 30d volume). From published fee schedule.",
        )
