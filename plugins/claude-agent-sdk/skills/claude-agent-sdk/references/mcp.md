# MCP in the SDK

Extend Claude Code with custom tools using Model Context Protocol servers.

## Transport Types

### stdio Servers

External processes communicating via stdin/stdout:

```json
{
  "mcpServers": {
    "my-tool": {
      "command": "node",
      "args": ["./my-mcp-server.js"],
      "env": { "DEBUG": "false" }
    }
  }
}
```

### HTTP/SSE Servers

Remote servers with network communication:

```json
{
  "mcpServers": {
    "remote-api": {
      "type": "sse",
      "url": "https://api.example.com/mcp/sse",
      "headers": { "Authorization": "Bearer ${API_TOKEN}" }
    },
    "http-service": {
      "type": "http",
      "url": "https://api.example.com/mcp",
      "headers": { "X-API-Key": "${API_KEY}" }
    }
  }
}
```

### SDK MCP Servers

In-process servers running within your application. See [custom-tools.md](custom-tools.md).

## Configuration

### Basic .mcp.json Configuration

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem"],
      "env": { "ALLOWED_PATHS": "/Users/me/projects" }
    }
  }
}
```

### SDK Usage

**TypeScript:**
```typescript
for await (const message of query({
  prompt: "List files in my project",
  options: {
    mcpServers: {
      "filesystem": {
        command: "npx",
        args: ["@modelcontextprotocol/server-filesystem"],
        env: { ALLOWED_PATHS: "/Users/me/projects" }
      }
    },
    allowedTools: ["mcp__filesystem__list_files"]
  }
})) {
  if (message.type === "result" && message.subtype === "success") {
    console.log(message.result);
  }
}
```

**Python:**
```python
async for message in query(
    prompt="List files in my project",
    options={
        "mcpServers": {
            "filesystem": {
                "command": "python",
                "args": ["-m", "mcp_server_filesystem"],
                "env": { "ALLOWED_PATHS": "/Users/me/projects" }
            }
        },
        "allowedTools": ["mcp__filesystem__list_files"]
    }
):
    if message["type"] == "result":
        print(message["result"])
```

## Resource Management

List and read MCP resources:

```typescript
for await (const message of query({
  prompt: "What resources are available from the database server?",
  options: {
    mcpServers: {
      "database": { command: "npx", args: ["@modelcontextprotocol/server-database"] }
    },
    allowedTools: ["mcp__list_resources", "mcp__read_resource"]
  }
})) {
  if (message.type === "result") console.log(message.result);
}
```

## Authentication

### Environment Variables

```json
{
  "mcpServers": {
    "secure-api": {
      "type": "sse",
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${API_TOKEN}",
        "X-API-Key": "${API_KEY:-default-key}"
      }
    }
  }
}
```

## Error Handling

```typescript
for await (const message of query({
  prompt: "Process data",
  options: { mcpServers: { "data-processor": dataServer } }
})) {
  if (message.type === "system" && message.subtype === "init") {
    const failedServers = message.mcp_servers.filter(s => s.status !== "connected");
    if (failedServers.length > 0) {
      console.warn("Failed to connect:", failedServers);
    }
  }

  if (message.type === "result" && message.subtype === "error_during_execution") {
    console.error("Execution failed");
  }
}
```
