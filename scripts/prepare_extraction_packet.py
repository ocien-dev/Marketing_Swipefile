#!/usr/bin/env python
"""Prepare a manual Codex extraction packet from content segments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from msf_common import repo_data_path


EXTRACTOR_FILES = {
    "copy": "prompts/extraction/copy_extractor.md",
    "vsl": "prompts/extraction/vsl_extractor.md",
    "ads": "prompts/extraction/ads_extractor.md",
    "offer": "prompts/extraction/offer_extractor.md",
    "funnel": "prompts/extraction/funnel_extractor.md",
    "ops": "prompts/extraction/ops_extractor.md",
    "asset": "prompts/extraction/asset_extractor.md",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def render_packet(
    base_prompt: str,
    extractor_prompt: str,
    segments: dict[str, Any],
    metadata: dict[str, Any] | None,
    taxonomy: dict[str, Any] | None,
    output_path: Path,
    extractor_name: str,
) -> str:
    packet = [
        "# Marketing Swipe File Extraction Packet",
        "",
        "## Task",
        "",
        f"Use the `{extractor_name}` extractor to generate an `insights.json` file.",
        "",
        "Return only JSON matching `schemas/insights.schema.json`.",
        "",
        f"Write the final JSON to: `{output_path}`",
        "",
        "## Base Prompt",
        "",
        base_prompt,
        "",
        "## Specialized Extractor Prompt",
        "",
        extractor_prompt,
        "",
    ]

    if metadata is not None:
        packet.extend(
            [
                "## Metadata",
                "",
                "```json",
                json.dumps(metadata, ensure_ascii=True, indent=2),
                "```",
                "",
            ]
        )

    if taxonomy is not None:
        compact_terms = [
            {
                "id": term.get("id"),
                "term": term.get("term"),
                "term_type": term.get("term_type"),
                "parent_id": term.get("parent_id"),
                "synonyms": term.get("synonyms", []),
            }
            for term in taxonomy.get("terms", [])
        ]
        packet.extend(
            [
                "## Taxonomy Seed",
                "",
                "```json",
                json.dumps({"terms": compact_terms}, ensure_ascii=True, indent=2),
                "```",
                "",
            ]
        )

    packet.extend(
        [
            "## Content Segments",
            "",
            "```json",
            json.dumps(segments, ensure_ascii=True, indent=2),
            "```",
            "",
            "## Reminder",
            "",
            "- Every insight needs evidence.",
            "- Keep quotes exact.",
            "- Prefer specific, actionable insights.",
            "- Use stable ids and dedupe keys.",
            "",
        ]
    )
    return "\n".join(packet)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--segments", required=True, type=Path, help="Path to content_segments.json")
    parser.add_argument("--extractor", required=True, choices=sorted(EXTRACTOR_FILES), help="Extractor focus")
    parser.add_argument("--output-packet", required=True, type=Path, help="Path to write extraction packet markdown")
    parser.add_argument("--output-insights", required=True, type=Path, help="Expected insights.json output path")
    parser.add_argument("--metadata", type=Path, help="Optional metadata.json")
    parser.add_argument("--taxonomy", default=repo_data_path("processed", "taxonomy_seed.json"), type=Path)
    parser.add_argument("--base-prompt", default=Path("prompts/extraction/base_insight_extraction.md"), type=Path)
    args = parser.parse_args()

    segments = load_json(args.segments)
    metadata = load_json(args.metadata) if args.metadata else None
    taxonomy = load_json(args.taxonomy) if args.taxonomy.exists() else None
    base_prompt = read_text(args.base_prompt)
    extractor_prompt = read_text(Path(EXTRACTOR_FILES[args.extractor]))

    packet = render_packet(
        base_prompt=base_prompt,
        extractor_prompt=extractor_prompt,
        segments=segments,
        metadata=metadata,
        taxonomy=taxonomy,
        output_path=args.output_insights,
        extractor_name=args.extractor,
    )
    args.output_packet.parent.mkdir(parents=True, exist_ok=True)
    args.output_packet.write_text(packet, encoding="utf-8", newline="\n")
    print(f"Wrote extraction packet to {args.output_packet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
