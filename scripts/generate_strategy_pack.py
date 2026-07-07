#!/usr/bin/env python
"""Generate a local evidence-backed strategy pack from consolidated insights."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from msf_common import as_list, first_evidence, load_json, normalize_text, tokens, write_json, write_text


TASK_THEMES = {
    "vsl": ["VSL", "copy", "hooks", "ofertas", "funil", "avatar", "prova social", "low ticket", "high ticket"],
    "anuncios": ["anuncios", "criativos", "hooks", "copy", "avatar", "prova social", "ofertas"],
    "ads": ["anuncios", "criativos", "hooks", "copy", "avatar", "prova social", "ofertas"],
    "offer": ["ofertas", "preco", "prova social", "avatar", "funil"],
    "oferta": ["ofertas", "preco", "prova social", "avatar", "funil"],
    "quiz": ["quiz", "avatar", "ofertas", "copy", "funil"],
    "webinar": ["webinar", "copy", "ofertas", "prova social", "funil"],
}

TASK_KEYWORDS = {
    "vsl": ["vsl", "lead", "mecanismo", "promessa", "objecao", "prova", "cta", "low ticket"],
    "anuncios": ["anuncio", "hook", "criativo", "angulo", "script", "teste", "trafego"],
    "ads": ["anuncio", "hook", "criativo", "angulo", "script", "teste", "trafego"],
    "offer": ["oferta", "bonus", "garantia", "preco", "stack", "urgencia"],
    "oferta": ["oferta", "bonus", "garantia", "preco", "stack", "urgencia"],
    "quiz": ["quiz", "diagnostico", "pergunta", "resultado", "ponte"],
    "webinar": ["webinar", "aula", "pitch", "apresentacao", "evento"],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_insights(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    return [item for item in payload.get("insights", []) if isinstance(item, dict)]


def theme_score(insight: dict[str, Any], desired_themes: list[str]) -> float:
    themes = [normalize_text(theme) for theme in as_list(insight.get("themes"))]
    desired = [normalize_text(theme) for theme in desired_themes]
    return sum(1 for theme in themes if theme in desired) * 8


def keyword_score(insight: dict[str, Any], keywords: list[str], briefing_terms: set[str]) -> float:
    text_terms = tokens(
        " ".join(
            [
                str(insight.get("title") or ""),
                str(insight.get("insight_ptbr") or ""),
                " ".join(str(item) for item in as_list(insight.get("themes"))),
                " ".join(str(item) for item in as_list(insight.get("applicability"))),
            ]
        )
    )
    score = sum(1 for keyword in keywords if normalize_text(keyword) in " ".join(text_terms)) * 5
    score += len(text_terms & briefing_terms) * 3
    return score


def confidence_score(insight: dict[str, Any]) -> float:
    confidence = insight.get("confidence_score")
    return float(confidence) if isinstance(confidence, (int, float)) else 0.0


def rank_insights(insights: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    task_key = normalize_text(args.task or "")
    desired_themes = TASK_THEMES.get(task_key, [])
    keywords = TASK_KEYWORDS.get(task_key, [])
    briefing_terms = tokens(" ".join(str(value or "") for value in [args.product, args.avatar, args.market, args.asset_type, args.query]))
    ranked = []
    for insight in insights:
        confidence = confidence_score(insight)
        if confidence < args.min_confidence:
            continue
        score = (
            theme_score(insight, desired_themes)
            + keyword_score(insight, keywords, briefing_terms)
            + confidence
            + len(insight.get("evidence") or []) * 0.5
        )
        if args.query:
            query_terms = tokens(args.query)
            insight_terms = tokens(json.dumps(insight, ensure_ascii=True))
            score += len(query_terms & insight_terms) * 4
        if score <= 0:
            continue
        ranked.append({"strategy_score": round(score, 4), **insight})
    return sorted(ranked, key=lambda item: (-float(item.get("strategy_score", 0)), str(item.get("insight_id") or "")))[: args.limit]


def group_pack_items(insights: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    pack = {
        "recommended_angles": [],
        "usable_insights": [],
        "asset_references": [],
        "evidence": [],
        "frameworks": [],
        "warnings": [],
    }
    for insight in insights:
        evidence = first_evidence(insight)
        item = {
            "insight_id": insight.get("insight_id"),
            "title": insight.get("title"),
            "insight_ptbr": insight.get("insight_ptbr"),
            "themes": insight.get("themes"),
            "level": insight.get("level"),
            "insight_type": insight.get("insight_type"),
            "confidence_score": insight.get("confidence_score"),
            "episode_video_id": insight.get("episode_video_id"),
            "episode_title": insight.get("episode_title"),
            "asset_id": insight.get("asset_id"),
            "strategy_score": insight.get("strategy_score"),
            "evidence_quote": evidence.get("quote_original"),
            "evidence_start_seconds": evidence.get("start_seconds"),
        }
        pack["usable_insights"].append(item)
        pack["evidence"].append(
            {
                "insight_id": item["insight_id"],
                "quote_original": evidence.get("quote_original"),
                "episode_video_id": evidence.get("episode_video_id") or insight.get("episode_video_id"),
                "asset_id": evidence.get("asset_id") or insight.get("asset_id"),
                "start_seconds": evidence.get("start_seconds"),
                "evidence_strength": evidence.get("evidence_strength"),
            }
        )
        if insight.get("asset_id") or insight.get("source_kind") == "asset":
            pack["asset_references"].append(item)
        if insight.get("insight_type") in {"framework", "template", "playbook_step", "checklist", "spreadsheet_model"}:
            pack["frameworks"].append(item)
        if insight.get("insight_type") in {"warning", "hypothesis"} or insight.get("review_status") == "needs_review":
            pack["warnings"].append(item)
        if any(normalize_text(theme) in {"hooks", "anuncios", "vsl", "copy", "ofertas"} for theme in as_list(insight.get("themes"))):
            pack["recommended_angles"].append(item)
    return pack


def build_pack(args: argparse.Namespace, insights: list[dict[str, Any]]) -> dict[str, Any]:
    selected = rank_insights(insights, args)
    grouped = group_pack_items(selected)
    open_questions = []
    if not selected:
        open_questions.append("A base ainda nao tem insights suficientes para esta tarefa. Rode extracao e consolide exports.")
    if not grouped["asset_references"]:
        open_questions.append("Nenhum material complementar apareceu entre os principais resultados; usar apenas transcricoes ou obter assets pendentes.")
    if len(selected) < min(args.limit, 10):
        open_questions.append("Poucos insights relevantes encontrados; expandir episodios ou baixar o limite de confianca pode ajudar.")

    return {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "task": args.task,
        "briefing": {
            "product": args.product,
            "avatar": args.avatar,
            "market": args.market,
            "asset_type": args.asset_type,
            "query": args.query,
            "constraints": args.constraints,
        },
        "result_count": len(selected),
        **grouped,
        "open_questions": open_questions,
    }


def render_markdown(pack: dict[str, Any]) -> str:
    briefing = pack["briefing"]
    lines = [
        f"# Strategy Pack - {pack['task']}",
        "",
        f"- Product: {briefing.get('product') or 'N/A'}",
        f"- Avatar: {briefing.get('avatar') or 'N/A'}",
        f"- Market: {briefing.get('market') or 'N/A'}",
        f"- Asset type: {briefing.get('asset_type') or 'N/A'}",
        f"- Results: {pack.get('result_count')}",
        "",
        "## Priority Insights",
        "",
    ]
    for item in pack.get("usable_insights", []):
        lines.extend(
            [
                f"### {item.get('insight_id')} - {item.get('title')}",
                "",
                f"- Themes: {', '.join(str(theme) for theme in as_list(item.get('themes')))}",
                f"- Level/type: {item.get('level')} / {item.get('insight_type')}",
                f"- Episode: {item.get('episode_video_id')} - {item.get('episode_title')}",
                f"- Confidence: {item.get('confidence_score')}",
                "",
                str(item.get("insight_ptbr") or ""),
                "",
                f"> {item.get('evidence_quote') or ''}",
                "",
            ]
        )
    if not pack.get("usable_insights"):
        lines.append("No usable insights found.")
        lines.append("")

    lines.extend(["## Open Questions", ""])
    for question in pack.get("open_questions", []):
        lines.append(f"- {question}")
    if not pack.get("open_questions"):
        lines.append("- None.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", default=Path("data/exports/insights_master.json"), type=Path)
    parser.add_argument("--task", required=True, help="Task type, e.g. vsl, anuncios, oferta, quiz")
    parser.add_argument("--product", help="Product or offer")
    parser.add_argument("--avatar", help="Target avatar")
    parser.add_argument("--market", help="Market or niche")
    parser.add_argument("--asset-type", help="Desired output asset type")
    parser.add_argument("--query", help="Extra retrieval query")
    parser.add_argument("--constraints", help="Free-form constraints")
    parser.add_argument("--min-confidence", default=0.0, type=float)
    parser.add_argument("--limit", default=20, type=int)
    parser.add_argument("--output-json", type=Path, help="Path to write strategy pack JSON")
    parser.add_argument("--output-md", type=Path, help="Path to write strategy pack markdown")
    args = parser.parse_args()

    insights = load_insights(args.master)
    pack = build_pack(args, insights)
    markdown = render_markdown(pack)
    if args.output_json:
        write_json(args.output_json, pack)
    if args.output_md:
        write_text(args.output_md, markdown)
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

