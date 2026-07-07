#!/usr/bin/env python
"""Download and transcribe VTurb Academy video queue items."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from msf_common import slugify, write_json


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def add_transcription_deps(deps_dir: Path) -> None:
    if deps_dir.exists():
        sys.path.insert(0, str(deps_dir.resolve()))


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def drive_file_id(url: str, fallback: str | None = None) -> str | None:
    patterns = [
        r"/file/d/([^/]+)",
        r"[?&]id=([^&]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return urllib.parse.unquote(match.group(1))
    return fallback or None


def media_id_for(row: dict[str, str]) -> str:
    raw_id = row.get("candidate_video_id") or drive_file_id(row.get("source_url", "")) or row.get("source_url", "")
    safe = re.sub(r"[^A-Za-z0-9_-]+", "", raw_id)[:40] or slugify(row.get("candidate_title") or row.get("lesson_title"), 40)
    return f"academyvid-{safe}"


def filename_for(row: dict[str, str], media_id: str) -> str:
    title = row.get("candidate_title") or row.get("lesson_title") or media_id
    suffix = Path(title).suffix.lower()
    if suffix not in {".mp4", ".mov", ".m4v", ".webm", ".mp3", ".m4a", ".wav"}:
        suffix = ".mp4"
    return f"{media_id}__{slugify(title, 80)}{suffix}"


def google_uc_url(file_id: str) -> str:
    return f"https://drive.google.com/uc?export=download&id={urllib.parse.quote(file_id)}"


def confirm_url_from_html(html_text: str, file_id: str) -> str | None:
    match = re.search(r'href="([^"]*confirm=[^"]*)"', html_text)
    if match:
        return "https://drive.google.com" + html.unescape(match.group(1))
    match = re.search(r"confirm=([0-9A-Za-z_]+)", html_text)
    if match:
        return f"{google_uc_url(file_id)}&confirm={match.group(1)}"
    form = re.search(r'<form[^>]*action="([^"]+)"[^>]*>(.*?)</form>', html_text, re.IGNORECASE | re.DOTALL)
    if form:
        action = html.unescape(form.group(1))
        params = dict(re.findall(r'name="([^"]+)"\s+value="([^"]*)"', form.group(2)))
        if params:
            query = urllib.parse.urlencode({html.unescape(k): html.unescape(v) for k, v in params.items()})
            separator = "&" if "?" in action else "?"
            return f"{action}{separator}{query}"
    return None


def download_url(url: str, output_path: Path, max_bytes: int | None = None) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=180) as response:
        content_type = response.headers.get("content-type", "")
        content_length = response.headers.get("content-length")
        if max_bytes and content_length and int(content_length) > max_bytes:
            raise RuntimeError(f"remote file is {content_length} bytes, over limit {max_bytes}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        total = 0
        with output_path.open("wb") as file:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if max_bytes and total > max_bytes:
                    file.close()
                    output_path.unlink(missing_ok=True)
                    raise RuntimeError(f"download exceeded limit {max_bytes} bytes")
                file.write(chunk)
    return total, content_type


def download_drive_file(file_id: str, output_path: Path, max_bytes: int | None = None) -> tuple[int, str, str]:
    first_url = google_uc_url(file_id)
    request = urllib.request.Request(first_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=180) as response:
        content_type = response.headers.get("content-type", "")
        prefix = response.read(65536)
        if "text/html" in content_type.lower():
            html_text = prefix.decode("utf-8", errors="replace") + response.read(512000).decode("utf-8", errors="replace")
            confirm_url = confirm_url_from_html(html_text, file_id)
            if not confirm_url:
                raise RuntimeError("Drive returned HTML and no confirm URL was found")
            size, final_type = download_url(confirm_url, output_path, max_bytes=max_bytes)
            return size, final_type, confirm_url

        content_length = response.headers.get("content-length")
        if max_bytes and content_length and int(content_length) > max_bytes:
            raise RuntimeError(f"remote file is {content_length} bytes, over limit {max_bytes}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        total = len(prefix)
        with output_path.open("wb") as file:
            file.write(prefix)
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if max_bytes and total > max_bytes:
                    file.close()
                    output_path.unlink(missing_ok=True)
                    raise RuntimeError(f"download exceeded limit {max_bytes} bytes")
                file.write(chunk)
    return total, content_type, first_url


def load_whisper_model(model_name: str, download_root: Path, deps_dir: Path):
    add_transcription_deps(deps_dir)
    from faster_whisper import WhisperModel

    download_root.mkdir(parents=True, exist_ok=True)
    return WhisperModel(model_name, device="cpu", compute_type="int8", download_root=str(download_root))


def transcribe_media(model: Any, media_path: Path, model_name: str) -> dict[str, Any]:
    segments_iter, info = model.transcribe(str(media_path), beam_size=1, vad_filter=True)
    segments = []
    for index, segment in enumerate(segments_iter):
        start = round(float(segment.start), 3)
        end = round(float(segment.end), 3)
        text = str(segment.text or "").strip()
        if not text:
            continue
        segments.append(
            {
                "index": index,
                "start_seconds": start,
                "duration_seconds": round(max(end - start, 0.0), 3),
                "text": text,
            }
        )
    return {
        "language": getattr(info, "language", None),
        "language_probability": getattr(info, "language_probability", None),
        "duration_seconds": round(float(getattr(info, "duration", 0.0) or 0.0)),
        "provider": f"faster_whisper:{model_name}",
        "segments": segments,
    }


def write_episode_metadata(media_id: str, row: dict[str, str], media_info: dict[str, Any], raw_dir: Path) -> None:
    title = row.get("candidate_title") or row.get("lesson_title") or media_id
    payload = {
        "schema_version": "1.0",
        "source": "VTurb Academy",
        "youtube_video_id": media_id,
        "url": row.get("source_url") or row.get("candidate_youtube_url") or "https://app.vturb.com/academy",
        "title": title,
        "channel_name": row.get("course") or "VTurb Academy",
        "channel_id": None,
        "description": json.dumps(row, ensure_ascii=True),
        "published_at": None,
        "duration_seconds": media_info.get("duration_seconds"),
        "language_original": media_info.get("language"),
        "collected_at": utc_now(),
        "processing_status": "processing",
        "transcript_status": "available" if media_info.get("segments") else "missing",
        "asset_detection_status": "pending",
        "notes": "Synthetic local metadata for a VTurb Academy video transcription.",
    }
    write_json(raw_dir / "metadata.json", payload)


def write_transcript(media_id: str, media_info: dict[str, Any], raw_dir: Path) -> None:
    payload = {
        "schema_version": "1.0",
        "youtube_video_id": media_id,
        "source_kind": "transcript",
        "language": media_info.get("language"),
        "provider": media_info.get("provider"),
        "collected_at": utc_now(),
        "segments": media_info.get("segments", []),
    }
    write_json(raw_dir / "transcript_original.json", payload)


def run_command(command: list[str]) -> None:
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr or completed.stdout)


def run_post_pipeline(media_id: str, raw_dir: Path, processed_dir: Path, max_chars: int) -> None:
    run_command(
        [
            sys.executable,
            "scripts/normalize_transcript.py",
            "--input",
            str(raw_dir / "transcript_original.json"),
            "--output",
            str(processed_dir / "content_segments.json"),
        ]
    )
    run_command(
        [
            sys.executable,
            "scripts/create_extraction_chunks.py",
            "--segments",
            str(processed_dir / "content_segments.json"),
            "--metadata",
            str(raw_dir / "metadata.json"),
            "--output-dir",
            str(processed_dir / "chunks"),
            "--max-chars",
            str(max_chars),
        ]
    )
    run_command(
        [
            sys.executable,
            "scripts/detect_assets.py",
            "--metadata",
            str(raw_dir / "metadata.json"),
            "--segments",
            str(processed_dir / "content_segments.json"),
            "--output-dir",
            str(processed_dir),
        ]
    )
    run_command([sys.executable, "scripts/generate_summaries.py", "--episode", media_id])


def process_row(args: argparse.Namespace, row: dict[str, str], model: Any | None) -> dict[str, Any]:
    media_id = media_id_for(row)
    raw_dir = args.raw_root / media_id
    processed_dir = args.processed_root / media_id
    transcript_path = raw_dir / "transcript_original.json"
    media_filename = filename_for(row, media_id)
    media_path = args.media_root / media_id / media_filename
    result = {
        "media_id": media_id,
        "queue_type": row.get("queue_type"),
        "source_url": row.get("source_url"),
        "title": row.get("candidate_title") or row.get("lesson_title"),
        "status": "pending",
    }

    if transcript_path.exists() and not args.force:
        result["status"] = "skipped_existing_transcript"
        return result

    if args.dry_run:
        result["status"] = "dry_run"
        return result

    if not media_path.exists() or args.force_download:
        file_id = drive_file_id(row.get("source_url", ""), row.get("candidate_video_id"))
        if not file_id:
            raise RuntimeError("no Drive file id found")
        size, content_type, final_url = download_drive_file(file_id, media_path, max_bytes=args.max_download_mb * 1024 * 1024)
        result.update({"downloaded_bytes": size, "content_type": content_type, "download_url": final_url})
    else:
        result.update({"downloaded_bytes": media_path.stat().st_size, "content_type": "existing"})

    if model is None:
        raise RuntimeError("transcription model was not loaded")
    media_info = transcribe_media(model, media_path, args.model)
    write_episode_metadata(media_id, row, media_info, raw_dir)
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


def update_queue_status(queue_path: Path, results: list[dict[str, Any]]) -> None:
    if not results:
        return
    rows = csv_rows(queue_path)
    by_source = {result.get("source_url"): result for result in results}
    fieldnames = list(rows[0].keys()) if rows else []
    for extra in ["transcription_media_id", "transcription_status", "transcription_segments", "transcription_updated_at"]:
        if extra not in fieldnames:
            fieldnames.append(extra)
    for row in rows:
        result = by_source.get(row.get("source_url"))
        if not result:
            continue
        row["transcription_media_id"] = str(result.get("media_id") or "")
        row["transcription_status"] = str(result.get("status") or "")
        row["transcription_segments"] = str(result.get("segment_count") or "")
        row["transcription_updated_at"] = utc_now()
    with queue_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", default=Path("data/input/academy_video_transcription_queue.csv"), type=Path)
    parser.add_argument("--queue-type", default="drive_video_asset")
    parser.add_argument("--status", default="needs_download_audio_extraction")
    parser.add_argument("--limit", default=5, type=int)
    parser.add_argument("--max-download-mb", default=8, type=int)
    parser.add_argument("--model", default="tiny")
    parser.add_argument("--deps-dir", default=Path(".codex_deps/transcription"), type=Path)
    parser.add_argument("--model-cache", default=Path("data/cache/faster_whisper"), type=Path)
    parser.add_argument("--media-root", default=Path("data/raw/academy_media"), type=Path)
    parser.add_argument("--raw-root", default=Path("data/raw/youtube"), type=Path)
    parser.add_argument("--processed-root", default=Path("data/processed"), type=Path)
    parser.add_argument("--output-log", default=Path("data/logs/academy_video_transcription_results.jsonl"), type=Path)
    parser.add_argument("--max-chars", default=50000, type=int)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--retry-status", action="append", default=[])
    args = parser.parse_args()
    retry_statuses = set(args.retry_status)

    rows = [
        row
        for row in csv_rows(args.queue)
        if row.get("queue_type") == args.queue_type
        and row.get("status") == args.status
        and row.get("source_url")
        and (not row.get("transcription_status") or row.get("transcription_status") in retry_statuses)
    ][: args.limit]

    model = None if args.dry_run or not rows else load_whisper_model(args.model, args.model_cache, args.deps_dir)
    args.output_log.parent.mkdir(parents=True, exist_ok=True)
    results = []
    with args.output_log.open("a", encoding="utf-8", newline="\n") as log:
        for row in rows:
            try:
                result = process_row(args, row, model)
            except Exception as error:
                error_text = f"{type(error).__name__}: {error}"
                status = "skipped_over_limit" if "over limit" in error_text or "exceeded limit" in error_text else "failed"
                result = {
                    "media_id": media_id_for(row),
                    "queue_type": row.get("queue_type"),
                    "source_url": row.get("source_url"),
                    "title": row.get("candidate_title") or row.get("lesson_title"),
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
    print(f"Processed {len(results)} queue item(s). Log: {args.output_log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
