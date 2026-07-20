#!/usr/bin/env python
"""Consolidate resumable human semantic reviews into a gold extraction.

No language model is called here.  The command consumes one review JSON per
chunk, validates evidence against the cleaned transcript, normalizes the
contract, records exact checkpoints, and leaves the episode awaiting an
independent external audit unless that audit has explicitly passed.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from scripts.gold_extraction_common import (
    GoldPauseError,
    SCHEMA_VERSION,
    calibration_coverage,
    calibration_target_errors,
    canonical_themes,
    citation,
    context_range,
    count_by,
    default_process_tags,
    evidence_quotes,
    external_audit_gate,
    fingerprint_paths,
    ledger_errors,
    ledger_for_signals,
    load_json,
    normalize_relations,
    now,
    protected_paths,
    sha256_json,
    validate_document,
    write_json,
)
from scripts.export_gold_audit_packet import export_packet


COMPATIBILITY = {
    "v2_mapping": {
        "gold.candidate_id": "v2.insight_id on approved migration only",
        "gold.title": "v2.canonical_title and title",
        "gold.takeaway_applicavel": "v2.specific_takeaway",
        "gold.themes": "v2.themes after canonical-to-serving mapping",
        "gold.subthemes": "v2.subthemes",
        "gold.process_tags": "v2.process_tags",
        "gold.evidence.minimal_quote": "v2.evidence",
        "gold.relations": "v2.relations",
    },
    "migration_policy": "parallel_only_until_owner_approves_a_dedicated_gold_to_v2_migration",
}


def apply_calibration_overrides(
    calibration: dict[str, Any], overrides: dict[str, Any] | None,
) -> dict[str, Any]:
    """Apply source-canonical calibration redirects without mutating their source.

    The builder rewrites ``calibration_tests.json`` as a derived coverage
    artifact.  Keeping redirects only in that derived artifact made every
    rebuild silently reintroduce stale calibration bindings.  The small
    override file is now the durable source of those redirects.
    """
    effective = copy.deepcopy(calibration)
    redirects = (overrides or {}).get("redirects", {})
    if not isinstance(redirects, dict):
        return effective
    tests = {
        str(item.get("calibration_id")): item
        for item in effective.get("tests", [])
        if isinstance(item, dict) and item.get("calibration_id")
    }
    for calibration_id, fields in redirects.items():
        target = tests.get(str(calibration_id))
        if target is None or not isinstance(fields, dict):
            continue
        for field, value in fields.items():
            target[field] = copy.deepcopy(value)
    return effective


def effective_calibration(out: Path) -> dict[str, Any]:
    calibration = load_json(out / "calibration_tests.json")
    overrides_path = out / "calibration_overrides.json"
    overrides = load_json(overrides_path) if overrides_path.exists() else None
    return apply_calibration_overrides(calibration, overrides)


def read_reviews(review_dir: Path) -> list[dict[str, Any]]:
    reviews: list[dict[str, Any]] = []
    for path in sorted(review_dir.glob("chunk_*_review.json")):
        reviews.append(load_json(path))
    return reviews


def citation_from_value(value: dict[str, Any], segments_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    segment = segments_by_id[value["segment_id"]]
    return citation(segment)


def legacy_minimal_quote(citations: list[dict[str, Any]], candidate: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Narrow legacy evidence while preserving every original citation as support."""
    numbers = [str(item.get("raw", "")).strip() for item in candidate.get("numbers", []) if isinstance(item, dict)]
    chosen = [item for item in citations if any(raw and raw in item["quote_verbatim"] for raw in numbers)]
    if not chosen:
        claim_words = set(re.findall(r"[a-z0-9]{4,}", candidate.get("source_claim", "").lower()))
        chosen = [max(citations, key=lambda item: len(claim_words & set(re.findall(r"[a-z0-9]{4,}", item["quote_verbatim"].lower()))))] if citations else []
    minimal_ids = {item["segment_id"] for item in chosen}
    return chosen, [item for item in citations if item["segment_id"] not in minimal_ids]


def normalize_numbers(numbers: Any) -> list[dict[str, Any]]:
    def scalar(value: Any) -> int | float | None:
        if isinstance(value, (int, float)):
            return value
        if not isinstance(value, str):
            return None
        compact = value.strip().replace(" ", "")
        if re.fullmatch(r"\d+(?:\.\d+)?", compact):
            return float(compact) if "." in compact else int(compact)
        return None

    def range_values(value: Any) -> tuple[int | float | None, int | float | None]:
        if not isinstance(value, str):
            return None, None
        matches = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*(?:-|_to_|a)\s*(\d+(?:\.\d+)?)\s*", value)
        if not matches:
            return None, None
        return scalar(matches.group(1)), scalar(matches.group(2))

    def normalized_role(value: Any) -> str:
        raw_role = str(value or "")
        lower = raw_role.lower()
        if "baseline" in lower or "before" in lower or "cac" in lower:
            return "baseline"
        if "after" in lower or "result" in lower or "return" in lower or "roas" in lower or "roi" in lower:
            return "result"
        if "price" in lower or "ticket" in lower:
            return "price"
        if "spend" in lower or "budget" in lower:
            return "budget"
        if "volume" in lower or "audience" in lower or "views" in lower or "buyers" in lower:
            return "capacity"
        return value if value in {"baseline", "result", "delta", "target", "price", "budget", "capacity", "cadence", "other"} else "other"

    normalized: list[dict[str, Any]] = []
    for raw_number in numbers or []:
        if not isinstance(raw_number, dict):
            raw_number = {"raw": str(raw_number), "value": None}
        unit = raw_number.get("unit")
        unit_text = str(unit or "").lower()
        unit_kind = raw_number.get("unit_kind")
        if not unit_kind:
            if "r$" in str(raw_number.get("raw", "")).lower() or any(token in unit_text for token in ("brl", "usd", "currency")):
                unit_kind = "currency"
            elif "%" in str(raw_number.get("raw", "")) or unit_text == "percent":
                unit_kind = "percent"
            elif any(word in unit_text for word in ("roas", "roi", "ratio", "multiple")) or unit_text == "x":
                unit_kind = "ratio"
            elif any(word in unit_text for word in ("minute", "hour", "dia", "mes", "minuto", "hora")) and not any(word in unit_text for word in ("per_", "_per", "views", "leads", "buyers", "sales")):
                unit_kind = "duration"
            else:
                unit_kind = "count"
        status = raw_number.get("value_status") or raw_number.get("certainty") or "reported"
        value = scalar(raw_number.get("value"))
        min_value = raw_number.get("min_value")
        max_value = raw_number.get("max_value")
        inferred_min, inferred_max = range_values(raw_number.get("value"))
        if inferred_min is not None:
            min_value, max_value = inferred_min, inferred_max
        period = raw_number.get("period")
        if not period:
            raw_and_unit = f"{raw_number.get('raw', '')} {unit_text}".lower()
            if "por dia" in raw_and_unit or "per_day" in raw_and_unit:
                period = "day"
            elif "por mes" in raw_and_unit or "per_month" in raw_and_unit:
                period = "month"
        record = {
            "raw": str(raw_number.get("raw", "")).strip(), "value": value,
            "min_value": min_value, "max_value": max_value,
            "unit_kind": unit_kind, "unit": unit, "period": period,
            "role": normalized_role(raw_number.get("role", "other")),
            "value_status": status if status in {"reported", "calculated", "corrected", "inferred"} else "reported",
            "denominator": raw_number.get("denominator"), "attribution_window": raw_number.get("attribution_window"),
            "legacy_role": raw_number.get("role"), "legacy_value_status": raw_number.get("certainty"),
        }
        if "before_after" in str(raw_number.get("role", "")).lower() and inferred_min is not None and inferred_max is not None:
            normalized.append({**record, "value": inferred_min, "min_value": None, "max_value": None, "role": "baseline"})
            normalized.append({**record, "value": inferred_max, "min_value": None, "max_value": None, "role": "result"})
        else:
            normalized.append(record)
    return normalized


def normalize_candidate(raw: dict[str, Any], video_id: str, segments_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    candidate = dict(raw)
    themes, inherited_subthemes = canonical_themes(candidate.get("themes") or [])
    candidate["themes"] = themes
    candidate["subthemes"] = list(dict.fromkeys(list(candidate.get("subthemes") or []) + inherited_subthemes))
    candidate["process_tags"] = list(candidate.get("process_tags") or default_process_tags(themes))
    candidate.setdefault("context", {"episode_video_id": video_id, "source_kind": "transcript"})
    candidate.setdefault("reported_case", False)
    candidate.setdefault("steps", [])
    candidate.setdefault("conditions", [])
    candidate.setdefault("caveats", [])
    candidate["numbers"] = normalize_numbers(candidate.get("numbers"))
    evidence = candidate.get("evidence")
    if isinstance(evidence, list):
        citations = [citation_from_value(item, segments_by_id) for item in evidence]
        minimal, support = legacy_minimal_quote(citations, candidate)
        candidate["evidence"] = {
            "minimal_quote": minimal,
            "context_range": context_range(citations, segments_by_id),
            "support_segments": support,
            "legacy_evidence_preserved": citations,
        }
    elif isinstance(evidence, dict):
        minimal = [citation_from_value(item, segments_by_id) for item in evidence.get("minimal_quote") or []]
        support = [citation_from_value(item, segments_by_id) for item in evidence.get("support_segments") or []]
        citations = minimal + support
        candidate["evidence"] = {
            "minimal_quote": minimal,
            "context_range": evidence.get("context_range") or context_range(citations, segments_by_id),
            "support_segments": support,
        }
    else:
        candidate["evidence"] = {"minimal_quote": [], "context_range": {}, "support_segments": []}
    relations = candidate.get("relations") if isinstance(candidate.get("relations"), dict) else {}
    candidate["relations"] = {
        "parent_candidate_id": relations.get("parent_candidate_id", candidate.pop("parent_candidate_id", None)),
        "child_candidate_ids": relations.get("child_candidate_ids", candidate.pop("child_candidate_ids", [])) or [],
    }
    return candidate


def readiness_check(video_id: str, data_root: Path, reviews_dir: Path) -> dict[str, Any]:
    """Check final-build inputs without changing episode state or artifacts."""
    out = data_root / "processed" / video_id / "gold_extraction"
    transcript = load_json(out / "transcript_clean.json")["segments"]
    chunks = load_json(out / "chunks" / "chunk_index.json")["chunks"]
    status = load_json(out / "gold_extraction_status.json")
    calibration = effective_calibration(out)
    signals = load_json(out / "signal_inventory.json").get("signals", [])
    segments_by_id = {item["segment_id"]: item for item in transcript}
    reviews = {item.get("chunk_id"): item for item in read_reviews(reviews_dir)}
    errors: list[str] = []
    candidates: list[dict[str, Any]] = []
    manual_decisions: dict[str, dict[str, Any]] = {}
    for chunk in status.get("chunks", []):
        review = reviews.get(chunk["chunk_id"])
        if review is None:
            errors.append(f"missing review for {chunk['chunk_id']}")
            continue
        if review.get("episode_video_id") != video_id:
            errors.append(f"{chunk['chunk_id']}: review episode mismatch")
        if review.get("input_hash") != chunk["input_hash"]:
            errors.append(f"{chunk['chunk_id']}: review input hash mismatch")
        if not review.get("full_chunk_reviewed"):
            errors.append(f"{chunk['chunk_id']}: review did not confirm full chunk read")
        candidates.extend(normalize_candidate(item, video_id, segments_by_id) for item in review.get("candidates", []))
        for decision in review.get("ledger_decisions", []):
            segment_id = decision.get("segment_id")
            if segment_id in manual_decisions:
                errors.append(f"duplicate manual ledger decision {segment_id}")
            elif segment_id:
                manual_decisions[str(segment_id)] = decision
    document = {
        "schema_version": SCHEMA_VERSION,
        "insight_layer": "gold_extraction",
        "episode_video_id": video_id,
        "audit": {"status": "pending_external", "open_findings": 0},
        "insights": candidates,
    }
    errors.extend(normalize_relations(candidates))
    errors.extend(validate_document(document, transcript, chunks, require_external_audit=False))
    preview_ledger = ledger_for_signals(signals, candidates, manual_decisions)
    covered_calibration = calibration_coverage(calibration, candidates, preview_ledger)
    errors.extend(calibration_target_errors(calibration, segments_by_id))
    if covered_calibration["status"] != "pass":
        errors.append("calibration coverage below episode minimum")
    return {
        "status": "ready" if not errors else "not_ready",
        "candidates": len(candidates),
        "errors": sorted(set(errors)),
        "calibration": covered_calibration["status"],
    }


def build_from_reviews(
    video_id: str,
    data_root: Path,
    reviews_dir: Path,
    legacy_audit_status: str | None = None,
    executor_thread_id: str | None = None,
    export_suffix: str | None = None,
    *,
    audit_warnings: list[dict[str, Any]] | None = None,
    revision_id: str | None = None,
    defer_packet: bool = False,
    force_pending_external: bool = False,
) -> dict[str, Any]:
    out = data_root / "processed" / video_id / "gold_extraction"
    # Fast Path invariant: deterministic review defects are reported before
    # this builder writes candidate chunks, ledgers, status or packets.
    preflight = readiness_check(video_id, data_root, reviews_dir)
    if preflight["errors"]:
        return {"status": "validation_failed", "candidates": preflight["candidates"], "errors": preflight["errors"], "calibration": preflight["calibration"]}
    transcript = load_json(out / "transcript_clean.json")["segments"]
    chunks = load_json(out / "chunks" / "chunk_index.json")["chunks"]
    signals = load_json(out / "signal_inventory.json")["signals"]
    calibration = effective_calibration(out)
    status = load_json(out / "gold_extraction_status.json")
    executor_thread_id = executor_thread_id or status.get("executor_thread_id")
    audit_gate = (
        {
            "status": "pending_external",
            "eligible_for_complete": False,
            "errors": [],
            "report": None,
        }
        if force_pending_external
        else external_audit_gate(out, executor_thread_id)
    )
    audit_status = audit_gate["status"]
    chunks_by_id = {item["chunk_id"]: item for item in chunks}
    segments_by_id = {item["segment_id"]: item for item in transcript}
    review_by_chunk = {item.get("chunk_id"): item for item in read_reviews(reviews_dir)}
    errors: list[str] = []
    if legacy_audit_status == "passed":
        errors.append("passed audit must be derived from editorial_audit_report.json")
    if audit_gate["errors"]:
        errors.extend(audit_gate["errors"])
    candidates: list[dict[str, Any]] = []
    manual_decisions: dict[str, dict[str, Any]] = {}
    new_chunk_states: list[dict[str, Any]] = []
    for previous in status.get("chunks", []):
        chunk_id = previous["chunk_id"]
        review = review_by_chunk.get(chunk_id)
        if review is None:
            errors.append(f"missing review for {chunk_id}")
            new_chunk_states.append({**previous, "status": "pending"})
            continue
        review_hash = sha256_json(review)
        if review.get("episode_video_id") != video_id:
            errors.append(f"{chunk_id}: review episode mismatch")
        if review.get("input_hash") != previous["input_hash"]:
            errors.append(f"{chunk_id}: review input hash mismatch")
        if not review.get("full_chunk_reviewed"):
            errors.append(f"{chunk_id}: review did not confirm full chunk read")
        chunk_candidates = [normalize_candidate(item, video_id, segments_by_id) for item in review.get("candidates", [])]
        for candidate in chunk_candidates:
            if candidate.get("chunk_id") != chunk_id:
                errors.append(f"{candidate.get('candidate_id', '<unknown>')}: wrong chunk_id")
        candidates.extend(chunk_candidates)
        for decision in review.get("ledger_decisions", []):
            if decision.get("segment_id") in manual_decisions:
                errors.append(f"duplicate manual ledger decision {decision['segment_id']}")
            else:
                manual_decisions[decision.get("segment_id")] = decision
        candidate_path = out / "candidate_chunks" / f"chunk_{previous['chunk_number']:03d}_candidates.json"
        candidate_payload = {
            "schema_version": SCHEMA_VERSION, "episode_video_id": video_id, "chunk_id": chunk_id,
            "input_hash": previous["input_hash"], "review_hash": review_hash,
            "review_route": "codex_manual_no_paid_api", "candidates": chunk_candidates,
        }
        # Rewriting identical content is harmless, but retaining the checkpoint makes a resume observable.
        write_json(candidate_path, candidate_payload)
        unchanged = previous.get("status") == "completed" and previous.get("review_hash") == review_hash
        new_chunk_states.append({
            **previous, "status": "completed", "attempts": previous.get("attempts", 0) + (0 if unchanged else 1),
            "review_hash": review_hash, "candidate_count": len(chunk_candidates), "completed_at": now(),
        })
    document = {
        "schema_version": SCHEMA_VERSION, "insight_layer": "gold_extraction", "episode_video_id": video_id,
        "compatibility": COMPATIBILITY,
        "audit": {
            "status": audit_status,
            "open_findings": audit_gate.get("report", {}).get("open_findings", 0) if audit_gate.get("report") else 0,
            "gate_source": "editorial_audit_report.json" if audit_gate.get("report") else "pending_external",
        },
        "insights": candidates,
    }
    errors.extend(normalize_relations(candidates))
    errors.extend(validate_document(document, transcript, chunks, require_external_audit=False))
    ledger_signals = list(signals)
    ledger_signal_ids = {item["segment_id"] for item in ledger_signals}
    for candidate in candidates:
        for item in evidence_quotes(candidate):
            if item["segment_id"] not in ledger_signal_ids:
                segment = segments_by_id[item["segment_id"]]
                ledger_signals.append({
                    "segment_id": segment["segment_id"], "clean_index": segment["clean_index"],
                    "signal_types": ["candidate_evidence"], "evidence": [citation(segment)],
                })
                ledger_signal_ids.add(item["segment_id"])
    ledger = ledger_for_signals(ledger_signals, candidates, manual_decisions)
    errors.extend(ledger_errors(ledger, {item["candidate_id"] for item in candidates}, {item["segment_id"] for item in ledger}))
    errors.extend(calibration_target_errors(calibration, segments_by_id))
    covered_calibration = calibration_coverage(calibration, candidates, ledger)
    if covered_calibration["status"] != "pass":
        errors.append("calibration coverage below episode minimum")
    protected = load_json(out / "protected_fingerprints.json")
    protected_after = fingerprint_paths(protected_paths(data_root, video_id))
    if protected.get("before") != protected_after:
        errors.append("protected v2/master/raw fingerprints changed")
    write_json(out / "candidate_claims_master.json", {
        "schema_version": SCHEMA_VERSION, "episode_video_id": video_id,
        "extraction_method": "codex_manual_semantic_gold", "candidates": candidates,
    })
    write_json(out / "insights_exhaustive.json", document)
    write_json(out / "high_signal_coverage_ledger.json", {"episode_video_id": video_id, "entries": ledger})
    write_json(out / "calibration_tests.json", {"episode_video_id": video_id, **covered_calibration})
    write_json(out / "protected_fingerprints.json", {"before": protected.get("before", {}), "after": protected_after, "verified_at": now()})
    with (out / "quantitative_claims.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["candidate_id", "chunk_id", "raw", "value", "min_value", "max_value", "unit_kind", "unit", "period", "role", "value_status", "denominator", "attribution_window", "legacy_role", "legacy_value_status", "source_claim"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for candidate in candidates:
            for number in candidate["numbers"]:
                writer.writerow({"candidate_id": candidate["candidate_id"], "chunk_id": candidate["chunk_id"], **number, "source_claim": candidate["source_claim"]})
    type_counts = count_by(candidates, "type")
    theme_counts = count_by(candidates, "themes")
    dispositions = defaultdict(int)
    exclusion_categories = defaultdict(int)
    for entry in ledger:
        dispositions[entry["disposition"]] += 1
        if entry["disposition"] == "excluded":
            exclusion_categories[entry.get("reason_code") or "unclassified"] += 1
    coverage = "# Gold extraction coverage\n\n" + "\n".join([
        f"- Clean segments: {len(transcript)}", f"- Chunks: {len(chunks)}", f"- Insights: {len(candidates)}",
        f"- Signals: {len(ledger)}", f"- Captured: {dispositions['captured']}",
        f"- Merged: {dispositions['merged']}", f"- Excluded: {dispositions['excluded']}",
        f"- Exclusion categories: {dict(sorted(exclusion_categories.items()))}",
        f"- Types: {type_counts}", f"- Themes: {theme_counts}",
        f"- Calibration: {covered_calibration['covered_count']}/{len(covered_calibration['tests'])}; {covered_calibration['status']}",
        f"- External audit: {audit_status}",
    ]) + "\n"
    (out / "coverage_report.md").write_text(coverage, encoding="utf-8")
    deterministic_pass = not errors
    lifecycle = "validation_failed" if errors else "complete" if audit_gate["eligible_for_complete"] else "awaiting_external_audit"
    validation = "# Gold extraction validation\n\n"
    validation += "PASS: deterministic schema, transcript, evidence, relation, ledger and calibration checks passed.\n" if deterministic_pass else "FAIL:\n" + "\n".join(f"- {item}" for item in sorted(set(errors))) + "\n"
    validation += f"\n- External audit status: {audit_status}\n- Protected fingerprint equality: {protected.get('before') == protected_after}\n- Candidate IDs: {len({item['candidate_id'] for item in candidates})}/{len(candidates)}\n"
    (out / "validation_report.md").write_text(validation, encoding="utf-8")
    updated_status = {
        **status, "status": lifecycle, "chunks": new_chunk_states, "candidate_count": len(candidates),
        "executor_thread_id": executor_thread_id, "open_audit_findings": document["audit"]["open_findings"], "audit_status": audit_status,
        "updated_at": now(), "errors": sorted(set(errors)),
    }
    write_json(out / "gold_extraction_status.json", updated_status)
    if lifecycle == "awaiting_external_audit" and not defer_packet:
        packet = export_packet(
            video_id,
            data_root,
            export_suffix or f"msf_r20_piloto_{video_id}",
            audit_warnings=audit_warnings,
            revision_id=revision_id,
        )
        updated_status["audit_packet"] = packet["packet"]
        updated_status["updated_at"] = now()
        write_json(out / "gold_extraction_status.json", updated_status)
    return {"status": lifecycle, "candidates": len(candidates), "errors": sorted(set(errors)), "calibration": covered_calibration["status"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--reviews-dir", type=Path)
    parser.add_argument("--executor-thread-id")
    parser.add_argument("--export-suffix", help="Override the audit-packet suffix for awaiting-external-audit builds.")
    parser.add_argument("--check-readiness", action="store_true", help="Validate reviews and candidates without writing artifacts.")
    args = parser.parse_args()
    reviews = args.reviews_dir or args.data_root / "processed" / args.video_id / "gold_extraction" / "manual_reviews"
    if args.check_readiness:
        result = readiness_check(args.video_id, args.data_root, reviews)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if not result["errors"] else 1
    try:
        result = build_from_reviews(args.video_id, args.data_root, reviews, executor_thread_id=args.executor_thread_id, export_suffix=args.export_suffix)
    except GoldPauseError as exc:
        print(json.dumps({"status": "paused_filesystem", "error": str(exc)}))
        return 75
    print(json.dumps(result, ensure_ascii=False))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
