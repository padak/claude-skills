---
name: swarm
description: Orchestrates multi-agent implementation using Tech Lead + DevAgent pattern. Parses phased plans, builds dependency graphs, spawns DevAgents per phase with automatic parallelization via git worktrees when safe. Reviews PRs rigorously, handles retries with escalation. Use when the user has a phased implementation plan and wants to execute it with parallel agents.
version: 1.1.0
argument-hint: "[init | <plan-file>]"
---

# Swarm - Multi-Agent Implementation

Execute a phased implementation plan using Tech Lead (orchestrator) + Developer (implementor) agents. Independent phases run in parallel via git worktrees, dependent phases run sequentially.

**Base branch** is the current branch when `/swarm` is invoked. All phase branches are created from it, all merges go back to it.
The base branch name is stored in the plan's status file (`<plan-file>.swarm_status.json`) and read by `swarm.py` on resume.

**Project root** is the directory containing `main/` and `worktrees/`. All Tech Lead commands assume cwd is the project root. Use absolute paths when passing working directories to DevAgents.

## Arguments

- `/swarm init` - Bootstrap worktree and build support for this project
- `/swarm` - Execute default plan `docs/PLAN.md`
- `/swarm <plan-file>` - Execute specified plan file

**swarm.py shorthand**: All `swarm.py` commands in this document expand to:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/swarm.py
```

## Step 0: Prerequisites

### `/swarm init`

Follow the full initialization workflow in [references/prerequisites.md](references/prerequisites.md). It covers: CLAUDE.md validation, directory restructuring, Makefile and .worktree-setup.sh creation with stack-specific examples, and verification cycle.

**STOP if any step fails. Do not proceed until init completes successfully.**

### `/swarm` or `/swarm <plan-file>`

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/swarm.py prereq <plan-file>
```

**If it fails with missing Makefile or directory structure: STOP and tell the user to run `/swarm init` first.**

## Key Concepts

**Execution group**: Phases at the same dependency level that can run in parallel. `swarm.py parse` computes these from the dependency graph. A group with one phase is **solo**; 2+ phases is **parallel**.

**Group label**: A letter identifier (A, B, C...) assigned to each execution group by `swarm.py parse`. Used in branch names like `integration-A` and status tracking.

**Solo phase**: PR is merged directly to base on approval → MERGED → DONE.

**Parallel phase**: PR stays open on remote for integration merge in Step 6. On approval → PR_APPROVED. Code reaches base only after all group phases pass integration review.

**Roles**: Tech Lead creates/removes all worktrees and branches. DevAgent only implements code and creates PRs.

**DevAgent**: The Developer agent spawned by Tech Lead to implement a phase. Referred to as "DevAgent" throughout this document and related guides.

**Dependency graph**: Phases declare explicit dependencies via `DEPENDS` attribute; implicit dependencies are auto-detected from overlapping files. See [references/dependency-graph.md](references/dependency-graph.md). For guidance on writing plans and maximizing parallelism, see [references/plan-writing-guide.md](references/plan-writing-guide.md).

**Worktrees and Makefile**: Each phase runs in its own git worktree. The Makefile provides `setup`, `build`, `test`, `worktree`, and `worktree-remove` targets. See [references/worktree-guide.md](references/worktree-guide.md).

**Workspace file**: VS Code multi-root workspace (`<project-name>.code-workspace`) at the project root. Synced automatically by `make sync-workspace` (called from `worktree` and `worktree-remove` targets).

## Status Diagram

```
PENDING ───── Tech Lead dispatches ──→ DISPATCHED
DISPATCHED ── DevAgent starts ───────→ DEVELOPING
DEVELOPING ── DevAgent creates PR ───→ FOR_REVIEW
FOR_REVIEW ── Tech Lead approves ────→ MERGED        (solo: merged to base)
FOR_REVIEW ── Tech Lead approves ────→ PR_APPROVED   (parallel: PR stays open)
FOR_REVIEW ── Tech Lead rejects ─────→ REJECTED      (GitHub issues created)
MERGED ───────────────────────────────→ DONE
PR_APPROVED ─ Integration passes ────→ DONE
REJECTED ──── DevAgent fixes ────────→ FIXING
FIXING ────── DevAgent creates new PR ─→ FOR_REVIEW
REJECTED ──── Max attempts reached ──→ ESCALATED
```

Synthetic integration fix phases (Step 6.4) follow the same flow with ID prefix `I-` and `"synthetic": true` flag.

**Who sets what:**

| Status | Set by | When |
|--------|--------|------|
| DISPATCHED | Tech Lead | Worktree created, agent spawned |
| DEVELOPING | DevAgent | Started implementing |
| FOR_REVIEW | DevAgent | PR created |
| MERGED | Tech Lead | Solo: PR merged, worktree removed. Immediately followed by DONE. |
| PR_APPROVED | Tech Lead | Parallel: PR approved, worktree removed, PR stays open |
| REJECTED | Tech Lead | PR closed, GitHub issues created |
| FIXING | DevAgent | Started fixing issues |
| DONE | Tech Lead | Solo: after MERGED. Parallel: after integration merged (Step 6) |
| ESCALATED | Tech Lead | Max review attempts exceeded |

## Workflow Overview

```
0. Verify prerequisites (Step 0)
1. Parse plan → build dependency graph (Step 1)
2. Identify phases with all dependencies DONE
3. Tech Lead: create worktree + branch for each ready phase (Step 2)
4. Spawn DevAgents — parallel when multiple phases ready (Step 3)
5. Tech Lead: review each PR (Step 4 + Step 5)
   - APPROVED solo → merge → DONE
   - APPROVED parallel → PR_APPROVED (PR stays open)
   - REJECTED → create issues, spawn fix DevAgent
   - Max attempts → ESCALATED
6. All phases in parallel group PR_APPROVED → integration review (Step 6)
   Return to step 3 — newly unblocked phases are now ready
7. All phases DONE (or ESCALATED) → summarize to user (Step 7)
```

## Step 1: Parse Plan and Build Dependency Graph

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/swarm.py parse <plan-file>
```

The `parse` command also records the current branch as `base_branch` in the status file.

If the command fails, stop and report errors to the user.

Expected phase structure:

```markdown
<!-- PHASE:1 -->
## Phase 1: Name

### Branch
`phase-1-name`

### Scope
...

### Files to Create/Modify
...

### Acceptance Criteria
- [ ] Criterion 1

### Tests Required
...
<!-- /PHASE:1 -->

<!-- PHASE:2 DEPENDS:1 -->
## Phase 2: Name
...
<!-- /PHASE:2 -->
```

The `parse` command validates tags, required sections, and dependency cycles. It outputs the execution graph as JSON. On first run, creates a status file (`<plan-file>.swarm_status.json`). On subsequent runs, reads existing status for resume.

For a complete example plan, see [references/example-plan.md](references/example-plan.md).

### Status Tracking

```bash
swarm.py update <plan-file> --phase <N...> --status <STATUS> [--pr "<#N...>"] [--attempts <N>]
swarm.py next <plan-file>             # phases ready to start
swarm.py check-group <plan-file>      # JSON: parallel groups where all phases PR_APPROVED
swarm.py status <plan-file>           # current state of all phases
```

## Step 2: Create Worktrees and Dispatch

For each phase returned by `swarm.py next`:

```bash
cd main
make worktree BRANCH=<branch-name>
swarm.py update <plan-file> --phase <N> --status DISPATCHED
```

Create worktrees for all ready phases before spawning agents (Step 3).

## Step 3: Spawn DevAgents

Spawn a `dev-agent` subagent for each DISPATCHED phase. For multiple ready phases, spawn in parallel.

```
Task(
  subagent_type: "swarm:dev-agent",
  description: "Implement Phase N: <name>",
  prompt: """
  Phase: N
  Branch: <branch-name>
  Plan file: <full-path-to-plan-file>
  Base branch: <base-branch>
  Working directory: <project-root>/worktrees/<branch-name>
  """
)
```

The `dev-agent` runs on Sonnet with preloaded instructions from the swarm-developer-guide skill, maxTurns=50, and bypassPermissions mode.

## Step 4: Review the PR

**Do NOT approve until ALL checks pass.** Incomplete phases are the most common swarm failure.

### 4.1 File Inventory
Read every file listed in "Files to Create/Modify". FAIL if:
- Any file is missing
- Any file contains unfinished code (empty bodies, TODO/FIXME, mocks, placeholders)

### 4.2 Acceptance Criteria
For EACH criterion, build an evidence table:

| Criterion | Evidence (file:line or test) | Verified |
|-----------|------------------------------|----------|
| Criterion 1 | src/auth.ts:42 | test passes |
| Criterion 2 | migration has UNIQUE constraint | verified |

FAIL if any criterion has no evidence or is only partially implemented.

### 4.3 Tests
Run `make test` in the worktree. FAIL if:
- Any test fails
- Test count is significantly lower than "Tests Required"
- Tests are trivial (don't verify real behavior)

### 4.4 Integration Points
Check CLAUDE.md section **"Project Structure"** for conventions (routing, config, migrations).
Verify new code is properly wired into the existing project. FAIL if any integration is missing.

### 4.5 Code Quality
Check CLAUDE.md sections **"Code Quality Standards"** and **"Config Management"**.
FAIL if code violates project conventions.

### 4.6 Verdict

**APPROVED** — all checks pass:
```markdown
## PR Review: Phase N
### File Inventory: PASS (N/N files, no stubs)
### Acceptance Criteria: PASS
| Criterion | Evidence | Verified |
|-----------|----------|----------|
### Tests: PASS (N/N pass)
### Integration: PASS
### Code Quality: PASS
**VERDICT: APPROVED**
```

**REJECTED** — any check fails:
```markdown
## PR Review: Phase N
### FAILED CHECKS:
1. **[Check name]**: specific issue, what is missing, what to fix
**VERDICT: REJECTED**
```

## Step 5: Act on Review Verdict

MAX_REVIEW_ATTEMPTS = 3 (two correction rounds + original; beyond this — escalate to human)

**Solo vs parallel**: Check the phase's `group` field in the status file (via `swarm.py status`). If `group` is `null`, the phase is solo. If `group` is a letter (A, B, ...), the phase is parallel.

### APPROVED — Solo Phase
```bash
cd main
gh pr merge <pr-number> --merge --delete-branch
make worktree-remove BRANCH=<branch-name>
swarm.py update <plan-file> --phase <N> --status MERGED --pr "<#N>"
swarm.py update <plan-file> --phase <N> --status DONE
```
Return to Step 2 — newly unblocked phases are now ready.

### APPROVED — Parallel Group Phase
```bash
cd main
make worktree-remove BRANCH=<branch-name>
swarm.py update <plan-file> --phase <N> --status PR_APPROVED --pr "<#N>"
```
**Do NOT merge the PR.** It stays open for integration in Step 6.

Check if the group is ready:
```bash
swarm.py check-group <plan-file>
```
All PR_APPROVED → proceed to Step 6. Otherwise continue reviewing other PRs.

### REJECTED (attempt < MAX_REVIEW_ATTEMPTS)

**Tech Lead: close PR, create issues, prepare fix worktree:**
```bash
gh pr close <pr-number>
gh issue create --title "Phase N: <failed check summary>" --body "<detailed finding>" --label "swarm-fix"
make worktree-remove BRANCH=<branch-name>
make worktree BRANCH=fix-<branch-name>
cd ../worktrees/fix-<branch-name> && git fetch origin && git merge origin/<branch-name>
swarm.py update <plan-file> --phase <N> --status REJECTED
```

**Tech Lead: spawn DevAgent to fix:**
```
Task(
  subagent_type: "swarm:dev-agent",
  description: "Fix Phase N review feedback (attempt M/3)",
  prompt: """
  Phase: N (fix)
  Branch: fix-<branch-name>
  Plan file: <full-path-to-plan-file>
  Base branch: <base-branch>
  Working directory: <project-root>/worktrees/fix-<branch-name>

  GitHub Issues to Resolve:
  - #<issue-1>: <title>
  - #<issue-2>: <title>

  This is attempt M of 3 (MAX_REVIEW_ATTEMPTS).
  """
)
```
Then re-review from Step 4.

### ESCALATED (attempt >= MAX_REVIEW_ATTEMPTS)
```bash
swarm.py update <plan-file> --phase <N> --status ESCALATED --pr "<#N>"
```
```
ESCALATE: Phase N requires human intervention.
PR: <url>
Issues: <summary of unresolved findings>
```
Stop processing this phase and all phases that depend on it.

## Step 6: Integration Review (Parallel Groups)

When `swarm.py check-group` reports a complete parallel group (all phases PR_APPROVED):

### 6.1 Create Integration Branch
```bash
cd main
git fetch origin
git checkout -b integration-<group> <base-branch>
git merge origin/<phase-1-branch>
git merge origin/<phase-2-branch>
```
If merge conflicts → escalate to human immediately.

### 6.2 Build and Test
```bash
make build && make test
```
If build or tests fail → proceed to 6.4.

### 6.3 Code Review on Integration Branch

For EACH phase in the group, verify on the integration branch:
1. **File Inventory** — all files exist with real implementation
2. **Acceptance Criteria** — build evidence table (see Step 4.2)
3. **Integration Points** — no conflicts in shared files, no duplicate registrations, cross-phase imports resolve
4. **Cross-phase consistency** — shared types compatible, no conflicting config changes

Stricter than individual review — phases developed independently may have subtle conflicts.

If any check fails → proceed to 6.4.

### All Good — Merge Integration Branch

```bash
git push -u origin integration-<group>
gh pr create --title "Integration: <group description>" --base <base-branch> --head integration-<group> --body "$(cat <<'PREOF'
## Summary
Integrates parallel phases: N1, N2, ...

## Phases Included
- Phase N1: <name> (PR #<pr-1>)
- Phase N2: <name> (PR #<pr-2>)

## Verification
- make build: PASS
- make test: PASS
- Cross-phase integration: verified
PREOF
)"
gh pr merge <integration-pr> --merge --delete-branch
```
Close individual phase PRs:
```bash
gh pr close <pr-1> --comment "Merged via integration-<group>"
gh pr close <pr-2> --comment "Merged via integration-<group>"
```
Update status:
```bash
swarm.py update <plan-file> --phase <N1> <N2> --status DONE --pr "<#integration-pr>"
git checkout <base-branch>
```
Return to Step 2.

### 6.4 Issues Found — Synthetic Integration Fix Phase

Original phases stay **PR_APPROVED**. Tech Lead creates a synthetic fix phase.

```bash
cd main
git checkout <base-branch>
git branch -D integration-<group>
gh issue create --title "Integration <group>: <issue summary>" --body "<detailed finding>" --label "swarm-integration-fix"
swarm.py add-phase <plan-file> --id I-<group> --depends <N1> <N2> --branch fix-integration-<group> --synthetic
make worktree BRANCH=fix-integration-<group>
cd ../worktrees/fix-integration-<group>
git merge origin/<phase-1-branch>
git merge origin/<phase-2-branch>
swarm.py update <plan-file> --phase I-<group> --status DISPATCHED
```

**Spawn DevAgent to fix integration issues:**
```
Task(
  subagent_type: "swarm:dev-agent",
  description: "Fix integration issues for group <group>",
  prompt: """
  Phase: I-<group> (integration fix)
  Branch: fix-integration-<group>
  Plan file: <full-path-to-plan-file>
  Base branch: <base-branch>
  Working directory: <project-root>/worktrees/fix-integration-<group>
  Note: This worktree already contains all phase branches merged.

  GitHub Issues to Resolve:
  - #<issue-1>: <title>
  - #<issue-2>: <title>
  """
)
```

**After fix PR is reviewed and APPROVED:**
```bash
gh pr merge <fix-pr> --merge --delete-branch
make worktree-remove BRANCH=fix-integration-<group>
gh pr close <pr-1> --comment "Merged via integration fix #<fix-pr>"
gh pr close <pr-2> --comment "Merged via integration fix #<fix-pr>"
swarm.py update <plan-file> --phase I-<group> --status MERGED
swarm.py update <plan-file> --phase I-<group> --status DONE
swarm.py update <plan-file> --phase <N1> <N2> --status DONE --pr "<#fix-pr>"
```
Return to Step 2. If REJECTED: same retry flow as Step 5.

## Progress Tracking

```bash
swarm.py status <plan-file>           # current state of all phases
swarm.py next <plan-file>             # phases ready to start
swarm.py check-group <plan-file>      # parallel groups ready for integration
swarm.py add-phase <plan-file> ...    # create synthetic integration fix phase
```

On resume after crash, `swarm.py status` shows where to continue.

## Error Handling

| Scenario | Action |
|----------|--------|
| Git merge conflict | Escalate to human immediately |
| CI failure | Count as failed review attempt |
| Agent timeout | Retry once, then escalate |
| Network error | Retry 3 times with 5s/15s/30s backoff, then escalate |
| Worktree lock conflict | Retry 3 times with 5s/15s/30s backoff, then escalate |
| `make build`/`make test` fails in worktree | DevAgent fixes before PR |
| `make build`/`make test` fails on integration | Synthetic fix phase (Step 6.4) |
| Dependency cycle detected | `swarm.py parse` fails at Step 1, stop |
| Orphaned worktree (agent crashed) | `make worktree-remove`, set REJECTED |

## Step 7: Summary

When all phases are DONE (or ESCALATED):

```bash
swarm.py status <plan-file>
```

Report to the user:
- Total phases: N completed, M escalated
- PRs merged: list with links
- Escalated phases: list with open issues and last PR links
- Duration: from first dispatch to last DONE
