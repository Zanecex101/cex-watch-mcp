"""MCP server entry point.

Exposes 4 tools for AI assistants:
    list_exchanges       — what we cover
    get_latest_listings  — newly active spot pairs per exchange
    compare_fees         — default-tier maker/taker across exchanges
    get_exchange_status  — health snapshot for one or all exchanges

Run:
    cex-watch-mcp                 # stdio transport (Claude Desktop, Cursor)
    python -m cex_watch_mcp.server
"""

from __future__ import annotations

import asyncio
import dataclasses
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from cex_watch_mcp import __version__
from cex_watch_mcp.exchanges import ALL_ADAPTERS, get_adapter

mcp = FastMCP("cex-watch-mcp")


def _to_dict(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    if isinstance(obj, list):
        return [_to_dict(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _to_dict(v) for k, v in obj.items()}
    return obj


async def _shared_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=15.0,
        headers={"User-Agent": f"cex-watch-mcp/{__version__}"},
    )


@mcp.tool()
async def list_exchanges() -> dict[str, Any]:
    """List the exchanges this server can monitor and the data dimensions each supports."""
    return {
        "version": __version__,
        "exchanges": [
            {
                "id": cls.id,
                "name": cls.name,
                "supports": ["spot_pairs", "status", "default_fee"],
            }
            for cls in ALL_ADAPTERS.values()
        ],
        "note": (
            "All sources are public REST APIs. No API keys required. "
            "See https://github.com/zanecex101/cex-watch-mcp for adapter source."
        ),
    }


@mcp.tool()
async def get_latest_listings(exchange: str, limit: int = 20) -> dict[str, Any]:
    """Return active spot trading pairs for one exchange.

    Args:
        exchange: One of binance, okx, bybit, coinbase, kraken.
        limit: Max number of pairs to return (sample). Default 20.
    """
    async with await _shared_client() as client:
        adapter_cls = ALL_ADAPTERS.get(exchange.lower())
        if adapter_cls is None:
            return {
                "error": f"unknown exchange: {exchange}",
                "supported": list(ALL_ADAPTERS),
            }
        async with adapter_cls(client=client) as adapter:
            pairs = await adapter.list_spot_pairs()
    return {
        "exchange": exchange.lower(),
        "total_active_pairs": len(pairs),
        "sample": [_to_dict(p) for p in pairs[: max(1, min(limit, 200))]],
    }


@mcp.tool()
async def compare_fees(pair: str = "*") -> dict[str, Any]:
    """Compare default public-tier maker/taker spot fees across all supported exchanges.

    Args:
        pair: Currently informational only — fees returned are the published default tier
              applicable to all spot pairs.

    Returns a sorted-by-taker-bps table.
    """
    async with await _shared_client() as client:
        results = []
        for cls in ALL_ADAPTERS.values():
            async with cls(client=client) as adapter:
                try:
                    fee = await adapter.get_default_fee()
                    results.append(_to_dict(fee))
                except Exception as e:  # noqa: BLE001
                    results.append(
                        {"exchange": cls.id, "error": str(e), "pair": pair}
                    )
    results.sort(key=lambda r: r.get("taker_bps") or 1e9)
    return {"pair": pair, "results": results}


@mcp.tool()
async def get_exchange_status(exchange: str = "all") -> dict[str, Any]:
    """Health snapshot: API reachability, latency, current spot pair count.

    Args:
        exchange: 'all' (default) or one specific id (binance/okx/bybit/coinbase/kraken).
    """
    async with await _shared_client() as client:
        if exchange == "all":
            results = []
            for cls in ALL_ADAPTERS.values():
                async with cls(client=client) as adapter:
                    s = await adapter.get_status()
                    results.append(_to_dict(s))
            return {"exchanges": results}
        adapter = get_adapter(exchange)
        async with adapter:
            s = await adapter.get_status()
        return _to_dict(s)


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    asyncio.run(main()) if False else main()
