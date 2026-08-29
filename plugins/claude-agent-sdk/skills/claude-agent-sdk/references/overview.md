# Claude Agent SDK Overview

## Installation

```bash
# TypeScript
npm install @anthropic-ai/claude-agent-sdk

# Python
pip install claude-agent-sdk
```

## Core Features

- **Context Management**: Automatic compaction and context management
- **Rich Tool Ecosystem**: File operations, code execution, web search, MCP extensibility
- **Advanced Permissions**: Fine-grained control over agent capabilities
- **Production Essentials**: Built-in error handling, session management, monitoring
- **Optimized Claude Integration**: Automatic prompt caching and performance optimizations

## Authentication

Set `ANTHROPIC_API_KEY` environment variable or configure:
- **Amazon Bedrock**: `CLAUDE_CODE_USE_BEDROCK=1`
- **Google Vertex AI**: `CLAUDE_CODE_USE_VERTEX=1`

## Full Feature Support

- **Subagents**: Markdown files in `.claude/agents/`
- **Agent Skills**: `SKILL.md` files in `.claude/skills/`
- **Hooks**: Custom commands in `.claude/settings.json`
- **Slash Commands**: Markdown files in `.claude/commands/`
- **Plugins**: Custom plugins via `plugins` option
- **Memory (CLAUDE.md)**: Project context files

## SDK Options

| SDK | Use Case |
|-----|----------|
| TypeScript | Node.js and web applications |
| Python | Python applications and data science |

## Core Concepts

### System Prompts
Define agent's role, expertise, and behavior.

### Tool Permissions
- `allowedTools` - Explicitly allow specific tools
- `disallowedTools` - Block specific tools
- `permissionMode` - Set overall permission strategy

### Model Context Protocol (MCP)
Extend agents with custom tools and integrations through MCP servers.
