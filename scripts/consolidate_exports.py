#!/usr/bin/env python
"""Consolidate local Marketing Swipe File artifacts into master exports."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from msf_common import first_evidence, insight_text, load_json, normalize_text, slugify, write_json


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


def insight_key(insight: dict[str, Any]) -> str:
    dedupe_key = normalize_text(insight.get("dedupe_key"))
    if dedupe_key:
        return f"dedupe:{dedupe_key}"
    return f"text:{slugify(insight.get('title'))}:{slugify(insight.get('insight_ptbr'))}"


def quality_score(insight: dict[str, Any]) -> tuple[float, int, int]:
    confidence = insight.get("confidence_score")
    confidence_value = float(confidence) if isinstance(confidence, (int, float)) else 0.0
    return confidence_value, len(insight.get("evidence") or []), len(insight_text(insight))


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-youtube-root", default=Path("data/raw/youtube"), type=Path)
    parser.add_argument("--raw-assets-root", default=Path("data/raw/assets"), type=Path)
    parser.add_argument("--processed-root", default=Path("data/processed"), type=Path)
    parser.add_argument("--output-dir", default=Path("data/exports"), type=Path)
    parser.add_argument("--include-fixtures", action="store_true", help="Include local fixture episode ids in exports")
    args = parser.parse_args()

    episodes = collect_episodes(args.raw_youtube_root, args.include_fixtures)
    assets = collect_assets(args.raw_assets_root, args.include_fixtures)
    insights = collect_insights(args.processed_root, episodes, assets, args.include_fixtures)
    referenced_assets = collect_referenced_assets(args.processed_root, episodes, args.include_fixtures)
    acquisition_tasks = collect_acquisition_tasks(args.processed_root, referenced_assets, args.include_fixtures)
    generated_at = utc_now()

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
        f"{len(insights)} insight(s), and {len(acquisition_tasks)} acquisition task(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
