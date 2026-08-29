# Todo Lists

Track and display todos using the Claude Agent SDK.

## Todo Lifecycle

1. **Created** as `pending` when tasks identified
2. **Activated** to `in_progress` when work begins
3. **Completed** when task finishes
4. **Removed** when all tasks in group completed

## When Todos Are Used

SDK automatically creates todos for:
- Complex multi-step tasks (3+ distinct actions)
- User-provided task lists (multiple items)
- Non-trivial operations benefiting from tracking
- Explicit requests for todo organization

## Monitoring Todo Changes

### TypeScript

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Optimize my React app performance and track progress with todos",
  options: { maxTurns: 15 }
})) {
  if (message.type === "assistant") {
    for (const block of message.message.content) {
      if (block.type === "tool_use" && block.name === "TodoWrite") {
        const todos = block.input.todos;

        console.log("Todo Status Update:");
        todos.forEach((todo, index) => {
          const status = todo.status === "completed" ? "✅" :
                        todo.status === "in_progress" ? "🔧" : "❌";
          console.log(`${index + 1}. ${status} ${todo.content}`);
        });
      }
    }
  }
}
```

### Python

```python
from claude_agent_sdk import query, AssistantMessage, ToolUseBlock

async for message in query(
    prompt="Optimize my React app performance and track progress with todos",
    options={"max_turns": 15}
):
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, ToolUseBlock) and block.name == "TodoWrite":
                todos = block.input["todos"]

                print("Todo Status Update:")
                for i, todo in enumerate(todos):
                    status = "✅" if todo["status"] == "completed" else \
                            "🔧" if todo["status"] == "in_progress" else "❌"
                    print(f"{i + 1}. {status} {todo['content']}")
```

## Real-time Progress Display

### TypeScript

```typescript
class TodoTracker {
  private todos: any[] = [];

  displayProgress() {
    if (this.todos.length === 0) return;

    const completed = this.todos.filter(t => t.status === "completed").length;
    const inProgress = this.todos.filter(t => t.status === "in_progress").length;
    const total = this.todos.length;

    console.log(`\nProgress: ${completed}/${total} completed`);
    console.log(`Currently working on: ${inProgress} task(s)\n`);

    this.todos.forEach((todo, index) => {
      const icon = todo.status === "completed" ? "✅" :
                  todo.status === "in_progress" ? "🔧" : "❌";
      const text = todo.status === "in_progress" ? todo.activeForm : todo.content;
      console.log(`${index + 1}. ${icon} ${text}`);
    });
  }

  async trackQuery(prompt: string) {
    for await (const message of query({ prompt, options: { maxTurns: 20 } })) {
      if (message.type === "assistant") {
        for (const block of message.message.content) {
          if (block.type === "tool_use" && block.name === "TodoWrite") {
            this.todos = block.input.todos;
            this.displayProgress();
          }
        }
      }
    }
  }
}

const tracker = new TodoTracker();
await tracker.trackQuery("Build a complete authentication system with todos");
```

### Python

```python
class TodoTracker:
    def __init__(self):
        self.todos = []

    def display_progress(self):
        if not self.todos:
            return

        completed = len([t for t in self.todos if t["status"] == "completed"])
        in_progress = len([t for t in self.todos if t["status"] == "in_progress"])
        total = len(self.todos)

        print(f"\nProgress: {completed}/{total} completed")
        print(f"Currently working on: {in_progress} task(s)\n")

        for i, todo in enumerate(self.todos):
            icon = "✅" if todo["status"] == "completed" else \
                  "🔧" if todo["status"] == "in_progress" else "❌"
            text = todo["activeForm"] if todo["status"] == "in_progress" else todo["content"]
            print(f"{i + 1}. {icon} {text}")

    async def track_query(self, prompt):
        async for message in query(prompt=prompt, options={"max_turns": 20}):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, ToolUseBlock) and block.name == "TodoWrite":
                        self.todos = block.input["todos"]
                        self.display_progress()

tracker = TodoTracker()
await tracker.track_query("Build a complete authentication system with todos")
```
