#!/usr/bin/env python3
"""Archived read-only research prototype; never a production gold route.

The module deliberately separates two concerns:

* mechanics: sharding, caching, proof validation, reduction, materialization,
  and risk-targeted audit planning;
* semantics: an adapter that interprets source text and emits semantic atoms.

The benchmark adapter replays an already approved gold dossier.  It validates
the mechanics without pretending to be an independent extraction benchmark.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable


SCHEMA_VERSION = "0.1.0"
COMPILER_VERSION = "gold-semantic-compiler-v1"
TRANSCRIPT_COLUMNS = [
    "clean_index", "start_seconds", "duration_seconds", "text",
    "ledger_disposition", "ledger_candidate_ids", "ledger_reason_code",
    "ledger_reason_reference",
]


def semantic_hash(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        Path(temporary_name).replace(path)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            for value in values:
                handle.write(json.dumps(value, ensure_ascii=False, separators=(",", ":")))
                handle.write("\n")
        Path(temporary_name).replace(path)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _row_to_object(columns: list[str], row: list[Any]) -> dict[str, Any]:
    return {column: row[index] if index < len(row) else None for index, column in enumerate(columns)}


def load_dossier(path: Path) -> dict[str, Any]:
    records = read_jsonl(path)
    if not records or records[0].get("record_type") != "header":
        raise ValueError("dossier must start with a header")
    if records[-1].get("record_type") != "footer":
        raise ValueError("dossier must end with a footer")
    header = records[0]
    expected_hash = records[-1].get("content_semantic_sha256")
    actual_hash = semantic_hash(records[:-1])
    if expected_hash and expected_hash != actual_hash:
        raise ValueError("dossier semantic hash mismatch")

    video_id = str(header["episode_video_id"])
    transcript_columns = header.get("transcript_columns") or TRANSCRIPT_COLUMNS
    transcript: list[dict[str, Any]] = []
    for record in records:
        if record.get("record_type") != "transcript_block":
            continue
        for row in record.get("value", []):
            item = _row_to_object(transcript_columns, row)
            clean_index = int(item["clean_index"])
            item["segment_id"] = f"{video_id}-transcript-{clean_index + 1:04d}"
            transcript.append(item)
    transcript.sort(key=lambda item: int(item["clean_index"]))

    candidate_columns = list(header.get("candidate_columns") or [])
    candidates = [
        _row_to_object(candidate_columns, record["value"])
        for record in records
        if record.get("record_type") == "candidate"
    ]
    calibrations = [
        record["value"]
        for record in records
        if record.get("record_type") == "calibration"
    ]
    ledger_groups = [
        record["value"]
        for record in records
        if record.get("record_type") == "ledger_group"
    ]
    if len(transcript) != int(header.get("segment_count", len(transcript))):
        raise ValueError("dossier transcript count mismatch")
    if len(candidates) != int(header.get("candidate_count", len(candidates))):
        raise ValueError("dossier candidate count mismatch")
    return {
        "path": path,
        "physical_bytes": path.stat().st_size,
        "semantic_sha256": actual_hash,
        "header": header,
        "video_id": video_id,
        "transcript": transcript,
        "candidates": candidates,
        "calibrations": calibrations,
        "ledger_groups": ledger_groups,
    }


@dataclass(frozen=True)
class Shard:
    shard_id: str
    core_start: int
    core_end: int
    context_start: int
    context_end: int
    core_segment_ids: tuple[str, ...]
    context_segment_ids: tuple[str, ...]
    input_semantic_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "shard_id": self.shard_id,
            "core_clean_index_range": [self.core_start, self.core_end],
            "context_clean_index_range": [self.context_start, self.context_end],
            "core_segment_ids": list(self.core_segment_ids),
            "context_segment_ids": list(self.context_segment_ids),
            "input_semantic_sha256": self.input_semantic_sha256,
        }


def plan_shards(
    video_id: str,
    transcript: list[dict[str, Any]],
    *,
    target_seconds: float = 480.0,
    max_segments: int = 140,
    overlap_segments: int = 3,
) -> list[Shard]:
    if not transcript:
        return []
    if target_seconds <= 0 or max_segments <= 0 or overlap_segments < 0:
        raise ValueError("invalid shard planning parameters")
    groups: list[tuple[int, int]] = []
    start = 0
    for index, segment in enumerate(transcript):
        elapsed = float(segment["start_seconds"]) - float(transcript[start]["start_seconds"])
        count = index - start + 1
        if index > start and (elapsed >= target_seconds or count > max_segments):
            groups.append((start, index - 1))
            start = index
    groups.append((start, len(transcript) - 1))

    shards: list[Shard] = []
    for number, (start, end) in enumerate(groups, 1):
        context_start = max(0, start - overlap_segments)
        context_end = min(len(transcript) - 1, end + overlap_segments)
        context = transcript[context_start : context_end + 1]
        source = [
            {
                "segment_id": item["segment_id"],
                "clean_index": item["clean_index"],
                "start_seconds": item["start_seconds"],
                "duration_seconds": item["duration_seconds"],
                "text": item["text"],
                "is_core": start <= int(item["clean_index"]) <= end,
            }
            for item in context
        ]
        shards.append(Shard(
            shard_id=f"{video_id}-semantic-shard-{number:03d}",
            core_start=int(transcript[start]["clean_index"]),
            core_end=int(transcript[end]["clean_index"]),
            context_start=int(transcript[context_start]["clean_index"]),
            context_end=int(transcript[context_end]["clean_index"]),
            core_segment_ids=tuple(item["segment_id"] for item in transcript[start : end + 1]),
            context_segment_ids=tuple(item["segment_id"] for item in context),
            input_semantic_sha256=semantic_hash(source),
        ))
    return shards


def validate_shard_plan(transcript: list[dict[str, Any]], shards: list[Shard]) -> list[str]:
    errors: list[str] = []
    expected = [str(item["segment_id"]) for item in transcript]
    owned = [segment_id for shard in shards for segment_id in shard.core_segment_ids]
    if owned != expected:
        errors.append("shard cores do not preserve exact chronological source ownership")
    if len(owned) != len(set(owned)):
        errors.append("one or more source segments have multiple shard owners")
    for shard in shards:
        if not set(shard.core_segment_ids) <= set(shard.context_segment_ids):
            errors.append(f"{shard.shard_id}: core escapes context")
    return errors


def build_shard_requests(
    video_id: str,
    transcript: list[dict[str, Any]],
    shards: list[Shard],
    *,
    routed_inventory: dict[str, dict[str, list[dict[str, Any]]]] | None = None,
) -> list[dict[str, Any]]:
    """Return oracle-free requests for a future independent semantic adapter."""
    source_by_id = {str(item["segment_id"]): item for item in transcript}
    requests = []
    for shard in shards:
        segments = []
        core_ids = set(shard.core_segment_ids)
        for segment_id in shard.context_segment_ids:
            source = source_by_id[segment_id]
            segments.append({
                "segment_id": segment_id,
                "clean_index": int(source["clean_index"]),
                "start_seconds": float(source["start_seconds"]),
                "duration_seconds": float(source.get("duration_seconds", 0.0)),
                "text": source["text"],
                "is_core": segment_id in core_ids,
            })
        request = {
            "schema_version": SCHEMA_VERSION,
            "kind": "gold_semantic_shard_request",
            "episode_video_id": video_id,
            "shard": shard.as_dict(),
            "source_segments": segments,
            "risk_inventory": (routed_inventory or {}).get(
                shard.shard_id,
                {"numeric": [], "calibration": [], "boundary": []},
            ),
            "instructions": {
                "emit_only_core_claims": True,
                "preserve_quote_verbatim": True,
                "disposition_every_risk_inventory_item": True,
                "output": "gold_semantic_shard_result",
                "required_atom_fields": [
                    "atom_id", "candidate_id", "candidate", "evidence", "provenance",
                ],
            },
        }
        request["semantic_sha256"] = semantic_hash(request)
        requests.append(request)
    return requests


def _evidence_indexes(candidate: dict[str, Any]) -> list[int]:
    return sorted({
        int(value)
        for field in ("minimal_clean_indexes", "support_clean_indexes")
        for value in (candidate.get(field) or [])
    })


def _candidate_atom(
    candidate: dict[str, Any],
    transcript_by_index: dict[int, dict[str, Any]],
    shard_id: str,
) -> dict[str, Any]:
    evidence_indexes = _evidence_indexes(candidate)
    evidence = [
        {
            "segment_id": transcript_by_index[index]["segment_id"],
            "clean_index": index,
            "quote_verbatim": transcript_by_index[index]["text"],
            "layer": "minimal" if index in (candidate.get("minimal_clean_indexes") or []) else "support",
        }
        for index in evidence_indexes
    ]
    atom = {
        "atom_id": candidate["candidate_id"],
        "candidate_id": candidate["candidate_id"],
        "owner_shard_id": shard_id,
        "provenance": {
            "adapter": "approved_gold_replay",
            "semantic_independence": False,
            "source_candidate_id": candidate["candidate_id"],
        },
        "candidate": candidate,
        "evidence": evidence,
    }
    atom["semantic_sha256"] = semantic_hash({key: value for key, value in atom.items() if key != "semantic_sha256"})
    return atom


def replay_adapter(
    shard: Shard,
    transcript: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    transcript_by_index = {int(item["clean_index"]): item for item in transcript}
    atoms = []
    for candidate in candidates:
        indexes = _evidence_indexes(candidate)
        owner_index = min(indexes) if indexes else -1
        if shard.core_start <= owner_index <= shard.core_end:
            atoms.append(_candidate_atom(candidate, transcript_by_index, shard.shard_id))
    result = {
        "schema_version": SCHEMA_VERSION,
        "kind": "gold_semantic_shard_result",
        "shard": shard.as_dict(),
        "adapter": "approved_gold_replay",
        "semantic_independence": False,
        "atoms": atoms,
    }
    result["semantic_sha256"] = semantic_hash(result)
    return result


def shard_cache_key(
    shard: Shard,
    *,
    adapter: str,
    prompt_version: str,
    model_version: str,
) -> str:
    return semantic_hash({
        "compiler_version": COMPILER_VERSION,
        "source": shard.input_semantic_sha256,
        "adapter": adapter,
        "prompt_version": prompt_version,
        "model_version": model_version,
    })


def compile_shards_cached(
    shards: list[Shard],
    *,
    cache_dir: Path,
    adapter_name: str,
    prompt_version: str,
    model_version: str,
    workers: int,
    compile_one: Callable[[Shard], dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    cache_dir.mkdir(parents=True, exist_ok=True)

    def resolve(shard: Shard) -> tuple[int, dict[str, Any]]:
        key = shard_cache_key(
            shard,
            adapter=adapter_name,
            prompt_version=prompt_version,
            model_version=model_version,
        )
        path = cache_dir / f"{key}.json"
        if path.exists():
            cached = json.loads(path.read_text(encoding="utf-8"))
            if cached.get("cache_key") == key and cached.get("result", {}).get("shard", {}).get("input_semantic_sha256") == shard.input_semantic_sha256:
                return 1, cached["result"]
        result = compile_one(shard)
        write_json(path, {"cache_key": key, "result": result})
        return 0, result

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        resolved = list(pool.map(resolve, shards))
    return [item[1] for item in resolved], {
        "hits": sum(item[0] for item in resolved),
        "misses": sum(1 - item[0] for item in resolved),
    }


def validate_and_reduce(
    transcript: list[dict[str, Any]],
    shard_results: list[dict[str, Any]],
) -> dict[str, Any]:
    source_by_id = {str(item["segment_id"]): item for item in transcript}
    atoms: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_ids: dict[str, str] = {}
    for result in shard_results:
        for atom in result.get("atoms", []):
            atom_id = str(atom.get("atom_id"))
            if atom_id in seen_ids:
                errors.append(f"duplicate atom_id: {atom_id}")
                continue
            seen_ids[atom_id] = str(atom.get("semantic_sha256"))
            evidence = atom.get("evidence") or []
            if not evidence:
                errors.append(f"{atom_id}: missing proof evidence")
            for citation in evidence:
                source = source_by_id.get(str(citation.get("segment_id")))
                if source is None:
                    errors.append(f"{atom_id}: missing source segment {citation.get('segment_id')}")
                elif citation.get("quote_verbatim") != source.get("text"):
                    errors.append(f"{atom_id}: non-verbatim evidence {citation.get('segment_id')}")
            atoms.append(atom)

    candidate_ids = {str(atom["candidate_id"]) for atom in atoms}
    relation_edges: list[dict[str, str]] = []
    adjacency: dict[str, set[str]] = {candidate_id: set() for candidate_id in candidate_ids}
    for atom in atoms:
        candidate = atom["candidate"]
        candidate_id = str(candidate["candidate_id"])
        relations = candidate.get("relations") or {}
        parent = relations.get("parent_candidate_id")
        children = [str(value) for value in relations.get("child_candidate_ids") or []]
        if parent:
            parent = str(parent)
            if parent not in candidate_ids:
                errors.append(f"{candidate_id}: missing parent {parent}")
            else:
                relation_edges.append({"parent": parent, "child": candidate_id})
                adjacency[parent].add(candidate_id)
        for child in children:
            if child not in candidate_ids:
                errors.append(f"{candidate_id}: missing child {child}")
            else:
                relation_edges.append({"parent": candidate_id, "child": child})
                adjacency[candidate_id].add(child)
    unique_edges = {(edge["parent"], edge["child"]) for edge in relation_edges}
    for parent, child in sorted(unique_edges):
        child_atom = next(atom for atom in atoms if atom["candidate_id"] == child)
        actual_parent = (child_atom["candidate"].get("relations") or {}).get("parent_candidate_id")
        parent_atom = next(atom for atom in atoms if atom["candidate_id"] == parent)
        actual_children = set((parent_atom["candidate"].get("relations") or {}).get("child_candidate_ids") or [])
        if actual_parent != parent or child not in actual_children:
            errors.append(f"asymmetric relation: {parent}->{child}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(child) for child in adjacency.get(node, set())):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    if any(visit(node) for node in sorted(candidate_ids)):
        errors.append("relation graph contains a cycle")

    atoms.sort(key=lambda atom: (
        min((item["clean_index"] for item in atom["evidence"]), default=10**12),
        atom["candidate_id"],
    ))
    proof_edges = [
        {
            "candidate_id": atom["candidate_id"],
            "segment_id": citation["segment_id"],
            "clean_index": citation["clean_index"],
            "layer": citation["layer"],
        }
        for atom in atoms
        for citation in atom["evidence"]
    ]
    return {
        "atoms": atoms,
        "candidate_projection": [atom["candidate"] for atom in atoms],
        "proof_graph": {
            "candidate_nodes": sorted(candidate_ids),
            "evidence_edges": proof_edges,
            "relation_edges": [
                {"parent": parent, "child": child}
                for parent, child in sorted(unique_edges)
            ],
        },
        "errors": sorted(set(errors)),
    }


def validate_calibration_bindings(
    calibrations: list[dict[str, Any]],
    transcript: list[dict[str, Any]],
    candidate_ids: set[str],
) -> list[str]:
    errors: list[str] = []
    source_indexes = {int(item["clean_index"]) for item in transcript}
    seen_targets: dict[tuple[int, ...], str] = {}
    for position, item in enumerate(calibrations, 1):
        calibration_id = str(item.get("calibration_id") or f"calibration-{position}")
        indexes = tuple(sorted(int(value) for value in item.get("clean_indexes") or []))
        if not indexes:
            errors.append(f"{calibration_id}: missing source target")
        elif any(index not in source_indexes for index in indexes):
            errors.append(f"{calibration_id}: target references missing source index")
        if indexes in seen_targets:
            errors.append(
                f"{calibration_id}: duplicates target of {seen_targets[indexes]}"
            )
        elif indexes:
            seen_targets[indexes] = calibration_id
        for candidate_id in item.get("semantic_candidate_ids") or []:
            if str(candidate_id) not in candidate_ids:
                errors.append(
                    f"{calibration_id}: missing semantic candidate {candidate_id}"
                )
    return errors


def validate_ledger_groups(
    ledger_groups: list[list[Any]],
    transcript: list[dict[str, Any]],
    reduced: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    source_indexes = {int(item["clean_index"]) for item in transcript}
    candidate_ids = {
        str(atom["candidate_id"])
        for atom in reduced.get("atoms", [])
    }
    evidence_by_candidate = {
        str(atom["candidate_id"]): {
            int(citation["clean_index"])
            for citation in atom.get("evidence", [])
        }
        for atom in reduced.get("atoms", [])
    }
    for position, row in enumerate(ledger_groups, 1):
        if len(row) < 5:
            errors.append(f"ledger group {position}: malformed row")
            continue
        disposition, row_candidate_ids, reason_code, _reason_reference, indexes = row[:5]
        clean_indexes = {int(value) for value in indexes or []}
        if any(index not in source_indexes for index in clean_indexes):
            errors.append(f"ledger group {position}: missing source index")
        ids = {str(value) for value in row_candidate_ids or []}
        if disposition in {"captured", "merged"}:
            if not ids:
                errors.append(f"ledger group {position}: {disposition} without candidate")
            for candidate_id in ids:
                if candidate_id not in candidate_ids:
                    errors.append(
                        f"ledger group {position}: missing candidate {candidate_id}"
                    )
                elif not clean_indexes <= evidence_by_candidate[candidate_id]:
                    errors.append(
                        f"ledger group {position}: {candidate_id} does not prove every captured source index"
                    )
        elif disposition == "excluded" and not reason_code:
            errors.append(f"ledger group {position}: exclusion without reason_code")
        elif disposition not in {"captured", "merged", "excluded"}:
            errors.append(f"ledger group {position}: invalid disposition {disposition}")
    return errors


def build_audit_plan(
    reduced: dict[str, Any],
    calibrations: list[dict[str, Any]],
    audit_warnings: list[dict[str, Any]],
    *,
    low_risk_sample_ratio: float = 0.10,
) -> dict[str, Any]:
    calibration_ids = {
        str(candidate_id)
        for item in calibrations
        for candidate_id in item.get("semantic_candidate_ids") or []
    }
    warning_ids = {
        str(candidate_id)
        for group in audit_warnings
        for item in group.get("items", [])
        for candidate_id in (
            item.get("candidate_ids")
            or ([item.get("candidate_id")] if item.get("candidate_id") else [])
        )
    }
    high_risk: list[dict[str, Any]] = []
    low_risk: list[dict[str, Any]] = []
    for atom in reduced["atoms"]:
        candidate = atom["candidate"]
        candidate_id = str(candidate["candidate_id"])
        reasons = []
        if candidate.get("numbers"):
            reasons.append("numbers")
        if candidate.get("type") in {"playbook_step", "framework", "script"} or candidate.get("steps"):
            reasons.append("procedure")
        if candidate.get("reported_case"):
            reasons.append("reported_case")
        if candidate.get("caveats"):
            reasons.append("caveat")
        relations = candidate.get("relations") or {}
        if relations.get("parent_candidate_id") or relations.get("child_candidate_ids"):
            reasons.append("relation")
        if candidate_id in calibration_ids:
            reasons.append("calibration")
        if candidate_id in warning_ids:
            reasons.append("audit_warning")
        entry = {
            "candidate_id": candidate_id,
            "risk_reasons": sorted(set(reasons)),
            "source_clean_indexes": [item["clean_index"] for item in atom["evidence"]],
        }
        (high_risk if reasons else low_risk).append(entry)
    sample_count = max(1, round(len(low_risk) * low_risk_sample_ratio)) if low_risk else 0
    sampled = sorted(low_risk, key=lambda item: semantic_hash(item["candidate_id"]))[:sample_count]
    selected = high_risk + sampled
    selected_indexes = sorted({
        index
        for item in selected
        for index in item["source_clean_indexes"]
    })
    plan = {
        "schema_version": SCHEMA_VERSION,
        "kind": "gold_risk_targeted_audit_plan",
        "high_risk_candidates": high_risk,
        "sampled_low_risk_candidates": sampled,
        "selected_candidate_count": len(selected),
        "selected_source_clean_indexes": selected_indexes,
        "limitations": [
            "This plan is a navigation surface, not proof that a sampled audit equals a full audit.",
            "Independent semantic validation remains required before production adoption.",
        ],
    }
    plan["semantic_sha256"] = semantic_hash(plan)
    return plan


def _projection_by_id(values: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item["candidate_id"]): item for item in values}


def benchmark_replay(
    dossier_path: Path,
    output_dir: Path,
    *,
    workers: int = 8,
    target_seconds: float = 480.0,
    max_segments: int = 140,
    overlap_segments: int = 3,
) -> dict[str, Any]:
    started = time.perf_counter()
    dossier = load_dossier(dossier_path)
    shards = plan_shards(
        dossier["video_id"], dossier["transcript"],
        target_seconds=target_seconds,
        max_segments=max_segments,
        overlap_segments=overlap_segments,
    )
    shard_errors = validate_shard_plan(dossier["transcript"], shards)
    shard_requests = build_shard_requests(
        dossier["video_id"], dossier["transcript"], shards
    )
    cache_dir = output_dir / "cache"

    cold_started = time.perf_counter()
    first_results, first_cache = compile_shards_cached(
        shards,
        cache_dir=cache_dir,
        adapter_name="approved_gold_replay",
        prompt_version="replay-v1",
        model_version="none",
        workers=workers,
        compile_one=lambda shard: replay_adapter(shard, dossier["transcript"], dossier["candidates"]),
    )
    cold_ms = (time.perf_counter() - cold_started) * 1000

    cache_mtimes = {path.name: path.stat().st_mtime_ns for path in cache_dir.glob("*.json")}
    warm_started = time.perf_counter()
    second_results, second_cache = compile_shards_cached(
        shards,
        cache_dir=cache_dir,
        adapter_name="approved_gold_replay",
        prompt_version="replay-v1",
        model_version="none",
        workers=workers,
        compile_one=lambda shard: replay_adapter(shard, dossier["transcript"], dossier["candidates"]),
    )
    warm_ms = (time.perf_counter() - warm_started) * 1000
    cache_unchanged = cache_mtimes == {
        path.name: path.stat().st_mtime_ns for path in cache_dir.glob("*.json")
    }
    if semantic_hash(first_results) != semantic_hash(second_results):
        shard_errors.append("warm cache results differ from cold results")

    reduced = validate_and_reduce(dossier["transcript"], first_results)
    oracle = _projection_by_id(dossier["candidates"])
    actual = _projection_by_id(reduced["candidate_projection"])
    candidate_ids_equal = set(actual) == set(oracle)
    exact_candidates = sum(actual.get(candidate_id) == value for candidate_id, value in oracle.items())
    audit_plan = build_audit_plan(
        reduced,
        dossier["calibrations"],
        dossier["header"].get("audit_warnings", []),
    )

    audit_bundle = {
        "episode_video_id": dossier["video_id"],
        "candidate_projection": [
            actual[candidate_id]
            for candidate_id in sorted({item["candidate_id"] for item in audit_plan["high_risk_candidates"] + audit_plan["sampled_low_risk_candidates"]})
        ],
        "source_segments": [
            dossier["transcript"][index]
            for index in audit_plan["selected_source_clean_indexes"]
        ],
        "calibrations": dossier["calibrations"],
    }
    targeted_bytes = len(json.dumps(audit_bundle, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    calibration_errors = validate_calibration_bindings(
        dossier["calibrations"], dossier["transcript"], set(actual)
    )
    ledger_errors = validate_ledger_groups(
        dossier["ledger_groups"], dossier["transcript"], reduced
    )
    all_errors = sorted(set(
        shard_errors + reduced["errors"] + calibration_errors + ledger_errors
    ))
    report = {
        "schema_version": SCHEMA_VERSION,
        "kind": "gold_semantic_compiler_benchmark",
        "episode_video_id": dossier["video_id"],
        "mode": "approved_gold_replay",
        "semantic_independence": False,
        "quality_claim": "mechanics_validated_semantics_pending",
        "baseline": {
            "segment_count": len(dossier["transcript"]),
            "candidate_count": len(dossier["candidates"]),
            "dossier_bytes": dossier["physical_bytes"],
            "dossier_semantic_sha256": dossier["semantic_sha256"],
        },
        "sharding": {
            "shard_count": len(shards),
            "workers": workers,
            "target_seconds": target_seconds,
            "max_segments": max_segments,
            "overlap_segments": overlap_segments,
            "core_segment_count": sum(len(shard.core_segment_ids) for shard in shards),
            "context_segment_count": sum(len(shard.context_segment_ids) for shard in shards),
        },
        "cache": {
            "cold": first_cache,
            "warm": second_cache,
            "warm_reused_without_rewrite": cache_unchanged,
        },
        "quality": {
            "candidate_ids_equal": candidate_ids_equal,
            "exact_candidate_count": exact_candidates,
            "candidate_count": len(oracle),
            "proof_edge_count": len(reduced["proof_graph"]["evidence_edges"]),
            "relation_edge_count": len(reduced["proof_graph"]["relation_edges"]),
            "calibration_count": len(dossier["calibrations"]),
            "covered_calibration_count": sum(
                bool(item.get("semantic_candidate_ids"))
                for item in dossier["calibrations"]
            ),
            "ledger_group_count": len(dossier["ledger_groups"]),
            "errors": all_errors,
        },
        "audit_surface": {
            "selected_candidate_count": audit_plan["selected_candidate_count"],
            "selected_segment_count": len(audit_plan["selected_source_clean_indexes"]),
            "targeted_bytes": targeted_bytes,
            "full_dossier_bytes": dossier["physical_bytes"],
            "byte_reduction_ratio": round(1 - targeted_bytes / dossier["physical_bytes"], 4),
            "segment_reduction_ratio": round(1 - len(audit_plan["selected_source_clean_indexes"]) / len(dossier["transcript"]), 4),
        },
        "performance": {
            "cold_compile_ms": round(cold_ms, 3),
            "warm_compile_ms": round(warm_ms, 3),
            "total_benchmark_ms": round((time.perf_counter() - started) * 1000, 3),
            "semantic_model_calls": 0,
        },
        "latency_feasibility": {
            "parallel_batches": math.ceil(len(shards) / max(1, workers)),
            "not_measured": True,
            "scenarios": [
                {
                    "seconds_per_shard_call": seconds,
                    "projected_parallel_extraction_seconds": (
                        math.ceil(len(shards) / max(1, workers)) * seconds
                    ),
                }
                for seconds in (30, 60, 90)
            ],
        },
        "adoption_gate": {
            "status": "prototype_passed_mechanics_only" if not all_errors and candidate_ids_equal and exact_candidates == len(oracle) else "prototype_failed",
            "production_ready": False,
            "remaining_requirements": [
                "Run an independent model adapter that cannot see approved candidates.",
                "Benchmark material recall and unsupported-claim rate on at least three completed episodes.",
                "Validate final Sol finding rate is non-inferior to the current full audit.",
            ],
        },
    }
    report["semantic_sha256"] = semantic_hash(report)

    write_json(output_dir / "architecture_manifest.json", {
        "compiler_version": COMPILER_VERSION,
        "episode_video_id": dossier["video_id"],
        "source_dossier": str(dossier_path),
        "source_dossier_semantic_sha256": dossier["semantic_sha256"],
        "shards": [shard.as_dict() for shard in shards],
    })
    write_jsonl(output_dir / "shard_requests.jsonl", shard_requests)
    write_jsonl(output_dir / "semantic_atoms.jsonl", reduced["atoms"])
    write_json(output_dir / "proof_graph.json", reduced["proof_graph"])
    write_json(output_dir / "risk_targeted_audit_plan.json", audit_plan)
    write_json(output_dir / "benchmark_report.json", report)
    return report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    benchmark = subparsers.add_parser("benchmark-replay")
    benchmark.add_argument("--dossier", type=Path, required=True)
    benchmark.add_argument("--output-dir", type=Path, required=True)
    benchmark.add_argument("--workers", type=int, default=8)
    benchmark.add_argument("--target-seconds", type=float, default=480.0)
    benchmark.add_argument("--max-segments", type=int, default=140)
    benchmark.add_argument("--overlap-segments", type=int, default=3)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if args.command == "benchmark-replay":
        report = benchmark_replay(
            args.dossier,
            args.output_dir,
            workers=args.workers,
            target_seconds=args.target_seconds,
            max_segments=args.max_segments,
            overlap_segments=args.overlap_segments,
        )
        print(json.dumps(report, ensure_ascii=False))
        return 0 if report["adoption_gate"]["status"] != "prototype_failed" else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
