---
name: swarm-developer-guide
description: DevAgent instructions for swarm implementation phases. Provides quality rules, implementation workflow, self-review checklist, and PR templates. Read by DevAgent at startup. Not intended for direct user invocation.
version: 1.0.0
user-invocable: false
---

# Swarm DevAgent Guide

Instructions for DevAgents implementing plan phases in the swarm workflow.

## First Action

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/swarm.py update <plan-file> --phase <N> --status DEVELOPING
```

## Implementation Workflow

1. Read the plan file, find your phase between `<!-- PHASE:N -->` and `<!-- /PHASE:N -->` markers
2. Read CLAUDE.md for project standards
3. Implement EVERYTHING in Scope
4. Build: `make build`
5. Test: `make test`
6. Self-review (see checklist below)
7. Create PR
8. Report status

## Quality Rules

The Tech Lead will rigorously verify your work. DO NOT leave unfinished code:

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

## Self-Review Checklist

Before creating the PR, verify:

- [ ] All files from "Files to Create/Modify" exist with real implementation
- [ ] No TODO/FIXME/placeholder/mock in new code
- [ ] All acceptance criteria have corresponding implementation
- [ ] Integration points wired (check CLAUDE.md section "Project Structure")
- [ ] `make build` passes
- [ ] `make test` passes

## Create PR

```bash
git push -u origin HEAD
gh pr create --base <base-branch> --title "Phase N: <name>" --body "$(cat <<'PREOF'
## Summary
<brief description>

## Acceptance Criteria
- [ ] Criterion - implemented in `file:function()`

## Tests
make test - N tests pass

## Files Changed
<list>
PREOF
)"
```

## Hand-over

After creating the PR:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/swarm.py update <plan-file> --phase <N> --status FOR_REVIEW --pr "<#N>"
```

Report back with PR number.

## Fixing Review Feedback

When spawned to fix rejected work:

1. First action: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/swarm.py update <plan-file> --phase <N> --status FIXING`
2. Read each GitHub issue for the detailed finding
3. Read CLAUDE.md for project standards
4. Fix ALL issues — do not leave any unresolved
5. Run `make build` and `make test`
6. For each fix, commit with message referencing the issue: `fix: <description> (closes #<issue-number>)`
7. Push and create PR: `git push -u origin HEAD && gh pr create --base <base-branch> --title "Phase N: <name> (fix attempt M/3)" --body "Fixes #<issue-number>"`
8. Hand-over: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/swarm.py update <plan-file> --phase <N> --status FOR_REVIEW --pr "<#N>"`
