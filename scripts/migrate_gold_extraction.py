#!/usr/bin/env python
"""Migrate an approved legacy gold package into resumable review files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.gold_extraction_common import SCHEMA_VERSION, load_json, sha256_json, write_json


def migrate(video_id: str, data_root: Path) -> dict[str, Any]:
    out = data_root / "processed" / video_id / "gold_extraction"
    legacy = load_json(out / "insights_exhaustive.json")
    status = load_json(out / "gold_extraction_status.json")
    by_chunk: dict[str, list[dict[str, Any]]] = {}
    for candidate in legacy.get("insights", []):
        by_chunk.setdefault(candidate["chunk_id"], []).append(candidate)
    migrated = 0
    for chunk in status.get("chunks", []):
        chunk_id = chunk["chunk_id"]
        review_path = out / "manual_reviews" / f"chunk_{chunk['chunk_number']:03d}_review.json"
        if review_path.exists():
            continue
        review = {
            "schema_version": SCHEMA_VERSION, "episode_video_id": video_id, "chunk_id": chunk_id,
            "input_hash": chunk["input_hash"], "review_route": "legacy_gold_migration",
            "full_chunk_reviewed": True, "candidates": by_chunk.get(chunk_id, []), "ledger_decisions": [],
            "migration_note": "Existing externally approved gold candidates preserved verbatim; layered evidence is normalized by the builder.",
        }
        write_json(review_path, review)
        migrated += 1
    return {"migrated_review_files": migrated, "legacy_candidates": sum(len(items) for items in by_chunk.values())}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--data-root", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(migrate(args.video_id, args.data_root), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
