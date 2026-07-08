"""Shared helpers for Marketing Swipe File local scripts."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable


BROKEN_ACCENT_DELETION_PATTERNS = [
    "anotaes",
    "cdigo",
    "comeou",
    "contedo",
    "contm",
    "difcil",
    "edio",
    "fcil",
    "histrias",
    "lanamento",
    "mtodo",
    "negcio",
    "nvel",
    "possvel",
    "seleo",
    "variaao",
    "varivel",
    "vdeo",
    "vocs",
]

BROKEN_ACCENT_DELETION_RE = re.compile(
    r"(?<!\w)("
    + "|".join(re.escape(pattern) for pattern in BROKEN_ACCENT_DELETION_PATTERNS)
    + r")(?!\w)",
    re.IGNORECASE,
)


def broken_accent_deletion_matches(value: Any) -> list[str]:
    text = "" if value is None else str(value)
    return sorted({match.group(1).lower() for match in BROKEN_ACCENT_DELETION_RE.finditer(text)})


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(payload, file, ensure_ascii=True, indent=2)
        file.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    ascii_text = ascii_text.lower()
    return re.sub(r"\s+", " ", ascii_text).strip()


def slugify(value: Any, max_length: int = 120) -> str:
    normalized = normalize_text(value)
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    if max_length and len(slug) > max_length:
        slug = slug[:max_length].rstrip("-")
    return slug or "item"


def tokens(value: Any) -> set[str]:
    return set(re.findall(r"[a-z0-9]{3,}", normalize_text(value)))


def jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def unique_preserve_order(values: Iterable[Any]) -> list[Any]:
    seen: set[str] = set()
    result: list[Any] = []
    for value in values:
        key = normalize_text(value)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def split_filter_values(values: Any) -> list[str]:
    result: list[str] = []
    for value in as_list(values):
        if value is None:
            continue
        for part in re.split(r"[,;]", str(value)):
            item = part.strip()
            if item:
                result.append(item)
    return result


def normalize_process_tag(value: Any) -> str:
    tag = slugify(value)
    if not tag:
        return ""
    if tag.startswith("process-"):
        return tag
    return f"process-{tag}"


def normalize_process_tags(values: Any) -> list[str]:
    return [
        str(item)
        for item in unique_preserve_order(
            normalize_process_tag(value) for value in split_filter_values(values)
        )
        if item
    ]


def insight_process_tags(insight: dict[str, Any]) -> list[str]:
    return normalize_process_tags(insight.get("process_tags"))


def matches_process_tags(insight: dict[str, Any], expected_tags: Any, mode: str = "any") -> bool:
    expected = set(normalize_process_tags(expected_tags))
    if not expected:
        return True
    current = set(insight_process_tags(insight))
    if mode == "all":
        return expected <= current
    return bool(expected & current)


def insight_text(insight: dict[str, Any], include_evidence: bool = True) -> str:
    parts = [
        insight.get("canonical_title"),
        insight.get("title"),
        insight.get("specific_takeaway"),
        insight.get("insight_original"),
        insight.get("insight_ptbr"),
        insight.get("summary_ptbr"),
        insight.get("use_case"),
        insight.get("when_to_use"),
        insight.get("when_not_to_use"),
        " ".join(str(item) for item in as_list(insight.get("themes"))),
        " ".join(str(item) for item in as_list(insight.get("subthemes"))),
        " ".join(str(item) for item in as_list(insight.get("applicability"))),
        " ".join(str(item) for item in as_list(insight.get("process_tags"))),
    ]
    if include_evidence:
        for evidence in as_list(insight.get("evidence")):
            if isinstance(evidence, dict):
                parts.append(evidence.get("quote_original"))
                parts.append(evidence.get("quote_ptbr"))
    return " ".join(str(part) for part in parts if part)


def first_evidence(insight: dict[str, Any]) -> dict[str, Any]:
    evidence_items = insight.get("evidence") or []
    if isinstance(evidence_items, list) and evidence_items and isinstance(evidence_items[0], dict):
        return evidence_items[0]
    return {}
