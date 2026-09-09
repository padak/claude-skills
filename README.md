# Claude Code Kit

Personal [Claude Code](https://docs.anthropic.com/en/docs/claude-code) setup used by petr@keboola.com. Use at your own risk.

A plugin marketplace with eight skills, plus the permission ruleset and global instructions I actually work with daily.

## Install

Add the marketplace once:

```bash
/plugin marketplace add padak/claude-code-kit
```

Then install only the plugins you want:

```bash
/plugin install trip-master-plan@claude-code-kit
```

Each skill is its own plugin, so nothing arrives that you did not ask for. Browse and install interactively with `/plugin`, and update everything later with `/plugin marketplace update claude-code-kit`.

## Plugins

| Plugin | Trigger | What it does |
|--------|---------|--------------|
| `claude-agent-sdk` | `/claude-agent-sdk` | Reference for building apps with the Claude Agent SDK (TypeScript/Python): `query()`, `ClaudeSDKClient`, custom MCP tools, subagents, sessions, permissions, hooks, structured outputs, cost tracking, hosting |
| `e2b` | `/e2b` | Execute code in secure isolated E2B cloud sandboxes: lifecycle, code interpreters, running coding agents inside sandboxes, MCP gateway, storage mounting, metrics |
| `keboola-data-app` | `/keboola-data-app` | Streamlit data apps for the Keboola platform: Storage Files API, OIDC auth via proxy headers, multi-step wizard patterns |
| `polymarket` | `/polymarket` | Trading bots on Polymarket prediction markets: py-clob-client SDK, WebSocket streaming, order placement, whale tracking, arbitrage detection |
| `post-merge` | `/post-merge` | After merging a PR: sync main, remove the merged worktree and branch, watch CI/CD. Works from a plain checkout or from a `.claude/worktrees` session |
| `second-opinion` | `/second-opinion` | External review via the Codex, Antigravity (`agy`) or Claude Code CLIs — one-shot question, multi-round consultation, diff review, or multi-model consensus when a decision is worth the extra round trip |
| `swarm` | `/swarm` | Multi-agent implementation of a phased plan: a Tech Lead spawns Developer agents in isolated git worktrees per phase, reviews their PRs, handles retries and escalation |
| `trip-master-plan` | `/trip-master-plan` | End-to-end trip planner. Interviews you, date-verifies attractions and local events, then compiles a versioned HTML artifact: route alternatives, SVG maps built from Natural Earth geodata whose routes follow real roads, day cards with drive times, Wikimedia photos with license credits, a weather widget, and copy-to-clipboard research prompts. Ships a `trip-fact-checker` subagent that audits the result adversarially |

`trip-master-plan` is the only plugin with runtime dependencies: `python3` (stdlib only) and `curl`. On first use it downloads ~85 MB of Natural Earth GeoJSON into a `geo/` directory in your working folder; the geodata is not vendored here.

### Subagents

`trip-master-plan` ships `trip-fact-checker` — a read-only adversarial verifier (`Read`, `Grep`, `WebSearch`, `WebFetch`) spawned one instance per section, in parallel. It reports only problems, each with an exact quote, what is wrong, a drop-in correction and a source URL. Running it as a subagent rather than inline keeps a long audit out of the main session's context.

## Configuration

Plugins cannot install user-level configuration, so `.claude/settings.json` and `CLAUDE.md` are copied by hand:

```bash
git clone https://github.com/padak/claude-code-kit.git
cd claude-code-kit
cp .claude/settings.json ~/.claude/settings.json
cp CLAUDE.md ~/.claude/CLAUDE.md
```

Read both before overwriting yours — they are opinionated.

### Why this `settings.json`

Permissions are split by **how reversible an action is**, not by how dangerous it sounds:

- **allow** — things that cannot break anything: `git status`, `ls`, `grep`, reading files, running tests, `python`, build tools. Auto-approving these is where the time saving actually comes from; they are also the calls Claude makes most often.
- **ask** — things that destroy work or are hard to undo: `rm`, `git push --force`, `git reset --hard`, `git clean`, package installs, `docker`, `kubectl`, and edits to lockfiles and `package.json`. Not blocked, just deliberate.
- **deny** — reading or writing secrets: `.env` files, SSH keys, `.aws/credentials`, certificates, keystores, anything matching `*token*`, `*password*`, `*credentials*`. This is the rule set worth copying even if you take nothing else. It is not about trust; it removes an entire class of accident where a secret gets pulled into the transcript and from there into a commit, a bug report or a PR description.

Two hooks:

- **PostToolUse** runs `py_compile` on edited Python and `tsc --noEmit` on edited TypeScript. Catching a syntax error at the moment of the edit beats discovering it ten steps later, when the fix means unwinding everything in between.
- **Notification** fires a macOS notification when Claude needs you — worth it once tasks run long enough that you switch windows.

### Why this `CLAUDE.md`

Most of it exists to close off shortcuts that are locally convenient and globally expensive:

- **No mocks, no stubs, no `TODO: implement later`.** If something is in the plan it gets built, or Claude asks. Left unstated, a blocked step quietly becomes a fake one that passes tests and fails in production.
- **No hardcoded values, no silent defaults.** Config lives in config files; a missing required variable fails loudly at startup instead of falling back to an invented value. A wrong default is much harder to debug than a crash.
- **Parallel subagents for independent work** — mandatory, not a suggestion, because the default instinct is to do things one at a time.
- **Research before implementing unfamiliar tech**, via Perplexity MCP, with explicit cost tiers so the cheap tool is the default and the expensive one is deliberate.
- **Czech in conversation, English in files.** Separating the language you think in from the language the artifact ships in keeps the codebase readable to everyone else.
- **Clean commits** — no `Co-Authored-By`, no generated-with footers.

### `.zshrc`

```bash
alias cc="claude --allow-dangerously-skip-permissions --chrome"
```

I run Claude as `cc` in full YOLO mode — all permissions bypassed, Chrome MCP included. That is how I work daily; if you want the guardrails above, use `claude` directly. Also included: auto-activation of `.venv` if present, and a `gtimeout` alias for macOS.

## Customization

- **Personal overrides** go in `~/.claude/settings.local.json`, which git ignores
- **Language** — set `"language": "Czech"` (or yours) in `settings.local.json`
- **Add a skill to a plugin** — create a directory with a `SKILL.md` under `plugins/<plugin>/skills/`
- **Add a subagent** — drop a Markdown file with `name` / `description` / `tools` front matter into `plugins/<plugin>/agents/`
- **Add a new plugin** — create `plugins/<name>/.claude-plugin/plugin.json` and list it in `.claude-plugin/marketplace.json`
- **Develop against a local checkout** — `/plugin marketplace add ./claude-code-kit` points at your working copy instead of GitHub

## License

MIT
