# E2B Monitoring and Events Reference

This guide provides comprehensive documentation for monitoring E2B sandboxes and handling lifecycle events through metrics, APIs, and webhooks.

## Table of Contents

- [Sandbox Metrics](#sandbox-metrics)
  - [Overview](#metrics-overview)
  - [Getting Metrics with SDKs](#getting-metrics-with-sdks)
  - [Getting Metrics with CLI](#getting-metrics-with-cli)
  - [Metrics Structure](#metrics-structure)
  - [Use Cases](#metrics-use-cases)
- [Lifecycle Events API](#lifecycle-events-api)
  - [Overview](#events-api-overview)
  - [REST API Endpoints](#rest-api-endpoints)
  - [Query Parameters](#query-parameters)
  - [Event Response Format](#event-response-format)
  - [Event Types](#event-types)
- [Webhooks](#webhooks)
  - [Overview](#webhooks-overview)
  - [Registering Webhooks](#registering-webhooks)
  - [Managing Webhooks](#managing-webhooks)
  - [Webhook Payload](#webhook-payload)
  - [Signature Verification](#signature-verification)
  - [Webhook Headers](#webhook-headers)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

---

## Sandbox Metrics

### Metrics Overview

Sandbox metrics provide real-time information about sandbox resource usage including:
- CPU utilization (percentage and core count)
- Memory usage (used and total, in bytes)
- Disk usage (used and total, in bytes)

**Key characteristics:**
- Metrics are collected every 5 seconds
- First metrics may take 1+ seconds to appear after sandbox creation
- Returns an array of timestamped metric snapshots
- Available via SDKs and CLI

### Getting Metrics with SDKs

#### JavaScript/TypeScript

```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sbx = await Sandbox.create()
console.log('Sandbox created', sbx.sandboxId)

// Wait for a few seconds to collect some metrics
await new Promise((resolve) => setTimeout(resolve, 10_000))

// Method 1: Get metrics from sandbox instance
const metrics = await sbx.getMetrics()

// Method 2: Get metrics by sandbox ID
// const metrics = await Sandbox.getMetrics(sbx.sandboxId)

console.log('Sandbox metrics:', metrics)
```

#### Python

```python
from e2b_code_interpreter import Sandbox
from time import sleep

sbx = Sandbox.create()
print(f'Sandbox created: {sbx.sandbox_id}')

# Wait for a few seconds to collect some metrics
sleep(10)

# Method 1: Get metrics from sandbox instance
metrics = sbx.get_metrics()

# Method 2: Get metrics by sandbox ID
# metrics = Sandbox.get_metrics(sbx.sandbox_id)

print('Sandbox metrics:', metrics)
```

### Getting Metrics with CLI

```bash
e2b sandbox metrics <sandbox_id>

# Example output:
# Metrics for sandbox <sandbox_id>
#
# [2025-07-25 14:05:55Z]  CPU:  8.27% /  2 Cores | Memory:    31 / 484   MiB | Disk:  1445 / 2453  MiB
# [2025-07-25 14:06:00Z]  CPU:   0.5% /  2 Cores | Memory:    32 / 484   MiB | Disk:  1445 / 2453  MiB
# [2025-07-25 14:06:05Z]  CPU:   0.1% /  2 Cores | Memory:    32 / 484   MiB | Disk:  1445 / 2453  MiB
# [2025-07-25 14:06:10Z]  CPU:   0.3% /  2 Cores | Memory:    32 / 484   MiB | Disk:  1445 / 2453  MiB
```

### Metrics Structure

Each metric snapshot includes:

**JavaScript response:**
```javascript
{
  timestamp: Date,          // 2025-07-28T08:04:05.000Z
  cpuUsedPct: number,       // CPU usage percentage (e.g., 20.33)
  cpuCount: number,         // Number of CPU cores (e.g., 2)
  memUsed: number,          // Memory used in bytes (e.g., 32681984)
  memTotal: number,         // Total memory in bytes (e.g., 507592704)
  diskUsed: number,         // Disk space used in bytes (e.g., 1514856448)
  diskTotal: number         // Total disk space in bytes (e.g., 2573185024)
}
```

**Python response:**
```python
SandboxMetric(
    cpu_count=2,
    cpu_used_pct=13.97,
    disk_total=2573185024,  # in bytes
    disk_used=1514856448,   # in bytes
    mem_total=507592704,    # in bytes
    mem_used=30588928,      # in bytes
    timestamp=datetime.datetime(2025, 7, 28, 8, 8, 15, tzinfo=tzutc()),
)
```

### Metrics Use Cases

1. **Performance Monitoring**: Track resource usage over time to identify bottlenecks
2. **Auto-scaling**: Trigger sandbox scaling based on resource thresholds
3. **Cost Optimization**: Identify underutilized sandboxes for termination
4. **Debugging**: Correlate application issues with resource constraints
5. **Capacity Planning**: Analyze historical metrics for infrastructure planning

**Example: Monitor high CPU usage**

```python
from e2b_code_interpreter import Sandbox
from time import sleep

sbx = Sandbox.create()

# Run some workload
sbx.run_code("import numpy as np; np.random.rand(1000, 1000) @ np.random.rand(1000, 1000)")

sleep(10)
metrics = sbx.get_metrics()

for metric in metrics:
    if metric.cpu_used_pct > 80:
        print(f"High CPU usage detected: {metric.cpu_used_pct}% at {metric.timestamp}")
```

---

## Lifecycle Events API

### Events API Overview

The Lifecycle Events API provides RESTful endpoints to query sandbox lifecycle events. This allows you to:
- Track when sandboxes are created, updated, or terminated
- Access historical event data with pagination
- Monitor all sandboxes or specific sandbox instances
- Integrate event data into custom monitoring dashboards

**Authentication:** All requests require your team API key in the `X-API-Key` header.

### REST API Endpoints

#### Get Events for a Specific Sandbox

```
GET https://api.e2b.app/events/sandboxes/{sandbox_id}
```

#### Get Events for All Team Sandboxes

```
GET https://api.e2b.app/events/sandboxes
```

### Query Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `offset` | integer | 0 | min: 0 | Number of events to skip (pagination) |
| `limit` | integer | 10 | min: 1, max: 100 | Number of events to return |
| `orderAsc` | boolean | false | - | Sort order: true=ascending, false=descending |

### Using the Lifecycle Events API

#### JavaScript/TypeScript

```javascript
import { Sandbox } from '@e2b/code-interpreter'

const E2B_API_KEY = process.env.E2B_API_KEY

const sbx = await Sandbox.create()

// Get events for a specific sandbox
const resp1 = await fetch(
  `https://api.e2b.app/events/sandboxes/${sbx.sandboxId}`,
  {
    method: 'GET',
    headers: {
      'X-API-Key': E2B_API_KEY,
    },
  }
)
const sandboxEvents = await resp1.json()
console.log('Sandbox events:', sandboxEvents)

// Get the latest 10 events for all team sandboxes
const resp2 = await fetch(
  'https://api.e2b.app/events/sandboxes?limit=10&orderAsc=false',
  {
    method: 'GET',
    headers: {
      'X-API-Key': E2B_API_KEY,
    },
  }
)
const teamEvents = await resp2.json()
console.log('Team events:', teamEvents)
```

#### Python

```python
import requests
import os

E2B_API_KEY = os.environ['E2B_API_KEY']

from e2b_code_interpreter import Sandbox

sbx = Sandbox.create()

# Get events for a specific sandbox
resp1 = requests.get(
    f'https://api.e2b.app/events/sandboxes/{sbx.sandbox_id}',
    headers={'X-API-Key': E2B_API_KEY}
)
sandbox_events = resp1.json()
print('Sandbox events:', sandbox_events)

# Get the latest 10 events for all team sandboxes
resp2 = requests.get(
    'https://api.e2b.app/events/sandboxes?limit=10&orderAsc=false',
    headers={'X-API-Key': E2B_API_KEY}
)
team_events = resp2.json()
print('Team events:', team_events)
```

### Event Response Format

Each event in the response array contains:

```json
{
  "version": "v1",
  "id": "f5911677-cb60-498f-afed-f68143b3cc59",
  "type": "sandbox.lifecycle.killed",
  "eventData": null,
  "sandboxBuildId": "a979a14b-bdcc-49e6-bc04-1189fc9fe7c2",
  "sandboxExecutionId": "1dae9e1c-9957-4ce7-a236-a99d5779aadf",
  "sandboxId": "your-sandbox-id",
  "sandboxTeamId": "460355b3-4f64-48f9-9a16-4442817f79f5",
  "sandboxTemplateId": "rki5dems9wqfm4r03t7g",
  "timestamp": "2025-08-06T20:59:36Z"
}
```

**Event with data (updated event):**

```json
{
  "version": "v1",
  "id": "30b09e11-9ba2-42db-9cf6-d21f0f43a234",
  "type": "sandbox.lifecycle.updated",
  "eventData": {
    "set_timeout": "2025-08-06T20:59:59Z"
  },
  "sandboxBuildId": "a979a14b-bdcc-49e6-bc04-1189fc9fe7c2",
  "sandboxExecutionId": "1dae9e1c-9957-4ce7-a236-a99d5779aadf",
  "sandboxId": "your-sandbox-id",
  "sandboxTeamId": "460355b3-4f64-48f9-9a16-4442817f79f5",
  "sandboxTemplateId": "rki5dems9wqfm4r03t7g",
  "timestamp": "2025-08-06T20:59:29Z"
}
```

### Event Types

The following event types are available:

- `sandbox.lifecycle.created` - Sandbox was created
- `sandbox.lifecycle.killed` - Sandbox was terminated
- `sandbox.lifecycle.updated` - Sandbox configuration was updated
- `sandbox.lifecycle.paused` - Sandbox was paused
- `sandbox.lifecycle.resumed` - Sandbox was resumed

---

## Webhooks

### Webhooks Overview

Webhooks provide real-time notifications when sandbox lifecycle events occur. Instead of polling the API, your server receives POST requests automatically when events happen.

**Benefits:**
- Real-time event delivery
- No polling overhead
- Automatic retry on failure (E2B handles this)
- Signature verification for security
- Filter by event types

**Authentication:** All webhook management requests require your team API key in the `X-API-Key` header.

### Registering Webhooks

To start receiving webhook notifications, register a webhook endpoint with E2B.

#### JavaScript/TypeScript

```javascript
const E2B_API_KEY = process.env.E2B_API_KEY

// Register a new webhook
const resp = await fetch(
  'https://api.e2b.app/events/webhooks',
  {
    method: 'POST',
    headers: {
      'X-API-Key': E2B_API_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name: 'My Sandbox Webhook',
      url: 'https://your-webhook-endpoint.com/webhook',
      enabled: true,
      events: [
        'sandbox.lifecycle.created',
        'sandbox.lifecycle.updated',
        'sandbox.lifecycle.killed'
      ],
      signatureSecret: 'secret-for-event-signature-verification'
    }),
  }
)

if (resp.status === 201) {
  console.log('Webhook registered successfully')
  const webhook = await resp.json()
  console.log('Webhook ID:', webhook.id)
}
```

#### Python

```python
import requests
import os

E2B_API_KEY = os.environ['E2B_API_KEY']

resp = requests.post(
    'https://api.e2b.app/events/webhooks',
    headers={
        'X-API-Key': E2B_API_KEY,
        'Content-Type': 'application/json',
    },
    json={
        'name': 'My Sandbox Webhook',
        'url': 'https://your-webhook-endpoint.com/webhook',
        'enabled': True,
        'events': [
            'sandbox.lifecycle.created',
            'sandbox.lifecycle.updated',
            'sandbox.lifecycle.killed'
        ],
        'signatureSecret': 'secret-for-event-signature-verification'
    }
)

if resp.status_code == 201:
    print('Webhook registered successfully')
    webhook = resp.json()
    print(f"Webhook ID: {webhook['id']}")
```

**Registration fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Human-readable webhook name |
| `url` | string | Yes | HTTPS endpoint to receive events |
| `enabled` | boolean | Yes | Whether webhook is active |
| `events` | array | Yes | List of event types to subscribe to |
| `signatureSecret` | string | Yes | Secret for signature verification |

### Managing Webhooks

#### List All Webhooks

```javascript
// JavaScript/TypeScript
const resp = await fetch(
  'https://api.e2b.app/events/webhooks',
  {
    method: 'GET',
    headers: {
      'X-API-Key': E2B_API_KEY
    },
  },
)

if (resp.status === 200) {
  const webhooks = await resp.json()
  console.log('Webhooks:', webhooks)
}
```

```python
# Python
resp = requests.get(
    'https://api.e2b.app/events/webhooks',
    headers={'X-API-Key': E2B_API_KEY}
)

if resp.status_code == 200:
    webhooks = resp.json()
    print('Webhooks:', webhooks)
```

#### Get Webhook Configuration

```javascript
// JavaScript/TypeScript
const webhookID = 'your-webhook-id'

const resp = await fetch(
  `https://api.e2b.app/events/webhooks/${webhookID}`,
  {
    method: 'GET',
    headers: {
      'X-API-Key': E2B_API_KEY,
    },
  }
)

const webhookConfig = await resp.json()
console.log(webhookConfig)
```

**Example response:**

```json
{
  "id": "webhook-id",
  "teamID": "your-team-id",
  "name": "My Sandbox Webhook",
  "createdAt": "2025-08-06T21:00:00Z",
  "enabled": true,
  "url": "https://your-webhook-endpoint.com/webhook",
  "events": ["sandbox.lifecycle.created", "sandbox.lifecycle.killed"]
}
```

#### Update Webhook Configuration

```javascript
// JavaScript/TypeScript
const resp = await fetch(
  `https://api.e2b.app/events/webhooks/${webhookID}`,
  {
    method: 'PATCH',
    headers: {
      'X-API-Key': E2B_API_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      url: 'https://your-updated-webhook-endpoint.com/webhook',
      enabled: false,
      events: ['sandbox.lifecycle.created']
    }),
  }
)

if (resp.status === 200) {
  console.log('Webhook updated successfully')
}
```

```python
# Python
resp = requests.patch(
    f'https://api.e2b.app/events/webhooks/{webhook_id}',
    headers={
        'X-API-Key': E2B_API_KEY,
        'Content-Type': 'application/json',
    },
    json={
        'url': 'https://your-updated-webhook-endpoint.com/webhook',
        'enabled': False,
        'events': ['sandbox.lifecycle.created']
    }
)

if resp.status_code == 200:
    print('Webhook updated successfully')
```

**Updatable fields:**
- `name`: Webhook name
- `url`: Endpoint URL
- `enabled`: Active status
- `events`: Event type subscriptions
- `signatureSecret`: Verification secret

#### Delete Webhook

```javascript
// JavaScript/TypeScript
const resp = await fetch(
  `https://api.e2b.app/events/webhooks/${webhookID}`,
  {
    method: 'DELETE',
    headers: {
      'X-API-Key': E2B_API_KEY,
    },
  }
)

if (resp.status === 200) {
  console.log('Webhook deleted successfully')
}
```

```python
# Python
resp = requests.delete(
    f'https://api.e2b.app/events/webhooks/{webhook_id}',
    headers={'X-API-Key': E2B_API_KEY}
)

if resp.status_code == 200:
    print('Webhook deleted successfully')
```

### Webhook Payload

When a subscribed event occurs, E2B sends a POST request to your webhook URL with the following JSON payload:

```json
{
  "version": "v1",
  "id": "event-id",
  "type": "sandbox.lifecycle.created",
  "eventData": {
    "sandbox_metadata": {
      "custom-key": "custom-value"
    }
  },
  "sandboxBuildId": "template-build-id",
  "sandboxExecutionId": "sandbox-unique-execution-id",
  "sandboxId": "your-sandbox-id",
  "sandboxTeamId": "your-team-id",
  "sandboxTemplateId": "your-template-id",
  "timestamp": "2025-08-06T20:59:24Z"
}
```

**Payload fields:**

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Event schema version (currently "v1") |
| `id` | string | Unique event identifier |
| `type` | string | Event type (e.g., "sandbox.lifecycle.created") |
| `eventData` | object | Additional event-specific data |
| `sandboxBuildId` | string | Template build identifier |
| `sandboxExecutionId` | string | Unique execution instance ID |
| `sandboxId` | string | Sandbox identifier |
| `sandboxTeamId` | string | Your team identifier |
| `sandboxTemplateId` | string | Template identifier |
| `timestamp` | string | ISO 8601 timestamp |

### Signature Verification

To ensure webhook requests are authentic and from E2B, verify the signature included in the `e2b-signature` header.

**Signature generation algorithm:**
1. Concatenate: `secret + payload`
2. Compute SHA-256 hash
3. Base64 encode the hash
4. Remove padding `=`
5. Compare with `e2b-signature` header

#### JavaScript/TypeScript

```javascript
import crypto from 'crypto'

function verifyWebhookSignature(secret, payload, payloadSignature) {
  const expectedSignatureRaw = crypto
    .createHash('sha256')
    .update(secret + payload)
    .digest('base64')

  const expectedSignature = expectedSignatureRaw.replace(/=+$/, '')

  return expectedSignature === payloadSignature
}

// Express.js example
app.post('/webhook', express.raw({ type: 'application/json' }), (req, res) => {
  const webhookBodyRaw = req.body.toString()
  const webhookSignatureHeader = req.headers['e2b-signature']
  const secret = process.env.WEBHOOK_SECRET

  const payloadValid = verifyWebhookSignature(
    secret,
    webhookBodyRaw,
    webhookSignatureHeader
  )

  if (payloadValid) {
    console.log("Payload signature is valid")
    const event = JSON.parse(webhookBodyRaw)

    switch (event.type) {
      case 'sandbox.lifecycle.created':
        console.log('Sandbox created:', event.sandboxId)
        break
      case 'sandbox.lifecycle.killed':
        console.log('Sandbox killed:', event.sandboxId)
        break
    }

    res.status(200).send('OK')
  } else {
    console.log("Payload signature is INVALID")
    res.status(401).send('Unauthorized')
  }
})
```

#### Python

```python
import hashlib
import base64

def verify_webhook_signature(secret: str, payload: str, payload_signature: str) -> bool:
    """Verify the webhook signature from E2B."""
    hash_bytes = hashlib.sha256(
        (secret + payload).encode('utf-8')
    ).digest()

    expected_signature = base64.b64encode(hash_bytes).decode('utf-8')
    expected_signature = expected_signature.rstrip('=')

    return expected_signature == payload_signature

if verify_webhook_signature(secret, webhook_body_raw, webhook_signature_header):
    print("Payload signature is valid")
else:
    print("Payload signature is INVALID")
```

#### Go

```go
import (
    "crypto/sha256"
    "encoding/base64"
    "strings"
)

func verifyWebhookSignature(secret, payload, payloadSignature string) bool {
    hash := sha256.Sum256([]byte(secret + payload))
    expectedSignature := base64.StdEncoding.EncodeToString(hash[:])
    expectedSignature = strings.TrimRight(expectedSignature, "=")
    return expectedSignature == payloadSignature
}
```

### Webhook Headers

E2B includes these headers with every webhook request:

| Header | Description |
|--------|-------------|
| `e2b-webhook-id` | Webhook ID that triggered the event |
| `e2b-delivery-id` | Unique ID for this delivery attempt |
| `e2b-signature-version` | Signature version (currently always "v1") |
| `e2b-signature` | Signature for verifying the request authenticity |

---

## Common Patterns

### Pattern 1: Monitor Sandbox Lifecycle with Metrics

Track a sandbox from creation to termination with resource monitoring:

```python
from e2b_code_interpreter import Sandbox
from time import sleep

def monitor_sandbox_lifecycle(duration_seconds=60):
    """Monitor a sandbox with metrics collection."""
    sbx = Sandbox.create()
    print(f"Sandbox {sbx.sandbox_id} created")

    start_time = time.time()

    # Run some workload
    sbx.run_code("""
import time
for i in range(100):
    sum([x**2 for x in range(1000)])
    time.sleep(0.5)
    """)

    # Collect metrics periodically
    while time.time() - start_time < duration_seconds:
        sleep(10)
        metrics = sbx.get_metrics()

        if metrics:
            latest = metrics[-1]
            print(f"CPU: {latest.cpu_used_pct:.2f}% | "
                  f"Memory: {latest.mem_used / 1024 / 1024:.2f} MB | "
                  f"Disk: {latest.disk_used / 1024 / 1024:.2f} MB")

    sbx.kill()
    print(f"Sandbox {sbx.sandbox_id} terminated")

monitor_sandbox_lifecycle()
```

### Pattern 2: Event-Driven Sandbox Management

Use webhooks to maintain a dashboard of active sandboxes:

```javascript
// server.js - Webhook receiver
import express from 'express'

const app = express()
const activeSandboxes = new Map()

app.post('/webhook', express.raw({ type: 'application/json' }), (req, res) => {
  const payload = req.body.toString()
  const signature = req.headers['e2b-signature']
  const secret = process.env.WEBHOOK_SECRET

  if (!verifyWebhookSignature(secret, payload, signature)) {
    return res.status(401).send('Unauthorized')
  }

  const event = JSON.parse(payload)

  switch (event.type) {
    case 'sandbox.lifecycle.created':
      activeSandboxes.set(event.sandboxId, {
        id: event.sandboxId,
        createdAt: event.timestamp,
        templateId: event.sandboxTemplateId
      })
      console.log(`Active sandboxes: ${activeSandboxes.size}`)
      break

    case 'sandbox.lifecycle.killed':
      activeSandboxes.delete(event.sandboxId)
      console.log(`Active sandboxes: ${activeSandboxes.size}`)
      break

    case 'sandbox.lifecycle.updated':
      const sandbox = activeSandboxes.get(event.sandboxId)
      if (sandbox) {
        sandbox.lastUpdated = event.timestamp
        sandbox.updateData = event.eventData
      }
      break
  }

  res.status(200).send('OK')
})

app.get('/dashboard', (req, res) => {
  res.json({
    activeCount: activeSandboxes.size,
    sandboxes: Array.from(activeSandboxes.values())
  })
})

app.listen(3000, () => console.log('Webhook server running on port 3000'))
```

### Pattern 3: Historical Event Analysis

Query lifecycle events to analyze sandbox usage patterns:

```python
import requests
import os
from datetime import datetime, timedelta
from collections import Counter

E2B_API_KEY = os.environ['E2B_API_KEY']

def analyze_sandbox_usage(days=7):
    """Analyze sandbox creation patterns over the last N days."""
    all_events = []
    offset = 0
    limit = 100

    while True:
        resp = requests.get(
            f'https://api.e2b.app/events/sandboxes?limit={limit}&offset={offset}',
            headers={'X-API-Key': E2B_API_KEY}
        )
        events = resp.json()

        if not events:
            break

        all_events.extend(events)
        offset += limit

    cutoff_date = datetime.utcnow() - timedelta(days=days)
    recent_events = [
        e for e in all_events
        if datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00')) > cutoff_date
    ]

    event_counts = Counter(e['type'] for e in recent_events)

    print(f"Sandbox events in last {days} days:")
    for event_type, count in event_counts.items():
        print(f"  {event_type}: {count}")

    template_counts = Counter(e['sandboxTemplateId'] for e in recent_events)
    print(f"\nMost used templates:")
    for template_id, count in template_counts.most_common(5):
        print(f"  {template_id}: {count}")

analyze_sandbox_usage(7)
```

---

## Troubleshooting

### Metrics Issues

#### Problem: Empty metrics array

**Solutions:**
1. Wait longer - metrics collection starts after sandbox creation (1+ seconds)
2. Check sandbox is still running - terminated sandboxes don't collect metrics
3. Verify sandbox ID is correct when using static method

```python
sbx = Sandbox.create()
sleep(2)  # Wait for first collection cycle
metrics = sbx.get_metrics()

if not metrics:
    print("No metrics yet, waiting longer...")
    sleep(5)
    metrics = sbx.get_metrics()
```

### Lifecycle Events API Issues

#### Problem: 401 Unauthorized

**Solutions:**
1. Verify API key is correct: `echo $E2B_API_KEY`
2. Check header format: `X-API-Key` (capital K)
3. Ensure API key has not expired

### Webhook Issues

#### Problem: Webhooks not received

**Solutions:**
1. Verify webhook is enabled: `GET /events/webhooks/{id}`
2. Check URL is publicly accessible (use ngrok for local testing)
3. Ensure URL uses HTTPS (HTTP not supported)
4. Check firewall/security group settings
5. Verify event types are subscribed

#### Problem: Signature verification fails

**Solutions:**
1. Verify you're using the raw request body (not parsed JSON)
2. Check secret matches registration
3. Ensure signature header is read correctly
4. Verify base64 encoding is correct (remove padding `=` only)

---

## Summary

This guide covered three complementary approaches to E2B monitoring:

1. **Metrics**: Real-time resource monitoring (CPU, memory, disk) collected every 5 seconds
2. **Lifecycle Events API**: RESTful polling for historical event data with pagination
3. **Webhooks**: Real-time push notifications for sandbox lifecycle events

**When to use each:**

- **Metrics**: Monitor resource usage, auto-scaling, performance optimization
- **Events API**: Historical analysis, auditing, batch processing
- **Webhooks**: Real-time alerts, event-driven architectures, dashboards

**Key takeaways:**

- Metrics provide performance data, events provide lifecycle data
- Always verify webhook signatures for security
- Use pagination when querying events API
- Metrics take 1+ seconds to appear after sandbox creation
- Webhooks require HTTPS endpoints
- All APIs require team API key authentication

For more information, visit [E2B documentation](https://e2b.dev/docs).
