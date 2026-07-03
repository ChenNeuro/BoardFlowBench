"""Minimal MiniMax API smoke test.

The script intentionally reads credentials only from environment variables and
never prints the credential value.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any


DEFAULT_BASE_URL = "https://api.minimaxi.com/v1"
DEFAULT_MODEL = "MiniMax-M3"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a minimal MiniMax chat-completions smoke test.")
    parser.add_argument("--base-url", default=os.getenv("MINIMAX_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--model", default=os.getenv("MINIMAX_MODEL", DEFAULT_MODEL))
    parser.add_argument("--prompt", default="Return exactly: repoflow-minimax-ok")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("MINIMAX_API_KEY is not set", file=sys.stderr)
        return 2
    if _looks_like_placeholder(api_key):
        print("MINIMAX_API_KEY looks like a placeholder; paste the real key without angle brackets.", file=sys.stderr)
        return 2

    payload = {
        "model": args.model,
        "messages": [
            {
                "role": "user",
                "content": args.prompt,
            }
        ],
        "temperature": 0,
    }
    url = args.base_url.rstrip("/") + "/chat/completions"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"MiniMax HTTP {exc.code}: {_truncate(body)}", file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"MiniMax request failed: {exc}", file=sys.stderr)
        return 1

    content = _first_message_content(data)
    if not content:
        print("MiniMax response did not include a chat message", file=sys.stderr)
        print(_truncate(json.dumps(data, ensure_ascii=False)), file=sys.stderr)
        return 1
    print(content)
    usage = data.get("usage")
    if isinstance(usage, dict):
        print("usage:", json.dumps(usage, sort_keys=True))
    return 0


def _first_message_content(data: dict[str, Any]) -> str:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    message = first.get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    return content if isinstance(content, str) else ""


def _truncate(value: str, limit: int = 1000) -> str:
    return value if len(value) <= limit else value[:limit] + "...<truncated>"


def _looks_like_placeholder(value: str) -> bool:
    stripped = value.strip()
    return (
        stripped.startswith("<")
        or stripped.endswith(">")
        or any(ord(char) > 127 for char in stripped)
    )


if __name__ == "__main__":
    raise SystemExit(main())
