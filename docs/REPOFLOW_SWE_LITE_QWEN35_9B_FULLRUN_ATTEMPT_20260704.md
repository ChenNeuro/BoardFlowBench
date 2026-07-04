# RepoFlow SWE Lite Qwen 9B Full-Run Attempt

Date: 2026-07-04

## Scope

This was an attempted full local SWE-style run for the existing RepoFlow SWE
Lite Astropy pilot.

- Instance: `astropy__astropy-12907`
- Dataset: `princeton-nlp/SWE-bench_Lite`
- Model: `qwen3.5:9b`
- Ollama: `0.31.1`
- Conditions: `plain` and mandatory `repoflow-task-agent`
- Seeds: `101`, `102`, `103`, `104`, `105`, `106`, `107`
- Temperature: `0.2`
- Official SWE-bench score: no

The model never saw `gold_patch.diff` or `test_patch.diff`. The evaluator test
patch was used only after generation by the local runner.

## Environment Result

Docker could not be used for the official/full harness path in this run.

- `docker version` failed because `npipe:////./pipe/dockerDesktopLinuxEngine`
  did not exist.
- `docker desktop status` could not retrieve Docker Desktop status.
- `docker desktop restart` and `docker desktop diagnose` timed out.
- `wsl --shutdown` stopped the WSL distributions, but Docker Desktop still did
  not start the Linux engine after restart.
- `Ubuntu-22.04` still reported Docker Desktop WSL integration as unavailable.
- Native WSL Docker install was not attempted because `sudo -n true` reported
  that a password is required.

Disk space was no longer the limiting factor: Windows had about 180 GB free and
the WSL root filesystem had about 817 GB free during the run.

## Generation Results

Fourteen variant runs were attempted across seven seeds.

| Outcome | Count |
| --- | ---: |
| Patch format failure | 6 |
| Patch applied | 8 |
| Non-official validation passed | 0 |
| Official Docker validation passed | 0 |

Detailed seed results are in:

- `docs/evidence/swe_lite_qwen35_9b_fullrun_attempt_20260704_seed101/`
- `docs/evidence/swe_lite_qwen35_9b_fullrun_attempt_20260704_seed102/`
- `docs/evidence/swe_lite_qwen35_9b_fullrun_attempt_20260704_seed103/`
- `docs/evidence/swe_lite_qwen35_9b_fullrun_attempt_20260704_wsl_seed104/`
- `docs/evidence/swe_lite_qwen35_9b_fullrun_attempt_20260704_wsl_seed105/`
- `docs/evidence/swe_lite_qwen35_9b_fullrun_attempt_20260704_wsl_seed106_noautoload/`
- `docs/evidence/swe_lite_qwen35_9b_fullrun_attempt_20260704_wsl_seed107_noautoload/`

## Local Validation

Windows Python reached dependency failures first because `hypothesis` was not
installed in the base Conda Python.

WSL Python 3.10 was closer to the target environment. A temporary venv installed
focused dependencies including `pytest`, `hypothesis`, `numpy`,
`pytest-astropy`, `pyerfa`, `scipy`, `cython`, and `setuptools-scm`. That moved
validation from missing Python packages to Astropy source build requirements,
but it still could not complete:

- `pip install -e .` failed on old Astropy/setuptools editable-install
  compatibility.
- `python setup.py build_ext --inplace` failed because `Python.h` was missing.
- Installing `python3-dev` was not attempted because WSL sudo requires a
  password.

The local `failed` results in the WSL evidence should therefore be interpreted
as local source-build/test-environment failures, not as valid SWE-bench task
resolution failures.

## Conclusion

This run did not produce evidence that the mandatory RepoFlow skill improves
correctness on the Astropy SWE Lite instance. It did produce additional evidence
that the skill sometimes improves patch applicability, but the evaluation could
not reach a valid Docker-isolated or properly built local Astropy test result.

The next valid step is to restore Docker Desktop Linux engine or run on the
5080 machine with working Docker, then re-evaluate the already generated
patches and future generations in the official SWE-bench harness.
