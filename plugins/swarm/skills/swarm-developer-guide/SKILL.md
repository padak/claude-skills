---
name: swarm-developer-guide
description: DevAgent instructions for swarm implementation phases. Provides quality rules, implementation workflow, self-review checklist, and PR templates. Read by DevAgent at startup. Not intended for direct user invocation.
version: 1.3.0
user-invocable: false
---

# Swarm DevAgent Guide

Instructions for DevAgents implementing plan phases in the swarm workflow.

## First Action

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/swarm.py update <plan-file> --phase <N> --status DEVELOPING
```

## Quality Rules

The Tech Lead WILL reject your work if ANY of the following are found. No exceptions:

- Empty function bodies (`pass`, `return None`, `{}`, `throw new Error("not implemented")`)
- Mock data instead of real implementation
- Trivial tests that don't verify real behavior (`assert True`, `expect(1).toBe(1)`)
- Placeholder comments (`// TODO`, `// FIXME`, `# implement later`)

## Implementation Rules

1. Follow CLAUDE.md standards (no hardcoded values, fail fast)
2. Create or update ALL files listed in "Files to Create/Modify" — every single one
3. Write ALL tests specified in "Tests Required" — run with `make test`
4. Verify build: `make build`
5. For each acceptance criterion, identify WHERE in your code it's satisfied
6. Commit with clear messages referencing the phase

## Gated Implementation Workflow

Every step below is a named GATE. You MUST pass each gate before proceeding to the next. If a gate fails, STOP, fix the issue, and retry the gate. DO NOT skip gates.

### GATE: Implement

1. Read the plan file, find your phase between `<!-- PHASE:N -->` and `<!-- /PHASE:N -->` markers
2. Read CLAUDE.md for project standards
3. Implement EVERYTHING in Scope — every file, every function, every test
4. Commit with clear messages referencing the phase

### GATE: Build

Run `make build`. The exit code MUST be 0.

- If it fails: STOP. Read the error output. Fix the issue. Run `make build` again.
- DO NOT CONTINUE to the next gate until `make build` exits 0.

### GATE: Tests

Run `make test`. The exit code MUST be 0.

- If it fails: STOP. Read the error output. Fix the failing tests or implementation. Run `make test` again.
- DO NOT CONTINUE to the next gate until `make test` exits 0.

### GATE: Mandatory Self-Review

You MUST verify every item below before proceeding. DO NOT CONTINUE to Create PR until ALL items are verified.

**File Inventory**

For EVERY file listed in "Files to Create/Modify" in the plan:
- Open the file using the Read tool and confirm it exists
- Confirm it contains real, complete implementation — not stubs, not empty bodies, not TODO placeholders
- If ANY file is missing or incomplete: STOP. Create/complete the file. Re-verify.

**Acceptance Criteria Verification**

For EVERY criterion listed in "Acceptance Criteria" in the plan:
- Identify the specific file:line where the criterion is implemented
- If you cannot point to a concrete file:line for any criterion: STOP. Implement it. Re-verify.

**Prohibited Patterns Check**

Run the following command in your worktree:
```bash
rg -n "TODO|FIXME|HACK|placeholder|not implemented|implement later" --type-not md
```
- If any matches are found in your new code: STOP. Replace every placeholder with real implementation. Re-run the check.

**Test Count Verification**

- Count the number of tests you wrote
- Compare against "Tests Required" in the plan
- Verify no tests are skipped (`@pytest.mark.skip`, `xit(`, `.skip(`, `xtest(`)
- If test count is lower than planned or any tests are skipped: STOP. Write the missing tests. Re-verify.

DO NOT CONTINUE to Create PR until ALL items above are verified.

### GATE: Create PR

Three explicit steps. Each MUST succeed.

**Step 1: Push**
```bash
git push -u origin HEAD
```
If push fails, diagnose and retry. DO NOT proceed without a successful push.

**Step 2: Create PR with evidence table**
```bash
gh pr create --base <base-branch> --title "Phase N: <name>" --body "$(cat <<'PREOF'
## Summary
<brief description>

## Evidence Table
| Acceptance Criterion | File:Line | Test |
|---------------------|-----------|------|
| Criterion 1 | src/file.ts:42 | test_name |
| Criterion 2 | src/other.ts:15 | test_name_2 |

## Tests
make test - N tests pass, 0 fail, 0 skip

## Files Changed
<list every file from plan with confirmation>
PREOF
)"
```

The evidence table in the PR body is MANDATORY. It MUST contain one row per acceptance criterion from the plan. DO NOT use any other format.

**Step 3: Verify PR existence**
```bash
gh pr view --json number,url
```
This command MUST succeed and return a valid PR number and URL. If it fails:
- Debug: check `gh pr list --head $(git branch --show-current)`
- Retry PR creation if needed
- DO NOT proceed to Hand-over without a verified PR

### GATE: Verify PR

Run `gh pr view --json number,url` one final time. Record the PR number.

- If this fails: go back to GATE: Create PR
- DO NOT hand-over without a verified PR number

## Hand-over

**PREREQUISITE**: You MUST have a verified PR number from GATE: Verify PR. If you do not have one, go back to GATE: Create PR. DO NOT report FOR_REVIEW if you have not created and verified a PR.

After verifying the PR:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/swarm.py update <plan-file> --phase <N> --status FOR_REVIEW --pr "<#N>"
```

Report back with the PR number and URL.

## Fixing Review Feedback

When spawned to fix rejected work, follow the same gated workflow:

1. **First action**: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/swarm.py update <plan-file> --phase <N> --status FIXING`
2. Read each GitHub issue for the detailed finding
3. Read CLAUDE.md for project standards
4. Fix ALL issues — do not leave any unresolved

Then pass through ALL gates again:

### GATE: Build (Fix)
`make build` MUST exit 0. If not: STOP, fix, retry. DO NOT CONTINUE.

### GATE: Tests (Fix)
`make test` MUST exit 0. If not: STOP, fix, retry. DO NOT CONTINUE.

### GATE: Mandatory Self-Review (Fix)
Same checklist as above — file inventory, acceptance criteria, prohibited patterns, test count. ALL items MUST pass.

### GATE: Create PR (Fix)
```bash
git push -u origin HEAD
gh pr create --base <base-branch> --title "Phase N: <name> (fix attempt M/3)" --body "$(cat <<'PREOF'
## Summary
Fixes review feedback for Phase N.

## Issues Resolved
- Fixes #<issue-number>: <description of fix>

## Evidence Table
| Acceptance Criterion | File:Line | Test |
|---------------------|-----------|------|
| Criterion 1 | src/file.ts:42 | test_name |

## Tests
make test - N tests pass, 0 fail, 0 skip
PREOF
)"
```

### GATE: Verify PR (Fix)
`gh pr view --json number,url` MUST succeed. If not: debug, retry. DO NOT hand-over without verified PR.

### Hand-over (Fix)
**PREREQUISITE**: You MUST have a verified PR number. If not, go back to GATE: Create PR (Fix).

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/swarm.py update <plan-file> --phase <N> --status FOR_REVIEW --pr "<#N>"
```

Report back with PR number.
