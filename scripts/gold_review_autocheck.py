#!/usr/bin/env python
"""Read-only directed-recall inventory for a prepared gold episode."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from scripts.gold_extraction_common import (
    EXCLUSION_REASON_CODES,
    calibration_coverage,
    calibration_target_errors,
    editorial_ascii_errors,
    evidence_quotes,
    ledger_for_signals,
    load_json,
    normalize_ascii,
    normalize_relations,
    validate_numbers,
    sha256_semantic_json,
)


WORD_NUMBER_MATERIAL_RE = re.compile(
    r"\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito|nove|dez)\b"
    r"(?:\s+(?:to|a|ate)\s+\b(?:one|two|three|four|five|six|seven|eight|nine|ten|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito|nove|dez)\b)?"
    r"\s+(?:percent|por cento|days?|dias?|weeks?|semanas?|months?|meses?|minutes?|minutos?|hours?|horas?|leads?|buyers?|compradores?|sales?|vendas?)\b",
    re.I,
)
INTERVIEWER_OR_PROMO_RE = re.compile(
    r"\b(?:subscribe|sign up|link in the description|podcast|website|you said|do you|what do you think|so you actually|right\?|"
    r"voce disse|o que voce acha|entao voce|nao e\?|certo\?)",
    re.I,
)


def read_reviews(directory: Path) -> list[dict[str, Any]]:
    return [load_json(path) for path in sorted(directory.glob("chunk_*_review.json"))]


def _quote_text(candidate: dict[str, Any]) -> str:
    return " ".join(item.get("quote_verbatim", "") for item in evidence_quotes(candidate))


def _candidate_evidence_segment_ids(candidate: dict[str, Any]) -> set[str]:
    """Read persisted evidence first, with legacy draft arrays as fallback."""
    persisted = {str(item.get("segment_id")) for item in evidence_quotes(candidate) if item.get("segment_id")}
    if persisted:
        return persisted
    return {str(item) for item in candidate.get("minimal_segment_ids", []) + candidate.get("support_segment_ids", []) if item}


def _meaningful_words(text: str) -> set[str]:
    ignored = {"about", "antes", "com", "como", "depois", "entre", "from", "para", "sobre", "testar", "teste", "that", "this", "uma", "with"}
    return {word for word in re.findall(r"[a-z0-9]+", normalize_ascii(text)) if len(word) >= 5 and word not in ignored}


def _title_content_words(title: str) -> set[str]:
    """Return title terms that can indicate a material semantic overlap."""
    return _meaningful_words(title)


def _has_symmetric_parent_child_relation(
    left_id: str | None,
    right_id: str | None,
    relations: dict[str | None, dict[str, Any]],
) -> bool:
    if not left_id or not right_id:
        return False
    left = relations.get(left_id, {})
    right = relations.get(right_id, {})
    return (
        left.get("parent_candidate_id") == right_id
        and left_id in right.get("child_candidate_ids", [])
    ) or (
        right.get("parent_candidate_id") == left_id
        and right_id in left.get("child_candidate_ids", [])
    )


def _classified(category: str, values: list[Any], kind: str) -> list[dict[str, Any]]:
    return [{"category": category, "kind": kind, "items": values}] if values else []


def autocheck_state(
    video_id: str,
    *,
    status: dict[str, Any],
    transcript: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
    signals: list[dict[str, Any]],
    calibration: dict[str, Any],
    reviews: list[dict[str, Any]] | dict[str, dict[str, Any]],
    stored_ledger: list[dict[str, Any]] | None = None,
    prefer_stored_ledger: bool = True,
) -> dict[str, Any]:
    """Evaluate the final candidate state without requiring persisted reviews."""
    review_values = list(reviews.values()) if isinstance(reviews, dict) else list(reviews)
    reviews = {review.get("chunk_id"): review for review in review_values}
    candidates = [candidate for review in reviews.values() for candidate in review.get("candidates", [])]
    evidence_ids = {segment_id for candidate in candidates for segment_id in _candidate_evidence_segment_ids(candidate)}
    stored_ledger = stored_ledger or []
    review_decisions = [decision for review in reviews.values() for decision in review.get("ledger_decisions", [])]
    manual_decisions = {
        str(decision["segment_id"]): decision
        for decision in review_decisions
        if decision.get("segment_id")
    }
    # Preparation creates pending placeholders. Once a derived ledger has real
    # dispositions it is the final source of truth for this read-only preview.
    decisions = (
        stored_ledger
        if prefer_stored_ledger and any(item.get("disposition") != "pending" for item in stored_ledger)
        else ledger_for_signals(signals, candidates, manual_decisions)
    )
    number_issues: list[dict[str, Any]] = []
    steps_issues: list[str] = []
    encoding: list[str] = []
    interview_or_promo: list[str] = []
    interviewer_only: list[str] = []
    claim_evidence: list[dict[str, Any]] = []
    caveat_issues: list[str] = []
    ledger_issues: list[dict[str, Any]] = []
    for candidate in candidates:
        quote_text = _quote_text(candidate)
        numbers = candidate.get("numbers", [])
        if (re.search(r"\d|%|\bpercent\b", quote_text, re.I) or WORD_NUMBER_MATERIAL_RE.search(normalize_ascii(quote_text))) and not numbers:
            number_issues.append({"candidate_id": candidate.get("candidate_id"), "issue": "possible material numeric evidence without structured numbers"})
        for error in validate_numbers(candidate.get("candidate_id", "<unknown>"), numbers, [quote_text]):
            number_issues.append({"candidate_id": candidate.get("candidate_id"), "issue": error})
        if candidate.get("type") in {"playbook_step", "framework", "script"} and not candidate.get("steps"):
            steps_issues.append(candidate.get("candidate_id", "<unknown>"))
        encoding.extend(editorial_ascii_errors(candidate))
        normalized = normalize_ascii(quote_text)
        if INTERVIEWER_OR_PROMO_RE.search(normalized):
            interview_or_promo.append(candidate.get("candidate_id", "<unknown>"))
        quote_parts = [normalize_ascii(item.get("quote_verbatim", "")) for item in evidence_quotes(candidate)]
        if quote_parts and all(INTERVIEWER_OR_PROMO_RE.search(item) for item in quote_parts):
            interviewer_only.append(candidate.get("candidate_id", "<unknown>"))
        claim_words = _meaningful_words(str(candidate.get("source_claim", "")))
        evidence_words = _meaningful_words(quote_text)
        if claim_words and not (claim_words & evidence_words):
            claim_evidence.append({"candidate_id": candidate.get("candidate_id"), "issue": "claim has no meaningful lexical support in minimal evidence"})
        if candidate.get("reported_case") and candidate.get("numbers") and not candidate.get("caveats"):
            caveat_issues.append(candidate.get("candidate_id", "<unknown>"))
    candidate_by_id = {candidate.get("candidate_id"): candidate for candidate in candidates}
    decisions_by_segment: dict[str, list[dict[str, Any]]] = {}
    for decision in decisions:
            segment_id = decision.get("segment_id")
            if segment_id:
                decisions_by_segment.setdefault(segment_id, []).append(decision)
            if decision.get("disposition") == "excluded":
                reason = decision.get("reason_code")
                reference = decision.get("reason_reference")
                if reason not in EXCLUSION_REASON_CODES or (reason == "duplicate_of" and reference not in candidate_by_id):
                    ledger_issues.append({"segment_id": segment_id, "issue": "excluded ledger decision has invalid reason or reference"})
                continue
            if decision.get("disposition") not in {"captured", "merged"}:
                ledger_issues.append({"segment_id": segment_id, "issue": "ledger decision has invalid disposition"})
                continue
            destination_ids = decision.get("candidate_ids") or []
            if not destination_ids:
                ledger_issues.append({"segment_id": decision.get("segment_id"), "issue": "captured or merged decision has no candidate destination"})
                continue
            matching = [candidate_by_id.get(candidate_id) for candidate_id in destination_ids]
            if any(candidate is None for candidate in matching) or not any(decision.get("segment_id") in _candidate_evidence_segment_ids(candidate) for candidate in matching if candidate):
                ledger_issues.append({"segment_id": decision.get("segment_id"), "candidate_ids": destination_ids, "issue": "ledger destination does not cite the same segment"})
    high_signals = [signal for signal in signals if signal.get("signal_types")]
    automatic_ledger_preview: list[dict[str, Any]] = []
    for signal in high_signals:
        decisions = decisions_by_segment.get(signal["segment_id"], [])
        resolved = False
        for decision in decisions:
            if decision.get("disposition") == "excluded":
                reason = decision.get("reason_code")
                resolved = reason in EXCLUSION_REASON_CODES and (reason != "duplicate_of" or decision.get("reason_reference") in candidate_by_id)
            elif decision.get("disposition") in {"captured", "merged"}:
                resolved = any(
                    candidate_id in candidate_by_id and signal["segment_id"] in _candidate_evidence_segment_ids(candidate_by_id[candidate_id])
                    for candidate_id in decision.get("candidate_ids", [])
                )
            if resolved:
                break
        if not resolved:
            automatic_ledger_preview.append({"segment_id": signal["segment_id"], "signal_types": signal["signal_types"], "issue": "automatic ledger final decision is missing or unsupported"})
    uncovered = [
        {"segment_id": signal["segment_id"], "signal_types": signal["signal_types"]}
        for signal in high_signals
        if signal["segment_id"] not in evidence_ids and signal["segment_id"] not in decisions_by_segment
    ]
    relations = {candidate.get("candidate_id"): candidate.get("relations", {}) for candidate in candidates}
    overlaps: list[dict[str, Any]] = []
    for left_index, left in enumerate(candidates):
        left_words = _title_content_words(str(left.get("title", "")))
        for right in candidates[left_index + 1:]:
            right_words = _title_content_words(str(right.get("title", "")))
            shared = left_words & right_words
            if len(shared) >= 3:
                left_id, right_id = left.get("candidate_id"), right.get("candidate_id")
                if not _has_symmetric_parent_child_relation(left_id, right_id, relations):
                    overlaps.append({"candidate_ids": [left_id, right_id], "shared_title_terms": sorted(shared)})
    signal_by_id = {item["segment_id"]: item for item in signals}
    boundaries: list[dict[str, Any]] = []
    for left, right in zip(chunks, chunks[1:]):
        left_signal = signal_by_id.get(left["last_segment_id"])
        right_signal = signal_by_id.get(right["first_segment_id"])
        if left_signal or right_signal:
            boundaries.append({
                "between_chunks": [left["chunk_id"], right["chunk_id"]],
                "segment_ids": [left["last_segment_id"], right["first_segment_id"]],
                "signal_types": [left_signal.get("signal_types", []) if left_signal else [], right_signal.get("signal_types", []) if right_signal else []],
            })
    calibration_target_issues = calibration_target_errors(calibration, {item["segment_id"]: item for item in transcript})
    calibration_result = calibration_coverage(calibration, candidates)
    calibration_semantic_issues: list[dict[str, Any]] = []
    for test in calibration.get("tests", []):
        for candidate_id in test.get("semantic_candidate_ids", []):
            candidate = candidate_by_id.get(candidate_id)
            if candidate is None:
                calibration_semantic_issues.append({"calibration_id": test.get("calibration_id"), "candidate_id": candidate_id, "issue": "missing candidate"})
                continue
            target_words = _meaningful_words(str(test.get("quote_verbatim", "")))
            candidate_words = _meaningful_words(f"{candidate.get('source_claim', '')} {candidate.get('takeaway_applicavel', '')}")
            target_numbers = set(re.findall(r"\d+(?:[.,]\d+)?", normalize_ascii(str(test.get("quote_verbatim", "")))))
            candidate_numbers = set(re.findall(r"\d+(?:[.,]\d+)?", " ".join(str(item.get("raw", "")) for item in candidate.get("numbers", []))))
            if (target_words and not (target_words & candidate_words)) or (target_numbers and not (target_numbers & candidate_numbers)):
                calibration_semantic_issues.append({"calibration_id": test.get("calibration_id"), "candidate_id": candidate_id, "issue": "candidate may not express calibration proposition"})
    missing_reviews = [chunk["chunk_id"] for chunk in status.get("chunks", []) if chunk["chunk_id"] not in reviews]
    report = {
        "episode_video_id": video_id,
        "read_only": True,
        "reviewed_chunks": len(reviews),
        "missing_reviews": missing_reviews,
        "candidate_count": len(candidates),
        "numbers": number_issues,
        "steps": steps_issues,
        "calibration": calibration_result,
        "calibration_target_errors": calibration_target_issues,
        "editorial_encoding": sorted(set(encoding)),
        "candidate_with_promo_or_interviewer_language": sorted(set(interview_or_promo)),
        "candidate_supported_only_by_interviewer_or_promo": sorted(set(interviewer_only)),
        "claim_evidence_alignment": claim_evidence,
        "ledger_semantic_alignment": ledger_issues,
        "calibration_semantic_alignment": calibration_semantic_issues,
        "reported_case_without_caveat": sorted(set(caveat_issues)),
        "relation_integrity": normalize_relations(candidates),
        "high_signals_without_direct_destination": uncovered,
        "automatic_ledger_preview": automatic_ledger_preview,
        "overlapping_candidates_without_relation": overlaps,
        "chunk_boundaries_to_review": boundaries,
        "transcript_segments": len(transcript),
    }
    hard_categories = {
        "missing_reviews": [{"chunk_id": item} for item in missing_reviews],
        "numbers": number_issues,
        "steps": [{"candidate_id": item, "issue": "procedural candidate needs steps"} for item in steps_issues],
        "editorial_encoding": [{"issue": item} for item in sorted(set(encoding))],
        "ledger": ledger_issues,
        "relation": [{"issue": item} for item in normalize_relations(candidates)],
        "high_signal": uncovered + automatic_ledger_preview,
        "calibration_structure": [{"issue": item} for item in calibration_target_issues],
    }
    if calibration_result["status"] != "pass":
        hard_categories["calibration_coverage"] = [{"issue": "calibration coverage below episode minimum or has duplicate targets"}]
    warning_categories = {
        "promo_or_interviewer": [{"candidate_id": item} for item in sorted(set(interview_or_promo))],
        "interviewer_or_promo_only": [{"candidate_id": item} for item in sorted(set(interviewer_only))],
        "overlap": overlaps,
        "calibration_semantic_ambiguity": calibration_semantic_issues,
        "claim_evidence_alignment": claim_evidence,
        "reported_case_caveat": [{"candidate_id": item, "issue": "reported case has no caveat"} for item in caveat_issues],
    }
    report["hard_blockers"] = [
        item for category, values in hard_categories.items() for item in _classified(category, values, "hard_blocker")
    ]
    report["audit_warnings"] = [
        item for category, values in warning_categories.items() for item in _classified(category, values, "audit_warning")
    ]
    review_categories = {
        "claim_evidence": claim_evidence,
        "ledger": ledger_issues,
        "calibration": calibration_semantic_issues,
        "caveat": [{"candidate_id": item, "issue": "reported case has no caveat"} for item in caveat_issues],
        "relation": [{"issue": item} for item in normalize_relations(candidates)],
        "interviewer_promo": [{"candidate_id": item, "issue": "all evidence is interviewer or promo language"} for item in interviewer_only],
        "overlap": overlaps,
        "high_signal": uncovered + automatic_ledger_preview,
    }
    issues: list[dict[str, Any]] = []
    for category, values in review_categories.items():
        for value in values:
            candidate_ids = sorted(value.get("candidate_ids", [value["candidate_id"]] if value.get("candidate_id") else []))
            segment_ids = sorted(value.get("segment_ids", [value["segment_id"]] if value.get("segment_id") else []))
            issue_id = sha256_semantic_json({"category": category, "candidate_ids": candidate_ids, "segment_ids": segment_ids, "issue": value.get("issue", "")})[:16]
            issues.append({"issue_id": f"semantic-{issue_id}", "category": category, "candidate_ids": candidate_ids, "segment_ids": segment_ids, "evidence": value, "resolution_required": category not in {"claim_evidence", "calibration", "caveat", "interviewer_promo", "overlap"}})
    report["review_required"] = issues
    report["semantic_report_hash"] = sha256_semantic_json(report)
    return report


def autocheck(video_id: str, data_root: Path) -> dict[str, Any]:
    out = data_root / "processed" / video_id / "gold_extraction"
    stored_ledger_path = out / "high_signal_coverage_ledger.json"
    return autocheck_state(
        video_id,
        status=load_json(out / "gold_extraction_status.json"),
        transcript=load_json(out / "transcript_clean.json")["segments"],
        chunks=load_json(out / "chunks" / "chunk_index.json")["chunks"],
        signals=load_json(out / "signal_inventory.json").get("signals", []),
        calibration=load_json(out / "calibration_tests.json"),
        reviews=read_reviews(out / "manual_reviews"),
        stored_ledger=load_json(stored_ledger_path).get("entries", []) if stored_ledger_path.exists() else [],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when deterministic gaps are found.")
    args = parser.parse_args()
    result = autocheck(args.video_id, args.data_root)
    print(json.dumps(result, ensure_ascii=False))
    return 1 if args.strict and result["hard_blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
