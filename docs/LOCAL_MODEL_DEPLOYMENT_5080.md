# Local Model Deployment on RTX 5080

This note is for running RepoFlow pilot experiments on a single RTX 5080 class
machine. The main constraint is VRAM. Treat 9B and 14B quantized coder models as
the practical local baseline; use 32B only for short-context stress tests.

## Recommended Model Tiers

| Tier | Model class | Use |
| --- | --- | --- |
| Primary | Qwen3.5 9B instruct/coder-class model | Fast local RepoFlow smoke and SWE-style small tasks |
| Strong local | Qwen/Qwen coder 14B class model, Q4 or Q5 | Better patch quality if latency is acceptable |
| Stress | Qwen coder 32B class model, Q4 | Short-context trials only; avoid as default |
| Avoid | 70B+ dense or 80B total-weight MoE | Not practical on a single 16 GB 5080 without heavy CPU offload |

## Ollama Setup

Install Ollama from the official distribution for the target operating system,
then verify the daemon and local model list:

```bash
ollama --version
ollama list
```

Pull a small first model to validate the machine:

```bash
ollama pull qwen3.5:9b
ollama run qwen3.5:9b "Return exactly: repoflow-local-ok"
```

If `qwen3.5:9b` is not available under that exact tag on the machine, list or
search available Qwen tags in the local Ollama registry and choose the closest
9B or 14B instruct/coder model.

## RepoFlow Smoke

Clone the repository and install the normal Python dependencies:

```bash
git clone https://github.com/ChenNeuro/BoardFlowBench.git
cd BoardFlowBench
python3 -m pip install -r requirements.txt
PYTHONPATH=. python3 -m unittest discover -s tests
```

For API-backed DeepSeek smoke, export credentials only in the shell. Do not
write keys into tracked files:

```bash
export DEEPSEEK_API_KEY="..."
export DEEPSEEK_BASE_URL="https://api.deepseek.com"
export DEEPSEEK_MODEL="deepseek-v4-flash"
python3 scripts/deepseek_smoke.py
```

For an Expense Lite Full BoardFlow smoke:

```bash
export BFB_ROOT="$PWD"
export SOURCE_REPO="../ExpenseLiteBenchDemo"
export ORACLE_ROOT="../ExpenseLiteBenchOracles"
bash scripts/run_deepseek_b001_smoke.sh
```

## SWE-Style Pilot

Standard SWE-bench evaluation needs Docker isolation. Before running a real
SWE-bench Lite or Verified subset, verify Docker on the target machine:

```bash
docker --version
docker run --rm hello-world
```

If Docker is unavailable, restrict the pilot to patch-generation and local
repository tests. Record it as a non-standard SWE-style smoke, not as an
official SWE-bench score.

## Suggested First Experiment

1. Run the repository unit tests.
2. Run `scripts/deepseek_smoke.py` or an Ollama one-line local model smoke.
3. Run one Expense Lite Full BoardFlow task to validate board, handoff, and gate
   mechanics.
4. Only after Docker is working, run one SWE-bench Lite instance with RepoFlow
   board files wrapped around the checked-out issue repository.

