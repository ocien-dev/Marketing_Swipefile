#!/usr/bin/env python
"""Generate episode and asset markdown summaries from local artifacts."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from msf_common import as_list, first_evidence, load_json, write_text


def safe_load(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return load_json(path)


def load_episode_insights(processed_dir: Path) -> list[dict[str, Any]]:
    insights: list[dict[str, Any]] = []
    direct = safe_load(processed_dir / "insights.json")
    if direct:
        insights.extend(item for item in direct.get("insights", []) if isinstance(item, dict))
    for path in sorted(processed_dir.glob("chunked_insights/*/*_insights.json")):
        payload = load_json(path)
        insights.extend(item for item in payload.get("insights", []) if isinstance(item, dict))
    return insights


def top_counts(items: list[str], limit: int = 8) -> list[tuple[str, int]]:
    return Counter(item for item in items if item).most_common(limit)


def render_episode_summary(video_id: str, raw_dir: Path, processed_dir: Path) -> str:
    metadata = safe_load(raw_dir / "metadata.json") or {}
    segments = safe_load(processed_dir / "content_segments.json") or {}
    referenced_assets = safe_load(processed_dir / "referenced_assets.json") or {"referenced_assets": []}
    tasks = safe_load(processed_dir / "acquisition_tasks.json") or {"tasks": []}
    chunk_index = safe_load(processed_dir / "chunks" / "chunk_index.json") or {"chunks": []}
    insights = load_episode_insights(processed_dir)

    theme_counts = top_counts([theme for insight in insights for theme in as_list(insight.get("themes"))])
    type_counts = top_counts([str(insight.get("insight_type") or "") for insight in insights])
    pending_tasks = [task for task in tasks.get("tasks", []) if task.get("status") in {"pending", "in_progress"}]

    lines = [
        f"# Episode Summary - {video_id}",
        "",
        f"- Title: {metadata.get('title') or 'N/A'}",
        f"- Channel: {metadata.get('channel_name') or 'N/A'}",
        f"- URL: {metadata.get('url') or 'N/A'}",
        f"- Duration seconds: {metadata.get('duration_seconds') or 'N/A'}",
        f"- Transcript segments: {len(segments.get('segments', []))}",
        f"- Extraction chunks: {len(chunk_index.get('chunks', []))}",
        f"- Referenced assets: {len(referenced_assets.get('referenced_assets', []))}",
        f"- Acquisition tasks: {len(tasks.get('tasks', []))}",
        f"- Insights: {len(insights)}",
        "",
        "## Top Themes",
        "",
    ]
    if theme_counts:
        lines.extend(f"- {theme}: {count}" for theme, count in theme_counts)
    else:
        lines.append("- No insights classified yet.")
    lines.extend(["", "## Insight Types", ""])
    if type_counts:
        lines.extend(f"- {insight_type}: {count}" for insight_type, count in type_counts)
    else:
        lines.append("- No insights extracted yet.")

    lines.extend(["", "## Top Insights", ""])
    for insight in sorted(insights, key=lambda item: float(item.get("confidence_score") or 0), reverse=True)[:10]:
        evidence = first_evidence(insight)
        lines.extend(
            [
                f"### {insight.get('insight_id')} - {insight.get('title')}",
                "",
                f"- Level/type: {insight.get('level')} / {insight.get('insight_type')}",
                f"- Confidence: {insight.get('confidence_score')}",
                f"- Themes: {', '.join(str(theme) for theme in as_list(insight.get('themes')))}",
                "",
                str(insight.get("insight_ptbr") or ""),
                "",
                f"> {evidence.get('quote_original', '')}",
                "",
            ]
        )
    if not insights:
        lines.append("- Extraction not completed yet.")
        lines.append("")

    lines.extend(["## Pending Manual Actions", ""])
    if pending_tasks:
        for task in pending_tasks:
            lines.append(f"- {task.get('priority')}: {task.get('instruction')} ({task.get('task_id')})")
    else:
        lines.append("- No pending manual acquisition tasks.")
    lines.extend(["", "## Next Actions", ""])
    if not insights:
        lines.append("- Run chunk-level extraction packets and save insights before strategy pack generation.")
    if pending_tasks:
        lines.append("- Obtain or mark pending complementary materials before the 20-episode MVP gate.")
    if insights:
        lines.append("- Run dedupe, taxonomy classification, consolidation, and local retrieval.")
    lines.append("")
    return "\n".join(lines)


def render_asset_summary(asset_id: str, raw_dir: Path, processed_dir: Path) -> str:
    metadata = safe_load(raw_dir / "metadata.json") or {}
    segments = safe_load(processed_dir / "content_segments.json") or {"segments": []}
    insights_payload = safe_load(processed_dir / "insights.json") or {"insights": []}
    insights = [item for item in insights_payload.get("insights", []) if isinstance(item, dict)]
    lines = [
        f"# Asset Summary - {asset_id}",
        "",
        f"- Episode video ID: {metadata.get('episode_video_id') or 'N/A'}",
        f"- Filename: {metadata.get('original_filename') or 'N/A'}",
        f"- Asset type: {metadata.get('asset_type') or 'N/A'}",
        f"- Checksum: {metadata.get('checksum') or 'N/A'}",
        f"- Segments: {len(segments.get('segments', []))}",
        f"- Insights: {len(insights)}",
        "",
        "## Segment Preview",
        "",
    ]
    for segment in segments.get("segments", [])[:5]:
        locator = segment.get("page_number") or segment.get("cell_range") or segment.get("slide_number") or segment.get("section_title")
        lines.append(f"- {locator or segment.get('segment_id')}: {str(segment.get('text_original') or '')[:240]}")
    if not segments.get("segments"):
        lines.append("- No segments extracted yet.")
    lines.extend(["", "## Top Insights", ""])
    for insight in sorted(insights, key=lambda item: float(item.get("confidence_score") or 0), reverse=True)[:10]:
        lines.append(f"- {insight.get('insight_id')}: {insight.get('title')} ({insight.get('confidence_score')})")
    if not insights:
        lines.append("- No asset insights extracted yet.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", help="Episode video id to summarize")
    parser.add_argument("--asset", help="Asset id to summarize")
    parser.add_argument("--all", action="store_true", help="Summarize all discovered episodes and assets")
    parser.add_argument("--raw-youtube-root", default=Path("data/raw/youtube"), type=Path)
    parser.add_argument("--raw-assets-root", default=Path("data/raw/assets"), type=Path)
    parser.add_argument("--processed-root", default=Path("data/processed"), type=Path)
    args = parser.parse_args()

    wrote = 0
    if args.episode or args.all:
        episode_ids = [args.episode] if args.episode else [path.name for path in sorted(args.raw_youtube_root.iterdir()) if path.is_dir()]
        for video_id in episode_ids:
            processed_dir = args.processed_root / video_id
            raw_dir = args.raw_youtube_root / video_id
            if not raw_dir.exists() and not processed_dir.exists():
                continue
            write_text(processed_dir / "episode_summary.md", render_episode_summary(video_id, raw_dir, processed_dir))
            wrote += 1

    if args.asset or args.all:
        asset_ids = [args.asset] if args.asset else [path.name for path in sorted(args.raw_assets_root.iterdir()) if path.is_dir()]
        for asset_id in asset_ids:
            processed_dir = args.processed_root / "assets" / asset_id
            raw_dir = args.raw_assets_root / asset_id
            if not raw_dir.exists() and not processed_dir.exists():
                continue
            write_text(processed_dir / "asset_summary.md", render_asset_summary(asset_id, raw_dir, processed_dir))
            wrote += 1

    print(f"Wrote {wrote} summary file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

