#!/usr/bin/env python
"""Download and transcribe VTurb Academy HLS lesson videos."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from msf_common import slugify, write_json
from transcribe_academy_videos import (
    load_whisper_model,
    run_post_pipeline,
    transcribe_media,
    update_queue_status,
    utc_now,
    write_episode_metadata,
    write_transcript,
)


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read()


def parse_attributes(line: str) -> dict[str, str]:
    return {key: value.strip('"') for key, value in re.findall(r"([A-Z-]+)=([^,]+(?:\"[^\"]*\")?)", line)}


def parse_master_playlist(main_url: str, playlist_text: str) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    lines = [line.strip() for line in playlist_text.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        if not line.startswith("#EXT-X-STREAM-INF"):
            continue
        if index + 1 >= len(lines):
            continue
        attrs = parse_attributes(line)
        uri = lines[index + 1]
        if uri.startswith("#"):
            continue
        width = height = None
        if attrs.get("RESOLUTION") and "x" in attrs["RESOLUTION"]:
            width_text, height_text = attrs["RESOLUTION"].split("x", 1)
            width = int(width_text)
            height = int(height_text)
        variants.append(
            {
                "url": urllib.parse.urljoin(main_url, uri),
                "uri": uri,
                "bandwidth": int(attrs.get("BANDWIDTH") or 0),
                "average_bandwidth": int(attrs.get("AVERAGE-BANDWIDTH") or attrs.get("BANDWIDTH") or 0),
                "resolution": attrs.get("RESOLUTION"),
                "width": width,
                "height": height,
            }
        )
    return variants


def choose_variant(variants: list[dict[str, Any]], max_height: int) -> dict[str, Any]:
    eligible = [variant for variant in variants if not variant.get("height") or variant["height"] <= max_height]
    pool = eligible or variants
    return sorted(pool, key=lambda item: (item.get("average_bandwidth") or 0, item.get("height") or 0))[0]


def parse_media_playlist(variant_url: str, playlist_text: str) -> tuple[list[dict[str, Any]], float]:
    segments: list[dict[str, Any]] = []
    pending_duration: float | None = None
    total_duration = 0.0
    for line in playlist_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#EXTINF:"):
            duration_text = line.split(":", 1)[1].split(",", 1)[0]
            pending_duration = float(duration_text)
            total_duration += pending_duration
            continue
        if line.startswith("#"):
            continue
        segments.append(
            {
                "url": urllib.parse.urljoin(variant_url, line),
                "uri": line,
                "duration_seconds": pending_duration,
            }
        )
        pending_duration = None
    return segments, total_duration


def media_id_for_lesson(row: dict[str, Any]) -> str:
    lesson_url = row.get("source_url") or row.get("lessonUrl") or ""
    match = re.search(r"/lessons/([^/?#]+)", lesson_url)
    raw_id = match.group(1) if match else lesson_url
    safe = re.sub(r"[^A-Za-z0-9_-]+", "", raw_id)[:40] or slugify(row.get("lesson_title") or row.get("lessonTitle") or "academy-hls", 40)
    return f"academyhls-{safe}"


def load_manifest_rows(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("lessons", []))


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def queue_status_by_url(queue_path: Path) -> dict[str, str]:
    if not queue_path.exists():
        return {}
    return {row.get("source_url", ""): row.get("transcription_status", "") for row in csv_rows(queue_path)}


def existing_hls_download(media_path: Path, hls_info_path: Path, args: argparse.Namespace) -> tuple[Path, dict[str, Any]] | None:
    if not hls_info_path.exists() or args.force_download:
        return None
    info = json.loads(hls_info_path.read_text(encoding="utf-8"))
    chunks = info.get("chunks") or []
    if args.chunk_duration_min and chunks and all(Path(chunk["path"]).exists() for chunk in chunks):
        info["downloaded_bytes"] = sum(Path(chunk["path"]).stat().st_size for chunk in chunks)
        info["reused_existing"] = True
        return Path(chunks[0]["path"]), info
    if not args.chunk_duration_min and media_path.exists():
        info["downloaded_bytes"] = media_path.stat().st_size
        info["reused_existing"] = True
        return media_path, info
    return None


def download_hls(row: dict[str, Any], args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    media_id = media_id_for_lesson(row)
    media_dir = args.media_root / media_id
    media_path = media_dir / f"{media_id}__{slugify(row.get('lesson_title') or media_id, 80)}.ts"
    hls_info_path = media_dir / "hls_info.json"
    existing = existing_hls_download(media_path, hls_info_path, args)
    if existing:
        return existing

    main_url = row.get("main_m3u8_url")
    if not main_url:
        raise RuntimeError("no main_m3u8_url found")

    master_text = fetch_text(main_url)
    variants = parse_master_playlist(main_url, master_text)
    if not variants:
        variant_url = main_url
        variant = {"url": variant_url, "uri": Path(urllib.parse.urlparse(variant_url).path).name}
    else:
        variant = choose_variant(variants, args.max_height)
        variant_url = variant["url"]

    variant_text = fetch_text(variant_url)
    segments, duration_seconds = parse_media_playlist(variant_url, variant_text)
    if not segments:
        raise RuntimeError("HLS variant has no media segments")
    if args.max_duration_min and duration_seconds > args.max_duration_min * 60:
        raise RuntimeError(f"remote HLS duration is {round(duration_seconds)} seconds, over limit {args.max_duration_min * 60}")
    if args.max_segments and len(segments) > args.max_segments:
        raise RuntimeError(f"remote HLS has {len(segments)} segments, over limit {args.max_segments}")

    max_bytes = args.max_download_mb * 1024 * 1024
    media_dir.mkdir(parents=True, exist_ok=True)
    total_bytes = 0
    chunk_infos: list[dict[str, Any]] = []
    chunk_duration_limit = args.chunk_duration_min * 60 if args.chunk_duration_min else 0
    chunk_index = 1
    chunk_duration = 0.0
    chunk_start_seconds = 0.0
    chunk_segment_count = 0
    output_path = (
        media_dir / "chunks" / f"{media_id}__part_{chunk_index:03d}.ts"
        if chunk_duration_limit
        else media_path.with_suffix(".tmp")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output = output_path.open("wb")
    try:
        for index, segment in enumerate(segments, 1):
            segment_duration = float(segment.get("duration_seconds") or 0.0)
            if chunk_duration_limit and chunk_segment_count and chunk_duration + segment_duration > chunk_duration_limit:
                output.close()
                chunk_infos.append(
                    {
                        "path": str(output_path),
                        "duration_seconds": round(chunk_duration, 3),
                        "start_offset_seconds": round(chunk_start_seconds, 3),
                        "segment_count": chunk_segment_count,
                    }
                )
                chunk_start_seconds += chunk_duration
                chunk_duration = 0.0
                chunk_segment_count = 0
                chunk_index += 1
                output_path = media_dir / "chunks" / f"{media_id}__part_{chunk_index:03d}.ts"
                output = output_path.open("wb")
            payload = fetch_bytes(segment["url"])
            total_bytes += len(payload)
            if total_bytes > max_bytes:
                output.close()
                output_path.unlink(missing_ok=True)
                raise RuntimeError(f"download exceeded limit {max_bytes} bytes")
            output.write(payload)
            chunk_duration += segment_duration
            chunk_segment_count += 1
            if args.progress and (index == 1 or index == len(segments) or index % args.progress == 0):
                print(f"  segment {index}/{len(segments)} {round(total_bytes / 1024 / 1024, 1)} MB")
    finally:
        if not output.closed:
            output.close()

    if chunk_duration_limit:
        if chunk_segment_count:
            chunk_infos.append(
                {
                    "path": str(output_path),
                    "duration_seconds": round(chunk_duration, 3),
                    "start_offset_seconds": round(chunk_start_seconds, 3),
                    "segment_count": chunk_segment_count,
                }
            )
        returned_path = Path(chunk_infos[0]["path"])
    else:
        output_path.replace(media_path)
        returned_path = media_path

    info = {
        "main_m3u8_url": main_url,
        "variant": variant,
        "segment_count": len(segments),
        "hls_duration_seconds": round(duration_seconds, 3),
        "downloaded_bytes": total_bytes,
        "downloaded_at": utc_now(),
    }
    if chunk_infos:
        info["chunks"] = chunk_infos
    write_json(hls_info_path, info)
    return returned_path, info


def transcribe_hls_media(model: Any, media_path: Path, hls_info: dict[str, Any], model_name: str) -> dict[str, Any]:
    chunks = hls_info.get("chunks") or []
    if not chunks:
        return transcribe_media(model, media_path, model_name)

    all_segments: list[dict[str, Any]] = []
    language = None
    language_probability = None
    for chunk in chunks:
        chunk_info = transcribe_media(model, Path(chunk["path"]), model_name)
        if language is None:
            language = chunk_info.get("language")
            language_probability = chunk_info.get("language_probability")
        offset = float(chunk.get("start_offset_seconds") or 0.0)
        for segment in chunk_info.get("segments", []):
            next_segment = dict(segment)
            next_segment["index"] = len(all_segments)
            next_segment["start_seconds"] = round(float(next_segment["start_seconds"]) + offset, 3)
            all_segments.append(next_segment)
    return {
        "language": language,
        "language_probability": language_probability,
        "duration_seconds": round(float(hls_info.get("hls_duration_seconds") or 0.0)),
        "provider": f"faster_whisper:{model_name}:hls_chunks",
        "segments": all_segments,
    }


def process_row(args: argparse.Namespace, row: dict[str, Any], model: Any | None) -> dict[str, Any]:
    media_id = media_id_for_lesson(row)
    raw_dir = args.raw_root / media_id
    processed_dir = args.processed_root / media_id
    transcript_path = raw_dir / "transcript_original.json"
    result = {
        "media_id": media_id,
        "queue_type": "academy_lesson",
        "source_url": row.get("source_url"),
        "title": row.get("lesson_title"),
        "status": "pending",
    }

    if transcript_path.exists() and not args.force:
        result["status"] = "skipped_existing_transcript"
        return result
    if args.dry_run:
        result["status"] = "dry_run"
        return result

    media_path, hls_info = download_hls(row, args)
    result.update(hls_info)
    if model is None:
        raise RuntimeError("transcription model was not loaded")

    media_info = transcribe_hls_media(model, media_path, hls_info, args.model)
    synthetic_row = {
        "lesson_title": row.get("lesson_title"),
        "source_url": row.get("source_url"),
        "course": row.get("course") or "VTurb Academy",
    }
    write_episode_metadata(media_id, synthetic_row, media_info, raw_dir)
    write_transcript(media_id, media_info, raw_dir)
    if media_info.get("segments"):
        run_post_pipeline(media_id, raw_dir, processed_dir, args.max_chars)
        result["status"] = "transcribed"
    else:
        result["status"] = "transcribed_empty"
    result["segment_count"] = len(media_info.get("segments", []))
    result["language"] = media_info.get("language")
    result["duration_seconds"] = media_info.get("duration_seconds")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=Path("data/exports/vturb_academy_lesson_media_manifest.json"), type=Path)
    parser.add_argument("--queue", default=Path("data/input/academy_video_transcription_queue.csv"), type=Path)
    parser.add_argument("--limit", default=3, type=int)
    parser.add_argument("--max-download-mb", default=250, type=int)
    parser.add_argument("--max-duration-min", default=0, type=int)
    parser.add_argument("--max-segments", default=0, type=int)
    parser.add_argument("--max-height", default=360, type=int)
    parser.add_argument("--chunk-duration-min", default=20, type=int)
    parser.add_argument("--model", default="tiny")
    parser.add_argument("--deps-dir", default=Path(".codex_deps/transcription"), type=Path)
    parser.add_argument("--model-cache", default=Path("data/cache/faster_whisper"), type=Path)
    parser.add_argument("--media-root", default=Path("data/raw/academy_hls"), type=Path)
    parser.add_argument("--raw-root", default=Path("data/raw/youtube"), type=Path)
    parser.add_argument("--processed-root", default=Path("data/processed"), type=Path)
    parser.add_argument("--output-log", default=Path("data/logs/academy_hls_transcription_results.jsonl"), type=Path)
    parser.add_argument("--max-chars", default=50000, type=int)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--retry-status", action="append", default=[])
    parser.add_argument("--progress", default=0, type=int)
    args = parser.parse_args()

    retry_statuses = set(args.retry_status)
    status_by_url = queue_status_by_url(args.queue)
    rows = [
        row
        for row in load_manifest_rows(args.manifest)
        if row.get("main_m3u8_url")
        and row.get("source_url")
        and (not status_by_url.get(row.get("source_url", "")) or status_by_url.get(row.get("source_url", "")) in retry_statuses)
    ][: args.limit]

    model = None if args.dry_run or not rows else load_whisper_model(args.model, args.model_cache, args.deps_dir)
    args.output_log.parent.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    with args.output_log.open("a", encoding="utf-8", newline="\n") as log:
        for row in rows:
            try:
                result = process_row(args, row, model)
            except Exception as error:
                error_text = f"{type(error).__name__}: {error}"
                if "MemoryError" in error_text or "Unable to allocate" in error_text:
                    status = "failed_memory"
                elif "duration" in error_text:
                    status = "skipped_over_duration"
                elif "over limit" in error_text or "exceeded limit" in error_text:
                    status = "skipped_over_limit"
                else:
                    status = "failed"
                result = {
                    "media_id": media_id_for_lesson(row),
                    "queue_type": "academy_lesson",
                    "source_url": row.get("source_url"),
                    "title": row.get("lesson_title"),
                    "status": status,
                    "error": error_text,
                }
            result["logged_at"] = utc_now()
            results.append(result)
            log.write(json.dumps(result, ensure_ascii=True) + "\n")
            print(f"{result['status']}: {result['media_id']} ({result.get('segment_count', 0)} segment(s))")
            if result.get("error"):
                print(f"  {result['error']}")

    if not args.dry_run:
        update_queue_status(args.queue, results)
    print(f"Processed {len(results)} HLS lesson(s). Log: {args.output_log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
