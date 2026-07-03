# MiniMax Testing Runbook

This runbook keeps MiniMax credentials out of the repository while making it
easy to use MiniMax for RepoFlow experiments.

## 1. Secret Handling

Do not write API keys into source files, prompts, run manifests, shell history
snippets, `.env` files committed to Git, or benchmark result directories.

Use a temporary shell environment variable:

```bash
export MINIMAX_API_KEY="<paste key locally>"
export MINIMAX_BASE_URL="https://api.minimaxi.com/v1"
export MINIMAX_MODEL="MiniMax-M3"
```

After testing, unset the variable:

```bash
unset MINIMAX_API_KEY
```

Rotate the key if it was ever pasted into a shared chat, document, log, or
screen recording.

## 2. API Smoke Test

Run a minimal direct API check:

```bash
cd /Users/chenyihao/mycode/BoardFlowBench
python3 scripts/minimax_smoke.py
```

Expected output should include:

```text
repoflow-minimax-ok
```

Override model or endpoint when needed:

```bash
python3 scripts/minimax_smoke.py \
  --base-url "https://api.minimaxi.com/v1" \
  --model "MiniMax-M3"
```

If using a different MiniMax model family, set:

```bash
export MINIMAX_MODEL="<model name>"
```

## 3. What This Smoke Test Does Not Do

The direct API smoke test only verifies chat-completions connectivity. It does
not give MiniMax shell, file-editing, or Git access.

For benchmark implementation runs, use one of these routes:

- configure an existing coding-agent client such as OpenCode or Claude Code to
  use MiniMax as the model provider;
- write a separate trusted adapter that calls MiniMax, applies patches, runs
  tests, and exits non-zero on failure;
- use MiniMax as an external reviewer or planner while Codex/OpenCode performs
  repository edits.

## 4. Recommended Experiment Order

Use MiniMax first for controlled repeated runs, then mixed-agent runs.

```text
MiniMax-only pilot:
  no_board_baseline x 5
  native_docs_handoff x 5
  full_boardflow x 5

Mixed-agent pilot:
  DeepSeek / B001 -> Codex / B002 -> MiniMax / B003
  conditions: no_board_baseline, full_boardflow, repo_expanded_context
```

This separates model capability from the repository scaffold effect.
