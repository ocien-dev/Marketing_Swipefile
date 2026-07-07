#!/usr/bin/env python
"""Run the Marketing Swipe File episode loop until a complete-video target is reached."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from youtube_common import extract_video_id


@dataclass
class EpisodeStatus:
    video_id: str
    url: str
    priority: int
    metadata: bool
    transcript_segments: int
    content_segments: int
    chunks: int
    insights: int

    @property
    def complete(self) -> bool:
        return bool(self.metadata and self.transcript_segments and self.content_segments and self.chunks and self.insights)

    @property
    def has_transcript_pipeline_base(self) -> bool:
        return bool(self.metadata and self.transcript_segments and self.content_segments and self.chunks)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def count_items(path: Path, key: str) -> int:
    if not path.exists():
        return 0
    try:
        payload = load_json(path)
    except Exception:
        return 0
    items = payload.get(key)
    return len(items) if isinstance(items, list) else 0


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def priority_value(row: dict[str, str]) -> int:
    try:
        return int(row.get("episode_priority") or 0)
    except ValueError:
        return 0


def status_for_row(row: dict[str, str], raw_root: Path, processed_root: Path) -> EpisodeStatus:
    url = (row.get("youtube_url") or "").strip()
    video_id = extract_video_id(url)
    raw_dir = raw_root / video_id
    processed_dir = processed_root / video_id
    return EpisodeStatus(
        video_id=video_id,
        url=url,
        priority=priority_value(row),
        metadata=(raw_dir / "metadata.json").exists(),
        transcript_segments=count_items(raw_dir / "transcript_original.json", "segments"),
        content_segments=count_items(processed_dir / "content_segments.json", "segments"),
        chunks=count_items(processed_dir / "chunks" / "chunk_index.json", "chunks"),
        insights=count_items(processed_dir / "insights.json", "insights"),
    )


def all_statuses(rows: list[dict[str, str]], raw_root: Path, processed_root: Path) -> list[EpisodeStatus]:
    return [status_for_row(row, raw_root, processed_root) for row in sorted(rows, key=priority_value)]


def run_command(command: list[str], dry_run: bool = False) -> None:
    printable = " ".join(str(part) for part in command)
    print(f"$ {printable}")
    if dry_run:
        return
    completed = subprocess.run(command, text=True, capture_output=True, encoding="utf-8", errors="replace")
    if completed.stdout:
        print(completed.stdout[-4000:])
    if completed.stderr:
        print(completed.stderr[-4000:], file=sys.stderr)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {completed.returncode}: {printable}")


def run_episode_pipeline(status: EpisodeStatus, args: argparse.Namespace, skip_metadata: bool, skip_transcript: bool) -> None:
    command = [
        sys.executable,
        "scripts/run_episode_pipeline.py",
        "--raw-youtube-root",
        str(args.raw_youtube_root),
        "--processed-root",
        str(args.processed_root),
    ]
    if skip_metadata:
        command.insert(2, f"--video-id={status.video_id}")
    else:
        command.insert(2, status.url)
        command.insert(2, "--url")
    if skip_metadata:
        command.append("--skip-metadata")
    if skip_transcript:
        command.append("--skip-transcript")
    run_command(command, dry_run=args.dry_run)


def capture_playwright_transcript(status: EpisodeStatus, args: argparse.Namespace) -> None:
    output = args.raw_youtube_root / status.video_id / "transcript_original.json"
    run_command(
        [
            sys.executable,
            "scripts/capture_youtube_transcript_with_playwright_cli.py",
            "--url",
            status.url,
            "--output",
            str(output),
            "--session",
            args.playwright_session,
            "--timeout",
            str(args.playwright_timeout),
        ],
        dry_run=args.dry_run,
    )


def extract_and_review(status: EpisodeStatus, args: argparse.Namespace) -> None:
    insights_path = args.processed_root / status.video_id / "insights.json"
    run_command([sys.executable, "scripts/extract_transcript_insights.py", f"--video-id={status.video_id}"], dry_run=args.dry_run)
    run_command([sys.executable, "scripts/classify_taxonomy.py", "--input", str(insights_path)], dry_run=args.dry_run)
    run_command([sys.executable, "scripts/dedupe_insights.py", "--input", str(insights_path)], dry_run=args.dry_run)
    run_command([sys.executable, "scripts/audit_insights.py", "--input", str(insights_path)], dry_run=args.dry_run)
    run_command([sys.executable, "scripts/generate_summaries.py", f"--episode={status.video_id}"], dry_run=args.dry_run)


def ensure_complete(row: dict[str, str], args: argparse.Namespace) -> str:
    status = status_for_row(row, args.raw_youtube_root, args.processed_root)
    print(
        f"\n[{status.priority}] {status.video_id}: "
        f"metadata={status.metadata} transcript={status.transcript_segments} "
        f"chunks={status.chunks} insights={status.insights}"
    )
    if status.complete:
        return "already_complete"

    if not status.metadata:
        run_episode_pipeline(status, args, skip_metadata=False, skip_transcript=False)
        status = status_for_row(row, args.raw_youtube_root, args.processed_root)

    if not status.transcript_segments and args.use_playwright_fallback:
        capture_playwright_transcript(status, args)
        status = status_for_row(row, args.raw_youtube_root, args.processed_root)

    if not status.content_segments or not status.chunks:
        if not status.transcript_segments:
            return "blocked_missing_transcript"
        run_episode_pipeline(status, args, skip_metadata=True, skip_transcript=True)
        status = status_for_row(row, args.raw_youtube_root, args.processed_root)

    if status.has_transcript_pipeline_base and not status.insights:
        extract_and_review(status, args)
        status = status_for_row(row, args.raw_youtube_root, args.processed_root)

    return "completed" if status.complete else "incomplete_after_attempt"


def print_status(statuses: list[EpisodeStatus]) -> None:
    print(f"listed={len(statuses)}")
    print(f"complete={sum(1 for item in statuses if item.complete)}")
    print(f"with_transcript={sum(1 for item in statuses if item.transcript_segments)}")
    print(f"with_chunks={sum(1 for item in statuses if item.chunks)}")
    print("incomplete:")
    for item in statuses:
        if not item.complete:
            print(
                f"- {item.priority} {item.video_id}: metadata={item.metadata} "
                f"transcript={item.transcript_segments} chunks={item.chunks} insights={item.insights}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", default=Path("data/input/youtube_urls.csv"), type=Path)
    parser.add_argument("--target-complete", default=50, type=int)
    parser.add_argument("--max-attempts", type=int, help="Maximum incomplete episodes to attempt in this run")
    parser.add_argument("--start-priority", type=int, help="Skip attempts before this episode_priority")
    parser.add_argument("--raw-youtube-root", default=Path("data/raw/youtube"), type=Path)
    parser.add_argument("--processed-root", default=Path("data/processed"), type=Path)
    parser.add_argument("--use-playwright-fallback", action="store_true")
    parser.add_argument("--playwright-session", default="msf-transcript-batch")
    parser.add_argument("--playwright-timeout", default=120, type=int)
    parser.add_argument("--status-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-consolidate", action="store_true")
    args = parser.parse_args()

    rows = [row for row in csv_rows(args.csv) if (row.get("youtube_url") or "").strip()]
    statuses = all_statuses(rows, args.raw_youtube_root, args.processed_root)
    print_status(statuses)
    if args.status_only:
        return 0 if sum(1 for item in statuses if item.complete) >= args.target_complete else 1

    attempted = 0
    outcomes: dict[str, int] = {}
    for row in sorted(rows, key=priority_value):
        if args.start_priority is not None and priority_value(row) < args.start_priority:
            continue
        statuses = all_statuses(rows, args.raw_youtube_root, args.processed_root)
        complete_count = sum(1 for item in statuses if item.complete)
        if complete_count >= args.target_complete:
            break
        current = status_for_row(row, args.raw_youtube_root, args.processed_root)
        if current.complete:
            continue
        if args.max_attempts is not None and attempted >= args.max_attempts:
            break
        attempted += 1
        try:
            outcome = ensure_complete(row, args)
        except Exception as error:
            outcome = "failed"
            print(f"ERROR {current.video_id}: {error}", file=sys.stderr)
        outcomes[outcome] = outcomes.get(outcome, 0) + 1

    if not args.skip_consolidate:
        run_command([sys.executable, "scripts/consolidate_exports.py"], dry_run=args.dry_run)

    final_statuses = all_statuses(rows, args.raw_youtube_root, args.processed_root)
    print("\nFinal status:")
    print_status(final_statuses)
    print(f"outcomes={outcomes}")
    complete_count = sum(1 for item in final_statuses if item.complete)
    return 0 if complete_count >= args.target_complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
