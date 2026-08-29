# Custom Tools

Build and integrate custom tools to extend Claude Agent SDK functionality through in-process MCP servers.

## Creating Custom Tools

### TypeScript

```typescript
import { query, tool, createSdkMcpServer } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

const customServer = createSdkMcpServer({
  name: "my-custom-tools",
  version: "1.0.0",
  tools: [
    tool(
      "get_weather",
      "Get current temperature for a location",
      {
        latitude: z.number().describe("Latitude coordinate"),
        longitude: z.number().describe("Longitude coordinate")
      },
      async (args) => {
        const response = await fetch(
          `https://api.open-meteo.com/v1/forecast?latitude=${args.latitude}&longitude=${args.longitude}&current=temperature_2m`
        );
        const data = await response.json();
        return {
          content: [{ type: "text", text: `Temperature: ${data.current.temperature_2m}°F` }]
        };
      }
    )
  ]
});
```

### Python

```python
from claude_agent_sdk import tool, create_sdk_mcp_server
import aiohttp

@tool("get_weather", "Get current temperature", {"latitude": float, "longitude": float})
async def get_weather(args: dict[str, Any]) -> dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={args['latitude']}&longitude={args['longitude']}&current=temperature_2m"
        ) as response:
            data = await response.json()
    return {
        "content": [{"type": "text", "text": f"Temperature: {data['current']['temperature_2m']}°F"}]
    }

custom_server = create_sdk_mcp_server(
    name="my-custom-tools",
    version="1.0.0",
    tools=[get_weather]
)
```

## Using Custom Tools

**Important:** Custom MCP tools require streaming input mode. Use async generator for the prompt.

### Tool Name Format

Pattern: `mcp__{server_name}__{tool_name}`
Example: `mcp__my-custom-tools__get_weather`

### TypeScript Usage

```typescript
async function* generateMessages() {
  yield {
    type: "user" as const,
    message: { role: "user" as const, content: "What's the weather in San Francisco?" }
  };
}

for await (const message of query({
  prompt: generateMessages(),
  options: {
    mcpServers: { "my-custom-tools": customServer },
    allowedTools: ["mcp__my-custom-tools__get_weather"],
    maxTurns: 3
  }
})) {
  if (message.type === "result" && message.subtype === "success") {
    console.log(message.result);
  }
}
```

### Python Usage

```python
options = ClaudeAgentOptions(
    mcp_servers={"my-custom-tools": custom_server},
    allowed_tools=["mcp__my-custom-tools__get_weather"]
)

async with ClaudeSDKClient(options=options) as client:
    await client.query("What's the weather in San Francisco?")
    async for msg in client.receive_response():
        print(msg)
```

## Input Schema Options

### Simple Type Mapping (Recommended)

```python
@tool("process", "Process data", {"name": str, "count": int, "enabled": bool})
```

### JSON Schema Format

```python
@tool("process", "Process data", {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "count": {"type": "integer", "minimum": 0}
    },
    "required": ["name"]
})
```

## Error Handling

```typescript
tool(
  "fetch_data",
  "Fetch data from API",
  { endpoint: z.string().url() },
  async (args) => {
    try {
      const response = await fetch(args.endpoint);
      if (!response.ok) {
        return {
          content: [{ type: "text", text: `API error: ${response.status}` }]
        };
      }
      const data = await response.json();
      return {
        content: [{ type: "text", text: JSON.stringify(data, null, 2) }]
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: `Failed: ${error.message}` }]
      };
    }
  }
)
```

## Example: Database Query Tool

```typescript
const databaseServer = createSdkMcpServer({
  name: "database-tools",
  version: "1.0.0",
  tools: [
    tool(
      "query_database",
      "Execute a database query",
      {
        query: z.string().describe("SQL query"),
        params: z.array(z.any()).optional().describe("Query parameters")
      },
      async (args) => {
        const results = await db.query(args.query, args.params || []);
        return {
          content: [{ type: "text", text: `Found ${results.length} rows:\n${JSON.stringify(results, null, 2)}` }]
        };
      }
    )
  ]
});
```

## Example: Calculator Tool

```python
@tool("calculate", "Perform calculations", {"expression": str, "precision": int})
async def calculate(args: dict[str, Any]) -> dict[str, Any]:
    try:
        result = eval(args["expression"], {"__builtins__": {}})
        precision = args.get("precision", 2)
        return {
            "content": [{"type": "text", "text": f"{args['expression']} = {round(result, precision)}"}]
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}]
        }
```
