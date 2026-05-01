# cex-watch-mcp

> **An open MCP server for monitoring centralized crypto exchanges.**
> No backend SaaS. No API token. Every data source is a public REST endpoint you can audit.

[![Daily Snapshot](https://github.com/Zanecex101/cex-watch-mcp/actions/workflows/daily-snapshot.yml/badge.svg)](https://github.com/Zanecex101/cex-watch-mcp/actions/workflows/daily-snapshot.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Why this exists

CEX monitoring tools today are either:

- **Closed-source SaaS** (you pay a token, you trust a backend you can't see), or
- **Per-exchange one-offs** (one script per exchange, never reused)

`cex-watch-mcp` is a small MCP server that gives an AI assistant unified, auditable access to a fixed set of CEX data dimensions. Every adapter is ~80 lines hitting a documented public endpoint. Read the source, run it yourself.

It plays nicely alongside broader news servers like [opennews-mcp](https://github.com/6551Team/opennews-mcp) — they cover 84 sources across news/onchain/listings; this one stays narrow on CEXes and stays open.

## What it does

Exposes 4 MCP tools to your AI assistant:

| Tool | What it answers |
|---|---|
| `list_exchanges` | "Which exchanges does this server cover?" |
| `get_latest_listings` | "What pairs is OKX currently trading?" |
| `compare_fees` | "Which CEX has the cheapest spot taker fee right now?" |
| `get_exchange_status` | "Is Binance API healthy? What's the latency?" |

Currently covers **Binance, OKX, Bybit, Coinbase, Kraken**. New adapters are ~80 lines — see [docs/adding-new-exchange.md](docs/adding-new-exchange.md).

## Install

### Option 1 — Claude Desktop / Cursor / Cline

Add to your MCP config (location varies by client; see [`examples/`](examples/)):

```json
{
  "mcpServers": {
    "cex-watch": {
      "command": "uvx",
      "args": ["cex-watch-mcp"]
    }
  }
}
```

### Option 2 — pip + run directly

```bash
pip install cex-watch-mcp
cex-watch-mcp        # stdio MCP server
```

### Option 3 — clone + run from source

```bash
git clone https://github.com/Zanecex101/cex-watch-mcp
cd cex-watch-mcp
pip install -e .
cex-watch-mcp
```

## Example prompts

Once connected, ask your AI:

- *"List the exchanges cex-watch covers."*
- *"Compare BTCUSDT spot fees across exchanges."*
- *"Is the Binance API healthy right now? What about Kraken?"*
- *"How many active spot pairs does OKX list today?"*

## Daily data dump

A GitHub Actions workflow runs the snapshot every day at **00:05 UTC** and commits the result to `data/`:

```
data/
├── listings/2026-05-01.json     # active pairs per exchange
├── fees/2026-05-01.json         # default-tier maker/taker bps
├── status/2026-05-01.json       # health snapshot
└── latest.json                  # convenience symlink to today's roll-up
```

Anyone can `git clone` and diff day-over-day to find listing changes, fee bumps, or outages.

## How it differs from opennews-mcp

| | cex-watch-mcp | opennews-mcp |
|---|---|---|
| Open-source backend | ✅ Every adapter visible in this repo | ❌ Backend at 6551.io is closed |
| Auth required | ❌ None (public APIs only) | ✅ API token from 6551.io |
| Coverage | Narrow: CEX data only | Broad: 84+ sources, news + onchain + listings |
| Real-time | Not yet (polling-only v0.1) | ✅ WebSocket subscriptions |

`opennews-mcp` is the kitchen sink. `cex-watch-mcp` is the small auditable knife.

## Roadmap

- **v0.1** ← current. 5 exchanges × 4 tools, daily snapshots.
- **v0.2** Add Bitget, KuCoin, Gate.io, MEXC, HTX. Withdrawal fee per coin.
- **v0.3** WebSocket `subscribe_listings` tool (stream new pair events).
- **v0.4** Anomaly detection: flag fee bumps, sudden delistings, API outages.

Issues and PRs welcome. See [docs/adding-new-exchange.md](docs/adding-new-exchange.md) for the contributor walkthrough.

## Author

Built by [Zane](https://github.com/Zanecex101) — independent crypto exchange researcher.
Also editor at [Cex101](https://cex101.com), where he writes multilingual exchange reviews.

## License

MIT — see [LICENSE](LICENSE).
