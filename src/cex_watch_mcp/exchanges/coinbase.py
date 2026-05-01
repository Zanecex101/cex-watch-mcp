"""Coinbase Exchange (formerly Pro) adapter."""

from __future__ import annotations

import time

from cex_watch_mcp.exchanges.base import (
    ExchangeAdapter,
    ExchangeStatus,
    FeeQuote,
    Listing,
)


class CoinbaseAdapter(ExchangeAdapter):
    id = "coinbase"
    name = "Coinbase"
    base_url = "https://api.exchange.coinbase.com"

    async def list_spot_pairs(self) -> list[Listing]:
        r = await self.client.get(f"{self.base_url}/products")
        r.raise_for_status()
        data = r.json()
        out: list[Listing] = []
        for s in data:
            if s.get("trading_disabled") or s.get("status") != "online":
                continue
            out.append(
                Listing(
                    exchange=self.id,
                    symbol=s["id"],
                    base=s["base_currency"],
                    quote=s["quote_currency"],
                    status="trading",
                )
            )
        return out

    async def get_status(self) -> ExchangeStatus:
        t0 = time.monotonic()
        try:
            r = await self.client.get(f"{self.base_url}/time")
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
        # Coinbase Advanced Trade default tier: 60 bps maker / 80 bps taker for <$10k 30d volume.
        # Source: https://www.coinbase.com/advanced-fees
        return FeeQuote(
            exchange=self.id,
            pair="*",
            maker_bps=60.0,
            taker_bps=80.0,
            notes="Advanced Trade default tier (<$10k 30d volume). From published fee schedule.",
        )
