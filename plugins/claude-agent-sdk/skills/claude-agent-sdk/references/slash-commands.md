# Slash Commands in the SDK

Control Claude Code sessions with special commands.

## Discovering Available Commands

```typescript
for await (const message of query({
  prompt: "Hello Claude",
  options: { maxTurns: 1 }
})) {
  if (message.type === "system" && message.subtype === "init") {
    console.log("Available commands:", message.slash_commands);
    // Example: ["/compact", "/clear", "/help"]
  }
}
```

## Sending Slash Commands

```typescript
for await (const message of query({
  prompt: "/compact",
  options: { maxTurns: 1 }
})) {
  if (message.type === "result") {
    console.log("Command executed:", message.result);
  }
}
```

## Common Commands

### `/compact` - Compact Conversation History

```typescript
for await (const message of query({
  prompt: "/compact",
  options: { maxTurns: 1 }
})) {
  if (message.type === "system" && message.subtype === "compact_boundary") {
    console.log("Pre-compaction tokens:", message.compact_metadata.pre_tokens);
  }
}
```

### `/clear` - Clear Conversation

```typescript
for await (const message of query({
  prompt: "/clear",
  options: { maxTurns: 1 }
})) {
  if (message.type === "system" && message.subtype === "init") {
    console.log("New session:", message.session_id);
  }
}
```

## Creating Custom Commands

### File Locations

- **Project commands**: `.claude/commands/` - current project only
- **Personal commands**: `~/.claude/commands/` - all projects

### Basic Example

Create `.claude/commands/refactor.md`:

```markdown
Refactor the selected code to improve readability and maintainability.
Focus on clean code principles and best practices.
```

This creates the `/refactor` command.

### With Frontmatter

Create `.claude/commands/security-check.md`:

```markdown
---
allowed-tools: Read, Grep, Glob
description: Run security vulnerability scan
model: claude-sonnet-4-5-20250929
---

Analyze the codebase for security vulnerabilities including:
- SQL injection risks
- XSS vulnerabilities
- Exposed credentials
- Insecure configurations
```

### Arguments and Placeholders

Create `.claude/commands/fix-issue.md`:

```markdown
---
argument-hint: [issue-number] [priority]
description: Fix a GitHub issue
---

Fix issue #$1 with priority $2.
Check the issue description and implement the necessary changes.
```

Usage:
```typescript
for await (const message of query({
  prompt: "/fix-issue 123 high",
  options: { maxTurns: 5 }
})) {
  // $1="123", $2="high"
}
```

### Bash Command Execution

```markdown
---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
description: Create a git commit
---

## Context
- Current status: !`git status`
- Current diff: !`git diff HEAD`

## Task
Create a git commit with appropriate message.
```

### File References

```markdown
---
description: Review configuration files
---

Review the following configuration files:
- Package config: @package.json
- TypeScript config: @tsconfig.json

Check for security issues and misconfigurations.
```

## Using Custom Commands

```typescript
for await (const message of query({
  prompt: "/refactor src/auth/login.ts",
  options: { maxTurns: 3 }
})) {
  if (message.type === "assistant") {
    console.log("Suggestions:", message.message);
  }
}
```

## Organization with Namespacing

```bash
.claude/commands/
├── frontend/
│   ├── component.md
│   └── style-check.md
├── backend/
│   ├── api-test.md
│   └── db-migrate.md
└── review.md
```

Subdirectory appears in description but doesn't affect command name.
