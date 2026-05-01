"""Abstract base class every exchange adapter implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import httpx

DEFAULT_TIMEOUT = 10.0
USER_AGENT = "cex-watch-mcp/0.1 (+https://github.com/Zanecex101/cex-watch-mcp)"


@dataclass
class FeeQuote:
    exchange: str
    pair: str
    maker_bps: float | None
    taker_bps: float | None
    notes: str = ""


@dataclass
class ExchangeStatus:
    exchange: str
    healthy: bool
    api_latency_ms: int | None
    spot_pair_count: int | None
    error: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Listing:
    exchange: str
    symbol: str
    base: str
    quote: str
    status: str
    raw: dict[str, Any] = field(default_factory=dict)


class ExchangeAdapter(ABC):
    """One adapter per exchange. All methods async."""

    id: str = ""
    name: str = ""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client
        self._owns_client = client is None

    async def __aenter__(self) -> "ExchangeAdapter":
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=DEFAULT_TIMEOUT,
                headers={"User-Agent": USER_AGENT},
            )
        return self

    async def __aexit__(self, *exc: Any) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("adapter must be used as async context manager")
        return self._client

    @abstractmethod
    async def list_spot_pairs(self) -> list[Listing]:
        """Return all currently active spot trading pairs."""

    @abstractmethod
    async def get_status(self) -> ExchangeStatus:
        """Return overall API health snapshot."""

    @abstractmethod
    async def get_default_fee(self) -> FeeQuote:
        """Return the public default tier maker/taker fee for spot."""
