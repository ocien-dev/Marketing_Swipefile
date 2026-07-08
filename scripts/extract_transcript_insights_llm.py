#!/usr/bin/env python
"""Codex-first extraction helper for raw_insights_v2.

This script intentionally does not call an LLM API yet. It prepares chunk
packets for Codex/manual review and merges validated chunk outputs into the
canonical `{MSF_DATA_DIR or repo/data}/processed/{video_id}/insights_v2.json` file.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from msf_common import data_path, load_json, slugify, write_json, write_text
from validate_insights_v2 import validate_payload


PROMPT_PATH = Path("prompts/extraction/base_insight_extraction_v2.md")
SCHEMA_PATH = Path("schemas/insights_v2.schema.json")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_chunk_selector(value: str | None) -> set[str] | None:
    if not value:
        return None
    selected: set[str] = set()
    for item in value.split(","):
        token = item.strip()
        if not token:
            continue
        if token.isdigit():
            selected.add(f"{int(token):03d}")
            selected.add(str(int(token)))
        else:
            selected.add(token)
    return selected


def chunk_matches(chunk: dict[str, Any], selected: set[str] | None) -> bool:
    if selected is None:
        return True
    file_stem = Path(str(chunk.get("file", ""))).stem.replace("chunk_", "")
    chunk_number = str(int(chunk.get("chunk_index", -1)) + 1) if isinstance(chunk.get("chunk_index"), int) else ""
    candidates = {
        str(chunk.get("chunk_id")),
        chunk_number,
        f"{int(chunk_number):03d}" if chunk_number.isdigit() else "",
        file_stem,
    }
    return bool(candidates & selected)


def load_chunk_index(video_id: str, processed_root: Path) -> dict[str, Any]:
    path = processed_root / video_id / "chunks" / "chunk_index.json"
    if not path.exists():
        raise SystemExit(f"Missing chunk index: {path}")
    return load_json(path)


def render_segments(chunk_payload: dict[str, Any]) -> str:
    lines: list[str] = []
    for segment in chunk_payload.get("segments", []):
        start = segment.get("start_seconds")
        end = segment.get("end_seconds")
        text = segment.get("text_original") or segment.get("text_ptbr") or ""
        lines.append(f"[{segment.get('segment_id')} {start}-{end}] {text}")
    return "\n".join(lines)


def prepare_packets(args: argparse.Namespace) -> int:
    chunk_index = load_chunk_index(args.video_id, args.processed_root)
    metadata_path = args.raw_youtube_root / args.video_id / "metadata.json"
    metadata = load_json(metadata_path) if metadata_path.exists() else {}
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    selected = parse_chunk_selector(args.chunks)
    output_dir = args.output_dir or args.processed_root / args.video_id / "llm_v2_packets"
    output_dir.mkdir(parents=True, exist_ok=True)

    prepared = 0
    for chunk in chunk_index.get("chunks", []):
        if not chunk_matches(chunk, selected):
            continue
        chunk_path = Path(str(chunk["file"]))
        if not chunk_path.exists():
            chunk_path = args.processed_root / args.video_id / "chunks" / chunk_path.name
        chunk_payload = load_json(chunk_path)
        chunk_number = int(chunk.get("chunk_index", 0)) + 1
        packet = f"""# raw_insights_v2 Codex Packet

Video ID: `{args.video_id}`
Episode title: {metadata.get("title", "")}
Chunk ID: `{chunk.get("chunk_id")}`
Chunk title: {chunk.get("title")}
Chunk file: `{chunk.get("file")}`
Time range: {chunk.get("start_seconds")} - {chunk.get("end_seconds")}
Max insights for this chunk: {args.max_insights_per_chunk}

## Extraction Prompt

{prompt}

## Chunk Segments

```text
{render_segments(chunk_payload)}
```
"""
        write_text(output_dir / f"chunk_{chunk_number:03d}_packet.md", packet)
        prepared += 1
    print(f"prepared_packets={prepared}")
    print(f"output_dir={output_dir}")
    return 0


def load_chunk_output(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    insights = payload.get("insights")
    if not isinstance(insights, list):
        raise SystemExit(f"Chunk output has no insights array: {path}")
    return insights


def chunk_id_from_output_path(path: Path, chunk_index: dict[str, Any]) -> str | None:
    payload = load_json(path)
    chunk_id = payload.get("chunk_id")
    if isinstance(chunk_id, str) and chunk_id:
        return chunk_id
    stem = path.stem.replace("_insights", "")
    if stem.startswith("chunk_"):
        suffix = stem.replace("chunk_", "", 1)
        if suffix.isdigit():
            chunk_number = int(suffix)
            for chunk in chunk_index.get("chunks", []):
                if int(chunk.get("chunk_index", -1)) + 1 == chunk_number:
                    candidate = chunk.get("chunk_id")
                    return str(candidate) if candidate else None
    return None


def source_chunk_sort_key(insight: dict[str, Any]) -> tuple[int, str]:
    source_chunk = insight.get("source_chunk") or {}
    chunk_index = source_chunk.get("chunk_index")
    if not isinstance(chunk_index, int):
        chunk_index = 999999
    return chunk_index, str(insight.get("insight_id", ""))


def combine_outputs(args: argparse.Namespace) -> int:
    chunk_index = load_chunk_index(args.video_id, args.processed_root)
    input_dir = args.input_dir or args.processed_root / args.video_id / "llm_v2_outputs"
    output_path = args.output or args.processed_root / args.video_id / "insights_v2.json"
    files = sorted(input_dir.glob("*.json"))
    if not files:
        raise SystemExit(f"No chunk output JSON files found in {input_dir}")

    merged: list[dict[str, Any]] = []
    seen_dedupe_keys: set[str] = set()
    seen_ids: set[str] = set()
    processed_chunk_ids: set[str] = set()
    for path in files:
        output_chunk_id = chunk_id_from_output_path(path, chunk_index)
        if output_chunk_id:
            processed_chunk_ids.add(output_chunk_id)
        for insight in load_chunk_output(path):
            dedupe_key = str(insight.get("dedupe_key", ""))
            insight_id = str(insight.get("insight_id", ""))
            if dedupe_key in seen_dedupe_keys or insight_id in seen_ids:
                continue
            seen_dedupe_keys.add(dedupe_key)
            seen_ids.add(insight_id)
            merged.append(insight)

    merged.sort(key=source_chunk_sort_key)
    input_chunk_ids = sorted(
        processed_chunk_ids
        | {
            str((insight.get("source_chunk") or {}).get("chunk_id"))
            for insight in merged
            if (insight.get("source_chunk") or {}).get("chunk_id")
        }
    )
    run_id = args.run_id or f"{args.video_id}-llm-v2-{slugify(args.route)}"
    payload: dict[str, Any] = {
        "schema_version": "2.0",
        "insight_layer": "raw_insights_v2",
        "episode_video_id": args.video_id,
        "asset_id": None,
        "extraction_run": {
            "run_id": run_id,
            "extraction_method": "llm_v2",
            "route": args.route,
            "model": args.model,
            "prompt_version": args.prompt_version,
            "generated_at": args.generated_at or utc_now(),
            "max_insights_per_chunk": args.max_insights_per_chunk,
            "chunk_count": len(input_chunk_ids),
            "input_chunk_ids": input_chunk_ids,
            "cost": {
                "input_tokens": args.input_tokens,
                "output_tokens": args.output_tokens,
                "estimated_usd": args.estimated_usd,
                "notes": args.cost_notes,
            },
        },
        "insights": merged,
    }

    errors = validate_payload(payload, SCHEMA_PATH)
    if errors:
        reprocess_path = output_path.with_name("insights_v2_reprocess_queue.json")
        write_json(
            reprocess_path,
            {
                "schema_version": "2.0",
                "episode_video_id": args.video_id,
                "errors": errors,
                "input_dir": str(input_dir),
            },
        )
        print(f"INVALID insights_v2 payload; wrote {reprocess_path}")
        for error in errors:
            print(f"- {error}")
        return 1

    # Ensure chunk_count reflects the source chunks available in the episode.
    known_chunks = {chunk.get("chunk_id") for chunk in chunk_index.get("chunks", [])}
    unknown_chunks = [chunk_id for chunk_id in input_chunk_ids if chunk_id not in known_chunks]
    if unknown_chunks:
        print(f"warning_unknown_chunks={','.join(unknown_chunks)}")

    write_json(output_path, payload)
    print(f"wrote={output_path}")
    print(f"insights={len(merged)}")
    print(f"chunks={len(input_chunk_ids)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    common: dict[str, Any] = {
        "processed_root": data_path("processed"),
        "raw_youtube_root": data_path("raw", "youtube"),
    }

    prepare = subparsers.add_parser("prepare", help="Prepare Codex packet files from transcript chunks.")
    prepare.add_argument("--video-id", required=True)
    prepare.add_argument("--processed-root", type=Path, default=common["processed_root"])
    prepare.add_argument("--raw-youtube-root", type=Path, default=common["raw_youtube_root"])
    prepare.add_argument("--chunks", help="Comma-separated chunk numbers, ids, or file suffixes.")
    prepare.add_argument("--output-dir", type=Path)
    prepare.add_argument("--max-insights-per-chunk", type=int, default=5)
    prepare.set_defaults(func=prepare_packets)

    combine = subparsers.add_parser("combine", help="Merge validated Codex chunk outputs into insights_v2.json.")
    combine.add_argument("--video-id", required=True)
    combine.add_argument("--processed-root", type=Path, default=common["processed_root"])
    combine.add_argument("--input-dir", type=Path)
    combine.add_argument("--output", type=Path)
    combine.add_argument("--route", choices=["codex_manual", "api"], default="codex_manual")
    combine.add_argument("--model", default="codex")
    combine.add_argument("--prompt-version", default="msf-r06-2026-07-07")
    combine.add_argument("--generated-at")
    combine.add_argument("--run-id")
    combine.add_argument("--max-insights-per-chunk", type=int, default=5)
    combine.add_argument("--input-tokens", type=int)
    combine.add_argument("--output-tokens", type=int)
    combine.add_argument("--estimated-usd", type=float, default=0)
    combine.add_argument("--cost-notes", default="Codex-first manual route; no external API billing.")
    combine.set_defaults(func=combine_outputs)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
