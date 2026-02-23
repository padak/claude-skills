# E2B Git Integration

## Table of Contents

- [Overview](#overview)
- [Authentication and Identity](#authentication-and-identity)
  - [Inline Credentials](#inline-credentials)
  - [Credential Helper (dangerouslyAuthenticate)](#credential-helper-dangerouslyauthenticate)
  - [Keep Credentials in Remote URL](#keep-credentials-in-remote-url)
  - [Configure Git Identity](#configure-git-identity)
- [Clone a Repository](#clone-a-repository)
- [Check Status and Branches](#check-status-and-branches)
- [Create and Manage Branches](#create-and-manage-branches)
- [Stage and Commit](#stage-and-commit)
- [Pull and Push](#pull-and-push)
- [Manage Remotes](#manage-remotes)
- [Git Config](#git-config)

## Overview

Use the `sandbox.git` methods to run common git operations inside an E2B sandbox. The API covers cloning, branching, staging, committing, pushing, pulling, remote management, and configuration.

## Authentication and Identity

### Inline Credentials

For private repositories over HTTPS, pass `username` and `password` (token) directly to commands that need authentication. A username is required whenever you pass a password/token.

**Python:**
```python
import os

repo_path = "/home/user/repo"

sandbox.git.push(
    repo_path,
    username=os.environ.get("GIT_USERNAME"),
    password=os.environ.get("GIT_TOKEN"),
)

sandbox.git.pull(
    repo_path,
    username=os.environ.get("GIT_USERNAME"),
    password=os.environ.get("GIT_TOKEN"),
)
```

**JavaScript/TypeScript:**
```javascript
const repoPath = '/home/user/repo'

await sandbox.git.push(repoPath, {
  username: process.env.GIT_USERNAME,
  password: process.env.GIT_TOKEN,
})

await sandbox.git.pull(repoPath, {
  username: process.env.GIT_USERNAME,
  password: process.env.GIT_TOKEN,
})
```

### Credential Helper (dangerouslyAuthenticate)

To avoid passing credentials on each command, store them in the git credential helper inside the sandbox using `dangerously_authenticate()` (Python) / `dangerouslyAuthenticate()` (JS/TS).

**WARNING:** This stores credentials on disk inside the sandbox. Any process or agent with access to the sandbox can read them. Use only when you understand the risk.

**Python:**
```python
import os

# Default (GitHub)
sandbox.git.dangerously_authenticate(
    username=os.environ.get("GIT_USERNAME"),
    password=os.environ.get("GIT_TOKEN"),
)

# Custom host (self-hosted)
sandbox.git.dangerously_authenticate(
    username=os.environ.get("GIT_USERNAME"),
    password=os.environ.get("GIT_TOKEN"),
    host="git.example.com",
    protocol="https",
)

# After this, HTTPS git operations use the stored credentials
sandbox.git.clone("https://git.example.com/org/repo.git", path="/home/user/repo")
sandbox.git.push("/home/user/repo")
```

**JavaScript/TypeScript:**
```javascript
// Default (GitHub)
await sandbox.git.dangerouslyAuthenticate({
  username: process.env.GIT_USERNAME,
  password: process.env.GIT_TOKEN,
})

// Custom host (self-hosted)
await sandbox.git.dangerouslyAuthenticate({
  username: process.env.GIT_USERNAME,
  password: process.env.GIT_TOKEN,
  host: 'git.example.com',
  protocol: 'https',
})

// After this, HTTPS git operations use the stored credentials
await sandbox.git.clone('https://git.example.com/org/repo.git', { path: '/home/user/repo' })
await sandbox.git.push('/home/user/repo')
```

### Keep Credentials in Remote URL

By default, credentials are stripped from the remote URL after cloning. To keep credentials in the remote URL (stored in `.git/config`), set `dangerously_store_credentials` (Python) / `dangerouslyStoreCredentials` (JS/TS).

**WARNING:** Storing credentials in the remote URL persists them in the repo config. Any process or agent with access to the sandbox can read them. Only use this when required.

**Python:**
```python
import os

# Default: credentials are stripped from the remote URL
sandbox.git.clone(
    "https://git.example.com/org/repo.git",
    path="/home/user/repo",
    username=os.environ.get("GIT_USERNAME"),
    password=os.environ.get("GIT_TOKEN"),
)

# Keep credentials in the remote URL
sandbox.git.clone(
    "https://git.example.com/org/repo.git",
    path="/home/user/repo",
    username=os.environ.get("GIT_USERNAME"),
    password=os.environ.get("GIT_TOKEN"),
    dangerously_store_credentials=True,
)
```

**JavaScript/TypeScript:**
```javascript
// Default: credentials are stripped from the remote URL
await sandbox.git.clone('https://git.example.com/org/repo.git', {
  path: '/home/user/repo',
  username: process.env.GIT_USERNAME,
  password: process.env.GIT_TOKEN,
})

// Keep credentials in the remote URL
await sandbox.git.clone('https://git.example.com/org/repo.git', {
  path: '/home/user/repo',
  username: process.env.GIT_USERNAME,
  password: process.env.GIT_TOKEN,
  dangerouslyStoreCredentials: true,
})
```

### Configure Git Identity

Set the git author name and email for commits. Configure globally or per-repository.

**Python:**
```python
repo_path = "/home/user/repo"

# Global config
sandbox.git.configure_user("E2B Bot", "bot@example.com")

# Repo-local config
sandbox.git.configure_user(
    "E2B Bot",
    "bot@example.com",
    scope="local",
    path=repo_path
)
```

**JavaScript/TypeScript:**
```javascript
const repoPath = '/home/user/repo'

// Global config
await sandbox.git.configureUser('E2B Bot', 'bot@example.com')

// Repo-local config
await sandbox.git.configureUser('E2B Bot', 'bot@example.com', {
  scope: 'local',
  path: repoPath
})
```

## Clone a Repository

Clone a repository into the sandbox. Supports branch selection and shallow clones. For private repos, see [Authentication and Identity](#authentication-and-identity).

**Python:**
```python
repo_url = "https://git.example.com/org/repo.git"
repo_path = "/home/user/repo"

# Default clone
sandbox.git.clone(repo_url, path=repo_path)

# Clone a specific branch
sandbox.git.clone(repo_url, path=repo_path, branch="main")

# Shallow clone
sandbox.git.clone(repo_url, path=repo_path, depth=1)
```

**JavaScript/TypeScript:**
```javascript
const repoUrl = 'https://git.example.com/org/repo.git'
const repoPath = '/home/user/repo'

// Default clone
await sandbox.git.clone(repoUrl, { path: repoPath })

// Clone a specific branch
await sandbox.git.clone(repoUrl, { path: repoPath, branch: 'main' })

// Shallow clone
await sandbox.git.clone(repoUrl, { path: repoPath, depth: 1 })
```

## Check Status and Branches

`status()` returns a structured object with branch name, ahead/behind counts, and file status details. `branches()` returns the branch list and the current branch.

**Python:**
```python
repo_path = "/home/user/repo"

status = sandbox.git.status(repo_path)
print(status.current_branch, status.ahead, status.behind)
print(status.file_status)

branches = sandbox.git.branches(repo_path)
print(branches.current_branch)
print(branches.branches)
```

**JavaScript/TypeScript:**
```javascript
const repoPath = '/home/user/repo'

const status = await sandbox.git.status(repoPath)
console.log(status.currentBranch, status.ahead, status.behind)
console.log(status.fileStatus)

const branches = await sandbox.git.branches(repoPath)
console.log(branches.currentBranch)
console.log(branches.branches)
```

## Create and Manage Branches

Create new branches, check out existing branches, and delete branches (with optional force delete).

**Python:**
```python
repo_path = "/home/user/repo"

# Create and switch to a new branch
sandbox.git.create_branch(repo_path, "feature/new-docs")

# Check out an existing branch
sandbox.git.checkout_branch(repo_path, "main")

# Delete a branch
sandbox.git.delete_branch(repo_path, "feature/old-docs")

# Force delete a branch
sandbox.git.delete_branch(repo_path, "feature/stale-docs", force=True)
```

**JavaScript/TypeScript:**
```javascript
const repoPath = '/home/user/repo'

// Create and switch to a new branch
await sandbox.git.createBranch(repoPath, 'feature/new-docs')

// Check out an existing branch
await sandbox.git.checkoutBranch(repoPath, 'main')

// Delete a branch
await sandbox.git.deleteBranch(repoPath, 'feature/old-docs')

// Force delete a branch
await sandbox.git.deleteBranch(repoPath, 'feature/stale-docs', { force: true })
```

## Stage and Commit

Stage files and create commits. By default, `add()` stages all changes. You can stage specific files. Commits support overriding author info and allowing empty commits.

**Python:**
```python
repo_path = "/home/user/repo"

# Default: stage all changes, commit with repo config
sandbox.git.add(repo_path)
sandbox.git.commit(repo_path, "Initial commit")

# Stage specific files
sandbox.git.add(repo_path, files=["README.md", "src/index.ts"])

# Allow empty commit and override author
sandbox.git.commit(
    repo_path,
    "Docs sync",
    author_name="E2B Bot",
    author_email="bot@example.com",
    allow_empty=True,
)
```

**JavaScript/TypeScript:**
```javascript
const repoPath = '/home/user/repo'

// Default: stage all changes, commit with repo config
await sandbox.git.add(repoPath)
await sandbox.git.commit(repoPath, 'Initial commit')

// Stage specific files
await sandbox.git.add(repoPath, { files: ['README.md', 'src/index.ts'] })

// Allow empty commit and override author
await sandbox.git.commit(repoPath, 'Docs sync', {
  authorName: 'E2B Bot',
  authorEmail: 'bot@example.com',
  allowEmpty: true,
})
```

## Pull and Push

Push to and pull from remote repositories. By default, uses the configured upstream. You can specify a remote, branch, and set upstream tracking. For authentication, see [Authentication and Identity](#authentication-and-identity).

**Python:**
```python
repo_path = "/home/user/repo"

# Default (uses upstream when set)
sandbox.git.push(repo_path)
sandbox.git.pull(repo_path)

# Target a specific remote/branch and set upstream
sandbox.git.push(
    repo_path,
    remote="origin",
    branch="main",
    set_upstream=True,
)

sandbox.git.pull(
    repo_path,
    remote="origin",
    branch="main",
)
```

**JavaScript/TypeScript:**
```javascript
const repoPath = '/home/user/repo'

// Default (uses upstream when set)
await sandbox.git.push(repoPath)
await sandbox.git.pull(repoPath)

// Target a specific remote/branch and set upstream
await sandbox.git.push(repoPath, {
  remote: 'origin',
  branch: 'main',
  setUpstream: true,
})

await sandbox.git.pull(repoPath, {
  remote: 'origin',
  branch: 'main',
})
```

## Manage Remotes

Add remotes with optional fetch-after-add and overwrite behavior.

**Python:**
```python
repo_path = "/home/user/repo"
repo_url = "https://git.example.com/org/repo.git"

# Default
sandbox.git.remote_add(repo_path, "origin", repo_url)

# Fetch after adding the remote
sandbox.git.remote_add(repo_path, "origin", repo_url, fetch=True)

# Overwrite the remote URL if it already exists
sandbox.git.remote_add(repo_path, "origin", repo_url, overwrite=True)
```

**JavaScript/TypeScript:**
```javascript
const repoPath = '/home/user/repo'
const repoUrl = 'https://git.example.com/org/repo.git'

// Default
await sandbox.git.remoteAdd(repoPath, 'origin', repoUrl)

// Fetch after adding the remote
await sandbox.git.remoteAdd(repoPath, 'origin', repoUrl, { fetch: true })

// Overwrite the remote URL if it already exists
await sandbox.git.remoteAdd(repoPath, 'origin', repoUrl, { overwrite: true })
```

## Git Config

Set and get git configuration values. Supports both global and repo-local scope. For configuring commit author, see [Configure Git Identity](#configure-git-identity).

**Python:**
```python
repo_path = "/home/user/repo"

# Global config
sandbox.git.set_config("pull.rebase", "false")
rebase = sandbox.git.get_config("pull.rebase")

# Repo-local config
sandbox.git.set_config("pull.rebase", "false", scope="local", path=repo_path)
local_rebase = sandbox.git.get_config("pull.rebase", scope="local", path=repo_path)
```

**JavaScript/TypeScript:**
```javascript
const repoPath = '/home/user/repo'

// Global config
await sandbox.git.setConfig('pull.rebase', 'false')
const rebase = await sandbox.git.getConfig('pull.rebase')

// Repo-local config
await sandbox.git.setConfig('pull.rebase', 'false', { scope: 'local', path: repoPath })
const localRebase = await sandbox.git.getConfig('pull.rebase', { scope: 'local', path: repoPath })
```

## API Method Summary

| Operation | Python | JavaScript/TypeScript |
|---|---|---|
| Clone | `sandbox.git.clone(url, path=...)` | `sandbox.git.clone(url, { path })` |
| Status | `sandbox.git.status(path)` | `sandbox.git.status(path)` |
| Branches | `sandbox.git.branches(path)` | `sandbox.git.branches(path)` |
| Create branch | `sandbox.git.create_branch(path, name)` | `sandbox.git.createBranch(path, name)` |
| Checkout branch | `sandbox.git.checkout_branch(path, name)` | `sandbox.git.checkoutBranch(path, name)` |
| Delete branch | `sandbox.git.delete_branch(path, name)` | `sandbox.git.deleteBranch(path, name)` |
| Add/stage | `sandbox.git.add(path)` | `sandbox.git.add(path)` |
| Commit | `sandbox.git.commit(path, message)` | `sandbox.git.commit(path, message)` |
| Push | `sandbox.git.push(path)` | `sandbox.git.push(path)` |
| Pull | `sandbox.git.pull(path)` | `sandbox.git.pull(path)` |
| Add remote | `sandbox.git.remote_add(path, name, url)` | `sandbox.git.remoteAdd(path, name, url)` |
| Set config | `sandbox.git.set_config(key, value)` | `sandbox.git.setConfig(key, value)` |
| Get config | `sandbox.git.get_config(key)` | `sandbox.git.getConfig(key)` |
| Configure user | `sandbox.git.configure_user(name, email)` | `sandbox.git.configureUser(name, email)` |
| Authenticate | `sandbox.git.dangerously_authenticate(...)` | `sandbox.git.dangerouslyAuthenticate(...)` |
