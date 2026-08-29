---
name: e2b
description: Execute AI-generated code in secure isolated E2B cloud sandboxes (SDK v2). Use for running Python/JavaScript/TypeScript/R/Java/Bash code, managing sandbox lifecycle (create, pause, resume, kill, list, connect), running coding agents (Claude Code, Codex, AMP, OpenCode) in sandboxes, git operations inside sandboxes, code contexts for parallel isolated execution, monitoring metrics (CPU, memory, disk), MCP gateway integration (200+ tools), uploading/downloading files, storage bucket mounting (S3, GCS, R2), streaming command output, SSH/PTY access, custom templates with Build System 2.0, and integrating LLMs with code execution capabilities.
---

# E2B Sandbox Skill

Secure isolated cloud VMs for executing AI-generated code. Sandboxes start in ~150ms with full code execution, filesystem, git, and network access.

**SDK v2 Breaking Change:** Python uses `Sandbox.create()` — not `Sandbox()`. Secured access is enabled by default.

## Quick Reference

| Feature | Reference |
|---------|-----------|
| Getting started | [quickstart.md](references/quickstart.md) |
| Lifecycle & security | [sandbox-lifecycle.md](references/sandbox-lifecycle.md) |
| Code execution & contexts | [code-interpreting.md](references/code-interpreting.md) |
| File operations | [filesystem.md](references/filesystem.md) |
| Git operations | [git-integration.md](references/git-integration.md) |
| Coding agents | [agents.md](references/agents.md) |
| Monitoring & events | [monitoring-and-events.md](references/monitoring-and-events.md) |
| Persistence (pause/resume) | [persistence.md](references/persistence.md) |
| MCP Gateway (200+ tools) | [mcp-gateway.md](references/mcp-gateway.md) |
| Custom templates | [custom-templates.md](references/custom-templates.md) |
| Advanced (SSH, PTY, buckets, proxy) | [advanced-sandbox.md](references/advanced-sandbox.md) |

## Installation

Two packages available — use `e2b` for base sandbox features, `e2b-code-interpreter` when you need `run_code()` (Jupyter-style execution):

```bash
# Python — base sandbox (filesystem, commands, git, processes)
pip install e2b

# Python — code interpreter (adds run_code with charts, multi-language)
pip install e2b-code-interpreter

# JavaScript/TypeScript — base sandbox
npm i e2b

# JavaScript/TypeScript — code interpreter
npm i @e2b/code-interpreter
```

Required environment variable:
```bash
E2B_API_KEY=e2b_***  # Get from https://e2b.dev/dashboard?tab=keys
```

## Core Patterns

### Pattern 1: One-shot Code Execution

```python
from e2b_code_interpreter import Sandbox

sandbox = Sandbox.create()
execution = sandbox.run_code('print("Hello from E2B!")')
print(execution.text)
sandbox.kill()
```

```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create()
const execution = await sandbox.runCode('console.log("Hello!")')
console.log(execution.text)
await sandbox.kill()
```

### Pattern 2: Multi-language Execution

```python
sandbox.run_code('import pandas as pd; df.describe()')       # Python (default)
sandbox.run_code('await fetch(url)', language='js')           # JavaScript
sandbox.run_code('const x: number = 42', language='ts')       # TypeScript
sandbox.run_code('summary(mtcars)', language='r')             # R
sandbox.run_code('System.out.println("hi")', language='java') # Java
sandbox.run_code('ls -la /home/user', language='bash')        # Bash
```

### Pattern 3: File Upload + Analysis

```python
sandbox.files.write('/home/user/data.csv', csv_content)

execution = sandbox.run_code('''
import pandas as pd
df = pd.read_csv('/home/user/data.csv')
df.describe()
''')

result = sandbox.files.read('/home/user/output.png')
```

### Pattern 4: Code Contexts (Isolated Parallel Execution)

```python
ctx_a = sandbox.create_code_context(cwd='/home/user/project-a')
ctx_b = sandbox.create_code_context(cwd='/home/user/project-b')

result_a = sandbox.run_code('import pandas; print("A")', context=ctx_a)
result_b = sandbox.run_code('import numpy; print("B")', context=ctx_b)
```

### Pattern 5: Git Operations

```python
from e2b import Sandbox

sandbox = Sandbox.create()
sandbox.git.clone('https://github.com/user/repo.git', '/home/user/repo',
                  username='user', password=os.environ['GITHUB_TOKEN'])
sandbox.git.checkout_branch('/home/user/repo', 'feature-branch')
sandbox.git.add('/home/user/repo')
sandbox.git.commit('/home/user/repo', 'fix: update config')
sandbox.git.push('/home/user/repo', username='user', password=os.environ['GITHUB_TOKEN'])
```

### Pattern 6: Running Coding Agents

```python
from e2b import Sandbox

sandbox = Sandbox.create(
    template='claude',
    envs={'ANTHROPIC_API_KEY': os.environ['ANTHROPIC_API_KEY']},
    timeout=300
)
result = sandbox.commands.run(
    'claude -p "Write a hello world server" --dangerously-skip-permissions',
    timeout=120
)
print(result.stdout)
```

See [agents.md](references/agents.md) for Codex, AMP, OpenCode, and more patterns.

### Pattern 7: LLM Tool Integration

```python
from anthropic import Anthropic
from e2b_code_interpreter import Sandbox

tools = [{
    "name": "execute_python",
    "description": "Execute python code in sandbox",
    "input_schema": {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Python code to execute"}
        },
        "required": ["code"]
    }
}]

client = Anthropic()
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Calculate 2+2"}],
    tools=tools
)

if message.stop_reason == "tool_use":
    tool_use = next(b for b in message.content if b.type == "tool_use")
    sandbox = Sandbox.create()
    result = sandbox.run_code(tool_use.input['code'])
    print(result.text)
    sandbox.kill()
```

### Pattern 8: MCP Gateway

```python
from e2b import Sandbox

sandbox = Sandbox.create(
    mcp={
        'github': {'githubPersonalAccessToken': os.environ['GITHUB_TOKEN']},
        'slack': {'botToken': os.environ['SLACK_BOT_TOKEN']}
    }
)
mcp_url = sandbox.get_mcp_url()
mcp_token = sandbox.get_mcp_token()
```

See [mcp-gateway.md](references/mcp-gateway.md) for 200+ available integrations.

### Pattern 9: Persistence (Pause/Resume)

```python
sandbox = Sandbox.create(auto_pause=True, timeout=600)
sandbox.run_code(code)
sandbox.pause()
saved_id = sandbox.sandbox_id

# Later: Resume
sandbox = Sandbox.connect(saved_id)
```

### Pattern 10: Custom Template (Build System 2.0)

```typescript
import { Template, waitForPort } from 'e2b'

const template = Template()
  .fromPythonImage('3.12')
  .pipInstall(['pandas', 'numpy', 'matplotlib'])
  .copy('./app', '/home/user/app')
  .setStartCmd('python /home/user/app/server.py', waitForPort(3000))

await Template.build(template, { name: 'my-data-template' })
```

## API Quick Reference

### Sandbox Lifecycle

```python
# Create (SDK v2 — always use .create())
sandbox = Sandbox.create()                          # Default 5 min timeout
sandbox = Sandbox.create(timeout=300)               # Custom timeout (seconds)
sandbox = Sandbox.create(envs={'KEY': 'val'})       # With env vars
sandbox = Sandbox.create(metadata={'user': '123'})  # With metadata
sandbox = Sandbox.create(template='my-template')    # Custom template
sandbox = Sandbox.create(secure=False)              # Disable secured access

# Info & timeout
info = sandbox.get_info()
sandbox.set_timeout(60)

# Kill
sandbox.kill()
Sandbox.kill(sandbox_id)
```

### Sandbox Discovery

```python
paginator = Sandbox.list()                                          # List all
sandboxes = paginator.next_items()
paginator = Sandbox.list(query={'state': ['running', 'paused']})    # Filter by state
paginator = Sandbox.list(query={'metadata': {'userId': '123'}})     # Filter by metadata
sandbox = Sandbox.connect(sandbox_id)                               # Connect to existing
```

### Code Execution

```python
execution = sandbox.run_code(code, language='python', envs={'VAR': 'val'})
execution.text          # Combined output
execution.logs.stdout   # Standard output
execution.logs.stderr   # Standard error
execution.results       # Rich results (charts, tables)
execution.error         # Runtime errors
```

### Commands

```python
result = sandbox.commands.run('ls -la')
result = sandbox.commands.run('cmd', envs={'VAR': 'val'})
result = sandbox.commands.run('cmd', background=True)
result = sandbox.commands.run('cmd', on_stdout=callback, on_stderr=callback)
```

### Files

```python
sandbox.files.write('/home/user/file.txt', content)     # Write single file
sandbox.files.write_files([('/path/a', data_a), ...])    # Write multiple files
content = sandbox.files.read('/home/user/file.txt')      # Read file
info = sandbox.files.get_info('/home/user/file.txt')     # File metadata
files = sandbox.files.list('/home/user')                 # List directory
watcher = sandbox.files.watch_dir('/path')               # Watch changes
```

### Git

```python
sandbox.git.clone(url, path, username=..., password=...)
sandbox.git.branches(path)
sandbox.git.create_branch(path, 'branch-name')
sandbox.git.checkout_branch(path, 'branch-name')
sandbox.git.add(path)
sandbox.git.commit(path, 'message')
sandbox.git.push(path, username=..., password=...)
sandbox.git.pull(path)
```

### Code Contexts

```python
ctx = sandbox.create_code_context(cwd='/path', language='python')
result = sandbox.run_code('print("isolated")', context=ctx)
contexts = sandbox.list_code_contexts()
sandbox.remove_code_context(ctx.id)
```

### Monitoring

```python
metrics = sandbox.get_metrics()
# Returns list of SandboxMetric: cpu_used_pct, cpu_count, mem_used, mem_total, disk_used, disk_total
```

## Python vs JavaScript API

| Operation | Python | JavaScript |
|-----------|--------|------------|
| Create | `Sandbox.create()` | `await Sandbox.create()` |
| Timeout | `set_timeout(60)` | `setTimeout(60000)` (ms) |
| Run code | `run_code(code)` | `await runCode(code)` |
| Kill | `kill()` | `await kill()` |
| Pause | `pause()` | `await pause()` |
| Git clone | `git.clone(url, path)` | `await git.clone(url, path)` |
| Code context | `create_code_context()` | `await createCodeContext()` |

## Packages: `e2b` vs `e2b-code-interpreter`

| Feature | `e2b` | `e2b-code-interpreter` |
|---------|-------|------------------------|
| Sandbox lifecycle | Yes | Yes (inherits) |
| Commands (`commands.run`) | Yes | Yes |
| Filesystem | Yes | Yes |
| Git integration | Yes | Yes |
| `run_code()` (Jupyter) | No | Yes |
| Charts/visualizations | No | Yes |
| Code contexts | No | Yes |
| Coding agent templates | Yes | No (use `e2b`) |

Use `e2b` for: running agents, shell commands, git workflows, file operations.
Use `e2b-code-interpreter` for: data analysis, code execution, charts, multi-language code.

## Default Environment Variables

Available in every sandbox:
- `E2B_SANDBOX=true`
- `E2B_SANDBOX_ID` - Current sandbox ID
- `E2B_TEAM_ID` - Team ID
- `E2B_TEMPLATE_ID` - Template used

## Best Practices

1. **Always clean up**: Use try/finally with `kill()` or context managers
2. **Use absolute paths**: `/home/user/file.txt` not `file.txt`
3. **Handle errors**: Check `execution.error` after `run_code()`
4. **Tag with metadata**: Use metadata for tracking user sessions
5. **Monitor resources**: Check `get_metrics()` for CPU/memory usage
6. **Set appropriate timeouts**: Short tasks 60-120s, analysis 300-600s
7. **Use code contexts**: Isolate parallel code execution within one sandbox
8. **Use git API**: Prefer `sandbox.git.*` over shell git commands

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Sandbox()` fails in Python | Use `Sandbox.create()` (SDK v2 breaking change) |
| Timeout too quick | `Sandbox.create(timeout=300)` or `set_timeout(300)` |
| Code fails | Check `execution.error` for details |
| File not found | Use absolute paths, verify with `files.list()` |
| Auth error on secured sandbox | Old template — rebuild with envd >= v0.2.0, or use `secure=False` |
| Rate limited | Check plan limits in [sandbox-lifecycle.md](references/sandbox-lifecycle.md) |
| High resource usage | Check `get_metrics()`, kill unused sandboxes |
