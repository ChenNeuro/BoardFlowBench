# RepoFlow SWE Lite Qwen 9B Pilot

Date: 2026-07-04

## Scope

- Model: `qwen3.5:9b`
- Ollama: `0.31.1`
- Instance: `astropy__astropy-12907`
- Base commit: `d16bfe05a744909de4b27f5875fe0d4ed41ce607`
- Conditions: plain single agent vs mandatory `repoflow-task-agent` skill
- Docker: unavailable
- Official SWE-bench score: no

The model received the public issue statement and two repository files. It did not receive `gold_patch.diff`, `test_patch.diff`, hidden tests, or oracle content. The public evaluator test patch was applied only after model generation.

## Iterations

| Version | Protocol change | Plain | Skill |
| --- | --- | --- | --- |
| v1 | Raw unified diff | Patch did not apply | Corrupt patch |
| v2 | Retry failed apply checks | Format failure after retry | Format failure after retry |
| v3 | Exact replacement JSON | Empty edits | Empty edits |
| v4 | Add composition-debugging skill | Empty edits | Empty edits |
| v5 | Enable model thinking | Empty response channel | Empty response channel |
| v6 | Separate analysis and edit passes | Applied an incorrect/incomplete patch | No-op edit accepted by old harness |
| v7 | Concise analysis and reject no-op edits | Invalid replacement | No-op rejected |

The v5 failure is a model-channel issue: with Ollama JSON format and thinking enabled, Qwen placed JSON in `thinking` while leaving `response` empty. It is not a RepoFlow task failure.

The v6 target test did not start because local pytest collection required the missing `hypothesis` package. This is a dependency/environment failure. `py_compile` passed, but the plain patch was visibly incomplete and is not counted as a task success.

## Result

This one-instance pilot shows no single-agent improvement from the mandatory skill. The skill condition did not produce a valid fix and repeatedly returned empty or no-op edits. The experiment does not evaluate multi-agent execution, and one instance is insufficient for an effect-size claim.

The useful outcome is harness hardening:

- shallow commit fetch with codeload fallback for large repositories;
- exact replacement protocol instead of fragile model-generated diff hunk metadata;
- explicit editable-file boundaries;
- rejection of missing, unsafe, non-unique, and no-op edits;
- evaluator patch isolation;
- separate model-channel, environment, repository-test, and evaluator failure categories.

## Evidence

Raw model responses, generated patches, command tails, prompt/context hashes, and summaries are under:

- `docs/evidence/swe_lite_qwen35_9b_skill_pilot_20260704_v1_apply_failure/`
- `docs/evidence/swe_lite_qwen35_9b_skill_pilot_20260704_v2_apply_retry/`
- `docs/evidence/swe_lite_qwen35_9b_skill_pilot_20260704_v3_replacements/`
- `docs/evidence/swe_lite_qwen35_9b_skill_pilot_20260704_v4_composition_skill/`
- `docs/evidence/swe_lite_qwen35_9b_skill_pilot_20260704_v5_thinking/`
- `docs/evidence/swe_lite_qwen35_9b_skill_pilot_20260704_v6_analysis_first/`
- `docs/evidence/swe_lite_qwen35_9b_skill_pilot_20260704_v7_concise_analysis/`

Control-plane gold and evaluator patches remain outside the repository in temporary directories.

## Repository Validation

- `python -m unittest tests.test_prepare_swe_lite_smoke tests.test_swe_lite_ollama_pilot -v`: 7 passed.
- Python compilation and `git diff --check`: passed.
- `python -m pytest -q`: 101 passed, 22 existing Windows-specific failures.
- `python -m unittest discover -s tests`: collection failed for 10 existing modules because their relative imports require a package top-level.
- Secret scan: no `sk-...`-like value found; only expected API environment-variable references were present.

## Next Experiment

Use an isolated Python environment with Astropy test dependencies, freeze the v7 runner before evaluation, and run multiple SWE-bench Lite instances and seeds. Compare plain, generic workflow skill, and domain-debugging skill as separate preregistered conditions. Add multi-agent conditions only after the single-agent harness produces valid patches reliably.
