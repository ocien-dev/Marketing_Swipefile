#!/usr/bin/env python3
"""Build the durable priority queue used to start gold episodes instantly."""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.gold_extraction_common import load_json, preferred_transcript_path, sha256_semantic_json, write_json


CATEGORY_ORDER = [
    "vsl",
    "copy",
    "ads",
    "funnel",
    "quiz",
    "scale",
    "evergreen",
    "launch",
    "experts",
    "affiliate",
    "nutra",
    "ai_automation",
    "direct_response",
    "crm_retention",
    "international",
    "content_organic",
    "infoproducts",
    "business_operations",
    "digital_business",
    "growth_cases",
    "other",
]
CATEGORY_LABELS = {
    "vsl": "VSL",
    "copy": "Copy",
    "ads": "Anuncios",
    "funnel": "Funil",
    "quiz": "Quiz",
    "scale": "Escala",
    "evergreen": "Perpetuo",
    "launch": "Lancamento",
    "experts": "Experts",
    "affiliate": "Afiliado",
    "nutra": "Nutra",
    "ai_automation": "IA e Automacao",
    "direct_response": "Marketing Direto",
    "crm_retention": "CRM e Retencao",
    "international": "Mercado Internacional",
    "content_organic": "Conteudo e Organico",
    "infoproducts": "Infoprodutos",
    "business_operations": "Negocios e Operacoes",
    "digital_business": "Empreendedorismo Digital",
    "growth_cases": "Cases de Crescimento",
    "other": "Outros",
}
CATEGORY_TERMS = {
    "vsl": ["vsl", "vsls", "video", "videos", "video de vendas", "videos de vendas", "carta de vendas", "video sales letter"],
    "copy": ["copy", "copys", "copies", "copywriter", "copywriters", "copywriting", "oferta", "ofertas", "narrativa", "narrativas", "swipe file"],
    "ads": ["anuncio", "anuncios", "ads", "criativo", "criativos", "trafego", "trafego pago"],
    "funnel": ["funil", "funis", "tracking", "trackear", "trackeou", "trackeamento", "rastreamento", "webinario", "webinarios", "webinar", "webinars"],
    "quiz": ["quiz", "quizzes"],
    "scale": ["escala", "escalar", "escalando", "escalam", "escalou", "escalei", "escalado", "escalados", "escalavel", "escalabilidade"],
    "evergreen": ["perpetuo", "perpetua", "perpetuos", "perpetuas", "evergreen", "mesmo produto"],
    "launch": ["lancamento", "lancamentos", "lancar", "launch", "abertura de carrinho"],
    "experts": ["expert", "experts", "especialista", "especialistas", "infoprodutor", "infoprodutores", "autoridade", "mentor"],
    "affiliate": ["afiliado", "afiliados", "afiliada", "afiliadas", "afiliacao", "affiliate", "affiliates"],
    "nutra": ["nutra", "nutraceutico", "nutraceuticos", "suplemento", "suplementos"],
    "ai_automation": ["ia", "inteligencia artificial", "automacao", "automacoes"],
    "direct_response": ["marketing direto", "direct response"],
    "crm_retention": ["e-mail marketing", "email marketing", "whatsapp", "recuperacao de vendas", "recuperou", "ascensao de clientes"],
    "international": ["mercado americano", "mercado internacional", "nos eua", "no exterior", "em dolar"],
    "content_organic": ["conteudo", "conteudos", "pinterest", "youtube"],
    "infoproducts": ["infoproduto", "infoprodutos", "produto digital", "produtos digitais"],
    "business_operations": ["negocio", "negocios", "operacao", "operacoes", "gestao", "time", "times", "fundador", "fundou", "marca", "marcas", "dropshipping", "queima diaria"],
    "digital_business": ["marketing digital", "no digital", "na internet", "online"],
    "growth_cases": ["fatura", "faturou", "faturados", "faturadas", "milhoes", "milionario", "milionarios", "milionaria", "milionarias", "multimilionario", "multimilionarios", "multimilionaria", "multimilionarias", "digito", "digitos", "vendas"],
}

QUEUE_STATE_SCHEMA_VERSION = "1.0.0"
QUEUE_STATE_KIND = "gold_episode_priority_state"
TERMINAL_QUEUE_STATES = {"finalized_pending_audit", "complete_passed"}
RUNTIME_READY = "runtime_ready"
CATALOG_UNVERIFIED = "cataloged_unverified"


def _normalize(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(char for char in text if not unicodedata.combining(char)).lower()


def _repair_known_mojibake(value: Any) -> Any:
    """Repair repeated UTF-8-as-Windows-1252 catalog corruption only."""
    if not isinstance(value, str) or not any(marker in value for marker in ("Ã", "Â", "â", "ƒ")):
        return value
    repaired = value
    for _ in range(3):
        try:
            candidate = repaired.encode("cp1252").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
        if candidate == repaired:
            break
        repaired = candidate
    return repaired


def _term_pattern(term: str) -> re.Pattern[str]:
    escaped = re.escape(_normalize(term)).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")


TERM_PATTERNS = {
    category: [(term, _term_pattern(term)) for term in terms]
    for category, terms in CATEGORY_TERMS.items()
}


def _classification_title(title: str | None) -> str:
    normalized = _normalize(title)
    # The channel suffix is metadata, not the episode topic.
    normalized = re.sub(r"\s*[-|]\s*segredos da escala\s*#?\s*\d+\s*$", "", normalized)
    return normalized.strip()


def classify_episode(title: str | None, segments: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Classify by title aliases only, resolving multi-theme titles by owner priority."""
    del segments
    normalized_title = _classification_title(title)
    matches = {
        category: [term for term, pattern in TERM_PATTERNS[category] if pattern.search(normalized_title)]
        for category in CATEGORY_ORDER[:-1]
    }
    best = next((category for category in CATEGORY_ORDER[:-1] if matches[category]), "other")
    return {
        "category": best,
        "category_label": CATEGORY_LABELS[best],
        "classification_evidence": {
            "classification_title": normalized_title,
            "matched_terms": matches.get(best, []),
            "all_title_matches": {category: terms for category, terms in matches.items() if terms},
        },
    }


def _episode_entry(data_root: Path, video_id: str) -> dict[str, Any] | None:
    processed = data_root / "processed" / video_id
    if (processed / "gold_extraction").exists():
        return None
    metadata_path = data_root / "raw" / "youtube" / video_id / "metadata.json"
    transcript_path = preferred_transcript_path(data_root, video_id)
    content_path = processed / "content_segments.json"
    if not all(path.exists() for path in (metadata_path, transcript_path, content_path)):
        return None
    try:
        metadata = load_json(metadata_path)
        transcript = load_json(transcript_path)
        content = load_json(content_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    clean_segments = content.get("segments", []) if isinstance(content, dict) else []
    raw_segments = transcript.get("segments", []) if isinstance(transcript, dict) else []
    transcript_status = metadata.get("transcript_status") or transcript.get("transcript_status")
    if transcript_status not in {None, "available"} or not clean_segments or not raw_segments:
        return None
    classification = classify_episode(metadata.get("title"), clean_segments)
    duration = metadata.get("duration_seconds") or metadata.get("duration")
    if not isinstance(duration, (int, float)) and clean_segments:
        last = clean_segments[-1]
        duration = float(last.get("start_seconds", 0)) + float(last.get("duration_seconds", 0))
    return {
        "video_id": video_id,
        "title": metadata.get("title") or video_id,
        "duration_seconds": round(float(duration or 0), 3),
        "clean_segments": len(clean_segments),
        # This status is proven only by the data root supplied to this build.
        "source_status": RUNTIME_READY,
        **classification,
    }


def _catalog_rows(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [
            {key: _repair_known_mojibake(value) for key, value in row.items()}
            for row in csv.DictReader(file)
        ]


def merge_catalog_entries(
    entries: list[dict[str, Any]],
    catalog: list[dict[str, Any]],
    *,
    excluded_video_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Merge ordering metadata without claiming availability outside this runtime."""
    by_id = {str(item.get("video_id") or ""): dict(item) for item in entries if item.get("video_id")}
    excluded = excluded_video_ids or set()
    for record in catalog:
        video_id = str(record.get("video_id") or "").strip()
        if not video_id or video_id in excluded:
            continue
        classification = classify_episode(str(record.get("title") or video_id))
        duration = record.get("duration_seconds")
        try:
            duration_value = round(float(duration or 0), 3)
        except (TypeError, ValueError):
            duration_value = 0.0
        previous = by_id.get(video_id)
        if previous is None:
            by_id[video_id] = {
                "video_id": video_id,
                "youtube_url": record.get("youtube_url") or f"https://www.youtube.com/watch?v={video_id}",
                "title": record.get("title") or video_id,
                "duration_seconds": duration_value,
                "clean_segments": 0,
                "source_status": CATALOG_UNVERIFIED,
                "discovered_order": int(record.get("discovered_order") or 0),
                "published_time_text": record.get("published_time_text") or "",
                **classification,
            }
            continue
        previous.update({
            "youtube_url": record.get("youtube_url") or previous.get("youtube_url") or f"https://www.youtube.com/watch?v={video_id}",
            "title": record.get("title") or previous.get("title") or video_id,
            "duration_seconds": duration_value or previous.get("duration_seconds") or 0,
            # A prior queue snapshot is catalog metadata, not evidence that the
            # active data root still contains the source artifacts.
            "source_status": RUNTIME_READY if previous.get("source_status") == RUNTIME_READY else CATALOG_UNVERIFIED,
            "discovered_order": int(record.get("discovered_order") or 0),
            "published_time_text": record.get("published_time_text") or "",
            **classification,
        })
    merged = list(by_id.values())
    merged.sort(key=lambda item: (
        CATEGORY_ORDER.index(item["category"]),
        item["duration_seconds"] if item["duration_seconds"] > 0 else float("inf"),
        int(item.get("discovered_order") or 10**9),
        item["video_id"],
    ))
    for rank, entry in enumerate(merged, 1):
        entry["rank"] = rank
    return merged


def build_priority_queue(
    data_root: Path | None = None,
    *,
    catalog: list[dict[str, Any]] | None = None,
    base_entries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if data_root is None and base_entries is None:
        raise ValueError("data_root or base_entries is required")
    entries = [
        {key: _repair_known_mojibake(value) for key, value in item.items()}
        for item in (base_entries or [])
    ]
    completed_video_ids: set[str] = set()
    for entry in entries:
        # A base queue is historical ordering information. Availability is
        # always rechecked by the selector against the active data root.
        entry["source_status"] = CATALOG_UNVERIFIED
    if data_root is not None:
        entries = []
        processed_root = data_root / "processed"
        if not processed_root.is_dir():
            raise FileNotFoundError(f"processed data root does not exist: {processed_root}")
        for episode_dir in sorted(processed_root.iterdir()):
            if not episode_dir.is_dir():
                continue
            if (episode_dir / "gold_extraction").exists():
                completed_video_ids.add(episode_dir.name)
                continue
            entry = _episode_entry(data_root, episode_dir.name)
            if entry is not None:
                entries.append(entry)
    entries = merge_catalog_entries(entries, catalog or [], excluded_video_ids=completed_video_ids)
    active_categories = [
        category for category in CATEGORY_ORDER
        if any(entry["category"] == category for entry in entries)
    ]
    core = {
        "schema_version": "1.2.0",
        "kind": "gold_episode_priority_queue",
        "category_order": active_categories,
        "category_labels": {category: CATEGORY_LABELS[category] for category in active_categories},
        "total_episodes": len(entries),
        "runtime_ready_episodes": sum(1 for item in entries if item.get("source_status") == RUNTIME_READY),
        "catalog_unverified_episodes": sum(1 for item in entries if item.get("source_status") == CATALOG_UNVERIFIED),
        "entries": entries,
    }
    return {
        **core,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "semantic_sha256": sha256_semantic_json(core),
    }


def queue_state_path(queue_path: Path) -> Path:
    """Keep mutable progress beside the immutable priority catalog."""
    return queue_path.with_name(f"{queue_path.stem}-state.json")


def _state_core(
    queue: dict[str, Any],
    terminal_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    entries = queue.get("entries", [])
    by_id = {str(item.get("video_id")): item for item in entries if isinstance(item, dict) and item.get("video_id")}
    terminal_by_id = {
        str(item.get("video_id")): item
        for item in terminal_entries
        if isinstance(item, dict)
        and str(item.get("video_id") or "") in by_id
        and item.get("state") in TERMINAL_QUEUE_STATES
    }
    normalized_terminal = []
    for item in entries:
        video_id = str(item.get("video_id") or "")
        terminal = terminal_by_id.get(video_id)
        if terminal is None:
            continue
        normalized_terminal.append({
            "video_id": video_id,
            "queue_rank": item.get("rank"),
            "state": terminal["state"],
            "recorded_at": terminal.get("recorded_at"),
            "source": terminal.get("source", "runtime"),
        })
    terminal_ids = {item["video_id"] for item in normalized_terminal}
    pending = [item for item in entries if str(item.get("video_id") or "") not in terminal_ids]
    next_episode = dict(pending[0]) if pending else None
    return {
        "schema_version": QUEUE_STATE_SCHEMA_VERSION,
        "kind": QUEUE_STATE_KIND,
        "priority_queue_semantic_sha256": queue.get("semantic_sha256"),
        "total_episodes": len(entries),
        "terminal_count": len(normalized_terminal),
        "remaining_count": len(pending),
        "terminal_entries": normalized_terminal,
        "next_episode": next_episode,
    }


def build_queue_state(
    queue: dict[str, Any],
    *,
    previous_state: dict[str, Any] | None = None,
    terminal_updates: dict[str, str] | None = None,
    source: str = "runtime",
) -> dict[str, Any]:
    previous_terminal = previous_state.get("terminal_entries", []) if isinstance(previous_state, dict) else []
    updates = terminal_updates or {}
    now = datetime.now(timezone.utc).isoformat()
    terminal_entries = [dict(item) for item in previous_terminal if isinstance(item, dict)]
    by_id = {str(item.get("video_id") or ""): item for item in terminal_entries}
    for video_id, state in updates.items():
        if state not in TERMINAL_QUEUE_STATES:
            raise ValueError(f"unsupported terminal queue state: {state}")
        by_id[str(video_id)] = {
            "video_id": str(video_id),
            "state": state,
            "recorded_at": now,
            "source": source,
        }
    core = _state_core(queue, list(by_id.values()))
    return {
        **core,
        "updated_at": now,
        "semantic_sha256": sha256_semantic_json(core),
    }


def queue_state_errors(queue: dict[str, Any], state: dict[str, Any]) -> list[str]:
    if state.get("kind") != QUEUE_STATE_KIND:
        return ["priority queue state kind is invalid"]
    if state.get("priority_queue_semantic_sha256") != queue.get("semantic_sha256"):
        return ["priority queue state does not match the current priority catalog"]
    expected_core = _state_core(queue, state.get("terminal_entries", []))
    if state.get("semantic_sha256") != sha256_semantic_json(expected_core):
        return ["priority queue state semantic hash is invalid"]
    for field in ("terminal_count", "remaining_count", "next_episode"):
        if state.get(field) != expected_core.get(field):
            return [f"priority queue state field is stale: {field}"]
    return []


def load_queue_state(queue_path: Path, state_path: Path | None = None) -> tuple[dict[str, Any] | None, list[str]]:
    resolved_state_path = state_path or queue_state_path(queue_path)
    if not resolved_state_path.is_file():
        return None, []
    try:
        queue = load_json(queue_path)
        state = load_json(resolved_state_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return None, [f"priority queue state is invalid: {error}"]
    return state, queue_state_errors(queue, state)


def render_queue_state_markdown(queue: dict[str, Any], state: dict[str, Any] | None = None) -> list[str]:
    if state is None:
        return []
    next_episode = state.get("next_episode")
    if not isinstance(next_episode, dict):
        return ["## Next Extraction", "", "No pending episode remains in this queue.", ""]
    return [
        "## Next Extraction",
        "",
        f"**Next:** `{next_episode['video_id']}` (rank {next_episode.get('rank')}, {next_episode.get('category_label')})",
        f"**Remaining:** {state.get('remaining_count')} | **Finalized/complete:** {state.get('terminal_count')}",
        f"**Title:** {next_episode.get('title')}",
        "",
    ]


def write_queue_state(
    queue_path: Path,
    state: dict[str, Any],
    *,
    state_path: Path | None = None,
    markdown_path: Path | None = None,
) -> Path:
    queue = load_json(queue_path)
    errors = queue_state_errors(queue, state)
    if errors:
        raise ValueError("; ".join(errors))
    resolved_state_path = state_path or queue_state_path(queue_path)
    write_json(resolved_state_path, state)
    resolved_markdown_path = markdown_path or queue_path.with_suffix(".md")
    resolved_markdown_path.write_text(render_markdown(queue, state), encoding="utf-8", newline="\n")
    return resolved_state_path


def advance_queue_state(
    queue_path: Path,
    video_id: str,
    state: str,
    *,
    state_path: Path | None = None,
    source: str = "runtime",
) -> dict[str, Any]:
    queue = load_json(queue_path)
    entries = queue.get("entries", [])
    if not any(isinstance(item, dict) and item.get("video_id") == video_id for item in entries):
        raise ValueError(f"video_id is not present in priority queue: {video_id}")
    existing, errors = load_queue_state(queue_path, state_path)
    if errors:
        raise ValueError("; ".join(errors))
    updated = build_queue_state(queue, previous_state=existing, terminal_updates={video_id: state}, source=source)
    write_queue_state(queue_path, updated, state_path=state_path)
    return updated


def _duration_label(seconds: float) -> str:
    total = int(round(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def render_markdown(queue: dict[str, Any], state: dict[str, Any] | None = None) -> str:
    terminal_ids = {
        str(item.get("video_id") or "")
        for item in (state or {}).get("terminal_entries", [])
        if isinstance(item, dict)
    }
    active_entries = [
        item for item in queue["entries"]
        if str(item.get("video_id") or "") not in terminal_ids
    ]
    lines = [
        "# Gold Episode Priority Queue",
        "",
        "Durable extraction order. Classification uses title aliases in owner-defined priority order; episodes are shortest-first inside each category. This catalog does not certify source availability.",
        "",
        f"Catalog episodes: **{queue['total_episodes']}**",
        f"Active queue: **{len(active_entries)}**",
        "The selector validates only the displayed next episode against the active data root before any gold work.",
        "",
        *render_queue_state_markdown(queue, state),
    ]
    for category in queue["category_order"]:
        items = [item for item in active_entries if item["category"] == category]
        if not items:
            continue
        lines.extend([
            f"## {CATEGORY_LABELS[category]} ({len(items)})",
            "",
            "| Rank | Video ID | Duration | Catalog state | Segments | Title |",
            "| ---: | --- | ---: | --- | ---: | --- |",
        ])
        for item in items:
            title = str(item["title"]).replace("|", "\\|")
            lines.append(f"| {item['rank']} | `{item['video_id']}` | {_duration_label(item['duration_seconds'])} | {item.get('source_status', CATALOG_UNVERIFIED)} | {item['clean_segments']} | {title} |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--data-root", type=Path)
    source.add_argument("--base-queue", type=Path, help="Rebuild from an existing queue snapshot when the active data root is unavailable")
    parser.add_argument("--catalog-csv", type=Path)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--state-output", type=Path, help="Create or refresh the mutable cursor beside the immutable queue.")
    parser.add_argument("--terminal-video-id", action="append", default=[], help="Seed a known complete/passed episode into the queue cursor.")
    args = parser.parse_args()
    base_entries = None
    if args.base_queue is not None:
        base_payload = load_json(args.base_queue)
        base_entries = base_payload.get("entries", []) if isinstance(base_payload, dict) else []
        if not isinstance(base_entries, list):
            raise ValueError("base queue entries must be a list")
    queue = build_priority_queue(args.data_root, catalog=_catalog_rows(args.catalog_csv), base_entries=base_entries)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.json_output, queue)
    state = None
    if args.state_output is not None:
        previous = load_json(args.state_output) if args.state_output.is_file() else None
        state = build_queue_state(
            queue,
            previous_state=previous,
            terminal_updates={video_id: "complete_passed" for video_id in args.terminal_video_id},
            source="initialization",
        )
        write_json(args.state_output, state)
    args.markdown_output.write_text(render_markdown(queue, state), encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": "ok",
        "total_episodes": queue["total_episodes"],
        "runtime_ready_episodes": queue["runtime_ready_episodes"],
        "catalog_unverified_episodes": queue["catalog_unverified_episodes"],
        "next_episode": queue["entries"][0] if queue["entries"] else None,
        "queue_state": state,
        "json_output": str(args.json_output),
        "markdown_output": str(args.markdown_output),
        "semantic_sha256": queue["semantic_sha256"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
