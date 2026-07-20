#!/usr/bin/env python
"""Build a deterministic navigation index over one clean transcript.

The index is derived, disposable, and deliberately non-editorial.  It groups
contiguous source segments into small navigation units, preserves every source
text verbatim, and surfaces deterministic cues that help the semantic reviewer
find numeric trajectories, mechanisms, procedures, outcomes, caveats, and
boundaries.  It never creates a gold claim or replaces chronological reading.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from scripts.gold_extraction_common import (
    GoldPauseError,
    load_json,
    normalize_ascii,
    now,
    numeric_mentions,
    sha256_semantic_json,
    signal_types,
    write_json,
)


INDEX_SCHEMA_VERSION = "1.0.0"
INDEX_ALGORITHM_VERSION = "semantic-navigation-v1"
INDEX_FILENAME = "transcript_semantic_index.jsonl"
STATUS_FILENAME = "transcript_semantic_index_status.json"
MAX_UNIT_SEGMENTS = 6
MAX_UNIT_CHARS = 900
MAX_GAP_SECONDS = 6.0

MECHANISM_RE = re.compile(
    r"\b(?:mecanismo|por\s+que|porque|faz\s+com\s+que|causa|explica|responsavel\s+por)\b",
    re.I,
)
OUTCOME_RE = re.compile(
    r"\b(?:resultado|converteu|conversao|vendeu|vendas|faturou|faturamento|lucro|"
    r"retorno|roi|roas|aumentou|diminuiu|caiu|dobrou|triplicou|funcionou)\b",
    re.I,
)
CAVEAT_RE = re.compile(
    r"\b(?:depende|cuidado|ressalva|nao\s+significa|nao\s+garante|pode\s+variar|"
    r"nesse\s+caso|naquele\s+caso|segundo\s+ele|segundo\s+ela|relatou|afirmou)\b",
    re.I,
)
PROMO_RE = re.compile(
    r"\b(?:se\s+inscrev|link\s+na\s+descricao|deixa\s+o\s+like|curte\s+o\s+video|"
    r"compartilha|comenta\s+aqui|nosso\s+curso|minha\s+mentoria|clique\s+no\s+link)\b",
    re.I,
)
QUESTION_RE = re.compile(
    r"(?:\?$|\b(?:me\s+conta|queria\s+te\s+perguntar|como\s+que|o\s+que\s+voce|"
    r"qual\s+foi|por\s+que\s+voce|voce\s+acha|faz\s+sentido)\b)",
    re.I,
)
ATTRIBUTION_RE = re.compile(
    r"\b(?:ele\s+disse|ela\s+disse|segundo\s+ele|segundo\s+ela|o\s+cliente\s+relatou|"
    r"o\s+entrevistado|a\s+entrevistada|afirmou|relatou)\b",
    re.I,
)
NUMBER_WORD_UNIT_RE = re.compile(
    r"\b(?:um|uma|dois|duas|tr[eê]s|quatro|cinco|seis|sete|oito|nove|dez|"
    r"onze|doze|treze|quatorze|catorze|quinze|dezesseis|dezessete|dezoito|"
    r"dezenove|vinte|trinta|quarenta|cinquenta|sessenta|setenta|oitenta|"
    r"noventa|cem|cento|mil)\s+(?:segundos?|minutos?|horas?|dias?|semanas?|"
    r"mes(?:es)?|anos?|vendas?|leads?|alunos?|clientes?|pessoas?)\b",
    re.I,
)
DISCOURSE_START_RE = re.compile(
    r"^(?:agora|mas|entao|primeiro|segundo|terceiro|outra|outro|por\s+fim|em\s+seguida)\b",
    re.I,
)


def semantic_index_paths(data_root: Path, video_id: str) -> tuple[Path, Path]:
    processed = data_root / "processed" / video_id
    return processed / INDEX_FILENAME, processed / STATUS_FILENAME


def source_semantic_sha256(video_id: str, segments: list[dict[str, Any]]) -> str:
    return sha256_semantic_json({"episode_video_id": video_id, "segments": segments})


def _segment_cues(segment: dict[str, Any], known_signals: Iterable[str] | None = None) -> list[str]:
    text = str(segment.get("text", ""))
    normalized = normalize_ascii(text)
    cues = set(known_signals or signal_types(text))
    if numeric_mentions(text):
        cues.add("number")
    if NUMBER_WORD_UNIT_RE.search(text):
        cues.add("number_word")
    if MECHANISM_RE.search(normalized):
        cues.add("mechanism")
    if OUTCOME_RE.search(normalized):
        cues.add("outcome")
    if CAVEAT_RE.search(normalized):
        cues.add("caveat")
    if PROMO_RE.search(normalized):
        cues.add("promo")
    if QUESTION_RE.search(normalized):
        cues.add("interviewer_question")
    if ATTRIBUTION_RE.search(normalized):
        cues.add("reported_attribution")
    return sorted(cues)


def _primary_cues(cues: Iterable[str]) -> set[str]:
    return set(cues) & {
        "number", "number_word", "comparison", "procedure", "experiment", "sequence",
        "mechanism", "outcome", "caveat", "promo", "interviewer_question",
    }


def _should_split(current: list[dict[str, Any]], segment: dict[str, Any]) -> bool:
    if not current:
        return False
    if len(current) >= MAX_UNIT_SEGMENTS:
        return True
    if sum(len(str(item.get("text", ""))) for item in current) + len(str(segment.get("text", ""))) > MAX_UNIT_CHARS:
        return True
    previous = current[-1]
    previous_end = float(previous.get("start_seconds", 0.0)) + float(previous.get("duration_seconds", 0.0))
    if float(segment.get("start_seconds", 0.0)) - previous_end > MAX_GAP_SECONDS:
        return True
    current_primary = set().union(*(_primary_cues(item.get("_semantic_cues", [])) for item in current))
    next_primary = _primary_cues(segment.get("_semantic_cues", []))
    normalized = normalize_ascii(segment.get("text", "")).strip()
    if len(current) >= 2 and DISCOURSE_START_RE.search(normalized) and current_primary and next_primary and not (current_primary & next_primary):
        return True
    next_roles = {"promo", "interviewer_question"} & next_primary
    current_roles = {"promo", "interviewer_question"} & current_primary
    if next_roles and next_roles != current_roles:
        return True
    return False


def _unit_type(cues: set[str]) -> str:
    has_number = bool({"number", "number_word"} & cues)
    if has_number and ({"outcome", "comparison", "sequence"} & cues):
        return "numeric_trajectory"
    if "mechanism" in cues and "sequence" in cues:
        return "mechanism_sequence"
    if "outcome" in cues and "mechanism" in cues:
        return "reported_outcome"
    if "comparison" in cues:
        return "before_after"
    if "procedure" in cues:
        return "procedure"
    if "caveat" in cues:
        return "caveat"
    if "promo" in cues:
        return "promo"
    if has_number:
        return "numeric_claim"
    if "experiment" in cues or "outcome" in cues:
        return "result_or_test"
    return "context"


def _speaker_role(cues: set[str]) -> str:
    if {"promo", "interviewer_question"} <= cues:
        return "unknown"
    if "promo" in cues:
        return "promo"
    if "interviewer_question" in cues:
        return "interviewer"
    return "unknown"


def _risk_score(cues: set[str], numbers: list[dict[str, Any]], crosses_chunk_boundary: bool) -> int:
    score = 0
    score += min(3, len(numbers))
    score += 1 if "number_word" in cues else 0
    score += 3 if "comparison" in cues else 0
    score += 3 if "outcome" in cues else 0
    score += 2 if "mechanism" in cues else 0
    score += 2 if "procedure" in cues else 0
    score += 2 if "sequence" in cues else 0
    score += 1 if "caveat" in cues or "reported_attribution" in cues else 0
    score += 2 if crosses_chunk_boundary else 0
    if "promo" in cues and not ({"number", "number_word", "comparison", "outcome", "mechanism", "procedure"} & cues):
        score = max(0, score - 3)
    return score


def _risk_tier(score: int) -> str:
    if score >= 8:
        return "high"
    if score >= 4:
        return "medium"
    return "low"


def build_semantic_index(
    video_id: str,
    segments: list[dict[str, Any]],
    *,
    chunks: list[list[dict[str, Any]]] | None = None,
    signals: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return a deterministic JSONL-ready semantic navigation index."""
    signal_by_id = {
        str(item.get("segment_id")): list(item.get("signal_types") or [])
        for item in (signals or []) if isinstance(item, dict)
    }
    chunk_by_id: dict[str, int] = {}
    for chunk_number, chunk in enumerate(chunks or [], 1):
        for segment in chunk:
            chunk_by_id[str(segment.get("segment_id"))] = chunk_number

    enriched: list[dict[str, Any]] = []
    for segment in segments:
        item = dict(segment)
        item["_semantic_cues"] = _segment_cues(item, signal_by_id.get(str(item.get("segment_id"))))
        enriched.append(item)

    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for segment in enriched:
        if _should_split(current, segment):
            groups.append(current)
            current = []
        current.append(segment)
    if current:
        groups.append(current)

    units: list[dict[str, Any]] = []
    for index, group in enumerate(groups, 1):
        unit_id = f"{video_id}-semantic-unit-{index:04d}"
        cues = set().union(*(set(item.get("_semantic_cues", [])) for item in group))
        numbers = [
            {
                "segment_id": item["segment_id"],
                "clean_index": int(item["clean_index"]),
                **mention,
            }
            for item in group
            for mention in numeric_mentions(item.get("text", ""))
        ]
        written_number_mentions = [
            {
                "segment_id": item["segment_id"],
                "clean_index": int(item["clean_index"]),
                "raw": match.group(0),
                "kind": "written_unit",
                "start": match.start(),
                "end": match.end(),
            }
            for item in group
            for match in NUMBER_WORD_UNIT_RE.finditer(str(item.get("text", "")))
        ]
        chunk_numbers = sorted({chunk_by_id[item["segment_id"]] for item in group if item["segment_id"] in chunk_by_id})
        crosses_chunk_boundary = len(chunk_numbers) > 1
        score = _risk_score(cues, numbers, crosses_chunk_boundary)
        verbatim_segments = [
            {
                "segment_id": item["segment_id"],
                "clean_index": int(item["clean_index"]),
                "start_seconds": float(item["start_seconds"]),
                "duration_seconds": float(item.get("duration_seconds", 0.0)),
                "text": item["text"],
            }
            for item in group
        ]
        unit_core = {
            "kind": "transcript_semantic_unit",
            "unit_id": unit_id,
            "clean_index_range": [int(group[0]["clean_index"]), int(group[-1]["clean_index"])],
            "segment_ids": [item["segment_id"] for item in group],
            "start_seconds": float(group[0]["start_seconds"]),
            "end_seconds": float(group[-1]["start_seconds"]) + float(group[-1].get("duration_seconds", 0.0)),
            "chunk_numbers": chunk_numbers,
            "crosses_chunk_boundary": crosses_chunk_boundary,
            "speaker_role": _speaker_role(cues),
            "unit_type": _unit_type(cues),
            "cues": sorted(cues),
            "risk_score": score,
            "risk_tier": _risk_tier(score),
            "numbers": numbers,
            "written_number_mentions": written_number_mentions,
            "verbatim_text": " ".join(str(item["text"]) for item in group),
            "verbatim_segments": verbatim_segments,
        }
        unit_core["source_semantic_sha256"] = sha256_semantic_json(verbatim_segments)
        units.append(unit_core)

    for index, unit in enumerate(units):
        unit["boundary_links"] = {
            "previous_unit_id": units[index - 1]["unit_id"] if index else None,
            "next_unit_id": units[index + 1]["unit_id"] if index + 1 < len(units) else None,
        }

    cue_counts = Counter(cue for unit in units for cue in unit["cues"])
    header = {
        "kind": "transcript_semantic_index_header",
        "schema_version": INDEX_SCHEMA_VERSION,
        "algorithm_version": INDEX_ALGORITHM_VERSION,
        "episode_video_id": video_id,
        "source_semantic_sha256": source_semantic_sha256(video_id, segments),
        "source_segment_count": len(segments),
        "unit_count": len(units),
        "cue_counts": dict(sorted(cue_counts.items())),
        "contract": {
            "authority": "navigation_only",
            "chronological_reading_required": True,
            "verbatim_segments_preserved": True,
            "editorial_claims_created": False,
        },
    }
    footer = {
        "kind": "transcript_semantic_index_footer",
        "unit_count": len(units),
        "units_semantic_sha256": sha256_semantic_json(units),
    }
    records = [header, *units, footer]
    return {
        "header": header,
        "units": units,
        "footer": footer,
        "records": records,
        "semantic_sha256": sha256_semantic_json(records),
    }


def _write_jsonl_atomic(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
        os.replace(temporary, path)
    except Exception as exc:
        if temporary.exists():
            temporary.unlink()
        if isinstance(exc, PermissionError):
            raise GoldPauseError(f"filesystem permission/lock while writing {path}") from exc
        raise


def _read_records(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def semantic_index_state(video_id: str, data_root: Path, segments: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate the derived index without writing or repairing it."""
    index_path, status_path = semantic_index_paths(data_root, video_id)
    expected_source = source_semantic_sha256(video_id, segments)
    if not index_path.exists() or not status_path.exists():
        return {"status": "missing", "current": False, "index_path": str(index_path), "status_path": str(status_path)}
    try:
        status = load_json(status_path)
        records = _read_records(index_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"status": "invalid", "current": False, "error": str(exc), "index_path": str(index_path), "status_path": str(status_path)}
    physical_sha256 = hashlib.sha256(index_path.read_bytes()).hexdigest()
    semantic_sha256 = sha256_semantic_json(records)
    header = records[0] if records else {}
    footer = records[-1] if records else {}
    units = records[1:-1] if len(records) >= 2 else []
    errors: list[str] = []
    if status.get("episode_video_id") != video_id or header.get("episode_video_id") != video_id:
        errors.append("episode_video_id mismatch")
    if status.get("algorithm_version") != INDEX_ALGORITHM_VERSION or header.get("algorithm_version") != INDEX_ALGORITHM_VERSION:
        errors.append("algorithm version is stale")
    if status.get("source_semantic_sha256") != expected_source or header.get("source_semantic_sha256") != expected_source:
        errors.append("source transcript hash is stale")
    if status.get("index_physical_sha256") != physical_sha256:
        errors.append("physical index hash mismatch")
    if status.get("index_semantic_sha256") != semantic_sha256:
        errors.append("semantic index hash mismatch")
    if header.get("unit_count") != len(units) or footer.get("unit_count") != len(units):
        errors.append("unit count mismatch")
    if footer.get("units_semantic_sha256") != sha256_semantic_json(units):
        errors.append("unit content hash mismatch")
    return {
        "status": "ready" if not errors else "stale",
        "current": not errors,
        "errors": errors,
        "index_path": str(index_path),
        "status_path": str(status_path),
        "source_semantic_sha256": expected_source,
        "index_physical_sha256": physical_sha256,
        "index_semantic_sha256": semantic_sha256,
        "unit_count": len(units),
        "cue_counts": header.get("cue_counts", {}),
        "units": units if not errors else [],
    }


def ensure_semantic_index(
    video_id: str,
    data_root: Path,
    segments: list[dict[str, Any]],
    *,
    chunks: list[list[dict[str, Any]]] | None = None,
    signals: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    current = semantic_index_state(video_id, data_root, segments)
    if current.get("current"):
        return {**current, "reused": True}
    built = build_semantic_index(video_id, segments, chunks=chunks, signals=signals)
    index_path, status_path = semantic_index_paths(data_root, video_id)
    _write_jsonl_atomic(index_path, built["records"])
    physical_sha256 = hashlib.sha256(index_path.read_bytes()).hexdigest()
    semantic_sha256 = sha256_semantic_json(_read_records(index_path))
    write_json(status_path, {
        "schema_version": INDEX_SCHEMA_VERSION,
        "kind": "transcript_semantic_index_status",
        "status": "ready",
        "episode_video_id": video_id,
        "algorithm_version": INDEX_ALGORITHM_VERSION,
        "source_semantic_sha256": built["header"]["source_semantic_sha256"],
        "source_segment_count": len(segments),
        "unit_count": len(built["units"]),
        "cue_counts": built["header"]["cue_counts"],
        "index_file": INDEX_FILENAME,
        "index_physical_sha256": physical_sha256,
        "index_semantic_sha256": semantic_sha256,
        "generated_at": now(),
    })
    verified = semantic_index_state(video_id, data_root, segments)
    if not verified.get("current"):
        raise GoldPauseError(f"semantic transcript index failed post-write validation: {verified.get('errors')}")
    return {**verified, "reused": False}


def semantic_navigation_summary(
    video_id: str,
    data_root: Path,
    segments: list[dict[str, Any]],
    *,
    limit: int = 48,
) -> dict[str, Any]:
    state = semantic_index_state(video_id, data_root, segments)
    if not state.get("current"):
        return {key: value for key, value in state.items() if key != "units"}
    ranked = sorted(
        state.get("units", []),
        key=lambda item: (-int(item.get("risk_score", 0)), item.get("clean_index_range", [0])[0]),
    )[:max(0, limit)]
    navigation_units = [{
        "unit_id": item["unit_id"],
        "range": item["clean_index_range"],
        "segment_ids": item["segment_ids"],
        "chunk_numbers": item["chunk_numbers"],
        "unit_type": item["unit_type"],
        "speaker_role": item["speaker_role"],
        "cues": item["cues"],
        "risk_score": item["risk_score"],
        "risk_tier": item["risk_tier"],
        "number_raws": [number["raw"] for number in item.get("numbers", [])],
        "written_number_raws": [number["raw"] for number in item.get("written_number_mentions", [])],
        "crosses_chunk_boundary": item["crosses_chunk_boundary"],
    } for item in ranked]
    return {
        "status": "ready",
        "current": True,
        "authority": "navigation_only",
        "index_path": state["index_path"],
        "status_path": state["status_path"],
        "source_semantic_sha256": state["source_semantic_sha256"],
        "index_semantic_sha256": state["index_semantic_sha256"],
        "unit_count": state["unit_count"],
        "cue_counts": state.get("cue_counts", {}),
        "navigation_units": navigation_units,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--data-root", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Validate current index without writing.")
    mode.add_argument("--build", action="store_true", help="Create or refresh the derived index atomically.")
    args = parser.parse_args()
    clean_path = args.data_root / "processed" / args.video_id / "gold_extraction" / "transcript_clean.json"
    if not clean_path.exists():
        print(json.dumps({"status": "missing", "error": f"missing clean transcript: {clean_path}"}))
        return 1
    segments = load_json(clean_path).get("segments", [])
    if args.check:
        result = semantic_index_state(args.video_id, args.data_root, segments)
    else:
        chunk_dir = clean_path.parent / "chunks"
        chunks = [load_json(path).get("segments", []) for path in sorted(chunk_dir.glob("chunk_[0-9][0-9][0-9].json"))]
        signals_path = clean_path.parent / "signal_inventory.json"
        signals = load_json(signals_path).get("signals", []) if signals_path.exists() else []
        result = ensure_semantic_index(args.video_id, args.data_root, segments, chunks=chunks, signals=signals)
    result = {key: value for key, value in result.items() if key != "units"}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("current") else 1


if __name__ == "__main__":
    raise SystemExit(main())
