"""Exchange adapters."""

from cex_watch_mcp.exchanges.base import ExchangeAdapter
from cex_watch_mcp.exchanges.binance import BinanceAdapter
from cex_watch_mcp.exchanges.bybit import BybitAdapter
from cex_watch_mcp.exchanges.coinbase import CoinbaseAdapter
from cex_watch_mcp.exchanges.kraken import KrakenAdapter
from cex_watch_mcp.exchanges.okx import OKXAdapter

ALL_ADAPTERS: dict[str, type[ExchangeAdapter]] = {
    "binance": BinanceAdapter,
    "okx": OKXAdapter,
    "bybit": BybitAdapter,
    "coinbase": CoinbaseAdapter,
    "kraken": KrakenAdapter,
}


def get_adapter(exchange_id: str) -> ExchangeAdapter:
    cls = ALL_ADAPTERS.get(exchange_id.lower())
    if cls is None:
        raise ValueError(f"unknown exchange: {exchange_id}. supported: {list(ALL_ADAPTERS)}")
    return cls()


__all__ = [
    "ALL_ADAPTERS",
    "ExchangeAdapter",
    "BinanceAdapter",
    "OKXAdapter",
    "BybitAdapter",
    "CoinbaseAdapter",
    "KrakenAdapter",
    "get_adapter",
]
