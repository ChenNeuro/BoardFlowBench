# SWE Lite Smoke Migration

This note describes the first migration path from Expense Lite pilots to a SWE-bench Lite style task.

The goal is deliberately narrow: prepare a local RepoFlow task packet for one public SWE-bench Lite instance, then use it for patch-generation smoke testing. This is not an official SWE-bench Lite score unless Docker isolation and the official harness are used.

## Default Instance

The initial smoke instance is:

- Dataset: `princeton-nlp/SWE-bench_Lite`
- Split: `test`
- Instance: `astropy__astropy-12907`
- Repository: `astropy/astropy`
- Base commit: `d16bfe05a744909de4b27f5875fe0d4ed41ce607`

This instance was chosen because it is the first visible SWE-bench Lite row and is enough to validate the migration mechanics.

## Prepare Metadata Only

Use metadata-only mode when GitHub clone access is unavailable or when you only want to generate control-plane evidence:

```powershell
python scripts\prepare_swe_lite_smoke.py `
  --instance-id astropy__astropy-12907 `
  --metadata-only
```

The script writes a temporary control directory containing:

- `instance_public.json`
- `problem_statement.md`
- `agent_task_packet.md`
- `repoflow_skill_packet.md`
- `gold_patch.diff`
- `test_patch.diff`
- `DO_NOT_SHOW_AGENT.txt`

`gold_patch.diff` and `test_patch.diff` are evaluator/control-plane material. Do not put them in an agent workspace or prompt.

## Prepare A Workspace

Only use this when GitHub clone access is available:

```powershell
$workspace = "$env:TEMP\swe-lite-astropy-12907-workspace"
$control = "$env:TEMP\swe-lite-astropy-12907-control"

python scripts\prepare_swe_lite_smoke.py `
  --instance-id astropy__astropy-12907 `
  --workspace $workspace `
  --control-dir $control `
  --force
```

The workspace receives:

- `AGENTS.md`
- `.repoflow/assigned_task.json`
- `.repoflow/assigned_task.md`
- `.repoflow/skill_packet.md`
- `.repoflow/handoffs/`

The workspace does not receive the gold patch or test patch.

## Local Model Use

For a local Qwen smoke, use the generated `.repoflow/assigned_task.md` and `.repoflow/skill_packet.md` as the model context. Keep the same distinction used in the Expense Lite pilot:

- model output failure;
- dependency/environment failure;
- repository test failure;
- harness/evaluator mismatch.

Do not run a full SWE-bench job on this machine until Docker works:

```powershell
docker --version
docker run --rm hello-world
```

Prepare a bounded plain-vs-skill local pilot after creating the workspace:

```powershell
python scripts\swe_lite_ollama_pilot.py `
  --workspace $workspace `
  --control-dir $control `
  --results-dir docs\evidence\swe_lite_local_pilot `
  --model qwen3.5:9b `
  --analysis-first
```

The runner:

- gives both variants the same task and source context;
- permits edits only to explicitly listed source paths;
- uses exact search/replace edits and rejects unsafe, non-unique, or no-op replacements;
- keeps the evaluator test patch out of model context and applies it only after generation;
- records model format, dependency/environment, repository test, and evaluator failures separately;
- always reports `official_score: false`.

The first Astropy pilot is documented in `docs/REPOFLOW_SWE_LITE_QWEN35_9B_PILOT_20260704.md`. It did not show a single-agent skill improvement. Docker and the official harness remain required before reporting a SWE-bench score.

## Next Step

Install the missing lightweight Astropy test dependency in an isolated environment, rerun the fixed protocol over several instances/seeds, and use Docker plus the official harness before treating results as benchmark scores.
