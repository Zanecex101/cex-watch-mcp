"""Smoke tests that don't hit the network — just verify the package imports cleanly."""

from cex_watch_mcp import __version__
from cex_watch_mcp.exchanges import ALL_ADAPTERS, get_adapter


def test_version():
    assert __version__ == "0.1.0"


def test_adapter_registry():
    assert set(ALL_ADAPTERS) == {"binance", "okx", "bybit", "coinbase", "kraken"}


def test_get_adapter_unknown():
    try:
        get_adapter("nonexistent")
    except ValueError as e:
        assert "unknown exchange" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_get_adapter_known():
    a = get_adapter("Binance")  # case-insensitive
    assert a.id == "binance"
