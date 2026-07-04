# RepoFlow SWE Lite Qwen 9B Multi-Seed Docker Pilot

Date: 2026-07-04

## Environment

- Docker Desktop: `4.80.0`
- Docker Engine: `29.6.1`
- Engine mode: Linux containers through WSL 2
- Model: `qwen3.5:9b` through Ollama `0.31.1`
- Instance: `astropy__astropy-12907`
- Base commit: `d16bfe05a744909de4b27f5875fe0d4ed41ce607`
- Official SWE-bench score: no

Docker passed `hello-world`. The targeted evaluator image used Python 3.9 and the pinned Astropy dependencies from the official SWE-bench harness constants. Docker Hub authentication was unreachable through the local DNS path, so the image used the Microsoft Dev Containers Python 3.9 base from MCR.

The official full harness was not started because the machine had about 43 GB free while the upstream Docker Desktop guidance recommends about 120 GB. The evaluation below is a Docker-isolated targeted smoke, not an official benchmark score.

## Design

Two single-agent conditions were run with the same task, source context, editable path, two-stage analysis protocol, and evaluator isolation:

- `plain`
- mandatory `repoflow-task-agent` skill

Seeds were `11`, `23`, and `47`.

At `temperature=0`, all six runs reproduced the same failures: plain generated non-matching source snippets and skill generated no-op edits. This is a deterministic replication, not three independent samples.

At `temperature=0.2`, the outputs varied and were evaluated as the stochastic multi-seed condition.

## Generation Results

| Condition | Format accepted | Patch applied | Local validation |
| --- | ---: | ---: | --- |
| Plain | 2/3 | 2/3 | Blocked by local Astropy test dependencies |
| Skill | 3/3 | 3/3 | Blocked by local Astropy test dependencies |

The skill improved patch applicability in this three-seed sample. That is a formatting/workflow result, not a correctness result.

## Docker Evaluation

The evaluator applied the public test patch only after generation. Neither gold nor evaluator patches were present in model context.

| Case | Targeted pytest result |
| --- | --- |
| Baseline | 2 failed, 13 passed |
| Gold control | 15 passed |
| Seed 11 skill | 13 failed, 2 passed |
| Seed 23 plain | 5 failed, 10 passed |
| Seed 23 skill | 2 failed, 13 passed |
| Seed 47 plain | 2 failed, 13 passed |
| Seed 47 skill | 10 failed, 5 passed |

The baseline/gold controls show that the targeted Docker evaluator distinguishes the known failing state from the reference repair. All five model patches failed. Resolution was therefore `0/3` for plain and `0/3` for skill when format failures are included.

## Conclusion

There is no correctness improvement from the mandatory skill on this instance. The skill increased the chance of producing an applicable patch at `temperature=0.2`, but its patches did not reduce the failing-test count consistently and sometimes introduced broad regressions.

This remains a one-instance result. It does not support a multi-agent claim. A defensible next experiment should add a repair/reflection stage that receives Docker test diagnostics, then preregister multiple instances before comparing single-agent and multi-agent conditions.

## Evidence

- Zero-temperature runs: `docs/evidence/swe_lite_qwen35_9b_multiseed_20260704_seed*/`
- Temperature 0.2 runs: `docs/evidence/swe_lite_qwen35_9b_temp02_20260704_seed*/`
- Docker evaluator logs and summary: `docs/evidence/swe_lite_astropy_12907_docker_eval_20260704/`
- Docker installation summary: `docs/evidence/docker_install_20260704_summary.json`

The local Docker image `repoflow/astropy-12907-smoke:20260704` is not committed to Git.
