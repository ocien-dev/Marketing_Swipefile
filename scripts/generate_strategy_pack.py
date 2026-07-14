#!/usr/bin/env python
"""Generate a local evidence-backed strategy pack from consolidated insights."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from msf_common import (
    RETRIEVAL_AVAILABLE_STATE,
    UNFOUNDED_OUTPUT_BANNER,
    as_list,
    data_path,
    first_evidence,
    jaccard,
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
    "pool": data_path("exports", "insights_v2_master.json"),
}


TASK_THEMES = {
    "vsl": ["VSL", "copy", "hooks", "ofertas", "funil", "avatar", "prova social", "low ticket", "high ticket"],
    "anuncios": ["anuncios", "criativos", "hooks", "copy", "avatar", "prova social", "ofertas"],
    "ads": ["anuncios", "criativos", "hooks", "copy", "avatar", "prova social", "ofertas"],
    "offer": ["ofertas", "preco", "prova social", "avatar", "funil"],
    "oferta": ["ofertas", "preco", "prova social", "avatar", "funil"],
    "construcao-oferta": ["ofertas", "preco", "prova social", "avatar", "funil"],
    "quiz": ["quiz", "avatar", "ofertas", "copy", "funil"],
    "webinar": ["webinar", "copy", "ofertas", "prova social", "funil"],
}

TASK_KEYWORDS = {
    "vsl": ["vsl", "lead", "mecanismo", "promessa", "objecao", "prova", "cta", "low ticket"],
    "anuncios": ["anuncio", "hook", "criativo", "angulo", "script", "teste", "trafego"],
    "ads": ["anuncio", "hook", "criativo", "angulo", "script", "teste", "trafego"],
    "offer": ["oferta", "bonus", "garantia", "preco", "stack", "urgencia"],
    "oferta": ["oferta", "bonus", "garantia", "preco", "stack", "urgencia"],
    "construcao-oferta": ["oferta", "bonus", "garantia", "preco", "stack", "urgencia"],
    "quiz": ["quiz", "diagnostico", "pergunta", "resultado", "ponte"],
    "webinar": ["webinar", "aula", "pitch", "apresentacao", "evento"],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_insights(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    return [item for item in payload.get("insights", []) if isinstance(item, dict)]


def resolve_master_path(args: argparse.Namespace) -> Path:
    if args.master:
        return args.master
    return DEFAULT_MASTERS[args.source]


def theme_score(insight: dict[str, Any], desired_themes: list[str]) -> float:
    themes = [normalize_text(theme) for theme in as_list(insight.get("themes"))]
    desired = [normalize_text(theme) for theme in desired_themes]
    return sum(1 for theme in themes if theme in desired) * 8


def keyword_score(insight: dict[str, Any], keywords: list[str], briefing_terms: set[str]) -> float:
    source_text = " ".join(
        [
            str(insight.get("title") or ""),
            str(insight.get("insight_ptbr") or ""),
            " ".join(str(item) for item in as_list(insight.get("themes"))),
            " ".join(str(item) for item in as_list(insight.get("applicability"))),
        ]
    )
    text_terms = tokens(source_text)
    source_norm = normalize_text(source_text)
    score = sum(1 for keyword in keywords if normalize_text(keyword) in source_norm) * 5
    score += len(text_terms & briefing_terms) * 3
    return score


def confidence_score(insight: dict[str, Any]) -> float:
    confidence = insight.get("confidence_score")
    return float(confidence) if isinstance(confidence, (int, float)) else 0.0


def editorial_score(insight: dict[str, Any]) -> float:
    score = insight.get("editorial_score")
    return float(score) if isinstance(score, (int, float)) else 0.0


def similarity_text(insight: dict[str, Any]) -> str:
    parts = [
        insight.get("canonical_title"),
        insight.get("title"),
        insight.get("specific_takeaway"),
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
    return " ".join(str(part) for part in parts if part)


def thesis_key(insight: dict[str, Any]) -> str:
    title = normalize_text(insight.get("canonical_title") or insight.get("title") or "")
    marker_index = title.find(" em ")
    if marker_index >= 24:
        title = title[:marker_index]
    return title or normalize_text(insight.get("specific_takeaway") or insight.get("insight_id"))


def build_ranked_candidates(insights: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    task_key = normalize_text(args.task or "")
    desired_themes = TASK_THEMES.get(task_key, [])
    keywords = TASK_KEYWORDS.get(task_key, [])
    briefing_terms = tokens(" ".join(str(value or "") for value in [args.product, args.avatar, args.market, args.asset_type, args.query]))
    process_tags = getattr(args, "process_tags", []) or []
    process_tag_mode = getattr(args, "process_tag_mode", "any")
    ranked = []
    for insight in insights:
        if not matches_process_tags(insight, process_tags, process_tag_mode):
            continue
        confidence = confidence_score(insight)
        if confidence < args.min_confidence:
            continue
        if editorial_score(insight) < getattr(args, "min_editorial_score", 0.0):
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
        ranked.append(
            {
                "base_strategy_score": round(score, 4),
                "similarity_tokens": sorted(tokens(similarity_text(insight))),
                "thesis_key": thesis_key(insight),
                **insight,
            }
        )
    return sorted(ranked, key=lambda item: (-float(item.get("base_strategy_score", 0)), str(item.get("insight_id") or "")))


def select_diverse_top_n(candidates: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    if not candidates or args.limit <= 0:
        return []

    weight = max(0.0, min(1.0, float(args.diversity_weight)))
    max_relevance = max(float(item.get("base_strategy_score") or 0.0) for item in candidates) or 1.0
    selected: list[dict[str, Any]] = []
    remaining = list(candidates)
    episode_counts: Counter[str] = Counter()
    thesis_counts: Counter[str] = Counter()
    thesis_cap_scope = min(10, args.limit)

    while remaining and len(selected) < args.limit:
        best_index: int | None = None
        best_key: tuple[float, float, float, str] | None = None
        best_similarity = 0.0

        for index, candidate in enumerate(remaining):
            episode_id = str(candidate.get("episode_video_id") or "unknown")
            if args.episode_cap > 0 and episode_counts[episode_id] >= args.episode_cap:
                continue
            candidate_thesis_key = str(candidate.get("thesis_key") or "")
            if (
                args.thesis_cap > 0
                and len(selected) < thesis_cap_scope
                and candidate_thesis_key
                and thesis_counts[candidate_thesis_key] >= args.thesis_cap
            ):
                continue

            candidate_tokens = candidate.get("similarity_tokens") or []
            max_similarity = 0.0
            if selected:
                max_similarity = max(
                    jaccard(candidate_tokens, item.get("similarity_tokens") or [])
                    for item in selected
                )
            normalized_relevance = float(candidate.get("base_strategy_score") or 0.0) / max_relevance
            selection_score = ((1.0 - weight) * normalized_relevance) - (weight * max_similarity)
            key = (
                selection_score,
                normalized_relevance,
                -max_similarity,
                str(candidate.get("insight_id") or ""),
            )
            if best_key is None or key > best_key:
                best_index = index
                best_key = key
                best_similarity = max_similarity

        if best_index is None:
            break

        chosen = remaining.pop(best_index)
        episode_id = str(chosen.get("episode_video_id") or "unknown")
        episode_counts[episode_id] += 1
        if chosen.get("thesis_key"):
            thesis_counts[str(chosen["thesis_key"])] += 1
        chosen["strategy_score"] = chosen.get("base_strategy_score")
        chosen["selection_score"] = round(best_key[0], 6) if best_key else None
        chosen["similarity_to_selected"] = round(best_similarity, 6)
        selected.append(chosen)

    for item in selected:
        item.pop("similarity_tokens", None)
    return selected


def rank_insights(insights: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    return select_diverse_top_n(build_ranked_candidates(insights, args), args)


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
            "editorial_score": insight.get("editorial_score"),
            "episode_video_id": insight.get("episode_video_id"),
            "episode_title": insight.get("episode_title"),
            "asset_id": insight.get("asset_id"),
            "strategy_score": insight.get("strategy_score"),
            "base_strategy_score": insight.get("base_strategy_score"),
            "selection_score": insight.get("selection_score"),
            "similarity_to_selected": insight.get("similarity_to_selected"),
            "cluster_id": insight.get("cluster_id"),
            "thesis_key": insight.get("thesis_key"),
            "process_tags": insight.get("process_tags"),
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
    process_tags = getattr(args, "process_tags", []) or []
    process_tag_mode = getattr(args, "process_tag_mode", "any")
    open_questions = []
    if not selected:
        open_questions.append("A base ainda nao tem insights suficientes para esta tarefa. Rode extracao e consolide exports.")
    if not grouped["asset_references"]:
        open_questions.append("Nenhum material complementar apareceu entre os principais resultados; usar apenas transcricoes ou obter assets pendentes.")
    if len(selected) < min(args.limit, 10):
        open_questions.append("Poucos insights relevantes encontrados; expandir episodios ou baixar o limite de confianca pode ajudar.")
    if len(selected) < args.limit:
        open_questions.append("A diversidade/cap por episodio reduziu o top-N; revisar se o limite ou o cap devem ser ajustados.")
    if process_tags and not selected:
        open_questions.append("Nenhum insight curado encontrado para os process_tags pedidos; revisar tags ou aguardar novo lote curado.")
    if getattr(args, "retrieval_state", RETRIEVAL_AVAILABLE_STATE) != RETRIEVAL_AVAILABLE_STATE:
        open_questions.insert(0, "Fonte de retrieval indisponivel; resposta nao fundamentada pela base.")

    return {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "banner": UNFOUNDED_OUTPUT_BANNER
        if getattr(args, "retrieval_state", RETRIEVAL_AVAILABLE_STATE) != RETRIEVAL_AVAILABLE_STATE
        else None,
        "retrieval_state": getattr(args, "retrieval_state", "available"),
        "task": args.task,
        "source": args.source,
        "source_path": str(resolve_master_path(args)),
        "min_editorial_score": args.min_editorial_score,
        "process_tag_filter": {
            "process_tags": process_tags,
            "mode": process_tag_mode,
        },
        "diversity": {
            "method": "mmr_jaccard",
            "diversity_weight": args.diversity_weight,
            "episode_cap": args.episode_cap,
            "thesis_cap": args.thesis_cap,
            "thesis_cap_scope": "top_10",
            "episode_cap_scope": "selected_top_n",
        },
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
    lines = []
    if pack.get("retrieval_state") != RETRIEVAL_AVAILABLE_STATE:
        lines.extend([UNFOUNDED_OUTPUT_BANNER, ""])
    lines.extend(
        [
        f"# Strategy Pack - {pack['task']}",
        "",
        f"- Product: {briefing.get('product') or 'N/A'}",
        f"- Avatar: {briefing.get('avatar') or 'N/A'}",
        f"- Market: {briefing.get('market') or 'N/A'}",
        f"- Asset type: {briefing.get('asset_type') or 'N/A'}",
        f"- Source: {pack.get('source')} ({pack.get('source_path')})",
        f"- Min editorial score: {pack.get('min_editorial_score')}",
        f"- Process tags: {', '.join(pack.get('process_tag_filter', {}).get('process_tags') or []) or 'N/A'}",
        f"- Retrieval state: {pack.get('retrieval_state')}",
        f"- Results: {pack.get('result_count')}",
        "",
        "## Priority Insights",
        "",
        ]
    )
    for item in pack.get("usable_insights", []):
        lines.extend(
            [
                f"### {item.get('insight_id')} - {item.get('title')}",
                "",
                f"- Themes: {', '.join(str(theme) for theme in as_list(item.get('themes')))}",
                f"- Level/type: {item.get('level')} / {item.get('insight_type')}",
                f"- Episode: {item.get('episode_video_id')} - {item.get('episode_title')}",
                f"- Confidence: {item.get('confidence_score')}",
                f"- Editorial score: {item.get('editorial_score')}",
                f"- Strategy score: {item.get('strategy_score')} | Selection score: {item.get('selection_score')} | Similarity: {item.get('similarity_to_selected')}",
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
    parser.add_argument("--master", type=Path, help="Override the source master path.")
    parser.add_argument("--source", choices=sorted(DEFAULT_MASTERS), default="curated", help="Source layer to use when --master is omitted.")
    parser.add_argument("--task", required=True, help="Task type, e.g. vsl, anuncios, oferta, quiz")
    parser.add_argument("--product", help="Product or offer")
    parser.add_argument("--avatar", help="Target avatar")
    parser.add_argument("--market", help="Market or niche")
    parser.add_argument("--asset-type", help="Desired output asset type")
    parser.add_argument("--query", help="Extra retrieval query")
    parser.add_argument("--constraints", help="Free-form constraints")
    parser.add_argument("--process-tags", nargs="+", help="Filter by process-* tags. Accepts repeated values or comma-separated lists.")
    parser.add_argument("--process-tag-mode", choices=["any", "all"], default="any", help="Require any or all requested process tags.")
    parser.add_argument("--min-confidence", default=0.0, type=float)
    parser.add_argument("--min-editorial-score", default=0.0, type=float)
    parser.add_argument("--limit", default=20, type=int)
    parser.add_argument("--diversity-weight", default=0.3, type=float, help="MMR Jaccard diversity penalty, 0.0 to 1.0.")
    parser.add_argument("--episode-cap", default=3, type=int, help="Maximum selected insights per episode in the top-N; use 0 to disable.")
    parser.add_argument("--thesis-cap", default=1, type=int, help="Maximum selected insights with the same title-derived thesis key in the top 10; use 0 to disable.")
    parser.add_argument("--output-json", type=Path, help="Path to write strategy pack JSON")
    parser.add_argument("--output-md", type=Path, help="Path to write strategy pack markdown")
    args = parser.parse_args()
    args.process_tags = normalize_process_tags(args.process_tags)

    master_path = resolve_master_path(args)
    args.retrieval_state = retrieval_source_state(args.source, master_path)
    insights = [] if args.retrieval_state != RETRIEVAL_AVAILABLE_STATE else load_insights(master_path)
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
