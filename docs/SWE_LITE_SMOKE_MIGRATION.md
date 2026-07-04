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

## Next Step

The next implementation step is a patch-oriented local runner that uses smaller outputs than the JSON full-file protocol from `scripts/ollama_repoflow_skill_pilot.py`. The Qwen 9B pilot showed that large JSON file payloads are a reliability bottleneck.
