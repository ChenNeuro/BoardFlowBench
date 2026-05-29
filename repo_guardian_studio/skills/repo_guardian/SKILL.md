# repo-guardian

## Description

Use this skill when reviewing AI-generated Python code for patch function bloat, unused functions, wrapper functions, duplicate helpers, and messy repo structure.

## Workflow

1. Scan the repository with AST-based function extraction.
2. Detect function smells such as patch-like names, unused functions, wrappers, fragmented helpers, and suspicious file names.
3. Generate a compact review prompt from the repo profile and smell report.
4. Produce a human-readable review using an OpenAI-compatible model or the local mock fallback.
5. Suggest a practical cleanup plan that preserves intentional public entry points.

