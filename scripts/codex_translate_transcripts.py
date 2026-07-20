#!/usr/bin/env python3
"""Prepare, assemble, validate, and promote Codex transcript translations."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.backfill_vturb_transcripts import (
    atomic_write_json,
    content_path,
    metadata_path,
    normalize_transcript,
    read_json,
    utc_now,
    validate_transcript_payload,
)


def source_path(data_root: Path, video_id: str) -> Path:
    return data_root / "raw" / "youtube" / video_id / "transcript_original.json"


def translation_path(data_root: Path, video_id: str) -> Path:
    return data_root / "raw" / "youtube" / video_id / "transcript_pt_br.json"


def source_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_units(payload: dict[str, Any], unit_seconds: float) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for segment in payload.get("segments") or []:
        text = str(segment.get("text") or "").strip()
        if not text:
            continue
        start = float(segment.get("start_seconds") or 0)
        duration = max(float(segment.get("duration_seconds") or 0), 0.0)
        bucket = int(start // unit_seconds)
        if not units or units[-1]["bucket"] != bucket:
            units.append({
                "bucket": bucket,
                "unit_id": f"U{bucket + 1:04d}",
                "start_seconds": start,
                "end_seconds": start + duration,
                "source_text_parts": [text],
            })
        else:
            units[-1]["source_text_parts"].append(text)
            units[-1]["end_seconds"] = max(units[-1]["end_seconds"], start + duration)
    result = []
    for unit in units:
        result.append({
            "unit_id": unit["unit_id"],
            "start_seconds": round(unit["start_seconds"], 3),
            "duration_seconds": round(max(unit["end_seconds"] - unit["start_seconds"], 0.0), 3),
            "source_text": " ".join(unit["source_text_parts"]),
        })
    return result


def prepare(video_id: str, data_root: Path, job_root: Path, unit_seconds: float, batch_chars: int) -> dict[str, Any]:
    path = source_path(data_root, video_id)
    payload = read_json(path)
    units = make_units(payload, unit_seconds)
    episode_root = job_root / video_id
    episode_root.mkdir(parents=True, exist_ok=True)
    batches: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_chars = 0
    for unit in units:
        unit_chars = len(unit["source_text"])
        if current and current_chars + unit_chars > batch_chars:
            batches.append(current)
            current = []
            current_chars = 0
        current.append(unit)
        current_chars += unit_chars
    if current:
        batches.append(current)
    batch_items = []
    for index, batch in enumerate(batches, start=1):
        batch_id = f"batch_{index:03d}"
        source_file = episode_root / f"{batch_id}_source.json"
        translation_file = episode_root / f"{batch_id}_translation.json"
        atomic_write_json(source_file, {
            "schema_version": "1.0.0",
            "kind": "codex_translation_source_batch",
            "video_id": video_id,
            "source_language": payload.get("language"),
            "target_language": "pt-BR",
            "source_transcript_sha256": source_sha256(path),
            "batch_id": batch_id,
            "instructions": "Translate every source_text faithfully to natural pt-BR. Preserve names, numbers, technical terms and meaning. Return a translation JSON keyed by unit_id.",
            "units": batch,
        })
        batch_items.append({
            "batch_id": batch_id,
            "source": str(source_file),
            "translation": str(translation_file),
            "units": len(batch),
            "source_chars": sum(len(item["source_text"]) for item in batch),
        })
    manifest = {
        "schema_version": "1.0.0",
        "kind": "codex_translation_manifest",
        "video_id": video_id,
        "source_language": payload.get("language"),
        "target_language": "pt-BR",
        "source_transcript_sha256": source_sha256(path),
        "unit_seconds": unit_seconds,
        "unit_count": len(units),
        "batch_count": len(batch_items),
        "batches": batch_items,
    }
    atomic_write_json(episode_root / "manifest.json", manifest)
    return manifest


def assemble(video_id: str, data_root: Path, job_root: Path, output_dir: Path) -> dict[str, Any]:
    episode_root = job_root / video_id
    manifest = read_json(episode_root / "manifest.json")
    current_sha = source_sha256(source_path(data_root, video_id))
    if manifest.get("source_transcript_sha256") != current_sha:
        raise ValueError("source transcript fingerprint changed")
    translated_segments: list[dict[str, Any]] = []
    missing: list[str] = []
    for batch in manifest.get("batches") or []:
        source = read_json(Path(batch["source"]))
        translated_file = Path(batch["translation"])
        if not translated_file.is_file():
            missing.append(str(translated_file))
            continue
        translated = read_json(translated_file)
        translations = translated.get("translations")
        if not isinstance(translations, dict):
            raise ValueError(f"translations must be an object: {translated_file}")
        expected = {unit["unit_id"] for unit in source.get("units") or []}
        if set(translations) != expected:
            raise ValueError(f"translation unit mismatch: {translated_file}")
        for unit in source["units"]:
            text = str(translations.get(unit["unit_id"]) or "").strip()
            if not text:
                raise ValueError(f"empty translation {unit['unit_id']}: {translated_file}")
            translated_segments.append({
                "start_seconds": unit["start_seconds"],
                "duration_seconds": unit["duration_seconds"],
                "text": text,
            })
    if missing:
        return {"status": "incomplete", "video_id": video_id, "missing": missing}
    payload = {
        "schema_version": "1.0",
        "youtube_video_id": video_id,
        "source_kind": "transcript_translation",
        "transcript_status": "available",
        "language": "pt-BR",
        "source_language": manifest.get("source_language"),
        "provider": "codex:faithful_translation",
        "translated_at": utc_now(),
        "source_transcript_sha256": current_sha,
        "segments": translated_segments,
    }
    output = output_dir / f"{video_id}.json"
    atomic_write_json(output, payload)
    return {"status": "assembled", "video_id": video_id, "segments": len(translated_segments), "path": str(output)}


def promote(video_id: str, data_root: Path, input_path: Path) -> dict[str, Any]:
    payload = read_json(input_path)
    original = source_path(data_root, video_id)
    current_sha = source_sha256(original)
    if payload.get("source_transcript_sha256") != current_sha:
        raise ValueError("translation source fingerprint does not match original")
    if str(payload.get("language") or "").lower() not in {"pt", "pt-br", "pt_br"}:
        raise ValueError("translation language must be pt-BR")
    meta = read_json(metadata_path(data_root, video_id))
    validation = validate_transcript_payload(
        payload,
        video_id=video_id,
        duration_seconds=float(meta.get("duration_seconds") or 0),
        minimum_bytes=1_000,
        minimum_coverage=0.60,
    )
    if validation["errors"]:
        raise ValueError(f"invalid translation: {validation['errors']}")
    target = translation_path(data_root, video_id)
    atomic_write_json(target, payload)
    normalized = normalize_transcript(payload)
    atomic_write_json(content_path(data_root, video_id), normalized)
    meta.update({
        "translation_status": "available",
        "translation_language": "pt-BR",
        "translation_provider": payload.get("provider"),
        "translation_sha256": validation["sha256"],
        "translation_segments": validation["segment_count"],
        "translation_last_timestamp": validation["last_timestamp"],
        "translation_coverage": validation["coverage"],
        "gold_transcript_language": "pt-BR",
    })
    atomic_write_json(metadata_path(data_root, video_id), meta)
    return {
        "status": "promoted",
        "video_id": video_id,
        "original": str(original),
        "translation": str(target),
        "segments": validation["segment_count"],
        "coverage": validation["coverage"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--video-id", required=True)
    sub = parser.add_mutually_exclusive_group(required=True)
    sub.add_argument("--prepare", action="store_true")
    sub.add_argument("--assemble", action="store_true")
    sub.add_argument("--promote", action="store_true")
    parser.add_argument("--job-root", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--unit-seconds", type=float, default=60)
    parser.add_argument("--batch-chars", type=int, default=30_000)
    args = parser.parse_args()
    if args.prepare:
        if args.job_root is None:
            parser.error("--prepare requires --job-root")
        result = prepare(args.video_id, args.data_root, args.job_root, args.unit_seconds, args.batch_chars)
    elif args.assemble:
        if args.job_root is None or args.output_dir is None:
            parser.error("--assemble requires --job-root and --output-dir")
        result = assemble(args.video_id, args.data_root, args.job_root, args.output_dir)
    else:
        if args.input is None:
            parser.error("--promote requires --input")
        result = promote(args.video_id, args.data_root, args.input)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") != "incomplete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
