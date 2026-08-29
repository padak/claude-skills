# Polymarket API Reference

## Table of Contents
- [Gamma API](#gamma-api)
- [CLOB API](#clob-api)
- [Data API](#data-api)
- [User PnL API](#user-pnl-api)

---

## Gamma API

**Base URL**: `https://gamma-api.polymarket.com`

### GET /markets

Fetch active markets.

**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `active` | bool | Filter by active status |
| `closed` | bool | Filter by closed status |
| `limit` | int | Max results (default 100) |

**Response** (key fields):
```json
{
  "id": "646091",
  "conditionId": "0x123...",
  "question": "Will Bitcoin hit $100k?",
  "slug": "will-bitcoin-hit-100k",
  "outcomePrices": "[\"0.65\", \"0.35\"]",
  "clobTokenIds": "[\"713...\", \"456...\"]",
  "volumeNum": 1500000.0,
  "active": true,
  "closed": false
}
```

**CRITICAL**: `outcomePrices` and `clobTokenIds` are JSON strings - parse with `json.loads()`.

### GET /markets/{market_id}

Fetch single market by ID.

### GET /events

Fetch events (groups of related markets).

### GET /tags

Fetch available market tags.

---

## CLOB API

**Base URL**: `https://clob.polymarket.com`

### GET /book

Fetch order book for a token.

**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `token_id` | string | CLOB token ID |

**Response**:
```json
{
  "bids": [
    {"price": "0.50", "size": "100"},
    {"price": "0.49", "size": "250"}
  ],
  "asks": [
    {"price": "0.52", "size": "150"},
    {"price": "0.53", "size": "300"}
  ]
}
```

**Note**: `price` and `size` are strings - convert to float.

### GET /midpoint

Get midpoint price.

**Parameters**: `token_id` (string)

**Response**: `{"mid": "0.51"}`

### GET /spread

Get bid-ask spread.

**Parameters**: `token_id` (string)

### GET /tick-size

Get minimum price increment.

**Parameters**: `token_id` (string)

**Response**: `{"tickSize": "0.01"}` or `{"tickSize": "0.001"}`

### GET /prices-history

Historical price data.

**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `token_id` | string | CLOB token ID |
| `startTs` | int | Start timestamp (Unix seconds) |
| `endTs` | int | End timestamp (Unix seconds) |
| `interval` | int | Resolution in minutes (default 60) |
| `duration` | string | Alternative: `1m`, `1h`, `6h`, `1d`, `1w`, `max` |

Use either `startTs/endTs` OR `duration`, not both.

**Response**:
```json
{
  "history": [
    {"t": 1697875200, "p": "0.65"},
    {"t": 1697878800, "p": "0.67"}
  ]
}
```

### POST /order

Place an order (requires authentication).

### DELETE /order/{order_id}

Cancel an order.

### DELETE /orders

Cancel all orders.

### GET /orders

Get open orders.

### GET /trades

Get your trades (authenticated - returns only YOUR trades).

---

## Data API

**Base URL**: `https://data-api.polymarket.com`

### GET /positions

Get user's current positions.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `user` | string | Yes | Wallet address |
| `sizeThreshold` | int | No | Minimum position size |
| `limit` | int | No | Max results (default 100) |

**Response**:
```json
[
  {
    "asset": "123456...",
    "conditionId": "0xabc...",
    "title": "Will Bitcoin hit $100k?",
    "slug": "btc-100k-yes",
    "eventSlug": "btc-100k",
    "outcome": "Yes",
    "size": 1000.0,
    "avgPrice": 0.45,
    "curPrice": 0.52,
    "currentValue": 520.0,
    "cashPnl": 70.0,
    "percentPnl": 15.5
  }
]
```

**IMPORTANT**: Use `eventSlug` for Polymarket URLs, not `slug`.

### GET /activity

Get user's trade history. **This is the key endpoint for whale tracking!**

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `user` | string | Yes | Wallet address (proxy wallet) |
| `limit` | int | No | Max results (default 25) |
| `offset` | int | No | Pagination offset |

**Response**:
```json
[
  {
    "proxyWallet": "0x16b29c50...",
    "timestamp": 1766854811,
    "conditionId": "0x51d53fc...",
    "type": "TRADE",
    "size": 777,
    "usdcSize": 396.27,
    "transactionHash": "0xb6f628a...",
    "price": 0.51,
    "asset": "112306036...",
    "side": "BUY",
    "outcomeIndex": 1,
    "title": "Spread: BYU (-3.5)",
    "eventSlug": "cfb-gtech-byu-2025-12-27",
    "outcome": "Georgia Tech",
    "name": "SeriouslySirius"
  }
]
```

### GET /trades

**WARNING**: Does NOT filter by wallet! Returns ALL platform trades.

**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `limit` | int | Max results (1-10000) |
| `conditionId` | string | Filter by market ID |
| `side` | string | `BUY` or `SELL` |

### GET /v1/leaderboard

Get trader leaderboard.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `timePeriod` | string | Yes | `day`, `week`, `month`, `all` |
| `orderBy` | string | Yes | `PNL` or `VOL` |
| `limit` | int | No | Max results (default 20) |
| `offset` | int | No | Pagination offset |
| `category` | string | No | `overall` or specific |

**Response**:
```json
[
  {
    "rank": "1",
    "proxyWallet": "0x5350afcd...",
    "userName": "simonbanza",
    "vol": 9138652.17,
    "pnl": 1186120.86
  }
]
```

---

## User PnL API

**Base URL**: `https://user-pnl-api.polymarket.com`

### GET /user-pnl

Get P&L time series.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `user_address` | string | Yes | Wallet address |
| `interval` | string | No | `1d`, `1w`, `1m`, `all` |
| `fidelity` | string | No | `1d`, `1h` |

**Response**:
```json
[
  {"t": 1697875200, "p": 150000.50},
  {"t": 1697961600, "p": 152340.25}
]
```

Where `t` is Unix timestamp and `p` is cumulative P&L.
