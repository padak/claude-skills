---
name: second-opinion
description: "Get second opinion from OpenAI (Codex), Google (Gemini), or Anthropic (Claude Code) models. Use when validating architectural decisions, reviewing code security, comparing implementation approaches, or when multi-model consensus adds value. Supports all three major AI CLI tools for maximum flexibility."
---

# Second Opinion via Codex, Gemini & Claude Code CLI

Get external AI perspective from OpenAI (Codex CLI), Google (Gemini CLI), or
Anthropic (Claude Code CLI) to validate decisions or compare approaches.

## Model Cheat Sheet (August 2026)

| Provider | Deep / frontier | Balanced (default) | Fast & cheap |
|----------|-----------------|--------------------|--------------|
| Codex (OpenAI) | `gpt-5.6-sol` | `gpt-5.6-terra` | `gpt-5.6-luna` |
| Gemini (Google) | `gemini-3.1-pro-preview` | auto-routing (omit `-m`) | `gemini-3-flash-preview` |
| Claude Code (Anthropic) | `claude-opus-5` | `claude-sonnet-5` | `claude-haiku-4-5-20251001` |

Also available on Codex: `gpt-5.5` (frontier, non-agentic focus), `gpt-5.4` /
`gpt-5.4-mini` (previous gen), `gpt-5.3-codex-spark` (ultra-fast). The GPT-5.6
family (Sol / Terra / Luna) is the current agentic coding lineup. Verify with
the live registry when in doubt: `python3 -c "import json; [print(m['slug'])
for m in json.load(open('$HOME/.codex/models_cache.json'))['models']]"`.

## Quick Patterns

### Codex (OpenAI)

```bash
# Simple question (Terra = balanced default)
codex exec -m gpt-5.6-terra --output-last-message /tmp/claude/answer.txt "Your question here"
cat /tmp/claude/answer.txt

# Deep review with high reasoning effort (Sol)
codex exec -m gpt-5.6-sol -c model_reasoning_effort="high" \
  --output-last-message /tmp/claude/answer.txt "Your question here"
```

Reasoning effort levels: `low`, `medium`, `high`, `xhigh`, `max` (Sol also
supports `ultra`). Set via `-c model_reasoning_effort="..."`.

#### Structured output with schema (Codex only)

**IMPORTANT:** With `--output-schema`, ALL objects (including nested ones) must have
`"additionalProperties": false` and `"required": [...]` listing every property.

```bash
cat > /tmp/claude/schema.json << 'EOF'
{
  "type": "object",
  "properties": {
    "assessment": { "type": "string" },
    "strengths": { "type": "array", "items": { "type": "string" } },
    "concerns": { "type": "array", "items": { "type": "string" } },
    "recommendation": { "type": "string" }
  },
  "required": ["assessment", "strengths", "concerns", "recommendation"],
  "additionalProperties": false
}
EOF

codex exec -m gpt-5.6-terra --output-schema /tmp/claude/schema.json \
  --output-last-message /tmp/claude/result.json \
  "Analyze [topic]. Provide structured assessment."
cat /tmp/claude/result.json
```

### Gemini (Google)

**WARNING (Aug 2026):** Gemini CLI no longer works with personal Google OAuth
("This client is no longer supported for Gemini Code Assist for individuals —
migrate to Antigravity"). It requires `GEMINI_API_KEY` (or a Workspace / Code
Assist license). If neither is available, skip the Gemini leg and use Codex +
Claude only.

```bash
# Auto-routing picks the model (recommended default)
gemini -p "Your question here" --output-format text > /tmp/claude/answer.txt

# Explicit model
gemini -m gemini-3.1-pro-preview -p "Your question here" --output-format text > /tmp/claude/answer.txt

# JSON output (no schema validation — describe the shape in the prompt)
gemini -p "Analyze [topic]. Respond in JSON with: assessment (string), strengths (array), concerns (array), recommendation (string)" \
  --output-format json > /tmp/claude/result.json
```

### Claude Code (Anthropic)

```bash
# Opus 5 for deep review
claude -p "Your question here" --model claude-opus-5 --output-format text > /tmp/claude/answer.txt

# Sonnet 5 balanced / Haiku 4.5 cheap
claude -p "Your question here" --model claude-sonnet-5 --output-format text > /tmp/claude/answer.txt
```

The spawned instance runs independently without access to the current session
context — a genuinely fresh perspective. `--output-format json` wraps the
response in a structured message object.

## Prompt Templates (any provider)

Substitute into any Quick Pattern above:

- **Architecture review:** "Review this architecture decision: [description]. Assess: scalability, maintainability, security risks, alternatives."
- **Security audit:** "Security review of [file/code]: input validation, authentication/authorization, data exposure risks. Provide specific vulnerabilities and fixes."
- **Code review:** "Review [file] for: bugs, performance issues, maintainability. Provide line-level recommendations."

Pick the deep-tier model (Sol / 3.1-pro / Opus 5) for architecture and
security; the fast tier (Luna / flash / Haiku) is fine for quick code review.

## Key Options

| CLI | Option | Purpose |
|-----|--------|---------|
| codex | `-m <model>` | Model selection (see cheat sheet) |
| codex | `-c model_reasoning_effort="high"` | Reasoning depth (low..max) |
| codex | `--output-schema file.json` | Structured JSON with schema validation |
| codex | `--output-last-message file.txt` | Save final response to file |
| codex | `-i image.png` | Include image for analysis |
| gemini | `-m <model>` | Explicit model (default: auto-routing) |
| gemini | `-p "prompt"` | Non-interactive mode (required) |
| gemini | `--output-format text\|json\|stream-json` | Output format |
| claude | `--model <model>` | Model selection |
| claude | `-p "prompt"` | Non-interactive print mode (required) |
| claude | `--output-format text\|json\|stream-json` | Output format |
| claude | `--max-turns N` | Limit agentic turns |

## Presenting Results

1. Label which provider and model was used, e.g. "Second opinion (OpenAI/Codex - gpt-5.6-sol)"
2. Compare with your own analysis
3. Highlight areas of agreement and disagreement
4. Synthesize a recommendation based on the perspectives

## Multi-Provider Consensus

```bash
Q="Should we use Redis or PostgreSQL for session storage in an e-commerce app?"

codex exec -m gpt-5.6-terra --output-last-message /tmp/claude/codex_opinion.txt "$Q"
gemini -p "$Q" --output-format text > /tmp/claude/gemini_opinion.txt
claude -p "$Q" --model claude-opus-5 --output-format text > /tmp/claude/claude_opinion.txt

for f in codex gemini claude; do echo "=== $f ==="; cat /tmp/claude/${f}_opinion.txt; echo; done
```

Run providers in parallel (background jobs or parallel tool calls) — each call
can take tens of seconds. Analyze agreement/disagreement and synthesize.

## Prerequisites

```bash
codex --version || echo "Codex CLI not installed"
gemini --version || echo "Gemini CLI not installed"
claude --version || echo "Claude Code CLI not installed"
```

**Authentication:**
- **Codex:** `codex login` or `OPENAI_API_KEY` env var
- **Gemini:** `GEMINI_API_KEY` env var required (personal OAuth was discontinued in favor of Antigravity)
- **Claude Code:** `claude login` or `ANTHROPIC_API_KEY` env var
