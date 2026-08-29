# Polymarket SDKs

## Table of Contents
- [Official SDKs](#official-sdks)
- [Unofficial SDKs](#unofficial-sdks)
- [SDK Comparison](#sdk-comparison)

---

## Official SDKs

### Python: py-clob-client

**Repository**: https://github.com/Polymarket/py-clob-client

**Installation**:
```bash
pip install py-clob-client
```

**Requirements**: Python 3.9+

**Complete Setup**:
```python
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, MarketOrderArgs, OrderType, OpenOrderParams
from py_clob_client.order_builder.constants import BUY, SELL

HOST = "https://clob.polymarket.com"
CHAIN_ID = 137

# For Magic.Link users (signature_type=1)
client = ClobClient(
    HOST,
    key=PRIVATE_KEY,
    chain_id=CHAIN_ID,
    signature_type=1,  # 0=EOA, 1=PolyProxy
    funder=FUNDER_ADDRESS
)

# Create/derive API credentials
creds = client.create_or_derive_api_creds()
client.set_api_creds(creds)
```

**Limit Order**:
```python
order_args = OrderArgs(
    price=0.50,
    size=100,
    side=BUY,
    token_id="<token-id>"
)
signed_order = client.create_order(order_args)
response = client.post_order(signed_order)
```

**Market Order**:
```python
market_order = MarketOrderArgs(
    token_id="<token-id>",
    amount=100.0,  # USDC for BUY, shares for SELL
    side=BUY
)
signed = client.create_market_order(market_order)
response = client.post_order(signed, OrderType.FOK)
```

**Order Management**:
```python
# Get open orders
orders = client.get_orders(OpenOrderParams())

# Cancel single order
client.cancel(order_id)

# Cancel all orders
client.cancel_all()

# Get trades
trades = client.get_trades()
```

**Order Book**:
```python
orderbook = client.get_order_book(token_id)
print(f"Best Bid: {orderbook.bids[0].price}")
print(f"Best Ask: {orderbook.asks[0].price}")
```

### TypeScript: clob-client

**Repository**: https://github.com/Polymarket/clob-client

**Installation**:
```bash
npm install @polymarket/clob-client
```

**Setup**:
```typescript
import { ClobClient, Side, OrderType } from "@polymarket/clob-client";
import { Wallet } from "ethers";

const HOST = "https://clob.polymarket.com";
const CHAIN_ID = 137;
const signer = new Wallet(process.env.PRIVATE_KEY);

// Create temp client to get credentials
const tempClient = new ClobClient(HOST, CHAIN_ID, signer);
const apiCreds = await tempClient.createOrDeriveApiKey();

// Create authenticated client
const client = new ClobClient(HOST, CHAIN_ID, signer, apiCreds, 0);
```

**Place Order**:
```typescript
const response = await client.createAndPostOrder(
  {
    tokenID: tokenID,
    price: 0.65,
    size: 100,
    side: Side.BUY,
  },
  { tickSize: "0.01", negRisk: false },
  OrderType.GTC
);
```

### TypeScript: real-time-data-client

**Repository**: https://github.com/Polymarket/real-time-data-client

**Installation**:
```bash
npm install @polymarket/real-time-data-client
```

**Usage**:
```typescript
import { RealTimeDataClient } from "@polymarket/real-time-data-client";

const client = new RealTimeDataClient({
    onConnect: (client) => {
        client.subscribe({
            subscriptions: [
                { topic: "activity", type: "trades" }
            ]
        });
    },
    onMessage: (_, message) => {
        console.log(`Trade: ${message.payload.side} @ ${message.payload.price}`);
    }
}).connect();
```

---

## Unofficial SDKs

### Rust: polymarket-rs (Recommended for Performance)

**Repository**: https://github.com/pawsengineer/polymarket-rs

**Benchmark Score**: 82.9 (highest among all SDKs)

**Features**:
- Full CLOB API support
- WebSocket streaming with auto-reconnection
- Type-safe with strongly typed builders
- Async/await with Tokio

**Installation** (Cargo.toml):
```toml
[dependencies]
polymarket-rs = "0.1"
tokio = { version = "1", features = ["full"] }
```

**Trading Example**:
```rust
use polymarket_rs::{AuthenticatedClient, TradingClient, OrderBuilder, SignatureType};

// Get API credentials
let auth_client = AuthenticatedClient::new(host, signer.clone(), chain_id, None, None);
let api_creds = auth_client.create_or_derive_api_key().await?;

// Create trading client
let order_builder = OrderBuilder::new(signer.clone(), Some(SignatureType::Eoa), None);
let trading_client = TradingClient::new(host, signer, chain_id, api_creds, order_builder);

// Place order
let order_args = OrderArgs::new(token_id, price, size, Side::Buy);
trading_client.create_and_post_order(&order_args, None, None, options, OrderType::Gtc).await?;
```

**WebSocket Streaming**:
```rust
use polymarket_rs::websocket::{MarketWsClient, ReconnectConfig, ReconnectingStream};

let client = MarketWsClient::new();
let config = ReconnectConfig::default();

let mut stream = ReconnectingStream::new(config, move || {
    client.subscribe(token_ids.clone())
});

while let Some(result) = stream.next().await {
    match result {
        Ok(WsEvent::Book(book)) => println!("Best bid: {}", book.bids[0].price),
        Ok(WsEvent::LastTradePrice(trade)) => println!("Trade: {} @ {}", trade.size, trade.price),
        Err(e) => eprintln!("Error: {}", e),
    }
}
```

### Python: PolyPy (High Performance)

**Repository**: https://github.com/hbr-l/polypy

**Benchmark Score**: 88.5 (highest Python SDK)

**Features**:
- Local order book management
- WebSocket streaming with hash verification
- Order/Position managers
- Higher performance than official client

**Installation**:
```bash
pip install polypy
```

**Complete Trading Bot**:
```python
import polypy as plp
from decimal import Decimal

# Create order book
book = plp.OrderBook(token_id="...", tick_size=0.01)

# Market stream (auto-updates order book)
market_stream = plp.MarketStream(
    ws_endpoint=plp.ENDPOINT.WS,
    books=book,
    rest_endpoint=plp.ENDPOINT.REST
)
market_stream.start()

# Order manager
order_manager = plp.OrderManager(
    rest_endpoint=plp.ENDPOINT.REST,
    private_key="...",
    api_key="...",
    secret="...",
    passphrase="...",
    maker_funder="wallet_addr",
    signature_type=plp.SIGNATURE_TYPE.POLY_PROXY,
    chain_id=plp.CHAIN_ID.POLYGON
)

# Position manager
position_manager = plp.PositionManager(
    rest_endpoint=plp.ENDPOINT.REST,
    gamma_endpoint=plp.ENDPOINT.GAMMA,
    usdc_position=100  # Starting balance
)

# User stream (auto-updates orders & positions)
user_stream = plp.UserStream(
    ws_endpoint=plp.ENDPOINT.WS,
    tuple_manager=(order_manager, position_manager),
    api_key="...",
    secret="...",
    passphrase="..."
)
user_stream.start()

# Place order
order, response = order_manager.limit_order(
    price=book.best_bid_price + book.tick_size,
    size=Decimal("10"),
    token_id="...",
    side=plp.SIDE.BUY,
    tick_size=book.tick_size,
    tif=plp.TIME_IN_FORCE.GTC
)
```

### Other SDKs

| SDK | Language | Benchmark | Features |
|-----|----------|-----------|----------|
| rs-clob-client | Rust | 66.2 | Official Rust, Alloy support |
| polymarket-go-gamma-client | Go | 59.4 | Gamma API only |
| polymarket-kit | TypeScript | 69.4 | Full SDK, proxy server |
| @dicedhq/polymarket | TypeScript | - | Deno, Bun, Workers support |

---

## SDK Comparison

| Language | Best SDK | Latency | Use Case |
|----------|----------|---------|----------|
| Rust | polymarket-rs | Lowest | HFT, market making |
| Python | PolyPy | Medium | Feature-rich bots |
| Python | py-clob-client | Medium | Simple bots, official |
| TypeScript | clob-client | Medium | Web apps, official |
