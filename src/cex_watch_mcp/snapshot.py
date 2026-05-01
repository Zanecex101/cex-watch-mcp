"""Daily snapshot generator. Run by GitHub Actions (or `cex-watch-snapshot` CLI).

Writes:
    data/listings/YYYY-MM-DD.json
    data/fees/YYYY-MM-DD.json
    data/status/YYYY-MM-DD.json
    data/latest.json

Each file is deterministic JSON with sorted keys, so day-over-day diffs are clean.
"""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from cex_watch_mcp import __version__
from cex_watch_mcp.exchanges import ALL_ADAPTERS

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _serialize(obj: object) -> object:
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)  # type: ignore[arg-type]
    raise TypeError(f"unserializable: {type(obj)}")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=_serialize),
        encoding="utf-8",
    )


async def collect_one(exchange_id: str, client: httpx.AsyncClient) -> dict[str, object]:
    cls = ALL_ADAPTERS[exchange_id]
    async with cls(client=client) as adapter:
        try:
            status = await adapter.get_status()
        except Exception as e:  # noqa: BLE001
            status = None
            status_error = str(e)
        else:
            status_error = None
        try:
            pairs = await adapter.list_spot_pairs()
        except Exception as e:  # noqa: BLE001
            pairs = []
            pairs_error = str(e)
        else:
            pairs_error = None
        try:
            fee = await adapter.get_default_fee()
        except Exception as e:  # noqa: BLE001
            fee = None
            fee_error = str(e)
        else:
            fee_error = None
    return {
        "exchange": exchange_id,
        "status": status,
        "status_error": status_error,
        "pair_count": len(pairs),
        "pairs_error": pairs_error,
        "pairs_sample": [p.symbol for p in pairs[:10]],
        "fee_default": fee,
        "fee_error": fee_error,
    }


async def run_snapshot(data_dir: Path) -> None:
    today = datetime.now(timezone.utc).date().isoformat()
    generated_at = datetime.now(timezone.utc).isoformat()

    async with httpx.AsyncClient(
        timeout=15.0,
        headers={"User-Agent": f"cex-watch-mcp/{__version__}"},
    ) as client:
        results = await asyncio.gather(
            *(collect_one(eid, client) for eid in ALL_ADAPTERS),
            return_exceptions=False,
        )

    listings_payload = {
        "snapshot_date": today,
        "generated_at": generated_at,
        "exchanges": {
            r["exchange"]: {
                "pair_count": r["pair_count"],
                "pairs_sample": r["pairs_sample"],
                "error": r["pairs_error"],
            }
            for r in results
        },
    }
    fees_payload = {
        "snapshot_date": today,
        "generated_at": generated_at,
        "exchanges": {
            r["exchange"]: {
                "default_fee": r["fee_default"],
                "error": r["fee_error"],
            }
            for r in results
        },
    }
    status_payload = {
        "snapshot_date": today,
        "generated_at": generated_at,
        "exchanges": {
            r["exchange"]: {
                "status": r["status"],
                "error": r["status_error"],
            }
            for r in results
        },
    }
    latest_payload = {
        "snapshot_date": today,
        "generated_at": generated_at,
        "tool_version": __version__,
        "summary": [
            {
                "exchange": r["exchange"],
                "healthy": (r["status"].healthy if r["status"] else False),
                "api_latency_ms": (r["status"].api_latency_ms if r["status"] else None),
                "pair_count": r["pair_count"],
                "maker_bps": (r["fee_default"].maker_bps if r["fee_default"] else None),
                "taker_bps": (r["fee_default"].taker_bps if r["fee_default"] else None),
            }
            for r in results
        ],
    }

    _write_json(data_dir / "listings" / f"{today}.json", listings_payload)
    _write_json(data_dir / "fees" / f"{today}.json", fees_payload)
    _write_json(data_dir / "status" / f"{today}.json", status_payload)
    _write_json(data_dir / "latest.json", latest_payload)

    print(f"snapshot {today} written to {data_dir}")
    for row in latest_payload["summary"]:
        print(
            f"  {row['exchange']:10}  healthy={row['healthy']!s:5}  "
            f"pairs={row['pair_count']:>5}  "
            f"maker={row['maker_bps']}bps  taker={row['taker_bps']}bps"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="cex-watch-mcp daily snapshot")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Output directory (default: repo data/)",
    )
    args = parser.parse_args()
    asyncio.run(run_snapshot(args.data_dir))


if __name__ == "__main__":
    main()
