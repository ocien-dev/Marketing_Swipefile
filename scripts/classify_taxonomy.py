#!/usr/bin/env python
"""Classify insights against the local taxonomy with deterministic heuristics."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from msf_common import (
    as_list,
    insight_text,
    load_json,
    normalize_text,
    unique_preserve_order,
    write_json,
    write_text,
)


THEME_APPLICATIONS = {
    "VSL": ["copywriter de VSLs", "copy strategist"],
    "copy": ["copy strategist"],
    "hooks": ["copywriter de anuncios", "copywriter de VSLs"],
    "anuncios": ["copywriter de anuncios"],
    "criativos": ["copywriter de anuncios"],
    "ofertas": ["CMO", "copy strategist"],
    "funil": ["CMO"],
    "checkout": ["CMO"],
    "gestao": ["COO"],
    "produto": ["head de produto"],
    "avatar": ["copy strategist", "CMO"],
    "prova social": ["copy strategist"],
    "low ticket": ["CMO", "copy strategist"],
    "high ticket": ["CMO", "copy strategist"],
    "quiz": ["copywriter de quiz"],
    "webinar": ["copywriter de webinarios"],
}

TASK_KEYWORDS = {
    "awareness": ["hook", "gancho", "atencao", "criativo", "topo", "headline"],
    "conversion": ["venda", "conversao", "oferta", "checkout", "cta", "pitch", "vsl"],
    "retention": ["retencao", "churn", "recompra", "recorrencia", "pos-compra"],
}

PROCESS_MATCH_FIELDS = [
    "canonical_title",
    "title",
    "specific_takeaway",
    "insight_ptbr",
    "summary_ptbr",
    "use_case",
    "when_to_use",
    "when_not_to_use",
    "themes",
    "subthemes",
    "funnel_stages",
    "niches",
]


def taxonomy_terms(taxonomy: dict[str, Any], term_type: str) -> list[dict[str, Any]]:
    return [term for term in taxonomy.get("terms", []) if term.get("term_type") == term_type and term.get("status") == "active"]


def active_process_ids(taxonomy: dict[str, Any]) -> set[str]:
    return {str(term.get("id")) for term in taxonomy_terms(taxonomy, "process") if term.get("id")}


def match_terms(text: str, terms: list[dict[str, Any]]) -> list[str]:
    normalized = normalize_text(text)
    matches: list[str] = []
    for term in terms:
        candidates = [term.get("term"), *as_list(term.get("synonyms"))]
        for candidate in candidates:
            candidate_norm = normalize_text(candidate)
            if candidate_norm and candidate_norm in normalized:
                matches.append(term.get("term"))
                break
    return unique_preserve_order(matches)


def process_match_text(insight: dict[str, Any]) -> str:
    parts: list[str] = []
    for field in PROCESS_MATCH_FIELDS:
        value = insight.get(field)
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif value:
            parts.append(str(value))
    return " ".join(parts)


def candidate_match_position(normalized_text: str, candidate: Any) -> int | None:
    candidate_norm = normalize_text(candidate)
    if not candidate_norm:
        return None
    pattern = re.compile(rf"(?<![a-z0-9]){re.escape(candidate_norm)}(?![a-z0-9])")
    match = pattern.search(normalized_text)
    return match.start() if match else None


def match_process_tags(insight: dict[str, Any], taxonomy: dict[str, Any], max_tags: int) -> list[str]:
    normalized_text = normalize_text(process_match_text(insight))
    valid_process_ids = active_process_ids(taxonomy)
    existing_tags = [
        str(tag)
        for tag in as_list(insight.get("process_tags"))
        if str(tag) in valid_process_ids
    ]
    matches: list[tuple[int, int, str]] = []
    for term in taxonomy_terms(taxonomy, "process"):
        process_id = str(term.get("id") or "")
        if not process_id:
            continue
        positions: list[int] = []
        candidates = [term.get("term"), *as_list(term.get("synonyms"))]
        for candidate in candidates:
            position = candidate_match_position(normalized_text, candidate)
            if position is not None:
                positions.append(position)
        if positions:
            matches.append((-len(positions), min(positions), process_id))

    matched_tags = [process_id for _, _, process_id in sorted(matches)]
    return unique_preserve_order([*existing_tags, *matched_tags])[:max_tags]


def infer_source_kind(insight: dict[str, Any], top_level_asset_id: str | None) -> str:
    if insight.get("source_kind"):
        return insight["source_kind"]
    if top_level_asset_id or insight.get("asset_id"):
        return "asset"
    for evidence in insight.get("evidence") or []:
        if isinstance(evidence, dict) and evidence.get("asset_id"):
            return "asset"
    return "transcript"


def classify_insight(
    insight: dict[str, Any],
    taxonomy: dict[str, Any],
    top_level_asset_id: str | None,
    max_process_tags: int,
) -> dict[str, Any]:
    classified = dict(insight)
    text = insight_text(classified, include_evidence=True)

    themes = unique_preserve_order([*as_list(classified.get("themes")), *match_terms(text, taxonomy_terms(taxonomy, "theme"))])
    if not themes:
        themes = ["estrategias"]
    classified["themes"] = themes

    funnel_stages = as_list(classified.get("funnel_stages"))
    normalized_text = normalize_text(text)
    for stage, keywords in TASK_KEYWORDS.items():
        if any(keyword in normalized_text for keyword in keywords):
            funnel_stages.append(stage)
    if funnel_stages:
        classified["funnel_stages"] = unique_preserve_order(funnel_stages)

    niches = as_list(classified.get("niches"))
    niches.extend(match_terms(text, taxonomy_terms(taxonomy, "market")))
    if niches:
        classified["niches"] = unique_preserve_order(niches)

    applicability = as_list(classified.get("applicability"))
    for theme in themes:
        applicability.extend(THEME_APPLICATIONS.get(theme, []))
    if not applicability:
        applicability = ["CMO"]
    classified["applicability"] = unique_preserve_order(applicability)

    classified["source_kind"] = infer_source_kind(classified, top_level_asset_id)
    process_tags = match_process_tags(classified, taxonomy, max_process_tags)
    if process_tags:
        classified["process_tags"] = process_tags
    else:
        classified.pop("process_tags", None)
    if not classified.get("review_status"):
        confidence = classified.get("confidence_score")
        confidence_value = float(confidence) if isinstance(confidence, (int, float)) else 0.0
        classified["review_status"] = "auto_accepted" if confidence_value >= 0.75 else "needs_review"
    if "relations" not in classified:
        classified["relations"] = []
    if "subthemes" not in classified:
        classified["subthemes"] = []
    return classified


def classify_payload(payload: dict[str, Any], taxonomy: dict[str, Any], max_process_tags: int = 4) -> dict[str, Any]:
    output = dict(payload)
    top_level_asset_id = payload.get("asset_id")
    output["insights"] = [
        classify_insight(insight, taxonomy, top_level_asset_id, max_process_tags)
        for insight in payload.get("insights", [])
        if isinstance(insight, dict)
    ]
    return output


def process_review_items(input_path: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for insight in payload.get("insights", []):
        if insight.get("process_tags"):
            continue
        items.append(
            {
                "source_file": str(input_path),
                "insight_id": insight.get("insight_id"),
                "episode_video_id": insight.get("episode_video_id"),
                "asset_id": insight.get("asset_id"),
                "title": insight.get("canonical_title") or insight.get("title"),
                "themes": as_list(insight.get("themes")),
                "review_reason": "no_process_term_or_synonym_match",
            }
        )
    return items


def render_process_review_queue(input_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    items = process_review_items(input_path, payload)
    return {
        "schema_version": "1.0",
        "source_file": str(input_path),
        "unmatched_insight_count": len(items),
        "items": items,
    }


def render_report(input_path: Path, payload: dict[str, Any]) -> str:
    theme_counts: dict[str, int] = {}
    process_counts: dict[str, int] = {}
    unmatched_process_count = 0
    for insight in payload.get("insights", []):
        for theme in insight.get("themes") or []:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        process_tags = insight.get("process_tags") or []
        if process_tags:
            for process_tag in process_tags:
                process_counts[str(process_tag)] = process_counts.get(str(process_tag), 0) + 1
        else:
            unmatched_process_count += 1

    lines = [
        f"# Taxonomy Classification - {input_path}",
        "",
        f"Insights classified: {len(payload.get('insights', []))}",
        f"Process-tag review queue: {unmatched_process_count}",
        "",
        "## Theme Counts",
        "",
    ]
    if not theme_counts:
        lines.append("- No themes found.")
    else:
        for theme, count in sorted(theme_counts.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- {theme}: {count}")
    lines.extend(["", "## Process Tag Counts", ""])
    if not process_counts:
        lines.append("- No process tags found.")
    else:
        for process_tag, count in sorted(process_counts.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- {process_tag}: {count}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Path to insights.json")
    parser.add_argument("--output", type=Path, help="Path to write classified insights.json")
    parser.add_argument("--taxonomy", default=Path("data/processed/taxonomy_seed.json"), type=Path)
    parser.add_argument("--report", type=Path, help="Optional markdown report path")
    parser.add_argument("--process-review-queue", type=Path, help="Optional JSON file for insights without process_tags.")
    parser.add_argument("--max-process-tags", type=int, default=4)
    args = parser.parse_args()

    payload = load_json(args.input)
    taxonomy = load_json(args.taxonomy)
    classified = classify_payload(payload, taxonomy, max_process_tags=args.max_process_tags)
    output_path = args.output or args.input
    write_json(output_path, classified)

    report_text = render_report(args.input, classified)
    if args.report:
        write_text(args.report, report_text)
    if args.process_review_queue:
        write_json(args.process_review_queue, render_process_review_queue(args.input, classified))
    print(report_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
