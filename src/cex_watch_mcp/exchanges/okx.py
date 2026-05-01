"""OKX adapter — public REST endpoints under /api/v5/public/."""

from __future__ import annotations

import time

from cex_watch_mcp.exchanges.base import (
    ExchangeAdapter,
    ExchangeStatus,
    FeeQuote,
    Listing,
)


class OKXAdapter(ExchangeAdapter):
    id = "okx"
    name = "OKX"
    base_url = "https://www.okx.com"

    async def list_spot_pairs(self) -> list[Listing]:
        r = await self.client.get(
            f"{self.base_url}/api/v5/public/instruments",
            params={"instType": "SPOT"},
        )
        r.raise_for_status()
        data = r.json()
        out: list[Listing] = []
        for s in data.get("data", []):
            if s.get("state") != "live":
                continue
            out.append(
                Listing(
                    exchange=self.id,
                    symbol=s["instId"],
                    base=s["baseCcy"],
                    quote=s["quoteCcy"],
                    status="trading",
                )
            )
        return out

    async def get_status(self) -> ExchangeStatus:
        t0 = time.monotonic()
        try:
            r = await self.client.get(f"{self.base_url}/api/v5/public/time")
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
        # Public default tier (Lv1): 8 bps maker / 10 bps taker for spot.
        # Source: https://www.okx.com/fees
        return FeeQuote(
            exchange=self.id,
            pair="*",
            maker_bps=8.0,
            taker_bps=10.0,
            notes="Regular user Lv1 spot. From published fee schedule.",
        )
