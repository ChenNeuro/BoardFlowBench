"""OpenAI-compatible review call with deterministic local fallback."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


def mock_review(prompt: str) -> str:
    smell_count = prompt.count('"type"')
    return (
        "Repo Manager mock review\n\n"
        f"Detected approximately {smell_count} suspicious signals in the generated prompt. "
        "The main cleanup target is to inspect patch-like names, temporary helpers, wrappers, "
        "and files that look like final/fixed/debug copies.\n\n"
        "Suggested cleanup plan:\n"
        "1. Confirm which suspicious functions are real public entry points.\n"
        "2. Merge duplicate-like date parsing or normalization helpers.\n"
        "3. Inline wrappers that only delegate without adding validation or meaning.\n"
        "4. Rename or remove temporary files after stable code is moved into clear modules.\n"
        "5. Re-run the scanner and keep only intentional warnings documented."
    )


def call_agent(prompt: str) -> str:
    """Call an OpenAI-compatible chat API when configured, otherwise mock."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return mock_review(prompt)

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You review AI-generated Python repositories."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
    except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return mock_review(prompt) + f"\n\nAPI call failed, so this mock review was used. Reason: {exc}"
