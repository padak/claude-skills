# Handling Permissions

Control tool usage and permissions in the Claude Agent SDK.

## Permission Flow

```
Tool Request → PreToolUse Hook → Deny Rules → Allow Rules → Ask Rules → Permission Mode → canUseTool Callback → Execute/Denied
```

## Permission Modes

| Mode | Description |
|------|-------------|
| `default` | Standard permission behavior |
| `plan` | Planning mode - no execution |
| `acceptEdits` | Auto-accept file edits |
| `bypassPermissions` | Bypass all checks (use with caution) |

### Setting Permission Mode

**Initial Configuration:**
```typescript
const result = await query({
  prompt: "Help me refactor this code",
  options: { permissionMode: 'default' }
});
```

**Dynamic Mode Change (Streaming Only):**
```typescript
const q = query({
  prompt: streamInput(),
  options: { permissionMode: 'default' }
});

await q.setPermissionMode('acceptEdits');

for await (const message of q) {
  console.log(message);
}
```

### Mode Behaviors

**acceptEdits Mode:**
- All file edits auto-approved
- Filesystem operations (mkdir, touch, rm, etc.) auto-approved
- Other tools require normal permissions

**bypassPermissions Mode:**
- ALL tool uses auto-approved
- No permission prompts
- Hooks still execute

## canUseTool Callback

Fires when Claude Code would show a permission prompt:

**TypeScript:**
```typescript
const result = await query({
  prompt: "Analyze this codebase",
  options: {
    canUseTool: async (toolName, input) => {
      console.log(`Tool: ${toolName}`);

      // Block writes to system directories
      if (toolName === "Write" && input.file_path?.startsWith("/system/")) {
        return {
          behavior: "deny",
          message: "System directory write not allowed"
        };
      }

      return {
        behavior: "allow",
        updatedInput: input
      };
    }
  }
});
```

**Python:**
```python
async def custom_permission_handler(tool_name: str, input_data: dict, context: dict):
    if tool_name == "Write" and input_data.get("file_path", "").startswith("/system/"):
        return {
            "behavior": "deny",
            "message": "System directory write not allowed",
            "interrupt": True
        }

    # Redirect sensitive operations
    if tool_name in ["Write", "Edit"] and "config" in input_data.get("file_path", ""):
        safe_path = f"./sandbox/{input_data['file_path']}"
        return {
            "behavior": "allow",
            "updatedInput": {**input_data, "file_path": safe_path}
        }

    return {"behavior": "allow", "updatedInput": input_data}

options = ClaudeAgentOptions(
    can_use_tool=custom_permission_handler,
    allowed_tools=["Read", "Write", "Edit"]
)
```

## Hooks for Permission Control

```python
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher

async def validate_bash_command(input_data, tool_use_id, context):
    if input_data['tool_name'] == 'Bash':
        command = input_data['tool_input'].get('command', '')
        if 'rm -rf /' in command:
            return {
                'hookSpecificOutput': {
                    'hookEventName': 'PreToolUse',
                    'permissionDecision': 'deny',
                    'permissionDecisionReason': 'Dangerous command blocked'
                }
            }
    return {}

options = ClaudeAgentOptions(
    hooks={
        'PreToolUse': [
            HookMatcher(matcher='Bash', hooks=[validate_bash_command], timeout=120)
        ]
    }
)
```

## Best Practices

1. **Use default mode** for controlled execution
2. **Use acceptEdits mode** for isolated file operations
3. **Avoid bypassPermissions** in production
4. **Combine modes with hooks** for fine-grained control
5. **Switch modes dynamically** based on task progress
