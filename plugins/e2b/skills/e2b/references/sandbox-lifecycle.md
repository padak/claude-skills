# Sandbox Lifecycle Management

## Overview

E2B sandboxes are isolated VMs with configurable lifetimes. Understanding lifecycle management is crucial for efficient resource usage.

**SDK v2 Breaking Change:** Python now uses `Sandbox.create()` instead of the `Sandbox()` constructor. Both Python and JavaScript use `Sandbox.create()`.

## Creating Sandboxes

### Default Creation

**Python:**
```python
from e2b_code_interpreter import Sandbox

# Create with default 5 minute timeout
sandbox = Sandbox.create()
print(sandbox.sandbox_id)
```

**JavaScript:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

// Create with default 5 minute timeout
const sandbox = await Sandbox.create()
console.log(sandbox.sandboxId)
```

### Custom Timeout

**Python:**
```python
# Timeout in seconds
sandbox = Sandbox.create(timeout=60)  # 60 seconds
```

**JavaScript:**
```javascript
// Timeout in milliseconds
const sandbox = await Sandbox.create({
  timeoutMs: 60_000  // 60 seconds
})
```

### Maximum Sandbox Running Time

- **Pro Tier:** 24 hours maximum without being paused
- **Base Tier:** 1 hour maximum without being paused

### Environment Variables on Creation

You can set global environment variables when creating a sandbox:

**Python:**
```python
sandbox = Sandbox.create(
    envs={
        'MY_VAR': 'my_value',
    },
)
```

**JavaScript:**
```javascript
const sandbox = await Sandbox.create({
  envs: {
    MY_VAR: 'my_value',
  },
})
```

You can also set environment variables per code execution or per command execution (see E2B docs for details).

**Default Environment Variables Inside Sandbox:**
- `E2B_SANDBOX` - set to `true` so processes know they are inside a sandbox
- `E2B_SANDBOX_ID` - the sandbox ID
- `E2B_TEAM_ID` - the team ID that created the sandbox
- `E2B_TEMPLATE_ID` - the template used for the sandbox

## Managing Timeout During Runtime

You can change the sandbox timeout while it's running. This resets the timeout to the new value from the current moment.

**Python:**
```python
# Change timeout to 30 seconds from now
sandbox.set_timeout(30)
```

**JavaScript:**
```javascript
// Change timeout to 30 seconds from now
await sandbox.setTimeout(30_000)  // milliseconds
```

**Use Cases:**
- Extend lifetime when user interacts with your app
- Periodically reset timeout for long-running sessions
- Shorten timeout when task is nearly complete

## Getting Sandbox Information

**Python:**
```python
info = sandbox.get_info()
print(info)

# SandboxInfo(sandbox_id='ig6f1yt6idvxkxl562scj-419ff533',
#   template_id='u7nqkmpn3jjf1tvftlsu',
#   name='base',
#   metadata={},
#   started_at=datetime.datetime(2025, 3, 24, 15, 42, 59, 255612, tzinfo=tzutc()),
#   end_at=datetime.datetime(2025, 3, 24, 15, 47, 59, 255612, tzinfo=tzutc())
# )
```

**JavaScript:**
```javascript
const info = await sandbox.getInfo()
console.log(info)

// {
//   "sandboxId": "iiny0783cype8gmoawzmx-ce30bc46",
//   "templateId": "rki5dems9wqfm4r03t7g",
//   "name": "base",
//   "metadata": {},
//   "startedAt": "2025-03-24T15:37:58.076Z",
//   "endAt": "2025-03-24T15:42:58.076Z"
// }
```

## Connecting to a Running Sandbox

If you have a running sandbox, you can connect to it using `Sandbox.connect()` with the sandbox ID.

### 1. Get the Sandbox ID

**Python:**
```python
from e2b_code_interpreter import Sandbox

sbx = Sandbox.create()

# Get all running sandboxes
paginator = Sandbox.list()
running_sandboxes = paginator.next_items()
if len(running_sandboxes) == 0:
    raise Exception("No running sandboxes found")

sandbox_id = running_sandboxes[0].sandbox_id
```

**JavaScript:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sbx = await Sandbox.create()

// Get all running sandboxes
const paginator = await Sandbox.list({
  query: { state: ['running'] },
})
const runningSandboxes = await paginator.nextItems()
if (runningSandboxes.length === 0) {
  throw new Error('No running sandboxes found')
}

const sandboxId = runningSandboxes[0].sandboxId
```

### 2. Connect to the Sandbox

**Python:**
```python
from e2b_code_interpreter import Sandbox

sandbox = Sandbox.connect(sandbox_id)

# Now you can use the sandbox as usual
r = sandbox.commands.run("whoami")
print(f"Running in sandbox {sandbox.sandbox_id} as \"{r.stdout.strip()}\"")
```

**JavaScript:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.connect(sandboxId)

// Now you can use the sandbox as usual
const result = await sandbox.commands.run("whoami")
console.log(`Running in sandbox ${sandbox.sandboxId} as "${result.stdout.trim()}"`)
```

## Shutting Down Sandboxes

Always shut down sandboxes when finished to free resources and avoid unnecessary charges.

### Manual Shutdown

**Python:**
```python
# Shutdown immediately
sandbox.kill()

# Or by ID
Sandbox.kill(sandbox_id)
```

**JavaScript:**
```javascript
// Shutdown immediately
await sandbox.kill()

// Or by ID
await Sandbox.kill(sandboxId)
```

### Using Context Manager (Python)

Recommended approach for automatic cleanup:

```python
with Sandbox.create() as sandbox:
    # Do work
    execution = sandbox.run_code(code)
    # Sandbox automatically killed when exiting context
```

### Try-Finally Pattern

For languages without context managers or when more control is needed:

**Python:**
```python
sandbox = Sandbox.create()
try:
    # Do work
    execution = sandbox.run_code(code)
finally:
    sandbox.kill()  # Always executed
```

**JavaScript:**
```javascript
const sandbox = await Sandbox.create()
try {
  // Do work
  const execution = await sandbox.runCode(code)
} finally {
  await sandbox.kill()  // Always executed
}
```

## Internet Access and Network Control

Every sandbox has internet access enabled by default and can be reached by a public URL.

### Controlling Internet Access

**Python:**
```python
# Create sandbox with internet access enabled (default)
sandbox = Sandbox.create(allow_internet_access=True)

# Create sandbox without internet access
isolated_sandbox = Sandbox.create(allow_internet_access=False)
```

**JavaScript:**
```javascript
// Create sandbox with internet access enabled (default)
const sandbox = await Sandbox.create({ allowInternetAccess: true })

// Create sandbox without internet access
const isolatedSandbox = await Sandbox.create({ allowInternetAccess: false })
```

### Fine-Grained Network Control

You can use `network` configuration for allow/deny lists with IPs, CIDR blocks, or domain names:

**Python:**
```python
from e2b_code_interpreter import Sandbox, ALL_TRAFFIC

# Deny all traffic except specific IPs
sandbox = Sandbox.create(
    network={
        "deny_out": [ALL_TRAFFIC],
        "allow_out": ["1.1.1.1", "8.8.8.0/24"]
    }
)

# Domain-based filtering (must use ALL_TRAFFIC in deny_out)
sandbox = Sandbox.create(
    network={
        "allow_out": ["api.example.com", "*.github.com"],
        "deny_out": [ALL_TRAFFIC]
    }
)
```

**JavaScript:**
```javascript
import { Sandbox, ALL_TRAFFIC } from '@e2b/code-interpreter'

// Deny all traffic except specific IPs
const sandbox = await Sandbox.create({
  network: {
    denyOut: [ALL_TRAFFIC],
    allowOut: ['1.1.1.1', '8.8.8.0/24']
  }
})

// Domain-based filtering (must use ALL_TRAFFIC in denyOut)
const sandbox2 = await Sandbox.create({
  network: {
    allowOut: ['api.example.com', '*.github.com'],
    denyOut: [ALL_TRAFFIC]
  }
})
```

**Network Priority Rules:** Allow rules always take precedence over deny rules. If an IP is in both lists, it will be allowed.

**Domain Filtering Notes:**
- Domain filtering only works for HTTP (port 80, via Host header) and TLS (port 443, via SNI)
- Traffic on other ports uses CIDR-based filtering only
- UDP-based protocols like QUIC/HTTP3 are not supported for domain filtering
- When any domain is used, the default nameserver `8.8.8.8` is automatically allowed

### Sandbox Public URL

```python
sandbox = Sandbox.create()
host = sandbox.get_host(3000)
print(f'https://{host}')
# Output: https://3000-i62mff4ahtrdfdkyn2esc.e2b.app
```

```javascript
const sandbox = await Sandbox.create()
const host = sandbox.getHost(3000)
console.log(`https://${host}`)
// Output: https://3000-i62mff4ahtrdfdkyn2esc.e2b.app
```

### Restricting Public Access to Sandbox URLs

**Python:**
```python
sandbox = Sandbox.create(
    network={
        "allow_public_traffic": False
    }
)

# Access requires the traffic access token header
print(sandbox.traffic_access_token)

# Request with token
import requests
host = sandbox.get_host(8080)
url = f"https://{host}"
response = requests.get(url, headers={
    'e2b-traffic-access-token': sandbox.traffic_access_token
})
```

**JavaScript:**
```javascript
const sandbox = await Sandbox.create({
  network: {
    allowPublicTraffic: false
  }
})

// Access requires the traffic access token header
console.log(sandbox.trafficAccessToken)

// Request with token
const host = sandbox.getHost(8080)
const url = `https://${host}`
const response = await fetch(url, {
  headers: {
    'e2b-traffic-access-token': sandbox.trafficAccessToken
  }
})
```

### Host Header Masking

You can customize the `Host` header sent to services inside the sandbox:

**Python:**
```python
sandbox = Sandbox.create(
    network={
        "mask_request_host": "localhost:${PORT}"
    }
)
# Requests will have Host header set to e.g. localhost:8080
```

**JavaScript:**
```javascript
const sandbox = await Sandbox.create({
  network: {
    maskRequestHost: 'localhost:${PORT}'
  }
})
```

## Secured Access (SDK v2.0.0+ Default)

Secure access authenticates communication between the SDK and the sandbox controller. Without it, anyone with a sandbox ID can access the controller APIs and control the sandbox from inside.

**SDK v2.0.0 and above enable secure access by default.** This may not be compatible with older custom templates -- you may need to rebuild them.

### Migration from Older Templates

When using custom templates created before envd `v0.2.0`, you need to rebuild them to enable secure access. Temporarily, you can disable secure access during sandbox creation (not recommended for production):

**Python:**
```python
sandbox = Sandbox.create(secure=False)  # Explicitly disable (not recommended)
```

**JavaScript:**
```javascript
const sandbox = await Sandbox.create({ secure: false }) // Explicitly disable (not recommended)
```

### Direct API Access with Secure Access

When secure access is enabled and you access sandbox controller APIs directly (not via SDK), you must include the `X-Access-Token` header with the access token returned during sandbox creation.

## Sandbox States

Sandboxes can be in one of three states:

1. **Running** - Actively executing and consuming resources
2. **Paused** - Suspended but state preserved (Beta feature)
3. **Killed** - Terminated, all resources released (terminal state)

### State Transitions

```
              create()
                 |
             [Running]
                 |
         +-------+-------+
         |               |
  beta_pause()       kill()
         |               |
     [Paused]      [Killed]
         |
    connect()
         |
     [Running]
```

## Rate Limits

### Limits by Plan

| Limit                              | Hobby        | Pro                    | Enterprise |
|------------------------------------|--------------|------------------------|------------|
| Sandbox lifecycle & management API | 20,000 / 30s | 20,000 / 30s          | Custom     |
| Sandbox operations                 | 40,000 / 60s per IP | 40,000 / 60s per IP | Custom     |
| Concurrent sandboxes               | 20           | 100 - 1,100 (add-on)  | Custom     |
| Sandbox creation rate              | 1 / sec      | 5 / sec                | Custom     |
| Egress connections per sandbox     | 2,500        | 2,500                  | Custom     |

### Rate Limit Details

- **Sandbox lifecycle & management API:** 20,000 requests per 30 seconds. Applies to create, kill, update, list operations.
- **Sandbox operations:** 40,000 requests per 60 seconds per IP. Applies to running code, listing files, running commands, and requests to custom ports.
- **Concurrent sandboxes:** Hobby = 20, Pro = 100 (up to 1,100 with purchasable add-on), Enterprise = custom (1,100+).
- **Sandbox creation rate:** Hobby = 1/sec, Pro = 5/sec, Enterprise = custom (5+/sec).
- **Egress connections:** 2,500 outbound connections per sandbox.

### When Limits Are Reached

- HTTP API returns `429 Too Many Requests`
- JS/TS SDK raises `RateLimitError`
- Python SDK raises `RateLimitException`

## Best Practices

### 1. Choose Appropriate Timeouts

```python
# Short task: 60-120 seconds
sandbox = Sandbox.create(timeout=60)

# Data analysis: 300-600 seconds
sandbox = Sandbox.create(timeout=300)

# Interactive session: Use auto-pause
sandbox = Sandbox.beta_create(
    auto_pause=True,
    timeout=600
)
```

### 2. Always Clean Up

```python
# Good: Automatic cleanup
with Sandbox.create() as sandbox:
    result = sandbox.run_code(code)

# Also good: Explicit cleanup
sandbox = Sandbox.create()
try:
    result = sandbox.run_code(code)
finally:
    sandbox.kill()

# Bad: No cleanup (sandbox times out eventually but wastes resources)
sandbox = Sandbox.create()
result = sandbox.run_code(code)
# Missing cleanup!
```

### 3. Track Sandbox IDs

For long-running or persisted sandboxes:

```python
# Save ID for later reconnection
sandbox = Sandbox.create()
sandbox_id = sandbox.sandbox_id
save_to_database(user_id, sandbox_id)

# Later: Reconnect
saved_id = load_from_database(user_id)
sandbox = Sandbox.connect(saved_id)
```

### 4. Handle Timeout Gracefully

```python
from e2b_code_interpreter.exceptions import TimeoutException

try:
    execution = sandbox.run_code(long_running_code)
except TimeoutException:
    print("Code execution timed out")
    # Handle appropriately
```

## Auto-Pause Feature (Beta)

For interactive applications where users may be inactive:

**Python:**
```python
# Create with auto-pause
sandbox = Sandbox.beta_create(
    auto_pause=True,
    timeout=10 * 60  # 10 minutes of inactivity
)

# Sandbox automatically pauses after timeout
# Instead of being killed
```

**JavaScript:**
```javascript
// Create with auto-pause
const sandbox = await Sandbox.betaCreate({
    autoPause: true,
    timeoutMs: 10 * 60 * 1000  // 10 minutes
})
```

**Key Points:**
- Sandbox pauses automatically after timeout
- Auto-pause persists across resume
- Calling `kill()` permanently deletes the sandbox
- Paused sandboxes can be resumed later

## Common Patterns

### Pattern 1: Quick One-Off Execution

```python
with Sandbox.create() as sandbox:
    result = sandbox.run_code(code)
    return result.text
```

### Pattern 2: Multi-Step Processing

```python
sandbox = Sandbox.create(timeout=300)
try:
    # Step 1
    sandbox.run_code(setup_code)

    # Step 2
    sandbox.files.write('/home/user/data.csv', data)

    # Step 3
    result = sandbox.run_code(analysis_code)

    return result
finally:
    sandbox.kill()
```

### Pattern 3: Interactive Session

```python
# Create with auto-pause
sandbox = Sandbox.beta_create(
    auto_pause=True,
    timeout=600
)

# User does work
result = sandbox.run_code(code)

# User goes inactive -> sandbox auto-pauses

# User returns -> reconnect
sandbox = Sandbox.connect(sandbox.sandbox_id)

# Continue work
result = sandbox.run_code(next_code)
```

### Pattern 4: Isolated Sandbox (No Internet)

```python
from e2b_code_interpreter import Sandbox, ALL_TRAFFIC

sandbox = Sandbox.create(
    allow_internet_access=False
)
# or for fine-grained control:
sandbox = Sandbox.create(
    network={
        "deny_out": [ALL_TRAFFIC],
        "allow_out": ["api.myservice.com"]
    }
)
```

## Monitoring and Debugging

### Check Remaining Time

```python
info = sandbox.get_info()
started_at = info.started_at
end_at = info.end_at

from datetime import datetime, timezone
remaining = end_at - datetime.now(timezone.utc)
print(f"Sandbox will timeout in {remaining.total_seconds()} seconds")
```

### List All Sandboxes

```python
# List running sandboxes
paginator = Sandbox.list()
sandboxes = paginator.next_items()

for sb in sandboxes:
    print(f"ID: {sb.sandbox_id}, Started: {sb.started_at}")
```

## Troubleshooting

### Sandbox Times Out Too Quickly
- Increase timeout on creation
- Reset timeout periodically during long operations
- Consider using auto-pause for interactive sessions

### Can't Reconnect to Sandbox
- Check if sandbox was killed (not paused)
- Verify sandbox hasn't exceeded maximum running time (24h Pro / 1h Base)
- Ensure sandbox ID is correct

### Memory/Resource Issues
- Kill unused sandboxes promptly
- Don't create too many sandboxes concurrently (check rate limits for your plan)
- Use pause/resume instead of keeping multiple sandboxes running

### Rate Limit Errors
- Check if you've exceeded concurrent sandbox limits for your plan
- Reduce sandbox creation rate (Hobby: 1/sec, Pro: 5/sec)
- Handle `RateLimitException` (Python) or `RateLimitError` (JS/TS) in your code
- Consider upgrading plan or purchasing concurrency add-ons

### Secured Access Issues (SDK v2)
- If using custom templates created before envd v0.2.0, rebuild them
- Check envd version with `e2b template list` or dashboard
- Temporarily disable with `secure=False` for debugging (not for production)
