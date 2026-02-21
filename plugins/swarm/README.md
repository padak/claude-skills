# Swarm Plugin for Claude Code

Multi-agent implementation orchestrator using Tech Lead + DevAgent pattern with git worktrees for parallel execution.

## What It Does

Swarm takes a phased implementation plan and executes it using parallel AI agents:

1. **Tech Lead** (orchestrator) parses the plan, builds a dependency graph, creates git worktrees, and spawns DevAgents
2. **DevAgents** (workers) implement code in isolated branches, run tests, and create PRs
3. **Tech Lead** reviews each PR rigorously — merges on approval, creates issues and spawns fix agents on rejection
4. Independent phases run **in parallel** via git worktrees — no conflicts, significant time savings

## Requirements

- Claude Code 1.0.33+
- git with worktree support
- gh (GitHub CLI) — authenticated (`gh auth login`)
- make
- Python 3.10+
- A GitHub remote

## Installation

### From a marketplace (recommended)

If the plugin is published in a marketplace:

```bash
/plugin marketplace add owner/repo
/plugin install swarm@marketplace-name
```

### From a local clone

Clone the repo and add it as a local marketplace:

```bash
git clone https://github.com/owner/swarm-plugin.git
```

Then in Claude Code:

```
/plugin marketplace add ./swarm-plugin
/plugin install swarm@swarm-plugins
```

### For development and testing

Load the plugin directly without installing:

```bash
claude --plugin-dir ./swarm-plugin
```

This is useful for testing changes before publishing. Restart Claude Code to pick up edits.

## Usage

### Initialize a project (once)

```
/swarm:swarm init
```

This will:
- Validate your CLAUDE.md has required sections (stack, testing, project structure, etc.)
- Reorganize directories: repo moves to `main/`, worktrees go to `worktrees/`
- Create a Makefile with build/test/worktree targets
- Create `.worktree-setup.sh` for dependency installation in worktrees
- Verify the full cycle works

### Run a plan

```
/swarm:swarm docs/PLAN.md
```

Or with the default plan (`docs/PLAN.md`):

```
/swarm:swarm
```

## Plan Format

Plans use markdown with phase markers:

```markdown
<!-- PHASE:1 -->
## Phase 1: Feature Name

### Branch
`phase-1-feature-name`

### Scope
What to implement.

### Files to Create/Modify
- `src/path/to/file.py` — description

### Acceptance Criteria
- [ ] Observable, verifiable outcome

### Tests Required
- `tests/test_file.py::test_name` — what it verifies
<!-- /PHASE:1 -->

<!-- PHASE:2 DEPENDS:1 -->
## Phase 2: Another Feature
...
<!-- /PHASE:2 -->
```

Phases without `DEPENDS` run in parallel. See [Plan Writing Guide](skills/swarm/references/plan-writing-guide.md) for tips on maximizing parallelism.

## Plugin Components

| Component | Description |
|-----------|-------------|
| `skills/swarm/` | Main orchestration skill (Tech Lead instructions) |
| `skills/swarm-developer-guide/` | DevAgent instructions, preloaded via agent config |
| `agents/dev-agent.md` | Custom DevAgent — Sonnet model, maxTurns=50, bypassPermissions |
| `scripts/swarm.py` | CLI tool for plan parsing, status tracking, dependency graphs |

## Reference Files

- [User Guide](skills/swarm/references/user-guide.md) — getting started, FAQ
- [Plan Writing Guide](skills/swarm/references/plan-writing-guide.md) — maximizing parallelism
- [Example Plan](skills/swarm/references/example-plan.md) — complete plan template
- [Prerequisites](skills/swarm/references/prerequisites.md) — initialization workflow
- [Dependency Graph](skills/swarm/references/dependency-graph.md) — how dependencies work
- [Worktree Guide](skills/swarm/references/worktree-guide.md) — git worktree operations

## License

MIT
