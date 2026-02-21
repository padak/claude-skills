# Plan Writing Guide

## Contents
- Phase structure recap
- Breaking work into phases
- Identifying dependencies
- Making phases independent
- Anti-patterns
- Decision flowchart

## Phase Structure Recap

Each phase needs these sections (validated by `swarm.py parse`):

```markdown
<!-- PHASE:N DEPENDS:X,Y -->
## Phase N: Name

### Branch
`phase-n-name`

### Scope
What to implement. Include pseudocode for non-trivial logic.

### Files to Create/Modify
- `path/to/file.py` — what it contains

### Acceptance Criteria
- [ ] Observable, verifiable outcome

### Tests Required
- `tests/test_file.py::test_name` — what it verifies
<!-- /PHASE:N -->
```

## Breaking Work Into Phases

A phase is a **unit of work one DevAgent can complete independently**. Good phase boundaries align with:

- **One vertical slice**: database model + API endpoint + tests for a single feature
- **One infrastructure layer**: all database models, all API routes, all workers
- **One bounded context**: authentication, billing, notifications

**Phase sizing**: A phase should produce 3-15 files. Fewer than 3 — merge with another phase. More than 15 — split into sub-features.

### Layered vs Vertical

**Layered** (horizontal): Phase 1 = all models, Phase 2 = all APIs, Phase 3 = all tests.
Simple dependency chain (1→2→3), no parallelism. Choose when layers are tightly coupled.

**Vertical** (by feature): Phase 1 = foundation, Phase 2 = users (model+API+tests), Phase 3 = tasks (model+API+tests).
Phases 2 and 3 run in parallel. Choose when features are independent.

**Prefer vertical** — it maximizes parallelism.

## Identifying Dependencies

### Explicit: data or logic flows between phases

Ask: "Does Phase B need something Phase A creates to exist first?"

Examples:
- API endpoint needs the database model it queries → depends
- Dashboard aggregates data from users and tasks → depends on both
- Auth middleware is used by all endpoints → all depend on auth phase

Declare with `DEPENDS` attribute: `<!-- PHASE:3 DEPENDS:1,2 -->`

### Implicit: overlapping files

`swarm.py parse` auto-detects when two phases list the same file in "Files to Create/Modify". The later phase (higher ID) gets an implicit dependency on the earlier one.

This is the most common source of **accidental serialization**. Two phases that seem independent become sequential because both modify `src/main.py`.

### No dependency needed when

- Phases touch completely different files
- Phases use shared code but only **read** it (not modify)
- Phases create independent modules that are wired together in a later phase

## Making Phases Independent

The goal: maximize the number of phases that can run in parallel.

### 1. Defer integration to a later phase

Bad — Phase 2 and 3 both modify `src/main.py` to register their routes:
```
Phase 2: User API      → Files: src/routers/users.py, src/main.py
Phase 3: Task API      → Files: src/routers/tasks.py, src/main.py
```
Phases 2 and 3 become sequential (implicit dependency on `src/main.py`).

Good — Phase 4 wires everything together:
```
Phase 2: User API      → Files: src/routers/users.py, src/schemas/user.py
Phase 3: Task API      → Files: src/routers/tasks.py, src/schemas/task.py
Phase 4: Integration   → Files: src/main.py (registers all routers)
```
Phases 2 and 3 run in parallel.

### 2. Avoid shared utility files

Bad — both phases create helpers in the same file:
```
Phase 2: → Files: src/utils/helpers.py (adds format_date)
Phase 3: → Files: src/utils/helpers.py (adds format_currency)
```

Good — each phase owns its utilities:
```
Phase 2: → Files: src/utils/date.py
Phase 3: → Files: src/utils/currency.py
```

### 3. Split shared config across phases

Bad:
```
Phase 2: → Files: src/config.py (adds USER_DEFAULTS)
Phase 3: → Files: src/config.py (adds TASK_DEFAULTS)
```

Good:
```
Phase 2: → Files: src/config/users.py
Phase 3: → Files: src/config/tasks.py
Phase 4: → Files: src/config/__init__.py (re-exports all)
```

### Rule of thumb

If the "Files to Create/Modify" lists of two phases share ANY file, they cannot run in parallel. Move shared file modifications to a dedicated integration phase.

## Anti-Patterns

| Anti-pattern | Problem | Fix |
|-------------|---------|-----|
| God phase | One phase with 20+ files, does everything | Split by feature or layer |
| Micro phases | Phase creates 1 file | Merge with related phase |
| Hidden dependency | Phases seem independent but import each other's code | Add explicit DEPENDS or defer imports to integration phase |
| Shared file trap | Two parallel phases both modify the same file | Move shared file to integration phase |
| Missing foundation | API phase doesn't depend on model phase | Add DEPENDS — build fails without models |
| Circular dependency | Phase A needs B, Phase B needs A | Restructure: extract shared part into Phase C |
| Test-only phase | Phase that only writes tests | Merge tests into the phase that creates the code |

## Decision Flowchart

When planning phases, for each pair ask:

```
Does Phase B need files/types/APIs created by Phase A?
  YES → B DEPENDS on A

Does Phase B modify any file that Phase A also modifies?
  YES → Move shared file to integration phase, OR add DEPENDS

Can Phase B's DevAgent run `make build && make test` without Phase A's code?
  NO  → B DEPENDS on A
  YES → Independent, no DEPENDS needed
```

For the complete dependency graph mechanics (topological sort, execution groups, cycle detection), see [dependency-graph.md](dependency-graph.md).

For a complete example plan demonstrating solo, parallel, and integration phases, see [example-plan.md](example-plan.md).
