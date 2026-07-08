#!/usr/bin/env python
"""Audit editorial text fields in raw_insights_v2 payloads."""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from msf_common import load_json, normalize_text


EDITORIAL_FIELDS = [
    "canonical_title",
    "specific_takeaway",
    "use_case",
    "when_to_use",
    "when_not_to_use",
]

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


def default_paths(processed_root: Path) -> list[Path]:
    paths = list(processed_root.glob("*/insights_v2.json"))
    paths.extend(processed_root.glob("*/llm_v2_outputs/*.json"))
    return sorted(paths)


def default_generated_text_paths(exports_root: Path) -> list[Path]:
    paths = list(exports_root.glob("*.csv"))
    paths.extend(exports_root.glob("*.md"))
    return sorted(path for path in paths if path.is_file())


def has_non_ascii(value: str) -> bool:
    return any(ord(char) > 127 for char in value)


def broken_accent_deletion_matches(value: str) -> list[str]:
    return sorted({match.group(1).lower() for match in BROKEN_ACCENT_DELETION_RE.finditer(value)})


def audit_payload(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    findings: list[dict[str, Any]] = []
    for insight in payload.get("insights", []):
        insight_id = str(insight.get("insight_id") or "")
        for field in EDITORIAL_FIELDS:
            value = insight.get(field)
            if not isinstance(value, str):
                continue
            non_ascii = has_non_ascii(value)
            orphan_question = "?" in value
            broken_accent_patterns = broken_accent_deletion_matches(value)
            if non_ascii or orphan_question or broken_accent_patterns:
                findings.append(
                    {
                        "path": str(path),
                        "insight_id": insight_id,
                        "field": field,
                        "non_ascii": non_ascii,
                        "orphan_question": orphan_question,
                        "broken_accent_patterns": broken_accent_patterns,
                        "value": value,
                    }
                )
    return findings


def read_generated_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def audit_generated_text(path: Path) -> list[dict[str, Any]]:
    text = read_generated_text(path)
    findings: list[dict[str, Any]] = []
    for match in BROKEN_ACCENT_DELETION_RE.finditer(text):
        start = match.start()
        line_number = text.count("\n", 0, start) + 1
        excerpt_start = max(0, start - 50)
        excerpt_end = min(len(text), match.end() + 50)
        findings.append(
            {
                "finding_type": "broken_accent_deletion",
                "path": str(path),
                "pattern": match.group(1),
                "line": line_number,
                "excerpt": " ".join(text[excerpt_start:excerpt_end].split()),
            }
        )
    return findings


def duplicate_takeaway_paths(paths: list[Path]) -> list[Path]:
    final_paths = [path for path in paths if path.name == "insights_v2.json"]
    return final_paths or paths


def audit_duplicate_takeaways(paths: list[Path]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for path in duplicate_takeaway_paths(paths):
        if not path.exists():
            continue
        payload = load_json(path)
        for insight in payload.get("insights", []):
            takeaway = insight.get("specific_takeaway")
            if not isinstance(takeaway, str):
                continue
            normalized = normalize_text(takeaway)
            if not normalized:
                continue
            grouped[normalized].append(
                {
                    "path": str(path),
                    "insight_id": str(insight.get("insight_id") or ""),
                    "canonical_title": str(insight.get("canonical_title") or ""),
                }
            )

    findings: list[dict[str, Any]] = []
    for normalized, occurrences in sorted(grouped.items()):
        if len(occurrences) <= 1:
            continue
        findings.append(
            {
                "finding_type": "duplicate_takeaway",
                "normalized_takeaway": normalized,
                "occurrences": occurrences,
            }
        )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Optional insights_v2.json files to audit.")
    parser.add_argument("--processed-root", type=Path, default=Path("data/processed"))
    parser.add_argument("--exports-root", type=Path, default=Path("data/exports"))
    parser.add_argument("--skip-generated-text-scan", action="store_true")
    args = parser.parse_args()

    paths = args.paths or default_paths(args.processed_root)
    generated_text_paths = [] if args.skip_generated_text_scan else default_generated_text_paths(args.exports_root)
    findings: list[dict[str, Any]] = []
    for path in paths:
        if path.exists():
            findings.extend(audit_payload(path))
    findings.extend(audit_duplicate_takeaways(paths))
    for path in generated_text_paths:
        findings.extend(audit_generated_text(path))

    if findings:
        print(f"INVALID audit_findings={len(findings)}")
        for item in findings:
            if item.get("finding_type") == "duplicate_takeaway":
                occurrences = " | ".join(
                    f"{occurrence['path']}:{occurrence['insight_id']}:{occurrence['canonical_title']}"
                    for occurrence in item["occurrences"]
                )
                print(
                    f"duplicate_takeaway count={len(item['occurrences'])} "
                    f"value={item['normalized_takeaway']!r} occurrences={occurrences}"
                )
            elif item.get("finding_type") == "broken_accent_deletion":
                print(
                    f"broken_accent_deletion path={item['path']} line={item['line']} "
                    f"pattern={item['pattern']!r} excerpt={item['excerpt']!r}"
                )
            else:
                print(
                    f"{item['path']} {item['insight_id']} {item['field']} "
                    f"non_ascii={item['non_ascii']} orphan_question={item['orphan_question']} "
                    f"broken_accent_patterns={item['broken_accent_patterns']} "
                    f"value={item['value']!r}"
                )
        return 1

    print(f"VALID editorial_text_files={len(paths)} generated_text_files={len(generated_text_paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
