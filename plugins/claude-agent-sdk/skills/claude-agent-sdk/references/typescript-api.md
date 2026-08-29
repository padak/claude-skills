# TypeScript SDK Reference

## Table of Contents
- [Installation](#installation)
- [Functions](#functions)
- [Types](#types)
- [Message Types](#message-types)
- [Hook Types](#hook-types)
- [Tool Input/Output Types](#tool-inputoutput-types)

## Installation

```bash
npm install @anthropic-ai/claude-agent-sdk
```

## Functions

### `query()`

Primary function for interacting with Claude Code:

```typescript
function query({
  prompt,
  options
}: {
  prompt: string | AsyncIterable<SDKUserMessage>;
  options?: Options;
}): Query
```

**Example:**
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

### `tool()`

Create type-safe MCP tool definition:

```typescript
import { z } from "zod";

tool(
  "get_weather",
  "Get current temperature",
  {
    latitude: z.number().describe("Latitude"),
    longitude: z.number().describe("Longitude")
  },
  async (args) => {
    const response = await fetch(`https://api.weather.com?lat=${args.latitude}&lon=${args.longitude}`);
    const data = await response.json();
    return {
      content: [{ type: "text", text: `Temperature: ${data.temp}°F` }]
    };
  }
)
```

### `createSdkMcpServer()`

Create in-process MCP server:

```typescript
const server = createSdkMcpServer({
  name: "my-tools",
  version: "1.0.0",
  tools: [weatherTool, calculatorTool]
});
```

## Types

### `Options`

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `abortController` | `AbortController` | `new AbortController()` | Cancel operations |
| `additionalDirectories` | `string[]` | `[]` | Additional accessible directories |
| `agents` | `Record<string, AgentDefinition>` | `undefined` | Programmatic subagents |
| `allowedTools` | `string[]` | All tools | Allowed tool names |
| `canUseTool` | `CanUseTool` | `undefined` | Custom permission function |
| `continue` | `boolean` | `false` | Continue recent conversation |
| `cwd` | `string` | `process.cwd()` | Working directory |
| `disallowedTools` | `string[]` | `[]` | Disallowed tool names |
| `forkSession` | `boolean` | `false` | Fork when resuming |
| `hooks` | `Partial<Record<HookEvent, HookCallbackMatcher[]>>` | `{}` | Hook callbacks |
| `includePartialMessages` | `boolean` | `false` | Include partial messages |
| `maxTurns` | `number` | `undefined` | Maximum conversation turns |
| `mcpServers` | `Record<string, McpServerConfig>` | `{}` | MCP server configs |
| `model` | `string` | Default CLI | Claude model |
| `outputFormat` | `{ type: 'json_schema', schema: JSONSchema }` | `undefined` | Structured output |
| `permissionMode` | `PermissionMode` | `'default'` | Permission mode |
| `plugins` | `SdkPluginConfig[]` | `[]` | Custom plugins |
| `resume` | `string` | `undefined` | Session ID to resume |
| `settingSources` | `SettingSource[]` | `[]` | Filesystem settings to load |
| `systemPrompt` | `string \| SystemPromptPreset` | `undefined` | System prompt |

### `Query`

```typescript
interface Query extends AsyncGenerator<SDKMessage, void> {
  interrupt(): Promise<void>;
  setPermissionMode(mode: PermissionMode): Promise<void>;
}
```

### `AgentDefinition`

```typescript
type AgentDefinition = {
  description: string;
  tools?: string[];
  prompt: string;
  model?: 'sonnet' | 'opus' | 'haiku' | 'inherit';
}
```

### `SettingSource`

```typescript
type SettingSource = 'user' | 'project' | 'local';
```

### `PermissionMode`

```typescript
type PermissionMode =
  | 'default'           // Standard permission behavior
  | 'acceptEdits'       // Auto-accept file edits
  | 'bypassPermissions' // Bypass all permission checks
  | 'plan'              // Planning mode - no execution
```

### `CanUseTool`

```typescript
type CanUseTool = (
  toolName: string,
  input: ToolInput,
  options: { signal: AbortSignal; suggestions?: PermissionUpdate[] }
) => Promise<PermissionResult>;
```

### `PermissionResult`

```typescript
type PermissionResult =
  | { behavior: 'allow'; updatedInput: ToolInput; updatedPermissions?: PermissionUpdate[]; }
  | { behavior: 'deny'; message: string; interrupt?: boolean; }
```

### `McpServerConfig`

```typescript
type McpServerConfig =
  | McpStdioServerConfig
  | McpSSEServerConfig
  | McpHttpServerConfig
  | McpSdkServerConfigWithInstance;

type McpStdioServerConfig = {
  type?: 'stdio';
  command: string;
  args?: string[];
  env?: Record<string, string>;
}

type McpSSEServerConfig = {
  type: 'sse';
  url: string;
  headers?: Record<string, string>;
}
```

## Message Types

### `SDKMessage`

```typescript
type SDKMessage =
  | SDKAssistantMessage
  | SDKUserMessage
  | SDKResultMessage
  | SDKSystemMessage
  | SDKPartialAssistantMessage
  | SDKCompactBoundaryMessage;
```

### `SDKResultMessage`

```typescript
type SDKResultMessage = {
  type: 'result';
  subtype: 'success' | 'error_max_turns' | 'error_during_execution';
  session_id: string;
  duration_ms: number;
  is_error: boolean;
  num_turns: number;
  result?: string;
  total_cost_usd: number;
  usage: NonNullableUsage;
}
```

### `SDKSystemMessage`

```typescript
type SDKSystemMessage = {
  type: 'system';
  subtype: 'init';
  session_id: string;
  tools: string[];
  mcp_servers: { name: string; status: string; }[];
  model: string;
  permissionMode: PermissionMode;
  slash_commands: string[];
}
```

## Hook Types

### `HookEvent`

```typescript
type HookEvent =
  | 'PreToolUse'
  | 'PostToolUse'
  | 'Notification'
  | 'UserPromptSubmit'
  | 'SessionStart'
  | 'SessionEnd'
  | 'Stop'
  | 'SubagentStop'
  | 'PreCompact';
```

### `HookCallbackMatcher`

```typescript
interface HookCallbackMatcher {
  matcher?: string;
  hooks: HookCallback[];
  timeout?: number;  // Default: 60 seconds
}
```

### `HookJSONOutput`

```typescript
type SyncHookJSONOutput = {
  continue?: boolean;
  suppressOutput?: boolean;
  decision?: 'approve' | 'block';
  systemMessage?: string;
  hookSpecificOutput?: {
    hookEventName: 'PreToolUse';
    permissionDecision?: 'allow' | 'deny' | 'ask';
    permissionDecisionReason?: string;
  } | {
    hookEventName: 'UserPromptSubmit';
    additionalContext?: string;
  };
}
```

## Tool Types

### Common Tool Inputs

```typescript
interface BashInput {
  command: string;
  timeout?: number;
  description?: string;
  run_in_background?: boolean;
}

interface FileReadInput {
  file_path: string;
  offset?: number;
  limit?: number;
}

interface FileEditInput {
  file_path: string;
  old_string: string;
  new_string: string;
  replace_all?: boolean;
}

interface GrepInput {
  pattern: string;
  path?: string;
  glob?: string;
  output_mode?: 'content' | 'files_with_matches' | 'count';
}
```
