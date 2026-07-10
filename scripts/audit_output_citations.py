#!/usr/bin/env python
"""Audit cited insight_ids in generated outputs against a target process tag."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from msf_common import as_list, data_path, load_json, write_json


CLASS_ON_TAG = "on-tag"
CLASS_CROSS_RELEVANT = "cross-tag-relevante"
CLASS_CROSS_WEAK = "cross-tag-fraca"
CLASS_MISSING = "inexistente"
CLASS_LOW_SCORE = "score<90"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def origin_for_episode(episode_id: str) -> str:
    if episode_id.startswith("academyhls-"):
        return "academyhls"
    if episode_id.startswith("academyvid-"):
        return "academyvid"
    return "podcast"


def load_pool_by_id(path: Path) -> dict[str, dict[str, Any]]:
    payload = load_json(path)
    return {
        str(item.get("insight_id")): item
        for item in as_list(payload.get("insights"))
        if isinstance(item, dict) and item.get("insight_id")
    }


def reviewed_cross_tag_set(values: list[str] | None) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    for value in values or []:
        parts = str(value).split(":", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise SystemExit("--reviewed-cross-tag must be PAIR_ID:INSIGHT_ID")
        result.add((parts[0], parts[1]))
    return result


def reviewed_cross_tags_from_audit(payload: dict[str, Any]) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    for item in as_list(payload.get("cross_tag_reviews")):
        if not isinstance(item, dict):
            continue
        pair_id = str(item.get("pair_id") or "")
        insight_id = str(item.get("insight_id") or "")
        classification = str(item.get("classification") or "")
        if pair_id and insight_id and classification == CLASS_CROSS_RELEVANT:
            result.add((pair_id, insight_id))
    return result


def citation_ids_from_pair(pair: dict[str, Any]) -> list[str]:
    if isinstance(pair.get("insights"), list):
        return [
            str(item.get("insight_id"))
            for item in pair["insights"]
            if isinstance(item, dict) and item.get("insight_id")
        ]
    if isinstance(pair.get("with_skill_insight_ids"), list):
        return [str(item) for item in pair["with_skill_insight_ids"] if item]
    return []


def classify_citation(
    *,
    pair_id: str,
    insight_id: str,
    pool: dict[str, dict[str, Any]],
    target_tag: str,
    min_editorial_score: int,
    reviewed_cross_tags: set[tuple[str, str]],
) -> dict[str, Any]:
    item = pool.get(insight_id)
    if not item:
        return {
            "pair_id": pair_id,
            "insight_id": insight_id,
            "classification": CLASS_MISSING,
            "origin": None,
            "editorial_score": None,
            "process_tags": [],
            "title": None,
        }

    tags = [str(tag) for tag in as_list(item.get("process_tags")) if tag]
    score = int(item.get("editorial_score") or 0)
    if score < min_editorial_score:
        classification = CLASS_LOW_SCORE
    elif target_tag in tags:
        classification = CLASS_ON_TAG
    elif (pair_id, insight_id) in reviewed_cross_tags:
        classification = CLASS_CROSS_RELEVANT
    else:
        classification = CLASS_CROSS_WEAK

    episode_id = str(item.get("episode_video_id") or "")
    return {
        "pair_id": pair_id,
        "insight_id": insight_id,
        "classification": classification,
        "origin": origin_for_episode(episode_id),
        "episode_video_id": episode_id,
        "title": item.get("title"),
        "editorial_score": score,
        "process_tags": tags,
        "target_tag": target_tag,
        "target_tag_present": target_tag in tags,
    }


def audit_citation_audit(
    citation_audit: dict[str, Any],
    pool: dict[str, dict[str, Any]],
    *,
    target_tag: str,
    min_editorial_score: int = 90,
    reviewed_cross_tags: set[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    reviewed = reviewed_cross_tags or set()
    pairs: list[dict[str, Any]] = []
    all_records: list[dict[str, Any]] = []
    for pair in as_list(citation_audit.get("pairs")):
        if not isinstance(pair, dict):
            continue
        pair_id = str(pair.get("pair_id") or "")
        records = [
            classify_citation(
                pair_id=pair_id,
                insight_id=insight_id,
                pool=pool,
                target_tag=target_tag,
                min_editorial_score=min_editorial_score,
                reviewed_cross_tags=reviewed,
            )
            for insight_id in citation_ids_from_pair(pair)
        ]
        all_records.extend(records)
        pairs.append(
            {
                "pair_id": pair_id,
                "briefing_id": pair.get("briefing_id"),
                "citation_count": len(records),
                "classification_counts": dict(Counter(record["classification"] for record in records)),
                "citations": records,
            }
        )

    counts = Counter(record["classification"] for record in all_records)
    for key in [CLASS_ON_TAG, CLASS_CROSS_RELEVANT, CLASS_CROSS_WEAK, CLASS_MISSING, CLASS_LOW_SCORE]:
        counts.setdefault(key, 0)
    pass_guard = counts[CLASS_CROSS_WEAK] == 0 and counts[CLASS_MISSING] == 0 and counts[CLASS_LOW_SCORE] == 0
    return {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "status": "PASS" if pass_guard else "FAIL",
        "target_tag": target_tag,
        "min_editorial_score": min_editorial_score,
        "citation_count": len(all_records),
        "classification_counts": dict(counts),
        "reviewed_cross_tags": [
            {"pair_id": pair_id, "insight_id": insight_id}
            for pair_id, insight_id in sorted(reviewed)
        ],
        "pairs": pairs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--citation-audit", type=Path, required=True)
    parser.add_argument("--pool", type=Path, default=data_path("exports", "insights_v2_master.json"))
    parser.add_argument("--target-tag", default="process-copy-anuncios")
    parser.add_argument("--min-editorial-score", type=int, default=90)
    parser.add_argument("--reviewed-cross-tag", action="append", help="PAIR_ID:INSIGHT_ID reviewed as relevant")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    citation_audit = load_json(args.citation_audit)
    reviewed = reviewed_cross_tags_from_audit(citation_audit) | reviewed_cross_tag_set(args.reviewed_cross_tag)
    result = audit_citation_audit(
        citation_audit,
        load_pool_by_id(args.pool),
        target_tag=args.target_tag,
        min_editorial_score=args.min_editorial_score,
        reviewed_cross_tags=reviewed,
    )
    if args.output:
        write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
