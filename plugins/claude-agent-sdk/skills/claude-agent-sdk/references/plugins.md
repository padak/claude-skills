# Plugins in the SDK

Load custom plugins to extend Claude Code with commands, agents, skills, and hooks.

## What Plugins Provide

- **Commands**: Custom slash commands
- **Agents**: Specialized subagents
- **Skills**: Model-invoked capabilities
- **Hooks**: Event handlers
- **MCP servers**: External tool integrations

## Loading Plugins

### TypeScript

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Hello",
  options: {
    plugins: [
      { type: "local", path: "./my-plugin" },
      { type: "local", path: "/absolute/path/to/another-plugin" }
    ]
  }
})) {
  // Plugin features are now available
}
```

### Python

```python
from claude_agent_sdk import query

async for message in query(
    prompt="Hello",
    options={
        "plugins": [
            {"type": "local", "path": "./my-plugin"},
            {"type": "local", "path": "/absolute/path/to/another-plugin"}
        ]
    }
):
    pass
```

## Path Specifications

- **Relative paths**: Resolved from current working directory
- **Absolute paths**: Full file system paths

Path should point to plugin root directory (containing `.claude-plugin/plugin.json`).

## Verifying Plugin Installation

### TypeScript

```typescript
for await (const message of query({
  prompt: "Hello",
  options: { plugins: [{ type: "local", path: "./my-plugin" }] }
})) {
  if (message.type === "system" && message.subtype === "init") {
    console.log("Plugins:", message.plugins);
    console.log("Commands:", message.slash_commands);
  }
}
```

### Python

```python
async for message in query(
    prompt="Hello",
    options={"plugins": [{"type": "local", "path": "./my-plugin"}]}
):
    if message.type == "system" and message.subtype == "init":
        print("Plugins:", message.data.get("plugins"))
        print("Commands:", message.data.get("slash_commands"))
```

## Using Plugin Commands

Commands are namespaced: `plugin-name:command-name`

```typescript
for await (const message of query({
  prompt: "/my-plugin:greet",  // Use plugin command
  options: { plugins: [{ type: "local", path: "./my-plugin" }] }
})) {
  if (message.type === "assistant") {
    console.log(message.content);
  }
}
```

## Plugin Structure

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # Required manifest
├── commands/                 # Custom slash commands
│   └── custom-cmd.md
├── agents/                   # Custom agents
│   └── specialist.md
├── skills/                   # Agent Skills
│   └── my-skill/
│       └── SKILL.md
├── hooks/                    # Event handlers
│   └── hooks.json
└── .mcp.json                # MCP server definitions
```

## Common Use Cases

### Development and Testing

```typescript
plugins: [{ type: "local", path: "./dev-plugins/my-plugin" }]
```

### Project-Specific Extensions

```typescript
plugins: [{ type: "local", path: "./project-plugins/team-workflows" }]
```

### Multiple Plugin Sources

```typescript
plugins: [
  { type: "local", path: "./local-plugin" },
  { type: "local", path: "~/.claude/custom-plugins/shared-plugin" }
]
```

## Troubleshooting

### Plugin Not Loading

1. Check path points to plugin root (containing `.claude-plugin/`)
2. Validate `plugin.json` has valid JSON syntax
3. Check file permissions

### Commands Not Available

1. Use namespace: `plugin-name:command-name`
2. Verify command appears in `slash_commands` in init message
3. Validate command files are in `commands/` directory
