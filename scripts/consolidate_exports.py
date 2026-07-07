#!/usr/bin/env python
"""Consolidate local Marketing Swipe File artifacts into master exports."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from msf_common import first_evidence, insight_text, load_json, normalize_text, slugify, write_json
from validate_insights_v2 import validate_payload
from youtube_common import extract_video_id


INSIGHTS_V2_SCHEMA_PATH = Path("schemas/insights_v2.schema.json")
R07_TARGET_EPISODE_COUNT = 50
R07_GATE_MIN_COMPLETE_EPISODES = 15
R07_GATE_MAX_COMPLETE_EPISODES = 20


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "|".join(str(item) for item in value)
    if isinstance(value, dict):
        return "; ".join(f"{key}={item}" for key, item in value.items())
    return str(value)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_value(row.get(field)) for field in fieldnames})


def load_json_files(patterns: list[str], root: Path) -> list[tuple[Path, dict[str, Any]]]:
    results: list[tuple[Path, dict[str, Any]]] = []
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if path.is_file():
                results.append((path, load_json(path)))
    return results


def is_fixture_id(value: Any) -> bool:
    return str(value or "").lower().startswith("fixture")


def collect_episodes(raw_youtube_root: Path, include_fixtures: bool) -> dict[str, dict[str, Any]]:
    episodes: dict[str, dict[str, Any]] = {}
    for path in sorted(raw_youtube_root.glob("*/metadata.json")):
        metadata = load_json(path)
        video_id = metadata.get("youtube_video_id")
        if not video_id:
            continue
        if is_fixture_id(video_id) and not include_fixtures:
            continue
        episodes[video_id] = {**metadata, "metadata_path": str(path)}
    return episodes


def collect_assets(raw_assets_root: Path, include_fixtures: bool) -> dict[str, dict[str, Any]]:
    assets: dict[str, dict[str, Any]] = {}
    for path in sorted(raw_assets_root.glob("*/metadata.json")):
        metadata = load_json(path)
        asset_id = metadata.get("asset_id")
        if not asset_id:
            continue
        if is_fixture_id(metadata.get("episode_video_id")) and not include_fixtures:
            continue
        assets[asset_id] = {**metadata, "metadata_path": str(path)}
    return assets


def collect_chunk_ready_episodes(processed_root: Path, include_fixtures: bool) -> dict[str, dict[str, Any]]:
    episodes: dict[str, dict[str, Any]] = {}
    for path in sorted(processed_root.glob("*/chunks/chunk_index.json")):
        video_id = path.parent.parent.name
        if is_fixture_id(video_id) and not include_fixtures:
            continue
        payload = load_json(path)
        chunks = payload.get("chunks")
        chunk_ids = []
        if isinstance(chunks, list):
            for index, chunk in enumerate(chunks, start=1):
                if isinstance(chunk, dict):
                    chunk_ids.append(str(chunk.get("chunk_id") or f"{video_id}-chunk-{index:04d}"))
        episodes[video_id] = {
            "episode_video_id": video_id,
            "chunk_count": len(chunks) if isinstance(chunks, list) else 0,
            "chunk_ids": chunk_ids,
            "chunk_index_path": str(path),
        }
    return episodes


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


def collect_r07_target_episodes(
    csv_path: Path,
    raw_youtube_root: Path,
    processed_root: Path,
    chunk_ready_episodes: dict[str, dict[str, Any]],
    target_count: int,
    include_fixtures: bool,
) -> dict[str, dict[str, Any]]:
    if not csv_path.exists():
        return {}

    targets: dict[str, dict[str, Any]] = {}
    for row in sorted(csv_rows(csv_path), key=priority_value):
        url = (row.get("youtube_url") or "").strip()
        if not url:
            continue
        video_id = extract_video_id(url)
        if is_fixture_id(video_id) and not include_fixtures:
            continue
        raw_dir = raw_youtube_root / video_id
        processed_dir = processed_root / video_id
        chunk_info = chunk_ready_episodes.get(video_id)
        if not chunk_info:
            continue
        is_complete_v1 = bool(
            (raw_dir / "metadata.json").exists()
            and count_items(raw_dir / "transcript_original.json", "segments")
            and count_items(processed_dir / "content_segments.json", "segments")
            and chunk_info.get("chunk_count", 0)
            and count_items(processed_dir / "insights.json", "insights")
        )
        if not is_complete_v1:
            continue
        targets[video_id] = {
            **chunk_info,
            "episode_priority": priority_value(row),
            "youtube_url": url,
        }
        if len(targets) >= target_count:
            break
    return targets


def insight_key(insight: dict[str, Any]) -> str:
    dedupe_key = normalize_text(insight.get("dedupe_key"))
    if dedupe_key:
        return f"dedupe:{dedupe_key}"
    return f"text:{slugify(insight.get('title'))}:{slugify(insight.get('insight_ptbr'))}"


def quality_score(insight: dict[str, Any]) -> tuple[float, int, int]:
    confidence = insight.get("confidence_score")
    confidence_value = float(confidence) if isinstance(confidence, (int, float)) else 0.0
    return confidence_value, len(insight.get("evidence") or []), len(insight_text(insight))


def insight_v2_key(insight: dict[str, Any]) -> str:
    dedupe_key = normalize_text(insight.get("dedupe_key"))
    if dedupe_key:
        return f"dedupe:{dedupe_key}"
    insight_id = normalize_text(insight.get("insight_id"))
    if insight_id:
        return f"id:{insight_id}"
    return f"text:{slugify(insight.get('canonical_title') or insight.get('title'))}:{slugify(insight.get('specific_takeaway'))}"


def quality_score_v2(insight: dict[str, Any]) -> tuple[int, float, int, int]:
    editorial = insight.get("editorial_score")
    editorial_value = int(editorial) if isinstance(editorial, int) else 0
    confidence = insight.get("confidence_score")
    confidence_value = float(confidence) if isinstance(confidence, (int, float)) else 0.0
    return editorial_value, confidence_value, len(insight.get("evidence") or []), len(insight_text(insight))


def collect_insights(
    processed_root: Path,
    episodes: dict[str, dict[str, Any]],
    assets: dict[str, dict[str, Any]],
    include_fixtures: bool,
) -> list[dict[str, Any]]:
    patterns = [
        "*/insights.json",
        "*/description_insights.json",
        "*/chunked_insights/*/*_insights.json",
        "assets/*/insights.json",
    ]
    by_key: dict[str, dict[str, Any]] = {}
    for path, payload in load_json_files(patterns, processed_root):
        top_episode_id = payload.get("episode_video_id")
        top_asset_id = payload.get("asset_id")
        if is_fixture_id(top_episode_id) and not include_fixtures:
            continue
        for item in payload.get("insights", []):
            if not isinstance(item, dict):
                continue
            insight = dict(item)
            episode_id = insight.get("episode_video_id") or top_episode_id
            asset_id = insight.get("asset_id") or top_asset_id
            episode = episodes.get(episode_id or "", {})
            asset = assets.get(asset_id or "", {})
            insight["episode_video_id"] = episode_id
            insight["asset_id"] = asset_id
            insight["source_file"] = str(path)
            insight["episode_title"] = episode.get("title")
            insight["channel_name"] = episode.get("channel_name")
            insight["asset_filename"] = asset.get("original_filename")

            key = insight_key(insight)
            current = by_key.get(key)
            if current is None or quality_score(insight) > quality_score(current):
                by_key[key] = insight

    return sorted(by_key.values(), key=lambda item: (str(item.get("episode_video_id") or ""), str(item.get("insight_id") or "")))


def collect_insights_v2(
    processed_root: Path,
    episodes: dict[str, dict[str, Any]],
    assets: dict[str, dict[str, Any]],
    include_fixtures: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    patterns = [
        "*/insights_v2.json",
        "assets/*/insights_v2.json",
    ]
    by_key: dict[str, dict[str, Any]] = {}
    runs: list[dict[str, Any]] = []
    validation_errors: list[dict[str, Any]] = []

    for path, payload in load_json_files(patterns, processed_root):
        top_episode_id = payload.get("episode_video_id")
        top_asset_id = payload.get("asset_id")
        if is_fixture_id(top_episode_id) and not include_fixtures:
            continue

        errors = validate_payload(payload, INSIGHTS_V2_SCHEMA_PATH)
        if errors:
            validation_errors.append(
                {
                    "source_file": str(path),
                    "episode_video_id": top_episode_id,
                    "asset_id": top_asset_id,
                    "errors": errors,
                }
            )
            continue

        extraction_run = payload.get("extraction_run") or {}
        raw_insights = payload.get("insights") or []
        runs.append(
            {
                "episode_video_id": top_episode_id,
                "asset_id": top_asset_id,
                "source_file": str(path),
                "insight_count": len(raw_insights) if isinstance(raw_insights, list) else 0,
                "run_id": extraction_run.get("run_id"),
                "route": extraction_run.get("route"),
                "model": extraction_run.get("model"),
                "prompt_version": extraction_run.get("prompt_version"),
                "generated_at": extraction_run.get("generated_at"),
                "chunk_count": extraction_run.get("chunk_count"),
                "input_chunk_ids": extraction_run.get("input_chunk_ids"),
                "cost": extraction_run.get("cost"),
            }
        )

        for item in raw_insights:
            if not isinstance(item, dict):
                continue
            insight = dict(item)
            source_chunk = insight.get("source_chunk") if isinstance(insight.get("source_chunk"), dict) else {}
            episode_id = top_episode_id
            asset_id = top_asset_id
            episode = episodes.get(episode_id or "", {})
            asset = assets.get(asset_id or "", {})
            insight["episode_video_id"] = episode_id
            insight["asset_id"] = asset_id
            insight["source_file"] = str(path)
            insight["episode_title"] = episode.get("title")
            insight["channel_name"] = episode.get("channel_name")
            insight["asset_filename"] = asset.get("original_filename")
            insight["extraction_run_id"] = extraction_run.get("run_id")
            insight["extraction_route"] = extraction_run.get("route")
            insight["extraction_model"] = extraction_run.get("model")
            insight["extraction_prompt_version"] = extraction_run.get("prompt_version")
            insight["source_chunk_id"] = source_chunk.get("chunk_id")
            insight["source_chunk_index"] = source_chunk.get("chunk_index")

            key = insight_v2_key(insight)
            current = by_key.get(key)
            if current is None or quality_score_v2(insight) > quality_score_v2(current):
                by_key[key] = insight

    return (
        sorted(
            by_key.values(),
            key=lambda item: (
                str(item.get("episode_video_id") or ""),
                int(item.get("source_chunk_index")) if isinstance(item.get("source_chunk_index"), int) else 999999,
                str(item.get("insight_id") or ""),
            ),
        ),
        runs,
        validation_errors,
    )


def collect_referenced_assets(processed_root: Path, episodes: dict[str, dict[str, Any]], include_fixtures: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path, payload in load_json_files(["*/referenced_assets.json"], processed_root):
        episode_id = payload.get("episode_video_id")
        if is_fixture_id(episode_id) and not include_fixtures:
            continue
        episode = episodes.get(episode_id or "", {})
        for asset in payload.get("referenced_assets", []):
            if isinstance(asset, dict):
                rows.append({**asset, "episode_video_id": episode_id, "episode_title": episode.get("title"), "source_file": str(path)})
    return rows


def collect_acquisition_tasks(processed_root: Path, referenced_assets: list[dict[str, Any]], include_fixtures: bool) -> list[dict[str, Any]]:
    asset_by_id = {asset.get("referenced_asset_id"): asset for asset in referenced_assets}
    rows: list[dict[str, Any]] = []
    for path, payload in load_json_files(["*/acquisition_tasks.json"], processed_root):
        episode_id = payload.get("episode_video_id")
        if is_fixture_id(episode_id) and not include_fixtures:
            continue
        for task in payload.get("tasks", []):
            if not isinstance(task, dict):
                continue
            ref_asset = asset_by_id.get(task.get("referenced_asset_id"), {})
            rows.append(
                {
                    **task,
                    "episode_video_id": episode_id,
                    "episode_title": ref_asset.get("episode_title"),
                    "asset_type_guess": ref_asset.get("asset_type_guess"),
                    "mention_start_seconds": ref_asset.get("mention_start_seconds"),
                    "mention_quote_original": ref_asset.get("mention_quote_original"),
                    "expected_value": ref_asset.get("expected_value"),
                    "source_file": str(path),
                }
            )
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(rows, key=lambda item: (priority_order.get(str(item.get("priority")), 9), str(item.get("episode_video_id") or "")))


def title_distribution_rows(insights: list[dict[str, Any]]) -> list[dict[str, Any]]:
    title_counts: Counter[str] = Counter()
    display_titles: dict[str, str] = {}
    for insight in insights:
        title = insight.get("canonical_title") or insight.get("title")
        key = normalize_text(title)
        if not key:
            continue
        title_counts[key] += 1
        display_titles.setdefault(key, str(title))

    total = sum(title_counts.values())
    rows: list[dict[str, Any]] = []
    for key, count in title_counts.most_common():
        percent = (count / total * 100) if total else 0
        rows.append(
            {
                "title": display_titles.get(key, key),
                "normalized_title": key,
                "count": count,
                "percent": round(percent, 2),
                "is_repeated_over_5_percent": bool(count > 1 and percent > 5),
            }
        )
    return rows


def v2_chunk_ids_by_episode(insights_v2: list[dict[str, Any]], runs: list[dict[str, Any]]) -> dict[str, set[str]]:
    chunks_by_episode: dict[str, set[str]] = {}
    for run in runs:
        episode_id = str(run.get("episode_video_id") or "")
        if not episode_id:
            continue
        input_chunk_ids = run.get("input_chunk_ids") or []
        if isinstance(input_chunk_ids, list):
            chunks_by_episode.setdefault(episode_id, set()).update(str(chunk_id) for chunk_id in input_chunk_ids if chunk_id)
    for insight in insights_v2:
        episode_id = str(insight.get("episode_video_id") or "")
        if not episode_id:
            continue
        source_chunk = insight.get("source_chunk") if isinstance(insight.get("source_chunk"), dict) else {}
        chunk_id = source_chunk.get("chunk_id") or insight.get("source_chunk_id")
        if chunk_id:
            chunks_by_episode.setdefault(episode_id, set()).add(str(chunk_id))
    return chunks_by_episode


def chunk_coverage_rows(
    target_episodes: dict[str, dict[str, Any]],
    insights_v2: list[dict[str, Any]],
    runs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    chunks_by_episode = v2_chunk_ids_by_episode(insights_v2, runs)
    rows: list[dict[str, Any]] = []
    for video_id, target in sorted(target_episodes.items(), key=lambda item: int(item[1].get("episode_priority") or 999999)):
        expected_chunks = {str(chunk_id) for chunk_id in target.get("chunk_ids", []) if chunk_id}
        extracted_chunks = chunks_by_episode.get(video_id, set())
        known_extracted_chunks = expected_chunks & extracted_chunks if expected_chunks else extracted_chunks
        missing_chunks = sorted(expected_chunks - extracted_chunks)
        expected_count = len(expected_chunks) if expected_chunks else int(target.get("chunk_count") or 0)
        extracted_count = len(known_extracted_chunks)
        rows.append(
            {
                "episode_video_id": video_id,
                "episode_priority": target.get("episode_priority"),
                "expected_chunk_count": expected_count,
                "extracted_v2_chunk_count": extracted_count,
                "missing_v2_chunk_count": max(expected_count - extracted_count, 0),
                "is_fully_extracted_v2": bool(expected_count and extracted_count >= expected_count),
                "missing_v2_chunk_ids": missing_chunks,
            }
        )
    return rows


def insights_v2_episode_status_rows(
    chunk_ready_episodes: dict[str, dict[str, Any]],
    r07_target_episodes: dict[str, dict[str, Any]],
    episodes: dict[str, dict[str, Any]],
    insights_v2: list[dict[str, Any]],
    runs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    insight_counts: Counter[str] = Counter(str(item.get("episode_video_id") or "") for item in insights_v2)
    run_by_episode = {str(run.get("episode_video_id") or ""): run for run in runs}
    chunk_coverage_by_episode = {row["episode_video_id"]: row for row in chunk_coverage_rows(r07_target_episodes, insights_v2, runs)}
    rows: list[dict[str, Any]] = []
    for video_id in sorted(set(chunk_ready_episodes) | {key for key in insight_counts if key}):
        episode = episodes.get(video_id, {})
        chunk_ready = chunk_ready_episodes.get(video_id, {})
        run = run_by_episode.get(video_id, {})
        cost = run.get("cost") if isinstance(run.get("cost"), dict) else {}
        chunk_coverage = chunk_coverage_by_episode.get(video_id, {})
        rows.append(
            {
                "episode_video_id": video_id,
                "episode_title": episode.get("title"),
                "channel_name": episode.get("channel_name"),
                "target_for_r07": video_id in r07_target_episodes,
                "has_chunks": video_id in chunk_ready_episodes,
                "chunk_count": chunk_ready.get("chunk_count"),
                "expected_v2_chunk_count": chunk_coverage.get("expected_chunk_count"),
                "extracted_v2_chunk_count": chunk_coverage.get("extracted_v2_chunk_count"),
                "missing_v2_chunk_count": chunk_coverage.get("missing_v2_chunk_count"),
                "is_fully_extracted_v2": chunk_coverage.get("is_fully_extracted_v2"),
                "has_valid_insights_v2": insight_counts.get(video_id, 0) > 0,
                "insights_v2_count": insight_counts.get(video_id, 0),
                "run_id": run.get("run_id"),
                "route": run.get("route"),
                "model": run.get("model"),
                "prompt_version": run.get("prompt_version"),
                "generated_at": run.get("generated_at"),
                "run_chunk_count": run.get("chunk_count"),
                "estimated_usd": cost.get("estimated_usd"),
                "cost_notes": cost.get("notes"),
                "source_file": run.get("source_file"),
            }
        )
    return rows


def build_insights_v2_status(
    generated_at: str,
    chunk_ready_episodes: dict[str, dict[str, Any]],
    r07_target_episodes: dict[str, dict[str, Any]],
    r07_target_episode_count: int,
    r07_gate_min_complete_episodes: int,
    r07_gate_max_complete_episodes: int,
    insights_v2: list[dict[str, Any]],
    runs: list[dict[str, Any]],
    validation_errors: list[dict[str, Any]],
) -> dict[str, Any]:
    v2_episode_ids = {str(insight.get("episode_video_id") or "") for insight in insights_v2 if insight.get("episode_video_id")}
    target_v2_episode_ids = v2_episode_ids & set(r07_target_episodes)
    chunk_coverage = chunk_coverage_rows(r07_target_episodes, insights_v2, runs)
    target_chunk_count = sum(int(row["expected_chunk_count"] or 0) for row in chunk_coverage)
    extracted_target_chunk_count = sum(int(row["extracted_v2_chunk_count"] or 0) for row in chunk_coverage)
    fully_extracted_episode_count = sum(1 for row in chunk_coverage if row["is_fully_extracted_v2"])
    partial_episode_count = sum(
        1
        for row in chunk_coverage
        if int(row["extracted_v2_chunk_count"] or 0) > 0 and not row["is_fully_extracted_v2"]
    )
    target_chunk_coverage_percent = round(extracted_target_chunk_count / target_chunk_count * 100, 2) if target_chunk_count else 0.0
    title_distribution = title_distribution_rows(insights_v2)
    repeated_over_5 = [row for row in title_distribution if row["is_repeated_over_5_percent"]]
    coverage_complete = bool(
        len(r07_target_episodes) >= r07_target_episode_count
        and fully_extracted_episode_count >= r07_target_episode_count
        and target_chunk_count
        and extracted_target_chunk_count >= target_chunk_count
    )
    amended_gate_coverage_ready = bool(fully_extracted_episode_count >= r07_gate_min_complete_episodes)
    title_distribution_ok = not repeated_over_5
    validation_ok = not validation_errors
    return {
        "schema_version": "1.0",
        "generated_at": generated_at,
        "target": "MSF-R07",
        "r07_target_episode_count": r07_target_episode_count,
        "r07_gate_route": "codex_manual_no_api",
        "r07_gate_min_complete_episodes": r07_gate_min_complete_episodes,
        "r07_gate_max_complete_episodes": r07_gate_max_complete_episodes,
        "r07_gate_expected_chunk_range": "225-300",
        "chunk_ready_episode_count": len(chunk_ready_episodes),
        "target_v1_complete_episode_count": len(r07_target_episodes),
        "valid_v2_episode_count": len(v2_episode_ids),
        "target_valid_v2_episode_count": len(target_v2_episode_ids),
        "fully_extracted_v2_episode_count": fully_extracted_episode_count,
        "partial_v2_episode_count": partial_episode_count,
        "valid_v2_insight_count": len(insights_v2),
        "valid_v2_file_count": len(runs),
        "invalid_v2_file_count": len(validation_errors),
        "target_expected_chunk_count": target_chunk_count,
        "target_extracted_v2_chunk_count": extracted_target_chunk_count,
        "target_missing_v2_chunk_count": max(target_chunk_count - extracted_target_chunk_count, 0),
        "target_chunk_coverage_percent": target_chunk_coverage_percent,
        "chunk_coverage_by_episode": chunk_coverage,
        "title_distribution": title_distribution,
        "title_repetition_over_5_percent": repeated_over_5,
        "validation_errors": validation_errors,
        "r07_acceptance": {
            "episode_coverage_complete": fully_extracted_episode_count >= r07_target_episode_count,
            "chunk_coverage_complete": bool(target_chunk_count and extracted_target_chunk_count >= target_chunk_count),
            "coverage_complete": coverage_complete,
            "amended_gate_coverage_ready": amended_gate_coverage_ready,
            "consolidated_master_available": True,
            "title_distribution_ok": title_distribution_ok,
            "validation_ok": validation_ok,
        },
        "gate_r1_ready": bool(amended_gate_coverage_ready and title_distribution_ok and validation_ok),
    }


def insight_csv_rows(insights: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for insight in insights:
        evidence = first_evidence(insight)
        rows.append(
            {
                "insight_id": insight.get("insight_id"),
                "episode_video_id": insight.get("episode_video_id"),
                "episode_title": insight.get("episode_title"),
                "channel_name": insight.get("channel_name"),
                "asset_id": insight.get("asset_id"),
                "asset_filename": insight.get("asset_filename"),
                "source_kind": insight.get("source_kind"),
                "title": insight.get("title"),
                "insight_ptbr": insight.get("insight_ptbr"),
                "level": insight.get("level"),
                "insight_type": insight.get("insight_type"),
                "themes": insight.get("themes"),
                "subthemes": insight.get("subthemes"),
                "applicability": insight.get("applicability"),
                "niches": insight.get("niches"),
                "funnel_stages": insight.get("funnel_stages"),
                "confidence_score": insight.get("confidence_score"),
                "review_status": insight.get("review_status"),
                "source_agent": insight.get("source_agent"),
                "dedupe_key": insight.get("dedupe_key"),
                "evidence_count": len(insight.get("evidence") or []),
                "first_evidence_quote": evidence.get("quote_original"),
                "first_evidence_start_seconds": evidence.get("start_seconds"),
                "first_evidence_asset_id": evidence.get("asset_id"),
                "source_file": insight.get("source_file"),
            }
        )
    return rows


def insight_v2_csv_rows(insights: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for insight in insights:
        evidence = first_evidence(insight)
        source_chunk = insight.get("source_chunk") if isinstance(insight.get("source_chunk"), dict) else {}
        locator = evidence.get("locator") if isinstance(evidence.get("locator"), dict) else {}
        rows.append(
            {
                "insight_id": insight.get("insight_id"),
                "episode_video_id": insight.get("episode_video_id"),
                "episode_title": insight.get("episode_title"),
                "channel_name": insight.get("channel_name"),
                "asset_id": insight.get("asset_id"),
                "asset_filename": insight.get("asset_filename"),
                "source_kind": insight.get("source_kind"),
                "canonical_title": insight.get("canonical_title"),
                "title": insight.get("title"),
                "specific_takeaway": insight.get("specific_takeaway"),
                "insight_ptbr": insight.get("insight_ptbr"),
                "summary_ptbr": insight.get("summary_ptbr"),
                "use_case": insight.get("use_case"),
                "when_to_use": insight.get("when_to_use"),
                "when_not_to_use": insight.get("when_not_to_use"),
                "claim_risk": insight.get("claim_risk"),
                "evidence_cleanliness": insight.get("evidence_cleanliness"),
                "editorial_score": insight.get("editorial_score"),
                "level": insight.get("level"),
                "insight_type": insight.get("insight_type"),
                "themes": insight.get("themes"),
                "subthemes": insight.get("subthemes"),
                "applicability": insight.get("applicability"),
                "niches": insight.get("niches"),
                "funnel_stages": insight.get("funnel_stages"),
                "confidence_score": insight.get("confidence_score"),
                "review_status": insight.get("review_status"),
                "source_agent": insight.get("source_agent"),
                "dedupe_key": insight.get("dedupe_key"),
                "cluster_id": insight.get("cluster_id"),
                "supporting_insight_ids": insight.get("supporting_insight_ids"),
                "source_chunk_id": source_chunk.get("chunk_id"),
                "source_chunk_index": source_chunk.get("chunk_index"),
                "source_chunk_title": source_chunk.get("chunk_title"),
                "evidence_count": len(insight.get("evidence") or []),
                "first_evidence_quote": evidence.get("quote_original"),
                "first_evidence_start_seconds": evidence.get("start_seconds"),
                "first_evidence_locator": locator.get("value"),
                "extraction_run_id": insight.get("extraction_run_id"),
                "extraction_route": insight.get("extraction_route"),
                "extraction_model": insight.get("extraction_model"),
                "extraction_prompt_version": insight.get("extraction_prompt_version"),
                "source_file": insight.get("source_file"),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-youtube-root", default=Path("data/raw/youtube"), type=Path)
    parser.add_argument("--raw-assets-root", default=Path("data/raw/assets"), type=Path)
    parser.add_argument("--processed-root", default=Path("data/processed"), type=Path)
    parser.add_argument("--output-dir", default=Path("data/exports"), type=Path)
    parser.add_argument("--target-episode-csv", default=Path("data/input/youtube_urls.csv"), type=Path)
    parser.add_argument("--r07-target-episode-count", default=R07_TARGET_EPISODE_COUNT, type=int)
    parser.add_argument("--r07-gate-min-complete-episodes", default=R07_GATE_MIN_COMPLETE_EPISODES, type=int)
    parser.add_argument("--r07-gate-max-complete-episodes", default=R07_GATE_MAX_COMPLETE_EPISODES, type=int)
    parser.add_argument("--include-fixtures", action="store_true", help="Include local fixture episode ids in exports")
    args = parser.parse_args()

    episodes = collect_episodes(args.raw_youtube_root, args.include_fixtures)
    assets = collect_assets(args.raw_assets_root, args.include_fixtures)
    chunk_ready_episodes = collect_chunk_ready_episodes(args.processed_root, args.include_fixtures)
    r07_target_episodes = collect_r07_target_episodes(
        args.target_episode_csv,
        args.raw_youtube_root,
        args.processed_root,
        chunk_ready_episodes,
        args.r07_target_episode_count,
        args.include_fixtures,
    )
    insights = collect_insights(args.processed_root, episodes, assets, args.include_fixtures)
    insights_v2, insights_v2_runs, insights_v2_validation_errors = collect_insights_v2(
        args.processed_root,
        episodes,
        assets,
        args.include_fixtures,
    )
    referenced_assets = collect_referenced_assets(args.processed_root, episodes, args.include_fixtures)
    acquisition_tasks = collect_acquisition_tasks(args.processed_root, referenced_assets, args.include_fixtures)
    generated_at = utc_now()
    insights_v2_status = build_insights_v2_status(
        generated_at,
        chunk_ready_episodes,
        r07_target_episodes,
        args.r07_target_episode_count,
        args.r07_gate_min_complete_episodes,
        args.r07_gate_max_complete_episodes,
        insights_v2,
        insights_v2_runs,
        insights_v2_validation_errors,
    )

    write_json(
        args.output_dir / "episodes_master.json",
        {"schema_version": "1.0", "generated_at": generated_at, "episodes": list(episodes.values())},
    )
    write_json(
        args.output_dir / "assets_master.json",
        {"schema_version": "1.0", "generated_at": generated_at, "assets": list(assets.values())},
    )
    write_json(
        args.output_dir / "referenced_assets_master.json",
        {"schema_version": "1.0", "generated_at": generated_at, "referenced_assets": referenced_assets},
    )
    write_json(
        args.output_dir / "insights_master.json",
        {"schema_version": "1.0", "generated_at": generated_at, "insight_count": len(insights), "insights": insights},
    )
    write_json(
        args.output_dir / "insights_v2_master.json",
        {
            "schema_version": "2.0",
            "insight_layer": "raw_insights_v2_master",
            "generated_at": generated_at,
            "source_schema_version": "2.0",
            "episode_count": insights_v2_status["valid_v2_episode_count"],
            "insight_count": len(insights_v2),
            "validation_error_count": len(insights_v2_validation_errors),
            "title_distribution": insights_v2_status["title_distribution"],
            "insights": insights_v2,
        },
    )
    write_json(args.output_dir / "insights_v2_status.json", insights_v2_status)

    write_csv(
        args.output_dir / "insights_master.csv",
        insight_csv_rows(insights),
        [
            "insight_id",
            "episode_video_id",
            "episode_title",
            "channel_name",
            "asset_id",
            "asset_filename",
            "source_kind",
            "title",
            "insight_ptbr",
            "level",
            "insight_type",
            "themes",
            "subthemes",
            "applicability",
            "niches",
            "funnel_stages",
            "confidence_score",
            "review_status",
            "source_agent",
            "dedupe_key",
            "evidence_count",
            "first_evidence_quote",
            "first_evidence_start_seconds",
            "first_evidence_asset_id",
            "source_file",
        ],
    )
    write_csv(
        args.output_dir / "insights_v2_master.csv",
        insight_v2_csv_rows(insights_v2),
        [
            "insight_id",
            "episode_video_id",
            "episode_title",
            "channel_name",
            "asset_id",
            "asset_filename",
            "source_kind",
            "canonical_title",
            "title",
            "specific_takeaway",
            "insight_ptbr",
            "summary_ptbr",
            "use_case",
            "when_to_use",
            "when_not_to_use",
            "claim_risk",
            "evidence_cleanliness",
            "editorial_score",
            "level",
            "insight_type",
            "themes",
            "subthemes",
            "applicability",
            "niches",
            "funnel_stages",
            "confidence_score",
            "review_status",
            "source_agent",
            "dedupe_key",
            "cluster_id",
            "supporting_insight_ids",
            "source_chunk_id",
            "source_chunk_index",
            "source_chunk_title",
            "evidence_count",
            "first_evidence_quote",
            "first_evidence_start_seconds",
            "first_evidence_locator",
            "extraction_run_id",
            "extraction_route",
            "extraction_model",
            "extraction_prompt_version",
            "source_file",
        ],
    )
    write_csv(
        args.output_dir / "insights_v2_episode_status.csv",
        insights_v2_episode_status_rows(chunk_ready_episodes, r07_target_episodes, episodes, insights_v2, insights_v2_runs),
        [
            "episode_video_id",
            "episode_title",
            "channel_name",
            "target_for_r07",
            "has_chunks",
            "chunk_count",
            "expected_v2_chunk_count",
            "extracted_v2_chunk_count",
            "missing_v2_chunk_count",
            "is_fully_extracted_v2",
            "has_valid_insights_v2",
            "insights_v2_count",
            "run_id",
            "route",
            "model",
            "prompt_version",
            "generated_at",
            "run_chunk_count",
            "estimated_usd",
            "cost_notes",
            "source_file",
        ],
    )
    write_csv(
        args.output_dir / "insights_v2_title_distribution.csv",
        title_distribution_rows(insights_v2),
        ["title", "normalized_title", "count", "percent", "is_repeated_over_5_percent"],
    )
    write_csv(
        args.output_dir / "acquisition_tasks_master.csv",
        acquisition_tasks,
        [
            "task_id",
            "episode_video_id",
            "episode_title",
            "referenced_asset_id",
            "asset_type_guess",
            "task_type",
            "instruction",
            "status",
            "priority",
            "mention_start_seconds",
            "mention_quote_original",
            "expected_value",
            "user_notes",
            "result_asset_id",
            "source_file",
        ],
    )

    print(
        "Consolidated "
        f"{len(episodes)} episode(s), {len(assets)} asset(s), "
        f"{len(insights)} v1 insight(s), {len(insights_v2)} v2 insight(s), "
        f"and {len(acquisition_tasks)} acquisition task(s)."
    )
    if insights_v2_validation_errors:
        print(f"warning_invalid_insights_v2_files={len(insights_v2_validation_errors)}")
    print(
        "R07 v2 coverage: "
        f"{insights_v2_status['target_valid_v2_episode_count']}/{args.r07_target_episode_count} target episode(s) with v2, "
        f"{insights_v2_status['fully_extracted_v2_episode_count']}/{args.r07_target_episode_count} fully extracted, "
        f"{insights_v2_status['target_extracted_v2_chunk_count']}/{insights_v2_status['target_expected_chunk_count']} target chunk(s), "
        f"gate_r1_ready={insights_v2_status['gate_r1_ready']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
