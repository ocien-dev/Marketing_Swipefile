#!/usr/bin/env python
"""Audit Marketing Swipe File insights for required fields and evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_INSIGHT_FIELDS = [
    "insight_id",
    "title",
    "insight_ptbr",
    "level",
    "insight_type",
    "themes",
    "applicability",
    "evidence",
    "confidence_score",
    "source_agent",
    "dedupe_key",
]

REQUIRED_EVIDENCE_FIELDS = [
    "evidence_id",
    "quote_original",
    "evidence_strength",
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def audit(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    insights = payload.get("insights", [])
    if not isinstance(insights, list):
        return ["Top-level `insights` must be a list."]

    seen_ids: set[str] = set()
    seen_dedupe: set[str] = set()
    for index, insight in enumerate(insights):
        prefix = f"insights[{index}]"
        if not isinstance(insight, dict):
            issues.append(f"{prefix} must be an object.")
            continue

        for field in REQUIRED_INSIGHT_FIELDS:
            if field not in insight or insight[field] in (None, "", []):
                issues.append(f"{prefix}.{field} is required.")

        insight_id = insight.get("insight_id")
        if insight_id in seen_ids:
            issues.append(f"{prefix}.insight_id duplicates {insight_id}.")
        if insight_id:
            seen_ids.add(insight_id)

        dedupe_key = insight.get("dedupe_key")
        if dedupe_key in seen_dedupe:
            issues.append(f"{prefix}.dedupe_key duplicates {dedupe_key}.")
        if dedupe_key:
            seen_dedupe.add(dedupe_key)

        confidence = insight.get("confidence_score")
        if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
            issues.append(f"{prefix}.confidence_score must be between 0 and 1.")

        evidence_items = insight.get("evidence", [])
        if not isinstance(evidence_items, list) or not evidence_items:
            issues.append(f"{prefix}.evidence must contain at least one evidence item.")
            continue

        for evidence_index, evidence in enumerate(evidence_items):
            evidence_prefix = f"{prefix}.evidence[{evidence_index}]"
            if not isinstance(evidence, dict):
                issues.append(f"{evidence_prefix} must be an object.")
                continue
            for field in REQUIRED_EVIDENCE_FIELDS:
                if field not in evidence or evidence[field] in (None, ""):
                    issues.append(f"{evidence_prefix}.{field} is required.")

            has_locator = any(
                evidence.get(field) not in (None, "")
                for field in [
                    "segment_id",
                    "start_seconds",
                    "page_number",
                    "sheet_name",
                    "cell_range",
                    "slide_number",
                    "asset_id",
                    "episode_video_id",
                ]
            )
            if not has_locator:
                issues.append(f"{evidence_prefix} needs at least one locator.")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Path to insights.json")
    parser.add_argument("--report", type=Path, help="Optional audit report path")
    args = parser.parse_args()

    payload = load_json(args.input)
    issues = audit(payload)
    lines = [f"# Insight Audit - {args.input}", ""]
    if issues:
        lines.append("Status: failed")
        lines.append("")
        for issue in issues:
            lines.append(f"- {issue}")
    else:
        lines.append("Status: passed")
        lines.append("")
        lines.append(f"Insights audited: {len(payload.get('insights', []))}")

    report = "\n".join(lines) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8", newline="\n")
    print(report)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())

