# Subagents in the SDK

Specialized AIs orchestrated by the main agent for context management and parallelization.

## Benefits

- **Context Management**: Separate context prevents information overload
- **Parallelization**: Multiple subagents run concurrently
- **Specialized Instructions**: Tailored prompts with specific expertise
- **Tool Restrictions**: Limited tools reduce unintended actions

## Creating Subagents

### Programmatic Definition (Recommended)

```typescript
import { query } from '@anthropic-ai/claude-agent-sdk';

const result = query({
  prompt: "Review the authentication module for security issues",
  options: {
    agents: {
      'code-reviewer': {
        description: 'Expert code review specialist. Use for quality, security, and maintainability reviews.',
        prompt: `You are a code review specialist with expertise in security, performance, and best practices.

When reviewing code:
- Identify security vulnerabilities
- Check for performance issues
- Verify adherence to coding standards
- Suggest specific improvements`,
        tools: ['Read', 'Grep', 'Glob'],
        model: 'sonnet'
      },
      'test-runner': {
        description: 'Runs and analyzes test suites. Use for test execution and coverage analysis.',
        prompt: `You are a test execution specialist. Run tests and analyze results.

Focus on:
- Running test commands
- Analyzing test output
- Identifying failing tests
- Suggesting fixes`,
        tools: ['Bash', 'Read', 'Grep'],
      }
    }
  }
});
```

### AgentDefinition Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | `string` | Yes | When to use this agent |
| `prompt` | `string` | Yes | Agent's system prompt |
| `tools` | `string[]` | No | Allowed tools (inherits all if omitted) |
| `model` | `'sonnet' \| 'opus' \| 'haiku' \| 'inherit'` | No | Model override |

### Filesystem-Based Definition

Alternative: Markdown files in `.claude/agents/` or `~/.claude/agents/`:

```markdown
---
name: code-reviewer
description: Expert code review specialist.
tools: Read, Grep, Glob, Bash
---

Your subagent's system prompt...
```

## SDK Integration Patterns

### Automatic Invocation

```typescript
const result = query({
  prompt: "Optimize the database queries in the API layer",
  options: {
    agents: {
      'performance-optimizer': {
        description: 'Use PROACTIVELY when code changes might impact performance. MUST BE USED for optimization tasks.',
        prompt: 'You are a performance optimization specialist...',
        tools: ['Read', 'Edit', 'Bash', 'Grep'],
        model: 'sonnet'
      }
    }
  }
});
```

### Explicit Invocation

```typescript
const result = query({
  prompt: "Use the code-reviewer agent to check the authentication module",
  options: {
    agents: {
      'code-reviewer': {
        description: 'Expert code review specialist',
        prompt: 'You are a security-focused code reviewer...',
        tools: ['Read', 'Grep', 'Glob']
      }
    }
  }
});
```

### Dynamic Agent Configuration

```typescript
function createSecurityAgent(securityLevel: 'basic' | 'strict'): AgentDefinition {
  return {
    description: 'Security code reviewer',
    prompt: `You are a ${securityLevel === 'strict' ? 'strict' : 'balanced'} security reviewer...`,
    tools: ['Read', 'Grep', 'Glob'],
    model: securityLevel === 'strict' ? 'opus' : 'sonnet'
  };
}

const result = query({
  prompt: "Review this PR for security issues",
  options: {
    agents: {
      'security-reviewer': createSecurityAgent('strict')
    }
  }
});
```

## Tool Restrictions

### Common Tool Combinations

**Read-only agents (analysis, review):**
```typescript
tools: ['Read', 'Grep', 'Glob']
```

**Test execution agents:**
```typescript
tools: ['Bash', 'Read', 'Grep']
```

**Code modification agents:**
```typescript
tools: ['Read', 'Edit', 'Write', 'Grep', 'Glob']
```

### Read-Only Analysis Example

```typescript
const result = query({
  prompt: "Analyze the architecture of this codebase",
  options: {
    agents: {
      'code-analyzer': {
        description: 'Static code analysis and architecture review',
        prompt: `You are a code architecture analyst. Analyze code structure,
identify patterns, and suggest improvements without making changes.`,
        tools: ['Read', 'Grep', 'Glob']  // No write permissions
      }
    }
  }
});
```
