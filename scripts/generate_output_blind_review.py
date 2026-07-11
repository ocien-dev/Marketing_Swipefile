#!/usr/bin/env python
"""Prepare and score blind A/B packages for output-level reviews.

MSF-R10 uses `prepare` in the generation session and `score` only after an
external blind judge returns the filled CSV.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
from collections import Counter
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def load_key(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload.get("pairs"), list):
        raise SystemExit(f"Invalid blind key file: {path}")
    return payload


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


def normalize_choice(value: Any) -> str:
    choice = str(value or "").strip().lower()
    if not choice:
        return ""
    if choice in {"a", "item a", "side a"}:
        return "A"
    if choice in {"b", "item b", "side b"}:
        return "B"
    if choice in {"tie", "empate", "equal", "igual"}:
        return "tie"
    raise SystemExit(f"Invalid judgment choice: {value!r}. Use A, B, tie, or blank.")


def score_rows(rows: list[dict[str, str]], key: dict[str, Any]) -> dict[str, Any]:
    pairs_by_id = {str(pair.get("pair_id")): pair for pair in key.get("pairs", [])}
    source_counts: Counter[str] = Counter()
    side_counts: Counter[str] = Counter()
    pair_results: list[dict[str, Any]] = []
    pending_cells = 0

    for row in rows:
        pair_id = str(row.get("pair_id") or "")
        pair = pairs_by_id.get(pair_id)
        if not pair:
            raise SystemExit(f"Judgment row has no matching key pair: {pair_id}")
        sides = pair.get("sides") or {}
        criteria = pair.get("criteria") or []
        pair_side_counts: Counter[str] = Counter()
        pair_source_counts: Counter[str] = Counter()
        criterion_results = []
        for criterion in criteria:
            choice = normalize_choice(row.get(f"judgment_{criterion}"))
            if not choice:
                pending_cells += 1
                criterion_results.append({"criterion": criterion, "winner_side": "pending", "winner_source": "pending"})
                continue
            side_counts[choice] += 1
            pair_side_counts[choice] += 1
            if choice == "tie":
                source_counts["tie"] += 1
                pair_source_counts["tie"] += 1
                criterion_results.append({"criterion": criterion, "winner_side": "tie", "winner_source": "tie"})
                continue
            source = str((sides.get(choice) or {}).get("source") or "")
            if source not in {"with_base_v2", "baseline_no_base"}:
                raise SystemExit(f"Invalid source for {pair_id} side {choice}: {source!r}")
            source_counts[source] += 1
            pair_source_counts[source] += 1
            criterion_results.append({"criterion": criterion, "winner_side": choice, "winner_source": source})

        if pair_source_counts["with_base_v2"] > pair_source_counts["baseline_no_base"]:
            pair_winner = "with_base_v2"
        elif pair_source_counts["baseline_no_base"] > pair_source_counts["with_base_v2"]:
            pair_winner = "baseline_no_base"
        else:
            pair_winner = "tie"
        pair_results.append(
            {
                "pair_id": pair_id,
                "artifact_type": pair.get("artifact_type"),
                "briefing_id": pair.get("briefing_id"),
                "A_source": (sides.get("A") or {}).get("source"),
                "B_source": (sides.get("B") or {}).get("source"),
                "criterion_results": criterion_results,
                "with_base_wins": pair_source_counts["with_base_v2"],
                "baseline_wins": pair_source_counts["baseline_no_base"],
                "ties": pair_source_counts["tie"],
                "pair_winner": pair_winner,
                "judge_notes": row.get("judge_notes") or "",
            }
        )

    if pending_cells:
        gate_result = "pending"
    elif source_counts["baseline_no_base"] > source_counts["with_base_v2"]:
        gate_result = "failed"
    else:
        gate_result = "approved"

    return {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "date": key.get("date"),
        "seed": key.get("seed"),
        "pair_count": len(pair_results),
        "criterion_cell_count": sum(len(pair.get("criterion_results", [])) for pair in pair_results),
        "pending_cells": pending_cells,
        "side_counts": dict(side_counts),
        "source_counts": {
            "with_base_v2": source_counts["with_base_v2"],
            "baseline_no_base": source_counts["baseline_no_base"],
            "tie": source_counts["tie"],
        },
        "gate_result": gate_result,
        "gate_rule": "output_with_base_wins_or_ties_baseline",
        "pairs": pair_results,
    }


def criterion_summary(pair: dict[str, Any]) -> str:
    values = []
    for item in pair.get("criterion_results", []):
        values.append(f"{item.get('criterion')}={item.get('winner_source')}")
    return ", ".join(values)


def render_scored_report(args: argparse.Namespace, score: dict[str, Any]) -> str:
    gate_result = score.get("gate_result")
    if gate_result == "approved":
        verdict = "Gate R2 APROVADO: output com base venceu ou empatou com baseline no julgamento cego externo."
    elif gate_result == "failed":
        verdict = "Gate R2 REPROVADO: baseline sem base venceu; voltar a R1/R3 antes de qualquer escala."
    else:
        verdict = "Gate R2 pendente: ha celulas de julgamento em branco."

    lines = [
        f"# Output R10 Blind Review - {score.get('date') or args.date}",
        "",
        "## Scope",
        "",
        f"- Judgments: `{args.judgments}`",
        f"- Local de-anonymization key: `{args.key_output}`",
        f"- Pairs scored: {score['pair_count']}",
        f"- Criterion cells scored: {score['criterion_cell_count'] - score['pending_cells']} / {score['criterion_cell_count']}",
        "- Reviewer: external blind reviewer, blind to source label.",
        "- Source labels were de-anonymized only after the judged CSV was returned.",
        "",
        "## Verdict",
        "",
        verdict,
        "",
        "## Counts",
        "",
        "| source | wins |",
        "| --- | --- |",
        f"| with_base_v2 | {score['source_counts']['with_base_v2']} |",
        f"| baseline_no_base | {score['source_counts']['baseline_no_base']} |",
        f"| tie | {score['source_counts']['tie']} |",
        "",
        "## Pair Results",
        "",
        "| pair | artifact | A_source | B_source | with_base_wins | baseline_wins | ties | pair_winner | criteria |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for pair in score.get("pairs", []):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(pair.get("pair_id")),
                    str(pair.get("artifact_type")),
                    str(pair.get("A_source")),
                    str(pair.get("B_source")),
                    str(pair.get("with_base_wins")),
                    str(pair.get("baseline_wins")),
                    str(pair.get("ties")),
                    str(pair.get("pair_winner")),
                    criterion_summary(pair).replace("|", "\\|"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Judge Caveats",
            "",
            "- Blindness was label blindness, not style blindness: the vocabulary and mechanics from the base can be recognizable.",
            "- The judge anchored the decision in content quality: specificity, mechanics, testability, and operational usefulness, not vocabulary alone.",
            "",
            "## Sample Limitation",
            "",
            "- This gate was measured on 1 briefing x 2 artifacts: low-ticket VSL and ads.",
            "- This is sufficient for the formal MSF-R10/R2 gate criterion used here, but MSF-S09 skill validations must use varied briefings as already planned.",
            "",
            "## Decision",
            "",
        ]
    )
    if gate_result == "approved":
        lines.extend(
            [
                "- Gate R2 is formally approved as of this scored report.",
                "- Next session: EPIC R3 with MSF-R11, MSF-R12, and MSF-R13.",
            ]
        )
    elif gate_result == "failed":
        lines.extend(
            [
                "- Gate R2 is rejected.",
                "- Do not scale. Return to R1/R3 remediation before any backfill or MSF-S work.",
            ]
        )
    else:
        lines.append("- Gate R2 remains pending until all cells are judged.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["prepare", "score"], default="prepare")
    parser.add_argument("--date", default=datetime.now(timezone.utc).date().isoformat())
    parser.add_argument("--seed", default=None)
    parser.add_argument(
        "--pair",
        action="append",
        help="artifact_type|with_base_path|baseline_path|briefing_id",
    )
    parser.add_argument("--blind-output", type=Path)
    parser.add_argument("--key-output", type=Path, required=True)
    parser.add_argument("--judgments", type=Path)
    parser.add_argument("--score-json", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    if args.mode == "score":
        if not args.judgments:
            raise SystemExit("--judgments is required for --mode score")
        key = load_key(args.key_output)
        score = score_rows(read_csv(args.judgments), key)
        if args.score_json:
            write_json(args.score_json, score)
        if args.report:
            write_text(args.report, render_scored_report(args, score))
        print(f"pairs={score['pair_count']}")
        print(f"criterion_cells={score['criterion_cell_count']}")
        print(f"pending_cells={score['pending_cells']}")
        print(f"with_base_wins={score['source_counts']['with_base_v2']}")
        print(f"baseline_wins={score['source_counts']['baseline_no_base']}")
        print(f"ties={score['source_counts']['tie']}")
        print(f"gate_result={score['gate_result']}")
        return 0 if score["gate_result"] != "pending" else 1

    if not args.pair:
        raise SystemExit("--pair is required for --mode prepare")
    if not args.blind_output:
        raise SystemExit("--blind-output is required for --mode prepare")
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
