#!/usr/bin/env python
"""Produce a read-only, machine-readable delta between two blind gold packets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.gold_extraction_common import json_hashes


PACKET_FILES = {
    "manifest": "packet_manifest.json",
    "transcript": "transcript_clean.json",
    "insights": "insights_exhaustive.json",
    "ledger": "high_signal_coverage_ledger.json",
    "calibration": "calibration_tests.json",
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _by_id(values: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in values:
        if field not in item:
            raise ValueError(f"item missing {field}")
        item_id = str(item[field])
        if item_id in result:
            raise ValueError(f"duplicate {field}: {item_id}")
        result[item_id] = item
    return result


def _changed_fields(before: dict[str, Any], after: dict[str, Any], excluded: set[str] | None = None) -> list[str]:
    excluded = excluded or set()
    return sorted(field for field in set(before) | set(after) if field not in excluded and before.get(field) != after.get(field))


def packet_delta(before_dir: Path, after_dir: Path) -> dict[str, Any]:
    for filename in PACKET_FILES.values():
        if not (before_dir / filename).exists() or not (after_dir / filename).exists():
            raise ValueError(f"both packets need {filename}")
    before_manifest = load(before_dir / PACKET_FILES["manifest"])
    after_manifest = load(after_dir / PACKET_FILES["manifest"])
    before_transcript = load(before_dir / PACKET_FILES["transcript"])
    after_transcript = load(after_dir / PACKET_FILES["transcript"])
    before_insights = _by_id(load(before_dir / PACKET_FILES["insights"]).get("insights", []), "candidate_id")
    after_insights = _by_id(load(after_dir / PACKET_FILES["insights"]).get("insights", []), "candidate_id")
    changed_candidates = [
        {"candidate_id": candidate_id, "changed_fields": _changed_fields(before_insights[candidate_id], after_insights[candidate_id], {"candidate_id"})}
        for candidate_id in sorted(before_insights.keys() & after_insights.keys())
        if _changed_fields(before_insights[candidate_id], after_insights[candidate_id], {"candidate_id"})
    ]
    before_ledger = _by_id(load(before_dir / PACKET_FILES["ledger"]).get("entries", []), "segment_id")
    after_ledger = _by_id(load(after_dir / PACKET_FILES["ledger"]).get("entries", []), "segment_id")
    changed_ledger = [
        {"segment_id": segment_id, "changed_fields": _changed_fields(before_ledger[segment_id], after_ledger[segment_id], {"segment_id"})}
        for segment_id in sorted(before_ledger.keys() & after_ledger.keys())
        if _changed_fields(before_ledger[segment_id], after_ledger[segment_id], {"segment_id"})
    ]
    before_segments = _by_id(before_transcript.get("segments", []), "segment_id")
    after_segments = _by_id(after_transcript.get("segments", []), "segment_id")
    changed_segments = [
        {"segment_id": segment_id, "changed_fields": _changed_fields(before_segments[segment_id], after_segments[segment_id], {"segment_id"})}
        for segment_id in sorted(before_segments.keys() & after_segments.keys())
        if _changed_fields(before_segments[segment_id], after_segments[segment_id], {"segment_id"})
    ]
    hashes = {
        key: {
            "before": json_hashes(before_dir / filename),
            "after": json_hashes(after_dir / filename),
        }
        for key, filename in PACKET_FILES.items()
    }
    return {
        "read_only": True,
        "before_packet": str(before_dir),
        "after_packet": str(after_dir),
        "candidates": {
            "added": sorted(after_insights.keys() - before_insights.keys()),
            "removed": sorted(before_insights.keys() - after_insights.keys()),
            "changed": changed_candidates,
        },
        "ledger": {
            "added_segments": sorted(after_ledger.keys() - before_ledger.keys()),
            "removed_segments": sorted(before_ledger.keys() - after_ledger.keys()),
            "changed": changed_ledger,
        },
        "transcript": {
            "content_changed": before_transcript != after_transcript,
            "added_segments": sorted(after_segments.keys() - before_segments.keys()),
            "removed_segments": sorted(before_segments.keys() - after_segments.keys()),
            "changed_segments": changed_segments,
        },
        "packet_manifest": {
            "changed": before_manifest != after_manifest,
            "changed_fields": _changed_fields(before_manifest, after_manifest),
        },
        "calibration_changed": load(before_dir / PACKET_FILES["calibration"]) != load(after_dir / PACKET_FILES["calibration"]),
        "hashes": hashes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--after", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = packet_delta(args.before, args.after)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
