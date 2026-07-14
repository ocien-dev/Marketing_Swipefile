#!/usr/bin/env python
"""Pure compilation and validation for manual gold review payloads."""

from __future__ import annotations

import copy
import unicodedata
from typing import Any

from scripts.gold_extraction_common import (
    CANONICAL_THEMES,
    EXCLUSION_REASON_CODES,
    SCHEMA_VERSION,
    citation,
    default_process_tags,
    editorial_ascii_errors,
    normalize_ascii,
    normalize_relations,
    sha256_semantic_json,
    THEME_ALIASES,
    validate_candidate,
)


TYPE_ALIASES = {
    "procedure": "playbook_step",
    "reported_case": "example",
}


def _repair_editorial(value: Any) -> str:
    text = str(value or "")
    if "Ã" in text or "Â" in text:
        for encoding in ("latin-1", "cp1252"):
            try:
                text = text.encode(encoding).decode("utf-8")
                break
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _issue(candidate_id: str, field: str, category: str, evidence: str, expected: str) -> dict[str, str]:
    return {
        "candidate_id": candidate_id or "<unknown>",
        "field": field,
        "category": category,
        "evidence": evidence,
        "expected": expected,
    }


def _resolved_ids(
    raw_ids: list[Any],
    index_mode: str | None,
    segments: dict[str, dict[str, Any]],
    segments_by_index: dict[int, dict[str, Any]],
) -> list[str]:
    resolved: list[str] = []
    for raw_id in raw_ids:
        segment_id = str(raw_id)
        suffix = segment_id.rsplit("-", 1)[-1]
        if index_mode == "zero_based" and suffix.isdigit() and int(suffix) in segments_by_index:
            resolved.append(segments_by_index[int(suffix)]["segment_id"])
        elif segment_id in segments:
            resolved.append(segment_id)
        elif suffix.isdigit() and int(suffix) in segments_by_index:
            resolved.append(segments_by_index[int(suffix)]["segment_id"])
        else:
            resolved.append(segment_id)
    return resolved


def _compile_themes(candidate_id: str, raw_themes: Any, raw_subthemes: Any, issues: list[dict[str, str]]) -> tuple[list[str], list[str]]:
    """Normalize only closed taxonomy entries; unknown terms must block apply."""
    if not isinstance(raw_themes, list):
        issues.append(_issue(candidate_id, "themes", "taxonomy", repr(raw_themes), "provide a list of canonical themes or approved aliases"))
        raw_themes = []
    if not isinstance(raw_subthemes, list):
        issues.append(_issue(candidate_id, "subthemes", "contract", repr(raw_subthemes), "provide a list of specific retrieval terms"))
        raw_subthemes = []
    themes: list[str] = []
    provenance: list[str] = [str(item) for item in raw_subthemes if str(item).strip()]
    for raw_theme in raw_themes:
        if not isinstance(raw_theme, str) or not raw_theme.strip():
            issues.append(_issue(candidate_id, "themes", "taxonomy", repr(raw_theme), "use a non-empty canonical theme or approved alias"))
            continue
        source = raw_theme.strip()
        key = normalize_ascii(source).replace(" ", "_").replace("-", "_")
        mapped = THEME_ALIASES.get(key)
        if mapped is None and key in CANONICAL_THEMES:
            mapped = key
        if mapped is None:
            issues.append(_issue(candidate_id, "themes", "taxonomy", source, "use a canonical theme or an alias from the closed theme table"))
            if source not in provenance:
                provenance.append(source)
            continue
        if mapped not in themes:
            themes.append(mapped)
        if source != mapped and source not in provenance:
            provenance.append(source)
    return themes, provenance


def _candidate_draft(
    video_id: str,
    raw_candidate: dict[str, Any],
    chunk: dict[str, Any],
    segments: dict[str, dict[str, Any]],
    segments_by_index: dict[int, dict[str, Any]],
    index_mode: str | None,
    issues: list[dict[str, str]],
) -> dict[str, Any] | None:
    candidate = copy.deepcopy(raw_candidate)
    candidate_id = str(candidate.get("candidate_id", "<unknown>"))
    for field in ("title", "source_claim", "takeaway_applicavel"):
        if field in candidate:
            candidate[field] = _repair_editorial(candidate[field])
    themes, mapped_subthemes = _compile_themes(candidate_id, candidate.get("themes", []), candidate.get("subthemes", []), issues)
    candidate["themes"] = themes
    candidate["subthemes"] = list(dict.fromkeys(mapped_subthemes))
    raw_type = str(candidate.get("type", "")).strip()
    candidate["type"] = TYPE_ALIASES.get(raw_type, raw_type)
    if raw_type == "reported_case":
        candidate["reported_case"] = True
    raw_minimal_ids = candidate.pop("minimal_segment_ids", [])
    raw_support_ids = candidate.pop("support_segment_ids", [])
    if not isinstance(raw_minimal_ids, list):
        issues.append(_issue(candidate_id, "minimal_segment_ids", "source", repr(raw_minimal_ids), "provide a list of transcript segment ids"))
        raw_minimal_ids = []
    if not isinstance(raw_support_ids, list):
        issues.append(_issue(candidate_id, "support_segment_ids", "source", repr(raw_support_ids), "provide a list of transcript segment ids"))
        raw_support_ids = []
    minimal_ids = _resolved_ids(raw_minimal_ids, index_mode, segments, segments_by_index)
    support_ids = _resolved_ids(raw_support_ids, index_mode, segments, segments_by_index)
    all_ids = minimal_ids + support_ids
    if not minimal_ids:
        issues.append(_issue(candidate_id, "minimal_segment_ids", "source", "candidate has no minimal segment", "provide one or more transcript segment ids"))
    missing = [segment_id for segment_id in all_ids if segment_id not in segments]
    if missing:
        issues.append(_issue(candidate_id, "evidence", "source", ", ".join(missing), "use only transcript segment ids from this episode"))
    valid_minimal_ids = [segment_id for segment_id in minimal_ids if segment_id in segments]
    valid_support_ids = [segment_id for segment_id in support_ids if segment_id in segments]
    valid_ids = valid_minimal_ids + valid_support_ids
    citations = [citation(segments[segment_id]) for segment_id in valid_ids]
    candidate["chunk_id"] = chunk["chunk_id"]
    candidate.setdefault("process_tags", default_process_tags(themes))
    candidate.setdefault("context", {"episode_video_id": video_id, "source_kind": "transcript"})
    candidate.setdefault("reported_case", False)
    candidate.setdefault("causal_certainty", "not_applicable")
    candidate.setdefault("claim_risk", "low")
    candidate.setdefault("numbers", [])
    candidate.setdefault("steps", [])
    candidate.setdefault("conditions", [])
    candidate.setdefault("caveats", [])
    context_range = {}
    if valid_ids:
        context_range = {
            "segment_start": min(segments[segment_id]["clean_index"] for segment_id in valid_ids),
            "segment_end": max(segments[segment_id]["clean_index"] for segment_id in valid_ids),
            "start_seconds": min(item["start_seconds"] for item in citations),
            "end_seconds": max(item["end_seconds"] for item in citations),
        }
    candidate["evidence"] = {
        "minimal_quote": [citation(segments[segment_id]) for segment_id in valid_minimal_ids],
        "context_range": context_range,
        "support_segments": [citation(segments[segment_id]) for segment_id in valid_support_ids],
    }
    if not isinstance(candidate.get("relations"), dict):
        issues.append(_issue(candidate_id, "relations", "contract", repr(candidate.get("relations")), "use an object with parent_candidate_id and child_candidate_ids"))
        candidate["relations"] = {"parent_candidate_id": None, "child_candidate_ids": []}
    candidate.setdefault("relations", {"parent_candidate_id": None, "child_candidate_ids": []})
    return candidate


def compile_payload(
    video_id: str,
    payload: dict[str, Any],
    status: dict[str, Any],
    transcript_segments: list[dict[str, Any]],
    existing_reviews: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Compile all drafts and return every validation issue without writing."""
    issues: list[dict[str, str]] = []
    if not isinstance(payload, dict):
        return {
            "status": "error", "issues": [_issue("<payload>", "payload", "contract", repr(payload), "provide an object with a reviews list")],
            "reviews": [], "review_paths": {}, "normalized_existing_reviews": existing_reviews,
            "composed_reviews": existing_reviews,
            "semantic_sha256": sha256_semantic_json({"video_id": video_id, "reviews": []}), "candidate_count": 0,
        }
    if payload.get("episode_video_id") not in {None, video_id}:
        issues.append(_issue("<payload>", "episode_video_id", "contract", str(payload.get("episode_video_id")), video_id))
    segments = {item["segment_id"]: item for item in transcript_segments}
    segments_by_index = {int(item["clean_index"]): item for item in transcript_segments}
    chunks: dict[int, dict[str, Any]] = {}
    for item in status.get("chunks", []):
        if not isinstance(item, dict):
            issues.append(_issue("<status>", "chunks", "contract", repr(item), "use prepared chunk objects"))
            continue
        try:
            chunks[int(item["chunk_number"])] = item
        except (KeyError, TypeError, ValueError):
            issues.append(_issue("<status>", "chunk_number", "contract", repr(item.get("chunk_number")), "use numeric prepared chunk numbers"))
    index_mode = payload.get("segment_index_mode")
    drafts: dict[str, dict[str, Any]] = {}
    target_chunk_ids: set[str] = set()
    raw_reviews = payload.get("reviews", [])
    if not isinstance(raw_reviews, list):
        issues.append(_issue("<payload>", "reviews", "contract", repr(raw_reviews), "provide a list of review objects"))
        raw_reviews = []
    for review_index, raw_review in enumerate(raw_reviews):
        if not isinstance(raw_review, dict):
            issues.append(_issue(f"<review:{review_index}>", "review", "contract", repr(raw_review), "provide a review object"))
            continue
        raw_number = raw_review.get("chunk_number", -1)
        try:
            if isinstance(raw_number, bool):
                raise ValueError
            number = int(raw_number)
        except (TypeError, ValueError):
            issues.append(_issue(f"<review:{review_index}>", "chunk_number", "contract", repr(raw_number), "use a numeric prepared chunk number"))
            continue
        if number not in chunks:
            issues.append(_issue("<review>", "chunk_number", "contract", f"unknown chunk_number {number}", "use a prepared chunk number"))
            continue
        chunk = chunks[number]
        if chunk["chunk_id"] in target_chunk_ids:
            issues.append(_issue("<review>", "chunk_number", "duplicate", chunk["chunk_id"], "one review per chunk"))
            continue
        target_chunk_ids.add(chunk["chunk_id"])
        candidates = []
        raw_candidates = raw_review.get("candidates", [])
        if not isinstance(raw_candidates, list):
            issues.append(_issue(f"<review:{number}>", "candidates", "contract", repr(raw_candidates), "provide a list of candidate objects"))
            raw_candidates = []
        for candidate_index, raw_candidate in enumerate(raw_candidates):
            if not isinstance(raw_candidate, dict):
                issues.append(_issue(f"<review:{number}:{candidate_index}>", "candidate", "contract", repr(raw_candidate), "provide a candidate object"))
                continue
            candidate = _candidate_draft(video_id, raw_candidate, chunk, segments, segments_by_index, index_mode, issues)
            if candidate is not None:
                candidates.append(candidate)
        raw_decisions = raw_review.get("ledger_decisions", [])
        if not isinstance(raw_decisions, list):
            issues.append(_issue(f"<review:{number}>", "ledger_decisions", "contract", repr(raw_decisions), "provide a list of ledger decision objects"))
            raw_decisions = []
        decisions = copy.deepcopy(raw_decisions)
        for decision_index, decision in enumerate(decisions):
            if not isinstance(decision, dict):
                issues.append(_issue(f"<ledger:{number}:{decision_index}>", "ledger_decision", "contract", repr(decision), "provide a ledger decision object"))
                continue
            if decision.get("disposition") == "excluded" and decision.get("reason_code") not in EXCLUSION_REASON_CODES:
                issues.append(_issue("<ledger>", "reason_code", "ledger", str(decision.get("reason_code")), "use a valid excluded reason code"))
            if decision.get("reason_code") == "duplicate_of" and not decision.get("reason_reference"):
                issues.append(_issue("<ledger>", "reason_reference", "ledger", "missing", "reference an existing final candidate"))
        review = {
            "schema_version": SCHEMA_VERSION,
            "episode_video_id": video_id,
            "chunk_id": chunk["chunk_id"],
            "input_hash": chunk["input_hash"],
            "review_route": "codex_manual_no_paid_api",
            "full_chunk_reviewed": True,
            "reviewer_effort_minutes": raw_review.get("reviewer_effort_minutes"),
            "candidates": candidates,
            "ledger_decisions": decisions,
        }
        drafts[f"chunk_{number:03d}_review.json"] = review
    composed = {**existing_reviews, **{path: review for path, review in drafts.items()}}
    all_candidates = [candidate for review in composed.values() if isinstance(review, dict) for candidate in review.get("candidates", []) if isinstance(candidate, dict)]
    candidate_ids = [str(candidate.get("candidate_id", "")) for candidate in all_candidates]
    duplicates = sorted({item for item in candidate_ids if item and candidate_ids.count(item) > 1})
    for candidate_id in duplicates:
        issues.append(_issue(candidate_id, "candidate_id", "duplicate", "duplicate candidate_id across persisted reviews and recorder payload", "use a globally unique candidate id"))
    chunk_ids = {item["chunk_id"] for item in status.get("chunks", [])}
    for candidate in all_candidates:
        candidate_id = str(candidate.get("candidate_id", "<unknown>"))
        for error in validate_candidate(candidate, segments, chunk_ids):
            issues.append(_issue(candidate_id, "candidate", "validation", error, "repair the candidate contract"))
        for error in editorial_ascii_errors(candidate):
            issues.append(_issue(candidate_id, "editorial", "encoding", error, "use ASCII/NFKD editorial text"))
    for error in normalize_relations(all_candidates):
        issues.append(_issue("<relations>", "relations", "relation", error, "use symmetric acyclic candidate relations"))
    compiled_reviews = [drafts[path] for path in sorted(drafts)]
    signature = sha256_semantic_json({"video_id": video_id, "reviews": compiled_reviews})
    return {
        "status": "ok" if not issues else "error",
        "issues": issues,
        "reviews": compiled_reviews,
        "review_paths": dict(drafts),
        "normalized_existing_reviews": existing_reviews,
        "composed_reviews": composed,
        "semantic_sha256": signature,
        "candidate_count": sum(len(review["candidates"]) for review in compiled_reviews),
    }
