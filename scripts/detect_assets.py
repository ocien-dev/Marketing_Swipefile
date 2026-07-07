#!/usr/bin/env python
"""Detect complementary materials mentioned in an episode."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


ASSET_PATTERNS = [
    {
        "asset_type_guess": "pdf",
        "keywords": ["pdf", "ebook", "guia"],
        "name": "PDF mencionado no episodio",
        "expected_value": "Possivel framework, template, checklist ou copy complementar.",
    },
    {
        "asset_type_guess": "spreadsheet",
        "keywords": ["planilha", "spreadsheet", "sheet", "xlsx"],
        "name": "Planilha mencionada no episodio",
        "expected_value": "Possivel modelo, calculadora, tabela de oferta, funil ou criativos.",
    },
    {
        "asset_type_guess": "doc",
        "keywords": ["doc", "documento", "google docs"],
        "name": "Documento mencionado no episodio",
        "expected_value": "Possivel estrutura, roteiro, checklist ou material de apoio.",
    },
    {
        "asset_type_guess": "slides",
        "keywords": ["slides", "apresentacao", "deck"],
        "name": "Slides mencionados no episodio",
        "expected_value": "Possivel aula, pitch, framework ou estrutura visual.",
    },
    {
        "asset_type_guess": "image",
        "keywords": ["banner", "imagem", "image", "mockup", "png", "jpg", "jpeg"],
        "name": "Imagem ou mockup mencionado no episodio",
        "expected_value": "Possivel referencia visual, banner, mockup ou criativo complementar.",
    },
]

ACTION_KEYWORDS = [
    "area de membros",
    "baixe",
    "baixar",
    "bonus",
    "comenta",
    "comente",
    "direct",
    "dm",
    "download",
    "link da descricao",
    "link na descricao",
    "link",
    "material",
    "pegar",
    "receber",
]

ASSET_CONTEXT_KEYWORDS = [
    "arquivo",
    "checklist",
    "framework",
    "modelo",
    "one pager",
    "planilha",
    "template",
]

PUBLIC_FILE_HINTS = {
    "pdf": [".pdf", "drive.google.com", "dropbox.com", "notion.site"],
    "doc": ["docs.google.com/document", ".doc", ".docx", "drive.google.com", "notion.site"],
    "spreadsheet": ["docs.google.com/spreadsheets", ".csv", ".xlsx", "airtable.com", "drive.google.com"],
    "slides": ["docs.google.com/presentation", ".ppt", ".pptx", "drive.google.com"],
    "image": [".png", ".jpg", ".jpeg", ".webp", "drive.google.com", "dropbox.com"],
}

NEGATIVE_ASSET_PHRASES = [
    "nao tem pdf",
    "nao achei",
    "nao encontrei",
    "talvez tenha",
    "sem pdf",
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(payload, file, ensure_ascii=True, indent=2)
        file.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    return ascii_text.lower()


def contains_term(normalized_text: str, term: str) -> bool:
    normalized_term = normalize_text(term)
    pattern = rf"(?<![a-z0-9_]){re.escape(normalized_term)}(?![a-z0-9_])"
    return re.search(pattern, normalized_text) is not None


def extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s)>\"]+", text)


def has_public_file_link(text: str, asset_type_guess: str) -> bool:
    hints = PUBLIC_FILE_HINTS.get(asset_type_guess, [])
    for url in extract_urls(text):
        lowered_url = normalize_text(url)
        if any(hint in lowered_url for hint in hints):
            return True
    return False


def is_actionable_asset_mention(mention: dict[str, Any], pattern: dict[str, Any]) -> bool:
    text = mention["text"]
    lowered = normalize_text(text)
    source = mention.get("source")
    asset_type_guess = pattern["asset_type_guess"]

    if any(phrase in lowered for phrase in NEGATIVE_ASSET_PHRASES):
        return False

    if source == "description":
        return has_public_file_link(text, asset_type_guess)

    has_action = any(contains_term(lowered, keyword) for keyword in ACTION_KEYWORDS)
    has_asset_context = any(contains_term(lowered, keyword) for keyword in ASSET_CONTEXT_KEYWORDS)
    has_public_file = has_public_file_link(text, asset_type_guess)

    if has_public_file:
        return True
    if has_action and has_asset_context:
        return True
    if has_action and asset_type_guess in {"pdf", "spreadsheet", "slides"}:
        return True

    return False


def detect_keyword_instruction(text: str, asset_type_guess: str) -> tuple[str, str]:
    lowered = normalize_text(text)
    has_description_link = "link da descricao" in lowered or "link na descricao" in lowered or "descricao" in lowered
    if has_public_file_link(text, asset_type_guess):
        return "download_public_file", "Baixar o material pelo link publico identificado."
    if asset_type_guess == "spreadsheet" and has_description_link:
        return "open_description_link", "Buscar a planilha no link da descricao do video."
    keyword_match = re.search(r"\bcoment(?:a|e)\s+([a-zA-Z0-9_-]{2,30})", text, re.IGNORECASE)
    if keyword_match:
        keyword = keyword_match.group(1).upper()
        return "comment_keyword", f"Comentar a palavra {keyword} conforme instrucao do episodio."
    if contains_term(lowered, "direct") or contains_term(lowered, "dm"):
        return "send_direct_message", "Enviar direct conforme instrucao mencionada no episodio."
    if has_description_link:
        return "open_description_link", "Buscar o material no link da descricao do video."
    if "area de membros" in lowered or "membros" in lowered:
        return "access_member_area", "Buscar o material na area de membros mencionada no episodio."
    return "manual_search", "Localizar o material manualmente com base na mencao do episodio."


def collect_mentions(metadata: dict[str, Any], segments_payload: dict[str, Any]) -> list[dict[str, Any]]:
    mentions: list[dict[str, Any]] = []
    for segment in segments_payload.get("segments", []):
        mentions.append(
            {
                "source": segment.get("source_kind", "transcript"),
                "text": segment.get("text_original", ""),
                "start_seconds": segment.get("start_seconds"),
                "end_seconds": segment.get("end_seconds"),
            }
        )
    description = metadata.get("description")
    if description:
        lines = [line.strip() for line in description.splitlines()]
        nonempty_lines = [line for line in lines if line]
        for index, line in enumerate(nonempty_lines):
            context = line
            if extract_urls(line) and index > 0 and len(nonempty_lines[index - 1]) <= 140:
                context = f"{nonempty_lines[index - 1]}\n{line}"
            mentions.append(
                {
                    "source": "description",
                    "text": context,
                    "start_seconds": None,
                    "end_seconds": None,
                }
            )
    return mentions


def detect_assets(metadata: dict[str, Any], segments_payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    video_id = metadata["youtube_video_id"]
    detected: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    seen: set[str] = set()

    for mention in collect_mentions(metadata, segments_payload):
        text = mention["text"]
        lowered = normalize_text(text)
        for pattern in ASSET_PATTERNS:
            if not any(contains_term(lowered, keyword) for keyword in pattern["keywords"]):
                continue
            if not is_actionable_asset_mention(mention, pattern):
                continue

            key = pattern["asset_type_guess"]
            if key in seen:
                continue
            seen.add(key)

            index = len(detected) + 1
            referenced_asset_id = f"{video_id}-refasset-{index:04d}"
            task_type, base_instruction = detect_keyword_instruction(text, pattern["asset_type_guess"])
            asset_dir = f"data/input/assets/{video_id}/"
            instruction = f"{base_instruction} Inserir o arquivo obtido em {asset_dir}."

            asset = {
                "referenced_asset_id": referenced_asset_id,
                "name": pattern["name"],
                "asset_type_guess": pattern["asset_type_guess"],
                "mention_source": mention["source"],
                "mention_start_seconds": mention["start_seconds"],
                "mention_end_seconds": mention["end_seconds"],
                "mention_quote_original": text,
                "mention_quote_ptbr": None,
                "acquisition_instruction": instruction,
                "expected_value": pattern["expected_value"],
                "status": "needs_user_action",
                "priority": "high",
            }
            detected.append(asset)

            tasks.append(
                {
                    "task_id": f"{video_id}-task-{len(tasks) + 1:04d}",
                    "referenced_asset_id": referenced_asset_id,
                    "task_type": task_type,
                    "instruction": instruction,
                    "status": "pending",
                    "priority": "high",
                    "user_notes": None,
                    "result_asset_id": None,
                }
            )

    return detected, tasks


def render_manual_actions(video_id: str, assets: list[dict[str, Any]], tasks: list[dict[str, Any]]) -> str:
    lines = [
        f"# Manual Actions - {video_id}",
        "",
    ]
    if not tasks:
        lines.append("No complementary materials requiring manual action were detected.")
        lines.append("")
        return "\n".join(lines)

    task_by_asset = {task["referenced_asset_id"]: task for task in tasks}
    for asset in assets:
        task = task_by_asset.get(asset["referenced_asset_id"])
        start = asset["mention_start_seconds"]
        end = asset["mention_end_seconds"]
        timestamp = "N/A" if start is None and end is None else f"{start} to {end}"
        lines.extend(
            [
                f"## {asset['referenced_asset_id']} - {asset['name']}",
                "",
                f"- Type guess: {asset['asset_type_guess']}",
                f"- Priority: {asset['priority']}",
                f"- Mention source: {asset['mention_source']}",
                f"- Timestamp: {timestamp}",
                f"- Evidence: {asset['mention_quote_original']}",
                f"- Instruction: {task['instruction'] if task else asset['acquisition_instruction']}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True, type=Path, help="Path to metadata.json")
    parser.add_argument("--segments", required=True, type=Path, help="Path to content_segments.json")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory for referenced_assets and tasks")
    args = parser.parse_args()

    metadata = load_json(args.metadata)
    segments = load_json(args.segments)
    video_id = metadata["youtube_video_id"]
    assets, tasks = detect_assets(metadata, segments)

    write_json(
        args.output_dir / "referenced_assets.json",
        {
            "schema_version": "1.0",
            "episode_video_id": video_id,
            "referenced_assets": assets,
        },
    )
    write_json(
        args.output_dir / "acquisition_tasks.json",
        {
            "schema_version": "1.0",
            "episode_video_id": video_id,
            "tasks": tasks,
        },
    )
    write_text(args.output_dir / "manual_actions.md", render_manual_actions(video_id, assets, tasks))

    print(f"Detected {len(assets)} referenced assets and wrote {len(tasks)} acquisition tasks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
