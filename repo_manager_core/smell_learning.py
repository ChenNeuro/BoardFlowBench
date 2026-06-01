"""External smell-rule loading and human feedback storage.

Learned behavior lives in .repo_manager/ so keyword policy changes are
auditable, reversible, and independent from packaged default config.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RULES_PATH = ".repo_manager/smell_rules.json"
FEEDBACK_PATH = ".repo_manager/user_feedback.jsonl"
DEFAULT_RULES_PATH = Path(__file__).with_name("default_smell_rules.json")

RULE_CATEGORIES = (
    "patch_keywords",
    "helper_keywords",
    "suspicious_file_keywords",
    "suspicious_directory_keywords",
)

POLICY_SUSPICIOUS = "suspicious"
POLICY_CONTEXTUAL = "contextual"
POLICY_ALLOWED = "allowed"
POLICY_CASE_BY_CASE = "case_by_case"
VALID_POLICIES = {
    POLICY_SUSPICIOUS,
    POLICY_CONTEXTUAL,
    POLICY_ALLOWED,
    POLICY_CASE_BY_CASE,
}

DECISION_TO_POLICY = {
    "always_suspicious": POLICY_SUSPICIOUS,
    "suspicious": POLICY_SUSPICIOUS,
    "contextual": POLICY_CONTEXTUAL,
    "allowed": POLICY_ALLOWED,
    "allowed_naming_convention": POLICY_ALLOWED,
    "case_by_case": POLICY_CASE_BY_CASE,
}


def load_default_smell_rules(path: str | Path = DEFAULT_RULES_PATH) -> dict[str, Any]:
    """Load default smell rules from a JSON or YAML config file."""
    return _normalise_rules(_read_rules_file(Path(path)), default_source="default_config")


def load_smell_rules(
    repo_path: str | Path = ".",
    default_rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load repo-local smell rules, creating them from defaults when missing."""
    rules = _normalise_rules(default_rules or load_default_smell_rules(), default_source="default_config")
    rules_path = Path(repo_path) / RULES_PATH
    if not rules_path.exists():
        rules_path.parent.mkdir(parents=True, exist_ok=True)
        rules_path.write_text(
            json.dumps(rules, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return rules

    learned = _normalise_rules(_read_rules_file(rules_path), default_source="user_feedback")
    return _merge_rules(rules, learned)


def record_feedback(
    repo_path: str | Path,
    *,
    keyword: str,
    decision: str,
    reason: str = "",
    category: str = "patch_keywords",
) -> Path:
    """Append one human feedback event to .repo_manager/user_feedback.jsonl."""
    feedback_path = Path(repo_path) / FEEDBACK_PATH
    feedback_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "category": category,
        "keyword": keyword,
        "decision": decision,
        "policy": _policy_from_decision(decision),
        "reason": reason,
    }
    with feedback_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return feedback_path


def update_smell_rules(
    repo_path: str | Path,
    *,
    keyword: str,
    policy: str,
    category: str = "patch_keywords",
    source: str = "user_feedback",
    reason: str = "",
) -> Path:
    """Persist a learned keyword policy to .repo_manager/smell_rules.json."""
    if category not in RULE_CATEGORIES:
        raise ValueError(f"unknown smell rule category: {category}")

    rules = load_smell_rules(repo_path)
    rules.setdefault(category, {})
    rules[category][keyword] = {
        "policy": _policy_from_decision(policy),
        "source": source,
    }
    if reason:
        rules[category][keyword]["reason"] = reason

    rules_path = Path(repo_path) / RULES_PATH
    rules_path.parent.mkdir(parents=True, exist_ok=True)
    rules_path.write_text(
        json.dumps(rules, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return rules_path


def generate_learned_policy_summary(rules: dict[str, Any]) -> list[dict[str, str]]:
    """Return human-facing policies learned outside default bootstrap rules."""
    summary: list[dict[str, str]] = []
    for category in RULE_CATEGORIES:
        for keyword, rule in sorted(rules.get(category, {}).items()):
            source = str(rule.get("source", "default_config"))
            if source in {"default_bootstrap", "default_config"}:
                continue
            summary.append(
                {
                    "category": category,
                    "keyword": keyword,
                    "policy": str(rule.get("policy", POLICY_SUSPICIOUS)),
                    "source": source,
                    "reason": str(rule.get("reason", "")),
                }
            )
    return summary


def keyword_rule(rules: dict[str, Any], category: str, keyword: str) -> dict[str, str]:
    """Return a normalized rule for one keyword."""
    rule = rules.get(category, {}).get(keyword, {})
    return {
        "policy": _policy_from_decision(str(rule.get("policy", POLICY_SUSPICIOUS))),
        "source": str(rule.get("source", "default_config")),
        "reason": str(rule.get("reason", "")),
    }


def active_keywords(rules: dict[str, Any], category: str) -> list[str]:
    """Return deterministic keywords for a rule category."""
    return sorted(rules.get(category, {}))


def feedback_question(
    *,
    category: str,
    keyword: str,
    observed: list[str],
) -> dict[str, Any]:
    """Build the auditable question object shown in reports."""
    return {
        "category": category,
        "keyword": keyword,
        "observed": observed[:10],
        "question": f'Should "{keyword}" be considered suspicious in this repository?',
        "options": [
            {
                "decision": "always_suspicious",
                "policy": POLICY_SUSPICIOUS,
                "label": "Always suspicious",
            },
            {
                "decision": "contextual",
                "policy": POLICY_CONTEXTUAL,
                "label": "Suspicious only when unused or untested",
            },
            {
                "decision": "allowed",
                "policy": POLICY_ALLOWED,
                "label": "Allowed naming convention",
            },
            {
                "decision": "case_by_case",
                "policy": POLICY_CASE_BY_CASE,
                "label": "Decide case by case",
            },
        ],
    }


def _read_rules_file(path: Path) -> dict[str, Any]:
    if path.suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError as exc:
            raise ValueError("YAML smell rules require PyYAML to be installed") from exc
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"smell rules file must contain an object: {path}")
    return data


def _merge_rules(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = _normalise_rules(base, default_source="default_config")
    for category in RULE_CATEGORIES:
        merged.setdefault(category, {})
        merged[category].update(overrides.get(category, {}))
    return _normalise_rules(merged, default_source="default_config")


def _normalise_rules(raw: dict[str, Any], *, default_source: str) -> dict[str, Any]:
    rules: dict[str, Any] = {"schema_version": int(raw.get("schema_version", 1))}
    for category in RULE_CATEGORIES:
        values = raw.get(category, {})
        if isinstance(values, list):
            values = {keyword: {"policy": POLICY_SUSPICIOUS} for keyword in values}
        rules[category] = {}
        if not isinstance(values, dict):
            continue
        for keyword, value in values.items():
            if isinstance(value, str):
                value = {"policy": value}
            if not isinstance(value, dict):
                continue
            policy = _policy_from_decision(str(value.get("policy", POLICY_SUSPICIOUS)))
            rules[category][str(keyword)] = {
                "policy": policy,
                "source": str(value.get("source", default_source)),
            }
            if value.get("reason"):
                rules[category][str(keyword)]["reason"] = str(value["reason"])
    return rules


def _policy_from_decision(value: str) -> str:
    policy = DECISION_TO_POLICY.get(value, value)
    if policy not in VALID_POLICIES:
        raise ValueError(f"unknown smell rule policy: {value}")
    return policy
