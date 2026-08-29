# Python SDK Reference

## Table of Contents
- [Installation](#installation)
- [Functions](#functions)
- [Classes](#classes)
- [Types](#types)
- [Message Types](#message-types)
- [Hook Types](#hook-types)
- [Tool Input/Output Types](#tool-inputoutput-types)

## Installation

```bash
pip install claude-agent-sdk
```

## Choosing Between `query()` and `ClaudeSDKClient`

| Feature | `query()` | `ClaudeSDKClient` |
|---------|-----------|-------------------|
| Session | Creates new each time | Reuses same session |
| Conversation | Single exchange | Multiple exchanges |
| Streaming Input | ✅ | ✅ |
| Interrupts | ❌ | ✅ |
| Hooks | ❌ | ✅ |
| Custom Tools | ❌ | ✅ |
| Continue Chat | ❌ | ✅ |

## Functions

### `query()`

Creates new session for each interaction:

```python
async def query(
    *,
    prompt: str | AsyncIterable[dict[str, Any]],
    options: ClaudeAgentOptions | None = None
) -> AsyncIterator[Message]
```

**Example:**
```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    options = ClaudeAgentOptions(
        system_prompt="You are an expert Python developer",
        permission_mode='acceptEdits',
        cwd="/home/user/project"
    )
    async for message in query(prompt="Create a web server", options=options):
        print(message)
```

### `tool()`

Decorator for defining MCP tools:

```python
from claude_agent_sdk import tool

@tool("greet", "Greet a user", {"name": str})
async def greet(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": f"Hello, {args['name']}!"}]
    }
```

### `create_sdk_mcp_server()`

Create in-process MCP server:

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("add", "Add two numbers", {"a": float, "b": float})
async def add(args):
    return {"content": [{"type": "text", "text": f"Sum: {args['a'] + args['b']}"}]}

calculator = create_sdk_mcp_server(
    name="calculator",
    version="2.0.0",
    tools=[add]
)
```

## Classes

### `ClaudeSDKClient`

Maintains conversation session across multiple exchanges:

```python
class ClaudeSDKClient:
    def __init__(self, options: ClaudeAgentOptions | None = None)
    async def connect(self, prompt: str | AsyncIterable[dict] | None = None) -> None
    async def query(self, prompt: str | AsyncIterable[dict], session_id: str = "default") -> None
    async def receive_messages(self) -> AsyncIterator[Message]
    async def receive_response(self) -> AsyncIterator[Message]
    async def interrupt(self) -> None
    async def disconnect(self) -> None
```

**Context Manager Example:**
```python
async with ClaudeSDKClient() as client:
    await client.query("Hello Claude")
    async for message in client.receive_response():
        print(message)
```

**Continuing Conversation:**
```python
async with ClaudeSDKClient() as client:
    await client.query("What's the capital of France?")
    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")

    # Follow-up - Claude remembers context
    await client.query("What's the population of that city?")
    async for message in client.receive_response():
        # Process response
        pass
```

## Types

### `ClaudeAgentOptions`

```python
@dataclass
class ClaudeAgentOptions:
    allowed_tools: list[str] = field(default_factory=list)
    system_prompt: str | SystemPromptPreset | None = None
    mcp_servers: dict[str, McpServerConfig] | str | Path = field(default_factory=dict)
    permission_mode: PermissionMode | None = None
    continue_conversation: bool = False
    resume: str | None = None
    max_turns: int | None = None
    disallowed_tools: list[str] = field(default_factory=list)
    model: str | None = None
    output_format: OutputFormat | None = None
    cwd: str | Path | None = None
    can_use_tool: CanUseTool | None = None
    hooks: dict[HookEvent, list[HookMatcher]] | None = None
    agents: dict[str, AgentDefinition] | None = None
    setting_sources: list[SettingSource] | None = None
    plugins: list[SdkPluginConfig] = field(default_factory=list)
```

### `PermissionMode`

```python
PermissionMode = Literal[
    "default",           # Standard permission behavior
    "acceptEdits",       # Auto-accept file edits
    "plan",              # Planning mode - no execution
    "bypassPermissions"  # Bypass all permission checks
]
```

### `SettingSource`

```python
SettingSource = Literal["user", "project", "local"]
```

- `"user"`: `~/.claude/settings.json`
- `"project"`: `.claude/settings.json`
- `"local"`: `.claude/settings.local.json`

### `AgentDefinition`

```python
@dataclass
class AgentDefinition:
    description: str
    prompt: str
    tools: list[str] | None = None
    model: Literal["sonnet", "opus", "haiku", "inherit"] | None = None
```

## Message Types

```python
Message = UserMessage | AssistantMessage | SystemMessage | ResultMessage
```

### `ResultMessage`

```python
@dataclass
class ResultMessage:
    subtype: str
    duration_ms: int
    duration_api_ms: int
    is_error: bool
    num_turns: int
    session_id: str
    total_cost_usd: float | None = None
    usage: dict[str, Any] | None = None
    result: str | None = None
```

## Content Block Types

```python
ContentBlock = TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock
```

## Hook Types

### `HookEvent`

```python
HookEvent = Literal[
    "PreToolUse",
    "PostToolUse",
    "UserPromptSubmit",
    "Stop",
    "SubagentStop",
    "PreCompact"
]
```

### `HookMatcher`

```python
@dataclass
class HookMatcher:
    matcher: str | None = None
    hooks: list[HookCallback] = field(default_factory=list)
    timeout: float | None = None  # Default: 60 seconds
```

**Hook Example:**
```python
async def validate_bash_command(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> dict[str, Any]:
    if input_data['tool_name'] == 'Bash':
        command = input_data['tool_input'].get('command', '')
        if 'rm -rf /' in command:
            return {
                'hookSpecificOutput': {
                    'hookEventName': 'PreToolUse',
                    'permissionDecision': 'deny',
                    'permissionDecisionReason': 'Dangerous command blocked'
                }
            }
    return {}

options = ClaudeAgentOptions(
    hooks={
        'PreToolUse': [HookMatcher(matcher='Bash', hooks=[validate_bash_command])]
    }
)
```

## Error Types

```python
class ClaudeSDKError(Exception): pass
class CLINotFoundError(CLIConnectionError): pass
class CLIConnectionError(ClaudeSDKError): pass
class ProcessError(ClaudeSDKError): pass
class CLIJSONDecodeError(ClaudeSDKError): pass
```
