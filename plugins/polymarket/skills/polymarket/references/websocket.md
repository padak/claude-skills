# Polymarket WebSocket Streaming

## Table of Contents
- [Endpoints](#endpoints)
- [Market Channel](#market-channel)
- [User Channel](#user-channel)
- [Message Types](#message-types)
- [Keep-Alive](#keep-alive)
- [Python Example](#python-example)

---

## Endpoints

| Channel | URL | Purpose |
|---------|-----|---------|
| Market | `wss://ws-subscriptions-clob.polymarket.com/ws/market` | Order book, trades |
| User | `wss://ws-subscriptions-clob.polymarket.com/ws/user` | Orders, fills (auth) |
| Live Data | `wss://ws-live-data.polymarket.com` | Activity streams |

---

## Market Channel

**URL**: `wss://ws-subscriptions-clob.polymarket.com/ws/market`

**Subscription Message**:
```json
{
    "assets_ids": ["<token-id-1>", "<token-id-2>"],
    "type": "market"
}
```

**Events Received**:
- Order book updates
- Trade executions
- Price changes

---

## User Channel

**URL**: `wss://ws-subscriptions-clob.polymarket.com/ws/user`

**Subscription Message** (requires authentication):
```json
{
    "markets": ["<condition-id-1>"],
    "type": "user",
    "auth": {
        "apiKey": "your-api-key",
        "secret": "your-secret",
        "passphrase": "your-passphrase"
    }
}
```

**Events Received**:
- Order status updates
- Fill notifications
- Position changes

---

## Message Types

### Trade Message
```json
{
  "asset": "12345",
  "side": "BUY",
  "size": 10,
  "price": 0.75,
  "timestamp": 1678886400,
  "transactionHash": "0xabc123..."
}
```

### Order Book Update
```json
{
  "type": "book",
  "market": "0x...",
  "bids": [{"price": "0.50", "size": "100"}],
  "asks": [{"price": "0.52", "size": "150"}]
}
```

### Last Trade Price
```json
{
  "type": "last_trade_price",
  "asset": "12345",
  "price": "0.75",
  "size": "10"
}
```

---

## Keep-Alive

Send `PING` every 10 seconds to maintain connection:

```python
import asyncio

async def keep_alive(ws):
    while True:
        await ws.send("PING")
        await asyncio.sleep(10)
```

---

## Python Example

### Basic Market Stream

```python
import asyncio
import json
import websockets

async def stream_market(token_ids: list[str]):
    uri = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

    async with websockets.connect(uri) as ws:
        # Subscribe
        await ws.send(json.dumps({
            "assets_ids": token_ids,
            "type": "market"
        }))

        # Keep-alive task
        async def ping():
            while True:
                await ws.send("PING")
                await asyncio.sleep(10)

        ping_task = asyncio.create_task(ping())

        try:
            async for message in ws:
                if message == "PONG":
                    continue
                data = json.loads(message)
                print(f"Event: {data}")
        finally:
            ping_task.cancel()

# Run
asyncio.run(stream_market(["token-id-1", "token-id-2"]))
```

### Authenticated User Stream

```python
async def stream_user(condition_ids: list[str], api_key: str, secret: str, passphrase: str):
    uri = "wss://ws-subscriptions-clob.polymarket.com/ws/user"

    async with websockets.connect(uri) as ws:
        # Subscribe with auth
        await ws.send(json.dumps({
            "markets": condition_ids,
            "type": "user",
            "auth": {
                "apiKey": api_key,
                "secret": secret,
                "passphrase": passphrase
            }
        }))

        async for message in ws:
            if message == "PONG":
                continue
            data = json.loads(message)

            if data.get("type") == "order_update":
                print(f"Order: {data['orderId']} - {data['status']}")
            elif data.get("type") == "fill":
                print(f"Fill: {data['size']} @ {data['price']}")
```

### Order Book Maintenance

```python
from dataclasses import dataclass, field

@dataclass
class LocalOrderBook:
    token_id: str
    bids: dict = field(default_factory=dict)  # price -> size
    asks: dict = field(default_factory=dict)

    def update(self, event: dict):
        """Apply WebSocket update to local book."""
        if "bids" in event:
            for bid in event["bids"]:
                price = bid["price"]
                size = float(bid["size"])
                if size == 0:
                    self.bids.pop(price, None)
                else:
                    self.bids[price] = size

        if "asks" in event:
            for ask in event["asks"]:
                price = ask["price"]
                size = float(ask["size"])
                if size == 0:
                    self.asks.pop(price, None)
                else:
                    self.asks[price] = size

    @property
    def best_bid(self) -> float:
        return max(float(p) for p in self.bids.keys()) if self.bids else 0.0

    @property
    def best_ask(self) -> float:
        return min(float(p) for p in self.asks.keys()) if self.asks else 1.0

async def maintain_book(token_id: str):
    book = LocalOrderBook(token_id)
    uri = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            "assets_ids": [token_id],
            "type": "market"
        }))

        async for message in ws:
            if message == "PONG":
                continue
            event = json.loads(message)

            if event.get("type") == "book":
                book.update(event)
                print(f"Spread: {book.best_bid} - {book.best_ask}")
```

### Reconnection Pattern

```python
async def resilient_stream(token_ids: list[str], on_message):
    uri = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

    while True:
        try:
            async with websockets.connect(uri) as ws:
                await ws.send(json.dumps({
                    "assets_ids": token_ids,
                    "type": "market"
                }))

                async for message in ws:
                    if message != "PONG":
                        await on_message(json.loads(message))

        except websockets.ConnectionClosed:
            print("Connection closed, reconnecting in 1s...")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error: {e}, reconnecting in 5s...")
            await asyncio.sleep(5)
```
