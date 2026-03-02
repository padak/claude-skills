# Dependency Graph

## Contents
- Phase tag format
- Dependency types
- Cycle detection
- Topological sort and execution groups
- Execution patterns

## Phase Tag Format

Phases are delimited by HTML comment tags with optional DEPENDS attribute:

```markdown
<!-- PHASE:1 -->
...
<!-- /PHASE:1 -->

<!-- PHASE:2 DEPENDS:1 -->
...
<!-- /PHASE:2 -->

<!-- PHASE:3 DEPENDS:1,2 -->
...
<!-- /PHASE:3 -->
```

Rules:
- Opening tag: `<!-- PHASE:<id> -->` or `<!-- PHASE:<id> DEPENDS:<id>,<id> -->`
- Closing tag: `<!-- /PHASE:<id> -->`
- IDs are positive integers
- DEPENDS lists comma-separated phase IDs
- Every referenced dependency must exist as a phase
- Opening and closing tags must match

## Dependency Types

### Explicit dependencies
Declared in the `DEPENDS` attribute of the phase tag.

### Implicit dependencies
Detected by `swarm.py parse` from overlapping files in `### Files to Create/Modify` sections. If Phase 2 and Phase 3 both modify `src/lib/auth.ts`, they cannot run in parallel — one gets an implicit dependency on the other (lower ID first).

## Cycle Detection

Before execution, `swarm.py parse` checks for cycles in the dependency graph. A cycle means the plan is impossible to execute:

```
Phase 1 depends on Phase 3
Phase 2 depends on Phase 1
Phase 3 depends on Phase 2
→ Cycle detected: 1 → 3 → 2 → 1. Stop with error.
```

## Topological Sort and Execution Groups

Phases are sorted into execution groups using topological sort (Kahn's algorithm):

1. Find all phases with no unresolved dependencies → Group 1
2. Mark Group 1 as "resolved"
3. Find all phases whose dependencies are now all resolved → Group 2
4. Repeat until all phases are grouped

Phases within the same group can run in parallel. Groups execute sequentially.

## Execution Patterns

### Linear
```
Phase 1 → Phase 2 → Phase 3
Groups: [1], [2], [3]
```
All sequential. Each phase depends on the previous.

### Fan-out
```
Phase 1 → Phase 2
Phase 1 → Phase 3
Phase 1 → Phase 4
Groups: [1], [2, 3, 4]
```
Phase 1 first, then 2, 3, 4 in parallel.

### Fan-in
```
Phase 1 → Phase 4
Phase 2 → Phase 4
Phase 3 → Phase 4
Groups: [1, 2, 3], [4]
```
Phases 1, 2, 3 in parallel, then Phase 4 after all complete.

### Diamond
```
Phase 1 → Phase 2
Phase 1 → Phase 3
Phase 2 → Phase 4
Phase 3 → Phase 4
Groups: [1], [2, 3], [4]
```
Phase 1 first, then 2 and 3 in parallel, then 4 after both complete.

### Mixed
```
Phase 1 (no deps)
Phase 2 DEPENDS:1
Phase 3 DEPENDS:1
Phase 4 DEPENDS:2,3
Phase 5 (no deps)
Phase 6 DEPENDS:5
Groups: [1, 5], [2, 3, 6], [4]
```
Independent chains can interleave their groups.
