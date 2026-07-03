#!/usr/bin/env bash
set -euo pipefail

ROOT="${BFB_ROOT:-/Users/chenyihao/mycode/BoardFlowBench}"
cd "$ROOT"

if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
  echo "DEEPSEEK_API_KEY is not set. Run this script from the terminal where the key is exported." >&2
  exit 2
fi

export DEEPSEEK_BASE_URL="${DEEPSEEK_BASE_URL:-https://api.deepseek.com}"
export DEEPSEEK_MODEL="${DEEPSEEK_MODEL:-deepseek-v4-flash}"

if [[ "${DEEPSEEK_MODEL}" == */* ]]; then
  OPENCODE_MODEL="${OPENCODE_DEEPSEEK_MODEL:-$DEEPSEEK_MODEL}"
else
  OPENCODE_MODEL="${OPENCODE_DEEPSEEK_MODEL:-deepseek/$DEEPSEEK_MODEL}"
fi

SOURCE_REPO="${SOURCE_REPO:-../ExpenseLiteBenchDemo}"
ORACLE_ROOT="${ORACLE_ROOT:-../ExpenseLiteBenchOracles}"
PROMPT_FILE="${PROMPT_FILE:-$ROOT/docs/prompts/B001_FULL_BOARDFLOW_PROMPT.md}"

if [[ ! -d "$SOURCE_REPO" ]]; then
  echo "Missing source repo: $SOURCE_REPO" >&2
  exit 2
fi
if [[ ! -d "$ORACLE_ROOT" ]]; then
  echo "Missing oracle root: $ORACLE_ROOT" >&2
  exit 2
fi
if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "Missing B001 prompt: $PROMPT_FILE" >&2
  exit 2
fi

echo "== DeepSeek API smoke =="
python3 scripts/deepseek_smoke.py

echo "== OpenCode DeepSeek smoke =="
TMPD="$(mktemp -d /tmp/repoflow-deepseek-opencode-XXXXXX)"
cleanup() {
  rm -rf "$TMPD"
}
trap cleanup EXIT
if ! opencode run --pure -m "$OPENCODE_MODEL" \
  --dir "$TMPD" \
  "Return exactly: repoflow-deepseek-opencode-ok"; then
  cat >&2 <<EOF
OpenCode could not run DeepSeek model '$OPENCODE_MODEL'.
The direct DeepSeek API smoke passed, so this is an OpenCode provider/client
failure rather than a DeepSeek API-key or endpoint failure.

Next options:
  1. run 'opencode providers login' to refresh the DeepSeek credential;
  2. try OPENCODE_DEEPSEEK_MODEL=deepseek/deepseek-chat with this script;
  3. use a direct DeepSeek coding adapter instead of OpenCode.
EOF
  exit 1
fi

echo "== Initialize Full BoardFlow B001 workspace =="
RUN_ID="${RUN_ID:-$(date +%Y%m%d-%H%M%S)}"
FULL_WS="${FULL_WS:-/tmp/repoflow-deepseek-full-$RUN_ID/workspace}"
RESULTS_ROOT="${RESULTS_ROOT:-/tmp/repoflow-deepseek-results-$RUN_ID}"

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/run_scenario.py \
  --target expense_lite \
  --condition full_boardflow \
  --workspace "$FULL_WS" \
  --oracle-root "$ORACLE_ROOT" \
  --results-dir "$RESULTS_ROOT" \
  --source-repo "$SOURCE_REPO" \
  --agent-profile deepseek

RUN_MANIFEST="$(find "$RESULTS_ROOT" -name run.json | head -1)"
if [[ -z "$RUN_MANIFEST" ]]; then
  echo "run.json was not created under $RESULTS_ROOT" >&2
  exit 1
fi

echo "FULL_WS=$FULL_WS"
echo "RUN_MANIFEST=$RUN_MANIFEST"

echo "== Run DeepSeek B001 through OpenCode =="
opencode run --pure -m "$OPENCODE_MODEL" \
  --dir "$FULL_WS" \
  "$(cat "$PROMPT_FILE")"

echo "== Finalize B001 gate =="
PYTHONPATH=. python3 scripts/run_scenario.py --resume "$RUN_MANIFEST"

echo "== Summary =="
SCORE_FILE="$(find "$RESULTS_ROOT" -path '*/stages/B001/score.json' | head -1)"
if [[ -n "$SCORE_FILE" ]]; then
  echo "SCORE_FILE=$SCORE_FILE"
  python3 - "$SCORE_FILE" <<'PY'
import json
import sys
from pathlib import Path

score = json.loads(Path(sys.argv[1]).read_text())
print("hard_gate_pass=", score.get("hard_gate_pass"))
print("violations=", score.get("violations", []))
for section in ("correctness", "scope_control", "handoff", "board_consistency", "hygiene"):
    value = score.get(section)
    if isinstance(value, dict):
        print(f"{section}_violations=", value.get("violations", []))
PY
fi

python3 - "$RUN_MANIFEST" <<'PY'
import json
import sys
from pathlib import Path

run = json.loads(Path(sys.argv[1]).read_text())
print("run_status=", run.get("status"))
print("current_task=", run.get("current_task"))
print("stages=", [stage.get("task_id") for stage in run.get("stages", [])])
PY
