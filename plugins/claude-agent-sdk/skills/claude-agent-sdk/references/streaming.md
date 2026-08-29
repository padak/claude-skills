# Streaming Input

Two input modes for Claude Agent SDK.

## Streaming Input Mode (Recommended)

Persistent, interactive session with full access to capabilities.

### Benefits

- **Image Uploads**: Attach images for visual analysis
- **Queued Messages**: Multiple messages process sequentially with interruption
- **Tool Integration**: Full access to all tools and custom MCP servers
- **Hooks Support**: Lifecycle hooks for customization
- **Real-time Feedback**: See responses as generated
- **Context Persistence**: Maintain conversation context

### TypeScript Example

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";
import { readFileSync } from "fs";

async function* generateMessages() {
  yield {
    type: "user" as const,
    message: {
      role: "user" as const,
      content: "Analyze this codebase for security issues"
    }
  };

  await new Promise(resolve => setTimeout(resolve, 2000));

  // Follow-up with image
  yield {
    type: "user" as const,
    message: {
      role: "user" as const,
      content: [
        { type: "text", text: "Review this architecture diagram" },
        {
          type: "image",
          source: {
            type: "base64",
            media_type: "image/png",
            data: readFileSync("diagram.png", "base64")
          }
        }
      ]
    }
  };
}

for await (const message of query({
  prompt: generateMessages(),
  options: { maxTurns: 10, allowedTools: ["Read", "Grep"] }
})) {
  if (message.type === "result") {
    console.log(message.result);
  }
}
```

### Python Example

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import asyncio
import base64

async def streaming_analysis():
    async def message_generator():
        yield {
            "type": "user",
            "message": { "role": "user", "content": "Analyze this codebase" }
        }

        await asyncio.sleep(2)

        with open("diagram.png", "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        yield {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    { "type": "text", "text": "Review this diagram" },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data
                        }
                    }
                ]
            }
        }

    options = ClaudeAgentOptions(max_turns=10, allowed_tools=["Read", "Grep"])

    async with ClaudeSDKClient(options) as client:
        await client.query(message_generator())
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)

asyncio.run(streaming_analysis())
```

## Single Message Input

One-shot queries using session state and resuming.

### When to Use

- One-shot response needed
- No image attachments required
- Stateless environment (lambda functions)

### Limitations

- ❌ Direct image attachments
- ❌ Dynamic message queueing
- ❌ Real-time interruption
- ❌ Hook integration

### TypeScript Example

```typescript
// Simple one-shot query
for await (const message of query({
  prompt: "Explain the authentication flow",
  options: { maxTurns: 1, allowedTools: ["Read", "Grep"] }
})) {
  if (message.type === "result") {
    console.log(message.result);
  }
}

// Continue conversation with session management
for await (const message of query({
  prompt: "Now explain authorization",
  options: { continue: true, maxTurns: 1 }
})) {
  if (message.type === "result") {
    console.log(message.result);
  }
}
```

### Python Example

```python
async for message in query(
    prompt="Explain the authentication flow",
    options=ClaudeAgentOptions(max_turns=1, allowed_tools=["Read", "Grep"])
):
    if isinstance(message, ResultMessage):
        print(message.result)

# Continue conversation
async for message in query(
    prompt="Now explain authorization",
    options=ClaudeAgentOptions(continue_conversation=True, max_turns=1)
):
    if isinstance(message, ResultMessage):
        print(message.result)
```
