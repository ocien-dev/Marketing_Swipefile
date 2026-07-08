#!/usr/bin/env python
"""Register and process complementary assets for an episode."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from msf_common import data_path, load_json


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


def run_step(logger: PipelineLogger, asset_id: str, step: str, command: list[str]) -> subprocess.CompletedProcess[str]:
    logger.event(asset_id=asset_id, step=step, status="started", command=command)
    completed = subprocess.run(command, text=True, capture_output=True)
    logger.event(
        asset_id=asset_id,
        step=step,
        status="passed" if completed.returncode == 0 else "failed",
        returncode=completed.returncode,
        stdout=completed.stdout[-4000:],
        stderr=completed.stderr[-4000:],
    )
    if completed.returncode != 0:
        raise RuntimeError(f"{step} failed for {asset_id}: {completed.stderr or completed.stdout}")
    return completed


def known_asset_ids(raw_assets_root: Path, episode_video_id: str) -> set[str]:
    asset_ids: set[str] = set()
    for path in raw_assets_root.glob("*/metadata.json"):
        metadata = load_json(path)
        if metadata.get("episode_video_id") == episode_video_id:
            asset_ids.add(str(metadata.get("asset_id")))
    return asset_ids


def process_assets(args: argparse.Namespace, logger: PipelineLogger) -> int:
    count = 0
    for metadata_path in sorted(args.raw_assets_root.glob("*/metadata.json")):
        metadata = load_json(metadata_path)
        if args.episode_video_id and metadata.get("episode_video_id") != args.episode_video_id:
            continue
        asset_id = metadata["asset_id"]
        output = args.processed_root / "assets" / asset_id / "content_segments.json"
        if metadata.get("asset_type") == "image":
            logger.event(asset_id=asset_id, step="process_asset", status="skipped", reason="image_ocr_not_supported_yet")
            continue
        if output.exists() and not args.force:
            logger.event(asset_id=asset_id, step="process_asset", status="skipped", reason="output_exists")
        else:
            run_step(
                logger,
                asset_id,
                "process_asset",
                [
                    sys.executable,
                    "scripts/process_asset.py",
                    "--metadata",
                    str(metadata_path),
                    "--output",
                    str(output),
                ],
            )
        run_step(logger, asset_id, "generate_asset_summary", [sys.executable, "scripts/generate_summaries.py", "--asset", asset_id])
        count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode-video-id", help="Episode/video id that owns assets")
    parser.add_argument("--input-dir", type=Path, help="Directory with files to register before processing")
    parser.add_argument("--raw-assets-root", default=data_path("raw", "assets"), type=Path)
    parser.add_argument("--processed-root", default=data_path("processed"), type=Path)
    parser.add_argument("--log", type=Path, help="JSONL log path")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    log_path = args.log or data_path("logs") / f"asset_pipeline_{utc_now().replace(':', '').replace('-', '')}.jsonl"
    logger = PipelineLogger(log_path)

    if args.input_dir:
        if not args.episode_video_id:
            raise ValueError("--episode-video-id is required when using --input-dir")
        before = known_asset_ids(args.raw_assets_root, args.episode_video_id)
        run_step(
            logger,
            args.episode_video_id,
            "register_assets",
            [
                sys.executable,
                "scripts/register_assets.py",
                "--episode-video-id",
                args.episode_video_id,
                "--input-dir",
                str(args.input_dir),
                "--output-root",
                str(args.raw_assets_root),
            ],
        )
        after = known_asset_ids(args.raw_assets_root, args.episode_video_id)
        logger.event(asset_id=args.episode_video_id, step="register_assets", status="summary", new_asset_ids=sorted(after - before))

    count = process_assets(args, logger)
    print(f"Processed {count} asset(s). Wrote pipeline log to {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
