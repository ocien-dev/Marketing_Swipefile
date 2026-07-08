#!/usr/bin/env python
"""Prepare Codex extraction packets for every chunk in a chunk index."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from msf_common import repo_data_path
from prepare_extraction_packet import EXTRACTOR_FILES, load_json, read_text, render_packet


def parse_extractors(value: str) -> list[str]:
    extractors = [extractor.strip() for extractor in value.split(",") if extractor.strip()]
    unknown = sorted(set(extractors) - set(EXTRACTOR_FILES))
    if unknown:
        raise ValueError(f"Unknown extractor(s): {', '.join(unknown)}")
    return extractors


def metadata_for_chunk(metadata: dict[str, Any] | None, chunk: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(metadata) if metadata else {}
    payload["extraction_chunk"] = {
        "chunk_id": chunk["chunk_id"],
        "chunk_index": chunk["chunk_index"],
        "title": chunk["title"],
        "chapter_title": chunk.get("chapter_title"),
        "part_index": chunk.get("part_index"),
        "start_seconds": chunk.get("start_seconds"),
        "end_seconds": chunk.get("end_seconds"),
        "segment_count": chunk.get("segment_count"),
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunk-index", required=True, type=Path, help="Path to chunk_index.json")
    parser.add_argument("--metadata", type=Path, help="Optional metadata.json")
    parser.add_argument("--extractors", default="vsl,ads", help="Comma-separated extractor names")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory for packet markdown files")
    parser.add_argument("--insights-dir", required=True, type=Path, help="Directory for expected insights JSON outputs")
    parser.add_argument("--taxonomy", default=repo_data_path("processed", "taxonomy_seed.json"), type=Path)
    parser.add_argument("--base-prompt", default=Path("prompts/extraction/base_insight_extraction.md"), type=Path)
    args = parser.parse_args()

    chunk_index = load_json(args.chunk_index)
    metadata = load_json(args.metadata) if args.metadata else None
    taxonomy = load_json(args.taxonomy) if args.taxonomy.exists() else None
    base_prompt = read_text(args.base_prompt)
    extractors = parse_extractors(args.extractors)

    packet_count = 0
    for extractor_name in extractors:
        extractor_prompt = read_text(Path(EXTRACTOR_FILES[extractor_name]))
        for chunk in chunk_index.get("chunks", []):
            chunk_file = Path(chunk["file"])
            segments = load_json(chunk_file)
            chunk_number = chunk["chunk_index"] + 1
            packet_path = args.output_dir / extractor_name / f"chunk_{chunk_number:03d}_packet.md"
            insights_path = args.insights_dir / extractor_name / f"chunk_{chunk_number:03d}_insights.json"
            packet = render_packet(
                base_prompt=base_prompt,
                extractor_prompt=extractor_prompt,
                segments=segments,
                metadata=metadata_for_chunk(metadata, chunk),
                taxonomy=taxonomy,
                output_path=insights_path,
                extractor_name=extractor_name,
            )
            packet_path.parent.mkdir(parents=True, exist_ok=True)
            packet_path.write_text(packet, encoding="utf-8", newline="\n")
            packet_count += 1

    print(f"Wrote {packet_count} chunked extraction packet(s) to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
