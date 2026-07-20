#!/usr/bin/env python3
"""Archived global-reducer research; never a production gold route.

The reducer is deliberately split into deterministic preparation/validation and
one stateless model synthesis call. Approved gold candidates are unavailable to
the reducer and are introduced only when building the compact judge packet.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
import time
import unicodedata
from pathlib import Path
from typing import Any, Iterable

from scripts.gold_semantic_compiler import semantic_hash, write_json


REDUCER_VERSION = "gold-semantic-global-reducer-v1"
NUMBER_RE = re.compile(
    r"(?i)(?:R\$\s*)?\d+(?:[.,]\d+)*(?:\s*%|\s*x|\s*vezes|\s*dias?|\s*meses?|\s*anos?)?"
    r"|\b(?:dois|duas|tr[eê]s|quatro|cinco|seis|sete|oito|nove|dez|"
    r"onze|doze|treze|catorze|quatorze|quinze|vinte|trinta|quarenta|cinquenta|"
    r"cem|cento|mil|milh[aã]o|milh[oõ]es|bilh[aã]o|bilh[oõ]es)\b"
)
FRAMEWORK_RE = re.compile(
    r"(?i)\b(?:primeir[oa]|segund[oa]|terceir[oa]|quart[oa]|quint[oa]|sext[oa]|"
    r"s[eé]tim[oa]|[uú]ltim[oa]|alavanca|pontos?|passos?|etapas?|framework)\b"
)
TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do", "dos",
    "e", "ela", "ele", "em", "essa", "esse", "isso", "na", "nas", "no", "nos",
    "o", "os", "ou", "para", "por", "que", "se", "sem", "um", "uma", "usar",
}


REDUCER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "episode_video_id", "candidates", "numeric_dispositions",
        "calibration_dispositions", "summary",
    ],
    "properties": {
        "episode_video_id": {"type": "string"},
        "summary": {"type": "string"},
        "candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "local_id", "source_atom_ids", "title", "source_claim", "type",
                    "themes", "subthemes", "takeaway", "reported_case",
                    "causal_certainty", "claim_risk", "numbers", "steps", "conditions",
                    "caveats", "evidence_segment_ids", "relations",
                ],
                "properties": {
                    "local_id": {"type": "string"},
                    "source_atom_ids": {"type": "array", "items": {"type": "string"}},
                    "title": {"type": "string"},
                    "source_claim": {"type": "string"},
                    "type": {"type": "string"},
                    "themes": {"type": "array", "items": {"type": "string"}},
                    "subthemes": {"type": "array", "items": {"type": "string"}},
                    "takeaway": {"type": "string"},
                    "reported_case": {"type": "boolean"},
                    "causal_certainty": {"type": "string"},
                    "claim_risk": {"type": "string"},
                    "numbers": {
                        "type": "array",
                        "items": {
                            "type": "object", "additionalProperties": False,
                            "required": ["raw", "role", "value_status"],
                            "properties": {
                                "raw": {"type": "string"},
                                "role": {"type": "string"},
                                "value_status": {"type": "string"},
                            },
                        },
                    },
                    "steps": {"type": "array", "items": {"type": "string"}},
                    "conditions": {"type": "array", "items": {"type": "string"}},
                    "caveats": {"type": "array", "items": {"type": "string"}},
                    "evidence_segment_ids": {"type": "array", "items": {"type": "string"}},
                    "relations": {
                        "type": "object", "additionalProperties": False,
                        "required": ["parent_local_id", "child_local_ids"],
                        "properties": {
                            "parent_local_id": {"type": ["string", "null"]},
                            "child_local_ids": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
            },
        },
        "numeric_dispositions": {"$ref": "#/$defs/dispositions"},
        "calibration_dispositions": {"$ref": "#/$defs/dispositions"},
    },
    "$defs": {
        "dispositions": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["inventory_id", "status", "candidate_local_ids", "reason"],
                "properties": {
                    "inventory_id": {"type": "string"},
                    "status": {"type": "string", "enum": ["captured", "merged", "excluded"]},
                    "candidate_local_ids": {"type": "array", "items": {"type": "string"}},
                    "reason": {"type": "string"},
                },
            },
        }
    },
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(value)
        Path(temporary).replace(path)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def _fold(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", value).lower()
        if not unicodedata.combining(char)
    )


def _tokens(value: str) -> set[str]:
    return {token for token in TOKEN_RE.findall(_fold(value)) if len(token) > 2 and token not in STOPWORDS}


def _numeric_literal(value: str) -> str:
    return re.sub(r"\s+", "", _fold(value))


def _literal_in_text(raw: str, text: str) -> bool:
    return bool(raw.strip()) and _numeric_literal(raw) in _numeric_literal(text)


def load_source_segments(request_dir: Path) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for path in sorted(request_dir.glob("*.json")):
        request = _read_json(path)
        for item in request.get("source_segments") or []:
            segment_id = str(item["segment_id"])
            normalized = {
                "segment_id": segment_id,
                "clean_index": int(item["clean_index"]),
                "text": str(item["text"]),
            }
            existing = by_id.get(segment_id)
            if existing is not None and existing != normalized:
                raise ValueError(f"conflicting source segment {segment_id}")
            by_id[segment_id] = normalized
    return sorted(by_id.values(), key=lambda item: item["clean_index"])


def build_numeric_inventory(segments: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    inventory = []
    for segment in segments:
        for position, match in enumerate(NUMBER_RE.finditer(str(segment["text"])), 1):
            raw = match.group(0).strip()
            inventory.append({
                "inventory_id": f"NUM-{int(segment['clean_index']):04d}-{position:02d}",
                "segment_id": segment["segment_id"],
                "clean_index": int(segment["clean_index"]),
                "raw": raw,
            })
    return inventory


def _risk_segment_ids(
    segments: list[dict[str, Any]],
    atoms: list[dict[str, Any]],
    calibrations: list[dict[str, Any]],
) -> set[str]:
    by_index = {int(item["clean_index"]): item for item in segments}
    selected_indexes: set[int] = set()
    for atom in atoms:
        selected_indexes.update(int(item["clean_index"]) for item in atom.get("evidence") or [])
    for item in build_numeric_inventory(segments):
        selected_indexes.add(int(item["clean_index"]))
    for calibration in calibrations:
        selected_indexes.update(int(item["clean_index"]) for item in calibration.get("source") or [])
    for segment in segments:
        if FRAMEWORK_RE.search(str(segment["text"])):
            selected_indexes.add(int(segment["clean_index"]))
    expanded = {
        neighbor
        for index in selected_indexes
        for neighbor in range(index - 2, index + 3)
        if neighbor in by_index
    }
    return {str(by_index[index]["segment_id"]) for index in expanded}


def _compact_atom(atom: dict[str, Any]) -> dict[str, Any]:
    return {
        "atom_id": atom["atom_id"],
        "source_claim": atom["source_claim"],
        "type": atom["type"],
        "themes": atom.get("themes") or [],
        "numbers": atom.get("numbers") or [],
        "steps": atom.get("steps") or [],
        "conditions": atom.get("conditions") or [],
        "caveats": atom.get("caveats") or [],
        "relation_hints": atom.get("relation_hints") or [],
        "evidence_segment_ids": [item["segment_id"] for item in atom.get("evidence") or []],
    }


def prepare_reducer_request(
    comparison_path: Path,
    request_dir: Path,
    output_path: Path,
    schema_path: Path,
) -> dict[str, Any]:
    comparison = _read_json(comparison_path)
    serialized_approved = json.dumps(comparison.get("approved_candidates") or [], ensure_ascii=False)
    approved_ids = set(re.findall(rf"{re.escape(comparison['episode_video_id'])}-G\d+", serialized_approved))
    segments = load_source_segments(request_dir)
    atoms = comparison.get("independent_atoms") or []
    calibrations = [
        {
            "inventory_id": f"CAL-{position:03d}",
            "calibration_id": item.get("calibration_id"),
            "source": item.get("source") or [],
        }
        for position, item in enumerate(comparison.get("calibration_targets") or [], 1)
    ]
    selected_ids = _risk_segment_ids(segments, atoms, calibrations)
    request = {
        "schema_version": "1.0.0",
        "kind": "gold_semantic_global_reducer_request",
        "reducer_version": REDUCER_VERSION,
        "episode_video_id": comparison["episode_video_id"],
        "source_segments": [item for item in segments if item["segment_id"] in selected_ids],
        "cached_independent_atoms": [_compact_atom(item) for item in atoms],
        "numeric_inventory": build_numeric_inventory(segments),
        "calibration_inventory": calibrations,
        "requirements": {
            "merge_duplicate_atoms": True,
            "reconstruct_episode_frameworks": True,
            "cross_shard_relations_must_be_symmetric": True,
            "every_inventory_item_requires_disposition": True,
            "preserve_transferable_interviewer_or_promo_rules": True,
            "procedures_require_all_boundary_setup_steps": True,
            "do_not_specialize_beyond_evidence": True,
        },
    }
    serialized = json.dumps(request, ensure_ascii=False, separators=(",", ":"))
    leaked = sorted(candidate_id for candidate_id in approved_ids if candidate_id in serialized)
    if leaked:
        raise ValueError(f"approved candidate IDs leaked into reducer request: {leaked}")
    request["semantic_sha256"] = semantic_hash(request)
    write_json(output_path, request)
    write_json(schema_path, REDUCER_SCHEMA)
    return request


def _reducer_prompt(request: dict[str, Any]) -> str:
    return """You are a stateless global semantic reducer. Do not call tools, inspect files, browse, or use information outside the JSON request.

The cached atoms were independently extracted from chronological shards and may be fragmented, duplicated, incomplete at boundaries, or over-specialized. Produce a compact episode-level candidate set without seeing approved gold.

Rules:
- Merge only atoms that express the same transferable proposition. Keep distinct mechanisms, outcomes, warnings, and procedures atomic.
- Reconstruct named or enumerated episode-level frameworks and symmetric parent/child relations when the source proves them.
- A candidate may have no source_atom_ids only when a numeric or calibration source segment proves a material proposition omitted by the shards.
- Use only evidence_segment_ids present in source_segments or cached atom evidence. Include every segment needed to prove the claim.
- Preserve every material number literally in numbers.raw. Every numeric_inventory and calibration_inventory item must receive exactly one disposition.
- Exclude incidental numbers or calibration targets honestly with a concrete reason. Captured/merged dispositions must reference output candidate local_ids.
- Procedures must include setup and boundary steps actually stated in evidence. Remove fabricated procedural specialization.
- Preserve transferable tests and decision rules even when spoken by an interviewer or inside promotion; keep honest attribution and caveats.
- Editorial fields must be concise Portuguese ASCII. Return only output-schema JSON.

REQUEST_JSON:
""" + json.dumps(request, ensure_ascii=False, separators=(",", ":"))


def _tool_events(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    forbidden = {"command_execution", "file_change", "mcp_tool_call", "web_search", "browser"}
    return [
        event for event in events
        if any(marker in json.dumps(event, ensure_ascii=False).lower() for marker in forbidden)
    ]


def invoke_reducer(
    input_path: Path,
    output_path: Path,
    log_path: Path,
    schema_path: Path,
    codex_exe: Path,
    model: str,
    effort: str,
    work_dir: Path,
) -> dict[str, Any]:
    request = _read_json(input_path)
    temporary_output = output_path.with_suffix(".tmp.json")
    command = [
        str(codex_exe), "exec", "--ephemeral", "--sandbox", "read-only",
        "--skip-git-repo-check", "--ignore-user-config", "--ignore-rules",
        "--json", "-C", str(work_dir), "-m", model,
        "-c", f"model_reasoning_effort='{effort}'", "--output-schema",
        str(schema_path), "-o", str(temporary_output), "-",
    ]
    started = time.perf_counter()
    completed = subprocess.run(
        command, input=_reducer_prompt(request), text=True, encoding="utf-8",
        errors="replace", capture_output=True, timeout=600, check=False,
    )
    duration = time.perf_counter() - started
    _atomic_text(log_path, completed.stdout + "\n--- STDERR ---\n" + completed.stderr)
    events = []
    for line in completed.stdout.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if completed.returncode != 0:
        raise RuntimeError(f"codex reducer failed ({completed.returncode}); see {log_path}")
    if _tool_events(events):
        raise RuntimeError(f"codex reducer used forbidden tools; see {log_path}")
    result = _read_json(temporary_output)
    if result.get("episode_video_id") != request.get("episode_video_id"):
        raise ValueError("reducer episode identity mismatch")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_output.replace(output_path)
    token_usage: dict[str, Any] = {}
    for event in events:
        usage = event.get("usage") or (event.get("data") or {}).get("usage")
        if isinstance(usage, dict):
            token_usage = usage
    report = {
        "mode": "global_reducer", "model": model, "reasoning_effort": effort,
        "duration_seconds": round(duration, 3), "tool_event_count": 0,
        "token_usage": token_usage,
        "input_semantic_sha256": request.get("semantic_sha256"),
        "output_semantic_sha256": semantic_hash(result),
    }
    write_json(output_path.parent / "invocation_report.json", report)
    return report


def _validate_dispositions(
    expected: list[dict[str, Any]],
    actual: list[dict[str, Any]],
    candidate_ids: set[str],
    label: str,
) -> list[str]:
    errors: list[str] = []
    expected_ids = [str(item["inventory_id"]) for item in expected]
    actual_ids = [str(item.get("inventory_id") or "") for item in actual]
    missing = sorted(set(expected_ids) - set(actual_ids))
    extra = sorted(set(actual_ids) - set(expected_ids))
    duplicates = sorted({value for value in actual_ids if actual_ids.count(value) > 1})
    if missing:
        errors.append(f"{label}: missing dispositions {missing}")
    if extra:
        errors.append(f"{label}: unknown dispositions {extra}")
    if duplicates:
        errors.append(f"{label}: duplicate dispositions {duplicates}")
    for item in actual:
        status = item.get("status")
        references = {str(value) for value in item.get("candidate_local_ids") or []}
        if references - candidate_ids:
            errors.append(f"{label}:{item.get('inventory_id')}: missing candidates {sorted(references - candidate_ids)}")
        if status in {"captured", "merged"} and not references:
            errors.append(f"{label}:{item.get('inventory_id')}: captured/merged without candidate")
        if status == "excluded" and len(str(item.get("reason") or "").strip()) < 8:
            errors.append(f"{label}:{item.get('inventory_id')}: exclusion reason too short")
    return errors


def validate_reducer_output(
    request_path: Path,
    response_path: Path,
    output_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    request = _read_json(request_path)
    response = _read_json(response_path)
    source = {str(item["segment_id"]): item for item in request["source_segments"]}
    atom_ids = {str(item["atom_id"]) for item in request["cached_independent_atoms"]}
    candidates = response.get("candidates") or []
    candidate_ids = [str(item.get("local_id") or "") for item in candidates]
    candidate_id_set = set(candidate_ids)
    hard_errors: list[str] = []
    warnings: list[str] = []
    if len(candidate_ids) != len(candidate_id_set) or "" in candidate_id_set:
        hard_errors.append("candidate local_id values must be non-empty and unique")

    adjacency: dict[str, set[str]] = {candidate_id: set() for candidate_id in candidate_id_set}
    hydrated = []
    for candidate in candidates:
        candidate_id = str(candidate.get("local_id") or "")
        evidence_ids = list(dict.fromkeys(str(value) for value in candidate.get("evidence_segment_ids") or []))
        missing_evidence = sorted(set(evidence_ids) - set(source))
        if not evidence_ids or missing_evidence:
            hard_errors.append(f"{candidate_id}: invalid evidence {missing_evidence}")
        unknown_atoms = sorted(set(candidate.get("source_atom_ids") or []) - atom_ids)
        if unknown_atoms:
            hard_errors.append(f"{candidate_id}: unknown source atoms {unknown_atoms}")
        evidence_text = " ".join(str(source[value]["text"]) for value in evidence_ids if value in source)
        folded_evidence = _fold(evidence_text)
        for number in candidate.get("numbers") or []:
            raw = str(number.get("raw") or "").strip()
            if not raw or not _literal_in_text(raw, evidence_text):
                hard_errors.append(f"{candidate_id}: number raw not literal in evidence: {raw}")
        claim_tokens = _tokens(str(candidate.get("source_claim") or ""))
        evidence_tokens = _tokens(evidence_text)
        if claim_tokens and len(claim_tokens & evidence_tokens) < min(2, len(claim_tokens)):
            warnings.append(f"{candidate_id}: weak lexical claim support")
        steps = candidate.get("steps") or []
        if steps and not any(_tokens(str(step)) & evidence_tokens for step in steps):
            hard_errors.append(f"{candidate_id}: procedure steps lack evidence support")
        relations = candidate.get("relations") or {}
        parent = relations.get("parent_local_id")
        children = {str(value) for value in relations.get("child_local_ids") or []}
        if parent:
            parent = str(parent)
            if parent not in candidate_id_set:
                hard_errors.append(f"{candidate_id}: missing parent {parent}")
            else:
                adjacency[parent].add(candidate_id)
        for child in children:
            if child not in candidate_id_set:
                hard_errors.append(f"{candidate_id}: missing child {child}")
            else:
                adjacency[candidate_id].add(child)
        hydrated.append({
            **candidate,
            "evidence": [
                {
                    "segment_id": segment_id,
                    "clean_index": source[segment_id]["clean_index"],
                    "quote_verbatim": source[segment_id]["text"],
                }
                for segment_id in evidence_ids if segment_id in source
            ],
        })

    by_id = {str(item.get("local_id")): item for item in candidates}
    for parent, children in adjacency.items():
        for child in children:
            parent_children = set((by_id[parent].get("relations") or {}).get("child_local_ids") or [])
            child_parent = (by_id[child].get("relations") or {}).get("parent_local_id")
            if child not in parent_children or child_parent != parent:
                hard_errors.append(f"asymmetric relation: {parent}->{child}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def has_cycle(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(has_cycle(child) for child in adjacency.get(node, set())):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    if any(has_cycle(node) for node in sorted(candidate_id_set)):
        hard_errors.append("relation graph contains a cycle")
    hard_errors.extend(_validate_dispositions(
        request["numeric_inventory"], response.get("numeric_dispositions") or [],
        candidate_id_set, "numeric_inventory",
    ))
    hard_errors.extend(_validate_dispositions(
        request["calibration_inventory"], response.get("calibration_dispositions") or [],
        candidate_id_set, "calibration_inventory",
    ))

    result = {
        "episode_video_id": response.get("episode_video_id"),
        "reducer_version": REDUCER_VERSION,
        "candidates": hydrated,
        "numeric_dispositions": response.get("numeric_dispositions") or [],
        "calibration_dispositions": response.get("calibration_dispositions") or [],
        "summary": response.get("summary"),
    }
    report = {
        "status": "pass" if not hard_errors else "fail",
        "hard_errors": sorted(set(hard_errors)),
        "warnings": sorted(set(warnings)),
        "candidate_count": len(hydrated),
        "numeric_inventory_count": len(request["numeric_inventory"]),
        "calibration_inventory_count": len(request["calibration_inventory"]),
        "relation_edge_count": sum(len(value) for value in adjacency.values()),
        "semantic_sha256": semantic_hash(result),
    }
    write_json(output_path, result)
    write_json(report_path, report)
    return report


def reconcile_numeric_evidence(
    request_path: Path,
    response_path: Path,
    output_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    """Repair only literal numeric evidence omissions in a model response.

    Existing output remains untouched except that a source-backed number gains
    its proving segment, while a number with no literal source is removed.
    """
    request = _read_json(request_path)
    response = _read_json(response_path)
    source = {str(item["segment_id"]): item for item in request["source_segments"]}
    additions: list[dict[str, str]] = []
    removals: list[dict[str, str]] = []
    for candidate in response.get("candidates") or []:
        candidate_id = str(candidate.get("local_id") or "")
        evidence_ids = list(dict.fromkeys(str(value) for value in candidate.get("evidence_segment_ids") or []))
        evidence_text = " ".join(str(source[value]["text"]) for value in evidence_ids if value in source)
        evidence_indexes = [int(source[value]["clean_index"]) for value in evidence_ids if value in source]
        evidence_center = sum(evidence_indexes) / max(1, len(evidence_indexes))
        retained = []
        for number in candidate.get("numbers") or []:
            raw = str(number.get("raw") or "").strip()
            if raw and _literal_in_text(raw, evidence_text):
                retained.append(number)
                continue
            matches = [
                segment_id for segment_id, segment in source.items()
                if _literal_in_text(raw, str(segment["text"]))
            ]
            if matches:
                segment_id = min(
                    matches,
                    key=lambda value: (
                        abs(int(source[value]["clean_index"]) - evidence_center),
                        int(source[value]["clean_index"]),
                    ),
                )
                if segment_id not in evidence_ids:
                    evidence_ids.append(segment_id)
                    additions.append({"candidate_local_id": candidate_id, "raw": raw, "segment_id": segment_id})
                retained.append(number)
                evidence_text = " ".join(str(source[value]["text"]) for value in evidence_ids)
            else:
                removals.append({"candidate_local_id": candidate_id, "raw": raw})
        candidate["numbers"] = retained
        candidate["evidence_segment_ids"] = evidence_ids
    write_json(output_path, response)
    report = {
        "status": "pass",
        "added_evidence_count": len(additions),
        "removed_number_count": len(removals),
        "additions": additions,
        "removals": removals,
        "semantic_sha256": semantic_hash(response),
    }
    write_json(report_path, report)
    return report


def _evidence_indexes_from_candidate(candidate: dict[str, Any]) -> set[int]:
    return {
        int(value)
        for field in ("minimal_clean_indexes", "support_clean_indexes")
        for value in candidate.get(field) or []
    }


def _candidate_match_score(approved: dict[str, Any], reduced: dict[str, Any]) -> float:
    approved_indexes = _evidence_indexes_from_candidate(approved)
    reduced_indexes = {int(item["clean_index"]) for item in reduced.get("evidence") or []}
    evidence_score = len(approved_indexes & reduced_indexes) / max(1, len(approved_indexes | reduced_indexes))
    approved_text = " ".join([
        str(approved.get("title") or ""), str(approved.get("source_claim") or ""),
        str(approved.get("takeaway_applicavel") or ""),
    ])
    reduced_text = " ".join([
        str(reduced.get("title") or ""), str(reduced.get("source_claim") or ""),
        str(reduced.get("takeaway") or ""),
    ])
    left, right = _tokens(approved_text), _tokens(reduced_text)
    lexical_score = len(left & right) / max(1, len(left | right))
    return 0.75 * evidence_score + 0.25 * lexical_score


def _compact_approved_entry(entry: dict[str, Any]) -> dict[str, Any]:
    candidate = entry["candidate"]
    return {
        "candidate": {
            key: candidate.get(key)
            for key in (
                "candidate_id", "title", "source_claim", "reported_case",
                "causal_certainty", "claim_risk", "numbers", "steps",
                "conditions", "caveats", "relations",
            )
        },
        "evidence": entry.get("evidence") or [],
    }


def _compact_reduced_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        key: candidate.get(key)
        for key in (
            "local_id", "title", "source_claim", "type", "themes",
            "reported_case", "causal_certainty", "claim_risk", "numbers",
            "steps", "conditions", "caveats", "relations", "evidence",
        )
    }


def build_compact_judge_packet(
    comparison_path: Path,
    reduced_path: Path,
    validation_report_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    comparison = _read_json(comparison_path)
    reduced = _read_json(reduced_path)
    validation = _read_json(validation_report_path)
    if validation.get("status") != "pass":
        raise ValueError("cannot build judge packet from invalid reducer output")
    candidates = reduced["candidates"]
    matches: dict[str, list[dict[str, Any]]] = {}
    selected_ids: set[str] = set()
    for entry in comparison["approved_candidates"]:
        approved = entry["candidate"]
        ranked = sorted(
            ((item["local_id"], _candidate_match_score(approved, item)) for item in candidates),
            key=lambda item: (-item[1], item[0]),
        )
        selected = [
            {"local_id": candidate_id, "score": round(score, 4)}
            for candidate_id, score in ranked[:4] if score > 0
        ]
        matches[approved["candidate_id"]] = selected
        selected_ids.update(item["local_id"] for item in selected)
    unmatched = sorted(set(item["local_id"] for item in candidates) - selected_ids)
    packet = {
        "episode_video_id": comparison["episode_video_id"],
        "adapter": {
            "model_outputs_are_independent": True,
            "approved_candidates_hidden_during_extraction_and_reduction": True,
            "cached_shard_calls_reused": True,
            "global_reducer_version": REDUCER_VERSION,
        },
        "approved_candidates": [_compact_approved_entry(item) for item in comparison["approved_candidates"]],
        "independent_atoms": [_compact_reduced_candidate(item) for item in candidates],
        "deterministic_matches": matches,
        "unmatched_independent_atom_ids": unmatched,
        "calibration_targets": comparison["calibration_targets"],
        "calibration_dispositions": reduced["calibration_dispositions"],
        "numeric_inventory_summary": {
            "total_count": len(reduced["numeric_dispositions"]),
            "status_counts": {
                status: sum(
                    item.get("status") == status
                    for item in reduced["numeric_dispositions"]
                )
                for status in ("captured", "merged", "excluded")
            },
        },
        "deterministic_validation": validation,
    }
    packet["semantic_sha256"] = semantic_hash(packet)
    write_json(output_path, packet)
    return packet


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--comparison", type=Path, required=True)
    prepare.add_argument("--request-dir", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--schema-output", type=Path, required=True)
    invoke = subparsers.add_parser("invoke")
    invoke.add_argument("--input", type=Path, required=True)
    invoke.add_argument("--output", type=Path, required=True)
    invoke.add_argument("--log", type=Path, required=True)
    invoke.add_argument("--schema", type=Path, required=True)
    invoke.add_argument("--codex-exe", type=Path, required=True)
    invoke.add_argument("--model", default="gpt-5.6-terra")
    invoke.add_argument("--effort", default="high")
    invoke.add_argument("--work-dir", type=Path, required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--request", type=Path, required=True)
    validate.add_argument("--response", type=Path, required=True)
    validate.add_argument("--output", type=Path, required=True)
    validate.add_argument("--report", type=Path, required=True)
    reconcile = subparsers.add_parser("reconcile-numbers")
    reconcile.add_argument("--request", type=Path, required=True)
    reconcile.add_argument("--response", type=Path, required=True)
    reconcile.add_argument("--output", type=Path, required=True)
    reconcile.add_argument("--report", type=Path, required=True)
    judge = subparsers.add_parser("build-judge")
    judge.add_argument("--comparison", type=Path, required=True)
    judge.add_argument("--reduced", type=Path, required=True)
    judge.add_argument("--validation-report", type=Path, required=True)
    judge.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "prepare":
        result = prepare_reducer_request(args.comparison, args.request_dir, args.output, args.schema_output)
    elif args.command == "invoke":
        result = invoke_reducer(
            args.input, args.output, args.log, args.schema, args.codex_exe,
            args.model, args.effort, args.work_dir,
        )
    elif args.command == "validate":
        result = validate_reducer_output(args.request, args.response, args.output, args.report)
    elif args.command == "reconcile-numbers":
        result = reconcile_numeric_evidence(args.request, args.response, args.output, args.report)
    elif args.command == "build-judge":
        result = build_compact_judge_packet(args.comparison, args.reduced, args.validation_report, args.output)
    else:
        return 2
    if args.command == "prepare":
        rendered = {
            "episode_video_id": result["episode_video_id"],
            "source_segment_count": len(result["source_segments"]),
            "cached_atom_count": len(result["cached_independent_atoms"]),
            "numeric_inventory_count": len(result["numeric_inventory"]),
            "calibration_inventory_count": len(result["calibration_inventory"]),
            "semantic_sha256": result["semantic_sha256"],
        }
    elif args.command == "build-judge":
        rendered = {
            "episode_video_id": result["episode_video_id"],
            "approved_candidate_count": len(result["approved_candidates"]),
            "independent_candidate_count": len(result["independent_atoms"]),
            "semantic_sha256": result["semantic_sha256"],
        }
    else:
        rendered = result
    print(json.dumps(rendered, ensure_ascii=False))
    return 0 if result.get("status") != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
