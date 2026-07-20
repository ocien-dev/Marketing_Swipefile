#!/usr/bin/env python3
"""Prepare Baoyu/Chrome transcript captures for the validated backfill importer."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.backfill_vturb_transcripts import atomic_write_json


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def timestamp_seconds(value: str) -> float:
    parts = [float(part) for part in str(value).strip().split(":")]
    if not parts or len(parts) > 3:
        raise ValueError(f"invalid timestamp: {value}")
    total = 0.0
    for part in parts:
        total = total * 60 + part
    return total


def canonical_payload(
    video_id: str,
    language: str,
    provider: str,
    segments: list[dict[str, Any]],
) -> dict[str, Any]:
    normalized = []
    for segment in segments:
        text = str(segment.get("text") or "").strip()
        if not text:
            continue
        if segment.get("start_seconds") is not None:
            start = float(segment["start_seconds"])
        elif segment.get("start") is not None:
            start = float(segment["start"])
        else:
            start = timestamp_seconds(str(segment.get("timestamp") or ""))
        duration = segment.get("duration_seconds", segment.get("duration"))
        normalized.append({
            "start_seconds": round(start, 3),
            "duration_seconds": round(max(float(duration or 0.0), 0.0), 3),
            "text": text,
        })
    normalized.sort(key=lambda item: item["start_seconds"])
    for index, segment in enumerate(normalized[:-1]):
        if segment["duration_seconds"] <= 0:
            segment["duration_seconds"] = round(
                max(normalized[index + 1]["start_seconds"] - segment["start_seconds"], 0.0), 3
            )
    return {
        "schema_version": "1.0",
        "youtube_video_id": video_id,
        "source_kind": "transcript",
        "transcript_status": "available",
        "language": language,
        "provider": provider,
        "collected_at": utc_now(),
        "segments": normalized,
    }


def baoyu_payload(root: Path, video_id: str, relative: str) -> dict[str, Any]:
    directory = (root / relative).resolve()
    if root.resolve() not in directory.parents:
        raise ValueError(f"unsafe Baoyu index path for {video_id}: {relative}")
    meta = read_json(directory / "meta.json")
    raw = read_json(directory / "transcript-raw.json")
    if meta.get("videoId") != video_id:
        raise ValueError(f"Baoyu metadata id mismatch: {video_id}")
    language = str((meta.get("language") or {}).get("code") or "").strip()
    if not language:
        raise ValueError(f"Baoyu language missing: {video_id}")
    return canonical_payload(video_id, language, "baoyu_youtube_transcript:youtube_captions", raw)


def browser_payload(video_id: str, path: Path) -> dict[str, Any]:
    source = read_json(path)
    if source.get("video_id") not in {None, video_id} and source.get("youtube_video_id") not in {None, video_id}:
        raise ValueError(f"browser capture id mismatch: {video_id}")
    return canonical_payload(
        video_id,
        str(source.get("language") or "").strip(),
        str(source.get("source") or source.get("provider") or "chrome_transcript_panel"),
        list(source.get("segments") or []),
    )


def parse_named_path(value: str) -> tuple[str, Path]:
    match = re.fullmatch(r"([A-Za-z0-9_-]{11})=(.+)", value)
    if not match:
        raise argparse.ArgumentTypeError("expected VIDEO_ID=PATH")
    return match.group(1), Path(match.group(2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baoyu-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--browser-json", action="append", default=[], type=parse_named_path)
    parser.add_argument("--summary-output", type=Path)
    args = parser.parse_args()

    index_path = args.baoyu_root / ".index.json"
    index = read_json(index_path) if index_path.is_file() else {}
    if not isinstance(index, dict):
        raise ValueError("Baoyu index must be an object")
    prepared: list[dict[str, Any]] = []
    for video_id, relative in sorted(index.items()):
        payload = baoyu_payload(args.baoyu_root, video_id, str(relative))
        target = args.output_dir / f"{video_id}.json"
        atomic_write_json(target, payload)
        prepared.append({
            "video_id": video_id,
            "language": payload["language"],
            "segments": len(payload["segments"]),
            "provider": payload["provider"],
            "path": str(target),
        })
    for video_id, source in args.browser_json:
        payload = browser_payload(video_id, source)
        target = args.output_dir / f"{video_id}.json"
        atomic_write_json(target, payload)
        prepared.append({
            "video_id": video_id,
            "language": payload["language"],
            "segments": len(payload["segments"]),
            "provider": payload["provider"],
            "path": str(target),
        })
    by_language: dict[str, int] = {}
    for item in prepared:
        by_language[item["language"]] = by_language.get(item["language"], 0) + 1
    summary = {
        "schema_version": "1.0.0",
        "kind": "vturb_transcript_import_preparation",
        "generated_at": utc_now(),
        "prepared": len(prepared),
        "by_language": dict(sorted(by_language.items())),
        "items": sorted(prepared, key=lambda item: item["video_id"]),
    }
    if args.summary_output:
        atomic_write_json(args.summary_output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
