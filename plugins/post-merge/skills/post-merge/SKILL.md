---
name: post-merge
description: "Post-merge cleanup after a PR is merged on GitHub. Works from a regular checkout AND from a git worktree (e.g. Claude Code .claude/worktrees). Syncs main, removes the merged worktree and branch, and watches CI/CD. Triggers: /post-merge, 'I merged the PR', 'PR is merged', 'cleanup after merge'."
---

# Post-Merge Cleanup

Run this after a PR has been merged on GitHub to sync local state and watch CI/CD.

Sessions often run inside a **git worktree** (Claude Code creates them under
`.claude/worktrees/<name>` with branches named `claude/<name>`). A worktree can
NEVER `git checkout main` — main is already checked out in the primary
checkout (`fatal: 'main' is already used by worktree at ...`). This skill
detects the environment first and never switches branches inside a worktree.

## Arguments

- `/post-merge` - Auto-detect the merged branch (current branch/worktree, or most recently merged PR)
- `/post-merge <branch-name>` - Specify the branch to clean up
- `/post-merge <pr-number>` - Specify the PR number

## Workflow

### Step 0: Detect environment (ALWAYS FIRST)

```bash
# Primary checkout path (first entry of worktree list is always the main checkout)
MAIN_WT=$(git worktree list --porcelain | head -1 | sed 's/^worktree //')

# Are we inside a linked worktree? (paths differ only in a worktree)
GIT_DIR=$(git rev-parse --git-dir)
COMMON_DIR=$(git rev-parse --git-common-dir)
if [ "$GIT_DIR" != "$COMMON_DIR" ]; then IN_WORKTREE=1; WT_PATH=$(git rev-parse --show-toplevel); fi

# Default branch without a network round-trip (fallback to remote show origin)
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD --short 2>/dev/null | sed 's|origin/||')
[ -z "$DEFAULT_BRANCH" ] && DEFAULT_BRANCH=$(git remote show origin | grep 'HEAD branch' | awk '{print $NF}')
```

From here on, **every command that touches the default branch runs against the
primary checkout via `git -C "$MAIN_WT"`** — never via `git checkout`.

### Step 1: Identify the merged branch

If a branch name or PR number was given as argument, use that. Otherwise:

```bash
BRANCH=$(git branch --show-current)

# On main already (primary checkout, nothing to infer) -> most recently merged PR
if [ "$BRANCH" = "$DEFAULT_BRANCH" ]; then
  gh pr list --state merged --limit 1 --json number,headRefName,mergedAt
fi

# Confirm the PR for this branch is actually merged before deleting anything
gh pr view "$BRANCH" --json state,mergedAt 2>/dev/null
```

If the PR is not merged (state is OPEN or CLOSED without mergedAt), STOP and
tell the user — do not delete anything.

### Step 2: Sync the default branch

```bash
git -C "$MAIN_WT" pull origin "$DEFAULT_BRANCH"
```

In a regular checkout (not a worktree, on a feature branch) it is fine to
switch first: `git checkout "$DEFAULT_BRANCH" && git pull`.

### Step 3: Remove the worktree (worktree path only)

Skip this step when not in a worktree.

```bash
# Refuse to destroy uncommitted work — check the worktree is clean first
git -C "$WT_PATH" status --porcelain

# Remove the worktree, then its branch
git -C "$MAIN_WT" worktree remove "$WT_PATH"
git -C "$MAIN_WT" branch -d "$BRANCH"
git -C "$MAIN_WT" remote prune origin
```

Gotchas:

- **The current directory vanishes** after `worktree remove`. Any later shell
  command must not rely on the old cwd — keep using absolute paths and
  `git -C "$MAIN_WT" ...` for everything after removal.
- If `worktree remove` refuses because of modified/untracked files, show the
  files and ASK the user before using `--force`. Never `--force` on your own.
- If `branch -d` complains the branch "is used by worktree", run
  `git -C "$MAIN_WT" worktree prune` first, then retry.

### Step 3b: Delete the merged branch (regular checkout path)

```bash
git branch -d "$BRANCH"
git remote prune origin
```

If `git branch -d` fails (branch not fully merged), warn the user instead of
force-deleting. Never use `git branch -D` without asking. Note: after a
**squash merge** the local branch is never "fully merged" in git's eyes — if
the PR is confirmed merged on GitHub (Step 1), it is safe to ask the user and
use `-D`.

### Step 4: Watch CI/CD

```bash
gh run list --branch "$DEFAULT_BRANCH" --limit 5 --json status,conclusion,name,databaseId,createdAt,headSha

# If any run is in_progress or queued, watch it
gh run watch <run-id>
```

Report the CI/CD status:
- All checks pass: confirm everything is green
- Still running: show progress and wait
- Checks fail: show which checks failed and link to the run

### Step 5: Summary

```
Post-merge cleanup complete:
- Synced: main (<commit-count> new commits)
- Removed worktree: .claude/worktrees/xyz   (worktree path only)
- Deleted branch: claude/xyz
- CI/CD: all checks passed (or status)
```

## Error Handling

- **Uncommitted changes in the worktree/branch:** Stop, show `git status`, ask
  the user (stash, commit, or discard) before any removal
- **PR not merged yet:** Stop — this skill only runs AFTER the merge
- **Branch/worktree already deleted:** Skip deletion, continue with pull and CI watch
- **No CI runs found:** Report that no workflows were triggered
- **CI timeout:** After 10 minutes of watching, stop and provide a link to check manually
