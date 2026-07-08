#!/usr/bin/env python
"""Build the first curated_insights lot from the v2 master export."""

from __future__ import annotations

import argparse
import csv
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from msf_common import (
    as_list,
    first_evidence,
    jaccard,
    load_json,
    normalize_text,
    slugify,
    tokens,
    unique_preserve_order,
    write_json,
    write_text,
)


PRIORITY_PROCESS_TAGS = [
    "process-construcao-oferta",
    "process-copy-vsl",
    "process-copy-anuncios",
    "process-produto-low-ticket",
    "process-quiz",
    "process-mecanismo-big-idea",
    "process-prova-depoimentos",
]

SCORE_WEIGHTS = {
    "evidence": 25,
    "specificity": 25,
    "applicability": 20,
    "portability": 15,
    "novelty": 10,
    "cleanliness": 5,
}

CLAIM_RISK_TERMS = [
    "garantia",
    "garantido",
    "resultado",
    "faturamento",
    "milhao",
    "lucro",
    "conversao",
    "roi",
    "escala",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def taxonomy_process_ids(taxonomy: dict[str, Any]) -> set[str]:
    return {
        str(term.get("id"))
        for term in taxonomy.get("terms", [])
        if term.get("term_type") == "process" and term.get("status") == "active" and term.get("id")
    }


def process_labels(taxonomy: dict[str, Any]) -> dict[str, str]:
    return {
        str(term.get("id")): str(term.get("term") or term.get("id"))
        for term in taxonomy.get("terms", [])
        if term.get("term_type") == "process" and term.get("status") == "active" and term.get("id")
    }


def insight_similarity_text(insight: dict[str, Any]) -> str:
    parts = [
        insight.get("canonical_title"),
        insight.get("title"),
        insight.get("specific_takeaway"),
        insight.get("insight_ptbr"),
        insight.get("summary_ptbr"),
        insight.get("use_case"),
        insight.get("when_to_use"),
        insight.get("when_not_to_use"),
        " ".join(str(item) for item in as_list(insight.get("themes"))),
        " ".join(str(item) for item in as_list(insight.get("subthemes"))),
        " ".join(str(item) for item in as_list(insight.get("process_tags"))),
    ]
    return " ".join(str(part) for part in parts if part)


def has_text(value: Any, min_length: int = 8) -> bool:
    return len(str(value or "").strip()) >= min_length


def transliterate_ascii(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    return normalized.encode("ascii", errors="ignore").decode("ascii")


def complete_editorial_fields(insight: dict[str, Any], labels: dict[str, str]) -> dict[str, Any]:
    item = dict(insight)
    title = str(item.get("canonical_title") or item.get("title") or item.get("specific_takeaway") or "").strip()
    if not title:
        title = f"Insight {item.get('insight_id')}"
    item["canonical_title"] = title
    item["title"] = str(item.get("title") or title)
    primary_tag = as_list(item.get("process_tags"))[0] if as_list(item.get("process_tags")) else ""
    primary_process = labels.get(str(primary_tag), str(primary_tag or "marketing"))
    if not has_text(item.get("use_case")):
        item["use_case"] = f"Aplicar este insight em {primary_process}."
    if not has_text(item.get("when_to_use")):
        item["when_to_use"] = f"Use quando o time precisa aplicar {primary_process} em uma decisao de copy, oferta ou funil."
    if not has_text(item.get("when_not_to_use")):
        item["when_not_to_use"] = "Nao use como regra universal sem validar contexto, evidencia e restricoes da oferta."
    if not item.get("dedupe_key"):
        item["dedupe_key"] = slugify(item["canonical_title"])
    item.setdefault("supporting_insight_ids", [])
    item.setdefault("relations", [])
    item.setdefault("subthemes", [])
    item.setdefault("niches", [])
    item.setdefault("funnel_stages", [])
    return item


def review_claim_risk(insight: dict[str, Any]) -> str:
    current = normalize_text(insight.get("claim_risk"))
    if current not in {"low", "medium", "high"}:
        current = "medium"
    text = normalize_text(
        " ".join(
            str(part or "")
            for part in [
                insight.get("canonical_title"),
                insight.get("specific_takeaway"),
                insight.get("insight_ptbr"),
                insight.get("use_case"),
            ]
        )
    )
    evidence = first_evidence(insight)
    strength = normalize_text(evidence.get("evidence_strength"))
    has_risky_term = any(term in text for term in CLAIM_RISK_TERMS)
    if strength == "weak":
        return "high" if has_risky_term else "medium"
    if has_risky_term and strength != "strong":
        return "high" if current == "high" else "medium"
    if current == "high" and strength == "strong":
        return "medium"
    return current


def evidence_score(insight: dict[str, Any]) -> int:
    evidence_items = [item for item in as_list(insight.get("evidence")) if isinstance(item, dict)]
    if not evidence_items:
        return 0
    strength_points = {"strong": 25, "medium": 20, "weak": 12}
    best = max(strength_points.get(normalize_text(item.get("evidence_strength")), 14) for item in evidence_items)
    first = evidence_items[0]
    quote = str(first.get("quote_original") or "")
    if len(quote.strip()) < 20:
        best -= 4
    locator = first.get("locator") if isinstance(first.get("locator"), dict) else {}
    if not (locator.get("value") or first.get("segment_id") or first.get("start_seconds") is not None):
        best -= 3
    if len(evidence_items) > 1:
        best += 2
    return max(0, min(SCORE_WEIGHTS["evidence"], best))


def specificity_score(insight: dict[str, Any]) -> int:
    takeaway = str(insight.get("specific_takeaway") or "")
    title = str(insight.get("canonical_title") or insight.get("title") or "")
    token_count = len(tokens(takeaway))
    score = 10
    if has_text(takeaway, 60):
        score += 6
    elif has_text(takeaway, 30):
        score += 4
    if token_count >= 14:
        score += 4
    elif token_count >= 9:
        score += 2
    if has_text(title, 18):
        score += 2
    if any(char.isdigit() for char in takeaway + title):
        score += 1
    if len(set(tokens(takeaway)) & tokens(insight.get("use_case"))) >= 2:
        score += 2
    return max(0, min(SCORE_WEIGHTS["specificity"], score))


def applicability_score(insight: dict[str, Any]) -> int:
    score = 0
    if has_text(insight.get("use_case"), 20):
        score += 6
    if has_text(insight.get("when_to_use"), 20):
        score += 5
    if has_text(insight.get("when_not_to_use"), 20):
        score += 4
    if as_list(insight.get("applicability")):
        score += 3
    if as_list(insight.get("process_tags")):
        score += 2
    return max(0, min(SCORE_WEIGHTS["applicability"], score))


def portability_score(insight: dict[str, Any]) -> int:
    score = 4
    if len(as_list(insight.get("process_tags"))) >= 1:
        score += 4
    if len(as_list(insight.get("themes"))) >= 2:
        score += 3
    if len(as_list(insight.get("applicability"))) >= 2:
        score += 2
    if insight.get("level") in {"strategic", "tactical"}:
        score += 1
    if insight.get("insight_type") in {"framework", "tactic", "principle", "example", "playbook_step", "checklist"}:
        score += 1
    return max(0, min(SCORE_WEIGHTS["portability"], score))


def novelty_score(cluster_size: int) -> int:
    if cluster_size <= 1:
        return 10
    if cluster_size == 2:
        return 8
    if cluster_size <= 4:
        return 6
    return 4


def cleanliness_score(insight: dict[str, Any]) -> int:
    cleanliness = normalize_text(insight.get("evidence_cleanliness"))
    return {
        "clean": 5,
        "minor_noise": 3,
        "transcript_noise": 2,
        "promo_contaminated": 0,
    }.get(cleanliness, 2)


def cluster_items(items: list[dict[str, Any]], threshold: float) -> dict[str, list[str]]:
    representatives: list[dict[str, Any]] = []
    clusters: dict[str, list[str]] = {}
    used_cluster_ids: Counter[str] = Counter()
    for item in sorted(items, key=lambda value: str(value.get("insight_id") or "")):
        item_tokens = tokens(insight_similarity_text(item))
        best_rep: dict[str, Any] | None = None
        best_similarity = 0.0
        for rep in representatives:
            similarity = jaccard(item_tokens, rep["tokens"])
            if similarity > best_similarity:
                best_similarity = similarity
                best_rep = rep
        if best_rep and best_similarity >= threshold:
            cluster_id = best_rep["cluster_id"]
        else:
            base_cluster_id = f"curated-{slugify(item.get('canonical_title') or item.get('insight_id'), 72)}"
            used_cluster_ids[base_cluster_id] += 1
            cluster_id = base_cluster_id if used_cluster_ids[base_cluster_id] == 1 else f"{base_cluster_id}-{used_cluster_ids[base_cluster_id]}"
            representatives.append({"cluster_id": cluster_id, "tokens": item_tokens})
            clusters[cluster_id] = []
        item["cluster_id"] = cluster_id
        item["_cluster_similarity"] = round(best_similarity, 6)
        item["_similarity_tokens"] = sorted(item_tokens)
        clusters.setdefault(cluster_id, []).append(str(item.get("insight_id")))
    return clusters


def score_item(insight: dict[str, Any], cluster_size: int) -> dict[str, Any]:
    components = {
        "evidence": evidence_score(insight),
        "specificity": specificity_score(insight),
        "applicability": applicability_score(insight),
        "portability": portability_score(insight),
        "novelty": novelty_score(cluster_size),
        "cleanliness": cleanliness_score(insight),
    }
    return {"components": components, "total": sum(components.values())}


def priority_count(insight: dict[str, Any]) -> int:
    tags = set(str(tag) for tag in as_list(insight.get("process_tags")))
    return len(tags & set(PRIORITY_PROCESS_TAGS))


def select_curated(items: list[dict[str, Any]], target_count: int, cluster_cap: int) -> list[dict[str, Any]]:
    ranked = sorted(
        items,
        key=lambda item: (
            -priority_count(item),
            -int(item.get("editorial_score") or 0),
            -float(item.get("confidence_score") or 0.0),
            str(item.get("cluster_id") or ""),
            str(item.get("insight_id") or ""),
        ),
    )
    selected: list[dict[str, Any]] = []
    cluster_counts: Counter[str] = Counter()
    for item in ranked:
        cluster_id = str(item.get("cluster_id") or "")
        if cluster_cap > 0 and cluster_counts[cluster_id] >= cluster_cap:
            continue
        selected.append(item)
        cluster_counts[cluster_id] += 1
        if len(selected) >= target_count:
            break

    if len(selected) < target_count:
        selected_ids = {str(item.get("insight_id")) for item in selected}
        for item in ranked:
            if str(item.get("insight_id")) in selected_ids:
                continue
            selected.append(item)
            if len(selected) >= target_count:
                break
    return selected


def clean_for_output(item: dict[str, Any], clusters: dict[str, list[str]], generated_at: str) -> dict[str, Any]:
    output = dict(item)
    cluster_members = [insight_id for insight_id in clusters.get(str(output.get("cluster_id")), []) if insight_id != output.get("insight_id")]
    output["supporting_insight_ids"] = unique_preserve_order([*as_list(output.get("supporting_insight_ids")), *cluster_members[:5]])
    output["review_status"] = "auto_accepted"
    output["reviewed_by"] = "codex_r12_auto_curator"
    output["reviewed_at"] = generated_at
    output.pop("_score_components", None)
    output.pop("_priority_count", None)
    output.pop("_cluster_similarity", None)
    output.pop("_similarity_tokens", None)
    return output


def bucket_scores(scores: list[int]) -> dict[str, int]:
    buckets = {"50-59": 0, "60-69": 0, "70-79": 0, "80-89": 0, "90-100": 0}
    for score in scores:
        if score < 60:
            buckets["50-59"] += 1
        elif score < 70:
            buckets["60-69"] += 1
        elif score < 80:
            buckets["70-79"] += 1
        elif score < 90:
            buckets["80-89"] += 1
        else:
            buckets["90-100"] += 1
    return buckets


def review_sample(items: list[dict[str, Any]], sample_size: int) -> list[dict[str, Any]]:
    if sample_size <= 0:
        return []
    if len(items) <= sample_size:
        return list(items)
    selected = []
    for index in range(sample_size):
        source_index = round(index * (len(items) - 1) / (sample_size - 1))
        selected.append(items[source_index])
    return selected


def write_review_sample(path: Path, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample_rank",
        "insight_id",
        "canonical_title",
        "process_tags",
        "editorial_score",
        "claim_risk",
        "cluster_id",
        "use_case",
        "when_to_use",
        "when_not_to_use",
        "evidence_quote",
        "owner_decision",
        "owner_notes",
    ]
    existing_annotations = load_existing_review_annotations(path)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for index, item in enumerate(items, start=1):
            insight_id = str(item.get("insight_id") or "")
            annotation = existing_annotations.get(insight_id, {})
            writer.writerow(
                {
                    "sample_rank": index,
                    "insight_id": insight_id,
                    "canonical_title": item.get("canonical_title"),
                    "process_tags": ";".join(str(tag) for tag in as_list(item.get("process_tags"))),
                    "editorial_score": item.get("editorial_score"),
                    "claim_risk": item.get("claim_risk"),
                    "cluster_id": item.get("cluster_id"),
                    "use_case": item.get("use_case"),
                    "when_to_use": item.get("when_to_use"),
                    "when_not_to_use": item.get("when_not_to_use"),
                    "evidence_quote": first_evidence(item).get("quote_original") or "",
                    "owner_decision": annotation.get("owner_decision", ""),
                    "owner_notes": annotation.get("owner_notes", ""),
                }
            )


def load_existing_review_annotations(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    annotations: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            insight_id = str(row.get("insight_id") or "").strip()
            if not insight_id:
                continue
            annotations[insight_id] = {
                "owner_decision": row.get("owner_decision") or "",
                "owner_notes": row.get("owner_notes") or "",
            }
    return annotations


def validate_curated(items: list[dict[str, Any]], valid_process_ids: set[str], min_score: int, min_count: int, max_count: int) -> list[str]:
    errors: list[str] = []
    if not (min_count <= len(items) <= max_count):
        errors.append(f"curated_count_out_of_range={len(items)} expected={min_count}-{max_count}")
    seen_ids: set[str] = set()
    for item in items:
        insight_id = str(item.get("insight_id") or "")
        if insight_id in seen_ids:
            errors.append(f"duplicate_insight_id={insight_id}")
        seen_ids.add(insight_id)
        tags = [str(tag) for tag in as_list(item.get("process_tags"))]
        if not tags:
            errors.append(f"missing_process_tags={insight_id}")
        invalid_tags = [tag for tag in tags if tag not in valid_process_ids]
        if invalid_tags:
            errors.append(f"invalid_process_tags={insight_id}:{','.join(invalid_tags)}")
        score = item.get("editorial_score")
        if not isinstance(score, int) or score < min_score:
            errors.append(f"invalid_editorial_score={insight_id}:{score}")
        for field in ["canonical_title", "specific_takeaway", "use_case", "when_to_use", "when_not_to_use", "claim_risk", "cluster_id"]:
            if not item.get(field):
                errors.append(f"missing_{field}={insight_id}")
    return errors


def render_report(payload: dict[str, Any], excluded_count: int, review_sample_path: Path) -> str:
    scores = [int(item.get("editorial_score") or 0) for item in payload["insights"]]
    process_counts = Counter(tag for item in payload["insights"] for tag in as_list(item.get("process_tags")))
    priority_count_value = sum(1 for item in payload["insights"] if priority_count(item))
    lines = [
        "# MSF-R12 Curated Insights Lot - 2026-07-07",
        "",
        f"- Source: `{payload['source_path']}`",
        f"- Source insights: {payload['source_insight_count']}",
        f"- Curated insights: {payload['insight_count']}",
        f"- Excluded below score floor: {excluded_count}",
        f"- Score floor: {payload['score_floor']}",
        f"- Cluster threshold: {payload['cluster_threshold']}",
        f"- Cluster count in curated lot: {payload['cluster_count']}",
        f"- Owner review sample: `{review_sample_path}`",
        "",
        "## Score Distribution",
        "",
        f"- Min: {min(scores) if scores else 0}",
        f"- Max: {max(scores) if scores else 0}",
        f"- Average: {round(mean(scores), 2) if scores else 0}",
    ]
    for bucket, count in payload["score_distribution"].items():
        lines.append(f"- {bucket}: {count}")
    lines.extend(
        [
            "",
            "## Priority Coverage",
            "",
            f"- Items with at least one first-wave process tag: {priority_count_value}",
        ]
    )
    for tag in PRIORITY_PROCESS_TAGS:
        lines.append(f"- {tag}: {process_counts.get(tag, 0)}")
    lines.extend(["", "## Top Process Tags", ""])
    for tag, count in process_counts.most_common(15):
        lines.append(f"- {tag}: {count}")
    lines.extend(
        [
            "",
            "## Human Review",
            "",
            "- The owner review sample has 30 items with empty `owner_decision` and `owner_notes` columns.",
            "- Gate R3 is not declared by this report; the sample and pack comparison remain external-review inputs.",
            "",
        ]
    )
    return "\n".join(lines)


def build_curated(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    source = load_json(args.input)
    taxonomy = load_json(args.taxonomy)
    valid_ids = taxonomy_process_ids(taxonomy)
    labels = process_labels(taxonomy)
    generated_at = utc_now()
    prepared: list[dict[str, Any]] = []

    for raw_item in source.get("insights", []):
        if not isinstance(raw_item, dict):
            continue
        tags = [str(tag) for tag in as_list(raw_item.get("process_tags")) if str(tag) in valid_ids]
        if not tags:
            continue
        item = complete_editorial_fields({**raw_item, "process_tags": unique_preserve_order(tags)[:4]}, labels)
        item["claim_risk"] = review_claim_risk(item)
        prepared.append(item)

    clusters = cluster_items(prepared, args.cluster_threshold)
    cluster_sizes = {cluster_id: len(ids) for cluster_id, ids in clusters.items()}
    scored: list[dict[str, Any]] = []
    excluded_count = 0
    for item in prepared:
        score = score_item(item, cluster_sizes.get(str(item.get("cluster_id")), 1))
        item["_score_components"] = score["components"]
        item["_priority_count"] = priority_count(item)
        item["editorial_score"] = int(score["total"])
        if item["editorial_score"] < args.score_floor:
            excluded_count += 1
            continue
        scored.append(item)

    selected = select_curated(scored, args.target_count, args.cluster_cap)
    curated = [clean_for_output(item, clusters, generated_at) for item in selected]
    scores = [int(item.get("editorial_score") or 0) for item in curated]
    payload = {
        "schema_version": "1.0",
        "insight_layer": "curated_insights",
        "generated_at": generated_at,
        "source_path": str(args.input),
        "taxonomy_path": str(args.taxonomy),
        "source_insight_count": len(source.get("insights", [])),
        "score_floor": args.score_floor,
        "score_weights": SCORE_WEIGHTS,
        "priority_process_tags": PRIORITY_PROCESS_TAGS,
        "cluster_threshold": args.cluster_threshold,
        "cluster_count": len({item.get("cluster_id") for item in curated}),
        "insight_count": len(curated),
        "score_distribution": bucket_scores(scores),
        "insights": curated,
    }
    errors = validate_curated(curated, valid_ids, args.score_floor, args.min_count, args.max_count)
    if errors:
        raise SystemExit("Curated validation failed:\n" + "\n".join(errors[:50]))
    return payload, review_sample(curated, args.review_sample_size), excluded_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=Path("data/exports/insights_v2_master.json"), type=Path)
    parser.add_argument("--taxonomy", default=Path("data/processed/taxonomy_seed.json"), type=Path)
    parser.add_argument("--output", default=Path("data/exports/curated_insights.json"), type=Path)
    parser.add_argument("--review-sample", default=Path("data/exports/curated_insights_owner_review_sample_2026-07-07.csv"), type=Path)
    parser.add_argument("--report", default=Path("docs/curated-insights-r12-review-2026-07-07.md"), type=Path)
    parser.add_argument("--target-count", default=125, type=int)
    parser.add_argument("--min-count", default=100, type=int)
    parser.add_argument("--max-count", default=150, type=int)
    parser.add_argument("--review-sample-size", default=30, type=int)
    parser.add_argument("--score-floor", default=50, type=int)
    parser.add_argument("--cluster-threshold", default=0.62, type=float)
    parser.add_argument("--cluster-cap", default=3, type=int)
    args = parser.parse_args()

    payload, sample, excluded_count = build_curated(args)
    write_json(args.output, payload)
    write_review_sample(args.review_sample, sample)
    write_text(args.report, render_report(payload, excluded_count, args.review_sample))
    print(f"curated_insights={payload['insight_count']}")
    print(f"source_insights={payload['source_insight_count']}")
    print(f"clusters={payload['cluster_count']}")
    print(f"review_sample={len(sample)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
