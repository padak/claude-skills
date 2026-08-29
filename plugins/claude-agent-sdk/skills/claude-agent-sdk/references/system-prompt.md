# Modifying System Prompts

Customize Claude's behavior with system prompts.

## Default Behavior

The Agent SDK uses an **empty system prompt** by default. To use Claude Code's system prompt, specify:
- TypeScript: `systemPrompt: { preset: "claude_code" }`
- Python: `system_prompt="claude_code"`

## Methods of Modification

### Method 1: CLAUDE.md Files

Project-specific context and instructions, automatically read by SDK.

**Locations:**
- Project-level: `CLAUDE.md` or `.claude/CLAUDE.md`
- User-level: `~/.claude/CLAUDE.md`

**Important:** SDK only reads CLAUDE.md when `settingSources`/`setting_sources` is configured.

**Example CLAUDE.md:**
```markdown
# Project Guidelines

## Code Style
- Use TypeScript strict mode
- Prefer functional components in React

## Commands
- Build: `npm run build`
- Dev server: `npm run dev`
```

**Usage:**
```typescript
for await (const message of query({
  prompt: "Add a new React component",
  options: {
    systemPrompt: { type: "preset", preset: "claude_code" },
    settingSources: ["project"]  // Required to load CLAUDE.md
  }
})) {
  // Claude has access to project guidelines
}
```

### Method 2: Output Styles

Saved configurations modifying Claude's system prompt.

**Creating:**
```typescript
async function createOutputStyle(name, description, prompt) {
  const outputStylesDir = join(homedir(), ".claude", "output-styles");
  await mkdir(outputStylesDir, { recursive: true });

  const content = `---
name: ${name}
description: ${description}
---

${prompt}`;

  const filePath = join(outputStylesDir, `${name.toLowerCase().replace(/\s+/g, "-")}.md`);
  await writeFile(filePath, content, "utf-8");
}

await createOutputStyle(
  "Code Reviewer",
  "Thorough code review assistant",
  `You are an expert code reviewer.
Check for bugs, security issues, and suggest improvements.`
);
```

**Note:** Loaded when `settingSources` includes `'user'` or `'project'`.

### Method 3: systemPrompt with Append

Add custom instructions while preserving Claude Code's functionality:

```typescript
for await (const message of query({
  prompt: "Help me write a Python function",
  options: {
    systemPrompt: {
      type: "preset",
      preset: "claude_code",
      append: "Always include detailed docstrings and type hints in Python code."
    }
  }
})) {
  console.log(message);
}
```

```python
async for message in query(
    prompt="Help me write a Python function",
    options=ClaudeAgentOptions(
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": "Always include detailed docstrings and type hints."
        }
    )
):
    print(message)
```

### Method 4: Custom System Prompt

Replace the default entirely:

```typescript
const customPrompt = `You are a Python coding specialist.
Follow these guidelines:
- Write clean, well-documented code
- Use type hints for all functions
- Include comprehensive docstrings`;

for await (const message of query({
  prompt: "Create a data processing pipeline",
  options: { systemPrompt: customPrompt }
})) {
  console.log(message);
}
```

## Comparison

| Feature | CLAUDE.md | Output Styles | Append | Custom |
|---------|-----------|---------------|--------|--------|
| Persistence | Per-project | Saved files | Session | Session |
| Default tools | Preserved | Preserved | Preserved | Lost |
| Built-in safety | Maintained | Maintained | Maintained | Must add |
| Customization | Additions | Replace | Additions | Complete |
| Version control | With project | Yes | With code | With code |

## When to Use Each

**CLAUDE.md:**
- Project-specific standards
- Team-shared context
- Common commands
- Version-controlled instructions

**Output Styles:**
- Persistent behavior changes
- Team-shared configurations
- Specialized assistants

**systemPrompt with Append:**
- Adding coding standards
- Customizing output formatting
- Adding domain knowledge
- Enhancing default behavior

**Custom systemPrompt:**
- Complete control over behavior
- Specialized single-session tasks
- Testing new prompts
- When default tools aren't needed
