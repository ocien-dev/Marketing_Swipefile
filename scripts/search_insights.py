#!/usr/bin/env python
"""Search consolidated Marketing Swipe File insights locally."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from msf_common import (
    CURATED_UNAVAILABLE_STATE,
    UNFOUNDED_OUTPUT_BANNER,
    as_list,
    data_path,
    first_evidence,
    insight_text,
    load_json,
    matches_process_tags,
    normalize_process_tags,
    normalize_text,
    retrieval_source_state,
    tokens,
    write_json,
    write_text,
)


DEFAULT_MASTERS = {
    "raw": data_path("exports", "insights_master.json"),
    "v1": data_path("exports", "insights_master.json"),
    "v2": data_path("exports", "insights_v2_master.json"),
    "curated": data_path("exports", "curated_insights.json"),
}


def load_master(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    insights = payload.get("insights", [])
    return [item for item in insights if isinstance(item, dict)]


def resolve_master_path(args: argparse.Namespace) -> Path:
    if args.master:
        return args.master
    return DEFAULT_MASTERS[args.source]


def contains_filter(values: list[Any], expected: str | None) -> bool:
    if not expected:
        return True
    expected_norm = normalize_text(expected)
    return any(expected_norm == normalize_text(value) or expected_norm in normalize_text(value) for value in values)


def passes_filters(insight: dict[str, Any], args: argparse.Namespace) -> bool:
    if args.theme and not contains_filter(as_list(insight.get("themes")), args.theme):
        return False
    if args.level and normalize_text(insight.get("level")) != normalize_text(args.level):
        return False
    if args.insight_type and normalize_text(insight.get("insight_type")) != normalize_text(args.insight_type):
        return False
    if args.source_kind and normalize_text(insight.get("source_kind")) != normalize_text(args.source_kind):
        return False
    if args.episode and normalize_text(args.episode) not in normalize_text(
        f"{insight.get('episode_video_id')} {insight.get('episode_title')}"
    ):
        return False
    if args.asset_id and normalize_text(insight.get("asset_id")) != normalize_text(args.asset_id):
        return False
    if args.applicability and not contains_filter(as_list(insight.get("applicability")), args.applicability):
        return False
    if not matches_process_tags(insight, args.process_tags, args.process_tag_mode):
        return False
    confidence = insight.get("confidence_score")
    confidence_value = float(confidence) if isinstance(confidence, (int, float)) else 0.0
    if confidence_value < args.min_confidence:
        return False
    return True


def query_score(insight: dict[str, Any], query: str | None) -> float:
    confidence = insight.get("confidence_score")
    confidence_value = float(confidence) if isinstance(confidence, (int, float)) else 0.0
    if not query:
        return confidence_value
    query_tokens = tokens(query)
    haystack = insight_text(insight, include_evidence=True)
    haystack_tokens = tokens(haystack)
    if not query_tokens:
        return confidence_value
    matched = len(query_tokens & haystack_tokens)
    phrase_bonus = 2 if normalize_text(query) in normalize_text(haystack) else 0
    return matched * 10 + phrase_bonus + confidence_value


def search(insights: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    results = []
    for insight in insights:
        if not passes_filters(insight, args):
            continue
        score = query_score(insight, args.query)
        if args.query and score <= 1:
            continue
        results.append({"score": round(score, 4), **insight})
    return sorted(results, key=lambda item: (-float(item.get("score", 0)), str(item.get("insight_id") or "")))[: args.limit]


def render_markdown(results: list[dict[str, Any]], args: argparse.Namespace) -> str:
    lines = []
    if getattr(args, "retrieval_state", None) == CURATED_UNAVAILABLE_STATE:
        lines.extend([UNFOUNDED_OUTPUT_BANNER, ""])
    lines.extend(
        [
        "# Marketing Swipe File Search Results",
        "",
        f"- Query: {args.query or 'N/A'}",
        f"- Source: {args.source}",
        f"- Source path: {resolve_master_path(args)}",
        f"- Retrieval state: {getattr(args, 'retrieval_state', 'available')}",
        f"- Process tags: {', '.join(args.process_tags) if args.process_tags else 'N/A'}",
        f"- Results: {len(results)}",
        "",
        ]
    )
    for index, insight in enumerate(results, start=1):
        evidence = first_evidence(insight)
        themes = ", ".join(str(item) for item in as_list(insight.get("themes")))
        lines.extend(
            [
                f"## {index}. {insight.get('title')}",
                "",
                f"- Insight ID: {insight.get('insight_id')}",
                f"- Episode: {insight.get('episode_video_id')} - {insight.get('episode_title')}",
                f"- Level/type: {insight.get('level')} / {insight.get('insight_type')}",
                f"- Themes: {themes}",
                f"- Process tags: {', '.join(str(item) for item in as_list(insight.get('process_tags')))}",
                f"- Confidence: {insight.get('confidence_score')}",
                f"- Score: {insight.get('score')}",
                "",
                str(insight.get("insight_ptbr") or ""),
                "",
                f"> {evidence.get('quote_original', '')}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=Path, help="Override source master path.")
    parser.add_argument("--source", choices=sorted(DEFAULT_MASTERS), default="curated", help="Source layer to use when --master is omitted.")
    parser.add_argument("--query", help="Text query")
    parser.add_argument("--theme", help="Filter by theme")
    parser.add_argument("--level", choices=["strategic", "tactical", "operational"])
    parser.add_argument("--insight-type", help="Filter by insight_type")
    parser.add_argument("--source-kind", choices=["transcript", "description", "comment", "asset"])
    parser.add_argument("--episode", help="Filter by episode id or title")
    parser.add_argument("--asset-id", help="Filter by asset id")
    parser.add_argument("--applicability", help="Filter by applicability role")
    parser.add_argument("--process-tags", nargs="+", help="Filter by process-* tags. Accepts repeated values or comma-separated lists.")
    parser.add_argument("--process-tag-mode", choices=["any", "all"], default="any", help="Require any or all requested process tags.")
    parser.add_argument("--min-confidence", default=0.0, type=float)
    parser.add_argument("--limit", default=20, type=int)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--output", type=Path, help="Optional output path")
    args = parser.parse_args()
    args.process_tags = normalize_process_tags(args.process_tags)

    master_path = resolve_master_path(args)
    args.retrieval_state = retrieval_source_state(args.source, master_path)
    insights = [] if args.retrieval_state == CURATED_UNAVAILABLE_STATE else load_master(master_path)
    results = search(insights, args)
    if args.format == "json":
        payload = {
            "banner": UNFOUNDED_OUTPUT_BANNER if args.retrieval_state == CURATED_UNAVAILABLE_STATE else None,
            "retrieval_state": args.retrieval_state,
            "query": args.query,
            "source": args.source,
            "source_path": str(master_path),
            "process_tags": args.process_tags,
            "process_tag_mode": args.process_tag_mode,
            "result_count": len(results),
            "results": results,
        }
        if args.output:
            write_json(args.output, payload)
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        markdown = render_markdown(results, args)
        if args.output:
            write_text(args.output, markdown)
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
