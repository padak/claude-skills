# Agent Skills in the SDK

Extend Claude with specialized capabilities using Agent Skills.

## How Skills Work

1. **Defined as filesystem artifacts**: `SKILL.md` files in `.claude/skills/`
2. **Loaded from filesystem**: Requires `settingSources`/`setting_sources` configuration
3. **Automatically discovered**: Skill metadata discovered at startup
4. **Model-invoked**: Claude autonomously chooses when to use them
5. **Enabled via allowed_tools**: Add `"Skill"` to `allowed_tools`

## Configuration

**Important:** By default, SDK does not load filesystem settings. You must explicitly configure:

### TypeScript

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Help me process this PDF document",
  options: {
    cwd: "/path/to/project",
    settingSources: ["user", "project"],  // Load Skills from filesystem
    allowedTools: ["Skill", "Read", "Write", "Bash"]
  }
})) {
  console.log(message);
}
```

### Python

```python
from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(
    cwd="/path/to/project",
    setting_sources=["user", "project"],  # Load Skills from filesystem
    allowed_tools=["Skill", "Read", "Write", "Bash"]
)

async for message in query(
    prompt="Help me process this PDF document",
    options=options
):
    print(message)
```

## Skill Locations

- **Project Skills**: `.claude/skills/` - shared via git
- **User Skills**: `~/.claude/skills/` - personal across all projects
- **Plugin Skills**: Bundled with installed plugins

## Creating Skills

Directory structure:
```bash
.claude/skills/processing-pdfs/
└── SKILL.md
```

SKILL.md with YAML frontmatter:
```markdown
---
name: pdf-processor
description: Process PDF documents for text extraction and analysis
---

Instructions for processing PDFs...
```

## Tool Restrictions

**Note:** `allowed-tools` frontmatter in SKILL.md is NOT supported in SDK. Control tools through main `allowedTools` option:

```typescript
for await (const message of query({
  prompt: "Analyze the codebase structure",
  options: {
    settingSources: ["user", "project"],
    allowedTools: ["Skill", "Read", "Grep", "Glob"]  // Restricted toolset
  }
})) {
  console.log(message);
}
```

## Discovering Available Skills

```typescript
for await (const message of query({
  prompt: "What Skills are available?",
  options: {
    settingSources: ["user", "project"],
    allowedTools: ["Skill"]
  }
})) {
  console.log(message);
}
```

## Testing Skills

```typescript
for await (const message of query({
  prompt: "Extract text from invoice.pdf",
  options: {
    cwd: "/path/to/project",
    settingSources: ["user", "project"],
    allowedTools: ["Skill", "Read", "Bash"]
  }
})) {
  console.log(message);
}
```

## Troubleshooting

### Skills Not Found

**Check settingSources configuration:**
```typescript
// Wrong - Skills won't be loaded
const options = { allowedTools: ["Skill"] };

// Correct - Skills will be loaded
const options = {
  settingSources: ["user", "project"],
  allowedTools: ["Skill"]
};
```

**Verify filesystem location:**
```bash
ls .claude/skills/*/SKILL.md
ls ~/.claude/skills/*/SKILL.md
```

### Skill Not Being Used

1. Confirm `"Skill"` is in `allowedTools`
2. Check description includes relevant keywords
