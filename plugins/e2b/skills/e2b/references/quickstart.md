# E2B Quickstart Guide

## SDK v2 Important Changes

- Python: Use `Sandbox.create()` instead of `Sandbox()` constructor
- Two packages: `e2b` (base sandbox) and `e2b-code-interpreter` (code execution with `run_code`)
- Secured access enabled by default (disable with `secure=False` if needed)
- Python 3.9 support dropped
- File writing: use `sandbox.files.write()` for single files, `sandbox.files.write_files()` for multiple files
- Listing sandboxes now uses pagination

## Installation

### Python
```bash
# Base sandbox (filesystem, commands, processes)
pip install e2b python-dotenv

# Code interpreter (adds run_code for Jupyter-style execution)
pip install e2b-code-interpreter python-dotenv
```

### JavaScript/TypeScript
```bash
# Base sandbox
npm i e2b dotenv

# Code interpreter
npm i @e2b/code-interpreter dotenv
```

## Setup

### 1. Create E2B Account
- Sign up at https://e2b.dev/auth/sign-up
- New accounts get $100 in credits

### 2. Get API Key
1. Navigate to https://e2b.dev/dashboard?tab=keys
2. Copy your API key
3. Add to `.env` file:

```bash
E2B_API_KEY=e2b_***
```

## Basic Usage (Code Interpreter)

### Python
```python
from dotenv import load_dotenv
load_dotenv()
from e2b_code_interpreter import Sandbox

# Create sandbox (alive for 5 minutes by default)
sbx = Sandbox.create()

# Execute Python code in Jupyter-style environment
execution = sbx.run_code("print('hello world')")
print(execution.logs)

# List files
files = sbx.files.list("/")
print(files)

# Clean up
sbx.kill()
```

### JavaScript/TypeScript
```javascript
import 'dotenv/config'
import { Sandbox } from '@e2b/code-interpreter'

// Create sandbox
const sbx = await Sandbox.create()

// Execute Python code
const execution = await sbx.runCode('print("hello world")')
console.log(execution.logs)

// List files
const files = await sbx.files.list('/')
console.log(files)

// Clean up
await sbx.kill()
```

## Basic Usage (Base Sandbox)

Use the base `e2b` package when you need filesystem/command access without the code interpreter.

### Python
```python
from e2b import Sandbox

sbx = Sandbox.create()

# Run shell commands
result = sbx.commands.run("echo 'hello world'")

# Write and read files
sbx.files.write("/home/user/hello.txt", "Hello, world!")
content = sbx.files.read("/home/user/hello.txt")

sbx.kill()
```

### JavaScript/TypeScript
```javascript
import { Sandbox } from 'e2b'

const sbx = await Sandbox.create()

// Run shell commands
const result = await sbx.commands.run('echo "hello world"')

// Write and read files
await sbx.files.write('/home/user/hello.txt', 'Hello, world!')
const content = await sbx.files.read('/home/user/hello.txt')

await sbx.kill()
```

## Upload and Download Files

### Upload File

**Python:**
```python
from e2b_code_interpreter import Sandbox

sbx = Sandbox.create()

# Read local file and upload to sandbox (use absolute paths in sandbox)
with open("local/file.csv", "rb") as file:
    sbx.files.write("/home/user/my-file.csv", file)
```

**JavaScript:**
```javascript
import fs from 'fs'
import { Sandbox } from '@e2b/code-interpreter'

const content = fs.readFileSync('local/file.csv')

const sbx = await Sandbox.create()
await sbx.files.write('/home/user/my-file.csv', content)
```

### Download File

**Python:**
```python
from e2b_code_interpreter import Sandbox

sbx = Sandbox.create()
# Download from sandbox
content = sbx.files.read('/home/user/my-file')
# Write to local file
with open('local/file', 'w') as file:
    file.write(content)
```

**JavaScript:**
```javascript
import fs from 'fs'
import { Sandbox } from '@e2b/code-interpreter'

const sbx = await Sandbox.create()
const content = await sbx.files.read('/home/user/my-file')
fs.writeFileSync('local/file', content)
```

### Multiple Files

Currently, you must upload/download files one at a time. E2B is working on batch operations.

**Python (v2 - write_files for multiple):**
```python
from e2b_code_interpreter import Sandbox

sbx = Sandbox.create()

# Write multiple files at once (SDK v2)
sbx.files.write_files([
    {"path": "/home/user/file-a.csv", "data": content_a},
    {"path": "/home/user/file-b.csv", "data": content_b},
])

# Or upload one at a time
with open("local/file/a", "rb") as file:
    sbx.files.write("/home/user/file-a.csv", file)

with open("local/file/b", "rb") as file:
    sbx.files.write("/home/user/file-b.csv", file)
```

## Install Custom Packages

### Option 1: Custom Sandbox Template (preinstalled packages)

Define a template with packages pre-installed using the `e2b` base package:

**Python:**
```python
from e2b import Template

template = (
    Template()
    .from_template("code-interpreter-v1")
    .pip_install(['cowsay'])   # Install Python packages
    .npm_install(['cowsay'])   # Install Node.js packages
)
```

Build and use the template:

```python
from dotenv import load_dotenv
from e2b import Template, default_build_logger, Sandbox
from template import template

load_dotenv()

# Build the template
Template.build(
    template,
    'custom-packages',
    cpu_count=2,
    memory_mb=2048,
    on_build_logs=default_build_logger(),
)

# Use the custom template
sbx = Sandbox.create("custom-packages")
```

**JavaScript:**
```typescript
import { Template } from 'e2b';

export const template = Template()
  .fromTemplate("code-interpreter-v1")
  .pipInstall(['cowsay'])
  .npmInstall(['cowsay']);
```

### Option 2: Install at Runtime

Packages installed at runtime are only available in the running sandbox instance.

**Python:**
```python
from e2b_code_interpreter import Sandbox

sbx = Sandbox.create()
sbx.commands.run("pip install cowsay")  # Install Python package
sbx.run_code("""
  import cowsay
  cowsay.cow("Hello, world!")
""")
```

**JavaScript:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sbx = await Sandbox.create()
sbx.commands.run('pip install cowsay')
sbx.runCode(`
  import cowsay
  cowsay.cow("Hello, world!")
`)
```

**System packages (apt-get):**
```python
from e2b_code_interpreter import Sandbox

sbx = Sandbox.create()
sbx.commands.run("apt-get update && apt-get install -y curl git")
```

## Connecting LLMs

E2B works with any LLM through tool use (function calling).

### OpenAI Example

```python
# pip install openai e2b-code-interpreter
import json
from openai import OpenAI
from e2b_code_interpreter import Sandbox

client = OpenAI()
model = "gpt-4o"

messages = [
    {
        "role": "user",
        "content": "Calculate how many r's are in the word 'strawberry'"
    }
]

# Define tool for code execution
tools = [{
    "type": "function",
    "function": {
        "name": "execute_python",
        "description": "Execute python code in a Jupyter notebook cell and return result",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The python code to execute in a single cell"
                }
            },
            "required": ["code"]
        }
    }
}]

# Send message
response = client.chat.completions.create(
    model=model,
    messages=messages,
    tools=tools,
)

# Append the response message
response_message = response.choices[0].message
messages.append(response_message)

# Execute if tool was called
if response_message.tool_calls:
    for tool_call in response_message.tool_calls:
        if tool_call.function.name == "execute_python":
            with Sandbox.create() as sandbox:
                code = json.loads(tool_call.function.arguments)['code']
                execution = sandbox.run_code(code)
                result = execution.text

            messages.append({
                "role": "tool",
                "name": "execute_python",
                "content": result,
                "tool_call_id": tool_call.id,
            })

# Generate the final response
final_response = client.chat.completions.create(
    model=model,
    messages=messages
)

print(final_response.choices[0].message.content)
```

### Anthropic Example

```python
# pip install anthropic e2b-code-interpreter
from anthropic import Anthropic
from e2b_code_interpreter import Sandbox

client = Anthropic()
model = "claude-3-5-sonnet-20240620"

messages = [
    {
        "role": "user",
        "content": "Calculate how many r's are in the word 'strawberry'"
    }
]

# Define tool
tools = [{
    "name": "execute_python",
    "description": "Execute python code in a Jupyter notebook cell and return (not print) the result",
    "input_schema": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The python code to execute in a single cell"
            }
        },
        "required": ["code"]
    }
}]

# Send message
message = client.messages.create(
    model=model,
    max_tokens=1024,
    messages=messages,
    tools=tools
)

# Append the response message
messages.append({
    "role": "assistant",
    "content": message.content
})

# Execute if tool was called
if message.stop_reason == "tool_use":
    tool_use = next(block for block in message.content if block.type == "tool_use")
    tool_name = tool_use.name
    tool_input = tool_use.input

    if tool_name == "execute_python":
        with Sandbox.create() as sandbox:
            code = tool_input['code']
            execution = sandbox.run_code(code)
            result = execution.text

        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result,
                }
            ],
        })

# Generate the final response
final_response = client.messages.create(
    model=model,
    max_tokens=1024,
    messages=messages,
    tools=tools
)

print(final_response.content[0].text)
```

### Vercel AI SDK Example

```javascript
// npm install ai @ai-sdk/openai zod @e2b/code-interpreter
import { openai } from '@ai-sdk/openai'
import { generateText } from 'ai'
import z from 'zod'
import { Sandbox } from '@e2b/code-interpreter'

const model = openai('gpt-4o')

const { text } = await generateText({
  model,
  prompt: "Calculate how many r's are in the word 'strawberry'",
  tools: {
    execute_python: {
      description: 'Execute python code in a Jupyter notebook cell and return result',
      parameters: z.object({
        code: z.string().describe('The python code to execute in a single cell'),
      }),
      execute: async ({ code }) => {
        const sandbox = await Sandbox.create()
        const { text, results, logs, error } = await sandbox.runCode(code)
        return results
      },
    },
  },
  maxSteps: 2
})

console.log(text)
```

## Secured Access (SDK v2 Default)

Sandboxes are now secure by default. The SDK handles authentication automatically.

To temporarily disable (not recommended for production):

**Python:**
```python
sandbox = Sandbox.create(secure=False)
```

**JavaScript:**
```javascript
const sandbox = await Sandbox.create({ secure: false })
```

For custom templates created before envd v0.2.0, rebuild them to enable secure communication.

## Listing Sandboxes (Paginated in v2)

**Python:**
```python
from e2b_code_interpreter import Sandbox, SandboxQuery

paginator = Sandbox.list()
while paginator.has_next:
    sandboxes = paginator.next_items()
    print(sandboxes)

# With metadata query
paginator = Sandbox.list(query=SandboxQuery(metadata={"key": "value"}))
```

**JavaScript:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const paginator = Sandbox.list()
for (const sandbox of await paginator.nextItems()) {
    console.log(sandbox.sandboxId)
}

// With metadata query
const queryPaginator = Sandbox.list({query: {metadata: {key: "value"}}})
```

## Next Steps

- Learn about [Sandbox Lifecycle](sandbox-lifecycle.md)
- Understand [File Operations](filesystem.md)
- Explore [Sandbox Persistence](persistence.md)
- See [Data Analysis Examples](code-interpreting.md)
