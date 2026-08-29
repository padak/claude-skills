# Polymarket Trading Patterns

## Table of Contents
- [Order Types](#order-types)
- [Order Parameters](#order-parameters)
- [Arbitrage Detection](#arbitrage-detection)
- [Market Making](#market-making)
- [Open Source Bots](#open-source-bots)

---

## Order Types

| Type | Description | Use Case |
|------|-------------|----------|
| **GTC** | Good-Til-Cancelled | Default limit orders |
| **FOK** | Fill-or-Kill | Market orders, must fill completely |
| **FAK** | Fill-and-Kill | Market orders, partial fills OK |

---

## Order Parameters

```python
{
    "tokenID": "71321...",     # Token to trade
    "price": 0.50,             # Price per share (0.01 to 0.99)
    "size": 100,               # Number of shares (MINIMUM 5!)
    "side": "BUY",             # BUY or SELL
    "expiration": 1700000000,  # Optional: UNIX timestamp
}
```

### Size Limits

| Limit | Value |
|-------|-------|
| Minimum size | 5 shares |
| Tick size | 0.01 or 0.001 |

**Calculating minimum USD**:
```python
def min_order_usd(price: float) -> float:
    MIN_SHARES = 5
    return MIN_SHARES * price

# At $0.33: 5 * $0.33 = $1.65 minimum
# At $0.60: 5 * $0.60 = $3.00 minimum
# Safe minimum for any market: $5 USD
```

### Market Parameters

```python
{
    "tickSize": "0.01",  # Minimum price increment
    "negRisk": false     # Negative risk market flag
}
```

---

## Arbitrage Detection

### Why Mid-Point Prices Don't Work

Gamma API returns **normalized mid-point prices** that ALWAYS sum to $1.00:
```python
yes_price = 0.65
no_price = 0.35
# yes + no = 1.00 ALWAYS - no arbitrage here!
```

### Where Arbitrage Exists

Arbitrage exists only at the **order book level** (bid/ask spread):

```
BUY ARBITRAGE: YES_ask + NO_ask < $1.00
─────────────────────────────────────────
Buy YES at ask + Buy NO at ask = guaranteed $1 payout
Profit = $1.00 - (YES_ask + NO_ask)

Example:
  YES ask: $0.48 (100 shares available)
  NO ask:  $0.51 (150 shares available)
  Total:   $0.99 < $1.00
  Profit:  $0.01 per share (1%)

SELL ARBITRAGE: YES_bid + NO_bid > $1.00
──────────────────────────────────────────
Sell YES at bid + Sell NO at bid (if you hold both)
Profit = (YES_bid + NO_bid) - $1.00

Example:
  YES bid: $0.52 (200 shares available)
  NO bid:  $0.49 (180 shares available)
  Total:   $1.01 > $1.00
  Profit:  $0.01 per share (1%)
```

### Detection Code

```python
from dataclasses import dataclass

@dataclass
class OrderBook:
    token_id: str
    bids: list
    asks: list

    @property
    def best_bid(self) -> float:
        return float(self.bids[0]["price"]) if self.bids else 0.0

    @property
    def best_ask(self) -> float:
        return float(self.asks[0]["price"]) if self.asks else 1.0

    @property
    def best_bid_size(self) -> float:
        return float(self.bids[0]["size"]) if self.bids else 0.0

    @property
    def best_ask_size(self) -> float:
        return float(self.asks[0]["size"]) if self.asks else 0.0


def check_arbitrage(yes_book: OrderBook, no_book: OrderBook,
                    min_profit: float = 0.001) -> dict | None:
    """Check for arbitrage opportunities."""
    if not yes_book.bids or not yes_book.asks:
        return None
    if not no_book.bids or not no_book.asks:
        return None

    # BUY arbitrage: YES_ask + NO_ask < 1
    buy_cost = yes_book.best_ask + no_book.best_ask
    if buy_cost < (1.0 - min_profit):
        profit = 1.0 - buy_cost
        max_size = min(yes_book.best_ask_size, no_book.best_ask_size)
        return {
            "type": "buy",
            "profit_pct": profit,
            "yes_ask": yes_book.best_ask,
            "no_ask": no_book.best_ask,
            "total": buy_cost,
            "max_size": max_size,
            "max_profit_usd": max_size * profit
        }

    # SELL arbitrage: YES_bid + NO_bid > 1
    sell_revenue = yes_book.best_bid + no_book.best_bid
    if sell_revenue > (1.0 + min_profit):
        profit = sell_revenue - 1.0
        max_size = min(yes_book.best_bid_size, no_book.best_bid_size)
        return {
            "type": "sell",
            "profit_pct": profit,
            "yes_bid": yes_book.best_bid,
            "no_bid": no_book.best_bid,
            "total": sell_revenue,
            "max_size": max_size,
            "max_profit_usd": max_size * profit
        }

    return None
```

### Practical Reality

| Metric | Observed Value |
|--------|----------------|
| Opportunity duration | 50-500ms |
| Profit margin | 0.1% - 0.5% |
| Occurrence rate | Rare on liquid markets |
| Competition | Professional HFT bots |

**Why arbitrage is hard**:
1. Market makers set wide spreads intentionally
2. Professional traders react in <10ms
3. Transaction costs eat small profits
4. Need real-time WebSocket, not REST polling
5. Opportunities close faster than typical latency

### Polling Strategy

```python
POLL_INTERVAL = 0.5  # 500ms
BATCH_SIZE = 5       # Markets per cycle
MIN_VOLUME = 100000  # Focus on liquid markets
MIN_PROFIT = 0.001   # 0.1% threshold

async def poll_markets(markets: list):
    while True:
        for batch in chunked(markets, BATCH_SIZE):
            tasks = [fetch_orderbook(m.yes_token) for m in batch]
            tasks += [fetch_orderbook(m.no_token) for m in batch]
            books = await asyncio.gather(*tasks)

            for market in batch:
                result = check_arbitrage(market.yes_book, market.no_book)
                if result:
                    log_opportunity(market, result)

        await asyncio.sleep(POLL_INTERVAL)
```

---

## Market Making

### Understanding Gamma vs CLOB Prices

| Source | Value | Meaning |
|--------|-------|---------|
| Gamma `bestBid` | 0.368 | Synthetic: `1 - bestAsk(NO)` |
| Gamma `bestAsk` | 0.375 | Lowest ask on YES token |
| CLOB | Bid: 0.001, Ask: 0.999 | Raw (often sparse) |

Gamma calculates synthetic prices:
```python
# Gamma API synthetic prices for YES token:
bestBid_YES = 1 - bestAsk_NO   # Implied from NO side
bestAsk_YES = lowest_ask_YES   # Direct from orderbook
```

### Finding Real Liquidity

```python
# Check BOTH tokens
yes_book = client.get_order_book(yes_token_id)
no_book = client.get_order_book(no_token_id)

# Real best bid for YES = 1 - best ask for NO
# Real best ask for YES = lowest ask on YES orderbook

# Find asks around target price:
for ask in yes_book.asks:
    if 0.35 <= float(ask.price) <= 0.45:
        print(f"Ask: {ask.price} x {ask.size}")
```

### Market Making Pattern

```python
# To BUY YES at 0.49:
# - Place limit order on YES token at 0.49
# - You're joining the bid queue

# To SELL YES at 0.50:
# - Place limit order on YES token at 0.50
# - You're adding to the ask side

# Spread = your profit per roundtrip
spread = sell_price - buy_price  # e.g., 0.50 - 0.49 = $0.01 (2%)
```

---

## Open Source Bots

### poly-maker (Market Making)

**Repository**: https://github.com/warproxxx/poly-maker

**Stars**: 221 | **Forks**: 119

**Features**:
- Automated market making
- Google Sheets configuration
- WebSocket order book updates
- Position management with stop-loss

**Setup**:
```bash
git clone https://github.com/warproxxx/poly-maker
cd poly-maker
uv sync
cp .env.example .env
# Edit .env: PK, BROWSER_ADDRESS, SPREADSHEET_URL
uv run python main.py
```

**Google Sheets Config**:
| Column | Description |
|--------|-------------|
| question | Market question |
| token1/token2 | YES/NO token IDs |
| trade_size | Base order size (USDC) |
| max_size | Maximum position |
| max_spread | Maximum acceptable spread |
| tick_size | Price increment |

### Polymarket/agents (AI Trading)

**Repository**: https://github.com/Polymarket/agents

**Features**:
- LLM-powered trading decisions
- Superforecaster prompts
- RAG support

**Setup**:
```bash
pip install -r requirements.txt
export POLYGON_WALLET_PRIVATE_KEY="..."
python agents/application/trade.py
```

### Security Warning

Always audit bot code before using - some repositories have been flagged for malicious private key theft.

---

## Performance Tips

| Language | Latency | Recommended For |
|----------|---------|-----------------|
| Rust | Lowest | HFT, market making |
| Go | Low | High-frequency bots |
| TypeScript | Medium | General trading |
| Python | Higher | Strategy testing |

**Optimization**:
1. Use WebSockets instead of REST polling
2. Maintain local order book copy
3. Batch order operations
4. Connection pooling
5. Async/await for concurrent I/O
