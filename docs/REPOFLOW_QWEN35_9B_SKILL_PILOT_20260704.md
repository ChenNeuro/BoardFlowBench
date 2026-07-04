# RepoFlow Qwen3.5 9B Skill Pilot - 2026-07-04

## Scope

This local pilot compared a plain Qwen/Ollama coding prompt against a RepoFlow-style mandatory skill packet on the public Expense Lite seed repository.

- Model: `qwen3.5:9b`
- Ollama: `0.31.1`
- Source repo: `../ExpenseLiteBenchDemo`
- Seed commit: `30ce6f0`
- Tasks: `B001` then `B002`
- Variants: `plain`, `repoflow_skill`
- Harness: `scripts/ollama_repoflow_skill_pilot.py`
- Skill packet: `skills/repoflow-task-agent/SKILL.md`

This is not an official SWE-bench or hidden-oracle run. Docker was not available in the local PowerShell environment, and the private `ExpenseLiteBenchOracles` repository was unavailable.

## Evidence

Primary evidence is stored under `docs/evidence/`:

- `repoflow_qwen35_9b_skill_pilot_20260704_summary.json`
- `repoflow_qwen35_9b_skill_pilot_20260704_runs.jsonl`
- `repoflow_qwen35_9b_skill_pilot_20260704_v1_prompt_skill_only.jsonl`
- `repoflow_qwen35_9b_skill_pilot_20260704_v2_hard_whitelist_regeneration.jsonl`
- `repoflow_qwen35_9b_skill_pilot_20260704_v3_overconstrained_repair_rule.jsonl`
- `repoflow_qwen35_9b_skill_pilot_20260704_final_skill_sanity_summary.json`

The JSONL files contain compact run summaries from the local pilot script. They do not include full temporary workspaces or full prompt/response files.

## Results

| Batch | Harness / skill condition | Plain B002 | Skill B002 | Main observation |
| --- | --- | ---: | ---: | --- |
| v1 | Prompt-level skill only | 0/5 | 0/5 | Plain usually returned empty CSV records; skill consistently attempted disallowed `src/expense_lite/__init__.py` edits. |
| v2 | Hard allowed-path whitelist plus format/path regeneration | 0/5 | 4/5 | Harness-level enforcement converted scope failures into repairable failures and produced the strongest skill signal. |
| v3 | Added over-specific B002 repair guidance | 0/5 | 0/5 | Skill regressed, mostly via circular imports or misplaced validation edits. |
| sanity | Current skill after adding normalized-date guidance | n/a | 0/1 | The model failed before editing because B002 responses were invalid JSON after all format retries. |

B001 passed for both variants in all batch runs. B001 is too easy to measure uplift.

## Interpretation

The useful signal is not that a prompt-only skill helps. It did not. The useful signal is that a skill packet plus harness-level control can help: v2 improved `repoflow_skill` B002 from 0/5 to 4/5 while plain remained 0/5.

The negative signal is also important. More detailed skill rules can make this small model worse. The v3 repair rule tried to prevent date-parser duplication, but it pushed the model toward circular imports and misplaced validation edits.

For `qwen3.5:9b`, the next improvement should be harness-side, not more prose:

- Keep allowed-path enforcement outside the model.
- Use smaller patch-oriented outputs or one-file-at-a-time generation to reduce invalid JSON.
- Add deterministic post-generation checks for common B002 failure modes: raw slash dates, empty record lists, circular imports, and missing amount conversion.
- Re-run 5x batches only after the output protocol is simplified.

## Commands

Representative commands used:

```powershell
python -m py_compile scripts\ollama_repoflow_skill_pilot.py
python scripts\ollama_repoflow_skill_pilot.py --tasks B001 B002 --max-repairs 2
python scripts\ollama_repoflow_skill_pilot.py --tasks B001 B002 --max-repairs 2 --max-format-retries 2
python scripts\ollama_repoflow_skill_pilot.py --tasks B001 B002 --variant repoflow_skill --max-repairs 2 --max-format-retries 2
```

## Current Recommendation

Do not proceed to a full SWE-style pilot from these results. The next local step is to simplify the model output protocol and re-run the v2 condition. Treat v2 as the promising harness design and v3 as evidence that over-specific skill text can harm local 9B reliability.
