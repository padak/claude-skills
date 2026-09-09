---
name: second-opinion
description: "Use when validating an architectural decision, reviewing code or a diff for bugs and security, comparing implementation approaches, or when the user asks for a second opinion, a consultation, or consensus from GPT/Codex, Gemini/Antigravity (agy), or another Claude. Covers the OpenAI Codex CLI, Google Antigravity CLI (agy) and Anthropic Claude Code CLI in headless mode."
---

# Second Opinion via Codex, Antigravity (agy) & Claude Code CLI

Get an independent perspective from OpenAI (Codex CLI), Google (Antigravity
CLI, command `agy`) or Anthropic (Claude Code CLI). Every call below is
headless, runs without the current session's context, and writes its answer
to a file so the result survives a backgrounded or crashed run.

## Model Cheat Sheet (September 2026)

| Provider | Deep / frontier | Balanced (default) | Fast & cheap |
|----------|-----------------|--------------------|--------------|
| Codex (OpenAI) | `gpt-6-astra` | `gpt-5.6-terra` | `gpt-5.6-luna` |
| Antigravity `agy` (Google) | `gemini-3.1-pro-high` | `gemini-3.8-flash` + `--effort medium` | `gemini-3.8-flash` + `--effort low` |
| Claude Code (Anthropic) | `claude-fable-5-1` / `claude-opus-5` | `claude-sonnet-5` | `claude-haiku-4-5-20251001` |

**Strategy / design consultations -> `gpt-6-astra` with `-c model_reasoning_effort="high"`.**

Effort scales: Codex `low` < `medium` < `high` < `xhigh` < `max` (+ `ultra`); agy
`low` < `medium` < `high`; Claude `low` < `medium` < `high` < `xhigh` < `max`.
Cheapest run on every provider = fast-tier model + `low`.

Also on Codex: `gpt-5.6-sol` (agentic workhorse; its default effort is `low`,
so always pass the effort explicitly), `gpt-5.5` (previous frontier),
`gpt-5.3-codex-spark` (ultra-fast), `gpt-daybreak-blue-latest`
(defensive-cybersecurity frontier). Hidden slugs `gpt-reserve` and
`codex-auto-review` exist but are not listed. Live registry:
`python3 -c "import json; [print(m['slug'], m['visibility']) for m in json.load(open('$HOME/.codex/models_cache.json'))['models']]"`.

Also on agy (`agy models` lists the live catalog): `gemini-3.7-flash`,
`gemini-3.6-flash` (older gens) and the non-Google `claude-opus-4-6-thinking`,
`claude-sonnet-4-6`, `gpt-oss-120b-medium`. Those are a cheap cross-check, not
a different-vendor opinion. `--model gemini-3.8-flash --effort high` resolves
to `gemini-3.8-flash-high`; the full slug works too. Pro exists only as
`gemini-3.1-pro-high` / `-low`. An unknown slug fails immediately and prints
the valid list.

Claude aliases: `fable` -> `claude-fable-5`, `opus` -> `claude-opus-5`,
`sonnet` -> `claude-sonnet-5`. `claude-fable-5-1` works but the CLI logs an
`unrecognized_model` notice (harmless).

## Quick Patterns

All snippets assume an output directory outside the repo:

```bash
OUT=/tmp/claude && mkdir -p "$OUT"   # or the session scratchpad
```

### Codex (OpenAI)

```bash
# One-shot (Terra, balanced). --ephemeral = nothing persisted, -s read-only = cannot edit
# Cheapest: -m gpt-5.6-luna -c model_reasoning_effort="low"
codex exec -m gpt-5.6-terra -c model_reasoning_effort="medium" -s read-only --ephemeral \
  --skip-git-repo-check -o "$OUT/answer.md" "Your question here" < /dev/null
cat "$OUT/answer.md"

# Deep design review (Astra, high)
codex exec -m gpt-6-astra -c model_reasoning_effort="high" -s read-only --ephemeral \
  --skip-git-repo-check -o "$OUT/answer.md" "Your question here" < /dev/null
```

Reasoning effort: `low`, `medium`, `high`, `xhigh`, `max`; `ultra` (Astra, Sol,
Terra, Daybreak) adds automatic task delegation.

Codex treats the cwd as its repo and will explore it. Pure consultation: run
from the scratchpad (or pass `-C <dir>`). Code review: run from the project
root. Three gotchas that end with no answer file: `--skip-git-repo-check` is
mandatory outside a git repo; `< /dev/null` is mandatory without a TTY
(background runs otherwise wait on stdin); `gpt-6-astra` refuses on an old CLI
("requires a newer version of Codex") -- run `codex update` (or
`brew upgrade codex`). Always check the exit code before reading the file.

#### Diff review (Codex)

```bash
# uncommitted changes | branch vs base | a single commit -- run from the repo root
codex review --uncommitted -c model="gpt-5.6-terra" -c model_reasoning_effort="medium" \
  < /dev/null > "$OUT/review.md"
codex review --base main < /dev/null > "$OUT/review.md"
codex review --commit <sha> --title "Fix session race" < /dev/null > "$OUT/review.md"

# custom review instructions: the working tree is reviewed, no scope flag allowed
codex review -c model="gpt-5.6-terra" -c model_reasoning_effort="medium" \
  "Focus on concurrency bugs and missing error handling" < /dev/null > "$OUT/review.md"

# same review with exec-style flags (-m, -o, --ephemeral, --skip-git-repo-check)
codex exec review --uncommitted -m gpt-6-astra -c model_reasoning_effort="high" --ephemeral \
  -o "$OUT/review.md" < /dev/null
```

A scope flag (`--uncommitted`, `--base`, `--commit`) and a custom prompt are
mutually exclusive: `error: the argument '--uncommitted' cannot be used with
'[PROMPT]'`. `codex review` has no `-m` or `-o`; pick the model with
`-c model="..."` and redirect stdout.

#### Structured output with schema (Codex)

**IMPORTANT:** With `--output-schema`, ALL objects (including nested ones) must
have `"additionalProperties": false` and `"required": [...]` listing every
property.

```bash
cat > "$OUT/schema.json" << 'JSON'
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
JSON

codex exec -m gpt-5.6-terra --output-schema "$OUT/schema.json" -s read-only --ephemeral \
  --skip-git-repo-check -o "$OUT/result.json" "Analyze [topic]. Provide structured assessment." < /dev/null
cat "$OUT/result.json"
```

### Antigravity `agy` (Google)

```bash
# One-shot, default model (gemini-3.8-flash at the --effort level)
agy -p "Your question here" --effort medium --output-format text > "$OUT/answer.md" < /dev/null

# Deep review on Gemini 3.1 Pro; raise the print timeout (default 5m) for long answers
agy -p "Your question here" --model gemini-3.1-pro-high --output-format text \
  --print-timeout 15m > "$OUT/answer.md" < /dev/null

# JSON envelope: {conversation_id, status, response, duration_seconds, num_turns, usage}
agy -p "Your question here" --output-format json > "$OUT/answer.json" < /dev/null
python3 -c "import json; print(json.load(open('$OUT/answer.json'))['response'])"

# Structured output: --json-schema needs --output-format json; read .structured_output
agy -p "Analyze [topic]. Provide structured assessment." --output-format json \
  --json-schema "$OUT/schema.json" > "$OUT/result.json" < /dev/null
python3 -c "import json; print(json.dumps(json.load(open('$OUT/result.json'))['structured_output'], indent=2))"
```

Print mode is consultation-only by default: any tool that needs the `command`
permission (that includes `ls` and `cat` of the cwd) is auto-denied and the
run ends with `jetski: no output produced`. Put the code **in the prompt**
(`"$(cat file.py)"`). If agy must explore a repo, run from the project root
with `--dangerously-skip-permissions`; that also allows writes, so prefer a
throwaway worktree. Do **not** use `--sandbox` for repo work: it switches the
cwd to an empty `~/.gemini/antigravity-cli/scratch`. Fatal errors go to stderr
with an `error:` prefix, a hit `--print-timeout` returns partial output with
exit 0 plus a warning, and the log is `~/.gemini/antigravity-cli/cli.log`.

### Gemini CLI (legacy)

Dead for personal Google OAuth (`IneligibleTierError ... migrate to
Antigravity`). It only runs with `GEMINI_API_KEY`, and headless runs also need
`--skip-trust` (or `GEMINI_CLI_TRUST_WORKSPACE=true`). Use `agy` instead.

### Claude Code (Anthropic)

```bash
# Pure consultation: no tools, nothing persisted, explicit effort
claude -p "Your question here" --model claude-opus-5 --effort high --tools "" \
  --no-session-persistence --output-format text > "$OUT/answer.md" < /dev/null

# Structured output: --json-schema takes the schema as a string; read .structured_output
claude -p "Analyze [topic]. Provide structured assessment." --model claude-sonnet-5 --tools "" \
  --no-session-persistence --output-format json --json-schema "$(cat "$OUT/schema.json")" < /dev/null \
  | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin)['structured_output'], indent=2))"
```

Worth knowing: `--max-budget-usd 2` caps spend; `--fallback-model sonnet`
survives overloads; the nested run loads `~/.claude/CLAUDE.md` and the
project's, so it may answer in your configured language; `--safe-mode` drops
CLAUDE.md, skills, plugins and hooks for a customization-free opinion; `--system-prompt "..."` sets a reviewer
persona; keep the default `--tools` (and drop `--no-session-persistence`) when
the reviewer must read the repo. Nesting from inside a Claude Code session
works without env tweaks. `claude ultrareview` is a cloud multi-agent review of
the current branch; it is user-triggered and billed separately.

## Consultation Dialogue (multi-round)

For "talk it through with X" requests, run a short dialogue and keep every
round on disk (all files below live in `$OUT`) so the thread is reproducible. Round 1 is a self-contained brief
(context, what exists, decisions A-H, requested structure); round 2+ quotes
what you accept or reject and why, then asks the next question.

| CLI | Round 1 | Round 2+ |
|-----|---------|----------|
| codex | `codex exec -m gpt-6-astra -c model_reasoning_effort="high" -s read-only --skip-git-repo-check -o r1.md "$(cat brief1.md)" < /dev/null` (no `--ephemeral`) | `codex exec resume --last --skip-git-repo-check -o r2.md "$(cat brief2.md)" < /dev/null` |
| agy | `agy -p "$(cat brief1.md)" --model gemini-3.1-pro-high --output-format json > r1.json < /dev/null` (`conversation_id` inside) | `agy -c -p "$(cat brief2.md)" --output-format text > r2.md < /dev/null` (or `--conversation <id>` instead of `-c`) |
| claude | `claude -p "$(cat brief1.md)" --model claude-opus-5 --tools "" --output-format json > r1.json < /dev/null` (`session_id` inside, no `--no-session-persistence`) | `claude -p --resume <session_id> --tools "" --output-format text "$(cat brief2.md)" > r2.md < /dev/null` |

Rules that keep it useful: the brief must stand alone (the model has no
session context); ask for numbered decisions and exact wording, not vibes;
when you disagree, say so in the next round and let it defend or concede; stop
after 2-3 rounds and write down the synthesis. Codex on `high` takes 1-5
minutes, Pro on agy about as long: run them in the background and keep
working.

## Prompt Templates (any provider)

Substitute into any Quick Pattern above:

- **Architecture review:** "Review this architecture decision: [description]. Assess: scalability, maintainability, security risks, alternatives."
- **Security audit:** "Security review of the code below: input validation, authentication/authorization, data exposure risks. Provide specific vulnerabilities and fixes. $(cat file.py)"
- **Code review:** "Review the code below for: bugs, performance issues, maintainability. Provide line-level recommendations. $(cat file.py)"

Paste the code into the prompt as shown: agy print mode and Claude with
`--tools ""` cannot open files, so a bare path gives them nothing to review.
Only Codex run from the repo root (or Claude with its default tools) may be
given a path instead.

Pick the deep tier (Astra / 3.1 Pro / Fable or Opus 5) for architecture and
security; the fast tier (Luna / Flash low / Haiku) is fine for a quick code
review.

## Key Options

| CLI | Option | Purpose |
|-----|--------|---------|
| codex | `-m <model>` | Model selection (see cheat sheet) |
| codex | `-c model_reasoning_effort="high"` | Reasoning depth (low..max, ultra) |
| codex | `-s read-only` / `--ephemeral` | No edits / no session on disk |
| codex | `--skip-git-repo-check` / `-C <dir>` | Run outside a repo / set the working root |
| codex | `--output-schema file.json` | Structured JSON with schema validation |
| codex | `-o file.txt` | Save the final message to a file |
| codex | `-i image.png` | Include an image |
| codex | `review --uncommitted\|--base X\|--commit SHA` | Diff review |
| agy | `-p "prompt"` | Print mode (required; tools auto-denied) |
| agy | `--model <slug>` / `--effort low\|medium\|high` | Model and effort variant |
| agy | `--output-format text\|json\|stream-json` | JSON carries `response`, `usage`, `conversation_id` |
| agy | `--json-schema <str\|file>` | Structured output (json format only) |
| agy | `--print-timeout 15m` | Longer wait for Pro / high effort |
| agy | `-c` / `--conversation <id>` | Continue a dialogue |
| claude | `--model <model\|alias>` / `--effort <level>` | Model and effort (low..max) |
| claude | `-p "prompt"` | Print mode (required) |
| claude | `--tools ""` / `--no-session-persistence` | No tools / nothing persisted |
| claude | `--output-format text\|json\|stream-json` | JSON carries `result`, `session_id`, `total_cost_usd` |
| claude | `--json-schema '<json>'` | Structured output in `structured_output` |
| claude | `--max-budget-usd N` / `--resume <id>` | Spend cap / continue a dialogue |

## Presenting Results

1. Label which provider and model was used, e.g. "Second opinion (OpenAI/Codex - gpt-6-astra)"
2. Compare with your own analysis
3. Highlight areas of agreement and disagreement
4. Synthesize a recommendation based on the perspectives

## Multi-Provider Consensus

```bash
Q="Should we use Redis or PostgreSQL for session storage in an e-commerce app?"

codex exec -m gpt-5.6-terra -c model_reasoning_effort="medium" -s read-only --ephemeral \
  --skip-git-repo-check -o "$OUT/codex_opinion.md" "$Q" < /dev/null > "$OUT/codex.log" 2>&1 &
PID_CODEX=$!
agy -p "$Q" --effort medium --output-format text > "$OUT/agy_opinion.md" 2> "$OUT/agy.log" < /dev/null &
PID_AGY=$!
claude -p "$Q" --model claude-opus-5 --tools "" --no-session-persistence --output-format text \
  > "$OUT/claude_opinion.md" 2> "$OUT/claude.log" < /dev/null &
PID_CLAUDE=$!

wait "$PID_CODEX"  || echo "codex FAILED (see $OUT/codex.log)"
wait "$PID_AGY"    || echo "agy FAILED (see $OUT/agy.log)"
wait "$PID_CLAUDE" || echo "claude FAILED (see $OUT/claude.log)"

for f in codex agy claude; do echo "=== $f ==="; cat "$OUT/${f}_opinion.md"; echo; done
```

Each call can take tens of seconds to minutes, so run them in parallel. A
bare `wait` returns success even when one job failed; wait on each PID and
skip a provider whose file is empty rather than synthesizing over a gap.

## Prerequisites

```bash
codex --version  || echo "Codex CLI not installed"
agy --version    || echo "Antigravity CLI not installed"
claude --version || echo "Claude Code CLI not installed"
```

**Authentication:**
- **Codex:** `codex login` or `OPENAI_API_KEY`; `codex doctor` checks auth and config
- **Antigravity:** run `agy` once interactively and sign in with Google (Antigravity OAuth, no API key); `agy update` upgrades
- **Claude Code:** `claude login` or `ANTHROPIC_API_KEY`
