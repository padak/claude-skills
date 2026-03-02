# Swarm Prerequisites and Initialization

## Contents
- Required tools
- `/swarm init` workflow
- CLAUDE.md minimum sections
- Stack examples (Makefile + .worktree-setup.sh)
- Run-mode prerequisite check

## Required Tools

These must be installed and configured before using swarm:

- **git** with worktree support (any recent version)
- **gh** (GitHub CLI) — authenticated (`gh auth login`)
- **make** — for build/test/worktree targets
- **Python 3.10+** — for `swarm.py` script (no external packages needed). Projects using Python should use `.venv` for virtual environments.
**Recommended permission settings:** DevAgents (subagents) inherit permission settings from the parent Claude Code session. For uninterrupted parallel execution, ensure your permissions allow autonomous file and bash operations.

## `/swarm init` Workflow

### 1. Validate CLAUDE.md

Read CLAUDE.md and verify it covers these sections (see minimum examples below):

- **Stack** (tools, frameworks, versions)
- **Testing conventions** (how to run tests, which framework)
- **Code quality standards** (linting, formatting, rules)
- **Project structure** (where modules live, how to register new ones)
- **Config management** (env vars, config files, fail-fast approach)

**If any section is missing or vague, STOP and tell the user what to add.**

### 2. Confirm Stack Matches Repo

Compare CLAUDE.md stack description with actual repo artifacts:
- Lock files (`package-lock.json`, `requirements.txt`, `go.sum`, etc.)
- Config files (`tsconfig.json`, `pyproject.toml`, etc.)
- Directory structure

If they don't match, STOP and ask user to update CLAUDE.md.

### 3. Reorganize Directory Structure

Check if project already has worktree layout:
- `main/` contains git repo
- `worktrees/` exists

If not, ask user for approval:

> Swarm needs to reorganize the project directory:
> - Current repo moves to `./main/`
> - Worktrees will be created in `./worktrees/`
> - All paths and git remotes stay the same.
> Is this OK?

If approved: move repo to `main/`, create `worktrees/`.
If denied: STOP.

### 4. Create Makefile

Create a Makefile in `main/` with these required targets. Use the stack examples below as reference — adapt to the project's actual stack.

Required targets:
- `setup` — install dependencies, prepare environment
- `build` — build the project
- `test` — run the test suite
- `worktree BRANCH=<name>` — create a git worktree and set it up
- `worktree-remove BRANCH=<name>` — remove a worktree and its branch
- `sync-workspace` — sync VS Code multi-root workspace file (called automatically by `worktree` and `worktree-remove`)

### 5. Create .worktree-setup.sh

Create `.worktree-setup.sh` in `main/`. This script runs inside each new worktree to install dependencies and configure the environment. See stack examples below.

### 6. Create Initial Workspace File

```bash
cd main
make sync-workspace
```

This creates `<project-name>.code-workspace` at the project root with `main/` as the only folder. Worktrees are added automatically when created via `make worktree`.

### 7. Verify Full Cycle

Run the complete worktree lifecycle to confirm everything works:

```bash
cd main
make worktree BRANCH=test-verify-setup
cd ../worktrees/test-verify-setup
make setup && make build && make test
cd ../../main
make worktree-remove BRANCH=test-verify-setup
```

If verification fails, fix and re-test. Do NOT commit until it passes.

### 8. Commit

```bash
git add Makefile .worktree-setup.sh
git commit -m "chore: add worktree and build support for swarm"
```

### 9. Inform user
Inform user about success and provide them with a link to [references/user-guide.md](references/user-guide.md), where they can learn more about swarm.

## CLAUDE.md Minimum Sections

Example of the minimum required content:

```markdown
## Stack

- Language: Python 3.13
- Framework: FastAPI
- Database: PostgreSQL 16 with SQLAlchemy
- Package manager: pip
- Testing: pytest

## Testing Conventions

- Run all tests: `make test`
- Test location: `tests/` next to source
- Naming: `test_*.py`

## Code Quality Standards

- No hardcoded values — use environment variables or config
- No silent defaults — fail fast on missing required config
- Ruff for linting and formatting

## Project Structure

- `src/app/` — application code
- `src/lib/` — shared utilities
- `tests/` — test files
- New modules: register router in `src/app/main.py`
- New config vars: add to `.env.example`

## Config Management

- `.env` for secrets (never committed)
- `.env.example` as template (committed, no real values)
- All required vars validated at startup
```

## Stack Examples

### Python (pip + pytest)

**Makefile:**
```makefile
.PHONY: setup build test worktree worktree-remove sync-workspace

setup:
	bash .worktree-setup.sh

build:
	.venv/bin/python3 -m py_compile src/**/*.py

test:
	.venv/bin/python3 -m pytest tests/ -v

sync-workspace:
	@python3 -c "\
	import json, os, sys; \
	root = os.path.abspath('..'); \
	ws_name = os.path.basename(root) + '.code-workspace'; \
	ws_path = os.path.join(root, ws_name); \
	folders = [{'path': 'main', 'name': 'main'}]; \
	wt_dir = os.path.join(root, 'worktrees'); \
	[folders.append({'path': f'worktrees/{d}', 'name': d}) for d in sorted(os.listdir(wt_dir)) if os.path.isfile(os.path.join(wt_dir, d, '.git'))] if os.path.isdir(wt_dir) else None; \
	data = {}; \
	exec('try:\n with open(ws_path) as f: data=json.load(f)\nexcept FileNotFoundError: pass\nexcept json.JSONDecodeError as e: sys.exit(f\"Invalid JSON in {ws_path}: {e}\")'); \
	data['folders'] = folders; \
	data.setdefault('settings', {'search.exclude': {'**/.git': True, '**/.venv': True, '**/node_modules': True, '**/__pycache__': True}}); \
	open(ws_path, 'w').write(json.dumps(data, indent=2) + '\n'); \
	print(f'Synced {ws_name}: {len(folders)} folders')"

worktree:
	@test -n "$(BRANCH)" || (echo "Usage: make worktree BRANCH=<name>" && exit 1)
	git worktree add ../worktrees/$(BRANCH) -b $(BRANCH)
	cd ../worktrees/$(BRANCH) && bash .worktree-setup.sh
	@$(MAKE) sync-workspace

worktree-remove:
	@test -n "$(BRANCH)" || (echo "Usage: make worktree-remove BRANCH=<name>" && exit 1)
	git worktree remove ../worktrees/$(BRANCH)
	git branch -D $(BRANCH)
	@$(MAKE) sync-workspace
```

**.worktree-setup.sh:**
```bash
#!/bin/bash
set -e
ln -sf ../../main/.env .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Node.js (npm + vitest/jest)

**Makefile:**
```makefile
.PHONY: setup build test worktree worktree-remove sync-workspace

setup:
	bash .worktree-setup.sh

build:
	npm run build

test:
	npm test

sync-workspace:
	@python3 -c "\
	import json, os, sys; \
	root = os.path.abspath('..'); \
	ws_name = os.path.basename(root) + '.code-workspace'; \
	ws_path = os.path.join(root, ws_name); \
	folders = [{'path': 'main', 'name': 'main'}]; \
	wt_dir = os.path.join(root, 'worktrees'); \
	[folders.append({'path': f'worktrees/{d}', 'name': d}) for d in sorted(os.listdir(wt_dir)) if os.path.isfile(os.path.join(wt_dir, d, '.git'))] if os.path.isdir(wt_dir) else None; \
	data = {}; \
	exec('try:\n with open(ws_path) as f: data=json.load(f)\nexcept FileNotFoundError: pass\nexcept json.JSONDecodeError as e: sys.exit(f\"Invalid JSON in {ws_path}: {e}\")'); \
	data['folders'] = folders; \
	data.setdefault('settings', {'search.exclude': {'**/.git': True, '**/.venv': True, '**/node_modules': True, '**/__pycache__': True}}); \
	open(ws_path, 'w').write(json.dumps(data, indent=2) + '\n'); \
	print(f'Synced {ws_name}: {len(folders)} folders')"

worktree:
	@test -n "$(BRANCH)" || (echo "Usage: make worktree BRANCH=<name>" && exit 1)
	git worktree add ../worktrees/$(BRANCH) -b $(BRANCH)
	cd ../worktrees/$(BRANCH) && bash .worktree-setup.sh
	@$(MAKE) sync-workspace

worktree-remove:
	@test -n "$(BRANCH)" || (echo "Usage: make worktree-remove BRANCH=<name>" && exit 1)
	git worktree remove ../worktrees/$(BRANCH)
	git branch -D $(BRANCH)
	@$(MAKE) sync-workspace
```

**.worktree-setup.sh:**
```bash
#!/bin/bash
set -e
ln -sf ../../main/.env .env
ln -sf ../../main/.env.local .env.local
npm ci
npm run generate 2>/dev/null || true
```

### Go (go build + go test)

**Makefile:**
```makefile
.PHONY: setup build test worktree worktree-remove sync-workspace

setup:
	bash .worktree-setup.sh

build:
	go build ./...

test:
	go test ./... -v

sync-workspace:
	@python3 -c "\
	import json, os, sys; \
	root = os.path.abspath('..'); \
	ws_name = os.path.basename(root) + '.code-workspace'; \
	ws_path = os.path.join(root, ws_name); \
	folders = [{'path': 'main', 'name': 'main'}]; \
	wt_dir = os.path.join(root, 'worktrees'); \
	[folders.append({'path': f'worktrees/{d}', 'name': d}) for d in sorted(os.listdir(wt_dir)) if os.path.isfile(os.path.join(wt_dir, d, '.git'))] if os.path.isdir(wt_dir) else None; \
	data = {}; \
	exec('try:\n with open(ws_path) as f: data=json.load(f)\nexcept FileNotFoundError: pass\nexcept json.JSONDecodeError as e: sys.exit(f\"Invalid JSON in {ws_path}: {e}\")'); \
	data['folders'] = folders; \
	data.setdefault('settings', {'search.exclude': {'**/.git': True, '**/.venv': True, '**/node_modules': True, '**/__pycache__': True}}); \
	open(ws_path, 'w').write(json.dumps(data, indent=2) + '\n'); \
	print(f'Synced {ws_name}: {len(folders)} folders')"

worktree:
	@test -n "$(BRANCH)" || (echo "Usage: make worktree BRANCH=<name>" && exit 1)
	git worktree add ../worktrees/$(BRANCH) -b $(BRANCH)
	cd ../worktrees/$(BRANCH) && bash .worktree-setup.sh
	@$(MAKE) sync-workspace

worktree-remove:
	@test -n "$(BRANCH)" || (echo "Usage: make worktree-remove BRANCH=<name>" && exit 1)
	git worktree remove ../worktrees/$(BRANCH)
	git branch -D $(BRANCH)
	@$(MAKE) sync-workspace
```

**.worktree-setup.sh:**
```bash
#!/bin/bash
set -e
ln -sf ../../main/.env .env
go mod download
```

## Run-Mode Prerequisite Check

When running `/swarm` or `/swarm <plan-file>`, verify the project was initialized:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/swarm.py prereq <plan-file>
```

The script checks:
- CLI tools installed (gh, make, git worktree)
- Directory structure exists (main/, worktrees/)
- CLAUDE.md has required sections
- Makefile has required targets
- Remote origin configured
- Working tree clean

**If it fails and reports missing Makefile or directory structure:**

STOP and tell the user: "Project not initialized for swarm. Run `/swarm init` first."
