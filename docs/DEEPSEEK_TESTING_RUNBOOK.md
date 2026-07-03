# DeepSeek Testing Runbook

This runbook starts RepoFlow testing with DeepSeek. It keeps credentials out of
the repository and separates a minimal API smoke test from real coding-agent
benchmark runs.

DeepSeek official API docs:

- <https://api-docs.deepseek.com/>
- <https://api-docs.deepseek.com/quick_start/pricing/>

## 1. Secret Handling

Do not write API keys into source files, prompts, run manifests, screenshots,
or committed `.env` files.

Use shell environment variables. Prefer hidden input so the key is not written
into shell history:

```bash
printf "DeepSeek key: "
stty -echo
IFS= read -r DEEPSEEK_API_KEY
stty echo
printf "\n"
export DEEPSEEK_API_KEY
export DEEPSEEK_BASE_URL="https://api.deepseek.com"
export DEEPSEEK_MODEL="deepseek-v4-pro"
```

For cheap smoke checks, use:

```bash
export DEEPSEEK_MODEL="deepseek-v4-flash"
```

After testing:

```bash
unset DEEPSEEK_API_KEY
```

## 2. Direct API Smoke Test

This only verifies that the DeepSeek Chat Completions API is reachable.
It does not edit files or run a coding benchmark.

```bash
cd /Users/chenyihao/mycode/BoardFlowBench
python3 scripts/deepseek_smoke.py
```

Expected output:

```text
repoflow-deepseek-ok
```

## 3. OpenCode Agent Smoke Test

Use OpenCode when you want DeepSeek to act as a coding agent with filesystem and
shell access. Keep the workspace isolated.

The fastest automated path is:

```bash
cd /Users/chenyihao/mycode/BoardFlowBench
bash scripts/run_deepseek_b001_smoke.sh
```

This performs:

1. direct DeepSeek API smoke;
2. OpenCode DeepSeek smoke in a temporary directory;
3. Full BoardFlow B001 workspace initialization;
4. DeepSeek B001 implementation through OpenCode;
5. deterministic B001 gate finalization.

It stops before B002.

Manual equivalent:

Initialize a Full BoardFlow workspace:

```bash
cd /Users/chenyihao/mycode/BoardFlowBench
export RUN_ID=$(date +%Y%m%d-%H%M%S)
export FULL_WS=/tmp/repoflow-deepseek-full-$RUN_ID/workspace
export RESULTS_ROOT=/tmp/repoflow-deepseek-results-$RUN_ID

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/run_scenario.py \
  --target expense_lite \
  --condition full_boardflow \
  --workspace "$FULL_WS" \
  --oracle-root ../ExpenseLiteBenchOracles \
  --results-dir "$RESULTS_ROOT" \
  --source-repo ../ExpenseLiteBenchDemo \
  --agent-profile deepseek

export RUN_MANIFEST=$(find "$RESULTS_ROOT" -name run.json | head -1)
```

Run only B001 first:

```bash
opencode run --pure -m deepseek/deepseek-v4-pro \
  --dir "$FULL_WS" \
  "$(cat /Users/chenyihao/mycode/BoardFlowBench/output/demo_recording/prompts/B001/board.txt)"
```

If `deepseek-v4-pro` is unavailable or too slow, use:

```bash
opencode run --pure -m deepseek/deepseek-v4-flash \
  --dir "$FULL_WS" \
  "$(cat /Users/chenyihao/mycode/BoardFlowBench/output/demo_recording/prompts/B001/board.txt)"
```

Finalize the B001 gate:

```bash
cd /Users/chenyihao/mycode/BoardFlowBench
PYTHONPATH=. python3 scripts/run_scenario.py --resume "$RUN_MANIFEST"
```

Do not continue to B002 until B001 gate passes.

## 4. First Controlled DeepSeek Experiment

Run a small DeepSeek-only pilot before mixed-agent testing.

```text
Target: expense_lite
Tasks: B001 -> B002 -> B003 -> B004
Agent: DeepSeek through OpenCode
Conditions:
  - no_board_baseline
  - native_docs_handoff
  - full_boardflow
Repetitions: 3 first, then 5 if stable
```

This tests whether repository-level scaffolding helps the same model under
different visible repository states.

## 5. What To Record

For each run, record:

- model name;
- OpenCode version;
- condition;
- run manifest path;
- first failing task, if any;
- gate score path;
- changed files;
- whether handoff was valid;
- whether downstream tasks reused upstream decisions.

Do not copy API keys into notes or terminal recordings.
