# Coding Agents in E2B Sandboxes

E2B provides pre-built sandbox templates for running coding agents (Claude Code, Codex, AMP, OpenCode, OpenClaw) in isolated Linux environments with full terminal, filesystem, and git access. Each agent gets its own secure sandbox and can work autonomously on code tasks.

## Table of Contents

- [Why Run Agents in Sandboxes](#why-run-agents-in-sandboxes)
- [How It Works](#how-it-works)
- [Agent Quick Reference](#agent-quick-reference)
- [Claude Code](#claude-code)
- [Codex (OpenAI)](#codex-openai)
- [AMP (Sourcegraph)](#amp-sourcegraph)
- [OpenCode](#opencode)
- [OpenClaw](#openclaw)
- [Computer Use / Desktop Sandbox](#computer-use--desktop-sandbox)
- [Common Patterns](#common-patterns)

## Why Run Agents in Sandboxes

1. **Isolation** -- agent-generated code runs in a secure sandbox, never touching production systems or local machine
2. **Full dev environment** -- terminal, filesystem, git, and package managers available out of the box
3. **Pre-built templates** -- ready-made templates for popular agents, plus ability to build custom templates
4. **Scalability** -- spin up many sandboxes in parallel, each running its own agent on a separate task

## How It Works

1. **Create a sandbox** from a pre-built template (or build a custom one)
2. **Agent gets a full environment** -- terminal, filesystem, git access, installed tools
3. **Agent works autonomously** -- reads codebase, writes code, runs tests, iterates
4. **Extract results** -- pull out git diff, structured output, or modified files via SDK
5. **Sandbox is cleaned up** -- destroyed automatically when done, no lingering state

## Agent Quick Reference

| Agent | Template | API Key Env Var | Headless Flag | Auto-approve Flag |
|-------|----------|-----------------|---------------|-------------------|
| Claude Code | `claude` | `ANTHROPIC_API_KEY` | `-p "prompt"` | `--dangerously-skip-permissions` |
| Codex | `codex` | `CODEX_API_KEY` | `exec "prompt"` | `--full-auto --skip-git-repo-check` |
| AMP | `amp` | `AMP_API_KEY` | `-x "prompt"` | `--dangerously-allow-all` |
| OpenCode | `opencode` | `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`, `GEMINI_API_KEY`) | `run "prompt"` | (none needed) |
| OpenClaw | `openclaw` | `ANTHROPIC_API_KEY` | `agent --local --message "prompt"` | (none needed) |

---

## Claude Code

Anthropic's agentic coding tool. E2B provides the `claude` template with Claude Code pre-installed.

### CLI Quick Start

```bash
e2b sbx create claude
# Once inside:
claude
```

### Headless Execution

Use `-p` for non-interactive mode and `--dangerously-skip-permissions` to auto-approve all tool calls (safe inside E2B sandboxes).

**Python:**
```python
import os
from e2b import Sandbox

sandbox = Sandbox.create("claude", envs={
    "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
})

result = sandbox.commands.run(
    'claude --dangerously-skip-permissions -p "Create a hello world HTTP server in Go"',
)

print(result.stdout)
sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('claude', {
  envs: { ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY },
})

const result = await sandbox.commands.run(
  `claude --dangerously-skip-permissions -p "Create a hello world HTTP server in Go"`
)

console.log(result.stdout)
await sandbox.kill()
```

### Work on a Cloned Repository

**Python:**
```python
import os
from e2b import Sandbox

sandbox = Sandbox.create("claude", envs={
    "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
}, timeout=600)

sandbox.git.clone("https://github.com/your-org/your-repo.git",
    path="/home/user/repo",
    username="x-access-token",
    password=os.environ["GITHUB_TOKEN"],
    depth=1,
)

result = sandbox.commands.run(
    'cd /home/user/repo && claude --dangerously-skip-permissions -p "Add error handling to all API endpoints"',
    on_stdout=lambda data: print(data, end=""),
)

diff = sandbox.commands.run("cd /home/user/repo && git diff")
print(diff.stdout)

sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('claude', {
  envs: { ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY },
  timeoutMs: 600_000,
})

await sandbox.git.clone('https://github.com/your-org/your-repo.git', {
  path: '/home/user/repo',
  username: 'x-access-token',
  password: process.env.GITHUB_TOKEN,
  depth: 1,
})

const result = await sandbox.commands.run(
  `cd /home/user/repo && claude --dangerously-skip-permissions -p "Add error handling to all API endpoints"`,
  { onStdout: (data) => process.stdout.write(data) }
)

const diff = await sandbox.commands.run('cd /home/user/repo && git diff')
console.log(diff.stdout)

await sandbox.kill()
```

### Structured Output

Use `--output-format json` to get machine-readable responses for pipelines.

**Python:**
```python
import os
import json
from e2b import Sandbox

sandbox = Sandbox.create("claude", envs={
    "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
})

result = sandbox.commands.run(
    'claude --dangerously-skip-permissions --output-format json -p "Review this codebase and list all security issues as JSON"',
)

response = json.loads(result.stdout)
print(response)

sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('claude', {
  envs: { ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY },
})

const result = await sandbox.commands.run(
  `claude --dangerously-skip-permissions --output-format json -p "Review this codebase and list all security issues as JSON"`
)

const response = JSON.parse(result.stdout)
console.log(response)

await sandbox.kill()
```

### Streaming Output

Use `--output-format stream-json` to get real-time JSONL event stream with tool calls, token usage, and result metadata.

**Python:**
```python
import os
import json
from e2b import Sandbox

sandbox = Sandbox.create("claude", envs={
    "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
})

def handle_event(data):
    for line in data.strip().split("\n"):
        if line:
            event = json.loads(line)
            if event["type"] == "assistant":
                usage = event.get("message", {}).get("usage", {})
                print(f"[assistant] tokens: {usage.get('output_tokens')}")
            elif event["type"] == "result":
                print(f"[done] {event['subtype']} in {event['duration_ms']}ms")

result = sandbox.commands.run(
    'cd /home/user/repo && claude --dangerously-skip-permissions --output-format stream-json -p "Find and fix all TODO comments"',
    on_stdout=handle_event,
)

sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('claude', {
  envs: { ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY },
})

const result = await sandbox.commands.run(
  `cd /home/user/repo && claude --dangerously-skip-permissions --output-format stream-json -p "Find and fix all TODO comments"`,
  {
    onStdout: (data) => {
      for (const line of data.split('\n').filter(Boolean)) {
        const event = JSON.parse(line)
        if (event.type === 'assistant') {
          console.log(`[assistant] tokens: ${event.message.usage?.output_tokens}`)
        } else if (event.type === 'result') {
          console.log(`[done] ${event.subtype} in ${event.duration_ms}ms`)
        }
      }
    },
  }
)

await sandbox.kill()
```

### Session Resumption

Claude Code persists conversations that can be resumed with `--session-id`.

**Python:**
```python
import os
import json
from e2b import Sandbox

sandbox = Sandbox.create("claude", envs={
    "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
}, timeout=600)

# Start a new session
initial = sandbox.commands.run(
    'cd /home/user/repo && claude --dangerously-skip-permissions --output-format json -p "Analyze the codebase and create a refactoring plan"',
)

# Extract session ID from the JSON response
response = json.loads(initial.stdout)
session_id = response["session_id"]

# Continue with a follow-up task
follow_up = sandbox.commands.run(
    f'cd /home/user/repo && claude --dangerously-skip-permissions --session-id {session_id} -p "Now implement step 1 of the plan"',
    on_stdout=lambda data: print(data, end=""),
)

diff = sandbox.commands.run("cd /home/user/repo && git diff")
print(diff.stdout)

sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('claude', {
  envs: { ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY },
  timeoutMs: 600_000,
})

// Start a new session
const initial = await sandbox.commands.run(
  `cd /home/user/repo && claude --dangerously-skip-permissions --output-format json -p "Analyze the codebase and create a refactoring plan"`
)

// Extract session ID from the JSON response
const response = JSON.parse(initial.stdout)
const sessionId = response.session_id

// Continue with a follow-up task
const followUp = await sandbox.commands.run(
  `cd /home/user/repo && claude --dangerously-skip-permissions --session-id ${sessionId} -p "Now implement step 1 of the plan"`,
  { onStdout: (data) => process.stdout.write(data) }
)

const diff = await sandbox.commands.run('cd /home/user/repo && git diff')
console.log(diff.stdout)

await sandbox.kill()
```

### Custom System Prompt via CLAUDE.md

Write a `CLAUDE.md` file into the sandbox for project context, or use `--system-prompt` for task-specific instructions.

**Python:**
```python
import os
from e2b import Sandbox

sandbox = Sandbox.create("claude", envs={
    "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
})

# Write project context
sandbox.files.write("/home/user/repo/CLAUDE.md", """
You are working on a Go microservice.
Always use structured logging with slog.
Follow the project's error handling conventions in pkg/errors.
""")

result = sandbox.commands.run(
    'cd /home/user/repo && claude --dangerously-skip-permissions -p "Add a /healthz endpoint"',
)

print(result.stdout)
sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('claude', {
  envs: { ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY },
})

// Write project context
await sandbox.files.write('/home/user/repo/CLAUDE.md', `
You are working on a Go microservice.
Always use structured logging with slog.
Follow the project's error handling conventions in pkg/errors.
`)

const result = await sandbox.commands.run(
  `cd /home/user/repo && claude --dangerously-skip-permissions -p "Add a /healthz endpoint"`
)

console.log(result.stdout)
await sandbox.kill()
```

### MCP Tool Integration for Claude Code

Claude Code has built-in MCP support. E2B provides an MCP gateway giving access to 200+ tools from the Docker MCP Catalog.

**Python:**
```python
import os
from e2b import Sandbox

sandbox = Sandbox.create("claude", envs={
    "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
}, mcp={
    "browserbase": {
        "apiKey": os.environ["BROWSERBASE_API_KEY"],
        "projectId": os.environ["BROWSERBASE_PROJECT_ID"],
    },
})

mcp_url = sandbox.get_mcp_url()
mcp_token = sandbox.get_mcp_token()

sandbox.commands.run(
    f'claude mcp add --transport http e2b-mcp-gateway {mcp_url} --header "Authorization: Bearer {mcp_token}"',
)

result = sandbox.commands.run(
    'claude --dangerously-skip-permissions -p "Use browserbase to research E2B and summarize your findings"',
    on_stdout=lambda data: print(data, end=""),
)

sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('claude', {
  envs: { ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY },
  mcp: {
    browserbase: {
      apiKey: process.env.BROWSERBASE_API_KEY,
      projectId: process.env.BROWSERBASE_PROJECT_ID,
    },
  },
})

const mcpUrl = sandbox.getMcpUrl()
const mcpToken = await sandbox.getMcpToken()

await sandbox.commands.run(
  `claude mcp add --transport http e2b-mcp-gateway ${mcpUrl} --header "Authorization: Bearer ${mcpToken}"`
)

const result = await sandbox.commands.run(
  `claude --dangerously-skip-permissions -p "Use browserbase to research E2B and summarize your findings"`,
  { onStdout: console.log }
)

await sandbox.kill()
```

### Custom Template for Claude Code

**Python:**
```python
# template.py
from e2b import Template

template = (
    Template()
    .from_template("claude")
)
```

```python
# build.py
from e2b import Template, default_build_logger
from template import template as claude_code_template

Template.build(claude_code_template, "my-claude",
    cpu_count=2,
    memory_mb=2048,
    on_build_logs=default_build_logger(),
)
```

**JavaScript/TypeScript:**
```typescript
// template.ts
import { Template } from 'e2b'

export const template = Template()
  .fromTemplate('claude')
```

```typescript
// build.ts
import { Template, defaultBuildLogger } from 'e2b'
import { template as claudeCodeTemplate } from './template'

await Template.build(claudeCodeTemplate, 'my-claude', {
  cpuCount: 2,
  memoryMB: 2048,
  onBuildLogs: defaultBuildLogger(),
})
```

---

## Codex (OpenAI)

OpenAI's open-source coding agent. E2B provides the `codex` template with Codex pre-installed.

### CLI Quick Start

```bash
e2b sbx create codex
# Once inside:
codex
```

### Headless Execution

Use `codex exec` for non-interactive mode, `--full-auto` to auto-approve tool calls, and `--skip-git-repo-check` to bypass git directory ownership checks.

**Python:**
```python
import os
from e2b import Sandbox

sandbox = Sandbox.create("codex", envs={
    "CODEX_API_KEY": os.environ["CODEX_API_KEY"],
})

result = sandbox.commands.run(
    'codex exec --full-auto --skip-git-repo-check "Create a hello world HTTP server in Go"',
)

print(result.stdout)
sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('codex', {
  envs: { CODEX_API_KEY: process.env.CODEX_API_KEY },
})

const result = await sandbox.commands.run(
  `codex exec --full-auto --skip-git-repo-check "Create a hello world HTTP server in Go"`
)

console.log(result.stdout)
await sandbox.kill()
```

### Work on a Cloned Repository

Use `-C` to set Codex's working directory.

**Python:**
```python
import os
from e2b import Sandbox

sandbox = Sandbox.create("codex", envs={
    "CODEX_API_KEY": os.environ["CODEX_API_KEY"],
}, timeout=600)

sandbox.git.clone("https://github.com/your-org/your-repo.git",
    path="/home/user/repo",
    username="x-access-token",
    password=os.environ["GITHUB_TOKEN"],
    depth=1,
)

result = sandbox.commands.run(
    'codex exec --full-auto --skip-git-repo-check -C /home/user/repo "Add error handling to all API endpoints"',
    on_stdout=lambda data: print(data, end=""),
)

diff = sandbox.commands.run("cd /home/user/repo && git diff")
print(diff.stdout)

sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('codex', {
  envs: { CODEX_API_KEY: process.env.CODEX_API_KEY },
  timeoutMs: 600_000,
})

await sandbox.git.clone('https://github.com/your-org/your-repo.git', {
  path: '/home/user/repo',
  username: 'x-access-token',
  password: process.env.GITHUB_TOKEN,
  depth: 1,
})

const result = await sandbox.commands.run(
  `codex exec --full-auto --skip-git-repo-check -C /home/user/repo "Add error handling to all API endpoints"`,
  { onStdout: (data) => process.stdout.write(data) }
)

const diff = await sandbox.commands.run('cd /home/user/repo && git diff')
console.log(diff.stdout)

await sandbox.kill()
```

### Schema-Validated Output

Use `--output-schema` to constrain the agent's final response to a JSON Schema.

**Python:**
```python
import os
import json
from e2b import Sandbox

sandbox = Sandbox.create("codex", envs={
    "CODEX_API_KEY": os.environ["CODEX_API_KEY"],
})

sandbox.files.write("/home/user/schema.json", json.dumps({
    "type": "object",
    "properties": {
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "line": {"type": "number"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "description": {"type": "string"},
                },
                "required": ["file", "severity", "description"],
            },
        },
    },
    "required": ["issues"],
}))

result = sandbox.commands.run(
    'codex exec --full-auto --skip-git-repo-check --output-schema /home/user/schema.json -C /home/user/repo "Review this codebase for security issues"',
)

response = json.loads(result.stdout)
print(response["issues"])

sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('codex', {
  envs: { CODEX_API_KEY: process.env.CODEX_API_KEY },
})

await sandbox.files.write('/home/user/schema.json', JSON.stringify({
  type: 'object',
  properties: {
    issues: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          file: { type: 'string' },
          line: { type: 'number' },
          severity: { type: 'string', enum: ['low', 'medium', 'high', 'critical'] },
          description: { type: 'string' },
        },
        required: ['file', 'severity', 'description'],
      },
    },
  },
  required: ['issues'],
}))

const result = await sandbox.commands.run(
  `codex exec --full-auto --skip-git-repo-check --output-schema /home/user/schema.json -C /home/user/repo "Review this codebase for security issues"`
)

const response = JSON.parse(result.stdout)
console.log(response.issues)

await sandbox.kill()
```

### Streaming Events

Use `--json` to get a JSONL event stream. Progress goes to stderr; events go to stdout.

**Python:**
```python
import os
import json
from e2b import Sandbox

sandbox = Sandbox.create("codex", envs={
    "CODEX_API_KEY": os.environ["CODEX_API_KEY"],
})

def handle_event(data):
    for line in data.strip().split("\n"):
        if line:
            event = json.loads(line)
            print(f"[{event['type']}]", event)

result = sandbox.commands.run(
    'codex exec --full-auto --skip-git-repo-check --json -C /home/user/repo "Refactor the utils module into separate files"',
    on_stdout=handle_event,
)

sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('codex', {
  envs: { CODEX_API_KEY: process.env.CODEX_API_KEY },
})

const result = await sandbox.commands.run(
  `codex exec --full-auto --skip-git-repo-check --json -C /home/user/repo "Refactor the utils module into separate files"`,
  {
    onStdout: (data) => {
      for (const line of data.split('\n').filter(Boolean)) {
        const event = JSON.parse(line)
        console.log(`[${event.type}]`, event)
      }
    },
  }
)

await sandbox.kill()
```

### Image Input

Pass screenshots or design mockups with `--image` to give Codex visual context.

**Python:**
```python
import os
from e2b import Sandbox

sandbox = Sandbox.create("codex", envs={
    "CODEX_API_KEY": os.environ["CODEX_API_KEY"],
}, timeout=600)

# Upload a design mockup to the sandbox
with open("./mockup.png", "rb") as f:
    sandbox.files.write("/home/user/mockup.png", f)

result = sandbox.commands.run(
    'codex exec --full-auto --skip-git-repo-check --image /home/user/mockup.png -C /home/user/repo "Implement this UI design as a React component"',
    on_stdout=lambda data: print(data, end=""),
)

sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import fs from 'fs'
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('codex', {
  envs: { CODEX_API_KEY: process.env.CODEX_API_KEY },
  timeoutMs: 600_000,
})

// Upload a design mockup to the sandbox
await sandbox.files.write(
  '/home/user/mockup.png',
  fs.readFileSync('./mockup.png')
)

const result = await sandbox.commands.run(
  `codex exec --full-auto --skip-git-repo-check --image /home/user/mockup.png -C /home/user/repo "Implement this UI design as a React component"`,
  { onStdout: (data) => process.stdout.write(data) }
)

await sandbox.kill()
```

### Custom Template for Codex

**Python:**
```python
from e2b import Template

template = (
    Template()
    .from_template("codex")
)
```

**JavaScript/TypeScript:**
```typescript
import { Template } from 'e2b'

export const template = Template()
  .fromTemplate('codex')
```

---

## AMP (Sourcegraph)

Sourcegraph's coding agent with multi-model architecture and built-in code intelligence. E2B provides the `amp` template with AMP pre-installed.

### CLI Quick Start

```bash
e2b sbx create amp
# Once inside:
amp
```

### Headless Execution

Use `-x` for non-interactive mode and `--dangerously-allow-all` to auto-approve tool calls. AMP uses its own API key from ampcode.com/settings.

**Python:**
```python
import os
from e2b import Sandbox

sandbox = Sandbox.create("amp", envs={
    "AMP_API_KEY": os.environ["AMP_API_KEY"],
})

result = sandbox.commands.run(
    'amp --dangerously-allow-all -x "Create a hello world HTTP server in Go"',
)

print(result.stdout)
sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('amp', {
  envs: { AMP_API_KEY: process.env.AMP_API_KEY },
})

const result = await sandbox.commands.run(
  `amp --dangerously-allow-all -x "Create a hello world HTTP server in Go"`
)

console.log(result.stdout)
await sandbox.kill()
```

### Work on a Cloned Repository

**Python:**
```python
import os
from e2b import Sandbox

sandbox = Sandbox.create("amp", envs={
    "AMP_API_KEY": os.environ["AMP_API_KEY"],
}, timeout=600)

sandbox.git.clone("https://github.com/your-org/your-repo.git",
    path="/home/user/repo",
    username="x-access-token",
    password=os.environ["GITHUB_TOKEN"],
    depth=1,
)

result = sandbox.commands.run(
    'cd /home/user/repo && amp --dangerously-allow-all -x "Add error handling to all API endpoints"',
    on_stdout=lambda data: print(data, end=""),
)

diff = sandbox.commands.run("cd /home/user/repo && git diff")
print(diff.stdout)

sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('amp', {
  envs: { AMP_API_KEY: process.env.AMP_API_KEY },
  timeoutMs: 600_000,
})

await sandbox.git.clone('https://github.com/your-org/your-repo.git', {
  path: '/home/user/repo',
  username: 'x-access-token',
  password: process.env.GITHUB_TOKEN,
  depth: 1,
})

const result = await sandbox.commands.run(
  `cd /home/user/repo && amp --dangerously-allow-all -x "Add error handling to all API endpoints"`,
  { onStdout: (data) => process.stdout.write(data) }
)

const diff = await sandbox.commands.run('cd /home/user/repo && git diff')
console.log(diff.stdout)

await sandbox.kill()
```

### Streaming JSON

Use `--stream-json` to get real-time JSONL event stream with tool calls, token usage, thinking blocks, and permission decisions.

**Python:**
```python
import os
import json
from e2b import Sandbox

sandbox = Sandbox.create("amp", envs={
    "AMP_API_KEY": os.environ["AMP_API_KEY"],
})

def handle_event(data):
    for line in data.strip().split("\n"):
        if line:
            event = json.loads(line)
            if event["type"] == "assistant":
                usage = event.get("message", {}).get("usage", {})
                print(f"[assistant] tokens: {usage.get('output_tokens')}")
            elif event["type"] == "result":
                msg = event["message"]
                print(f"[done] {msg['subtype']} in {msg['duration_ms']}ms")

result = sandbox.commands.run(
    'cd /home/user/repo && amp --dangerously-allow-all --stream-json -x "Find and fix all TODO comments"',
    on_stdout=handle_event,
)

sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('amp', {
  envs: { AMP_API_KEY: process.env.AMP_API_KEY },
})

const result = await sandbox.commands.run(
  `cd /home/user/repo && amp --dangerously-allow-all --stream-json -x "Find and fix all TODO comments"`,
  {
    onStdout: (data) => {
      for (const line of data.split('\n').filter(Boolean)) {
        const event = JSON.parse(line)
        if (event.type === 'assistant') {
          console.log(`[assistant] tokens: ${event.message.usage?.output_tokens}`)
        } else if (event.type === 'result') {
          console.log(`[done] ${event.message.subtype} in ${event.message.duration_ms}ms`)
        }
      }
    },
  }
)

await sandbox.kill()
```

### Thread Management

AMP persists conversations as threads that can be resumed or continued with follow-up tasks.

**Python:**
```python
import os
import json
from e2b import Sandbox

sandbox = Sandbox.create("amp", envs={
    "AMP_API_KEY": os.environ["AMP_API_KEY"],
}, timeout=600)

# Start a new thread
initial = sandbox.commands.run(
    'cd /home/user/repo && amp --dangerously-allow-all -x "Analyze the codebase and create a refactoring plan"',
    on_stdout=lambda data: print(data, end=""),
)

# List threads and get the most recent thread ID
threads = sandbox.commands.run("amp threads list --json")
thread_id = json.loads(threads.stdout)[0]["id"]

# Continue the thread with a follow-up task
follow_up = sandbox.commands.run(
    f'cd /home/user/repo && amp threads continue {thread_id} --dangerously-allow-all -x "Now implement step 1 of the plan"',
    on_stdout=lambda data: print(data, end=""),
)

diff = sandbox.commands.run("cd /home/user/repo && git diff")
print(diff.stdout)

sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('amp', {
  envs: { AMP_API_KEY: process.env.AMP_API_KEY },
  timeoutMs: 600_000,
})

// Start a new thread
const initial = await sandbox.commands.run(
  `cd /home/user/repo && amp --dangerously-allow-all -x "Analyze the codebase and create a refactoring plan"`,
  { onStdout: (data) => process.stdout.write(data) }
)

// List threads and get the most recent thread ID
const threads = await sandbox.commands.run('amp threads list --json')
const threadId = JSON.parse(threads.stdout)[0].id

// Continue the thread with a follow-up task
const followUp = await sandbox.commands.run(
  `cd /home/user/repo && amp threads continue ${threadId} --dangerously-allow-all -x "Now implement step 1 of the plan"`,
  { onStdout: (data) => process.stdout.write(data) }
)

const diff = await sandbox.commands.run('cd /home/user/repo && git diff')
console.log(diff.stdout)

await sandbox.kill()
```

### Custom Template for AMP

**Python:**
```python
from e2b import Template

template = (
    Template()
    .from_template("amp")
)
```

**JavaScript/TypeScript:**
```typescript
import { Template } from 'e2b'

export const template = Template()
  .fromTemplate('amp')
```

---

## OpenCode

Open-source coding agent supporting multiple LLM providers. E2B provides the `opencode` template with OpenCode pre-installed.

### CLI Quick Start

```bash
e2b sbx create opencode
# Once inside:
opencode
```

### Headless Execution

Use `opencode run` for non-interactive mode. Pass your LLM provider's API key as an environment variable -- OpenCode supports `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, and others.

**Python:**
```python
import os
from e2b import Sandbox

sandbox = Sandbox.create("opencode", envs={
    "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
})

result = sandbox.commands.run(
    'opencode run "Create a hello world HTTP server in Go"',
)

print(result.stdout)
sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('opencode', {
  envs: { ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY },
})

const result = await sandbox.commands.run(
  `opencode run "Create a hello world HTTP server in Go"`
)

console.log(result.stdout)
await sandbox.kill()
```

### Work on a Cloned Repository

**Python:**
```python
import os
from e2b import Sandbox

sandbox = Sandbox.create("opencode", envs={
    "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
}, timeout=600)

sandbox.git.clone("https://github.com/your-org/your-repo.git",
    path="/home/user/repo",
    username="x-access-token",
    password=os.environ["GITHUB_TOKEN"],
    depth=1,
)

result = sandbox.commands.run(
    'cd /home/user/repo && opencode run "Add error handling to all API endpoints"',
    on_stdout=lambda data: print(data, end=""),
)

diff = sandbox.commands.run("cd /home/user/repo && git diff")
print(diff.stdout)

sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('opencode', {
  envs: { ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY },
  timeoutMs: 600_000,
})

await sandbox.git.clone('https://github.com/your-org/your-repo.git', {
  path: '/home/user/repo',
  username: 'x-access-token',
  password: process.env.GITHUB_TOKEN,
  depth: 1,
})

const result = await sandbox.commands.run(
  `cd /home/user/repo && opencode run "Add error handling to all API endpoints"`,
  { onStdout: (data) => process.stdout.write(data) }
)

const diff = await sandbox.commands.run('cd /home/user/repo && git diff')
console.log(diff.stdout)

await sandbox.kill()
```

### OpenCode SDK (Headless HTTP Server)

OpenCode includes a headless HTTP server that you can control programmatically using the `@opencode-ai/sdk` client. Start the server inside a sandbox, get the public URL, and connect.

**Python:**
```python
import os
import time
import requests
from e2b import Sandbox

sandbox = Sandbox.beta_create("opencode", envs={
    "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
}, auto_pause=True, timeout=10 * 60)

# Start the OpenCode server
sandbox.commands.run(
    "opencode serve --hostname 0.0.0.0 --port 4096",
    background=True,
)

# Wait for the server to be ready
host = sandbox.get_host(4096)
base_url = f"https://{host}"
while True:
    try:
        requests.get(f"{base_url}/global/health")
        break
    except requests.ConnectionError:
        time.sleep(0.5)

# Create a session and send a prompt via the HTTP API
session = requests.post(f"{base_url}/session").json()
result = requests.post(
    f"{base_url}/session/{session['id']}/message",
    json={
        "parts": [{"type": "text", "text": "Create a hello world HTTP server in Go"}],
    },
).json()
print(result)
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'
import { createOpencodeClient } from '@opencode-ai/sdk'

const sandbox = await Sandbox.betaCreate('opencode', {
  envs: { ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY },
  autoPause: true,
  timeoutMs: 10 * 60 * 1000,
})

// Start the OpenCode server
sandbox.commands.run('opencode serve --hostname 0.0.0.0 --port 4096', {
  background: true,
})

// Wait for the server to be ready
const host = sandbox.getHost(4096)
const baseUrl = `https://${host}`
while (true) {
  try {
    await fetch(`${baseUrl}/global/health`)
    break
  } catch {
    await new Promise((r) => setTimeout(r, 500))
  }
}

// Connect to the server
const client = createOpencodeClient({
  baseUrl,
})

// Create a session and send a prompt
const { data: session } = await client.session.create({
  body: { title: 'E2B Session' },
})
const { data: result } = await client.session.prompt({
  path: { id: session.id },
  body: {
    parts: [{ type: 'text', text: 'Create a hello world HTTP server in Go' }],
  },
})
console.log(result)
```

### Custom Template for OpenCode (with Start Command)

OpenCode templates can optionally auto-start the HTTP server on sandbox creation.

**Python:**
```python
from e2b import Template, wait_for_port

template = (
    Template()
    .from_template("opencode")
    .set_envs({
        "OPENCODE_SERVER_PASSWORD": "your-password",
    })
    # Optional - start the OpenCode server on sandbox start
    .set_start_cmd(
        "opencode serve --hostname 0.0.0.0 --port 4096",
        wait_for_port(4096)
    )
)
```

**JavaScript/TypeScript:**
```typescript
import { Template, waitForPort } from 'e2b'

export const template = Template()
  .fromTemplate('opencode')
  .setEnvs({
    OPENCODE_SERVER_PASSWORD: 'your-password',
  })
  // Optional - start the OpenCode server on sandbox start
  .setStartCmd(
    'opencode serve --hostname 0.0.0.0 --port 4096',
    waitForPort(4096)
  )
```

---

## OpenClaw

Open-source personal AI assistant supporting multiple LLM providers and messaging channels. E2B provides the `openclaw` template with OpenClaw pre-installed.

### CLI Quick Start

```bash
e2b sbx create openclaw
# Once inside:
openclaw agent --local --message "Hello"
```

### Headless Execution

Use `openclaw agent --message` for non-interactive mode. Pass `--local` to use API keys from environment variables and `--thinking` to control reasoning depth.

**Python:**
```python
import os
from e2b import Sandbox

sandbox = Sandbox.create("openclaw", envs={
    "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
})

result = sandbox.commands.run(
    'openclaw agent --local --thinking high --message "Create a hello world HTTP server in Go"',
)

print(result.stdout)
sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('openclaw', {
  envs: { ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY },
})

const result = await sandbox.commands.run(
  `openclaw agent --local --thinking high --message "Create a hello world HTTP server in Go"`
)

console.log(result.stdout)
await sandbox.kill()
```

### Work on a Cloned Repository

**Python:**
```python
import os
from e2b import Sandbox

sandbox = Sandbox.create("openclaw", envs={
    "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
}, timeout=600)

sandbox.git.clone("https://github.com/your-org/your-repo.git",
    path="/home/user/repo",
    username="x-access-token",
    password=os.environ["GITHUB_TOKEN"],
    depth=1,
)

result = sandbox.commands.run(
    'cd /home/user/repo && openclaw agent --local --thinking high --message "Add error handling to all API endpoints"',
    on_stdout=lambda data: print(data, end=""),
)

diff = sandbox.commands.run("cd /home/user/repo && git diff")
print(diff.stdout)

sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('openclaw', {
  envs: { ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY },
  timeoutMs: 600_000,
})

await sandbox.git.clone('https://github.com/your-org/your-repo.git', {
  path: '/home/user/repo',
  username: 'x-access-token',
  password: process.env.GITHUB_TOKEN,
  depth: 1,
})

const result = await sandbox.commands.run(
  `cd /home/user/repo && openclaw agent --local --thinking high --message "Add error handling to all API endpoints"`,
  { onStdout: (data) => process.stdout.write(data) }
)

const diff = await sandbox.commands.run('cd /home/user/repo && git diff')
console.log(diff.stdout)

await sandbox.kill()
```

### Structured Output

Use `--json` for machine-readable responses with structured payload and metadata.

**Python:**
```python
import os
import json
from e2b import Sandbox

sandbox = Sandbox.create("openclaw", envs={
    "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
})

result = sandbox.commands.run(
    'openclaw agent --local --json --message "List all files in the current directory and describe each"',
)

response = json.loads(result.stdout)
print(response)

sandbox.kill()
```

### Customize SOUL.md

SOUL.md defines the agent's personality, boundaries, and operating principles. Write it into the workspace before running the agent.

**Python:**
```python
import os
from e2b import Sandbox

sandbox = Sandbox.create("openclaw", envs={
    "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
})

sandbox.files.write("/home/user/.openclaw/workspaces/default/SOUL.md", """
# Soul

## Core Truths
- Be genuinely helpful, not performatively helpful
- Be resourceful before asking -- check the workspace, search the web, read docs

## Boundaries
- Never share user data outside this session
- Be cautious with external actions (git push, API calls, file deletion)

## Vibe
Concise when needed, thorough when it matters.
""")

result = sandbox.commands.run(
    'openclaw agent --local --thinking high --message "Introduce yourself"',
    on_stdout=lambda data: print(data, end=""),
)

sandbox.kill()
```

### Customize HEARTBEAT.md

HEARTBEAT.md is a periodic checklist the agent reviews on a recurring schedule (roughly every 30 minutes). Use it for background task reminders.

**Python:**
```python
import os
from e2b import Sandbox

sandbox = Sandbox.create("openclaw", envs={
    "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
})

sandbox.files.write("/home/user/.openclaw/workspaces/default/HEARTBEAT.md", """
# Heartbeat Checklist

- Check for new issues in the repository
- Run the test suite if any files changed
- Review open pull requests for stale reviews
""")

result = sandbox.commands.run(
    'openclaw agent --local --message "Start monitoring the project"',
    on_stdout=lambda data: print(data, end=""),
)

sandbox.kill()
```

### Add Skills

OpenClaw supports skills via ClawHub. Skills are markdown files (SKILL.md) that extend the agent with additional tools.

**Python:**
```python
import os
from e2b import Sandbox

sandbox = Sandbox.create("openclaw", envs={
    "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
})

# Install a skill from ClawHub
sandbox.commands.run("clawhub install <skill-slug>")

# Or write a custom skill directly
sandbox.files.write("/home/user/.openclaw/workspaces/default/SKILL.md", """---
name: code-reviewer
description: Review code changes for bugs, security issues, and style violations.
user-invocable: true
---

# Code Reviewer

When asked to review code, follow these steps:

1. Read the changed files
2. Check for common bugs and security issues
3. Verify error handling is present
4. Output a structured review with severity levels
""")

result = sandbox.commands.run(
    'openclaw agent --local --message "Review the latest changes in this project"',
    on_stdout=lambda data: print(data, end=""),
)

sandbox.kill()
```

### Launch the Gateway (Web UI)

OpenClaw has a built-in web UI and chat interface served by its gateway.

**Python:**
```python
import os
from e2b import Sandbox

sandbox = Sandbox.beta_create("openclaw", envs={
    "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
}, auto_pause=True, timeout=10 * 60)

# Start the gateway
sandbox.commands.run("openclaw gateway --port 18789 --verbose")

host = sandbox.get_host(18789)
url = f"https://{host}"
print(f"OpenClaw Gateway: {url}")
print(f"Sandbox ID: {sandbox.sandbox_id}")
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.betaCreate('openclaw', {
  envs: { ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY },
  autoPause: true,
  timeoutMs: 10 * 60 * 1000,
})

// Start the gateway
sandbox.commands.run('openclaw gateway --port 18789 --verbose')

const host = sandbox.getHost(18789)
const url = `https://${host}`
console.log(`OpenClaw Gateway: ${url}`)
console.log(`Sandbox ID: ${sandbox.sandboxId}`)
```

### Custom Template for OpenClaw (with Gateway Start)

**Python:**
```python
from e2b import Template, wait_for_port

template = (
    Template()
    .from_template("openclaw")
    # Optional - start the OpenClaw gateway on sandbox start
    .set_start_cmd(
        "openclaw gateway --port 18789 --verbose",
        wait_for_port(18789)
    )
)
```

**JavaScript/TypeScript:**
```typescript
import { Template, waitForPort } from 'e2b'

export const template = Template()
  .fromTemplate('openclaw')
  // Optional - start the OpenClaw gateway on sandbox start
  .setStartCmd(
    'openclaw gateway --port 18789 --verbose',
    waitForPort(18789)
  )
```

---

## Computer Use / Desktop Sandbox

For AI agents that interact with graphical desktops (viewing screen, clicking, typing, scrolling). Uses the E2B Desktop SDK with VNC streaming.

### Install Desktop SDK

```bash
# Python
pip install e2b-desktop

# JavaScript/TypeScript
npm i @e2b/desktop
```

### Setting Up a Desktop Sandbox

**Python:**
```python
from e2b_desktop import Sandbox

# Create a desktop sandbox with a 5-minute timeout
sandbox = Sandbox.create(
    resolution=(1024, 720),
    dpi=96,
    timeout=300,
)

# Start VNC streaming for browser-based viewing
sandbox.stream.start()
stream_url = sandbox.stream.get_url()
print("View desktop at:", stream_url)
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from '@e2b/desktop'

// Create a desktop sandbox with a 5-minute timeout
const sandbox = await Sandbox.create({
  resolution: [1024, 720],
  dpi: 96,
  timeoutMs: 300_000,
})

// Start VNC streaming for browser-based viewing
await sandbox.stream.start()
const streamUrl = sandbox.stream.getUrl()
console.log('View desktop at:', streamUrl)
```

### Desktop Actions API

**Python:**
```python
from e2b_desktop import Sandbox

sandbox = Sandbox.create(timeout=300)

# Mouse actions
sandbox.left_click(500, 300)
sandbox.right_click(500, 300)
sandbox.double_click(500, 300)
sandbox.middle_click(500, 300)
sandbox.move_mouse(500, 300)
sandbox.drag([100, 200], [400, 500])

# Keyboard actions
sandbox.write("Hello, world!")  # Type text
sandbox.press("Enter")          # Press a key

# Scrolling
sandbox.scroll("down", 3)  # Scroll down 3 ticks
sandbox.scroll("up", 3)    # Scroll up 3 ticks

# Screenshots
screenshot = sandbox.screenshot()  # Returns bytes

# Run terminal commands
sandbox.commands.run("ls -la /home")
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from '@e2b/desktop'

const sandbox = await Sandbox.create({ timeoutMs: 300_000 })

// Mouse actions
await sandbox.leftClick(500, 300)
await sandbox.rightClick(500, 300)
await sandbox.doubleClick(500, 300)
await sandbox.middleClick(500, 300)
await sandbox.moveMouse(500, 300)
await sandbox.drag([100, 200], [400, 500])

// Keyboard actions
await sandbox.write('Hello, world!')  // Type text
await sandbox.press('Enter')          // Press a key

// Scrolling
await sandbox.scroll('down', 3)  // Scroll down 3 ticks
await sandbox.scroll('up', 3)    // Scroll up 3 ticks

// Screenshots
const screenshot = await sandbox.screenshot()  // Returns Buffer

// Run terminal commands
await sandbox.commands.run('ls -la /home')
```

### Computer Use Agent Loop

The core loop takes screenshots, sends them to an LLM, and executes the returned actions on the desktop.

**Python:**
```python
from e2b_desktop import Sandbox

sandbox = Sandbox.create(
    resolution=(1024, 720),
    timeout=300,
)
sandbox.stream.start()

while True:
    # 1. Capture the current desktop state
    screenshot = sandbox.screenshot()

    # 2. Send screenshot to your LLM and get the next action
    #    (use OpenAI Computer Use, Anthropic Claude, etc.)
    action = get_next_action_from_llm(screenshot)

    if not action:
        break  # LLM signals task is complete

    # 3. Execute the action on the desktop
    if action.type == "click":
        sandbox.left_click(action.x, action.y)
    elif action.type == "type":
        sandbox.write(action.text)
    elif action.type == "keypress":
        sandbox.press(action.keys)
    elif action.type == "scroll":
        direction = "up" if action.scroll_y < 0 else "down"
        sandbox.scroll(direction, abs(action.scroll_y))
    elif action.type == "drag":
        sandbox.drag(
            [action.start_x, action.start_y],
            [action.end_x, action.end_y],
        )

sandbox.kill()
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from '@e2b/desktop'

const sandbox = await Sandbox.create({
  resolution: [1024, 720],
  timeoutMs: 300_000,
})
await sandbox.stream.start()

while (true) {
  // 1. Capture the current desktop state
  const screenshot = await sandbox.screenshot()

  // 2. Send screenshot to your LLM and get the next action
  //    (use OpenAI Computer Use, Anthropic Claude, etc.)
  const action = await getNextActionFromLLM(screenshot)

  if (!action) break // LLM signals task is complete

  // 3. Execute the action on the desktop
  switch (action.type) {
    case 'click':
      await sandbox.leftClick(action.x, action.y)
      break
    case 'type':
      await sandbox.write(action.text)
      break
    case 'keypress':
      await sandbox.press(action.keys)
      break
    case 'scroll':
      await sandbox.scroll(
        action.scrollY < 0 ? 'up' : 'down',
        Math.abs(action.scrollY)
      )
      break
    case 'drag':
      await sandbox.drag(
        [action.startX, action.startY],
        [action.endX, action.endY]
      )
      break
  }
}

await sandbox.kill()
```

---

## Common Patterns

### Building Custom Templates (All Agents)

All agent templates follow the same pattern. Replace the template name accordingly.

**Python:**
```python
# build.py
from e2b import Template, default_build_logger
from template import template as agent_template

Template.build(agent_template, "my-agent-name",
    cpu_count=2,
    memory_mb=2048,
    on_build_logs=default_build_logger(),
)
```

**JavaScript/TypeScript:**
```typescript
// build.ts
import { Template, defaultBuildLogger } from 'e2b'
import { template as agentTemplate } from './template'

await Template.build(agentTemplate, 'my-agent-name', {
  cpuCount: 2,
  memoryMB: 2048,
  onBuildLogs: defaultBuildLogger(),
})
```

Run the build:

```bash
# JavaScript/TypeScript
npx tsx build.ts

# Python
python build.py
```

### Git Clone + Agent + Extract Diff (Generic Pattern)

This pattern works for any agent. Replace the agent command accordingly.

**Python:**
```python
import os
from e2b import Sandbox

sandbox = Sandbox.create("<template>", envs={
    "<API_KEY_VAR>": os.environ["<API_KEY_VAR>"],
}, timeout=600)

# Clone repository
sandbox.git.clone("https://github.com/your-org/your-repo.git",
    path="/home/user/repo",
    username="x-access-token",
    password=os.environ["GITHUB_TOKEN"],
    depth=1,
)

# Run agent
result = sandbox.commands.run(
    'cd /home/user/repo && <agent-command> "<prompt>"',
    on_stdout=lambda data: print(data, end=""),
)

# Extract results
diff = sandbox.commands.run("cd /home/user/repo && git diff")
print(diff.stdout)

sandbox.kill()
```

### Sandbox Persistence with Agents

Use auto-pause to keep sandboxes alive between agent runs. Resume with `Sandbox.connect()`.

**Python:**
```python
import os
from e2b import Sandbox

# Create with auto-pause enabled
sandbox = Sandbox.beta_create("<template>", envs={
    "<API_KEY_VAR>": os.environ["<API_KEY_VAR>"],
}, auto_pause=True, timeout=10 * 60)

sandbox_id = sandbox.sandbox_id

# Run first task
sandbox.commands.run('<agent-command> "<first task>"')

# Sandbox auto-pauses after timeout

# Later: resume and continue
sandbox = Sandbox.connect(sandbox_id)
sandbox.commands.run('<agent-command> "<follow-up task>"')
```

**JavaScript/TypeScript:**
```typescript
import { Sandbox } from 'e2b'

// Create with auto-pause enabled
const sandbox = await Sandbox.betaCreate('<template>', {
  envs: { '<API_KEY_VAR>': process.env['<API_KEY_VAR>'] },
  autoPause: true,
  timeoutMs: 10 * 60 * 1000,
})

const sandboxId = sandbox.sandboxId

// Run first task
await sandbox.commands.run('<agent-command> "<first task>"')

// Sandbox auto-pauses after timeout

// Later: resume and continue
const resumed = await Sandbox.connect(sandboxId)
await resumed.commands.run('<agent-command> "<follow-up task>"')
```
