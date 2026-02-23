# Advanced Sandbox Management

This guide covers advanced sandbox management capabilities in E2B, including listing, filtering, connecting to running sandboxes, metadata tracking, environment variable management, storage bucket integration, SSH access, interactive terminals (PTY), proxy tunneling, custom domains, and secured access.

## Table of Contents

- [Listing Sandboxes](#listing-sandboxes)
- [Metadata](#metadata)
- [Connecting to Running Sandboxes](#connecting-to-running-sandboxes)
- [Environment Variables](#environment-variables)
- [Storage Bucket Integration](#storage-bucket-integration)
- [SSH Access](#ssh-access)
- [Interactive Terminal (PTY)](#interactive-terminal-pty)
- [Proxy Tunneling](#proxy-tunneling)
- [Custom Domain](#custom-domain)
- [Secured Access](#secured-access)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

## Listing Sandboxes

The `Sandbox.list()` method provides paginated access to your sandboxes with support for filtering by state and metadata.

### Basic Listing

**Python:**
```python
from e2b_code_interpreter import Sandbox, SandboxInfo

sandbox = Sandbox.create(
    metadata={"name": "My Sandbox"},
)

paginator = Sandbox.list()

# Get the first page of sandboxes (running and paused)
first_page = paginator.next_items()

running_sandbox = first_page[0]

print('Running sandbox metadata:', running_sandbox.metadata)
print('Running sandbox id:', running_sandbox.sandbox_id)
print('Running sandbox started at:', running_sandbox.started_at)
print('Running sandbox template id:', running_sandbox.template_id)

# Get the next page of sandboxes
next_page = paginator.next_items()
```

**JavaScript:**
```javascript
import { Sandbox, SandboxInfo } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create({
    metadata: { name: 'My Sandbox' },
})

const paginator = Sandbox.list()

// Get first page
const firstPage = await paginator.nextItems()

const runningSandbox = firstPage[0]
console.log('Running sandbox metadata:', runningSandbox.metadata)
console.log('Running sandbox id:', runningSandbox.sandboxId)
console.log('Running sandbox started at:', runningSandbox.startedAt)
console.log('Running sandbox template id:', runningSandbox.templateId)

// Get next page
const nextPage = await paginator.nextItems()
```

### Pagination Control

Control pagination with limit and offset parameters. The default and maximum limit is 100 items per page.

**Python:**
```python
# Custom pagination
paginator = Sandbox.list(limit=100, next_token='<base64-token>')

# Loop through all pages
all_sandboxes = []
while paginator.has_next:
    items = paginator.next_items()
    all_sandboxes.extend(items)

# Check pagination state
print(f"Has next page: {paginator.has_next}")
print(f"Next token: {paginator.next_token}")
```

**JavaScript:**
```javascript
const paginator = Sandbox.list({
  limit: 100,
  nextToken: '<base64-encoded-token>'
})

// Paginator properties
paginator.hasNext      // Whether there is a next page
paginator.nextToken    // Token for next page
await paginator.nextItems()  // Fetch next page

// Fetch all pages
const allSandboxes = []
while (paginator.hasNext) {
  const items = await paginator.nextItems()
  allSandboxes.push(...items)
}
```

### Filtering by State

Filter sandboxes by their current state: `running` or `paused`.

**Python:**
```python
from e2b_code_interpreter import Sandbox, SandboxQuery, SandboxState

# List running or paused sandboxes
paginator = Sandbox.list(
    query=SandboxQuery(
        state=[SandboxState.RUNNING, SandboxState.PAUSED],
    ),
)

sandboxes = paginator.next_items()
```

**JavaScript:**
```javascript
// List running sandboxes
const paginator = Sandbox.list({
  query: {
    state: ['running', 'paused']
  }
})

const sandboxes = await paginator.nextItems()
```

### Filtering by Metadata

Filter sandboxes by metadata key-value pairs. Multiple pairs create an AND filter (sandbox must match all specified metadata).

**Python:**
```python
from e2b_code_interpreter import Sandbox, SandboxQuery

# Create sandbox with metadata
sandbox = Sandbox.create(
    metadata={
        'userId': '123',
        'env': 'dev',
        'app': 'my-app'
    }
)

# Find sandboxes matching metadata
paginator = Sandbox.list(
    query=SandboxQuery(
        metadata={'userId': '123', 'env': 'dev'}
    )
)

sandboxes = paginator.next_items()
```

**JavaScript:**
```javascript
// Create with metadata
const sandbox = await Sandbox.create({
  metadata: {
    env: 'dev',
    app: 'my-app',
    userId: '123'
  }
})

// Filter by metadata
const paginator = Sandbox.list({
  query: {
    metadata: { userId: '123', env: 'dev' }
  }
})

const sandboxes = await paginator.nextItems()
```

### Combined Filtering

Combine state and metadata filters for precise queries.

**Python:**
```python
# Find running sandboxes for specific user
paginator = Sandbox.list(
    query=SandboxQuery(
        state=[SandboxState.RUNNING],
        metadata={'userId': '123'}
    )
)
```

**JavaScript:**
```javascript
const paginator = Sandbox.list({
  query: {
    state: ['running'],
    metadata: { userId: '123' }
  }
})
```

## Metadata

Metadata allows you to attach custom key-value pairs to sandboxes for tracking and organization purposes.

### Attaching Metadata on Creation

**Python:**
```python
sandbox = Sandbox.create(
    metadata={
        'userId': 'user_12345',
        'sessionId': 'session_abc',
        'environment': 'production',
        'purpose': 'data-analysis',
    }
)
```

**JavaScript:**
```javascript
const sandbox = await Sandbox.create({
  metadata: {
    userId: 'user_12345',
    sessionId: 'session_abc',
    environment: 'production',
    purpose: 'data-analysis',
  }
})
```

### Reading Metadata

**Python:**
```python
# When listing
paginator = Sandbox.list()
sandboxes = paginator.next_items()
for sbx in sandboxes:
    print(f"Sandbox {sbx.sandbox_id}: {sbx.metadata}")
```

**JavaScript:**
```javascript
const paginator = Sandbox.list()
const sandboxes = await paginator.nextItems()
sandboxes.forEach(sbx => {
  console.log(`Sandbox ${sbx.sandboxId}:`, sbx.metadata)
})
```

### Use Cases for Metadata

1. **User Session Tracking**: Associate sandboxes with user sessions
2. **Multi-Tenant Applications**: Tag sandboxes by tenant/org
3. **Environment Segregation**: Tag by deployment environment (dev/staging/production)
4. **Cost Tracking**: Track usage per project/department
5. **API Key Tracking**: Audit sandboxes created by specific API keys

### Best Practices for Metadata

1. **Use consistent key names** across your application
2. **Keep metadata flat** (avoid nested objects)
3. **Use metadata for filtering**, not for storing large data
4. **Include timestamps** for tracking creation and lifecycle
5. **Add user/session identifiers** for multi-user applications
6. **Limit metadata size** to essential tracking information

## Connecting to Running Sandboxes

Connect to existing sandboxes using their ID to resume work or inspect state.

### Connect by Sandbox ID

**Python:**
```python
# Connect to existing sandbox
sandbox = Sandbox.connect('ixjj3iankaishgcge4jwn-b0b684e9')

# Use the sandbox
execution = sandbox.run_code('print("Reconnected!")')
print(execution.text)
```

**JavaScript:**
```javascript
// Connect to existing sandbox
const sandbox = await Sandbox.connect('ixjj3iankaishgcge4jwn-b0b684e9')

// Use the sandbox
const execution = await sandbox.runCode('print("Reconnected!")')
console.log(execution.text)
```

## Environment Variables

E2B supports environment variables at three scoping levels: global (sandbox-wide), code execution, and command execution.

### Default E2B Environment Variables

E2B automatically sets metadata environment variables in every sandbox:

- `E2B_SANDBOX=true` - Indicates code is running inside an E2B sandbox
- `E2B_SANDBOX_ID` - The unique ID of the current sandbox
- `E2B_TEAM_ID` - Team ID that created the sandbox
- `E2B_TEMPLATE_ID` - Template ID used to create the sandbox

### Setting Environment Variables

#### 1. Global Environment Variables (Sandbox-Wide)

Set variables when creating the sandbox. These are available to all code and commands.

**Python:**
```python
sandbox = Sandbox.create(
    envs={
        'API_KEY': 'secret_key_123',
        'DATABASE_URL': 'postgres://localhost/db',
        'DEBUG': 'true'
    }
)

# Variables available to all code
result = sandbox.run_code('import os; print(os.environ.get("API_KEY"))')
print(result.text)  # Output: secret_key_123
```

**JavaScript:**
```javascript
const sandbox = await Sandbox.create({
  envs: {
    API_KEY: 'secret_key_123',
    DATABASE_URL: 'postgres://localhost/db',
    DEBUG: 'true'
  }
})
```

#### 2. Code Execution Scope

Set variables for a specific code execution call. These override global variables for that execution only.

**Python:**
```python
sandbox = Sandbox.create(
    envs={'API_KEY': 'global_key'}
)

# Override for this execution
execution = sandbox.run_code(
    'import os; print(os.environ.get("API_KEY"))',
    envs={'API_KEY': 'execution_specific_key'}
)
print(execution.text)  # Output: execution_specific_key

# Global variable still unchanged
execution = sandbox.run_code('import os; print(os.environ.get("API_KEY"))')
print(execution.text)  # Output: global_key
```

#### 3. Command Execution Scope

Set variables for a specific command execution.

**Python:**
```python
sandbox = Sandbox.create()

# Set variable for this command only
result = sandbox.commands.run(
    'echo $MY_VAR',
    envs={'MY_VAR': '123'}
)
print(result)  # Output: 123

# Variable not available in other commands
result = sandbox.commands.run('echo $MY_VAR')
print(result)  # Output: (empty)
```

### Environment Variable Scoping Summary

| Scope Level | Set When | Visibility | Override Behavior |
|-------------|----------|------------|-------------------|
| **Global** | `Sandbox.create(envs=...)` | All code and commands | Lowest priority |
| **Code Execution** | `run_code(..., envs=...)` | Single code execution | Overrides global for that execution |
| **Command Execution** | `commands.run(..., envs=...)` | Single command | Overrides global for that command |

## Storage Bucket Integration

Connect external storage buckets (GCS, S3, Cloudflare R2) to sandboxes using FUSE file systems. Requires a custom sandbox template with the FUSE driver installed.

### Google Cloud Storage

#### Template Setup

```python
from e2b import Template

template = (
    Template()
    .from_template("code-interpreter-v1")
    .apt_install(["gnupg", "lsb-release"])
    .run_cmd("lsb_release -c -s > /tmp/lsb_release")
    .run_cmd(
        'GCSFUSE_REPO=$(cat /tmp/lsb_release) && echo "deb [signed-by=/usr/share/keyrings/cloud.google.asc] https://packages.cloud.google.com/apt gcsfuse-$GCSFUSE_REPO main" | sudo tee /etc/apt/sources.list.d/gcsfuse.list'
    )
    .run_cmd(
        "curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo tee /usr/share/keyrings/cloud.google.asc"
    )
    .apt_install(["gcsfuse"])
)
```

#### Mounting the Bucket

```python
from e2b import Sandbox

sandbox = Sandbox.create("<your template id>")
sandbox.files.make_dir("/home/user/bucket")
sandbox.files.write("key.json", "<your service account key>")

sandbox.commands.run(
    "sudo gcsfuse --key-file /home/user/key.json <bucket-name> /home/user/bucket"
)
```

**To allow the default user to access the files:**
```
-o allow_other -file-mode=777 -dir-mode=777
```

### Amazon S3

#### Template Setup

```python
from e2b import Template

template = (
    Template()
    .from_image("ubuntu:latest")
    .apt_install(["s3fs"])
)
```

#### Mounting the Bucket

```python
from e2b import Sandbox

sandbox = Sandbox.create("<your template id>")
sandbox.files.make_dir("/home/user/bucket")

# Create credentials file
sandbox.files.write("/root/.passwd-s3fs", "<AWS_ACCESS_KEY_ID>:<AWS_SECRET_ACCESS_KEY>")
sandbox.commands.run("sudo chmod 600 /root/.passwd-s3fs")

sandbox.commands.run("sudo s3fs <bucket-name> /home/user/bucket")
```

### Cloudflare R2

Same template as S3, but the mounting command includes the R2 endpoint:

```python
sandbox.commands.run(
    "sudo s3fs -o url=https://<ACCOUNT_ID>.r2.cloudflarestorage.com <bucket-name> /home/user/bucket"
)
```

## SSH Access

SSH access enables remote terminal sessions, SCP/SFTP file transfers, and integration with tools that expect SSH connectivity. It works by proxying SSH connections over WebSocket through the sandbox's exposed ports.

### Template Setup

Define a template with OpenSSH server and websocat:

**Python:**
```python
from e2b import Template, wait_for_port

template = (
    Template()
    .from_ubuntu_image("25.04")
    .apt_install(["openssh-server"])
    .run_cmd([
        "curl -fsSL -o /usr/local/bin/websocat https://github.com/vi/websocat/releases/latest/download/websocat.x86_64-unknown-linux-musl",
        "chmod a+x /usr/local/bin/websocat",
    ], user="root")
    .set_start_cmd(
        "sudo websocat -b --exit-on-eof ws-l:0.0.0.0:8081 tcp:127.0.0.1:22",
        wait_for_port(8081)
    )
)
```

**JavaScript:**
```javascript
import { Template, waitForPort } from 'e2b'

const template = Template()
  .fromUbuntuImage('25.04')
  .aptInstall(['openssh-server'])
  .runCmd([
    'curl -fsSL -o /usr/local/bin/websocat https://github.com/vi/websocat/releases/latest/download/websocat.x86_64-unknown-linux-musl',
    'chmod a+x /usr/local/bin/websocat',
  ], { user: 'root' })
  .setStartCmd('sudo websocat -b --exit-on-eof ws-l:0.0.0.0:8081 tcp:127.0.0.1:22', waitForPort(8081))
```

### Build and Connect

Build the template, create a sandbox, then connect:

```bash
# macOS
brew install websocat
ssh -o 'ProxyCommand=websocat --binary -B 65536 - wss://8081-%h.e2b.app' user@<sandbox-id>

# Linux
sudo curl -fsSL -o /usr/local/bin/websocat https://github.com/vi/websocat/releases/latest/download/websocat.x86_64-unknown-linux-musl
sudo chmod a+x /usr/local/bin/websocat
ssh -o 'ProxyCommand=websocat --binary -B 65536 - wss://8081-%h.e2b.app' user@<sandbox-id>
```

### How It Works

```
Your Machine                          E2B Sandbox
+----------+    ProxyCommand    +------------------+
|   SSH    | ---- websocat ---> |    websocat      |
|  Client  |   (WebSocket)      |  (WS -> TCP:22)  |
+----------+                    +--------+---------+
                                         |
                                +--------v---------+
                                |   SSH Server     |
                                |   (OpenSSH)      |
                                +------------------+
```

## Interactive Terminal (PTY)

The PTY module allows you to create interactive terminal sessions with real-time, bidirectional communication.

Unlike `commands.run()` which returns output after completion, PTY provides:
- **Real-time streaming** - Output is streamed as it happens via callbacks
- **Bidirectional input** - Send input while the terminal is running
- **Interactive shell** - Full terminal support with ANSI colors and escape sequences
- **Session persistence** - Disconnect and reconnect to running sessions

### Create a PTY Session

**Python:**
```python
from e2b_code_interpreter import Sandbox

sandbox = Sandbox()

terminal = sandbox.pty.create(
    cols=80,              # Terminal width in characters
    rows=24,              # Terminal height in characters
    on_data=lambda data: print(data.decode(), end=''),
    envs={'MY_VAR': 'hello'},  # Optional environment variables
    cwd='/home/user',          # Optional working directory
    user='root',               # Optional user to run as
)

print('Terminal PID:', terminal.pid)
```

**JavaScript:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create()

const terminal = await sandbox.pty.create({
  cols: 80,
  rows: 24,
  onData: (data) => process.stdout.write(data),
  envs: { MY_VAR: 'hello' },
  cwd: '/home/user',
  user: 'root',
})

console.log('Terminal PID:', terminal.pid)
```

### Timeout

By default, PTY sessions have a 60-second timeout. For long-running sessions, set `timeout=0` (Python) or `timeoutMs: 0` (JavaScript) to disable it.

### Send Input to PTY

**Python:**
```python
# Send a command as bytes (don't forget the newline!)
sandbox.pty.send_stdin(terminal.pid, b'echo "Hello from PTY"\n')
```

**JavaScript:**
```javascript
await sandbox.pty.sendInput(
  terminal.pid,
  new TextEncoder().encode('echo "Hello from PTY"\n')
)
```

### Resize the Terminal

**Python:**
```python
sandbox.pty.resize(terminal.pid, cols=120, rows=40)
```

**JavaScript:**
```javascript
await sandbox.pty.resize(terminal.pid, { cols: 120, rows: 40 })
```

### Disconnect and Reconnect

You can disconnect from a PTY session while keeping it running, then reconnect later.

**Python:**
```python
terminal = sandbox.pty.create(
    cols=80, rows=24,
    on_data=lambda data: print('Handler 1:', data.decode()),
)

pid = terminal.pid
sandbox.pty.send_stdin(pid, b'echo hello\n')

# Disconnect - PTY keeps running in the background
terminal.disconnect()

# Later: reconnect with a new data handler
reconnected = sandbox.pty.connect(
    pid,
    on_data=lambda data: print('Handler 2:', data.decode()),
)

sandbox.pty.send_stdin(pid, b'echo world\n')
reconnected.wait()
```

**JavaScript:**
```javascript
const terminal = await sandbox.pty.create({
  cols: 80, rows: 24,
  onData: (data) => console.log('Handler 1:', new TextDecoder().decode(data)),
})

const pid = terminal.pid
await sandbox.pty.sendInput(pid, new TextEncoder().encode('echo hello\n'))

// Disconnect
await terminal.disconnect()

// Reconnect
const reconnected = await sandbox.pty.connect(pid, {
  onData: (data) => console.log('Handler 2:', new TextDecoder().decode(data)),
})

await sandbox.pty.sendInput(pid, new TextEncoder().encode('echo world\n'))
await reconnected.wait()
```

### Kill the PTY

**Python:**
```python
killed = sandbox.pty.kill(terminal.pid)
print('Killed:', killed)  # True if successful
```

**JavaScript:**
```javascript
const killed = await sandbox.pty.kill(terminal.pid)
console.log('Killed:', killed)  // true if successful
```

### Wait for PTY to Exit

**Python:**
```python
sandbox.pty.send_stdin(terminal.pid, b'exit\n')
result = terminal.wait()
print('Exit code:', result.exit_code)
```

**JavaScript:**
```javascript
await sandbox.pty.sendInput(terminal.pid, new TextEncoder().encode('exit\n'))
const result = await terminal.wait()
console.log('Exit code:', result.exitCode)
```

## Proxy Tunneling

Route sandbox network traffic through a proxy server to use a dedicated IP address for outgoing requests. Uses Shadowsocks with either local proxy (designated traffic only) or transparent proxy (all traffic).

### Overview

1. Set up a Shadowsocks server on a VM (e.g., GCP)
2. Create a custom E2B template with Shadowsocks client installed
3. Create sandboxes from that template - traffic routes through the proxy

### Local Proxy Template

Route only designated traffic through the proxy:

**Python:**
```python
from e2b import Template, wait_for_port

template = (
    Template()
    .from_base_image()
    .run_cmd([
        "wget https://github.com/shadowsocks/shadowsocks-rust/releases/latest/download/shadowsocks-v1.24.0.x86_64-unknown-linux-gnu.tar.xz",
        "tar -xf shadowsocks-*.tar.xz",
        "sudo mv sslocal /usr/local/bin/"
    ])
    .copy("config.json", "config.json")
    .set_start_cmd(
        "sudo sslocal -c config.json --daemonize",
        wait_for_port(1080)
    )
)
```

### Transparent Proxy Template

Route all traffic through the proxy (uses iptables rules in addition).

### Using the Proxy

```python
from e2b import Sandbox

# Local proxy - use SOCKS5 flag
sbx = Sandbox.create('shadowsocks-client')
curl = sbx.commands.run('curl --socks5 127.0.0.1:1080 https://ifconfig.me')
print(curl.stdout)  # Shows proxy server IP

# Transparent proxy - all traffic automatically routes through proxy
sbx = Sandbox.create('shadowsocks-client')
curl = sbx.commands.run('curl https://ifconfig.me')
print(curl.stdout)  # Shows proxy server IP
```

## Custom Domain

Set up a custom domain for sandboxes hosted on E2B using a reverse proxy (e.g., Caddy with Cloudflare DNS).

### Overview

Maps `<port>-<sandboxid>.mydomain.com` to `<port>-<sandboxid>.e2b.app`.

### Requirements

- Domain registered with Cloudflare DNS
- Cloudflare API Token for DNS management
- GCP VM (or similar) running Caddy server with Docker

### Setup Steps

1. Create a GCP VM with Caddy server
2. Configure Caddyfile for wildcard domain proxying
3. Create a Cloudflare wildcard A DNS record pointing to the VM
4. Test with `https://80-sandboxid.mydomain.com`

### Example Caddyfile

```caddyfile
*.mydomain.com {
    tls {
        dns cloudflare {env.CLOUDFLARE_API_TOKEN}
    }

    vars sandboxId {labels.2}

    reverse_proxy {vars.sandboxId}.e2b.app:443 {
        header_up Host {vars.sandboxId}.e2b.app
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
        header_up X-Forwarded-Host {host}

        transport http {
            tls
            tls_server_name {vars.sandboxId}.e2b.app
        }
    }
}
```

## Secured Access

Secure access authenticates communication between SDK and sandbox controller. Without it, anyone with a sandbox ID can access the controller APIs.

### Key Points

- **SDK v2.0.0+** uses secure access by default when creating sandboxes
- All sandboxes based on templates with envd version `v0.2.0+` support secure access
- Custom templates created before envd `v0.2.0` need to be rebuilt

### Migration Path

When using older custom templates, you can temporarily disable secure access:

**Python:**
```python
from e2b_code_interpreter import Sandbox

sandbox = Sandbox.create(secure=False)  # Explicitly disable (not recommended)
```

**JavaScript:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create({ secure: false }) // Explicitly disable (not recommended)
```

### Direct API Access

When secure access is enabled and you access sandbox controller APIs directly (without SDKs), include the `X-Access-Token` header with the access token returned during sandbox creation.

For upload and download URLs, use the SDK to generate pre-signed URLs.

## Common Patterns

### Pattern 1: Multi-User Session Management

```python
from e2b_code_interpreter import Sandbox, SandboxQuery
from datetime import datetime

class UserSandboxManager:
    def __init__(self):
        self.sandbox_cache = {}

    def get_sandbox(self, user_id: str) -> Sandbox:
        if user_id in self.sandbox_cache:
            return self.sandbox_cache[user_id]

        paginator = Sandbox.list(
            query=SandboxQuery(
                state=['running', 'paused'],
                metadata={'userId': user_id}
            )
        )
        sandboxes = paginator.next_items()

        if sandboxes:
            sandbox = Sandbox.connect(sandboxes[0].sandbox_id)
        else:
            sandbox = Sandbox.create(
                timeout=600,
                metadata={
                    'userId': user_id,
                    'created': datetime.now().isoformat()
                }
            )

        self.sandbox_cache[user_id] = sandbox
        return sandbox

    def cleanup_user_sandbox(self, user_id: str):
        if user_id in self.sandbox_cache:
            self.sandbox_cache[user_id].kill()
            del self.sandbox_cache[user_id]
```

### Pattern 2: Cleanup Orphaned Sandboxes

```python
from datetime import datetime, timedelta
from e2b_code_interpreter import Sandbox

def cleanup_old_sandboxes(max_age_minutes: int = 60):
    cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)

    paginator = Sandbox.list(query={'state': ['running']})

    killed_count = 0
    while paginator.has_next:
        sandboxes = paginator.next_items()
        for sbx_info in sandboxes:
            started_at = datetime.fromisoformat(
                sbx_info.started_at.replace('Z', '+00:00')
            )
            if started_at < cutoff_time:
                print(f"Killing old sandbox: {sbx_info.sandbox_id}")
                Sandbox.kill(sbx_info.sandbox_id)
                killed_count += 1

    print(f"Cleaned up {killed_count} old sandboxes")

cleanup_old_sandboxes(max_age_minutes=30)
```

### Pattern 3: Graceful Degradation

```python
def get_or_recreate_sandbox(sandbox_id: str, metadata: dict):
    try:
        sandbox = Sandbox.connect(sandbox_id)
        sandbox.run_code('print("alive")')
        return sandbox, False  # False = not recreated
    except Exception as e:
        print(f"Failed to connect to {sandbox_id}: {e}")
        new_sandbox = Sandbox.create(metadata=metadata)
        return new_sandbox, True  # True = recreated
```

## Troubleshooting

### Issue: Sandbox Not Found When Connecting

**Possible Causes:**
1. Sandbox has already been killed
2. Sandbox timeout expired (default 5 minutes)
3. Sandbox ID is incorrect
4. Using wrong API key (sandboxes belong to team/API key)

**Solutions:**
```python
paginator = Sandbox.list()
sandboxes = paginator.next_items()
sandbox_ids = [sbx.sandbox_id for sbx in sandboxes]

if target_id in sandbox_ids:
    sandbox = Sandbox.connect(target_id)
else:
    print(f"Sandbox {target_id} not found, creating new one")
    sandbox = Sandbox.create()
```

### Issue: Metadata Filtering Not Working

**Possible Causes:**
1. Metadata keys are case-sensitive
2. Multiple metadata pairs create AND filter (not OR)
3. Metadata value types must match exactly (string vs int)

### Issue: Environment Variables Not Available

**Possible Causes:**
1. Variable set at wrong scope
2. Variable name typo
3. Using subprocess that doesn't inherit environment

**Solutions:**
```python
sandbox = Sandbox.create(envs={'MY_VAR': 'test_value'})

# Check if variable is set
result = sandbox.commands.run('env | grep MY_VAR')
print(result)

# In Python code
result = sandbox.run_code('''
import os
print("MY_VAR:", os.environ.get("MY_VAR"))
''')
```

### Issue: Stale Sandbox Connections

**Solutions:**
```python
def ensure_responsive_sandbox(sandbox_id: str, metadata: dict = None):
    try:
        sandbox = Sandbox.connect(sandbox_id)
        result = sandbox.run_code('print("alive")', timeout=5)
        if result.error:
            raise Exception("Sandbox not responsive")
        return sandbox
    except Exception as e:
        print(f"Sandbox {sandbox_id} not responsive: {e}")
        return Sandbox.create(metadata=metadata or {})
```

## See Also

- [Sandbox Lifecycle](./sandbox-lifecycle.md) - Creating, pausing, and managing sandboxes
- [Monitoring & Events](./monitoring-and-events.md) - Metrics, events, and webhooks
- [Persistence Guide](./persistence.md) - Pausing and resuming sandboxes
- [Quickstart Guide](./quickstart.md) - Getting started with E2B
