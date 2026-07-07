#!/usr/bin/env python
"""Extract evidence-backed candidate insights from YouTube descriptions."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from msf_common import load_json, normalize_text, slugify, write_json


STOP_MARKERS = [
    "links do episodio",
    "links do episódio",
    "siga o perfil",
    "inscreva-se",
    "assista tambem",
    "assista também",
    "guia do episodio",
    "guia do episódio",
    "#podcast",
]

THEME_KEYWORDS = {
    "VSL": ["vsl", "mini-vsl", "video de vendas", "video vendas"],
    "anuncios": ["anuncio", "trafego", "criativo", "campanha", "meta", "tiktok"],
    "criativos": ["criativo", "imagem", "video", "hook"],
    "hooks": ["hook", "gancho", "abertura"],
    "ofertas": ["oferta", "low ticket", "produto", "preco", "bonus", "garantia"],
    "funil": ["funil", "quiz", "checkout", "upsell", "aquisicao"],
    "copy": ["copy", "copywriter", "promessa", "mecanismo", "persuasao"],
    "gestao": ["time", "operacao", "processo", "gestao", "rotina"],
    "produto": ["produto", "entregavel", "entrega"],
    "avatar": ["pessoa", "cliente", "publico", "avatar"],
    "prova social": ["case", "resultado", "faturamento", "milhoes", "100k", "7 digitos", "8 digitos"],
    "low ticket": ["low ticket", "mini-vsl", "quiz"],
    "high ticket": ["high ticket", "premium"],
    "perpetuo": ["perpetuo", "todos os dias"],
    "lancamento": ["lancamento"],
}

APPLICATIONS_BY_THEME = {
    "VSL": ["copywriter de VSLs", "copy strategist"],
    "anuncios": ["copywriter de anuncios"],
    "criativos": ["copywriter de anuncios"],
    "hooks": ["copywriter de anuncios", "copywriter de VSLs"],
    "ofertas": ["CMO", "copy strategist"],
    "funil": ["CMO", "copy strategist"],
    "copy": ["copy strategist"],
    "gestao": ["COO"],
    "produto": ["head de produto"],
    "avatar": ["copy strategist"],
}


def useful_description_lines(description: str) -> list[str]:
    lines = [line.strip() for line in description.splitlines()]
    selected: list[str] = []
    stopped = False
    for line in lines:
        if not line:
            continue
        normalized = normalize_text(line)
        if any(marker in normalized for marker in STOP_MARKERS):
            stopped = True
        if stopped:
            continue
        if line.startswith("-"):
            text = line.lstrip("-").strip()
            if text and not text.startswith("http"):
                selected.append(text)
    return selected


def infer_themes(text: str) -> list[str]:
    normalized = normalize_text(text)
    themes = []
    for theme, keywords in THEME_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            themes.append(theme)
    return themes or ["estrategias"]


def infer_level(text: str) -> str:
    normalized = normalize_text(text)
    if any(keyword in normalized for keyword in ["passo", "como", "metrica", "otimizacao", "ajuste"]):
        return "operational"
    if any(keyword in normalized for keyword in ["funil", "vsl", "anuncio", "criativo", "quiz", "oferta"]):
        return "tactical"
    return "strategic"


def infer_applicability(themes: list[str]) -> list[str]:
    values = []
    for theme in themes:
        values.extend(APPLICATIONS_BY_THEME.get(theme, []))
    if not values:
        values.append("CMO")
    deduped = []
    seen = set()
    for value in values:
        key = normalize_text(value)
        if key not in seen:
            seen.add(key)
            deduped.append(value)
    return deduped


def clean_title(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:120].rstrip(" .")


def build_insight(video_id: str, line: str, index: int) -> dict[str, Any]:
    themes = infer_themes(line)
    title = clean_title(line)
    return {
        "insight_id": f"{video_id}-desc-insight-{index + 1:04d}",
        "source_kind": "description",
        "title": title,
        "insight_original": None,
        "insight_ptbr": f"A descricao do episodio sinaliza este ponto de valor: {line}",
        "summary_ptbr": title,
        "level": infer_level(line),
        "insight_type": "hypothesis",
        "themes": themes,
        "subthemes": [],
        "applicability": infer_applicability(themes),
        "niches": ["infoprodutos"],
        "funnel_stages": [],
        "confidence_score": 0.62,
        "review_status": "needs_review",
        "source_agent": "description_candidate_extractor",
        "dedupe_key": f"description-{video_id}-{slugify(line, max_length=80)}",
        "evidence": [
            {
                "evidence_id": f"{video_id}-desc-evidence-{index + 1:04d}",
                "segment_id": None,
                "episode_video_id": video_id,
                "asset_id": None,
                "start_seconds": None,
                "end_seconds": None,
                "page_number": None,
                "sheet_name": None,
                "cell_range": None,
                "slide_number": None,
                "quote_original": line,
                "quote_ptbr": None,
                "evidence_strength": "medium",
            }
        ],
        "relations": [],
    }


def extract_from_metadata(metadata_path: Path, output_path: Path) -> dict[str, Any]:
    metadata = load_json(metadata_path)
    video_id = metadata["youtube_video_id"]
    description = metadata.get("description") or ""
    lines = useful_description_lines(description)
    payload = {
        "schema_version": "1.0",
        "episode_video_id": video_id,
        "asset_id": None,
        "insights": [build_insight(video_id, line, index) for index, line in enumerate(lines)],
    }
    write_json(output_path, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, help="Single metadata.json")
    parser.add_argument("--all", action="store_true", help="Process all metadata under data/raw/youtube")
    parser.add_argument("--raw-youtube-root", default=Path("data/raw/youtube"), type=Path)
    parser.add_argument("--processed-root", default=Path("data/processed"), type=Path)
    args = parser.parse_args()

    metadata_paths: list[Path]
    if args.all:
        metadata_paths = sorted(args.raw_youtube_root.glob("*/metadata.json"))
    elif args.metadata:
        metadata_paths = [args.metadata]
    else:
        parser.error("Provide --metadata or --all")

    count = 0
    for metadata_path in metadata_paths:
        metadata = load_json(metadata_path)
        video_id = metadata["youtube_video_id"]
        output = args.processed_root / video_id / "description_insights.json"
        payload = extract_from_metadata(metadata_path, output)
        print(f"Wrote {len(payload['insights'])} description insight candidate(s) to {output}")
        count += len(payload["insights"])

    print(f"Wrote {count} description insight candidate(s) total.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

