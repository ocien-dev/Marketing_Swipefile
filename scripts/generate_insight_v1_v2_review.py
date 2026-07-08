#!/usr/bin/env python
"""Prepare and score blind paired v1/v2 insight reviews.

The default `prepare` mode creates a randomized A/B CSV plus a local key file.
The judged CSV can later be passed to `score` to de-anonymize and compute the
v1/tie/v2 result. No automatic winner is inferred from v2 self-declared fields.
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

from msf_common import data_path, first_evidence, insight_text, jaccard, load_json, normalize_text, tokens, write_json, write_text


CRITERIA = ["specificity", "evidence_fidelity", "applicability", "quote_cleanliness"]
NOISE_PATTERNS = [
    ("subscribe_cta", re.compile(r"\b(inscreva|inscreva-se|se inscreva|inscrito|sininho)\b")),
    (
        "engagement_cta",
        re.compile(
            r"\b(deixa o like|deixem o like|da o like|dar o like|curte ai|curtir o video|"
            r"compartilha esse video|compartilhem esse video|comenta aqui|comentem aqui|"
            r"deixa [a-z0-9 ]{0,40}comentario|segue la|sigam la)\b"
        ),
    ),
    ("description_cta", re.compile(r"\b(link na descricao|descricao do video|acesse o link)\b")),
    ("watch_next", re.compile(r"\b(assista tambem|proximo video|video recomendado|continua assistindo)\b")),
    (
        "promo_training_pitch",
        re.compile(
            r"\b(imersao|call semanal|calls semanais|condicao especial|14 dias [a-z0-9 ]{0,20}gratis|15% de desconto|"
            r"te dar um treinamento|vou te dar um treinamento|treinamento gratuito|treinamento exclusivo|"
            r"receber [a-z0-9 ]{0,40}treinamento)\b"
        ),
    ),
    (
        "intro_narration",
        re.compile(
            r"\b(fala pessoal|sejam bem-vindos|nesse episodio|no episodio de hoje|"
            r"hoje a gente vai ter um episodio|e com voces|bem-vindo a mais um episodio)\b"
        ),
    ),
    ("closing_narration", re.compile(r"\bespero que (tu|voce|voces) goste[m]?\b")),
    ("hashtag", re.compile(r"#[a-z0-9_]+")),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
    return jaccard(tokens(insight_text(left)), tokens(insight_text(right)))


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


def collect_episode_titles(insights: list[dict[str, Any]]) -> dict[str, str]:
    titles: dict[str, str] = {}
    for insight in insights:
        episode_id = str(insight.get("episode_video_id") or "")
        title = str(insight.get("episode_title") or "")
        if episode_id and title:
            titles.setdefault(episode_id, title)
    return titles


def noise_flags(quote: Any, episode_id: str, episode_titles: dict[str, str]) -> list[str]:
    normalized = normalize_text(quote)
    flags = [name for name, pattern in NOISE_PATTERNS if pattern.search(normalized)]
    for other_episode_id, title in episode_titles.items():
        if other_episode_id == episode_id:
            continue
        normalized_title = normalize_text(title)
        if len(normalized_title) >= 30 and normalized_title in normalized:
            flags.append("other_episode_title")
            break
    return sorted(set(flags))


def list_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " | ".join(str(item) for item in value)
    return str(value)


def evidence_locator(evidence: dict[str, Any]) -> str:
    locator = evidence.get("locator") if isinstance(evidence.get("locator"), dict) else {}
    if locator.get("value"):
        return str(locator.get("value"))
    if evidence.get("segment_id"):
        return str(evidence.get("segment_id"))
    start = evidence.get("start_seconds")
    end = evidence.get("end_seconds")
    if start is not None or end is not None:
        return f"{start}-{end}"
    return ""


def blind_item(insight: dict[str, Any], episode_titles: dict[str, str]) -> dict[str, Any]:
    evidence = first_evidence(insight)
    episode_id = str(insight.get("episode_video_id") or evidence.get("episode_video_id") or "")
    quote = evidence.get("quote_original") or ""
    flags = noise_flags(quote, episode_id, episode_titles)
    operational_context = " | ".join(
        value
        for value in [
            str(insight.get("use_case") or ""),
            str(insight.get("when_to_use") or ""),
            str(insight.get("when_not_to_use") or ""),
            list_value(insight.get("applicability")),
            list_value(insight.get("funnel_stages")),
        ]
        if value
    )
    return {
        "title": strip_chunk_suffix(insight.get("canonical_title") or insight.get("title")),
        "takeaway": insight.get("specific_takeaway") or insight.get("insight_ptbr") or insight.get("summary_ptbr") or "",
        "operational_context": operational_context,
        "themes": list_value(insight.get("themes")),
        "evidence_quote": quote,
        "evidence_locator": evidence_locator(evidence),
        "quote_noise_count": len(flags),
        "quote_noise_flags": "|".join(flags),
    }


def side_fieldnames(side: str) -> list[str]:
    return [
        f"{side}_title",
        f"{side}_takeaway",
        f"{side}_operational_context",
        f"{side}_themes",
        f"{side}_evidence_quote",
        f"{side}_evidence_locator",
        f"{side}_quote_noise_count",
        f"{side}_quote_noise_flags",
    ]


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


def prepare_blind_sample(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    v1_insights = load_insights(args.v1_master)
    v2_insights = load_insights(args.v2_master)
    pairs = pair_insights(v1_insights, v2_insights, args.sample_size)
    episode_titles = {**collect_episode_titles(v1_insights), **collect_episode_titles(v2_insights)}
    rng = random.Random(str(args.seed or args.date))
    rows: list[dict[str, Any]] = []
    key_pairs: list[dict[str, Any]] = []

    for index, pair in enumerate(pairs, start=1):
        pair_id = f"pair_{index:03d}"
        side_versions = [("v1", pair["v1"]), ("v2", pair["v2"])]
        rng.shuffle(side_versions)
        row: dict[str, Any] = {
            "pair_id": pair_id,
            "episode_video_id": pair.get("episode_video_id"),
            "chunk": f"chunk_{int(pair['chunk_number']):03d}" if isinstance(pair.get("chunk_number"), int) else "",
            "similarity": pair.get("similarity"),
        }
        sides: dict[str, dict[str, Any]] = {}
        for side_name, (version, insight) in zip(["a", "b"], side_versions):
            item = blind_item(insight, episode_titles)
            for field, value in item.items():
                row[f"{side_name}_{field}"] = value
            sides[side_name.upper()] = {
                "version": version,
                "insight_id": insight.get("insight_id"),
                "source_file": insight.get("source_file"),
                "episode_video_id": insight.get("episode_video_id"),
                "chunk_number": v1_chunk_number(insight) if version == "v1" else v2_chunk_number(insight),
            }
        for criterion in CRITERIA:
            row[f"judgment_{criterion}"] = ""
        row["judge_notes"] = ""
        rows.append(row)
        key_pairs.append(
            {
                "pair_id": pair_id,
                "episode_video_id": pair.get("episode_video_id"),
                "chunk_number": pair.get("chunk_number"),
                "similarity": pair.get("similarity"),
                "sides": sides,
            }
        )

    key = {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "date": args.date,
        "seed": str(args.seed or args.date),
        "v1_master": str(args.v1_master),
        "v2_master": str(args.v2_master),
        "criteria": CRITERIA,
        "pairs": key_pairs,
    }
    return rows, key


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        safe_row = [str(value).replace("|", "\\|") for value in row]
        lines.append("| " + " | ".join(safe_row) + " |")
    return "\n".join(lines)


def render_pending_report(args: argparse.Namespace, pair_count: int) -> str:
    return "\n".join(
        [
            f"# Insight v1 vs v2 Review - {args.date}",
            "",
            "## Scope",
            "",
            f"- Blind sample: `{args.blind_output}`",
            f"- Local de-anonymization key: `{args.key_output}`",
            f"- Paired sample generated: {pair_count} pair(s).",
            f"- R08 target: {args.target_pairs} comparable pair(s) after R07 reaches {args.target_episodes} fully extracted v2 episode(s).",
            "- Raw transcript quotes are kept only in ignored local CSV exports, not copied into this tracked report.",
            "",
            "## Verdict",
            "",
            "Pending blind judgment. No v1/tie/v2 score has been computed from labels or v2 self-declared fields.",
            "",
            "## Blind Judging Instructions",
            "",
            "- Fill each `judgment_*` column with `A`, `B`, or `tie` while looking only at the blind CSV.",
            "- Judge quote cleanliness using the detector columns for both sides plus the quote text itself.",
            "- After judging, run `scripts/generate_insight_v1_v2_review.py --mode score --judgments <filled_csv>` to de-anonymize and compute the score.",
            "",
            "## Decision",
            "",
            "- Continue MSF-R07 only after this harness correction is committed.",
            "- Do not declare Gate R1 until R07 coverage is complete by episode and by chunk, and the blind 40-pair review has been scored.",
            "",
        ]
    )


def normalize_choice(value: Any) -> str:
    choice = normalize_text(value)
    if not choice:
        return ""
    if choice in {"a", "item a", "side a"}:
        return "A"
    if choice in {"b", "item b", "side b"}:
        return "B"
    if choice in {"tie", "empate", "equal", "igual"}:
        return "tie"
    raise SystemExit(f"Invalid judgment choice: {value!r}. Use A, B, tie, or blank.")


def load_key(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload.get("pairs"), list):
        raise SystemExit(f"Invalid blind key file: {path}")
    return payload


def score_judgments(
    rows: list[dict[str, str]], key: dict[str, Any]
) -> tuple[dict[str, Counter[str]], dict[str, Counter[str]], list[list[Any]], int]:
    key_by_pair = {str(pair.get("pair_id")): pair for pair in key.get("pairs", [])}
    counts: dict[str, Counter[str]] = {criterion: Counter() for criterion in CRITERIA}
    blind_counts: dict[str, Counter[str]] = {criterion: Counter() for criterion in CRITERIA}
    pair_rows: list[list[Any]] = []
    pending = 0

    for row in rows:
        pair_id = str(row.get("pair_id") or "")
        pair = key_by_pair.get(pair_id)
        if not pair:
            raise SystemExit(f"Judgment row has no matching key pair: {pair_id}")
        winners: list[str] = []
        for criterion in CRITERIA:
            choice = normalize_choice(row.get(f"judgment_{criterion}"))
            if not choice:
                pending += 1
                winners.append(f"{criterion}=pending")
                continue
            blind_counts[criterion][choice] += 1
            if choice == "tie":
                counts[criterion]["tie"] += 1
                winners.append(f"{criterion}=tie")
                continue
            side = (pair.get("sides") or {}).get(choice)
            if not isinstance(side, dict):
                raise SystemExit(f"Missing side {choice} for {pair_id}")
            version = str(side.get("version"))
            if version not in {"v1", "v2"}:
                raise SystemExit(f"Invalid side version in key: {version}")
            counts[criterion][version] += 1
            winners.append(f"{criterion}={version}")
        pair_rows.append(
            [
                pair_id,
                pair.get("episode_video_id"),
                f"chunk_{int(pair['chunk_number']):03d}" if isinstance(pair.get("chunk_number"), int) else "",
                (pair.get("sides") or {}).get("A", {}).get("version"),
                (pair.get("sides") or {}).get("A", {}).get("insight_id"),
                (pair.get("sides") or {}).get("B", {}).get("version"),
                (pair.get("sides") or {}).get("B", {}).get("insight_id"),
                ", ".join(winners),
            ]
        )
    return counts, blind_counts, pair_rows, pending


def render_scored_report(
    args: argparse.Namespace,
    key: dict[str, Any],
    counts: dict[str, Counter[str]],
    blind_counts: dict[str, Counter[str]],
    pair_rows: list[list[Any]],
    pending: int,
) -> str:
    score_rows = []
    for criterion in CRITERIA:
        criterion_counts = counts[criterion]
        score_rows.append([criterion, criterion_counts.get("v2", 0), criterion_counts.get("tie", 0), criterion_counts.get("v1", 0)])

    total_v2 = sum(counts[criterion].get("v2", 0) for criterion in CRITERIA)
    total_v1 = sum(counts[criterion].get("v1", 0) for criterion in CRITERIA)
    target_reached = len(pair_rows) >= args.target_pairs
    if pending:
        verdict = f"Pending judgment: {pending} criterion cell(s) are blank."
    elif not target_reached:
        verdict = "Pilot scored, but Gate R1 is not declared because the 40-pair R08 target is not met."
    elif total_v2 > total_v1:
        verdict = "Blind review scored: v2 wins more judged criteria than v1. Gate R1 is not declared by this report."
    elif total_v1 > total_v2:
        verdict = "Blind review scored: v1 wins more judged criteria than v2. Gate R1 is not declared by this report."
    else:
        verdict = "Blind review scored: v1 and v2 are tied across judged criteria. Gate R1 is not declared by this report."
    applicability_blind = blind_counts["applicability"]

    return "\n".join(
        [
            f"# Insight v1 vs v2 Review - {args.date}",
            "",
            "## Scope",
            "",
            f"- Judgments: `{args.judgments}`",
            f"- Local de-anonymization key: `{args.key_output}`",
            f"- Paired sample scored: {len(pair_rows)} pair(s).",
            f"- R08 target: {args.target_pairs} comparable pair(s) after R07 reaches {args.target_episodes} fully extracted v2 episode(s).",
            "- Raw transcript quotes are not copied into this tracked report.",
            "",
            "## Verdict",
            "",
            verdict,
            "",
            "## Criteria Counts",
            "",
            markdown_table(["criterion", "v2_wins", "ties", "v1_wins"], score_rows),
            "",
            "## Interpretation Notes",
            "",
            (
                "- Applicability should be read with discount: before de-anonymization, blind sides split "
                f"A={applicability_blind.get('A', 0)}, B={applicability_blind.get('B', 0)}, "
                f"tie={applicability_blind.get('tie', 0)}. The side with richer operational fields can win "
                "by structure, so specificity and evidence_fidelity are the decisive criteria."
            ),
            "- This report records the external blind judgment only; remediation findings discovered during score review must be resolved before any gate declaration.",
            "- De-anonymized pair rows reference the sample as judged; batch 006 duplicate-takeaway and evidence-window remediation can change current v2 insight IDs or quotes after scoring.",
            "",
            "## De-Anonymized Pair Results",
            "",
            markdown_table(["pair", "episode", "chunk", "A_version", "A_id", "B_version", "B_id", "judged_winners"], pair_rows),
            "",
            "## Decision",
            "",
            "- Use this scored report only after confirming R07 episode and chunk coverage in `data/exports/insights_v2_status.json`.",
            "- Gate R1 remains undeclared unless both coverage and blind-review criteria are satisfied.",
            "",
        ]
    )


def prepare_mode(args: argparse.Namespace) -> int:
    rows, key = prepare_blind_sample(args)
    fieldnames = (
        ["pair_id", "episode_video_id", "chunk", "similarity"]
        + side_fieldnames("a")
        + side_fieldnames("b")
        + [f"judgment_{criterion}" for criterion in CRITERIA]
        + ["judge_notes"]
    )
    write_csv(args.blind_output, rows, fieldnames)
    write_json(args.key_output, key)
    write_text(args.output, render_pending_report(args, len(rows)))
    print(f"wrote_blind_sample={args.blind_output}")
    print(f"wrote_key={args.key_output}")
    print(f"wrote_report={args.output}")
    print(f"pairs={len(rows)}")
    return 0


def score_mode(args: argparse.Namespace) -> int:
    rows = read_csv(args.judgments)
    key = load_key(args.key_output)
    counts, blind_counts, pair_rows, pending = score_judgments(rows, key)
    write_text(args.output, render_scored_report(args, key, counts, blind_counts, pair_rows, pending))
    print(f"wrote_report={args.output}")
    print(f"pairs={len(pair_rows)}")
    print(f"pending_cells={pending}")
    return 0 if pending == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["prepare", "score"], default="prepare")
    parser.add_argument("--v1-master", type=Path, default=data_path("exports", "insights_master.json"))
    parser.add_argument("--v2-master", type=Path, default=data_path("exports", "insights_v2_master.json"))
    parser.add_argument("--date", default=utc_date())
    parser.add_argument("--sample-size", type=int, default=40)
    parser.add_argument("--target-pairs", type=int, default=40)
    parser.add_argument("--target-episodes", type=int, default=15)
    parser.add_argument("--seed", default=None)
    parser.add_argument("--blind-output", type=Path)
    parser.add_argument("--key-output", type=Path)
    parser.add_argument("--judgments", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    args.blind_output = args.blind_output or data_path("exports", f"insight_v1_v2_blind_sample_{args.date}.csv")
    args.key_output = args.key_output or data_path("exports", f"insight_v1_v2_blind_key_{args.date}.json")
    args.judgments = args.judgments or args.blind_output
    args.output = args.output or Path("docs") / f"insight-v1-vs-v2-review-{args.date}.md"

    if args.mode == "prepare":
        return prepare_mode(args)
    return score_mode(args)


if __name__ == "__main__":
    raise SystemExit(main())
