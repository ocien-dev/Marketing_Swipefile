#!/usr/bin/env python
"""Prepare a blind A/B package for output-level reviews.

This is intentionally prepare-only for MSF-R10. The external judge fills the
blind CSV; Codex must not score the package in the same session.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from msf_common import write_json, write_text


INSIGHT_ID_RE = re.compile(r"[A-Za-z0-9_-]+-(?:tr-insight|v2)-\d+")
BLIND_SECTION_HEADINGS = {
    "referencias usadas",
    "referencias",
    "registro de uso",
    "source notes",
    "evidence notes",
}

CRITERIA_BY_TYPE = {
    "vsl": [
        "clarity",
        "curiosity",
        "specificity",
        "mechanism",
        "proof",
        "objection_handling",
        "offer_bridge",
        "overall_quality",
    ],
    "ads": [
        "hook_strength",
        "angle_clarity",
        "avatar_fit",
        "proof_or_plausibility",
        "testability",
        "platform_fit",
        "creative_direction",
        "overall_quality",
    ],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_heading(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"^#+\s*", "", text)
    text = re.sub(r"[^a-z0-9 ]+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def blind_text(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    kept: list[str] = []
    skipping = False
    for line in lines:
        if line.startswith("## "):
            heading = normalize_heading(line)
            skipping = heading in BLIND_SECTION_HEADINGS
            if skipping:
                continue
        if skipping:
            continue
        kept.append(INSIGHT_ID_RE.sub("[source-ref]", line))
    return "\n".join(kept).strip() + "\n"


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def parse_pair_args(values: list[str]) -> list[dict[str, Any]]:
    pairs = []
    for value in values:
        parts = value.split("|")
        if len(parts) != 4:
            raise SystemExit("--pair must be artifact_type|with_base_path|baseline_path|briefing_id")
        artifact_type, with_base_path, baseline_path, briefing_id = parts
        if artifact_type not in CRITERIA_BY_TYPE:
            raise SystemExit(f"Unsupported artifact_type in --pair: {artifact_type}")
        pairs.append(
            {
                "artifact_type": artifact_type,
                "with_base_path": Path(with_base_path),
                "baseline_path": Path(baseline_path),
                "briefing_id": briefing_id,
            }
        )
    return pairs


def prepare(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rng = random.Random(str(args.seed or args.date))
    rows: list[dict[str, Any]] = []
    key_pairs: list[dict[str, Any]] = []
    for index, pair in enumerate(parse_pair_args(args.pair), start=1):
        pair_id = f"r10_pair_{index:03d}"
        sides = [
            ("with_base_v2", pair["with_base_path"]),
            ("baseline_no_base", pair["baseline_path"]),
        ]
        rng.shuffle(sides)
        side_a, side_b = sides
        criteria = CRITERIA_BY_TYPE[pair["artifact_type"]]
        row: dict[str, Any] = {
            "pair_id": pair_id,
            "artifact_type": pair["artifact_type"],
            "briefing_id": pair["briefing_id"],
            "a_output": blind_text(side_a[1]),
            "b_output": blind_text(side_b[1]),
            "judge_notes": "",
        }
        for criterion in criteria:
            row[f"judgment_{criterion}"] = ""
        rows.append(row)
        key_pairs.append(
            {
                "pair_id": pair_id,
                "artifact_type": pair["artifact_type"],
                "briefing_id": pair["briefing_id"],
                "sides": {
                    "A": {"source": side_a[0], "path": str(side_a[1])},
                    "B": {"source": side_b[0], "path": str(side_b[1])},
                },
                "criteria": criteria,
            }
        )
    key = {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "date": args.date,
        "seed": str(args.seed or args.date),
        "mode": "prepare_only",
        "pairs": key_pairs,
    }
    return rows, key


def render_pending_report(args: argparse.Namespace, key: dict[str, Any]) -> str:
    lines = [
        f"# Output R10 Blind Review - {args.date}",
        "",
        "## Scope",
        "",
        f"- Blind sample: `{args.blind_output}`",
        f"- Local de-anonymization key: `{args.key_output}`",
        f"- Pairs prepared: {len(key['pairs'])}",
        "- Source labels are hidden from the blind CSV.",
        "- Source/reference sections and raw `insight_id` values are stripped from blind output text.",
        "- This session prepared the package only; no R10 judgment or score was run.",
        "",
        "## Judge Instructions",
        "",
        "- Fill each `judgment_*` column with `A`, `B`, or `tie`.",
        "- Judge output quality only; do not infer which side used the base.",
        "- Use `judge_notes` for caveats, unsupported claims, or strong wins.",
        "",
        "## Decision",
        "",
        "- Pending external blind judgment.",
        "- Do not declare Gate R2 from this prepare package alone.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=datetime.now(timezone.utc).date().isoformat())
    parser.add_argument("--seed", default=None)
    parser.add_argument(
        "--pair",
        action="append",
        required=True,
        help="artifact_type|with_base_path|baseline_path|briefing_id",
    )
    parser.add_argument("--blind-output", type=Path, required=True)
    parser.add_argument("--key-output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    rows, key = prepare(args)
    max_criteria = sorted({criterion for pair in key["pairs"] for criterion in pair["criteria"]})
    fieldnames = ["pair_id", "artifact_type", "briefing_id", "a_output", "b_output"] + [
        f"judgment_{criterion}" for criterion in max_criteria
    ] + ["judge_notes"]
    write_csv(args.blind_output, rows, fieldnames)
    write_json(args.key_output, key)
    if args.report:
        write_text(args.report, render_pending_report(args, key))
    print(f"wrote_blind_sample={args.blind_output}")
    print(f"wrote_key={args.key_output}")
    if args.report:
        print(f"wrote_report={args.report}")
    print(f"pairs={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
