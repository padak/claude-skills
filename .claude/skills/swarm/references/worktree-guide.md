# Git Worktree Guide

## Contents
- Project directory structure
- Makefile targets
- .worktree-setup.sh
- Worktree lifecycle
- Troubleshooting

## Project Directory Structure

After `/swarm init`, the project is organized as:

```
myapp/
├── myapp.code-workspace  # VS Code multi-root workspace (auto-synced)
├── main/              # git repo (base branch checkout)
│   ├── Makefile
│   ├── .worktree-setup.sh
│   ├── CLAUDE.md
│   ├── src/
│   └── ...
└── worktrees/
    ├── phase-1-auth/  # git worktree (created on demand)
    ├── phase-2-api/   # git worktree
    └── fix-phase-2-api/  # fix worktree (after rejection)
```

- `main/` is the primary git checkout on the base branch
- `worktrees/` contains all worktrees created by swarm
- Each worktree is an isolated working directory with its own branch
- All worktrees share the same `.git` database (disk efficient)

## Makefile Targets

The Makefile in `main/` provides these targets:

### `make worktree BRANCH=<name>`
Creates a new worktree and sets it up:
```bash
git worktree add ../worktrees/$(BRANCH) -b $(BRANCH)
cd ../worktrees/$(BRANCH) && bash .worktree-setup.sh
```

### `make worktree-remove BRANCH=<name>`
Removes a worktree and its branch:
```bash
git worktree remove ../worktrees/$(BRANCH)
git branch -D $(BRANCH)
```

### `make setup`
Installs dependencies and prepares the environment. Run inside any worktree.
Stack-specific — delegates to `.worktree-setup.sh`.

### `make build`
Builds the project. Stack-specific.

### `make test`
Runs the test suite. Stack-specific.

## .worktree-setup.sh

Created by `/swarm init` based on detected stack. Handles:

- **Dependency installation**: `npm ci`, `pip install -r requirements.txt`, etc.
- **Environment setup**: symlink `.env` from main, copy if needed
- **Stack-specific setup**: database migrations, code generation, etc.

Example for a Node.js project:
```bash
#!/bin/bash
set -e
# Symlink env from main
ln -sf ../../main/.env .env
# Install dependencies (clean install for consistency)
npm ci
# Run code generation if needed
npm run generate 2>/dev/null || true
```

Example for a Python project:
```bash
#!/bin/bash
set -e
# Symlink env from main
ln -sf ../../main/.env .env
# Create and activate venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Worktree Lifecycle

### Create
```bash
cd main
make worktree BRANCH=phase-1-auth
```
This creates `../worktrees/phase-1-auth/` with a new branch, installs deps, and sets up env.

### Use
DevAgent works in `worktrees/phase-1-auth/`. All git operations (commit, push) happen there.
The worktree has its own branch — no conflict with other worktrees or main.

### Remove
```bash
cd main
make worktree-remove BRANCH=phase-1-auth
```
This removes the worktree directory and deletes the branch.

## Workspace File

The `.code-workspace` file at the project root provides VS Code multi-root workspace support. It allows you to see `main/` and all active worktrees in a single VS Code window.

### Automatic Sync

The workspace file is synced automatically by `make sync-workspace`, which is called from both `worktree` and `worktree-remove` targets. You don't need to manage it manually.

The sync logic:
- Scans `worktrees/*/` — a subdirectory is a worktree only if it contains a `.git` file
- `main/` is always listed first, then worktrees sorted alphabetically
- Preserves existing settings in the workspace file (only `folders` are overwritten)
- Creates a new workspace file if one doesn't exist
- Fails with a clear error if the workspace file contains invalid JSON

### Opening the Workspace

```bash
code myapp.code-workspace
```

This opens VS Code with all active worktrees visible in the sidebar. When worktrees are added or removed, VS Code will detect the workspace file change and offer to reload.

### Initial Creation

The workspace file is created during `/swarm init` when `make sync-workspace` runs for the first time. Initially it contains only `main/`.

## Troubleshooting

### Worktree lock conflict
```
fatal: '<path>' is locked
```
Another process is using the worktree. Wait and retry. If stale:
```bash
git worktree unlock ../worktrees/<branch-name>
```

### Stale worktree reference
```bash
git worktree prune
```
Removes references to worktrees whose directories no longer exist.

### Branch already exists
```
fatal: a branch named '<name>' already exists
```
A previous worktree wasn't cleaned up properly:
```bash
git branch -D <branch-name>
git worktree prune
```

### Orphaned worktree (agent crashed)
List all worktrees and remove abandoned ones:
```bash
git worktree list
make worktree-remove BRANCH=<abandoned-branch>
swarm.py update <plan-file> --phase <N> --status REJECTED
```

### Disk space
Each worktree shares the `.git` database but has its own working copy. For large repos, check available space before creating many worktrees:
```bash
du -sh main/
# Multiply by number of parallel phases for rough estimate
```
