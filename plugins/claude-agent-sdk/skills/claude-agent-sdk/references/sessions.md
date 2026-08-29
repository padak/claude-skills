# Session Management

Handle conversation state and resumption in the Claude Agent SDK.

## How Sessions Work

The SDK creates a session and returns a session ID in the initial system message.

### Getting the Session ID

**TypeScript:**
```typescript
let sessionId: string | undefined;

const response = query({
  prompt: "Help me build a web application",
  options: { model: "claude-sonnet-4-5" }
});

for await (const message of response) {
  if (message.type === 'system' && message.subtype === 'init') {
    sessionId = message.session_id;
    console.log(`Session started: ${sessionId}`);
  }
}
```

**Python:**
```python
session_id = None

async for message in query(
    prompt="Help me build a web application",
    options=ClaudeAgentOptions(model="claude-sonnet-4-5")
):
    if hasattr(message, 'subtype') and message.subtype == 'init':
        session_id = message.data.get('session_id')
        print(f"Session started: {session_id}")
```

## Resuming Sessions

Use the `resume` option to continue a previous conversation:

**TypeScript:**
```typescript
const response = query({
  prompt: "Continue implementing the authentication system",
  options: {
    resume: "session-xyz",
    model: "claude-sonnet-4-5",
    allowedTools: ["Read", "Edit", "Write", "Glob", "Grep", "Bash"]
  }
});

for await (const message of response) {
  console.log(message);
}
```

**Python:**
```python
async for message in query(
    prompt="Continue implementing the authentication system",
    options=ClaudeAgentOptions(
        resume="session-xyz",
        model="claude-sonnet-4-5",
        allowed_tools=["Read", "Edit", "Write", "Glob", "Grep", "Bash"]
    )
):
    print(message)
```

## Forking Sessions

Create a new branch from a resumed session instead of continuing the original.

### When to Fork

- Explore different approaches from the same starting point
- Create multiple conversation branches
- Test changes without affecting original session
- Maintain separate conversation paths for experiments

### Forking vs Continuing

| Behavior | `forkSession: false` (default) | `forkSession: true` |
|----------|-------------------------------|---------------------|
| Session ID | Same as original | New session ID |
| History | Appends to original | Creates new branch |
| Original Session | Modified | Preserved |
| Use Case | Continue linear conversation | Branch for alternatives |

### Example

**TypeScript:**
```typescript
// Original session
let sessionId: string | undefined;

for await (const message of query({
  prompt: "Help me design a REST API",
  options: { model: "claude-sonnet-4-5" }
})) {
  if (message.type === 'system' && message.subtype === 'init') {
    sessionId = message.session_id;
  }
}

// Fork to try different approach
for await (const message of query({
  prompt: "Now let's redesign this as a GraphQL API",
  options: {
    resume: sessionId,
    forkSession: true,  // New session ID
    model: "claude-sonnet-4-5"
  }
})) {
  if (message.type === 'system' && message.subtype === 'init') {
    console.log(`Forked session: ${message.session_id}`);
  }
}

// Original session unchanged - can still resume it
for await (const message of query({
  prompt: "Add authentication to the REST API",
  options: {
    resume: sessionId,
    forkSession: false,  // Continue original
    model: "claude-sonnet-4-5"
  }
})) {
  console.log(message);
}
```

**Python:**
```python
# Fork the session
async for message in query(
    prompt="Now let's redesign this as a GraphQL API",
    options=ClaudeAgentOptions(
        resume=session_id,
        fork_session=True,
        model="claude-sonnet-4-5"
    )
):
    if hasattr(message, 'subtype') and message.subtype == 'init':
        forked_id = message.data.get('session_id')
        print(f"Forked session: {forked_id}")
```
