#!/usr/bin/env python
"""Deduplicate and lightly relate Marketing Swipe File insights."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from msf_common import (
    insight_text,
    jaccard,
    load_json,
    normalize_text,
    slugify,
    tokens,
    write_json,
    write_text,
)


def insight_quality_score(insight: dict[str, Any]) -> tuple[float, int, int]:
    confidence = insight.get("confidence_score")
    confidence_value = float(confidence) if isinstance(confidence, (int, float)) else 0.0
    evidence_count = len(insight.get("evidence") or [])
    text_size = len(insight_text(insight, include_evidence=True))
    return confidence_value, evidence_count, text_size


def exact_key(insight: dict[str, Any]) -> str:
    dedupe_key = normalize_text(insight.get("dedupe_key"))
    if dedupe_key:
        return f"dedupe:{dedupe_key}"
    title = slugify(insight.get("title"), max_length=80)
    body = slugify(insight.get("insight_ptbr"), max_length=120)
    return f"text:{title}:{body}"


def relation_exists(insight: dict[str, Any], target_id: str, relation_type: str) -> bool:
    for relation in insight.get("relations") or []:
        if not isinstance(relation, dict):
            continue
        if relation.get("target_insight_id") == target_id and relation.get("relation_type") == relation_type:
            return True
    return False


def add_similarity_relations(insights: list[dict[str, Any]], threshold: float) -> list[dict[str, Any]]:
    token_sets = [tokens(insight_text(insight, include_evidence=False)) for insight in insights]
    for index, insight in enumerate(insights):
        for other_index in range(index):
            score = jaccard(token_sets[index], token_sets[other_index])
            if score < threshold:
                continue
            other = insights[other_index]
            other_id = other.get("insight_id")
            if not other_id or relation_exists(insight, other_id, "similar_to"):
                continue
            relations = insight.setdefault("relations", [])
            relations.append(
                {
                    "target_insight_id": other_id,
                    "relation_type": "similar_to",
                    "rationale": f"Simple text overlap score {score:.2f}.",
                    "confidence_score": round(score, 3),
                }
            )
    return insights


def dedupe(payload: dict[str, Any], similarity_threshold: float) -> tuple[dict[str, Any], dict[str, Any]]:
    insights = [item for item in payload.get("insights", []) if isinstance(item, dict)]
    kept_by_key: dict[str, dict[str, Any]] = {}
    dropped: list[dict[str, Any]] = []

    for insight in insights:
        key = exact_key(insight)
        if key not in kept_by_key:
            kept_by_key[key] = insight
            continue

        current = kept_by_key[key]
        if insight_quality_score(insight) > insight_quality_score(current):
            kept_by_key[key] = insight
            dropped_insight = current
        else:
            dropped_insight = insight

        dropped.append(
            {
                "reason": "duplicate_key",
                "key": key,
                "kept_insight_id": kept_by_key[key].get("insight_id"),
                "dropped_insight_id": dropped_insight.get("insight_id"),
            }
        )

    deduped = list(kept_by_key.values())
    add_similarity_relations(deduped, threshold=similarity_threshold)

    result = dict(payload)
    result["insights"] = deduped
    report = {
        "input_count": len(insights),
        "output_count": len(deduped),
        "dropped_count": len(dropped),
        "similarity_threshold": similarity_threshold,
        "dropped": dropped,
    }
    return result, report


def render_report(input_path: Path, report: dict[str, Any]) -> str:
    lines = [
        f"# Insight Deduplication - {input_path}",
        "",
        f"- Input insights: {report['input_count']}",
        f"- Output insights: {report['output_count']}",
        f"- Dropped duplicates: {report['dropped_count']}",
        f"- Similarity threshold: {report['similarity_threshold']}",
        "",
    ]
    for item in report.get("dropped", []):
        lines.append(
            f"- Dropped {item.get('dropped_insight_id')} as duplicate of "
            f"{item.get('kept_insight_id')} via {item.get('key')}"
        )
    if not report.get("dropped"):
        lines.append("No exact duplicates were dropped.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Path to insights.json")
    parser.add_argument("--output", type=Path, help="Path to write deduped insights.json")
    parser.add_argument("--report", type=Path, help="Optional markdown report path")
    parser.add_argument("--similarity-threshold", default=0.86, type=float)
    args = parser.parse_args()

    payload = load_json(args.input)
    output_payload, report = dedupe(payload, args.similarity_threshold)
    output_path = args.output or args.input
    write_json(output_path, output_payload)

    report_text = render_report(args.input, report)
    if args.report:
        write_text(args.report, report_text)
    print(report_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

