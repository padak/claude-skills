---
name: swarm
description: Orchestrated multi-agent implementation using Tech Lead + Developer pattern. Use when implementing phased plans from docs/PLAN.md. Triggers: /swarm, "implement the plan", "run phased implementation", "execute PLAN.md phases". Spawns Developer agents in isolated git worktrees per phase, reviews PRs, handles retries and escalation.
---

# Swarm - Orchestrated Multi-Agent Implementation

Execute a phased implementation plan using a Tech Lead + Developer agent
pattern. Each phase runs in its **own git worktree**, so the main checkout
never switches branches and independent phases can run in parallel.

## Arguments

- `/swarm` - Use default plan file `docs/PLAN.md`
- `/swarm <plan-file>` - Use specified plan file

## Workflow

```
For each phase in plan:
  1. Create a worktree + branch for the phase (main checkout stays on main)
  2. Spawn Developer agent working inside that worktree
  3. Developer creates PR when done
  4. Tech Lead (this agent) reviews PR
  5. If APPROVED: merge, clean up worktree + branch, continue
  6. If CHANGES_REQUESTED: Developer fixes (max 3 attempts)
  7. If max attempts exceeded: ESCALATE to human

Phases marked independent in the plan MAY run in parallel (one worktree +
one Developer agent each). Dependent phases run sequentially — each starts
from main AFTER the previous phase merged.
```

## Step 1: Parse Plan

Read the plan file and extract phases. Each phase has this structure:

```markdown
<!-- PHASE:N -->
## Phase N: Name

### Branch
`phase-N-name`

### Depends on
Phase N-1 (or "none" — independent phases may run in parallel)

### Scope
...

### Files to Create/Modify
...

### Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

### Tests Required
...
<!-- /PHASE:N -->
```

## Step 2: Create a worktree for the phase

Run from the primary checkout (never `git checkout` a phase branch there):

```bash
MAIN_WT=$(git worktree list --porcelain | head -1 | sed 's/^worktree //')
git -C "$MAIN_WT" pull origin main
git -C "$MAIN_WT" worktree add "$MAIN_WT/.claude/worktrees/<branch-name>" -b <branch-name> main
```

If the Agent tool supports `isolation: "worktree"`, prefer that — it creates
and cleans up the worktree automatically. Otherwise pass the worktree path to
the Developer agent explicitly.

## Step 3: Spawn Developer Agent

For parallel-safe phases, send multiple Task calls in a single message — one
Developer per phase, each in its own worktree.

```
Task(
  subagent_type: "general-purpose",
  description: "Implement Phase N",
  prompt: """
You are a Developer agent implementing Phase N.

## Working directory
You work EXCLUSIVELY inside the worktree: <worktree-path>
It is already on branch <branch-name>. Never touch the primary checkout,
never switch branches. All file paths and commands are relative to this
worktree.

## Task
Read the plan file, find Phase N (between <!-- PHASE:N --> markers), implement EVERYTHING in Scope.

## CRITICAL: Your Work Will Be Rigorously Reviewed

The Tech Lead will verify:
1. **Every file** in "Files to Create/Modify" exists and has real implementation
2. **Every acceptance criterion** is fully implemented (not stubbed)
3. **Every test** in "Tests Required" exists and passes
4. **Integration points** - routes/entry points registered, config documented, migrations match models

DO NOT:
- Create stub implementations (empty functions, pass, TODO comments)
- Skip any file from the list
- Write trivial tests that don't verify real behavior
- Leave acceptance criteria partially implemented
- Forget to register routers/entry points or add config vars

## Rules
1. Follow CLAUDE.md configuration standards (no hardcoded values, fail fast)
2. Create ALL files listed in "Files to Create/Modify" - every single one
3. Write ALL tests specified in "Tests Required" - run them to verify they pass
4. For each acceptance criterion, identify WHERE in your code it's satisfied
5. Commit with clear messages referencing the phase

## Before Creating PR - Self-Review Checklist
- [ ] All files from "Files to Create/Modify" exist
- [ ] No TODO/FIXME/placeholder comments in new code
- [ ] All acceptance criteria have corresponding implementation
- [ ] All tests pass (run the project's test command)
- [ ] New entry points registered, new config vars documented

## When Done
Push the branch and create a PR with acceptance criteria as checklist:

git push -u origin <branch-name>
gh pr create --title "Phase N: <name>" --body "$(cat <<'EOF'
## Implementation Summary
<brief description>

## Acceptance Criteria
- [ ] Criterion 1 - implemented in `file.py:function()`
- [ ] Criterion 2 - implemented in `file.py:function()`

## Tests
- <test command> - X tests pass

## Files Changed
<list of files created/modified>
EOF
)"

Report back with PR number.
"""
)
```

## Step 4: Review the PR (RIGOROUS)

**IMPORTANT:** Previous swarm runs had phases that were incomplete or sloppy.
Review inside the phase's worktree (`cd <worktree-path>` or absolute paths).
Do NOT approve until ALL checks pass.

### 4.1 File Inventory Check

For EACH file in the phase's "Files to Create/Modify" list: check it exists,
read it, verify the content is substantial.

**FAIL if:** any listed file is missing; any file contains TODO/FIXME/
placeholder comments; any file is a stub (empty class, pass-only functions).

### 4.2 Acceptance Criteria Verification

For EACH criterion: read it literally, find the implementing code, verify
behavior (run a specific test or manual check).

```markdown
| Criterion | Evidence | Verified |
|-----------|----------|----------|
| "Can create quota for user" | quotas/service.py:create_quota() | ✓ test passes |
| "Unique constraint prevents duplicates" | migration has UNIQUE KEY | ✓ |
```

**FAIL if:** any criterion has no implementation, is partial, or relies on
code that doesn't exist yet.

### 4.3 Test Coverage Check

Run the phase's tests inside the worktree. **FAIL if:** any test fails, test
count is significantly lower than the plan specifies, or tests are trivial
(`assert True`).

### 4.4 Integration Points Check

For new modules verify: entry points/routers registered, config vars
documented (.env.example or equivalent), migrations match ORM models.
**FAIL if** endpoints are unreachable or config is undocumented.

### 4.5 Code Quality Check

1. **No hardcoded values** - all thresholds from config
2. **No silent defaults** - missing required config = startup failure
3. **Follows existing patterns** - check similar modules for consistency

### 4.6 Final Verdict

Only after ALL checks pass, produce the review report:

```markdown
## PR Review: Phase N

### File Inventory: ✓ PASS (all N files, no stubs)
### Acceptance Criteria: ✓ PASS (table with evidence per criterion)
### Tests: ✓ PASS (X/X, matches "Tests Required")
### Integration: ✓ PASS
### Code Quality: ✓ PASS

**VERDICT: APPROVED**
```

If ANY check fails, list each failed check with what is missing and what is
required, then **VERDICT: CHANGES_REQUESTED**.

## Step 5: Decision

**APPROVED:**
```bash
gh pr merge <pr-number> --squash --delete-branch

# Post-merge cleanup (see post-merge skill): sync main, drop the worktree
git -C "$MAIN_WT" pull origin main
git -C "$MAIN_WT" worktree remove "$MAIN_WT/.claude/worktrees/<branch-name>"
git -C "$MAIN_WT" worktree prune
git -C "$MAIN_WT" branch -d <branch-name> 2>/dev/null || true
git -C "$MAIN_WT" remote prune origin
```
Continue to next phase (dependent phases create their worktree from the
freshly pulled main).

**CHANGES_REQUESTED:**
```
Task(
  prompt: """
Your PR for Phase N needs changes.

## Working directory
Fix EXCLUSIVELY inside the worktree: <worktree-path> (branch <branch-name>).

## Feedback
<specific feedback>

## Required Changes
1. ...

Fix, commit, and push to the same branch. Attempt: <N>/3
"""
)
```

**Attempt >= 3:**
```
ESCALATE: Phase N requires human intervention.
PR: <url>
Issues: <summary>
```
Keep the worktree for inspection. Stop and notify the user.

## Step 6: Progress Tracking

After each phase:

```
## Swarm Progress

| Phase | Status      | Worktree                       | PR  | Attempts |
|-------|-------------|--------------------------------|-----|----------|
| 1     | DONE        | (removed)                      | #12 | 1        |
| 2     | IN_PROGRESS | .claude/worktrees/phase-2-api  | #13 | 1        |
| 3     | PENDING     | -                              | -   | -        |
```

## Error Handling

- **Git conflict on merge:** Escalate immediately (parallel phases touching the same files)
- **`worktree add` fails (branch exists):** `git worktree prune`, delete the stale branch, retry once
- **CI failure:** Count as failed review attempt
- **Agent timeout:** Retry once, then escalate
- **Network error:** Retry with backoff
