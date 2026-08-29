# Tracking Costs and Usage

Track token usage for billing in the Claude Agent SDK.

## Key Concepts

1. **Steps**: Single request/response pair
2. **Messages**: Individual messages within a step
3. **Usage**: Token consumption attached to assistant messages

## Usage Reporting Rules

### Same ID = Same Usage

All messages with the same `id` field report identical usage. When Claude sends multiple messages in the same turn, they share the same message ID and usage data.

### Charge Once Per Step

Only charge users once per step, not for each individual message.

### Result Message Contains Cumulative Usage

Final `result` message contains total usage from all steps.

## Implementation

### TypeScript

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

class CostTracker {
  private processedMessageIds = new Set<string>();
  private stepUsages: Array<any> = [];

  async trackConversation(prompt: string) {
    const result = await query({
      prompt,
      options: {
        onMessage: (message) => this.processMessage(message)
      }
    });

    return {
      result,
      stepUsages: this.stepUsages,
      totalCost: result.usage?.total_cost_usd || 0
    };
  }

  private processMessage(message: any) {
    if (message.type !== 'assistant' || !message.usage) return;
    if (this.processedMessageIds.has(message.id)) return;

    this.processedMessageIds.add(message.id);
    this.stepUsages.push({
      messageId: message.id,
      timestamp: new Date().toISOString(),
      usage: message.usage,
      costUSD: this.calculateCost(message.usage)
    });
  }

  private calculateCost(usage: any): number {
    const inputCost = usage.input_tokens * 0.00003;
    const outputCost = usage.output_tokens * 0.00015;
    const cacheReadCost = (usage.cache_read_input_tokens || 0) * 0.0000075;
    return inputCost + outputCost + cacheReadCost;
  }
}
```

### Python

```python
from claude_agent_sdk import query, AssistantMessage, ResultMessage
from datetime import datetime

class CostTracker:
    def __init__(self):
        self.processed_message_ids = set()
        self.step_usages = []

    async def track_conversation(self, prompt):
        result = None

        async for message in query(prompt=prompt):
            self.process_message(message)
            if isinstance(message, ResultMessage):
                result = message

        return {
            "result": result,
            "step_usages": self.step_usages,
            "total_cost": result.total_cost_usd if result else 0
        }

    def process_message(self, message):
        if not isinstance(message, AssistantMessage) or not hasattr(message, 'usage'):
            return

        message_id = getattr(message, 'id', None)
        if not message_id or message_id in self.processed_message_ids:
            return

        self.processed_message_ids.add(message_id)
        self.step_usages.append({
            "message_id": message_id,
            "timestamp": datetime.now().isoformat(),
            "usage": message.usage,
            "cost_usd": self.calculate_cost(message.usage)
        })

    def calculate_cost(self, usage):
        input_cost = usage.get("input_tokens", 0) * 0.00003
        output_cost = usage.get("output_tokens", 0) * 0.00015
        cache_read_cost = usage.get("cache_read_input_tokens", 0) * 0.0000075
        return input_cost + output_cost + cache_read_cost
```

## Usage Fields Reference

| Field | Description |
|-------|-------------|
| `input_tokens` | Base input tokens processed |
| `output_tokens` | Tokens generated in response |
| `cache_creation_input_tokens` | Tokens used to create cache |
| `cache_read_input_tokens` | Tokens read from cache |
| `service_tier` | Service tier used |
| `total_cost_usd` | Total cost in USD (result message only) |

## Best Practices

1. **Use Message IDs for Deduplication**: Track processed IDs to avoid double-charging
2. **Monitor the Result Message**: Contains authoritative cumulative usage
3. **Implement Logging**: Log all usage data for auditing
4. **Handle Failures Gracefully**: Track partial usage even if conversation fails
5. **Consider Streaming**: Accumulate usage as messages arrive

## Billing Dashboard Example

```typescript
class BillingAggregator {
  private userUsage = new Map<string, {
    totalTokens: number;
    totalCost: number;
    conversations: number;
  }>();

  async processUserRequest(userId: string, prompt: string) {
    const tracker = new CostTracker();
    const { result, stepUsages, totalCost } = await tracker.trackConversation(prompt);

    const current = this.userUsage.get(userId) || {
      totalTokens: 0, totalCost: 0, conversations: 0
    };

    const totalTokens = stepUsages.reduce((sum, step) =>
      sum + step.usage.input_tokens + step.usage.output_tokens, 0
    );

    this.userUsage.set(userId, {
      totalTokens: current.totalTokens + totalTokens,
      totalCost: current.totalCost + totalCost,
      conversations: current.conversations + 1
    });

    return result;
  }
}
```
