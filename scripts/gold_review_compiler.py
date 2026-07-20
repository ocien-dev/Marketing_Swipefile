#!/usr/bin/env python
"""Pure compilation and validation for manual gold review payloads."""

from __future__ import annotations

import copy
import re
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
    numeric_mentions,
    sha256_semantic_json,
    THEME_ALIASES,
    validate_candidate,
)


TYPE_ALIASES = {
    "procedure": "playbook_step",
    "reported_case": "example",
}

COMPACT_PAYLOAD_FORMAT = "gold_episode_compact_v1"
COMPACT_EPISODE_PAYLOAD_FORMAT = "gold_episode_compact_v2"
COMPACT_EPISODE_PAYLOAD_FORMAT_V3 = "gold_episode_compact_v3"
COMPACT_EPISODE_PAYLOAD_FORMATS = {
    COMPACT_EPISODE_PAYLOAD_FORMAT,
    COMPACT_EPISODE_PAYLOAD_FORMAT_V3,
}
COMPACT_CANDIDATE_ALIASES = {
    "id": "candidate_id",
    "claim": "source_claim",
    "takeaway": "takeaway_applicavel",
    "minimal": "minimal_segment_ids",
    "support": "support_segment_ids",
}
COMPACT_V3_TOP_LEVEL_ALIASES = {
    "d": "candidate_defaults",
    "td": "type_defaults",
    "c": "candidates",
    "z": "zero_insight_chunks",
    "l": "ledger_decisions",
    "r": "risk_recall_acknowledgements",
    "w": "audit_warning_dispositions",
    "cal": "calibration_decisions",
}
COMPACT_V3_CANDIDATE_ALIASES = {
    "id": "candidate_id",
    "a": "_local_alias",
    "k": "chunk",
    "t": "title",
    "y": "type",
    "th": "themes",
    "st": "subthemes",
    "cl": "source_claim",
    "ta": "takeaway_applicavel",
    "m": "minimal_segment_ids",
    "s": "support_segment_ids",
    "n": "numbers",
    "p": "steps",
    "co": "conditions",
    "ca": "caveats",
    "rel": "relations",
    "rc": "reported_case",
    "cc": "causal_certainty",
    "cr": "claim_risk",
    "pt": "process_tags",
}
COMPACT_V3_NUMBER_ALIASES = {
    "r": "raw",
    "v": "value",
    "lo": "min_value",
    "hi": "max_value",
    "k": "unit_kind",
    "u": "unit",
    "p": "period",
    "o": "role",
    "s": "value_status",
    "sid": "source_segment_id",
    "si": "source_clean_index",
    "sp": "source_span",
    "sl": "source_literal",
    "so": "source_occurrence",
}

NUMBER_SOURCE_FIELDS = {
    "source_segment_id", "source_clean_index", "source_span", "source_literal",
    "source_occurrence",
}

THEME_SUGGESTIONS = {
    "storytelling": ["copywriting"],
    "competitive_analysis": ["audience_market", "creative_strategy"],
    "affiliate_marketing": ["business_model", "sales_relationship"],
    "product_development": ["product_strategy", "delivery_support"],
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
        if isinstance(raw_id, dict) and isinstance(raw_id.get("range"), list):
            bounds = raw_id["range"]
            if len(bounds) != 2:
                resolved.append(str(raw_id))
                continue
            try:
                start, end = int(bounds[0]), int(bounds[1])
            except (TypeError, ValueError):
                resolved.append(str(raw_id))
                continue
            step = 1 if end >= start else -1
            for clean_index in range(start, end + step, step):
                if clean_index in segments_by_index:
                    resolved.append(segments_by_index[clean_index]["segment_id"])
                else:
                    resolved.append(f"<missing-clean-index:{clean_index}>")
            continue
        segment_id = str(raw_id)
        suffix = segment_id.rsplit("-", 1)[-1]
        if segment_id in segments:
            resolved.append(segment_id)
        elif index_mode == "zero_based" and suffix.isdigit() and int(suffix) in segments_by_index:
            resolved.append(segments_by_index[int(suffix)]["segment_id"])
        elif suffix.isdigit() and int(suffix) in segments_by_index:
            resolved.append(segments_by_index[int(suffix)]["segment_id"])
        else:
            resolved.append(segment_id)
    return resolved


def expand_compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Expand the optional model-facing compact payload without touching quotes.

    The compiler remains the only authority that turns segment selectors into
    verbatim citations.  Compact drafts only remove repeated editorial
    boilerplate and may use clean-index ranges for evidence references.
    """
    expanded = copy.deepcopy(payload)
    if expanded.get("payload_format") != COMPACT_PAYLOAD_FORMAT:
        return expanded
    defaults = expanded.pop("candidate_defaults", {})
    if not isinstance(defaults, dict):
        defaults = {}
    reviews = expanded.get("reviews", [])
    if not isinstance(reviews, list):
        return expanded
    for review in reviews:
        if not isinstance(review, dict) or not isinstance(review.get("candidates", []), list):
            continue
        review_defaults = review.pop("candidate_defaults", {})
        if not isinstance(review_defaults, dict):
            review_defaults = {}
        candidates: list[Any] = []
        for raw_candidate in review.get("candidates", []):
            if not isinstance(raw_candidate, dict):
                candidates.append(raw_candidate)
                continue
            candidate = {**copy.deepcopy(defaults), **copy.deepcopy(review_defaults), **copy.deepcopy(raw_candidate)}
            for compact_name, canonical_name in COMPACT_CANDIDATE_ALIASES.items():
                if compact_name in candidate and canonical_name not in candidate:
                    candidate[canonical_name] = candidate.pop(compact_name)
            candidates.append(candidate)
        review["candidates"] = candidates
    return expanded


def _expand_v3_evidence_selectors(value: Any) -> Any:
    if not isinstance(value, list):
        return value
    expanded: list[Any] = []
    for item in value:
        if isinstance(item, list) and len(item) == 2:
            expanded.append({"range": copy.deepcopy(item)})
        else:
            expanded.append(copy.deepcopy(item))
    return expanded


def _expand_v3_numbers(value: Any) -> Any:
    if not isinstance(value, list):
        return value
    expanded: list[Any] = []
    fields = (
        "raw", "value", "min_value", "max_value", "unit_kind", "unit",
        "period", "role", "value_status",
    )
    for item in value:
        if isinstance(item, list) and len(item) == len(fields):
            record = dict(zip(fields, copy.deepcopy(item)))
            record["denominator"] = None
            record["attribution_window"] = None
            expanded.append(record)
            continue
        if isinstance(item, dict):
            record = {
                COMPACT_V3_NUMBER_ALIASES.get(key, key): copy.deepcopy(field_value)
                for key, field_value in item.items()
            }
            record.setdefault("denominator", None)
            record.setdefault("attribution_window", None)
            expanded.append(record)
            continue
        expanded.append(copy.deepcopy(item))
    return expanded


def _source_canonical_number_raw(
    candidate_id: str,
    record: dict[str, Any],
    *,
    evidence_segment_ids: set[str],
    segments: dict[str, dict[str, Any]],
    segments_by_index: dict[int, dict[str, Any]],
    issues: list[dict[str, str]],
) -> None:
    """Copy numeric raw from one explicitly selected evidence segment."""
    selector_fields = NUMBER_SOURCE_FIELDS & set(record)
    if not selector_fields:
        return
    raw_segment_id = record.get("source_segment_id")
    raw_clean_index = record.get("source_clean_index")
    segment: dict[str, Any] | None = None
    if raw_segment_id is not None:
        segment = segments.get(str(raw_segment_id))
        if segment is None:
            issues.append(_issue(candidate_id, "numbers.source_segment_id", "source", str(raw_segment_id), "reference a transcript segment from this episode"))
    if raw_clean_index is not None:
        try:
            by_index = segments_by_index.get(int(raw_clean_index))
        except (TypeError, ValueError):
            by_index = None
        if by_index is None:
            issues.append(_issue(candidate_id, "numbers.source_clean_index", "source", repr(raw_clean_index), "reference a valid zero-based clean index"))
        elif segment is not None and by_index.get("segment_id") != segment.get("segment_id"):
            issues.append(_issue(candidate_id, "numbers", "source", repr({"source_segment_id": raw_segment_id, "source_clean_index": raw_clean_index}), "use selectors that identify the same transcript segment"))
        else:
            segment = by_index
    if segment is None:
        issues.append(_issue(candidate_id, "numbers", "source", repr({key: record.get(key) for key in sorted(selector_fields)}), "provide source_segment_id or source_clean_index for source-canonical raw"))
        return
    segment_id = str(segment["segment_id"])
    if segment_id not in evidence_segment_ids:
        issues.append(_issue(candidate_id, "numbers", "source", segment_id, "the numeric source segment must also be candidate evidence"))
        return
    text = str(segment.get("text", ""))
    span = record.get("source_span")
    source_literal = record.get("source_literal")
    selected: str | None = None
    if span is not None:
        if not isinstance(span, list) or len(span) != 2:
            issues.append(_issue(candidate_id, "numbers.source_span", "source", repr(span), "use [start, end] character offsets within the selected segment"))
            return
        try:
            start, end = int(span[0]), int(span[1])
        except (TypeError, ValueError):
            issues.append(_issue(candidate_id, "numbers.source_span", "source", repr(span), "use integer [start, end] character offsets"))
            return
        if start < 0 or end <= start or end > len(text):
            issues.append(_issue(candidate_id, "numbers.source_span", "source", repr(span), f"use offsets inside a {len(text)}-character segment"))
            return
        selected = text[start:end]
        if source_literal is not None and selected != str(source_literal):
            issues.append(_issue(
                candidate_id,
                "numbers.source_literal",
                "source",
                repr(source_literal),
                "source_literal must equal the exact text selected by source_span",
            ))
            return
    elif source_literal is not None:
        literal = str(source_literal)
        positions = [match.start() for match in re.finditer(re.escape(literal), text)] if literal else []
        if len(positions) != 1:
            issues.append(_issue(
                candidate_id,
                "numbers.source_literal",
                "source",
                repr(source_literal),
                "use a non-empty literal that occurs exactly once, or add source_span",
            ))
            return
        selected = literal
    else:
        mentions = numeric_mentions(text)
        try:
            occurrence = int(record.get("source_occurrence", 0))
        except (TypeError, ValueError):
            occurrence = -1
        if occurrence < 0 or occurrence >= len(mentions):
            issues.append(_issue(candidate_id, "numbers.source_occurrence", "source", repr(record.get("source_occurrence", 0)), f"choose an occurrence from 0 to {max(len(mentions) - 1, 0)}"))
            return
        selected = str(mentions[occurrence]["raw"])
    if not selected:
        issues.append(_issue(candidate_id, "numbers.raw", "source", repr(selected), "source-canonical numeric raw must be non-empty"))
        return
    record["raw"] = selected


def repair_scaffold(issues: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a deterministic repair surface without fabricating semantics."""
    rows = []
    for item in issues:
        row = {
            "candidate_id": item.get("candidate_id", "<unknown>"),
            "field": item.get("field"),
            "category": item.get("category"),
            "current": item.get("evidence"),
            "expected": item.get("expected"),
            "requires_semantic_judgment": item.get("category") in {
                "claim", "relation", "taxonomy", "ledger", "calibration", "validation",
            },
        }
        rows.append(row)
    return {
        "schema_version": "1.0.0",
        "issue_count": len(rows),
        "issues": rows,
        "mechanical_fields": sorted({
            str(row["field"]) for row in rows
            if not row["requires_semantic_judgment"] and row.get("field")
        }),
        "semantic_fields": sorted({
            str(row["field"]) for row in rows
            if row["requires_semantic_judgment"] and row.get("field")
        }),
    }


def _expand_v3_candidate(value: Any) -> Any:
    if not isinstance(value, dict):
        return copy.deepcopy(value)
    candidate = {
        COMPACT_V3_CANDIDATE_ALIASES.get(key, key): copy.deepcopy(field_value)
        for key, field_value in value.items()
    }
    for field in ("minimal_segment_ids", "support_segment_ids"):
        if field in candidate:
            candidate[field] = _expand_v3_evidence_selectors(candidate[field])
    if "numbers" in candidate:
        candidate["numbers"] = _expand_v3_numbers(candidate["numbers"])
    relations = candidate.get("relations")
    if isinstance(relations, dict):
        candidate["relations"] = {
            "_parent_alias" if key == "p" else "_children_aliases" if key == "c" else key: copy.deepcopy(field_value)
            for key, field_value in relations.items()
        }
    return candidate


def expand_compact_episode_payload_v3(payload: dict[str, Any]) -> dict[str, Any]:
    """Expand the authoring-only v3 shorthand into the compatible v2 shape."""
    if payload.get("payload_format") != COMPACT_EPISODE_PAYLOAD_FORMAT_V3:
        return copy.deepcopy(payload)
    expanded = {
        COMPACT_V3_TOP_LEVEL_ALIASES.get(key, key): copy.deepcopy(value)
        for key, value in payload.items()
    }
    expanded["payload_format"] = COMPACT_EPISODE_PAYLOAD_FORMAT
    defaults = expanded.get("candidate_defaults", {})
    expanded["candidate_defaults"] = _expand_v3_candidate(defaults) if isinstance(defaults, dict) else defaults
    raw_type_defaults = expanded.pop("type_defaults", {})
    type_defaults = {}
    if isinstance(raw_type_defaults, dict):
        type_defaults = {
            str(candidate_type): _expand_v3_candidate(value)
            for candidate_type, value in raw_type_defaults.items()
            if isinstance(value, dict)
        }
    candidates: list[Any] = []
    raw_candidates = expanded.get("candidates", [])
    if isinstance(raw_candidates, list):
        for raw_candidate in raw_candidates:
            candidate = _expand_v3_candidate(raw_candidate)
            if isinstance(candidate, dict):
                raw_type = str(candidate.get("type", ""))
                candidate_type = TYPE_ALIASES.get(raw_type, raw_type)
                candidate = {
                    **copy.deepcopy(type_defaults.get(candidate_type, {})),
                    **candidate,
                }
            candidates.append(candidate)
        expanded["candidates"] = candidates
    return expanded


def hydrate_episode_payload(
    video_id: str,
    payload: dict[str, Any],
    status: dict[str, Any],
    existing_reviews: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Hydrate an episode-level compact draft into canonical chunk reviews.

    The model states each candidate once.  A small numeric ``chunk`` selector
    replaces repeated review boilerplate; the compiler restores hashes,
    routes, citations, and explicit zero-insight reviews deterministically.
    """
    if payload.get("payload_format") == COMPACT_EPISODE_PAYLOAD_FORMAT_V3:
        payload = expand_compact_episode_payload_v3(payload)
    if payload.get("payload_format") != COMPACT_EPISODE_PAYLOAD_FORMAT:
        return payload, []
    issues: list[dict[str, str]] = []
    expanded = copy.deepcopy(payload)
    replace_existing_reviews = bool(expanded.pop("_replace_existing_reviews", False))
    raw_candidates = expanded.get("candidates", [])
    if not isinstance(raw_candidates, list):
        return expanded, [_issue("<payload>", "candidates", "contract", repr(raw_candidates), "provide an episode-level candidate list")]
    defaults = expanded.get("candidate_defaults", {})
    if not isinstance(defaults, dict):
        defaults = {}
        issues.append(_issue("<payload>", "candidate_defaults", "contract", repr(expanded.get("candidate_defaults")), "provide an object"))
    chunks = {int(item["chunk_number"]): item for item in status.get("chunks", []) if isinstance(item, dict) and str(item.get("chunk_number", "")).isdigit()}
    existing_chunk_ids = (
        set()
        if replace_existing_reviews
        else {review.get("chunk_id") for review in existing_reviews.values() if isinstance(review, dict)}
    )
    existing_ids = [
        str(candidate.get("candidate_id", ""))
        for review in existing_reviews.values() if isinstance(review, dict)
        for candidate in review.get("candidates", []) if isinstance(candidate, dict)
    ]
    next_id = max(
        [int(match.group(1)) for value in existing_ids if (match := re.search(r"-G(\d+)$", value))] or [0]
    ) + 1
    grouped: dict[int, list[dict[str, Any]]] = {}
    local_aliases: dict[str, str] = {}
    for position, raw_candidate in enumerate(raw_candidates):
        if not isinstance(raw_candidate, dict):
            issues.append(_issue(f"<candidate:{position}>", "candidate", "contract", repr(raw_candidate), "provide a candidate object"))
            continue
        candidate = {**copy.deepcopy(defaults), **copy.deepcopy(raw_candidate)}
        for compact_name, canonical_name in COMPACT_CANDIDATE_ALIASES.items():
            if compact_name in candidate and canonical_name not in candidate:
                candidate[canonical_name] = candidate.pop(compact_name)
        raw_chunk = candidate.pop("chunk", candidate.pop("chunk_number", None))
        try:
            if isinstance(raw_chunk, bool):
                raise ValueError
            chunk_number = int(raw_chunk)
        except (TypeError, ValueError):
            issues.append(_issue(str(candidate.get("candidate_id", f"<candidate:{position}>")), "chunk", "contract", repr(raw_chunk), "provide the prepared chunk number"))
            continue
        if chunk_number not in chunks:
            issues.append(_issue(str(candidate.get("candidate_id", f"<candidate:{position}>")), "chunk", "contract", str(chunk_number), "use a prepared chunk number"))
            continue
        if not candidate.get("candidate_id"):
            candidate["candidate_id"] = f"{video_id}-G{next_id:03d}"
            next_id += 1
        local_alias = candidate.pop("_local_alias", None)
        if local_alias is not None:
            alias = str(local_alias).strip()
            if not alias:
                issues.append(_issue(str(candidate["candidate_id"]), "alias", "contract", repr(local_alias), "use a non-empty local alias"))
            elif alias in local_aliases:
                issues.append(_issue(str(candidate["candidate_id"]), "alias", "duplicate", alias, "use a unique local alias"))
            else:
                local_aliases[alias] = str(candidate["candidate_id"])
        grouped.setdefault(chunk_number, []).append(candidate)
    candidate_ids = {
        str(candidate.get("candidate_id"))
        for candidates in grouped.values()
        for candidate in candidates
        if candidate.get("candidate_id")
    }
    for candidates in grouped.values():
        for candidate in candidates:
            relations = candidate.get("relations")
            if not isinstance(relations, dict):
                continue
            parent_alias = relations.pop("_parent_alias", None)
            children_aliases = relations.pop("_children_aliases", None)
            if parent_alias is not None:
                parent_key = str(parent_alias)
                parent_id = local_aliases.get(parent_key, parent_key if parent_key in candidate_ids else None)
                if parent_id is None:
                    issues.append(_issue(str(candidate.get("candidate_id")), "relations.parent", "relation", parent_key, "reference a local alias or candidate id from this payload"))
                else:
                    relations["parent_candidate_id"] = parent_id
            if children_aliases is not None:
                if not isinstance(children_aliases, list):
                    issues.append(_issue(str(candidate.get("candidate_id")), "relations.children", "relation", repr(children_aliases), "provide a list of local aliases or candidate ids"))
                else:
                    resolved_children: list[str] = []
                    for child_alias in children_aliases:
                        child_key = str(child_alias)
                        child_id = local_aliases.get(child_key, child_key if child_key in candidate_ids else None)
                        if child_id is None:
                            issues.append(_issue(str(candidate.get("candidate_id")), "relations.children", "relation", child_key, "reference a local alias or candidate id from this payload"))
                        elif child_id not in resolved_children:
                            resolved_children.append(child_id)
                    relations["child_candidate_ids"] = resolved_children
            relations.setdefault("parent_candidate_id", None)
            relations.setdefault("child_candidate_ids", [])
    zero_chunks: set[int] = set()
    for raw in expanded.get("zero_insight_chunks", []):
        try:
            zero_chunks.add(int(raw))
        except (TypeError, ValueError):
            issues.append(_issue("<payload>", "zero_insight_chunks", "contract", repr(raw), "use numeric prepared chunk numbers"))
    overlap = sorted(set(grouped) & zero_chunks)
    for number in overlap:
        issues.append(_issue("<payload>", "zero_insight_chunks", "contract", str(number), "a chunk cannot contain candidates and be zero-insight"))
    decisions_by_chunk: dict[int, list[dict[str, Any]]] = {}
    for position, decision in enumerate(expanded.get("ledger_decisions", [])):
        if not isinstance(decision, dict):
            issues.append(_issue(f"<ledger:{position}>", "ledger_decision", "contract", repr(decision), "provide a ledger decision object"))
            continue
        raw_chunk = decision.get("chunk_number")
        try:
            chunk_number = int(raw_chunk)
        except (TypeError, ValueError):
            issues.append(_issue(f"<ledger:{position}>", "chunk_number", "contract", repr(raw_chunk), "provide the owning prepared chunk number"))
            continue
        clean = {key: value for key, value in decision.items() if key != "chunk_number"}
        decisions_by_chunk.setdefault(chunk_number, []).append(clean)
    pending_numbers = [number for number, item in chunks.items() if item.get("chunk_id") not in existing_chunk_ids]
    covered_numbers = set(grouped) | zero_chunks | set(decisions_by_chunk)
    for number in sorted(set(pending_numbers) - covered_numbers):
        issues.append(_issue("<payload>", "episode_coverage", "coverage", str(number), "include candidates or list the chunk in zero_insight_chunks"))
    reviews = [
        {
            "chunk_number": number,
            "candidates": grouped.get(number, []),
            "ledger_decisions": decisions_by_chunk.get(number, []),
        }
        for number in sorted(covered_numbers)
        if number in chunks and chunks[number].get("chunk_id") not in existing_chunk_ids
    ]
    hydrated = {
        "episode_video_id": expanded.get("episode_video_id", video_id),
        "payload_format": COMPACT_PAYLOAD_FORMAT,
        "segment_index_mode": expanded.get("segment_index_mode", "zero_based"),
        "reviews": reviews,
        "risk_recall_acknowledgements": copy.deepcopy(expanded.get("risk_recall_acknowledgements", [])),
        "audit_warning_dispositions": copy.deepcopy(expanded.get("audit_warning_dispositions", [])),
        "calibration_decisions": copy.deepcopy(expanded.get("calibration_decisions", [])),
        "enforce_risk_recall": True,
    }
    return hydrated, issues


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
            suggestions = THEME_SUGGESTIONS.get(key, [])
            expected = "use a canonical theme or an alias from the closed theme table"
            if suggestions:
                expected += f"; review and choose explicitly from {suggestions}"
            issues.append(_issue(candidate_id, "themes", "taxonomy", source, expected))
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
    raw_numbers = candidate.get("numbers", [])
    if isinstance(raw_numbers, list):
        for number_index, record in enumerate(raw_numbers):
            if not isinstance(record, dict):
                continue
            _source_canonical_number_raw(
                candidate_id,
                record,
                evidence_segment_ids=set(valid_ids),
                segments=segments,
                segments_by_index=segments_by_index,
                issues=issues,
            )
            for field in NUMBER_SOURCE_FIELDS:
                record.pop(field, None)
    else:
        issues.append(_issue(candidate_id, "numbers", "contract", repr(raw_numbers), "provide a list of structured number records"))
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
        invalid_payload_issues = [_issue("<payload>", "payload", "contract", repr(payload), "provide an object with a reviews list")]
        return {
            "status": "error", "issues": invalid_payload_issues,
            "reviews": [], "review_paths": {}, "normalized_existing_reviews": existing_reviews,
            "composed_reviews": existing_reviews,
            "semantic_sha256": sha256_semantic_json({"video_id": video_id, "reviews": []}), "candidate_count": 0,
            "repair_scaffold": repair_scaffold(invalid_payload_issues),
        }
    payload, hydration_issues = hydrate_episode_payload(video_id, payload, status, existing_reviews)
    issues.extend(hydration_issues)
    payload = expand_compact_payload(payload)
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
    calibration_decisions = copy.deepcopy(payload.get("calibration_decisions", []))
    signature = sha256_semantic_json({
        "video_id": video_id,
        "reviews": compiled_reviews,
        "calibration_decisions": calibration_decisions,
    })
    return {
        "status": "ok" if not issues else "error",
        "issues": issues,
        "reviews": compiled_reviews,
        "review_paths": dict(drafts),
        "normalized_existing_reviews": existing_reviews,
        "composed_reviews": composed,
        "semantic_sha256": signature,
        "candidate_count": sum(len(review["candidates"]) for review in compiled_reviews),
        "calibration_decisions": calibration_decisions,
        "repair_scaffold": repair_scaffold(issues),
    }
