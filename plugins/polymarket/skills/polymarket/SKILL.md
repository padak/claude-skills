---
name: polymarket
description: "Build trading bots and applications on Polymarket prediction markets. Use when working with Polymarket APIs, py-clob-client SDK, WebSocket streaming, order placement, market data fetching, whale tracking, or arbitrage detection. Triggers: Polymarket, prediction market, CLOB, trading bot, market making, py-clob-client, Magic.Link wallet, polygon trading."
---

# Polymarket Developer Skill

Build trading applications on Polymarket (Polygon chain, USDC settlement).

## Architecture Overview

```
Gamma API (market discovery) ─┐
CLOB API (trading/orders)    ─┼─→ WebSocket API (real-time)
Data API (positions/trades)  ─┘
```

| API | Endpoint | Purpose |
|-----|----------|---------|
| CLOB | `https://clob.polymarket.com` | Trading, orders |
| Gamma | `https://gamma-api.polymarket.com` | Market discovery |
| Data | `https://data-api.polymarket.com` | Positions, trades |
| WebSocket | `wss://ws-subscriptions-clob.polymarket.com` | Real-time |

## Quick Start (Python)

### Installation
```bash
pip install py-clob-client
```

### Authentication

**CRITICAL: Magic.Link Users (Google/Email login)**

Magic.Link creates TWO wallets:
- **Signer**: Signs transactions (has private key - export from wallet.magic.link)
- **Proxy**: Holds funds (shown in Polymarket UI - smart contract, no key)

```python
from py_clob_client.client import ClobClient

client = ClobClient(
    host="https://clob.polymarket.com",
    key=SIGNER_PRIVATE_KEY,      # From wallet.magic.link export
    chain_id=137,
    signature_type=1,            # MUST be 1 for Magic.Link!
    funder=PROXY_WALLET_ADDRESS  # Address from Polymarket UI
)

# Create/derive API credentials
creds = client.create_or_derive_api_creds()
client.set_api_creds(creds)
```

**EOA Wallets (MetaMask/hardware)**
```python
client = ClobClient(
    host="https://clob.polymarket.com",
    key=PRIVATE_KEY,
    chain_id=137,
    signature_type=0  # EOA
)
```

### Place Orders

```python
from py_clob_client.clob_types import OrderArgs, MarketOrderArgs, OrderType
from py_clob_client.order_builder.constants import BUY, SELL

# Limit order
order = client.create_order(OrderArgs(
    price=0.50,
    size=100,  # MINIMUM 5 shares!
    side=BUY,
    token_id="<token-id>"
))
client.post_order(order)

# Market order (FOK = Fill-or-Kill)
market_order = client.create_market_order(MarketOrderArgs(
    token_id="<token-id>",
    amount=100.0,  # USDC for BUY, shares for SELL
    side=BUY
))
client.post_order(market_order, OrderType.FOK)

# Cancel
client.cancel(order_id)
client.cancel_all()
```

### Get Market Data

```python
# Order book
book = client.get_order_book(token_id)
best_bid = float(book.bids[0].price)  # Prices are strings!
best_ask = float(book.asks[0].price)

# Midpoint
mid = client.get_midpoint(token_id)
```

## Critical Gotchas

### 1. JSON String Fields in Gamma API

`outcomePrices` and `clobTokenIds` are **JSON strings**, not arrays:

```python
import json

market = gamma_response
# WRONG: market["clobTokenIds"][0]
# RIGHT:
clob_ids = json.loads(market["clobTokenIds"])
yes_token = clob_ids[0]
no_token = clob_ids[1]
```

### 2. Minimum Order Size

Minimum is **5 shares**, not $5 USD:
- At $0.10 price: 5 shares = $0.50 minimum
- At $0.90 price: 5 shares = $4.50 minimum

### 3. slug vs eventSlug for URLs

```python
# WRONG - 404 error
f"https://polymarket.com/event/{position['slug']}"

# RIGHT
f"https://polymarket.com/event/{position['eventSlug']}"
```

### 4. /trades Endpoint Does NOT Filter by Wallet

```python
# DOES NOT WORK - returns ALL platform trades
GET /trades?proxyWallet=0x...

# USE THIS for user-specific trades:
GET /activity?user=0x...&limit=100
```

### 5. Gamma API Prices are Normalized

`outcomePrices` always sum to $1.00 - can't find arbitrage here.
Use CLOB orderbook for real bid/ask spreads.

### 6. Orderbook Prices are Strings

```python
# WRONG
best_bid = book.bids[0].price + 0.01

# RIGHT
best_bid = float(book.bids[0].price) + 0.01
```

## Common Patterns

### Fetch User Positions
```python
import httpx

async def get_positions(wallet: str):
    url = "https://data-api.polymarket.com/positions"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params={"user": wallet})
        return resp.json()
```

### Fetch Whale Trades (Activity Endpoint)
```python
async def get_whale_trades(wallet: str, limit: int = 100):
    url = "https://data-api.polymarket.com/activity"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params={
            "user": wallet,
            "limit": limit
        })
        return resp.json()
```

### Get Top Traders (Leaderboard)
```python
async def get_leaderboard(period: str = "week"):
    url = "https://data-api.polymarket.com/v1/leaderboard"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params={
            "timePeriod": period,
            "orderBy": "PNL",
            "limit": 20
        })
        return resp.json()
```

## Reference Files

For detailed documentation, see:

- **[references/api-reference.md](references/api-reference.md)** - Complete API endpoints (Gamma, CLOB, Data APIs)
- **[references/sdks.md](references/sdks.md)** - SDK patterns (Python, TypeScript, Rust)
- **[references/websocket.md](references/websocket.md)** - Real-time streaming patterns
- **[references/trading.md](references/trading.md)** - Order types, arbitrage detection, market making

## Environment Variables

```bash
POLYMARKET_PRIVATE_KEY=0x...     # Signer key
POLY_FUNDER_ADDRESS=0x...        # Proxy wallet (Magic.Link users)
POLY_SIGNATURE_TYPE=1            # 0=EOA, 1=PolyProxy
POLY_API_KEY=...                 # After credential creation
POLY_SECRET=...
POLY_PASSPHRASE=...
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `invalid signature` | Wrong signature_type | Use 1 for Magic.Link |
| `not enough balance / allowance` | Missing funder | Add funder=PROXY_ADDRESS |
| `Unauthorized/Invalid api key` | Stale creds | Re-derive credentials |
