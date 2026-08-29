# Custom Templates

Custom templates allow you to create pre-configured sandbox environments with pre-installed packages, running services, and custom configurations. Templates dramatically reduce sandbox startup time by snapshotting ready-to-use environments.

## Table of Contents

1. [Overview](#overview)
2. [Build System 2.0 (Recommended)](#build-system-20-recommended)
3. [Defining a Template](#defining-a-template)
4. [Base Images](#base-images)
5. [Template Builder Methods](#template-builder-methods)
6. [Start and Ready Commands](#start-and-ready-commands)
7. [Building Templates](#building-templates)
8. [Tags and Versioning](#tags-and-versioning)
9. [Layer Caching](#layer-caching)
10. [Template Names](#template-names)
11. [Build Logging](#build-logging)
12. [Error Handling](#error-handling)
13. [Private Registries](#private-registries)
14. [Migration from Legacy System](#migration-from-legacy-system)
15. [Examples](#examples)
16. [Best Practices](#best-practices)
17. [Troubleshooting](#troubleshooting)

## Overview

### What Are Templates

Templates are pre-configured sandbox snapshots that include:

- **Pre-installed packages** - Python packages (pip), Node.js packages (npm), Bun packages, system packages (apt)
- **Running services** - Pre-started servers, databases, or background processes
- **Custom configurations** - Environment variables, file system setup, runtime settings
- **Resource allocation** - Custom CPU and RAM configurations

Templates enable:
- **Fast sandbox startup** - Load pre-configured environments in ~80ms
- **Consistent environments** - Same configuration across all sandbox instances
- **Reduced runtime overhead** - No package installation delays during execution
- **Complex setups** - Pre-configured development environments with multiple services

### How Templates Work

Every time you build a sandbox template:
1. A container is created based on the definition
2. The container's filesystem is extracted, provisioned, and configured
3. Layer commands are executed (install packages, copy files, run commands)
4. If a start command is specified, it executes and the system waits for readiness
5. The sandbox is snapshotted (filesystem + all running processes serialized)
6. The snapshot becomes your template, loadable in ~80ms with everything running

### Default User and Workdir

- **Default user:** `user` (non-root, different from Docker's default `root`)
- **Default workdir:** `/home/user` (the user's home directory)
- The last set user and workdir in the template definition persist as defaults for sandbox execution

### Kernel

E2B sandboxes run on an LTS 6.1 Linux kernel. The kernel version is fixed at template build time. Templates built on or after 27.11.2025 use kernel 6.1.158. Older templates use 6.1.102. To use a newer kernel, rebuild the template.

## Build System 2.0 (Recommended)

Build System 2.0 uses a fluent programmatic API (TypeScript/Python) to define and build templates. This is the recommended approach for all new templates.

### Quickstart

#### 1. Install E2B SDK

```bash
# TypeScript
npm install e2b dotenv

# Python
pip install e2b dotenv
```

Create a `.env` file:

```
E2B_API_KEY=e2b_***
```

#### 2. Define Your Template

```typescript
// template.ts
import { Template, waitForTimeout } from 'e2b';

export const template = Template()
  .fromBaseImage()
  .setEnvs({
    HELLO: "Hello, World!",
  })
  .setStartCmd("echo $HELLO", waitForTimeout(5_000));
```

```python
# template.py
from e2b import Template, wait_for_timeout

template = (
    Template()
    .from_base_image()
    .set_envs(
        {
            "HELLO": "Hello, World!",
        }
    )
    .set_start_cmd("echo $HELLO", wait_for_timeout(5_000)))
```

#### 3. Create Build Scripts

Development build script:

```typescript
// build.dev.ts
import 'dotenv/config';
import { Template, defaultBuildLogger } from 'e2b';
import { template } from './template';

async function main() {
  await Template.build(template, 'template-tag-dev', {
    cpuCount: 1,
    memoryMB: 1024,
    onBuildLogs: defaultBuildLogger(),
  });
}

main().catch(console.error);
```

```python
# build_dev.py
from dotenv import load_dotenv
from e2b import Template, default_build_logger
from template import template

load_dotenv()

if __name__ == '__main__':
    Template.build(
        template,
        'template-tag-dev',
        cpu_count=1,
        memory_mb=1024,
        on_build_logs=default_build_logger(),
    )
```

Production build script:

```typescript
// build.prod.ts
import 'dotenv/config';
import { Template, defaultBuildLogger } from 'e2b';
import { template } from './template';

async function main() {
  await Template.build(template, 'template-tag', {
    cpuCount: 1,
    memoryMB: 1024,
    onBuildLogs: defaultBuildLogger(),
  });
}

main().catch(console.error);
```

```python
# build_prod.py
from dotenv import load_dotenv
from e2b import Template, default_build_logger
from template import template

load_dotenv()

if __name__ == '__main__':
    Template.build(
        template,
        'template-tag',
        cpu_count=1,
        memory_mb=1024,
        on_build_logs=default_build_logger(),
    )
```

#### 4. Build the Template

```bash
# TypeScript - Development
npx tsx build.dev.ts

# TypeScript - Production
npx tsx build.prod.ts

# Python - Development
python build_dev.py

# Python - Production
python build_prod.py
```

#### 5. Use Your Custom Template

```typescript
import 'dotenv/config';
import { Sandbox } from 'e2b';

// Create a Sandbox from development template
const sandbox = await Sandbox.create("template-tag-dev");

// Create a Sandbox from production template
const sandbox = await Sandbox.create("template-tag");
```

```python
from dotenv import load_dotenv
from e2b import Sandbox

load_dotenv()

# Create a new Sandbox from the development template
sbx = Sandbox(template="template-tag-dev")

# Create a new Sandbox from the production template
sbx = Sandbox(template="template-tag")
```

## Defining a Template

### Template Constructor Options

When creating a template, you can specify file context options:

```typescript
const template = Template({
  fileContextPath: ".",  // Custom file context path
  fileIgnorePatterns: [".git", "node_modules"],  // File patterns to ignore
});
```

```python
template = Template(
    file_context_path=".",  # Custom file context path
    file_ignore_patterns=[".git", "node_modules"],  # File patterns to ignore
)
```

The SDK automatically reads `.dockerignore` files and combines them with your ignore patterns. Files matching these patterns are excluded from uploads and hash calculations.

### Method Chaining

All template methods return the template instance, allowing for fluent API usage:

```typescript
const template = Template()
  .fromUbuntuImage("22.04")
  .aptInstall(["curl"])
  .setWorkdir('/app')
  .copy("package.json", "/app/package.json")
  .runCmd("npm install")
  .setStartCmd("npm start", waitForPort(3000));
```

```python
template = (
    Template()
    .from_ubuntu_image("22.04")
    .set_workdir("/app")
    .copy("package.json", "/app/package.json")
    .run_cmd("npm install")
    .set_start_cmd("npm start", wait_for_timeout(10_000)))
```

## Base Images

Every template starts with a base image. You can only call a base image method once per template.

### Predefined Base Images

Convenience methods for common base images:

```typescript
template.fromUbuntuImage("22.04");       // ubuntu:22.04
template.fromDebianImage("stable-slim"); // debian:stable-slim
template.fromPythonImage("3.13");        // python:3.13
template.fromNodeImage("lts");           // node:lts
template.fromBunImage("1.3");            // oven/bun:1.3
```

```python
template.from_ubuntu_image("22.04")       # ubuntu:22.04
template.from_debian_image("stable-slim") # debian:stable-slim
template.from_python_image("3.13")        # python:3.13
template.from_node_image("lts")           # node:lts
template.from_bun_image("1.3")            # oven/bun:1.3
```

### Default E2B Base Image

Pre-configured for sandbox environments:

```typescript
template.fromBaseImage(); // e2bdev/base
```

```python
template.from_base_image()  # e2bdev/base
```

### Custom Docker Image

Use any Docker image from Docker Hub or other registries:

```typescript
template.fromImage("custom-image:latest");
```

```python
template.from_image("custom-image:latest")
```

### Build from Existing Template

Extend an existing template from your team or organization:

```typescript
template.fromTemplate("my-template");           // Your team's template
template.fromTemplate("acme/other-template");   // Full namespaced reference
```

```python
template.from_template("my-template")           # Your team's template
template.from_template("acme/other-template")   # Full namespaced reference
```

### Parse Existing Dockerfile

Convert existing Dockerfiles to template format using `fromDockerfile()`:

```typescript
const dockerfileContent = `
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y curl
WORKDIR /app
COPY . .
ENV NODE_ENV=production
ENV PORT=3000
USER appuser`;

const template = Template()
  .fromDockerfile(dockerfileContent)
  .setStartCmd("npm start", waitForTimeout(5_000));
```

```python
dockerfile_content = """
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y curl
WORKDIR /app
COPY . .
ENV NODE_ENV=production
ENV PORT=3000
USER appuser
"""

template = (
    Template()
    .from_dockerfile(dockerfile_content)
    .set_start_cmd("npm start", wait_for_timeout(5_000))
)
```

**Supported Dockerfile instructions:**

| Instruction | Supported | Behavior |
|-------------|-----------|----------|
| `FROM` | Yes | Sets base image |
| `RUN` | Yes | Converts to `runCmd()` / `run_cmd()` |
| `COPY` / `ADD` | Yes | Converts to `copy()` |
| `WORKDIR` | Yes | Converts to `setWorkdir()` / `set_workdir()` |
| `USER` | Yes | Converts to `setUser()` / `set_user()` |
| `ENV` | Yes | Converts to `setEnvs()` / `set_envs()` (both `ENV key=value` and `ENV key value` formats) |
| `CMD` / `ENTRYPOINT` | Yes | Converts to `setStartCmd()` / `set_start_cmd()` with 20s timeout as ready command |
| `EXPOSE` | No | Skipped |
| `VOLUME` | No | Skipped |

Multi-stage Dockerfiles are NOT supported.

## Template Builder Methods

### Complete Method Reference

| Method (TypeScript) | Method (Python) | Description |
|---------------------|-----------------|-------------|
| `fromUbuntuImage(tag)` | `from_ubuntu_image(tag)` | Start from Ubuntu base image |
| `fromDebianImage(tag)` | `from_debian_image(tag)` | Start from Debian base image |
| `fromPythonImage(tag)` | `from_python_image(tag)` | Start from Python base image |
| `fromNodeImage(tag)` | `from_node_image(tag)` | Start from Node.js base image |
| `fromBunImage(tag)` | `from_bun_image(tag)` | Start from Bun base image |
| `fromImage(image)` | `from_image(image)` | Start from any Docker image |
| `fromBaseImage()` | `from_base_image()` | Start from default E2B base image |
| `fromTemplate(name)` | `from_template(name)` | Extend an existing template |
| `fromDockerfile(content)` | `from_dockerfile(content)` | Parse a Dockerfile string |
| `aptInstall(packages)` | `apt_install(packages)` | Install system packages (auto runs apt update) |
| `pipInstall(packages, opts?)` | `pip_install(packages, **opts)` | Install Python packages |
| `npmInstall(packages, opts?)` | `npm_install(packages, **opts)` | Install Node.js packages |
| `bunInstall(packages, opts?)` | `bun_install(packages, **opts)` | Install Bun packages |
| `gitClone(url, path?, opts?)` | `git_clone(url, path?, **opts)` | Clone a git repository |
| `copy(src, dest, opts?)` | `copy(src, dest, **opts)` | Copy files from local filesystem |
| `copyItems(items)` | `copy_items(items)` | Copy multiple file mappings |
| `remove(path, opts?)` | `remove(path, **opts)` | Remove files or directories |
| `rename(old, new, opts?)` | `rename(old, new, **opts)` | Rename files or directories |
| `makeDir(path, opts?)` | `make_dir(path, **opts)` | Create directories |
| `makeSymlink(target, link)` | `make_symlink(target, link)` | Create symbolic links |
| `runCmd(cmd, opts?)` | `run_cmd(cmd, **opts)` | Execute shell commands |
| `setEnvs(envs)` | `set_envs(envs)` | Set environment variables (build-time only) |
| `setStartCmd(cmd, readyCmd)` | `set_start_cmd(cmd, ready_cmd)` | Set startup command with readiness check |
| `setWorkdir(path)` | `set_workdir(path)` | Set working directory |
| `setUser(user)` | `set_user(user)` | Set the user for subsequent commands |
| `skipCache()` | `skip_cache()` | Invalidate cache from this point forward |

### Installing Packages

```typescript
// System packages (automatically runs apt update)
template.aptInstall(['curl', 'wget', 'git'])

// Python packages (global by default)
template.pipInstall(['requests', 'pandas', 'numpy'])

// Python packages (user install)
template.pipInstall(['requests', 'pandas', 'numpy'], { g: false })

// Node.js packages (local by default)
template.npmInstall(['express', 'lodash'])

// Node.js packages (global)
template.npmInstall(['express', 'lodash'], { g: true })

// Bun packages (local by default)
template.bunInstall(['express', 'lodash'])

// Bun packages (global)
template.bunInstall(['express', 'lodash'], { g: true })
```

```python
# System packages (automatically runs apt update)
template.apt_install(["curl", "wget", "git"])

# Python packages (global by default)
template.pip_install(["requests", "pandas", "numpy"])

# Python packages (user install)
template.pip_install(["requests", "pandas", "numpy"], g=False)

# Node.js packages (local by default)
template.npm_install(["express", "lodash"])

# Node.js packages (global)
template.npm_install(["express", "lodash"], g=True)

# Bun packages (local by default)
template.bun_install(["express", "lodash"])

# Bun packages (global)
template.bun_install(["express", "lodash"], g=True)
```

### Copying Files

```typescript
// Copy a single file
template.copy("package.json", "/app/package.json");

// Copy multiple files to same destination
template.copy(["file1", "file2"], "/app/file")

// Multiple copy operations using copyItems
template.copyItems([
  { src: "src/", dest: "/app/src/" },
  { src: "package.json", dest: "/app/package.json" },
]);

// Copy with user and mode options
template.copy("config.json", "/app/config.json", {
  user: "appuser",
  mode: 0o644,
});

// Force upload (invalidates file cache)
template.copy("config.json", "/app/config.json", { forceUpload: true });
```

```python
# Copy a single file
template.copy("package.json", "/app/package.json")

# Copy multiple files to the same destination
template.copy(["file1", "file2"], "/app/file")

# Multiple copy operations using copy_items
template.copy_items([
    {"src": "src/", "dest": "/app/src/"},
    {"src": "package.json", "dest": "/app/package.json"},
])

# Copy with user and mode options
template.copy("config.json", "/app/config.json", user="appuser", mode=0o644)

# Force upload (invalidates file cache)
template.copy("config.json", "/app/config.json", force_upload=True)
```

### File Operations

```typescript
// Remove files or directories
template.remove("/tmp/temp-file.txt");
template.remove("/old-directory", { recursive: true });
template.remove("/file.txt", { force: true });

// Rename files or directories
template.rename("/old-name.txt", "/new-name.txt");
template.rename("/old-dir", "/new-dir", { force: true });

// Create directories
template.makeDir("/app/logs");
template.makeDir("/app/data", { mode: 0o755 });

// Create symbolic links
template.makeSymlink("/app/data", "/app/logs/data");
```

```python
# Remove files or directories
template.remove("/tmp/old-file")
template.remove("/tmp/old-dir", recursive=True)
template.remove("/tmp/file", force=True)

# Rename files or directories
template.rename("/old/path", "/new/path")
template.rename("/old/path", "/new/path", force=True)

# Create directories
template.make_dir("/app/data")
template.make_dir("/app/data", mode=0o755)

# Create symbolic links
template.make_symlink("/path/to/target", "/path/to/link")
```

### Git Operations

Requires `git` to be installed in the template:

```typescript
// Clone a repository
template.gitClone('https://github.com/user/repo.git')

// Clone to a specific path
template.gitClone('https://github.com/user/repo.git', '/app/repo')

// Clone a specific branch
template.gitClone('https://github.com/user/repo.git', '/app/repo', {
  branch: 'main',
})

// Shallow clone with depth limit
template.gitClone('https://github.com/user/repo.git', '/app/repo', {
  depth: 1,
})
```

```python
# Clone a repository
template.git_clone("https://github.com/user/repo.git")

# Clone to a specific path
template.git_clone("https://github.com/user/repo.git", "/app/repo")

# Clone a specific branch
template.git_clone("https://github.com/user/repo.git", "/app/repo", branch="main")

# Shallow clone with depth limit
template.git_clone("https://github.com/user/repo.git", "/app/repo", depth=1)
```

### Running Commands

```typescript
// Run a single command
template.runCmd('apt-get update && apt-get install -y curl')

// Run multiple commands
template.runCmd(['apt-get update', 'apt-get install -y curl', 'curl --version'])

// Run commands as a specific user
template.runCmd('npm install', { user: 'node' })
```

```python
# Run a single command
template.run_cmd("apt-get update && apt-get install -y curl")

# Run multiple commands
template.run_cmd(["apt-get update", "apt-get install -y curl", "curl --version"])

# Run command as specific user
template.run_cmd("npm install", user="node")
```

### Environment Variables

Environment variables set in the template definition are only available during template build, NOT at sandbox runtime. Use sandbox environment variables for runtime configuration.

```typescript
template.setEnvs({
  NODE_ENV: 'production',
  API_KEY: 'your-api-key',
  DEBUG: 'true',
})
```

```python
template.set_envs({
    "NODE_ENV": "production",
    "API_KEY": "your-api-key",
    "DEBUG": "true",
})
```

### User and Working Directory

```typescript
// Set working directory
template.setWorkdir("/app");

// Set user (runs subsequent commands as this user)
template.setUser('node')
template.setUser("1000:1000"); // User ID and group ID
```

```python
# Set working directory
template.set_workdir("/app")

# Set user (runs subsequent commands as this user)
template.set_user("node")
template.set_user("1000:1000")  # User ID and group ID
```

The last set user and workdir persist to the sandbox:

```typescript
const template = Template()
  .fromBaseImage()
  .runCmd("whoami") // user
  .runCmd("pwd")    // /home/user
  .setUser("guest")
  .runCmd("whoami") // guest
  .runCmd("pwd")    // /home/guest

// After build, sandbox will default to user "guest" with workdir "/home/guest"
```

## Start and Ready Commands

### Start Command

The start command specifies a process that will be **already running** when you spawn the sandbox. Use it for servers, databases, or background processes that should be ready with zero wait time.

### Ready Command

The ready command determines when the template sandbox is ready for snapshotting. It runs in an infinite loop until it returns exit code 0.

### Usage

```typescript
// Set start command with a port-based ready check
template.setStartCmd('npm start', waitForPort(3000))

// Set start command with a custom ready command string
template.setStartCmd('npm start', 'curl -s -o /dev/null -w "200"')

// Set only a ready command (no start command)
template.setReadyCmd(waitForTimeout(10_000))
```

```python
# Set start command with a port-based ready check
template.set_start_cmd("npm start", wait_for_port(3000))

# Set start command with a custom ready command string
template.set_start_cmd("npm start", 'curl -s -o /dev/null -w "200"')

# Set only a ready command (no start command)
template.set_ready_cmd(wait_for_timeout(10_000))
```

### Ready Command Helpers

The SDK provides helper functions for common readiness patterns:

```typescript
import {
  waitForPort,
  waitForProcess,
  waitForFile,
  waitForTimeout,
  waitForURL,
} from 'e2b'

waitForPort(3000)            // Wait for a port to be available
waitForProcess('node')       // Wait for a process to be running
waitForFile('/tmp/ready')    // Wait for a file to exist
waitForTimeout(10_000)       // Wait for a specified duration (ms)
waitForURL('http://localhost:3000')  // Wait for a URL to respond
```

```python
from e2b import wait_for_port, wait_for_process, wait_for_file, wait_for_timeout, wait_for_url

wait_for_port(3000)            # Wait for a port to be available
wait_for_process("node")       # Wait for a process to be running
wait_for_file("/tmp/ready")    # Wait for a file to exist
wait_for_timeout(10_000)       # Wait for a specified duration (ms)
wait_for_url('http://localhost:3000')  # Wait for a URL to respond
```

## Building Templates

### Build and Wait for Completion

The `build` method builds the template and waits for the build to complete. Returns build information including the template ID and build ID.

```typescript
const buildInfo = await Template.build(template, 'my-template', {
  cpuCount: 2,                         // CPU cores
  memoryMB: 2048,                      // Memory in MB
  skipCache: false,                    // Skip cache (except for files)
  onBuildLogs: defaultBuildLogger(),   // Log callback
  apiKey: 'your-api-key',             // Override API key
  domain: 'your-domain',              // Override domain
  tags: ['v1.0.0', 'latest'],         // Additional tags
})
// buildInfo contains: { name, templateId, buildId }
```

```python
build_info = Template.build(
    template,
    'my-template',
    cpu_count=2,                         # CPU cores
    memory_mb=2048,                      # Memory in MB
    skip_cache=False,                    # Skip cache (except for files)
    on_build_logs=default_build_logger(),# Log callback
    api_key="your-api-key",             # Override API key
    domain="your-domain",               # Override domain
    tags=['v1.0.0', 'latest'],          # Additional tags
)
# build_info contains: BuildInfo(name, template_id, build_id)
```

### Build in Background

The `buildInBackground` method starts the build and returns immediately without waiting for completion:

```typescript
const buildInfo = await Template.buildInBackground(template, 'my-template', {
  cpuCount: 2,
  memoryMB: 2048,
})
// Returns immediately with: { name, templateId, buildId }
```

```python
build_info = Template.build_in_background(
    template,
    'my-template',
    cpu_count=2,
    memory_mb=2048,
)
# Returns immediately with: BuildInfo(name, template_id, build_id)
```

### Check Build Status

Use `getBuildStatus` to check the status of a background build:

```typescript
const status = await Template.getBuildStatus(buildInfo, {
  logsOffset: 0,  // Optional: offset for fetching logs
})
// status contains: { status: 'building' | 'ready' | 'error', logEntries: [...] }
```

```python
status = Template.get_build_status(
    build_info,
    logs_offset=0,  # Optional: offset for fetching logs
)
# status contains build status and logs
```

### Background Build with Polling

```typescript
// Start build in background
const buildInfo = await Template.buildInBackground(template, 'my-template', {
  cpuCount: 2,
  memoryMB: 2048,
})

// Poll for build status
let logsOffset = 0
let status = 'building'

while (status === 'building') {
  const buildStatus = await Template.getBuildStatus(buildInfo, {
    logsOffset,
  })

  logsOffset += buildStatus.logEntries.length
  status = buildStatus.status

  buildStatus.logEntries.forEach(
    (logEntry) => console.log(logEntry.toString())
  )

  await new Promise(resolve => setTimeout(resolve, 2000))
}

if (status === 'ready') {
  console.log('Build completed successfully')
} else {
  console.error('Build failed')
}
```

```python
import time

# Start build in background
build_info = Template.build_in_background(
    template,
    'my-template',
    cpu_count=2,
    memory_mb=2048,
)

# Poll for build status
logs_offset = 0
status = "building"

while status == "building":
    build_status = Template.get_build_status(
        build_info,
        logs_offset=logs_offset,
    )

    logs_offset += len(build_status.log_entries)
    status = build_status.status.value

    for log_entry in build_status.log_entries:
        print(log_entry)

    time.sleep(2)

if status == "ready":
    print("Build completed successfully")
else:
    print("Build failed")
```

### Check Name Availability

```typescript
const exists = await Template.exists('my-template')
console.log(`Name ${exists ? 'is taken' : 'is available'}`)
```

```python
exists = Template.exists('my-template')
print(f"Name {'is taken' if exists else 'is available'}")
```

## Tags and Versioning

Template versioning uses tags in the `name:tag` format. Tags allow you to maintain multiple versions of the same template.

### The Default Tag

When you build or reference a template without a tag, E2B uses the `default` tag automatically:

```typescript
// These are equivalent
const sandbox1 = await Sandbox.create('my-template')
const sandbox2 = await Sandbox.create('my-template:default')
```

```python
# These are equivalent
sandbox1 = Sandbox.create('my-template')
sandbox2 = Sandbox.create('my-template:default')
```

### Building with Tags

Single tag:

```typescript
await Template.build(template, 'my-template:v1.0.0')
```

```python
Template.build(template, 'my-template:v1.0.0')
```

Multiple tags:

```typescript
await Template.build(template, 'my-template', { tags: ['v1.2.0', 'latest'] })
```

```python
Template.build(template, 'my-template', tags=['v1.2.0', 'latest'])
```

### Assign Tags

Assign new tags to an existing build without rebuilding (useful for promoting versions):

```typescript
// Assign a single tag
await Template.assignTags('my-template:v1.2.0', 'production')

// Assign multiple tags at once
await Template.assignTags('my-template:v1.2.0', ['production', 'stable'])
```

```python
# Assign a single tag
Template.assign_tags('my-template:v1.2.0', 'production')

# Assign multiple tags at once
Template.assign_tags('my-template:v1.2.0', tags=['production', 'stable'])
```

### Remove Tags

Remove a tag from a template. The underlying build artifact remains accessible via other tags.

```typescript
await Template.removeTags('my-template', 'staging')
```

```python
Template.remove_tags('my-template', 'staging')
```

### Versioning Use Cases

**Semantic versioning:**

```typescript
await Template.build(template, 'api-server:v1.0.0')
await Template.build(template, 'api-server:v1.1.0')
await Template.build(template, 'api-server:v2.0.0')

// Create sandbox from specific version
const sandbox = await Sandbox.create('api-server:v1.1.0')
```

**Environment-based tags:**

```typescript
// Build new version
await Template.build(template, 'my-app:v1.5.0')

// Promote through environments
await Template.assignTags('my-app:v1.5.0', 'staging')

// After testing, promote to production
await Template.assignTags('my-app:v1.5.0', 'production')

// Use in your application
const env = process.env.NODE_ENV
const sandbox = await Sandbox.create(`my-app:${env}`)
```

**Latest and stable rolling tags:**

```typescript
// Build with version and latest tag
await Template.build(template, 'my-tool', { tags: ['v3.0.0', 'latest'] })

// Mark a tested version as stable
await Template.assignTags('my-tool:v2.9.0', 'stable')

// Choose risk tolerance
const latestSandbox = await Sandbox.create('my-tool:latest')   // Newest
const stableSandbox = await Sandbox.create('my-tool:stable')   // Tested
```

## Layer Caching

E2B uses a layer caching system similar to Docker. For each layer command (`.copy()`, `.runCmd()`, `.setEnvs()`, etc.), a new layer is created. If a layer command is unchanged and its inputs are the same as any previous build, the cached layer is reused.

Cache is scoped to the team -- multiple templates can share cached layers if they have identical layers.

### Partial Cache Invalidation

Force rebuild from a specific point using `skipCache()`:

```typescript
const template = Template()
  .fromBaseImage()
  .skipCache()  // Everything after this will be rebuilt
  .runCmd("echo 'Hello, World!'")
```

```python
template = (
    Template()
    .from_base_image()
    .skip_cache()  # Everything after this will be rebuilt
    .run_cmd("echo 'Hello, World!'")
)
```

### Full Template Cache Skip

Skip cache for the entire build:

```typescript
Template.build(template, 'my-template', {
  skipCache: true,  // Skip cache (except for files)
})
```

```python
Template.build(
    template,
    'my-template',
    skip_cache=True,  # Skip cache (except for files)
)
```

### File Caching

When using `.copy()`, files are cached based on their content. Even if you invalidate a layer before `.copy()`, already uploaded files are reused. To force re-upload files, use `forceUpload`:

```typescript
template.copy("config.json", "/app/config.json", { forceUpload: true })
```

```python
template.copy("config.json", "/app/config.json", force_upload=True)
```

### Leveraging Cache for Variants

Build the same template with different CPU/RAM while reusing common layers:

```typescript
// Same template definition, different configurations
await Template.build(template, 'my-template-2cpu-2gb', { cpuCount: 2, memoryMB: 2048 })
await Template.build(template, 'my-template-1cpu-4gb', { cpuCount: 1, memoryMB: 4096 })
// Second build reuses all cached layers
```

### Optimizing Build Times

Place frequently changing commands towards the end of your template definition so earlier layers can be cached and reused more often.

## Template Names

Template names are unique identifiers scoped to your team:

- Your template named `my-app` is stored as `your-team-slug/my-app`
- Reference it simply as `my-app` within your team
- Other teams can have their own `my-app` without conflict
- Public templates should use full namespaced format (`team-slug/template-name`)

Existing public templates remain accessible without the team slug prefix. New public templates should use the full namespaced format.

### Development and Production Names

```typescript
// Development template
await Template.build(template, 'myapp-dev', { cpuCount: 1, memoryMB: 1024 })

// Production template
await Template.build(template, 'myapp-prod', { cpuCount: 4, memoryMB: 4096 })
```

### Resource Variants

```typescript
// Small instance
await Template.build(template, 'myapp-small', { cpuCount: 1, memoryMB: 512 })

// Large instance
await Template.build(template, 'myapp-large', { cpuCount: 8, memoryMB: 16384 })
```

## Build Logging

### Default Logger

```typescript
import { Template, defaultBuildLogger } from 'e2b';

await Template.build(template, 'my-template', {
  onBuildLogs: defaultBuildLogger({
    minLevel: "info",  // Minimum log level: 'debug' | 'info' | 'warn' | 'error'
  }),
});
```

```python
from e2b import Template, default_build_logger

Template.build(
    template,
    'my-template',
    on_build_logs=default_build_logger(
        min_level="info",
    )
)
```

### Custom Logger

```typescript
// Simple logging
onBuildLogs: (logEntry) => console.log(logEntry.toString());

// Custom formatting
onBuildLogs: (logEntry) => {
  const time = logEntry.timestamp.toISOString();
  console.log(`[${time}] ${logEntry.level.toUpperCase()}: ${logEntry.message}`);
};

// Filter by log level
onBuildLogs: (logEntry) => {
  if (logEntry.level === "error" || logEntry.level === "warn") {
    console.error(logEntry.toString());
  }
};
```

```python
# Simple logging
on_build_logs=lambda log_entry: print(log_entry)

# Custom formatting
def custom_logger(log_entry):
    time = log_entry.timestamp.isoformat()
    print(f"[{time}] {log_entry.level.upper()}: {log_entry.message}")

Template.build(template, 'my-template', on_build_logs=custom_logger)
```

### LogEntry Types

The callback receives `LogEntry` objects with properties: `timestamp` (Date/datetime), `level` ('debug'|'info'|'warn'|'error'), and `message` (string).

Special subtypes:
- `LogEntryStart` - Indicates the start of the build process (level: 'debug')
- `LogEntryEnd` - Indicates the end of the build process (level: 'debug')

```typescript
if (logEntry instanceof LogEntryStart) {
  // Build started
}
if (logEntry instanceof LogEntryEnd) {
  // Build ended
}
```

```python
if isinstance(log_entry, LogEntryStart):
    # Build started
    pass
if isinstance(log_entry, LogEntryEnd):
    # Build ended
    pass
```

## Error Handling

The SDK provides specific error types for template builds:

```typescript
import { AuthError, BuildError, FileUploadError } from 'e2b';

try {
  await Template.build(template, 'my-template');
} catch (error) {
  if (error instanceof AuthError) {
    console.error("Authentication failed:", error.message);
  } else if (error instanceof FileUploadError) {
    console.error("File upload failed:", error.message);
  } else if (error instanceof BuildError) {
    console.error("Build failed:", error.message);
  }
}
```

```python
from e2b import AuthError, BuildError, FileUploadError

try:
    Template.build(template, 'my-template')
except AuthError as error:
    print(f"Authentication failed: {error}")
except FileUploadError as error:
    print(f"File upload failed: {error}")
except BuildError as error:
    print(f"Build failed: {error}")
```

## Private Registries

### General Registry

```typescript
Template().fromImage('ubuntu:22.04', {
  username: 'user',
  password: 'pass',
})
```

```python
Template().from_image(
    image="ubuntu:22.04",
    username="user",
    password="pass",
)
```

### GCP Artifact Registry

```typescript
// From file path
Template().fromGCPRegistry('ubuntu:22.04', {
  serviceAccountJSON: './service_account.json',
})

// From object
Template().fromGCPRegistry('ubuntu:22.04', {
  serviceAccountJSON: { project_id: '123', private_key_id: '456' },
})
```

```python
# From file path
Template().from_gcp_registry(
    image="ubuntu:22.04",
    service_account_json="./service_account.json",
)

# From object
Template().from_gcp_registry(
    image="ubuntu:22.04",
    service_account_json={"project_id": "123", "private_key_id": "456"},
)
```

### AWS ECR

```typescript
Template().fromAWSRegistry('ubuntu:22.04', {
  accessKeyId: '123',
  secretAccessKey: '456',
  region: 'us-west-1',
})
```

```python
Template().from_aws_registry(
    image="ubuntu:22.04",
    access_key_id="123",
    secret_access_key="456",
    region="us-west-1",
)
```

## Migration from Legacy System

There are three ways to migrate from the legacy template system (e2b.toml + Dockerfile) to Build System 2.0.

### Migration Command (Recommended)

1. Install the latest E2B CLI
2. Navigate to your template folder (where `e2b.toml` and `e2b.Dockerfile` files are)
3. Run migration command:

```bash
e2b template migrate
```

4. Follow the prompts

Your existing `e2b.toml` and `e2b.Dockerfile` files will be renamed to `e2b.toml.old` and `e2b.Dockerfile.old`.

The migration generates three files:

**TypeScript:** `template.ts`, `build.dev.ts`, `build.prod.ts`
**Python:** `template.py`, `build_dev.py`, `build_prod.py`

### Using fromDockerfile()

Keep your existing Dockerfile content and parse it programmatically:

```typescript
const template = Template()
  .fromDockerfile(dockerfileContent);
```

```python
template = (
    Template()
    .from_dockerfile(dockerfile_content)
)
```

Compatible instructions: `FROM`, `RUN`, `COPY`, `ADD`, `WORKDIR`, `USER`, `ENV`, `ARG`, `CMD`, `ENTRYPOINT`

### Using fromImage()

Build the Docker image yourself for `linux/amd64`, push to a registry, and reference it:

```typescript
const template = Template()
  .fromImage("your-image:tag");
```

```python
template = (
    Template()
    .from_image("your-image:tag")
)
```

## Examples

### Example 1: Claude Code Agent Sandbox

Template with Claude Code CLI pre-installed:

```typescript
// template.ts
import { Template } from 'e2b'

export const template = Template()
  .fromNodeImage('24')
  .aptInstall(['curl', 'git', 'ripgrep'])
  .npmInstall('@anthropic-ai/claude-code@latest', { g: true })
```

```python
# template.py
from e2b import Template

template = (
    Template()
    .from_node_image("24")
    .apt_install(["curl", "git", "ripgrep"])
    .npm_install("@anthropic-ai/claude-code@latest", g=True)
)
```

Build and use:

```typescript
// build.ts
import { Template, defaultBuildLogger } from 'e2b'
import { template as claudeCodeTemplate } from './template'

Template.build(claudeCodeTemplate, 'claude-code', {
  cpuCount: 1,
  memoryMB: 1024,
  onBuildLogs: defaultBuildLogger(),
})

// sandbox.ts
import { Sandbox } from 'e2b'

const sbx = await Sandbox.create('claude-code', {
  envs: {
    ANTHROPIC_API_KEY: '<your api key>',
  },
})

const result = await sbx.commands.run(
  `claude --dangerously-skip-permissions -p 'Create a hello world index.html'`,
  { timeoutMs: 0 }
)
console.log(result.stdout)
sbx.kill()
```

### Example 2: Desktop Environment with VNC

Full Ubuntu 22.04 desktop with XFCE, VNC streaming, LibreOffice, and automation tools:

```typescript
// template.ts
import { Template, waitForPort } from 'e2b'

export const template = Template()
  .fromUbuntuImage('22.04')
  .runCmd([
    'yes | unminimize',
    'apt-get update',
    'apt-get install -y \
      xserver-xorg xorg x11-xserver-utils xvfb x11-utils xauth \
      xfce4 xfce4-goodies util-linux sudo curl git wget python3-pip \
      xdotool scrot ffmpeg x11vnc net-tools netcat x11-apps \
      libreoffice xpdf gedit xpaint tint2 galculator pcmanfm',
    'apt-get clean',
    'rm -rf /var/lib/apt/lists/*',
  ])
  .runCmd([
    'git clone --branch e2b-desktop https://github.com/e2b-dev/noVNC.git /opt/noVNC',
    'ln -s /opt/noVNC/vnc.html /opt/noVNC/index.html',
    'git clone --branch v0.12.0 https://github.com/novnc/websockify /opt/noVNC/utils/websockify',
  ])
  .runCmd('ln -sf /usr/bin/xfce4-terminal.wrapper /etc/alternatives/x-terminal-emulator')
  .copy('start_command.sh', '/start_command.sh')
  .runCmd('chmod +x /start_command.sh')
  .setStartCmd('/start_command.sh', waitForPort(6080))
```

Build with higher resources:

```typescript
await Template.build(desktopTemplate, 'desktop', {
  cpuCount: 8,
  memoryMB: 8192,
  onBuildLogs: defaultBuildLogger(),
})
```

### Example 3: Docker-in-Sandbox

```typescript
// template.ts
import { Template } from 'e2b'

export const template = Template()
  .fromUbuntuImage('25.04')
  .runCmd('curl -fsSL https://get.docker.com | sudo sh')
  .runCmd('sudo docker run --rm hello-world')
```

Build (minimum 2 CPUs, 2 GB RAM recommended):

```typescript
Template.build(dockerTemplate, 'docker', {
  cpuCount: 2,
  memoryMB: 2048,
  onBuildLogs: defaultBuildLogger(),
})
```

Usage:

```typescript
const sbx = await Sandbox.create('docker')
const result = await sbx.commands.run('sudo docker run --rm alpine echo "Hello from Alpine!"')
console.log(result.stdout)
await sbx.kill()
```

### Example 4: Next.js App (Node.js)

Next.js with Tailwind and shadcn UI, development server pre-started on port 3000:

```typescript
// template.ts
import { Template, waitForURL } from 'e2b'

export const template = Template()
  .fromNodeImage('21-slim')
  .setWorkdir('/home/user/nextjs-app')
  .runCmd(
    'npx create-next-app@14.2.30 . --ts --tailwind --no-eslint --import-alias "@/*" --use-npm --no-app --no-src-dir'
  )
  .runCmd('npx shadcn@2.1.7 init -d')
  .runCmd('npx shadcn@2.1.7 add --all')
  .runCmd('mv /home/user/nextjs-app/* /home/user/ && rm -rf /home/user/nextjs-app')
  .setWorkdir('/home/user')
  .setStartCmd('npx next --turbo', waitForURL('http://localhost:3000'))
```

```typescript
Template.build(nextJSTemplate, 'nextjs-app', {
  cpuCount: 4,
  memoryMB: 4096,
  onBuildLogs: defaultBuildLogger(),
})
```

### Example 5: Next.js App (Bun)

Same as above but using Bun runtime:

```typescript
// template.ts
import { Template, waitForURL } from 'e2b'

export const template = Template()
  .fromBunImage('1.3')
  .setWorkdir('/home/user/nextjs-app')
  .runCmd('bun create next-app --app --ts --tailwind --turbopack --yes --use-bun .')
  .runCmd('bunx --bun shadcn@latest init -d')
  .runCmd('bunx --bun shadcn@latest add --all')
  .runCmd('mv /home/user/nextjs-app/* /home/user/ && rm -rf /home/user/nextjs-app')
  .setWorkdir('/home/user')
  .setStartCmd('bun --bun run dev --turbo', waitForURL('http://localhost:3000'))
```

```typescript
Template.build(nextJSTemplate, 'nextjs-app-bun', {
  cpuCount: 4,
  memoryMB: 4096,
  onBuildLogs: defaultBuildLogger(),
})
```

### Example 6: Expo App

Expo web app with development server on port 8081:

```typescript
// template.ts
import { Template, waitForURL } from 'e2b'

export const template = Template()
  .fromNodeImage()
  .setWorkdir("/home/user/expo-app")
  .runCmd("npx create-expo-app@latest . --yes")
  .runCmd("mv /home/user/expo-app/* /home/user/ && rm -rf /home/user/expo-app")
  .setWorkdir("/home/user")
  .setStartCmd("npx expo start", waitForURL("http://localhost:8081"));
```

```typescript
Template.build(expoTemplate, 'expo-app', {
  cpuCount: 4,
  memoryMB: 8192,
  onBuildLogs: defaultBuildLogger(),
})
```

## Best Practices

### 1. Use Tags for Versioning

Instead of version numbers in names, use the tag system:

```typescript
// Good - use tags
await Template.build(template, 'myapp:v1.0.0')
await Template.build(template, 'myapp', { tags: ['v1.1.0', 'latest'] })

// Avoid - version in name
await Template.build(template, 'myapp-v1.0.0')
```

### 2. Optimize Package Installation

Pin package versions for reproducibility:

```typescript
.pipInstall([
  'pandas==2.0.0',
  'numpy==1.24.0'
])
```

Group related packages in single calls:

```typescript
// Good: Single install call
.pipInstall(['pandas', 'numpy', 'matplotlib'])

// Avoid: Separate installs (each creates a new layer)
.pipInstall(['pandas'])
.pipInstall(['numpy'])
.pipInstall(['matplotlib'])
```

### 3. Optimize Layer Order for Caching

Place frequently changing commands towards the end of the template definition:

```typescript
const template = Template()
  .fromNodeImage('lts')
  .aptInstall(['curl', 'git'])        // Rarely changes - cached
  .copy("package.json", "/app/package.json")  // Changes sometimes
  .runCmd("npm install")               // Depends on package.json
  .copy("src/", "/app/src/")           // Changes often - last
```

### 4. Resource Allocation

Match resources to workload:

```typescript
// Light workloads (simple scripts)
cpuCount: 1, memoryMB: 512

// Standard workloads (web servers, APIs)
cpuCount: 2, memoryMB: 2048

// Heavy workloads (ML, desktop, build tools)
cpuCount: 4, memoryMB: 4096

// Maximum
cpuCount: 8, memoryMB: 16384
```

### 5. Use Descriptive Names

```typescript
// Good
'data-science'
'web-api'
'claude-code'

// Avoid
'template1'
'test'
'my-template'
```

### 6. Always Enable Build Logs

```typescript
await Template.build(template, {
  onBuildLogs: defaultBuildLogger(),  // Essential for debugging
});
```

### 7. Test Before Production

```typescript
// Build dev template
await Template.build(template, 'my-template:dev')

// Test in sandbox
const sbx = await Sandbox.create('my-template:dev')
// ... run tests ...

// Promote to production
await Template.assignTags('my-template:dev', 'production')
```

### 8. Leverage Cache for Variants

Build multiple CPU/RAM configurations reusing common layers:

```typescript
await Template.build(template, 'myapp-small', { cpuCount: 1, memoryMB: 512 })
await Template.build(template, 'myapp-large', { cpuCount: 8, memoryMB: 16384 })
// Second build reuses all cached layers
```

## Troubleshooting

### Build Failures

**Problem:** Template build fails during package installation

**Solutions:**
- Verify package names are correct
- Pin package versions to avoid dependency conflicts
- Enable build logs: `onBuildLogs: defaultBuildLogger()`
- Use specific error handling (`AuthError`, `BuildError`, `FileUploadError`)

### Start Command Not Working

**Problem:** Service not running when sandbox spawns

**Solutions:**
- Verify the start command works in an interactive sandbox first
- Use appropriate ready command helpers (`waitForPort`, `waitForURL`, `waitForProcess`)
- Check build logs for startup errors
- Ensure the start command doesn't exit immediately (long-running process required)

### Package Not Found at Runtime

**Problem:** Packages installed in template not available in sandbox

**Solutions:**
- Verify template was built successfully (check build logs)
- Ensure you are creating the sandbox from the correct template name/tag
- Verify the package was included in the template definition
- Rebuild the template after making changes

### Slow Build Times

**Solutions:**
- Use layer caching -- place stable commands early in the definition
- Extend existing templates with `fromTemplate()` instead of rebuilding from scratch
- Pin package versions to avoid dependency resolution overhead
- Only install frequently-used packages in template; install rare packages at runtime
- Use `skipCache: false` (default) to leverage cached layers

### Cache Not Working

**Problem:** Builds are not using cached layers

**Solutions:**
- Ensure the template definition order hasn't changed (changes invalidate downstream layers)
- Check if `skipCache: true` is set in the build options
- Verify file content hasn't changed when using `.copy()`
- Remember cache is team-scoped -- it works across templates with identical layers

### Permission Errors

**Problem:** Permission denied errors during build or in sandbox

**Solutions:**
- Use `setUser()` to switch to appropriate user before running commands
- Run commands as specific user: `runCmd('npm install', { user: 'node' })`
- Default user is `user` (non-root); use `setUser('root')` if root access is needed temporarily

### Getting Help

1. **Check build logs:** `onBuildLogs: defaultBuildLogger()`
2. **Review documentation:** [E2B Template Docs](https://e2b.dev/docs/template)
3. **Search GitHub issues:** [E2B GitHub](https://github.com/e2b-dev/e2b/issues)
4. **Contact support:** [E2B Discord](https://discord.gg/U7KEcGErtQ)

---

**Related Documentation:**
- [Quickstart Guide](/docs/quickstart.md)
- [Code Interpreting](/docs/code-interpreting.md)
- [Sandbox Lifecycle](/docs/sandbox-lifecycle.md)
- [E2B Template Reference](https://e2b.dev/docs/template)
