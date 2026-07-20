#!/usr/bin/env python3
"""Backfill VTurb YouTube transcripts without invoking an LLM.

The runner is resumable and source-first. It preserves valid transcripts,
stages every new capture before promotion, normalizes content segments after a
successful capture, and records compact state/JSONL evidence outside the repo.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from collections import Counter
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from scripts.normalize_transcript import normalize_transcript


SCHEMA_VERSION = "1.0.0"
TERMINAL_OR_RESUMABLE_STATES = {
    "pending_direct",
    "pending_ui",
    "pending_chrome",
    "pending_asr",
    "failed",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=True, indent=2) + "\n").encode("utf-8")


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(json_bytes(payload))
    os.replace(temporary, path)


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as file:
        file.write(json.dumps(payload, ensure_ascii=True) + "\n")


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    return sorted(rows, key=lambda row: int(row.get("episode_priority") or 10**9))


def transcript_path(data_root: Path, video_id: str) -> Path:
    return data_root / "raw" / "youtube" / video_id / "transcript_original.json"


def metadata_path(data_root: Path, video_id: str) -> Path:
    return data_root / "raw" / "youtube" / video_id / "metadata.json"


def content_path(data_root: Path, video_id: str) -> Path:
    return data_root / "processed" / video_id / "content_segments.json"


def row_duration(row: dict[str, str], metadata: dict[str, Any] | None = None) -> float:
    value = (metadata or {}).get("duration_seconds") or row.get("duration_seconds") or 0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def validate_transcript_payload(
    payload: dict[str, Any],
    *,
    video_id: str,
    duration_seconds: float = 0,
    minimum_bytes: int = 50_000,
    minimum_coverage: float = 0.60,
    warning_coverage: float = 0.85,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if payload.get("youtube_video_id") != video_id:
        errors.append("youtube_video_id_mismatch")
    segments = payload.get("segments")
    if not isinstance(segments, list) or not segments:
        errors.append("segments_missing_or_empty")
        segments = []
    previous_start = -1.0
    last_timestamp = 0.0
    text_characters = 0
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            errors.append(f"segment_{index}_not_object")
            continue
        text = str(segment.get("text") or "").strip()
        if not text:
            errors.append(f"segment_{index}_text_empty")
        text_characters += len(text)
        try:
            start = float(segment.get("start_seconds"))
        except (TypeError, ValueError):
            errors.append(f"segment_{index}_start_invalid")
            continue
        if start < 0 or start < previous_start:
            errors.append(f"segment_{index}_order_invalid")
        previous_start = start
        duration = segment.get("duration_seconds")
        if duration is None:
            duration_value = 0.0
        else:
            try:
                duration_value = float(duration)
            except (TypeError, ValueError):
                errors.append(f"segment_{index}_duration_invalid")
                duration_value = 0.0
            if duration_value < 0:
                errors.append(f"segment_{index}_duration_negative")
        last_timestamp = max(last_timestamp, start + max(duration_value, 0.0))
    serialized = json_bytes(payload)
    if len(serialized) < minimum_bytes:
        errors.append(f"file_too_small:{len(serialized)}<{minimum_bytes}")
    language = str(payload.get("language") or "").strip()
    if not language:
        warnings.append("language_missing")
    coverage = (last_timestamp / duration_seconds) if duration_seconds > 0 else None
    if coverage is not None and coverage < minimum_coverage:
        errors.append(f"coverage_too_low:{coverage:.3f}<{minimum_coverage:.3f}")
    elif coverage is not None and coverage < warning_coverage:
        warnings.append(f"coverage_warning:{coverage:.3f}<{warning_coverage:.3f}")
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "segment_count": len(segments),
        "text_characters": text_characters,
        "bytes": len(serialized),
        "last_timestamp": round(last_timestamp, 3),
        "coverage": round(coverage, 4) if coverage is not None else None,
        "sha256": hashlib.sha256(serialized).hexdigest(),
        "provider": payload.get("provider"),
        "language": payload.get("language"),
    }


def validate_transcript_file(
    path: Path,
    *,
    video_id: str,
    duration_seconds: float,
    minimum_bytes: int,
    minimum_coverage: float,
) -> dict[str, Any]:
    if not path.is_file():
        return {"valid": False, "errors": ["file_missing"], "segment_count": 0, "bytes": 0}
    try:
        payload = read_json(path)
    except Exception as error:
        return {"valid": False, "errors": [f"invalid_json:{error}"], "segment_count": 0, "bytes": path.stat().st_size}
    return validate_transcript_payload(
        payload,
        video_id=video_id,
        duration_seconds=duration_seconds,
        minimum_bytes=minimum_bytes,
        minimum_coverage=minimum_coverage,
    )


def metadata_from_queue(row: dict[str, str]) -> dict[str, Any]:
    video_id = row["video_id"]
    published = row.get("published_time_text") or None
    return {
        "schema_version": "1.0",
        "source": row.get("channel_name") or "VTurb",
        "youtube_video_id": video_id,
        "url": row.get("youtube_url") or f"https://www.youtube.com/watch?v={video_id}",
        "title": row.get("title") or video_id,
        "channel_name": row.get("channel_name") or "VTurb",
        "channel_id": None,
        "description": None,
        "published_at": None,
        "duration_seconds": int(float(row.get("duration_seconds") or 0)) or None,
        "language_original": None,
        "collected_at": utc_now(),
        "processing_status": "pending",
        "transcript_status": "pending",
        "asset_detection_status": "pending",
        "notes": f"Metadata seeded from verified VTurb public catalog. Published label: {published or 'unknown'}",
    }


def load_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"schema_version": SCHEMA_VERSION, "kind": "vturb_transcript_backfill_state", "entries": {}}
    payload = read_json(path)
    if not isinstance(payload.get("entries"), dict):
        raise ValueError("backfill state entries must be an object")
    return payload


def load_mirror_receipt(path: Path | None) -> set[str]:
    """Return episodes that have a passed Windows-mirror reconciliation receipt.

    A valid transcript in the canonical acquisition root is intentionally not
    ``source_complete`` until its accessibility mirror has a terminal receipt.
    """
    if path is None:
        return set()
    payload = read_json(path)
    if payload.get("kind") != "transcript_root_reconciliation_receipt" or payload.get("status") != "passed":
        raise ValueError("mirror receipt is not a passed transcript-root reconciliation receipt")
    return {
        str(item["video_id"])
        for item in payload.get("terminal_results", [])
        if isinstance(item, dict) and item.get("status") in {"promoted", "idempotent"} and item.get("video_id")
    }


def acquisition_processing_status(video_id: str, mirror_verified_video_ids: set[str]) -> str:
    return "source_complete" if video_id in mirror_verified_video_ids else "mirror_pending"


def set_state_entry(state: dict[str, Any], video_id: str, **fields: Any) -> dict[str, Any]:
    entries = state.setdefault("entries", {})
    entry = dict(entries.get(video_id) or {})
    entry.update(fields)
    entry["video_id"] = video_id
    entry["updated_at"] = utc_now()
    entries[video_id] = entry
    state["updated_at"] = entry["updated_at"]
    return entry


def live_status(
    row: dict[str, str],
    data_root: Path,
    prior: dict[str, Any] | None,
    *,
    minimum_bytes: int,
    minimum_coverage: float,
) -> tuple[str, dict[str, Any]]:
    video_id = row["video_id"]
    metadata = None
    meta_path = metadata_path(data_root, video_id)
    if meta_path.is_file():
        try:
            metadata = read_json(meta_path)
        except Exception:
            metadata = None
    validation = validate_transcript_file(
        transcript_path(data_root, video_id),
        video_id=video_id,
        duration_seconds=row_duration(row, metadata),
        minimum_bytes=minimum_bytes,
        minimum_coverage=minimum_coverage,
    )
    if validation["valid"]:
        return "completed", validation
    if metadata is None:
        return "pending_metadata", validation
    prior_status = str((prior or {}).get("status") or "")
    if prior_status.startswith("running_"):
        interrupted_route = prior_status.removeprefix("running_")
        resumable_status = {
            "direct": "pending_direct",
            "ui": "pending_ui",
            "browser": "pending_chrome",
            "asr": "pending_asr",
        }.get(interrupted_route)
        if resumable_status:
            return resumable_status, validation
    if prior_status in TERMINAL_OR_RESUMABLE_STATES:
        return prior_status, validation
    transcript = None
    path = transcript_path(data_root, video_id)
    if path.is_file():
        try:
            transcript = read_json(path)
        except Exception:
            transcript = None
    provider = str((transcript or {}).get("provider") or "")
    if provider.startswith("missing:"):
        return "pending_ui", validation
    return "pending_direct", validation


def materialization_status(
    row: dict[str, Any],
    data_root: Path,
    validation: dict[str, Any],
) -> str:
    """Classify canonical artifacts independently from transcript acquisition."""
    video_id = row["video_id"]
    processed_dir = data_root / "processed" / video_id
    if (processed_dir / "gold_extraction").exists():
        return "protected_gold"
    if not validation.get("valid"):
        return "transcript_invalid"
    path = content_path(data_root, video_id)
    if not path.is_file():
        return "needs_materialization"
    try:
        content = read_json(path)
    except Exception:
        return "needs_materialization"
    if content.get("episode_video_id") != video_id or not isinstance(content.get("segments"), list) or not content["segments"]:
        return "needs_materialization"
    return "materialized"


def materialize_existing_transcript(
    row: dict[str, Any],
    validation: dict[str, Any],
    args: argparse.Namespace,
) -> str:
    """Promote a previously validated raw transcript without recapturing it."""
    status = materialization_status(row, args.data_root, validation)
    if status == "materialized":
        return "already_materialized"
    if status != "needs_materialization":
        return status
    video_id = row["video_id"]
    payload = read_json(transcript_path(args.data_root, video_id))
    normalized = normalize_transcript(payload)
    if not normalized.get("segments"):
        raise RuntimeError("normalized transcript has no segments")
    atomic_write_json(content_path(args.data_root, video_id), normalized)
    meta_path = metadata_path(args.data_root, video_id)
    metadata = read_json(meta_path) if meta_path.is_file() else metadata_from_queue(row)
    metadata.update({
        "transcript_status": "available",
        "processing_status": acquisition_processing_status(
            video_id,
            getattr(args, "mirror_verified_video_ids", set()),
        ),
        "language_original": payload.get("language"),
        "transcript_provider": payload.get("provider"),
        "transcript_sha256": validation["sha256"],
        "transcript_segments": validation["segment_count"],
        "transcript_last_timestamp": validation["last_timestamp"],
        "transcript_coverage": validation["coverage"],
    })
    atomic_write_json(meta_path, metadata)
    marker = args.data_root / "processed" / video_id / "transcript_fallback_needed.md"
    marker.unlink(missing_ok=True)
    return "materialized"


def build_inventory(
    rows: list[dict[str, str]],
    data_root: Path,
    state: dict[str, Any],
    *,
    minimum_bytes: int,
    minimum_coverage: float,
) -> list[dict[str, Any]]:
    inventory = []
    entries = state.get("entries", {})
    for row in rows:
        status, validation = live_status(
            row,
            data_root,
            entries.get(row["video_id"]),
            minimum_bytes=minimum_bytes,
            minimum_coverage=minimum_coverage,
        )
        inventory.append({
            **row,
            "status": status,
            "validation": validation,
            "materialization_status": materialization_status(row, data_root, validation),
            "duration_seconds_value": row_duration(row),
        })
    return inventory


def select_inventory(
    inventory: list[dict[str, Any]],
    *,
    start_priority: int | None,
    recent_limit: int | None,
    max_items: int | None,
    video_ids: set[str] | None = None,
    actionable_statuses: set[str] | None = None,
) -> list[dict[str, Any]]:
    selected = [item for item in inventory if item["status"] != "completed"]
    if video_ids:
        selected = [item for item in selected if item["video_id"] in video_ids]
    if actionable_statuses is not None:
        selected = [item for item in selected if item["status"] in actionable_statuses]
    if start_priority is not None:
        selected = [item for item in selected if int(item.get("episode_priority") or 0) >= start_priority]
    if recent_limit is not None:
        selected = sorted(selected, key=lambda item: int(item.get("discovered_order") or 10**9))[:recent_limit]
        selected.sort(key=lambda item: int(item.get("episode_priority") or 10**9))
    if max_items is not None:
        selected = selected[:max_items]
    return selected


def command_result(command: list[str], *, cwd: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "command failed")[-2000:]
        raise RuntimeError(f"exit={completed.returncode} {detail}")
    return completed


def error_class(message: str) -> str:
    lowered = message.lower()
    patterns = [
        ("path_mixed", ("exec format error", "npx.cmd", "windowsapps")),
        ("node_engine", ("requires node.js 20", "node.js 20 or higher")),
        ("cli_protocol", ("unknown command",)),
        ("browser_missing", ("distribution 'chrome' is not found", "executable doesn't exist")),
        ("system_library_missing", ("error while loading shared libraries", ".so: cannot open shared object file")),
        ("caption_empty", ("segments_missing_or_empty", "coverage_too_low")),
        ("timeout", ("timed out", "timeout")),
        ("file_missing", ("is missing", "file_missing", "no such file")),
    ]
    for label, needles in patterns:
        if any(needle in lowered for needle in needles):
            return label
    return "unclassified"


def timer_start() -> tuple[str, float]:
    return utc_now(), time.perf_counter()


def elapsed_ms(started_monotonic: float) -> float:
    return round((time.perf_counter() - started_monotonic) * 1000, 3)


def record_phase(
    args: argparse.Namespace,
    video_id: str,
    phase: str,
    started_at: str,
    started_monotonic: float,
    *,
    status: str = "completed",
    **fields: Any,
) -> None:
    record_event(
        args,
        video_id,
        "phase_finished",
        phase=phase,
        status=status,
        started_at=started_at,
        finished_at=utc_now(),
        duration_ms=elapsed_ms(started_monotonic),
        **fields,
    )


def probe_ui_capability(args: argparse.Namespace) -> dict[str, Any]:
    started_at, started = timer_start()
    command = [
        sys.executable,
        str(args.repo_root / "scripts" / "capture_youtube_transcript_with_playwright_cli.py"),
        "--preflight",
        "--timeout",
        str(args.ui_preflight_timeout),
    ]
    try:
        completed = command_result(command, cwd=args.repo_root, timeout=args.ui_preflight_timeout + 30)
        payload = json.loads(completed.stdout)
        if not isinstance(payload, dict):
            raise ValueError("UI capability output is not an object")
    except Exception as error:
        message = str(error)[-2000:]
        payload = {"available": False, "error_class": error_class(message), "error": message}
    record_phase(
        args,
        "__run__",
        "ui_capability_preflight",
        started_at,
        started,
        status="completed" if payload.get("available") else "unavailable",
        available=bool(payload.get("available")),
        error_class=payload.get("error_class"),
    )
    return payload


def stage_path(args: argparse.Namespace, video_id: str, route: str) -> Path:
    path = args.staging_root / video_id / f"{route}_transcript.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    return path


def run_direct(row: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    staged = stage_path(args, row["video_id"], "direct")
    command_result(
        [
            sys.executable,
            str(args.repo_root / "scripts" / "collect_youtube_transcript.py"),
            "--url",
            row["youtube_url"],
            "--output",
            str(staged),
        ],
        cwd=args.repo_root,
        timeout=args.direct_timeout,
    )
    return read_json(staged)


def run_ui(row: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    staged = stage_path(args, row["video_id"], "ui")
    command_result(
        [
            sys.executable,
            str(args.repo_root / "scripts" / "capture_youtube_transcript_with_playwright_cli.py"),
            "--url",
            row["youtube_url"],
            "--output",
            str(staged),
            "--session",
            args.playwright_session,
            "--snapshot-root",
            str(args.snapshot_root),
            "--timeout",
            str(args.playwright_timeout),
        ],
        cwd=args.repo_root,
        timeout=args.ui_process_timeout,
    )
    return read_json(staged)


def run_browser_import(row: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    if args.browser_checkpoint_dir is not None:
        source = args.browser_checkpoint_dir / "captures" / f"{row['video_id']}.json"
    elif args.browser_import_dir is not None:
        source = args.browser_import_dir / f"{row['video_id']}.json"
    else:
        raise RuntimeError("browser route requires --browser-checkpoint-dir or --browser-import-dir")
    if not source.is_file():
        raise FileNotFoundError(f"browser capture is missing: {source}")
    checkpoint = args.browser_checkpoint_results.get(row["video_id"]) if args.browser_checkpoint_dir else None
    if checkpoint:
        for phase, duration in (checkpoint.get("phases") or {}).items():
            record_event(
                args,
                row["video_id"],
                "phase_finished",
                phase=phase.removesuffix("_ms"),
                status="completed",
                started_at=None,
                finished_at=checkpoint.get("finished_at"),
                duration_ms=duration,
                cache_hit=False,
                bytes=checkpoint.get("bytes") if phase == "browser_serialize_ms" else None,
                segments=checkpoint.get("segment_count") if phase == "browser_serialize_ms" else None,
            )
    return read_json(source)


def load_browser_checkpoint_results(checkpoint_dir: Path | None) -> tuple[dict[str, dict[str, Any]], str | None]:
    if checkpoint_dir is None:
        return {}, None
    manifest_path = checkpoint_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"browser checkpoint manifest is missing: {manifest_path}")
    manifest = read_json(manifest_path)
    manifest_sha256 = str(manifest.get("manifest_sha256") or "")
    if not manifest_sha256:
        raise ValueError("browser checkpoint manifest_sha256 is missing")
    results: dict[str, dict[str, Any]] = {}
    result_root = checkpoint_dir / "results"
    for path in sorted(result_root.glob("*.json")) if result_root.is_dir() else []:
        result = read_json(path)
        video_id = str(result.get("video_id") or "")
        if not video_id or path.stem != video_id:
            continue
        if result.get("manifest_sha256") != manifest_sha256:
            continue
        if result.get("status") not in {"captured", "no_ui", "retryable", "failed"}:
            continue
        results[video_id] = result
    return results, manifest_sha256


def apply_browser_checkpoint_results(
    state: dict[str, Any],
    results: dict[str, dict[str, Any]],
    queue_video_ids: set[str],
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for video_id, result in results.items():
        if video_id not in queue_video_ids:
            continue
        checkpoint_status = str(result["status"])
        counts[checkpoint_status] += 1
        common = {
            "browser_checkpoint_status": checkpoint_status,
            "browser_checkpoint_finished_at": result.get("finished_at"),
            "browser_checkpoint_manifest_sha256": result.get("manifest_sha256"),
            "browser_checkpoint_phases": result.get("phases") or {},
        }
        if checkpoint_status == "no_ui":
            set_state_entry(
                state,
                video_id,
                status="pending_asr",
                chrome_real_confirmed_no_transcript_at=result.get("finished_at") or utc_now(),
                chrome_real_no_transcript_reason=result.get("reason"),
                **common,
            )
        elif checkpoint_status == "captured":
            set_state_entry(state, video_id, status="pending_chrome", **common)
        elif checkpoint_status == "failed":
            set_state_entry(
                state,
                video_id,
                status="pending_asr",
                chrome_real_confirmed_transcript_unusable_at=result.get("finished_at") or utc_now(),
                chrome_real_transcript_unusable_reason=result.get("reason"),
                **common,
            )
        else:
            set_state_entry(
                state,
                video_id,
                status="pending_chrome",
                last_error=result.get("reason"),
                **common,
            )
    return counts


def browser_capture_available(video_id: str, args: argparse.Namespace) -> bool:
    if args.browser_checkpoint_dir is not None:
        result = args.browser_checkpoint_results.get(video_id) or {}
        source = args.browser_checkpoint_dir / "captures" / f"{video_id}.json"
        return result.get("status") == "captured" and source.is_file()
    return args.browser_import_dir is not None and (args.browser_import_dir / f"{video_id}.json").is_file()


def existing_audio(media_root: Path, video_id: str) -> Path | None:
    candidates = [
        path for path in media_root.glob(f"{video_id}.*")
        if path.is_file() and not path.name.endswith((".part", ".ytdl"))
    ]
    return sorted(candidates, key=lambda path: path.stat().st_size, reverse=True)[0] if candidates else None


def _download_audio_uncached(row: dict[str, Any], args: argparse.Namespace) -> tuple[Path, bool]:
    media_dir = args.media_root / row["video_id"]
    media_dir.mkdir(parents=True, exist_ok=True)
    cached = existing_audio(media_dir, row["video_id"])
    if cached:
        return cached, True
    try:
        from yt_dlp import YoutubeDL
    except ImportError as error:
        raise RuntimeError("yt_dlp is required for ASR audio acquisition") from error
    options = {
        "format": "bestaudio/best",
        "outtmpl": str(media_dir / f"{row['video_id']}.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 3,
        "fragment_retries": 3,
        "socket_timeout": 30,
    }
    with YoutubeDL(options) as downloader:
        downloader.download([row["youtube_url"]])
    downloaded = existing_audio(media_dir, row["video_id"])
    if not downloaded:
        raise RuntimeError("yt_dlp completed without a usable audio file")
    return downloaded, False


def media_duration_seconds(path: Path) -> float:
    import av

    with av.open(str(path)) as container:
        if container.duration is not None:
            return max(float(container.duration / av.time_base), 0.0)
        durations = [
            float(stream.duration * stream.time_base)
            for stream in container.streams.audio
            if stream.duration is not None and stream.time_base is not None
        ]
    return max(durations, default=0.0)


def media_fingerprint(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"sha256": digest.hexdigest(), "bytes": path.stat().st_size}


def chunk_specs(duration: float, chunk_seconds: int, overlap_seconds: int) -> list[dict[str, Any]]:
    if duration <= 0 or chunk_seconds <= 0 or overlap_seconds < 0:
        raise ValueError("invalid ASR chunk configuration")
    specs = []
    nominal_start = 0.0
    index = 0
    while nominal_start < duration:
        nominal_end = min(nominal_start + chunk_seconds, duration)
        specs.append({
            "index": index,
            "nominal_start": round(nominal_start, 3),
            "nominal_end": round(nominal_end, 3),
            "clip_start": round(max(0.0, nominal_start - overlap_seconds), 3),
            "clip_end": round(min(duration, nominal_end + overlap_seconds), 3),
        })
        nominal_start = nominal_end
        index += 1
    return specs


def asr_config_key(args: argparse.Namespace) -> str:
    raw = f"{args.asr_model}|cpu|int8|batch={args.asr_batch_size}|{args.asr_chunk_seconds}|{args.asr_overlap_seconds}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def valid_chunk_receipt(
    receipt: dict[str, Any] | None,
    *,
    video_id: str,
    media_sha256: str,
    config_key: str,
    spec: dict[str, Any],
) -> bool:
    return bool(
        receipt
        and receipt.get("video_id") == video_id
        and receipt.get("media_sha256") == media_sha256
        and receipt.get("config_key") == config_key
        and receipt.get("chunk_index") == spec["index"]
        and receipt.get("nominal_start") == spec["nominal_start"]
        and receipt.get("nominal_end") == spec["nominal_end"]
        and isinstance(receipt.get("segments"), list)
        and receipt.get("status") == "completed"
    )


def _load_whisper_model(args: argparse.Namespace, video_id: str) -> None:
    if getattr(args, "_whisper_model", None) is not None:
        return
    started_at, started = timer_start()
    from faster_whisper import WhisperModel

    existed = args.model_cache.is_dir() and any(args.model_cache.iterdir())
    args.model_cache.mkdir(parents=True, exist_ok=True)
    args._whisper_model = WhisperModel(
        args.asr_model,
        device="cpu",
        compute_type="int8",
        download_root=str(args.model_cache),
    )
    if args.asr_batch_size:
        from faster_whisper import BatchedInferencePipeline

        args._batched_pipeline = BatchedInferencePipeline(args._whisper_model)
    record_phase(
        args,
        video_id,
        "model_load",
        started_at,
        started,
        cache_hit=existed,
        model=args.asr_model,
    )


def _assemble_chunk_segments(receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    assembled: list[dict[str, Any]] = []
    for receipt in receipts:
        start = float(receipt["nominal_start"])
        end = float(receipt["nominal_end"])
        final_chunk = bool(receipt.get("final_chunk"))
        for segment in receipt.get("segments") or []:
            segment_start = float(segment["start_seconds"])
            segment_end = segment_start + float(segment.get("duration_seconds") or 0)
            midpoint = segment_start + max(segment_end - segment_start, 0.0) / 2
            if midpoint < start or (midpoint >= end and not final_chunk):
                continue
            text = str(segment.get("text") or "").strip()
            if not text:
                continue
            # Whisper may re-segment the same overlap differently in adjacent
            # chunks. Keep midpoint ownership, but constrain timestamps to the
            # chunk's nominal window so the assembled timeline cannot move
            # backwards at a boundary.
            owned_start = max(segment_start, start)
            owned_end = min(segment_end, end)
            assembled.append({
                "index": len(assembled),
                "start_seconds": round(owned_start, 3),
                "duration_seconds": round(max(owned_end - owned_start, 0.0), 3),
                "text": text,
            })
    return assembled


def download_audio(row: dict[str, Any], args: argparse.Namespace) -> tuple[Path, bool, float]:
    started_at, started = timer_start()
    future = getattr(args, "_audio_futures", {}).pop(row["video_id"], None)
    if future is not None:
        path, cache_hit = future.result()
    else:
        path, cache_hit = _download_audio_uncached(row, args)
    duration = media_duration_seconds(path)
    record_phase(
        args,
        row["video_id"],
        "audio_download",
        started_at,
        started,
        cache_hit=cache_hit,
        bytes=path.stat().st_size,
        media_seconds=round(duration, 3),
    )
    return path, cache_hit, duration


def run_asr(row: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    media_path, _, duration = download_audio(row, args)
    fingerprint = media_fingerprint(media_path)
    _load_whisper_model(args, row["video_id"])
    if args.asr_clip_seconds:
        duration = min(duration, float(args.asr_clip_seconds))
        specs = chunk_specs(duration, int(args.asr_clip_seconds), 0)
    else:
        specs = chunk_specs(duration, args.asr_chunk_seconds, args.asr_overlap_seconds)
    config_key = asr_config_key(args)
    receipt_root = args.asr_checkpoint_root / row["video_id"] / config_key
    receipts: list[dict[str, Any]] = []
    language = None
    decoded_audio = None
    sampling_rate = 16_000
    if args.asr_batch_size:
        from faster_whisper.audio import decode_audio

        decode_started_at, decode_started = timer_start()
        decoded_audio = decode_audio(str(media_path), sampling_rate=sampling_rate)
        record_phase(
            args,
            row["video_id"],
            "audio_decode",
            decode_started_at,
            decode_started,
            cache_hit=False,
            bytes=int(decoded_audio.nbytes),
            media_seconds=round(len(decoded_audio) / sampling_rate, 3),
        )
    for spec in specs:
        receipt_path = receipt_root / f"chunk-{spec['index']:04d}.json"
        existing = read_json(receipt_path) if receipt_path.is_file() else None
        if valid_chunk_receipt(
            existing,
            video_id=row["video_id"],
            media_sha256=fingerprint["sha256"],
            config_key=config_key,
            spec=spec,
        ):
            receipt = existing
            record_event(
                args,
                row["video_id"],
                "asr_chunk_reused",
                phase="inference",
                chunk_index=spec["index"],
                cache_hit=True,
                media_seconds=round(spec["nominal_end"] - spec["nominal_start"], 3),
                segments=len(receipt.get("segments") or []),
            )
        else:
            started_at, started = timer_start()
            if args.asr_batch_size:
                clip_offset = float(spec["clip_start"])
                audio_slice = decoded_audio[
                    int(clip_offset * sampling_rate):int(float(spec["clip_end"]) * sampling_rate)
                ]
                segments_iter, info = args._batched_pipeline.transcribe(
                    audio_slice,
                    beam_size=1,
                    vad_filter=True,
                    without_timestamps=False,
                    batch_size=args.asr_batch_size,
                )
            else:
                clip_offset = 0.0
                segments_iter, info = args._whisper_model.transcribe(
                    str(media_path),
                    beam_size=1,
                    vad_filter=True,
                    clip_timestamps=f"{spec['clip_start']},{spec['clip_end']}",
                )
            segments = []
            for segment in segments_iter:
                text = str(segment.text or "").strip()
                if not text:
                    continue
                segment_start = round(float(segment.start) + clip_offset, 3)
                segment_end = round(float(segment.end) + clip_offset, 3)
                segments.append({
                    "start_seconds": segment_start,
                    "duration_seconds": round(max(segment_end - segment_start, 0.0), 3),
                    "text": text,
                })
            language = getattr(info, "language", None) or language
            inference_ms = elapsed_ms(started)
            media_seconds = round(spec["nominal_end"] - spec["nominal_start"], 3)
            receipt = {
                "schema_version": SCHEMA_VERSION,
                "kind": "vturb_asr_chunk_receipt",
                "status": "completed",
                "video_id": row["video_id"],
                "media_sha256": fingerprint["sha256"],
                "config_key": config_key,
                "model": args.asr_model,
                "batch_size": args.asr_batch_size,
                "chunk_index": spec["index"],
                "nominal_start": spec["nominal_start"],
                "nominal_end": spec["nominal_end"],
                "clip_start": spec["clip_start"],
                "clip_end": spec["clip_end"],
                "final_chunk": spec["index"] == len(specs) - 1,
                "language": language,
                "segments": segments,
                "inference_ms": inference_ms,
                "media_seconds": media_seconds,
                "completed_at": utc_now(),
            }
            atomic_write_json(receipt_path, receipt)
            record_phase(
                args,
                row["video_id"],
                "inference",
                started_at,
                started,
                cache_hit=False,
                chunk_index=spec["index"],
                media_seconds=media_seconds,
                segments=len(segments),
            )
            if media_seconds > 0:
                args._asr_rtfs.append((inference_ms / 1000) / media_seconds)
                args._asr_remaining_media_seconds = max(args._asr_remaining_media_seconds - media_seconds, 0.0)
                ordered = sorted(args._asr_rtfs)
                median_rtf = ordered[len(ordered) // 2]
                record_event(
                    args,
                    row["video_id"],
                    "asr_eta_updated",
                    chunk_index=spec["index"],
                    hot_rtf=round(median_rtf, 4),
                    remaining_media_seconds=round(args._asr_remaining_media_seconds, 3),
                    eta_seconds=round(args._asr_remaining_media_seconds * median_rtf, 1),
                )
        receipts.append(receipt)
        language = receipt.get("language") or language
    segments = _assemble_chunk_segments(receipts)
    return {
        "schema_version": "1.0",
        "youtube_video_id": row["video_id"],
        "source_kind": "transcript",
        "language": language,
        "provider": f"faster_whisper:{args.asr_model}:youtube_audio",
        "collected_at": utc_now(),
        "segments": segments,
    }


def promote_transcript(
    row: dict[str, Any],
    payload: dict[str, Any],
    validation: dict[str, Any],
    args: argparse.Namespace,
) -> None:
    video_id = row["video_id"]
    target = transcript_path(args.data_root, video_id)
    atomic_write_json(target, payload)
    normalized = normalize_transcript(payload)
    if len(normalized.get("segments", [])) != validation["segment_count"]:
        raise RuntimeError("normalized segment count does not match validated transcript")
    atomic_write_json(content_path(args.data_root, video_id), normalized)
    meta_path = metadata_path(args.data_root, video_id)
    metadata = read_json(meta_path) if meta_path.is_file() else metadata_from_queue(row)
    metadata.update({
        "transcript_status": "available",
        "processing_status": acquisition_processing_status(
            video_id,
            getattr(args, "mirror_verified_video_ids", set()),
        ),
        "language_original": payload.get("language"),
        "transcript_provider": payload.get("provider"),
        "transcript_sha256": validation["sha256"],
        "transcript_segments": validation["segment_count"],
        "transcript_last_timestamp": validation["last_timestamp"],
        "transcript_coverage": validation["coverage"],
    })
    atomic_write_json(meta_path, metadata)
    marker = args.data_root / "processed" / video_id / "transcript_fallback_needed.md"
    marker.unlink(missing_ok=True)


def route_validation(row: dict[str, Any], payload: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    metadata = None
    path = metadata_path(args.data_root, row["video_id"])
    if path.is_file():
        metadata = read_json(path)
    return validate_transcript_payload(
        payload,
        video_id=row["video_id"],
        duration_seconds=row_duration(row, metadata),
        minimum_bytes=args.minimum_bytes,
        minimum_coverage=args.minimum_coverage,
    )


def record_event(args: argparse.Namespace, video_id: str, event: str, **fields: Any) -> None:
    payload = {
        "logged_at": utc_now(),
        "run_id": getattr(args, "run_id", None),
        "video_id": video_id,
        "event": event,
        **fields,
    }
    lock = getattr(args, "_ledger_lock", None)
    if lock is None:
        append_jsonl(args.ledger, payload)
    else:
        with lock:
            append_jsonl(args.ledger, payload)


def increment_attempt(entry: dict[str, Any], route: str) -> None:
    attempts = dict(entry.get("attempts") or {})
    attempts[route] = int(attempts.get(route) or 0) + 1
    entry["attempts"] = attempts


def process_item(
    item: dict[str, Any],
    state: dict[str, Any],
    args: argparse.Namespace,
) -> str:
    video_id = item["video_id"]
    entry = set_state_entry(
        state,
        video_id,
        status=item["status"],
        category=item.get("category"),
        priority=int(item.get("episode_priority") or 0),
        title=item.get("title"),
    )
    routes = args.routes
    if item["status"] == "pending_metadata" and "metadata" in routes:
        phase_started_at, phase_started = timer_start()
        atomic_write_json(metadata_path(args.data_root, video_id), metadata_from_queue(item))
        entry = set_state_entry(state, video_id, status="pending_direct", last_route="metadata", last_error=None)
        record_event(args, video_id, "metadata_seeded")
        record_phase(args, video_id, "metadata", phase_started_at, phase_started)
        atomic_write_json(args.state, state)
    status, _ = live_status(
        item,
        args.data_root,
        entry,
        minimum_bytes=args.minimum_bytes,
        minimum_coverage=args.minimum_coverage,
    )
    if status == "completed":
        return "completed"

    attempted_routes: set[str] = set()
    while True:
        route: str | None = None
        runner: Any = None
        failure_status = status
        if (
            status in {"pending_direct", "pending_ui", "pending_chrome", "pending_asr"}
            and "browser" in routes
            and browser_capture_available(video_id, args)
            and "browser" not in attempted_routes
        ):
            route, runner, failure_status = "browser", run_browser_import, "pending_chrome"
        elif status == "pending_direct" and "direct" in routes and "direct" not in attempted_routes:
            route, runner, failure_status = "direct", run_direct, "pending_ui"
        elif status == "pending_ui" and "ui" in routes and "ui" not in attempted_routes:
            route, runner, failure_status = "ui", run_ui, "pending_chrome"
        elif status == "pending_chrome" and "ui" in routes and args.retry_ui and "ui" not in attempted_routes:
            route, runner, failure_status = "ui", run_ui, "pending_chrome"
        elif status == "pending_asr" and "asr" in routes and args.allow_asr and "asr" not in attempted_routes:
            route, runner, failure_status = "asr", run_asr, "failed"
        if route is None:
            break
        attempted_routes.add(route)
        entry = set_state_entry(state, video_id, status=f"running_{route}", last_route=route, last_error=None)
        increment_attempt(entry, route)
        attempt = entry["attempts"][route]
        attempt_id = f"{getattr(args, 'run_id', 'run')}:{video_id}:{route}:{attempt}"
        route_started_at, route_started = timer_start()
        record_event(
            args,
            video_id,
            "route_started",
            route=route,
            attempt=attempt,
            attempt_id=attempt_id,
            started_at=route_started_at,
        )
        atomic_write_json(args.state, state)
        try:
            route_phase_started_at, route_phase_started = timer_start()
            payload = runner(item, args)
            if route in {"direct", "ui"}:
                record_phase(
                    args,
                    video_id,
                    "direct" if route == "direct" else "transcript_panel",
                    route_phase_started_at,
                    route_phase_started,
                    route=route,
                    attempt_id=attempt_id,
                )
            validation_started_at, validation_started = timer_start()
            if route == "asr" and args.asr_clip_seconds:
                validation = validate_transcript_payload(
                    payload,
                    video_id=video_id,
                    duration_seconds=float(args.asr_clip_seconds),
                    minimum_bytes=1,
                    minimum_coverage=args.minimum_coverage,
                )
            else:
                validation = route_validation(item, payload, args)
            record_phase(
                args,
                video_id,
                "validation",
                validation_started_at,
                validation_started,
                route=route,
                attempt_id=attempt_id,
                segments=validation.get("segment_count"),
                coverage=validation.get("coverage"),
                bytes=validation.get("bytes"),
            )
            if not validation["valid"]:
                raise RuntimeError(";".join(validation["errors"]))
            if route == "asr" and args.asr_clip_seconds:
                set_state_entry(
                    state,
                    video_id,
                    status="pending_asr",
                    last_route=route,
                    last_error=None,
                    asr_pilot_validation=validation,
                    asr_pilot_completed_at=utc_now(),
                )
                record_event(
                    args,
                    video_id,
                    "asr_pilot_completed",
                    route=route,
                    attempt_id=attempt_id,
                    duration_ms=elapsed_ms(route_started),
                    validation=validation,
                )
                atomic_write_json(args.state, state)
                return "pending_asr"
            promotion_started_at, promotion_started = timer_start()
            promote_transcript(item, payload, validation, args)
            record_phase(
                args,
                video_id,
                "promotion",
                promotion_started_at,
                promotion_started,
                route=route,
                attempt_id=attempt_id,
                segments=validation.get("segment_count"),
                bytes=validation.get("bytes"),
            )
            set_state_entry(
                state,
                video_id,
                status="completed",
                last_route=route,
                last_error=None,
                validation=validation,
                completed_at=utc_now(),
            )
            record_event(
                args,
                video_id,
                "completed",
                route=route,
                attempt_id=attempt_id,
                duration_ms=elapsed_ms(route_started),
                validation=validation,
            )
            atomic_write_json(args.state, state)
            return "completed"
        except Exception as error:
            message = str(error)[-2000:]
            set_state_entry(state, video_id, status=failure_status, last_route=route, last_error=message)
            record_event(
                args,
                video_id,
                "route_failed",
                route=route,
                attempt_id=attempt_id,
                duration_ms=elapsed_ms(route_started),
                next_status=failure_status,
                error_class=error_class(message),
                error=message,
            )
            atomic_write_json(args.state, state)
            status = failure_status
            continue
    set_state_entry(state, video_id, status=status)
    atomic_write_json(args.state, state)
    return status


def summary_payload(
    inventory: list[dict[str, Any]],
    *,
    selected: list[dict[str, Any]] | None = None,
    outcomes: Counter[str] | None = None,
) -> dict[str, Any]:
    status_counts = Counter(item["status"] for item in inventory)
    materialization_counts = Counter(item.get("materialization_status") or "unknown" for item in inventory)
    pending_by_category = Counter(
        item.get("category") or "unknown" for item in inventory if item["status"] != "completed"
    )
    missing_duration = sum(
        float(item.get("duration_seconds_value") or 0)
        for item in inventory
        if item["status"] != "completed"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "vturb_transcript_backfill_summary",
        "generated_at": utc_now(),
        "total_videos": len(inventory),
        "valid_transcripts": status_counts.get("completed", 0),
        "pending_transcripts": len(inventory) - status_counts.get("completed", 0),
        "status_counts": dict(status_counts),
        "materialization_counts": dict(materialization_counts),
        "pending_by_category": dict(pending_by_category),
        "pending_duration_hours": round(missing_duration / 3600, 2),
        "selected_items": len(selected or []),
        "run_outcomes": dict(outcomes or {}),
    }


@contextmanager
def exclusive_lock(path: Path, *, stale_seconds: int = 21_600) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        stale_by_age = time.time() - path.stat().st_mtime > stale_seconds
        owner_is_dead = False
        try:
            owner_pid = int(read_json(path).get("pid") or 0)
            if owner_pid > 0:
                os.kill(owner_pid, 0)
        except ProcessLookupError:
            owner_is_dead = True
        except (ValueError, OSError, json.JSONDecodeError):
            pass
        if stale_by_age or owner_is_dead:
            path.unlink()
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        raise RuntimeError(f"backfill lock already exists: {path}") from error
    try:
        os.write(descriptor, json.dumps({"pid": os.getpid(), "started_at": utc_now()}).encode("utf-8"))
        os.close(descriptor)
        yield
    finally:
        path.unlink(missing_ok=True)


def rebuild_gold(args: argparse.Namespace) -> None:
    if not (args.gold_json_output and args.gold_markdown_output):
        raise ValueError("--rebuild-gold requires --gold-json-output and --gold-markdown-output")
    started_at, started = timer_start()
    command_result(
        [
            sys.executable,
            "-m",
            "scripts.gold_episode_priority",
            "--data-root",
            str(args.data_root),
            "--catalog-csv",
            str(args.catalog),
            "--json-output",
            str(args.gold_json_output),
            "--markdown-output",
            str(args.gold_markdown_output),
        ],
        cwd=args.repo_root,
        timeout=args.gold_timeout,
    )
    record_phase(args, "__run__", "gold_rebuild", started_at, started)


def parse_routes(value: str) -> set[str]:
    routes = {item.strip() for item in value.split(",") if item.strip()}
    invalid = routes - {"metadata", "direct", "ui", "browser", "asr"}
    if invalid:
        raise argparse.ArgumentTypeError(f"invalid routes: {sorted(invalid)}")
    return routes


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--catalog", default=repo_root / "docs" / "coordination" / "vturb-public-video-catalog.csv", type=Path)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--inventory-output", type=Path)
    parser.add_argument("--staging-root", type=Path)
    parser.add_argument("--snapshot-root", type=Path)
    parser.add_argument("--media-root", type=Path)
    parser.add_argument("--model-cache", type=Path)
    parser.add_argument("--browser-import-dir", type=Path)
    parser.add_argument("--browser-checkpoint-dir", type=Path)
    parser.add_argument("--routes", default="metadata,direct,ui", type=parse_routes)
    parser.add_argument("--video-id", action="append", default=[])
    parser.add_argument("--max-items", type=int)
    parser.add_argument("--start-priority", type=int)
    parser.add_argument("--recent-limit", type=int)
    parser.add_argument("--status-only", action="store_true")
    parser.add_argument("--materialize-ready", action="store_true", help="Materialize content_segments only from already valid raw transcripts.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--retry-ui", action="store_true")
    parser.add_argument("--mark-no-ui", action="append", default=[])
    parser.add_argument("--allow-asr", action="store_true")
    parser.add_argument("--asr-model", default="large-v3-turbo")
    parser.add_argument("--asr-batch-size", default=0, type=int)
    parser.add_argument("--asr-clip-seconds", type=int)
    parser.add_argument("--asr-chunk-seconds", default=1200, type=int)
    parser.add_argument("--asr-overlap-seconds", default=2, type=int)
    parser.add_argument("--asr-checkpoint-root", type=Path)
    parser.add_argument("--no-prefetch-audio", action="store_true")
    parser.add_argument("--minimum-bytes", default=50_000, type=int)
    parser.add_argument("--minimum-coverage", default=0.60, type=float)
    parser.add_argument("--playwright-session", default="msf-transcript-backfill")
    parser.add_argument("--playwright-timeout", default=120, type=int)
    parser.add_argument("--ui-process-timeout", default=240, type=int)
    parser.add_argument("--ui-preflight-timeout", default=45, type=int)
    parser.add_argument("--skip-ui-preflight", action="store_true")
    parser.add_argument("--direct-timeout", default=60, type=int)
    parser.add_argument("--rebuild-gold", action="store_true")
    parser.add_argument("--gold-json-output", type=Path)
    parser.add_argument("--gold-markdown-output", type=Path)
    parser.add_argument("--gold-timeout", default=120, type=int)
    parser.add_argument("--mirror-receipt", type=Path, help="Passed reconciliation receipt required before new acquisitions become source_complete.")
    args = parser.parse_args()
    args.repo_root = repo_root
    args.queue = args.queue or args.data_root / "input" / "youtube_urls.csv"
    args.state = args.state or args.data_root / "input" / "vturb_transcript_backfill_state.json"
    args.ledger = args.ledger or args.data_root / "logs" / "vturb_transcript_backfill.jsonl"
    args.summary = args.summary or args.data_root / "exports" / "vturb_transcript_backfill_summary.json"
    args.staging_root = args.staging_root or args.data_root / "cache" / "vturb_transcript_backfill" / "staging"
    args.snapshot_root = args.snapshot_root or args.data_root / "cache" / "vturb_transcript_backfill" / "playwright"
    args.media_root = args.media_root or args.data_root / "cache" / "vturb_transcript_backfill" / "audio"
    args.model_cache = args.model_cache or args.data_root / "cache" / "faster_whisper"
    args.asr_checkpoint_root = args.asr_checkpoint_root or args.data_root / "cache" / "vturb_transcript_backfill" / "asr-checkpoints"
    args.lock = args.state.with_suffix(".lock")
    args.run_id = uuid.uuid4().hex
    args._ledger_lock = threading.Lock()
    args.routes_requested = set(args.routes)
    args.ui_capability = None
    args._audio_futures = {}
    args._prefetched_video_ids = set()
    args._asr_rtfs = []
    args._asr_remaining_media_seconds = 0.0
    args.mirror_verified_video_ids = load_mirror_receipt(args.mirror_receipt)
    if args.asr_chunk_seconds <= 0 or args.asr_overlap_seconds < 0 or args.asr_batch_size < 0:
        parser.error("ASR chunk and batch sizes must be non-negative, with positive chunk seconds")

    rows = csv_rows(args.queue)
    queue_video_ids = {row["video_id"] for row in rows}
    unknown_video_ids = sorted(set(args.video_id) - queue_video_ids)
    if unknown_video_ids:
        parser.error(f"--video-id is not in queue: {', '.join(unknown_video_ids)}")
    state = load_state(args.state)
    args.browser_checkpoint_results, args.browser_manifest_sha256 = load_browser_checkpoint_results(
        args.browser_checkpoint_dir
    )
    checkpoint_counts = apply_browser_checkpoint_results(
        state, args.browser_checkpoint_results, queue_video_ids
    )
    for video_id in args.mark_no_ui:
        if video_id not in queue_video_ids:
            parser.error(f"--mark-no-ui id is not in queue: {video_id}")
        set_state_entry(state, video_id, status="pending_asr", chrome_real_confirmed_no_transcript_at=utc_now())
    inventory_started_at, inventory_started = timer_start()
    inventory = build_inventory(
        rows,
        args.data_root,
        state,
        minimum_bytes=args.minimum_bytes,
        minimum_coverage=args.minimum_coverage,
    )
    if not (args.status_only or args.dry_run):
        record_phase(
            args,
            "__run__",
            "inventory",
            inventory_started_at,
            inventory_started,
            total_videos=len(inventory),
            queue_sha256=hashlib.sha256(args.queue.read_bytes()).hexdigest(),
        )
        if "ui" in args.routes and not args.skip_ui_preflight:
            args.ui_capability = probe_ui_capability(args)
            if not args.ui_capability.get("available"):
                args.routes.discard("ui")
                record_event(
                    args,
                    "__run__",
                    "circuit_breaker_opened",
                    route="ui",
                    error_class=args.ui_capability.get("error_class"),
                    error=args.ui_capability.get("error"),
                )
    actionable_statuses: set[str] = set()
    if "metadata" in args.routes:
        actionable_statuses.add("pending_metadata")
    if "direct" in args.routes:
        actionable_statuses.add("pending_direct")
    if "ui" in args.routes:
        actionable_statuses.add("pending_ui")
        if args.retry_ui:
            actionable_statuses.add("pending_chrome")
    if "browser" in args.routes:
        actionable_statuses.update({"pending_metadata", "pending_direct", "pending_ui", "pending_chrome", "pending_asr"})
    if "asr" in args.routes and args.allow_asr:
        actionable_statuses.add("pending_asr")
    selected = select_inventory(
        inventory,
        start_priority=args.start_priority,
        recent_limit=args.recent_limit,
        max_items=args.max_items,
        video_ids=set(args.video_id) or None,
        actionable_statuses=actionable_statuses,
    )
    args._asr_remaining_media_seconds = sum(
        float(item.get("duration_seconds_value") or 0)
        for item in selected
        if item.get("status") == "pending_asr"
    )
    initial_summary = summary_payload(inventory, selected=selected)
    initial_summary.update({
        "run_id": args.run_id,
        "routes_requested": sorted(args.routes_requested),
        "routes_active": sorted(args.routes),
        "ui_capability": args.ui_capability,
        "browser_checkpoint_counts": dict(checkpoint_counts),
        "browser_manifest_sha256": args.browser_manifest_sha256,
    })
    if args.inventory_output:
        atomic_write_json(args.inventory_output, {
            "schema_version": SCHEMA_VERSION,
            "kind": "vturb_transcript_backfill_inventory",
            "generated_at": utc_now(),
            "items": [
                {
                    "video_id": item["video_id"],
                    "youtube_url": item["youtube_url"],
                    "title": item.get("title"),
                    "duration_seconds": item.get("duration_seconds_value"),
                    "category": item.get("category"),
                    "episode_priority": int(item.get("episode_priority") or 0),
                    "status": item["status"],
                    "materialization_status": item.get("materialization_status"),
                    "validation": item.get("validation"),
                }
                for item in inventory
            ],
        })
    if args.status_only or args.dry_run:
        print(json.dumps(initial_summary, ensure_ascii=False, indent=2))
        if args.dry_run:
            print(json.dumps({"selected": [{"video_id": item["video_id"], "status": item["status"]} for item in selected]}, ensure_ascii=False, indent=2))
        return 0

    if args.materialize_ready:
        outcomes: Counter[str] = Counter()
        with exclusive_lock(args.lock):
            for item in inventory:
                try:
                    outcome = materialize_existing_transcript(item, item["validation"], args)
                except Exception as error:
                    outcome = "materialization_failed"
                    record_event(args, item["video_id"], "materialization_failed", error=str(error)[-2000:])
                outcomes[outcome] += 1
            final_inventory = build_inventory(
                rows,
                args.data_root,
                state,
                minimum_bytes=args.minimum_bytes,
                minimum_coverage=args.minimum_coverage,
            )
            summary = summary_payload(final_inventory, selected=[], outcomes=outcomes)
            summary.update({"run_id": args.run_id, "materialize_ready": True})
            atomic_write_json(args.summary, summary)
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    outcomes: Counter[str] = Counter()
    with exclusive_lock(args.lock):
        atomic_write_json(args.state, state)
        executor = None if args.no_prefetch_audio or not ("asr" in args.routes and args.allow_asr) else ThreadPoolExecutor(max_workers=1)
        try:
            for index, item in enumerate(selected):
                if executor is not None:
                    for candidate in selected[index:index + 2]:
                        if candidate.get("status") == "pending_asr" and candidate["video_id"] not in args._prefetched_video_ids:
                            args._audio_futures[candidate["video_id"]] = executor.submit(_download_audio_uncached, candidate, args)
                            args._prefetched_video_ids.add(candidate["video_id"])
                try:
                    outcome = process_item(item, state, args)
                except Exception as error:
                    outcome = "failed"
                    set_state_entry(state, item["video_id"], status="failed", last_error=str(error)[-2000:])
                    record_event(
                        args,
                        item["video_id"],
                        "item_failed",
                        error_class=error_class(str(error)),
                        error=str(error)[-2000:],
                    )
                    atomic_write_json(args.state, state)
                outcomes[outcome] += 1
        finally:
            if executor is not None:
                executor.shutdown(wait=True, cancel_futures=True)
        final_inventory = build_inventory(
            rows,
            args.data_root,
            state,
            minimum_bytes=args.minimum_bytes,
            minimum_coverage=args.minimum_coverage,
        )
        summary = summary_payload(final_inventory, selected=selected, outcomes=outcomes)
        summary.update({
            "run_id": args.run_id,
            "routes_requested": sorted(args.routes_requested),
            "routes_active": sorted(args.routes),
            "ui_capability": args.ui_capability,
            "browser_checkpoint_counts": dict(checkpoint_counts),
            "browser_manifest_sha256": args.browser_manifest_sha256,
            "asr_hot_rtf_samples": len(args._asr_rtfs),
        })
        atomic_write_json(args.summary, summary)
        if args.rebuild_gold and outcomes.get("completed", 0):
            rebuild_gold(args)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
