# Structured Outputs

Get validated JSON results from agent workflows.

## When to Use

Use structured outputs when you need validated JSON after an agent completes a multi-turn workflow with tools (file searches, command execution, web research, etc.).

## Benefits

- **Validated structure**: Always receive valid JSON matching schema
- **Simplified integration**: No parsing or validation code needed
- **Type safety**: Use with TypeScript or Python type hints
- **Clean separation**: Define output requirements separately from instructions
- **Tool autonomy**: Agent chooses tools while guaranteeing output format

## Quick Start

### TypeScript

```typescript
import { query } from '@anthropic-ai/claude-agent-sdk';

const schema = {
  type: 'object',
  properties: {
    company_name: { type: 'string' },
    founded_year: { type: 'number' },
    headquarters: { type: 'string' }
  },
  required: ['company_name']
};

for await (const message of query({
  prompt: 'Research Anthropic and provide key company information',
  options: {
    outputFormat: { type: 'json_schema', schema: schema }
  }
})) {
  if (message.type === 'result' && message.structured_output) {
    console.log(message.structured_output);
    // { company_name: "Anthropic", founded_year: 2021, headquarters: "San Francisco" }
  }
}
```

### Python

```python
from claude_agent_sdk import query

schema = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "founded_year": {"type": "number"},
        "headquarters": {"type": "string"}
    },
    "required": ["company_name"]
}

async for message in query(
    prompt="Research Anthropic and provide key company information",
    options={
        "output_format": { "type": "json_schema", "schema": schema }
    }
):
    if hasattr(message, 'structured_output'):
        print(message.structured_output)
```

## Using Zod (TypeScript)

```typescript
import { z } from 'zod';
import { zodToJsonSchema } from 'zod-to-json-schema';

const AnalysisResult = z.object({
  summary: z.string(),
  issues: z.array(z.object({
    severity: z.enum(['low', 'medium', 'high']),
    description: z.string(),
    file: z.string()
  })),
  score: z.number().min(0).max(100)
});

type AnalysisResult = z.infer<typeof AnalysisResult>;

const schema = zodToJsonSchema(AnalysisResult, { $refStrategy: 'root' });

for await (const message of query({
  prompt: 'Analyze codebase for security issues',
  options: { outputFormat: { type: 'json_schema', schema: schema } }
})) {
  if (message.type === 'result' && message.structured_output) {
    const parsed = AnalysisResult.safeParse(message.structured_output);
    if (parsed.success) {
      console.log(`Score: ${parsed.data.score}`);
    }
  }
}
```

## Using Pydantic (Python)

```python
from pydantic import BaseModel
from claude_agent_sdk import query

class Issue(BaseModel):
    severity: str
    description: str
    file: str

class AnalysisResult(BaseModel):
    summary: str
    issues: list[Issue]
    score: int

async for message in query(
    prompt="Analyze codebase for security issues",
    options={
        "output_format": {
            "type": "json_schema",
            "schema": AnalysisResult.model_json_schema()
        }
    }
):
    if hasattr(message, 'structured_output'):
        result = AnalysisResult.model_validate(message.structured_output)
        print(f"Score: {result.score}")
```

## Supported JSON Schema Features

- All basic types: object, array, string, integer, number, boolean, null
- `enum`, `const`, `required`, `additionalProperties` (must be `false`)
- String formats: `date-time`, `date`, `email`, `uri`, `uuid`, etc.
- `$ref`, `$def`, and `definitions`

## Error Handling

```typescript
for await (const msg of query({
  prompt: 'Analyze the data',
  options: { outputFormat: { type: 'json_schema', schema: mySchema } }
})) {
  if (msg.type === 'result') {
    if (msg.subtype === 'success' && msg.structured_output) {
      console.log(msg.structured_output);
    } else if (msg.subtype === 'error_max_structured_output_retries') {
      console.error('Could not produce valid output');
    }
  }
}
```

## Example: TODO Tracking

```typescript
const todoSchema = {
  type: 'object',
  properties: {
    todos: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          text: { type: 'string' },
          file: { type: 'string' },
          line: { type: 'number' },
          author: { type: 'string' },
          date: { type: 'string' }
        },
        required: ['text', 'file', 'line']
      }
    },
    total_count: { type: 'number' }
  },
  required: ['todos', 'total_count']
};

for await (const message of query({
  prompt: 'Find all TODO comments in src/ and identify who added them',
  options: { outputFormat: { type: 'json_schema', schema: todoSchema } }
})) {
  if (message.type === 'result' && message.structured_output) {
    const data = message.structured_output;
    console.log(`Found ${data.total_count} TODOs`);
    data.todos.forEach(todo => {
      console.log(`${todo.file}:${todo.line} - ${todo.text}`);
    });
  }
}
```
