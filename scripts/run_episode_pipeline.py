#!/usr/bin/env python
"""Run the deterministic local episode pipeline and write JSONL logs."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from msf_common import load_json, write_json, write_text
from youtube_common import extract_video_id


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class PipelineLogger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def event(self, **payload: Any) -> None:
        payload.setdefault("logged_at", utc_now())
        with self.path.open("a", encoding="utf-8", newline="\n") as file:
            file.write(json.dumps(payload, ensure_ascii=True) + "\n")


def run_step(logger: PipelineLogger, video_id: str, step: str, command: list[str]) -> subprocess.CompletedProcess[str]:
    logger.event(video_id=video_id, step=step, status="started", command=command)
    completed = subprocess.run(command, text=True, capture_output=True)
    logger.event(
        video_id=video_id,
        step=step,
        status="passed" if completed.returncode == 0 else "failed",
        returncode=completed.returncode,
        stdout=completed.stdout[-4000:],
        stderr=completed.stderr[-4000:],
    )
    if completed.returncode != 0:
        raise RuntimeError(f"{step} failed for {video_id}: {completed.stderr or completed.stdout}")
    return completed


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def video_inputs(args: argparse.Namespace) -> list[dict[str, str | None]]:
    if args.csv:
        rows = []
        for row in csv_rows(args.csv):
            url = (row.get("youtube_url") or "").strip()
            if not url or "REPLACE_WITH_REAL" in url:
                continue
            rows.append({"url": url, "video_id": extract_video_id(url)})
        return rows
    if args.url:
        return [{"url": args.url, "video_id": extract_video_id(args.url)}]
    if args.video_id:
        return [{"url": None, "video_id": args.video_id}]
    raise ValueError("Provide --url, --csv, or --video-id")


def transcript_has_segments(path: Path) -> bool:
    if not path.exists():
        return False
    payload = load_json(path)
    return bool(payload.get("segments"))


def update_metadata_status(metadata_path: Path, **fields: Any) -> None:
    if not metadata_path.exists():
        return
    metadata = load_json(metadata_path)
    metadata.update(fields)
    write_json(metadata_path, metadata)


def write_fallback_note(video_id: str, processed_dir: Path) -> None:
    note = "\n".join(
        [
            f"# Transcript Fallback Needed - {video_id}",
            "",
            "The direct YouTube caption endpoint returned no transcript segments.",
            "",
            "Use the Playwright UI transcript fallback documented in docs/marketing-swipe-file-handoff.md.",
            "After saving transcript_original.json, rerun this pipeline with --video-id and --skip-metadata --skip-transcript.",
            "",
        ]
    )
    write_text(processed_dir / "transcript_fallback_needed.md", note)


def run_for_video(args: argparse.Namespace, logger: PipelineLogger, item: dict[str, str | None]) -> None:
    video_id = str(item["video_id"])
    url = item.get("url")
    raw_dir = args.raw_youtube_root / video_id
    processed_dir = args.processed_root / video_id
    metadata_path = raw_dir / "metadata.json"
    transcript_path = raw_dir / "transcript_original.json"
    segments_path = processed_dir / "content_segments.json"

    logger.event(video_id=video_id, step="episode_pipeline", status="started")

    if not args.skip_metadata:
        if url:
            run_step(
                logger,
                video_id,
                "collect_metadata",
                [
                    sys.executable,
                    "scripts/collect_youtube_metadata.py",
                    "--url",
                    url,
                    "--source",
                    args.source,
                    "--output-root",
                    str(args.raw_youtube_root),
                ],
            )
        elif not metadata_path.exists():
            raise FileNotFoundError(f"Missing metadata for {video_id}: {metadata_path}")

    if not args.skip_transcript and (args.force or not transcript_has_segments(transcript_path)):
        run_step(
            logger,
            video_id,
            "collect_transcript",
            [
                sys.executable,
                "scripts/collect_youtube_transcript.py",
                "--metadata",
                str(metadata_path),
                "--output-root",
                str(args.raw_youtube_root),
            ],
        )

    if not transcript_has_segments(transcript_path):
        write_fallback_note(video_id, processed_dir)
        logger.event(
            video_id=video_id,
            step="collect_transcript",
            status="needs_playwright_fallback",
            note="Direct transcript has no segments. See transcript_fallback_needed.md.",
        )
        update_metadata_status(
            metadata_path,
            processing_status="blocked",
            transcript_status="missing",
            asset_detection_status="pending",
        )
        logger.event(video_id=video_id, step="episode_pipeline", status="blocked")
        return

    fallback_note = processed_dir / "transcript_fallback_needed.md"
    if fallback_note.exists():
        try:
            fallback_note.unlink()
        except OSError as error:
            try:
                fallback_note.write_text(
                    "\n".join(
                        [
                            f"# Stale Transcript Fallback Marker - {video_id}",
                            "",
                            "This episode now has transcript segments, but the old fallback marker could not be deleted.",
                            f"Cleanup error: {error}",
                            "",
                        ]
                    ),
                    encoding="utf-8",
                    newline="\n",
                )
            except OSError:
                pass
            logger.event(
                video_id=video_id,
                step="cleanup_fallback_note",
                status="skipped",
                reason=f"could_not_remove_stale_marker={error}",
            )

    if args.force or not segments_path.exists():
        run_step(
            logger,
            video_id,
            "normalize_transcript",
            [
                sys.executable,
                "scripts/normalize_transcript.py",
                "--input",
                str(transcript_path),
                "--output",
                str(segments_path),
            ],
        )

    run_step(
        logger,
        video_id,
        "create_chunks",
        [
            sys.executable,
            "scripts/create_extraction_chunks.py",
            "--segments",
            str(segments_path),
            "--metadata",
            str(metadata_path),
            "--output-dir",
            str(processed_dir / "chunks"),
            "--max-chars",
            str(args.max_chars),
        ],
    )
    run_step(
        logger,
        video_id,
        "detect_assets",
        [
            sys.executable,
            "scripts/detect_assets.py",
            "--metadata",
            str(metadata_path),
            "--segments",
            str(segments_path),
            "--output-dir",
            str(processed_dir),
        ],
    )
    run_step(
        logger,
        video_id,
        "prepare_chunked_extraction_packets",
        [
            sys.executable,
            "scripts/prepare_chunked_extraction_packets.py",
            "--chunk-index",
            str(processed_dir / "chunks" / "chunk_index.json"),
            "--metadata",
            str(metadata_path),
            "--extractors",
            args.extractors,
            "--output-dir",
            str(processed_dir / "chunked_extraction_packets"),
            "--insights-dir",
            str(processed_dir / "chunked_insights"),
        ],
    )
    run_step(
        logger,
        video_id,
        "generate_summary",
        [sys.executable, "scripts/generate_summaries.py", f"--episode={video_id}"],
    )
    update_metadata_status(
        metadata_path,
        processing_status="processed",
        transcript_status="available",
        asset_detection_status="processed",
    )
    logger.event(video_id=video_id, step="episode_pipeline", status="passed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Single YouTube URL or id")
    parser.add_argument("--csv", type=Path, help="CSV with youtube_url values")
    parser.add_argument("--video-id", help="Existing local video id")
    parser.add_argument("--source", default="VTurb")
    parser.add_argument("--raw-youtube-root", default=Path("data/raw/youtube"), type=Path)
    parser.add_argument("--processed-root", default=Path("data/processed"), type=Path)
    parser.add_argument("--log", type=Path, help="JSONL log path")
    parser.add_argument("--extractors", default="vsl,ads,offer,funnel,copy,ops")
    parser.add_argument("--max-chars", default=50000, type=int)
    parser.add_argument("--skip-metadata", action="store_true")
    parser.add_argument("--skip-transcript", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    log_path = args.log or Path("data/logs") / f"episode_pipeline_{utc_now().replace(':', '').replace('-', '')}.jsonl"
    logger = PipelineLogger(log_path)
    for item in video_inputs(args):
        run_for_video(args, logger, item)
    print(f"Wrote pipeline log to {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
