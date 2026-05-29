# RepoGuardian Studio

RepoGuardian Studio is a lightweight Streamlit GUI for reviewing AI-generated Python repositories. It scans Python files with the standard-library AST module, extracts function-level metadata, flags suspicious helper and patch patterns, and generates a human-readable review report.

The project is intentionally small. It does not modify code automatically and it does not require an LLM API key to run.

## Installation

```bash
cd repo_guardian_studio
pip install -r requirements.txt
```

## Run the App

```bash
streamlit run app.py
```

The default repo path points to `demo_repo/messy_ai_case`, which contains intentionally suspicious AI-generated patterns.

## Example Workflow

1. Open the Streamlit app.
2. Keep the default repo path or enter another Python repository path.
3. Click **Check Repo** to scan all Python files recursively.
4. Click **Detect Function Smells** to list suspicious functions and structure warnings.
5. Click **Generate LLM Review** to create a mock review or an API-backed review if `OPENAI_API_KEY` is configured.

## Controls

- **Check Repo** scans every `.py` file under the selected repository while skipping common ignored directories such as `.git`, `venv`, `__pycache__`, `dist`, and `node_modules`.
- **Check File** scans one Python file using the same AST extraction logic.
- **Detect Function Smells** flags patch-like names, unused functions, thin wrappers, fragmented helpers, suspicious file names, and suspicious repository structure.
- **Generate LLM Review** builds a compact review prompt and calls an OpenAI-compatible API when configured. Without an API key, it returns a deterministic local mock review.

## LLM Configuration

No API key is required. To use a real OpenAI-compatible endpoint, set:

```bash
set OPENAI_API_KEY=your_key
set OPENAI_MODEL=gpt-4o-mini
set OPENAI_BASE_URL=https://api.openai.com/v1
```

`OPENAI_MODEL` and `OPENAI_BASE_URL` are optional.

## Limitations

- Call graph detection is name-based and does not resolve imports or dynamic dispatch.
- Unused function warnings may include framework entry points or functions called from outside the scanned repo.
- Wrapper detection is heuristic and should be reviewed by a human.
- Comment extraction only captures simple contiguous comments immediately above function definitions.
- The app does not implement automatic cleanup or code modification.

## Future Work

- Add import-aware call graph resolution.
- Group duplicate-like helpers by body similarity.
- Add richer repo structure scoring.
- Add configurable ignore patterns.
- Add real Codex, Claude, or OpenCode adapters behind the existing placeholder module.

