# Claude Code Boilerplate

Personal [Claude Code](https://docs.anthropic.com/en/docs/claude-code) setup used by petr@keboola.com. Use at your own risk.

Fork this repo and you get a pre-configured Claude Code environment with skills, subagents, permissions, hooks, and shell aliases.

## What's Inside

### `.claude/settings.json` - Team Settings

Pre-configured permissions so Claude doesn't ask you every time it runs `git status` or `ls`:

- **allow** - Auto-approved: git operations, python/node/build tools, file exploration, web search, Playwright, Perplexity, Atlassian MCP, gcloud/terraform/aws/docker
- **deny** - Hard-blocked: reading `.env`, credentials, SSH keys, certificates, secrets (69 rules)
- **ask** - Requires confirmation: `rm`, `git push --force`, `pip install`, `docker`, `kubectl`, package.json edits

Hooks that run automatically:
- **PostToolUse** - Auto-compiles Python (`py_compile`) and TypeScript (`tsc --noEmit`) after every file edit - catches syntax errors immediately
- **Notification** - macOS notification when Claude needs your attention (useful for long-running tasks)

### `.claude/skills/` - Slash Commands & Knowledge

| Skill | Trigger | What it does |
|-------|---------|--------------|
| **claude-agent-sdk** | `/claude-agent-sdk` | Reference for building apps with Claude Agent SDK (TypeScript/Python) |
| **e2b** | `/e2b` | Execute code in secure E2B cloud sandboxes with MCP gateway |
| **keboola-data-app** | `/keboola-data-app` | Streamlit + Google Sheets patterns for Keboola data apps |
| **polymarket** | `/polymarket` | Build trading bots on Polymarket (py-clob-client SDK, WebSocket, order placement) |
| **post-merge** | `/post-merge` | After merging a PR: sync main, remove the merged worktree/branch, watch CI/CD. Worktree-aware (works from `.claude/worktrees` sessions) |
| **second-opinion** | `/second-opinion` | External AI review via Codex (GPT-5.6 Sol/Terra/Luna), Gemini, or Claude Code CLI - single provider or multi-model consensus |
| **swarm** | `/swarm` | Multi-agent implementation: Tech Lead spawns Developer agents in isolated git worktrees per phase, reviews PRs, handles retries |
| **trip-master-plan** | `/trip-master-plan` | End-to-end trip planner: interviews you, date-verifies attractions & local events, then compiles a versioned HTML artifact with route alternatives, real-geodata SVG maps (routes follow actual roads), day cards with drive times, Wikimedia photos with credits, weather map with scheduled auto-refresh, and copy-to-clipboard research prompts. Ships a `trip-fact-checker` agent for the adversarial audit phase |

Removed in the 2026-08 facelift: **Browser** (Playwright-based, superseded by Claude Code's built-in browser and the Claude Chrome MCP) and **skill-creator** (superseded by the official `anthropic-skills:skill-creator` plugin).

Some skills need local tooling: **trip-master-plan** shells out to `python3` (stdlib only) and `curl` — its `scripts/fetch_geo.sh` downloads ~85 MB of Natural Earth GeoJSON into a `geo/` directory in your working folder on first use. The geodata is not vendored in this repo.

### `.claude/agents/` - Subagents

Subagent definitions that skills (or you) can spawn in parallel. Each runs in its own clean context with a restricted toolset, so a long audit does not flood the main session.

| Agent | Spawned by | What it does |
|-------|-----------|--------------|
| **trip-fact-checker** | `trip-master-plan` (Phase 7), or on request | Adversarial "arbitr" for one section of a travel plan. Verifies dates, superlatives, measurements, prices and historical claims against primary sources; reports only problems, each with an exact quote, what is wrong, a drop-in corrected phrasing and a source URL. Read-only (`Read`, `Grep`, `WebSearch`, `WebFetch`) |

### `CLAUDE.md` - Global Instructions

Rules that shape how Claude behaves in every project:

- Communicates in Czech, writes code in English
- Uses Perplexity MCP for research before implementing unknown tech
- Parallel sub-agents for independent tasks (mandatory)
- No mock implementations, no TODO stubs, no hardcoded values
- Fail-fast on missing config (no silent defaults)
- Structured JSON logging for all server apps
- Clean commits (no Co-Authored-By, no Generated-with footer)

### `.zshrc` - Shell Aliases

```bash
alias cc="claude --allow-dangerously-skip-permissions --chrome"
```

I run Claude as `cc` in full YOLO mode - all permissions bypassed, no confirmation prompts. Chrome MCP included for browser automation. This is how I work daily; if you prefer guardrails, use `claude` directly instead.

Also: auto-activates `.venv` if present, `gtimeout` alias for macOS.

## Installation

### Option A: Fork and clone (recommended)

```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR_USERNAME/claude-code-kit.git
cd claude-code-kit

# Copy what you need to your global config:
cp .claude/settings.json ~/.claude/settings.json
cp CLAUDE.md ~/.claude/CLAUDE.md
cp -r .claude/skills/* ~/.claude/skills/
mkdir -p ~/.claude/agents && cp .claude/agents/* ~/.claude/agents/

# Optional: add shell aliases
cat .zshrc >> ~/.zshrc && source ~/.zshrc
```

### Option B: Install a single skill

Skills are self-contained directories - you can cherry-pick one without taking the rest:

```bash
# Example: just the trip planner and the agent it spawns
cp -r .claude/skills/trip-master-plan ~/.claude/skills/
mkdir -p ~/.claude/agents && cp .claude/agents/trip-fact-checker.md ~/.claude/agents/
```

Restart Claude Code, then confirm it registered - `/trip-master-plan` should appear in the slash-command list.

### Option C: Just tell Claude

```
Clone https://github.com/padak/claude-code-kit and copy .claude/settings.json
to ~/.claude/settings.json, CLAUDE.md to ~/.claude/CLAUDE.md, all skills from
.claude/skills/ to ~/.claude/skills/, and all agents from .claude/agents/ to
~/.claude/agents/
```

## Customization

- **Personal overrides** go in `~/.claude/settings.local.json` (not tracked by git)
- **Language** - set `"language": "Czech"` (or your language) in settings.local.json
- **Remove skills** you don't need - just delete the directory from `.claude/skills/`
- **Add your own skills** - create a new directory with `SKILL.md` in `.claude/skills/`
- **Add your own subagents** - drop a Markdown file with `name` / `description` / `tools` front matter into `.claude/agents/`
- **Project-scoped install** - copy into a project's own `.claude/skills/` and `.claude/agents/` instead of `~/.claude/` to keep a skill scoped to one repo

## License

MIT
