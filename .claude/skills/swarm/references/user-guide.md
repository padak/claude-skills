# Swarm User Guide

## Contents
- What is swarm
- Requirements
- Quick start
- Writing a plan
- Running swarm
- What happens during execution
- Resuming after interruption
- FAQ

## What Is Swarm

Swarm executes a phased implementation plan using parallel AI agents. You write the plan, swarm handles the rest:

1. **Tech Lead** (orchestrator) reads the plan, creates git worktrees, spawns agents
2. **DevAgents** (workers) implement code in isolated branches, create PRs
3. **Tech Lead** reviews each PR rigorously, merges or sends back for fixes
4. Independent phases run **in parallel** — a 4-phase plan with 2 independent phases saves ~40% time

Swarm uses git worktrees for isolation — each agent works in its own directory on its own branch, no conflicts.

## Requirements

- **Claude Code** with permissions allowing autonomous file and bash operations
- **git** with worktree support
- **gh** (GitHub CLI) — authenticated (`gh auth login`)
- **make** — for build/test/worktree targets
- **Python 3.10+** — for the `swarm.py` helper script
- **A GitHub remote** — swarm creates branches, PRs, and issues

## Quick Start

### 1. Initialize (once per project)

```
/swarm init
```

This will:
- Validate your `CLAUDE.md` has required sections (stack, testing, project structure, etc.)
- Reorganize directories: repo moves to `main/`, worktrees go to `worktrees/`
- Create a `Makefile` with build/test/worktree targets
- Create `.worktree-setup.sh` for dependency installation
- Verify the full cycle works

### 2. Write a plan

Create a markdown file (e.g., `docs/PLAN.md`) with phases. Each phase needs:

```markdown
<!-- PHASE:1 -->
## Phase 1: Feature Name

### Branch
`phase-1-feature-name`

### Scope
What to implement. Include pseudocode for non-trivial logic.

### Files to Create/Modify
- `src/path/to/file.py` — description

### Acceptance Criteria
- [ ] Observable, verifiable outcome

### Tests Required
- `tests/test_file.py::test_name` — what it verifies
<!-- /PHASE:1 -->
```

Dependencies between phases: `<!-- PHASE:2 DEPENDS:1 -->`

See [example-plan.md](example-plan.md) for a complete example and [plan-writing-guide.md](plan-writing-guide.md) for tips on maximizing parallelism.

### 3. Run

```
/swarm docs/PLAN.md
```

Or with the default plan (`docs/PLAN.md`):

```
/swarm
```

## Writing a Plan

### Phase sizing
- **3-15 files** per phase. Fewer → merge phases. More → split.
- Each phase should be a **vertical slice** (model + API + tests) for maximum parallelism.

### Dependencies
- Use `DEPENDS:N` when Phase B needs something Phase A creates
- Phases that modify the **same file** cannot run in parallel (auto-detected)
- Defer shared file modifications to an integration phase

### Example: 4-phase plan

```
Phase 1: Database models (solo)           → foundation
Phase 2: User API (parallel, depends: 1)  → independent feature
Phase 3: Task API (parallel, depends: 1)  → independent feature
Phase 4: Dashboard (solo, depends: 2,3)   → integration
```

Execution: Phase 1 → Phases 2+3 simultaneously → Phase 4.

## What Happens During Execution

```
/swarm docs/PLAN.md
         │
         ▼
    Parse plan, build dependency graph
         │
         ▼
    Create worktrees for ready phases
         │
         ▼
    Spawn DevAgents (parallel when possible)
         │
         ▼
    Each DevAgent: implement → build → test → create PR
         │
         ▼
    Tech Lead reviews each PR:
    ├── APPROVED solo    → merge to base → DONE
    ├── APPROVED parallel → wait for group → integration merge
    └── REJECTED         → create issues → spawn fix agent (max 3 attempts)
         │
         ▼
    All phases DONE → summary report
```

### What you'll see
- Worktree creation messages
- DevAgent task launches (parallel when safe)
- Detailed review reports with evidence tables
- PR merge confirmations
- Final summary with PR links

### What requires human intervention
- **Merge conflicts** during integration — swarm escalates immediately
- **3 failed review attempts** — swarm marks phase as ESCALATED with issue links
- **Missing CLAUDE.md sections** — swarm stops and tells you what to add

## Resuming After Interruption

Swarm tracks state in `<plan-file>.swarm_status.json`. If interrupted:

```
/swarm docs/PLAN.md
```

It picks up where it left off — completed phases stay DONE, in-progress phases are re-evaluated.