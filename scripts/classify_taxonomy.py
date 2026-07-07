#!/usr/bin/env python
"""Classify insights against the local taxonomy with deterministic heuristics."""

from __future__ import annotations

import argparse
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


def taxonomy_terms(taxonomy: dict[str, Any], term_type: str) -> list[dict[str, Any]]:
    return [term for term in taxonomy.get("terms", []) if term.get("term_type") == term_type and term.get("status") == "active"]


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


def infer_source_kind(insight: dict[str, Any], top_level_asset_id: str | None) -> str:
    if insight.get("source_kind"):
        return insight["source_kind"]
    if top_level_asset_id or insight.get("asset_id"):
        return "asset"
    for evidence in insight.get("evidence") or []:
        if isinstance(evidence, dict) and evidence.get("asset_id"):
            return "asset"
    return "transcript"


def classify_insight(insight: dict[str, Any], taxonomy: dict[str, Any], top_level_asset_id: str | None) -> dict[str, Any]:
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
    if not classified.get("review_status"):
        confidence = classified.get("confidence_score")
        confidence_value = float(confidence) if isinstance(confidence, (int, float)) else 0.0
        classified["review_status"] = "auto_accepted" if confidence_value >= 0.75 else "needs_review"
    if "relations" not in classified:
        classified["relations"] = []
    if "subthemes" not in classified:
        classified["subthemes"] = []
    return classified


def classify_payload(payload: dict[str, Any], taxonomy: dict[str, Any]) -> dict[str, Any]:
    output = dict(payload)
    top_level_asset_id = payload.get("asset_id")
    output["insights"] = [
        classify_insight(insight, taxonomy, top_level_asset_id)
        for insight in payload.get("insights", [])
        if isinstance(insight, dict)
    ]
    return output


def render_report(input_path: Path, payload: dict[str, Any]) -> str:
    theme_counts: dict[str, int] = {}
    for insight in payload.get("insights", []):
        for theme in insight.get("themes") or []:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1

    lines = [
        f"# Taxonomy Classification - {input_path}",
        "",
        f"Insights classified: {len(payload.get('insights', []))}",
        "",
        "## Theme Counts",
        "",
    ]
    if not theme_counts:
        lines.append("- No themes found.")
    else:
        for theme, count in sorted(theme_counts.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- {theme}: {count}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Path to insights.json")
    parser.add_argument("--output", type=Path, help="Path to write classified insights.json")
    parser.add_argument("--taxonomy", default=Path("data/processed/taxonomy_seed.json"), type=Path)
    parser.add_argument("--report", type=Path, help="Optional markdown report path")
    args = parser.parse_args()

    payload = load_json(args.input)
    taxonomy = load_json(args.taxonomy)
    classified = classify_payload(payload, taxonomy)
    output_path = args.output or args.input
    write_json(output_path, classified)

    report_text = render_report(args.input, classified)
    if args.report:
        write_text(args.report, report_text)
    print(report_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

