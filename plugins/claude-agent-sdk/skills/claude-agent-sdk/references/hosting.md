# Hosting the Agent SDK

Deploy and host Claude Agent SDK in production environments.

## Understanding the Architecture

Unlike stateless API calls, the Claude Agent SDK operates as a **long-running process** that:
- Executes commands in a persistent shell environment
- Manages file operations within a working directory
- Handles tool execution with context from previous interactions

## Hosting Requirements

### Container-Based Sandboxing

For security and isolation:
- **Process isolation** - Separate execution environment per session
- **Resource limits** - CPU, memory, and storage constraints
- **Network control** - Restrict outbound connections
- **Ephemeral filesystems** - Clean state for each session

### System Requirements

- **Runtime dependencies**
  - Python 3.10+ (Python SDK) or Node.js 18+ (TypeScript SDK)
  - Node.js (required by Claude Code CLI)
  - Claude Code CLI: `npm install -g @anthropic-ai/claude-code`

- **Resource allocation**
  - Recommended: 1GiB RAM, 5GiB disk, 1 CPU (adjust for task)

- **Network access**
  - Outbound HTTPS to `api.anthropic.com`
  - Optional: Access to MCP servers or external tools

## Sandbox Providers

- [Cloudflare Sandboxes](https://github.com/cloudflare/sandbox-sdk)
- [Modal Sandboxes](https://modal.com/docs/guide/sandbox)
- [Daytona](https://www.daytona.io/)
- [E2B](https://e2b.dev/)
- [Fly Machines](https://fly.io/docs/machines/)
- [Vercel Sandbox](https://vercel.com/docs/functions/sandbox)

## Deployment Patterns

### Pattern 1: Ephemeral Sessions

New container per task, destroyed when complete.

**Best for:** One-off tasks
**Examples:**
- Bug Investigation & Fix
- Invoice Processing
- Translation Tasks
- Image/Video Processing

### Pattern 2: Long-Running Sessions

Persistent container instances for long-running tasks.

**Best for:** Proactive agents, content serving, high-frequency messaging
**Examples:**
- Email Agent (monitors and responds to emails)
- Site Builder (hosts custom websites)
- High-Frequency Chat Bots

### Pattern 3: Hybrid Sessions

Ephemeral containers hydrated with history and state.

**Best for:** Intermittent interaction that spins down when idle
**Examples:**
- Personal Project Manager
- Deep Research
- Customer Support Agent

### Pattern 4: Single Containers

Multiple SDK processes in one global container.

**Best for:** Agent collaboration/simulations
**Examples:**
- Video game agent simulations

## FAQ

**Container communication?**
Expose ports for HTTP/WebSocket endpoints while SDK runs internally.

**Container cost?**
~5 cents/hour minimum; tokens are typically the dominant cost.

**Idle container management?**
Tune provider-specific idle timeouts based on expected user response frequency.

**CLI updates?**
Versioned with semver; breaking changes are versioned.

**Container health monitoring?**
Use same logging infrastructure as backend.

**Session timeout?**
Sessions don't timeout, but set `maxTurns` to prevent infinite loops.
