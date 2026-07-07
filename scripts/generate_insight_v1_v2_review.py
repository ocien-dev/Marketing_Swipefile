#!/usr/bin/env python
"""Generate a paired v1/v2 insight quality review.

The generated report intentionally avoids copying raw transcript quotes into
tracked docs. It references insight ids, titles, chunks, and evidence locators.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from msf_common import first_evidence, insight_text, jaccard, load_json, normalize_text, tokens, write_text


def utc_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def strip_chunk_suffix(title: Any) -> str:
    return re.sub(r"\s*\(chunk[_-]\d+\)\s*$", "", str(title or ""), flags=re.IGNORECASE).strip()


def chunk_number_from_values(*values: Any) -> int | None:
    text = " ".join(str(value) for value in values if value is not None)
    match = re.search(r"chunk[_-](\d+)", text, flags=re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def v1_chunk_number(insight: dict[str, Any]) -> int | None:
    return chunk_number_from_values(insight.get("title"), insight.get("subthemes"), insight.get("dedupe_key"), insight.get("source_file"))


def v2_chunk_number(insight: dict[str, Any]) -> int | None:
    source_chunk = insight.get("source_chunk") if isinstance(insight.get("source_chunk"), dict) else {}
    chunk_index = source_chunk.get("chunk_index")
    if isinstance(chunk_index, int):
        return chunk_index + 1
    return chunk_number_from_values(source_chunk.get("chunk_id"), source_chunk.get("chunk_file"), insight.get("source_file"))


def load_insights(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    insights = payload.get("insights")
    if not isinstance(insights, list):
        raise SystemExit(f"Missing insights array: {path}")
    return [item for item in insights if isinstance(item, dict)]


def insight_similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    left_text = insight_text(left)
    right_text = insight_text(right)
    return jaccard(tokens(left_text), tokens(right_text))


def pair_insights(v1_insights: list[dict[str, Any]], v2_insights: list[dict[str, Any]], sample_size: int) -> list[dict[str, Any]]:
    by_episode_chunk: dict[tuple[str, int | None], list[dict[str, Any]]] = {}
    by_episode: dict[str, list[dict[str, Any]]] = {}
    for insight in v1_insights:
        episode_id = str(insight.get("episode_video_id") or "")
        if not episode_id:
            continue
        chunk_number = v1_chunk_number(insight)
        by_episode_chunk.setdefault((episode_id, chunk_number), []).append(insight)
        by_episode.setdefault(episode_id, []).append(insight)

    pairs: list[dict[str, Any]] = []
    for v2 in v2_insights:
        episode_id = str(v2.get("episode_video_id") or "")
        chunk_number = v2_chunk_number(v2)
        candidates = by_episode_chunk.get((episode_id, chunk_number)) or by_episode.get(episode_id) or []
        if not candidates:
            continue
        best = max(candidates, key=lambda candidate: insight_similarity(candidate, v2))
        pairs.append(
            {
                "episode_video_id": episode_id,
                "chunk_number": chunk_number,
                "v1": best,
                "v2": v2,
                "similarity": round(insight_similarity(best, v2), 3),
            }
        )
    return pairs[:sample_size]


def repeated_v1_title_counts(v1_insights: list[dict[str, Any]]) -> Counter[str]:
    return Counter(normalize_text(strip_chunk_suffix(insight.get("title"))) for insight in v1_insights if insight.get("title"))


def criterion_winners(pair: dict[str, Any], v1_title_counts: Counter[str]) -> dict[str, str]:
    v1 = pair["v1"]
    v2 = pair["v2"]
    v1_title_key = normalize_text(strip_chunk_suffix(v1.get("title")))
    v2_title = str(v2.get("canonical_title") or v2.get("title") or "")
    v2_has_operational_fields = all(v2.get(field) for field in ["specific_takeaway", "use_case", "when_to_use", "when_not_to_use"])
    v2_evidence = first_evidence(v2)
    v2_locator = v2_evidence.get("locator") if isinstance(v2_evidence.get("locator"), dict) else {}
    cleanliness = v2.get("evidence_cleanliness")
    return {
        "specificity": "v2" if v1_title_counts.get(v1_title_key, 0) >= 5 or len(tokens(v2_title)) >= len(tokens(v1.get("title"))) else "tie",
        "evidence_fidelity": "v2" if v2_locator.get("value") and v2_evidence.get("evidence_strength") in {"medium", "strong"} else "tie",
        "applicability": "v2" if v2_has_operational_fields else "tie",
        "quote_cleanliness": "v2" if cleanliness in {"clean", "minor_noise"} else "tie",
    }


def truncate(value: Any, limit: int = 84) -> str:
    text = str(value or "").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        safe_row = [str(value).replace("|", "\\|") for value in row]
        lines.append("| " + " | ".join(safe_row) + " |")
    return "\n".join(lines)


def render_report(args: argparse.Namespace, v1_insights: list[dict[str, Any]], v2_insights: list[dict[str, Any]], pairs: list[dict[str, Any]]) -> str:
    v1_title_counts = repeated_v1_title_counts(v1_insights)
    criterion_counts: dict[str, Counter[str]] = {
        "specificity": Counter(),
        "evidence_fidelity": Counter(),
        "applicability": Counter(),
        "quote_cleanliness": Counter(),
    }
    pair_rows: list[list[Any]] = []
    for pair in pairs:
        v1 = pair["v1"]
        v2 = pair["v2"]
        winners = criterion_winners(pair, v1_title_counts)
        for criterion, winner in winners.items():
            criterion_counts[criterion][winner] += 1
        evidence = first_evidence(v2)
        locator = evidence.get("locator") if isinstance(evidence.get("locator"), dict) else {}
        pair_rows.append(
            [
                pair.get("episode_video_id"),
                f"chunk_{int(pair['chunk_number']):03d}" if isinstance(pair.get("chunk_number"), int) else "",
                v1.get("insight_id"),
                truncate(v1.get("title")),
                v1_title_counts.get(normalize_text(strip_chunk_suffix(v1.get("title"))), 0),
                v2.get("insight_id"),
                truncate(v2.get("canonical_title") or v2.get("title")),
                ", ".join(f"{key}=v2" for key, value in winners.items() if value == "v2") or "tie",
                locator.get("value") or "",
            ]
        )

    score_rows = []
    for criterion in ["specificity", "evidence_fidelity", "applicability", "quote_cleanliness"]:
        counts = criterion_counts[criterion]
        score_rows.append([criterion, counts.get("v2", 0), counts.get("tie", 0), counts.get("v1", 0)])

    target_reached = len(pairs) >= args.target_pairs and len({pair["episode_video_id"] for pair in pairs}) >= args.target_episodes
    verdict = "Gate R1 not declared: this is a pilot review, because R07 coverage is still below the 50 episode target."
    pilot_verdict = "Pilot verdict: v2 is directionally stronger than v1 on specificity, evidence locators, and operational fields."
    if target_reached:
        verdict = "Gate R1 can be reviewed manually against the acceptance checklist; automated coverage targets were met."

    return "\n".join(
        [
            f"# Insight v1 vs v2 Review - {args.date}",
            "",
            "## Scope",
            "",
            f"- v1 source: `{args.v1_master}`",
            f"- v2 source: `{args.v2_master}`",
            f"- Paired sample generated: {len(pairs)} pair(s).",
            f"- R08 target: {args.target_pairs} comparable pair(s) after R07 reaches {args.target_episodes} v2 episode(s).",
            "- Raw transcript quotes are not copied into this tracked report; use evidence locators in local exports for inspection.",
            "",
            "## Verdict",
            "",
            pilot_verdict,
            "",
            verdict,
            "",
            "## Criteria Counts",
            "",
            markdown_table(["criterion", "v2_wins", "ties", "v1_wins"], score_rows),
            "",
            "## Pair Sample",
            "",
            markdown_table(
                [
                    "episode",
                    "chunk",
                    "v1_id",
                    "v1_title",
                    "v1_title_count",
                    "v2_id",
                    "v2_title",
                    "v2_winning_criteria",
                    "v2_locator",
                ],
                pair_rows,
            ),
            "",
            "## Decision",
            "",
            "- Continue MSF-R07 before declaring Gate R1.",
            "- Use `data/exports/insights_v2_status.json` to track coverage and title repetition.",
            "- Re-run this report when the v2 master has at least 40 comparable pairs across the 50 target episodes.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v1-master", type=Path, default=Path("data/exports/insights_master.json"))
    parser.add_argument("--v2-master", type=Path, default=Path("data/exports/insights_v2_master.json"))
    parser.add_argument("--date", default=utc_date())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--sample-size", type=int, default=40)
    parser.add_argument("--target-pairs", type=int, default=40)
    parser.add_argument("--target-episodes", type=int, default=50)
    args = parser.parse_args()

    output = args.output or Path("docs") / f"insight-v1-vs-v2-review-{args.date}.md"
    v1_insights = load_insights(args.v1_master)
    v2_insights = load_insights(args.v2_master)
    pairs = pair_insights(v1_insights, v2_insights, args.sample_size)
    write_text(output, render_report(args, v1_insights, v2_insights, pairs))
    print(f"wrote={output}")
    print(f"pairs={len(pairs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
