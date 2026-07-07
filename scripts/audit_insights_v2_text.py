#!/usr/bin/env python
"""Audit editorial text fields in raw_insights_v2 payloads."""

from __future__ import annotations

import argparse
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


def default_paths(processed_root: Path) -> list[Path]:
    paths = list(processed_root.glob("*/insights_v2.json"))
    paths.extend(processed_root.glob("*/llm_v2_outputs/*.json"))
    return sorted(paths)


def has_non_ascii(value: str) -> bool:
    return any(ord(char) > 127 for char in value)


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
            if non_ascii or orphan_question:
                findings.append(
                    {
                        "path": str(path),
                        "insight_id": insight_id,
                        "field": field,
                        "non_ascii": non_ascii,
                        "orphan_question": orphan_question,
                        "value": value,
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
    args = parser.parse_args()

    paths = args.paths or default_paths(args.processed_root)
    findings: list[dict[str, Any]] = []
    for path in paths:
        if path.exists():
            findings.extend(audit_payload(path))
    findings.extend(audit_duplicate_takeaways(paths))

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
            else:
                print(
                    f"{item['path']} {item['insight_id']} {item['field']} "
                    f"non_ascii={item['non_ascii']} orphan_question={item['orphan_question']} "
                    f"value={item['value']!r}"
                )
        return 1

    print(f"VALID editorial_text_files={len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
