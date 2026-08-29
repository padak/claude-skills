---
name: claude-agent-sdk
description: Build production applications with Claude Agent SDK (TypeScript and Python). Use when writing code that uses @anthropic-ai/claude-agent-sdk or claude-agent-sdk packages, creating agents with query(), ClaudeSDKClient, custom MCP tools, subagents, session management, permissions, hooks, plugins, structured outputs, or cost tracking. Also use for hosting/deploying SDK-based agents.
---

# Claude Agent SDK

Build production applications that leverage Claude's agentic coding capabilities.

## Quick Start

**TypeScript:**
```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Analyze this codebase",
  options: {
    maxTurns: 10,
    allowedTools: ["Read", "Grep", "Glob"]
  }
})) {
  if (message.type === "result" && message.subtype === "success") {
    console.log(message.result);
  }
}
```

**Python:**
```python
from claude_agent_sdk import query, ClaudeAgentOptions

async for message in query(
    prompt="Analyze this codebase",
    options=ClaudeAgentOptions(
        max_turns=10,
        allowed_tools=["Read", "Grep", "Glob"]
    )
):
    if message.type == "result":
        print(message.result)
```

## Reference Documentation

| Topic | Description |
|-------|-------------|
| [overview.md](references/overview.md) | Installation, authentication, core concepts |
| [python-api.md](references/python-api.md) | Python SDK complete API reference |
| [typescript-api.md](references/typescript-api.md) | TypeScript SDK complete API reference |
| [custom-tools.md](references/custom-tools.md) | Creating custom MCP tools |
| [mcp.md](references/mcp.md) | Model Context Protocol integration |
| [permissions.md](references/permissions.md) | Permission modes and canUseTool |
| [hosting.md](references/hosting.md) | Production deployment patterns |
| [sessions.md](references/sessions.md) | Session management and resumption |
| [subagents.md](references/subagents.md) | Creating specialized subagents |
| [streaming.md](references/streaming.md) | Streaming vs single message input |
| [structured-output.md](references/structured-output.md) | JSON schema validated outputs |
| [costs.md](references/costs.md) | Token usage and cost tracking |
| [skills.md](references/skills.md) | Agent Skills in SDK |
| [plugins.md](references/plugins.md) | Loading custom plugins |
| [slash-commands.md](references/slash-commands.md) | Custom slash commands |
| [system-prompt.md](references/system-prompt.md) | Modifying system prompts |
| [todos.md](references/todos.md) | Todo list tracking |

## Common Patterns

### Basic Query

```typescript
for await (const message of query({
  prompt: "Your task",
  options: { maxTurns: 5, model: "claude-sonnet-4-5" }
})) {
  console.log(message);
}
```

### With Custom Tools

```typescript
import { tool, createSdkMcpServer } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

const server = createSdkMcpServer({
  name: "my-tools",
  version: "1.0.0",
  tools: [
    tool("get_data", "Fetch data", { id: z.string() }, async (args) => ({
      content: [{ type: "text", text: `Data for ${args.id}` }]
    }))
  ]
});

// Use with streaming input
async function* messages() {
  yield { type: "user", message: { role: "user", content: "Get data for user-123" } };
}

for await (const msg of query({
  prompt: messages(),
  options: {
    mcpServers: { "my-tools": server },
    allowedTools: ["mcp__my-tools__get_data"]
  }
})) {
  console.log(msg);
}
```

### With Subagents

```typescript
const result = query({
  prompt: "Review this code",
  options: {
    agents: {
      'reviewer': {
        description: 'Code review specialist',
        prompt: 'You are a code reviewer...',
        tools: ['Read', 'Grep'],
        model: 'sonnet'
      }
    }
  }
});
```

### With Structured Output

```typescript
for await (const message of query({
  prompt: "Extract user info",
  options: {
    outputFormat: {
      type: 'json_schema',
      schema: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          email: { type: 'string' }
        },
        required: ['name', 'email']
      }
    }
  }
})) {
  if (message.structured_output) {
    console.log(message.structured_output);
  }
}
```

### Session Management

```typescript
// Get session ID
let sessionId: string;
for await (const msg of query({ prompt: "Hello" })) {
  if (msg.type === 'system' && msg.subtype === 'init') {
    sessionId = msg.session_id;
  }
}

// Resume later
for await (const msg of query({
  prompt: "Continue",
  options: { resume: sessionId }
})) {
  console.log(msg);
}
```

### Permission Control

```typescript
const result = query({
  prompt: "Make changes",
  options: {
    permissionMode: 'acceptEdits',  // Auto-accept file edits
    canUseTool: async (toolName, input) => {
      if (toolName === "Bash" && input.command?.includes("rm")) {
        return { behavior: "deny", message: "Deletion not allowed" };
      }
      return { behavior: "allow", updatedInput: input };
    }
  }
});
```

## Key Options

| Option | Description |
|--------|-------------|
| `maxTurns` | Maximum conversation turns |
| `allowedTools` | Explicitly allowed tools |
| `disallowedTools` | Explicitly blocked tools |
| `permissionMode` | `default`, `acceptEdits`, `bypassPermissions` |
| `model` | Claude model to use |
| `mcpServers` | MCP server configurations |
| `agents` | Subagent definitions |
| `outputFormat` | Structured output schema |
| `resume` | Session ID to resume |
| `systemPrompt` | Custom or preset system prompt |
| `hooks` | Event hook callbacks |
| `plugins` | Plugin configurations |
| `settingSources` | Load settings from `user`, `project`, `local` |

## Message Types

- `system` (subtype: `init`) - Session started, lists tools and commands
- `assistant` - Claude's response with content blocks
- `result` (subtype: `success`, `error_max_turns`, `error_during_execution`) - Final result
- `user` - User messages (tool results)
