#!/usr/bin/env python3
"""Archived blind benchmark adapter; never a production gold route.

The script has deliberately separate phases:

* ``prepare`` and ``score`` run on the Linux runtime;
* ``invoke`` is a transport-only phase for the authenticated Windows Codex CLI;
* approved candidates are never written under the transport work directory.

No command writes the active gold data root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable

from scripts.gold_semantic_compiler import (
    _evidence_indexes,
    build_shard_requests,
    load_dossier,
    plan_shards,
    semantic_hash,
    validate_shard_plan,
    write_json,
    write_jsonl,
)
from scripts.gold_semantic_inventory import (
    build_pre_shard_inventory,
    build_relation_review_requests,
    build_targeted_gap_requests,
    exact_dedupe_atoms,
    route_inventory_to_shards,
    validate_inventory_dispositions,
)


PROMPT_VERSION = "blind-semantic-adapter-v2-inventory"
JUDGE_PROMPT_VERSION = "blind-semantic-judge-v1"


ATOM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["shard_id", "atoms", "inventory_dispositions"],
    "properties": {
        "shard_id": {"type": "string"},
        "atoms": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "local_id", "title", "source_claim", "type", "themes",
                    "subthemes", "takeaway", "reported_case",
                    "causal_certainty", "claim_risk", "numbers", "steps",
                    "conditions", "caveats", "evidence_segment_ids",
                    "relation_hints",
                ],
                "properties": {
                    "local_id": {"type": "string"},
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
                    "evidence_segment_ids": {
                        "type": "array", "items": {"type": "string"},
                    },
                    "relation_hints": {
                        "type": "array",
                        "items": {
                            "type": "object", "additionalProperties": False,
                            "required": ["kind", "target_local_id"],
                            "properties": {
                                "kind": {"type": "string"},
                                "target_local_id": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
        "inventory_dispositions": {
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
        },
    },
}


JUDGE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "episode_video_id", "approved_candidate_assessments",
        "independent_atom_assessments", "metrics", "findings", "summary",
    ],
    "properties": {
        "episode_video_id": {"type": "string"},
        "approved_candidate_assessments": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False,
                "required": [
                    "candidate_id", "status", "matched_atom_ids", "material",
                    "reason",
                ],
                "properties": {
                    "candidate_id": {"type": "string"},
                    "status": {"type": "string"},
                    "matched_atom_ids": {"type": "array", "items": {"type": "string"}},
                    "material": {"type": "boolean"},
                    "reason": {"type": "string"},
                },
            },
        },
        "independent_atom_assessments": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["atom_id", "status", "reason"],
                "properties": {
                    "atom_id": {"type": "string"},
                    "status": {"type": "string"},
                    "reason": {"type": "string"},
                },
            },
        },
        "metrics": {
            "type": "object", "additionalProperties": False,
            "required": [
                "material_recall", "unsupported_claim_count", "partial_count",
                "number_recall", "procedure_recall", "caveat_recall",
                "relation_recall", "calibration_recall", "open_finding_count",
            ],
            "properties": {
                "material_recall": {"type": "number"},
                "unsupported_claim_count": {"type": "integer"},
                "partial_count": {"type": "integer"},
                "number_recall": {"type": "number"},
                "procedure_recall": {"type": "number"},
                "caveat_recall": {"type": "number"},
                "relation_recall": {"type": "number"},
                "calibration_recall": {"type": "number"},
                "open_finding_count": {"type": "integer"},
            },
        },
        "findings": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["severity", "category", "candidate_or_atom_ids", "description"],
                "properties": {
                    "severity": {"type": "string"},
                    "category": {"type": "string"},
                    "candidate_or_atom_ids": {"type": "array", "items": {"type": "string"}},
                    "description": {"type": "string"},
                },
            },
        },
        "summary": {"type": "string"},
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


def prepare_episode(dossier_path: Path, output_dir: Path, *, target_seconds: float, max_segments: int, overlap_segments: int) -> dict[str, Any]:
    dossier = load_dossier(dossier_path)
    shards = plan_shards(
        dossier["video_id"], dossier["transcript"], target_seconds=target_seconds,
        max_segments=max_segments, overlap_segments=overlap_segments,
    )
    errors = validate_shard_plan(dossier["transcript"], shards)
    if errors:
        raise ValueError("; ".join(errors))
    inventory = build_pre_shard_inventory(dossier["transcript"], dossier["calibrations"])
    routed_inventory = route_inventory_to_shards(inventory, shards)
    requests = build_shard_requests(
        dossier["video_id"], dossier["transcript"], shards,
        routed_inventory=routed_inventory,
    )
    approved_id_pattern = re.compile(rf"{re.escape(dossier['video_id'])}-G\d+")
    requests_dir = output_dir / "blind_requests"
    requests_dir.mkdir(parents=True, exist_ok=True)
    for request in requests:
        serialized = json.dumps(request, ensure_ascii=False, separators=(",", ":"))
        if approved_id_pattern.search(serialized):
            raise ValueError(f"approved candidate ID leaked into {request['shard']['shard_id']}")
        write_json(requests_dir / f"{request['shard']['shard_id']}.json", request)
    manifest = {
        "episode_video_id": dossier["video_id"],
        "source_dossier_semantic_sha256": dossier["semantic_sha256"],
        "segment_count": len(dossier["transcript"]),
        "approved_candidate_count_hidden_from_adapter": len(dossier["candidates"]),
        "shard_count": len(requests),
        "risk_inventory_counts": {
            category: len(items) for category, items in inventory.items()
        },
        "request_semantic_sha256": semantic_hash(requests),
        "blindness": {
            "approved_candidate_ids_in_requests": False,
            "approved_candidates_written_to_transport_dir": False,
        },
    }
    write_json(output_dir / "episode_manifest.json", manifest)
    return manifest


def _adapter_prompt(request: dict[str, Any]) -> str:
    return """You are a stateless semantic compiler. Do not call tools, inspect files, browse, or use any information outside the JSON request below.

Extract every independently useful marketing or business insight whose primary evidence is in a segment with is_core=true. Context-only segments may clarify a core claim but may not own an atom. Ignore greetings, promotion, interviewer restatements, and biography unless they support a transferable mechanism, decision rule, procedure, warning, or reported result.

Rules:
- One atomic proposition per atom. Split mechanisms, outcomes, warnings, and procedures when independently useful.
- evidence_segment_ids must be copied only from source_segments and include at least one core segment. Include every segment needed to prove the claim.
- Preserve every material number in numbers.raw exactly as spoken in the referenced segment text. Do not calculate or repair uncertain numbers.
- Procedures require ordered steps. Reported examples require reported_case=true, honest attribution, and caveats when baseline, sample, or independent verification is missing.
- relation_hints may reference only local_id values emitted in this same shard. Use kind parent, child, supports, contrasts, or overlaps only when useful.
- risk_inventory is source-only recall coverage. Return exactly one disposition for every listed inventory_id: captured or merged must reference a local atom; excluded must give a concise source-grounded reason. Never invent an item or silently omit one.
- Editorial fields should be concise Portuguese ASCII. Source evidence is represented by IDs and will be hydrated verbatim by the deterministic reducer.
- local_id values must be unique within the shard and follow A001, A002, ...
- Return only the JSON object required by the output schema.

REQUEST_JSON:
""" + json.dumps(request, ensure_ascii=False, separators=(",", ":"))


def _judge_prompt(packet: dict[str, Any]) -> str:
    return """You are the final independent evaluator of a blind semantic-extraction benchmark. Do not call tools or use information outside the packet. The approved candidates are a frozen gold reference and were hidden from the extractor. The independent atoms contain source evidence hydrated deterministically from transcript segment IDs.

Compare propositions, not wording. For each approved candidate classify status as matched, partial, or missed and identify independent atom IDs. For each independent atom classify status as supported_useful, supported_redundant, or unsupported. A claim is unsupported if its evidence does not prove the material proposition, number, causality, procedure, or attribution. Compute recall separately for material candidates, numbers, procedures, caveats, relations, and calibration targets. Treat an approved candidate as material unless it is clearly incidental. Findings should represent defects that a final gold audit would ask to correct, not stylistic preferences.

Metrics must be ratios from 0 to 1. relation_recall is 1 when the approved reference has no relations. calibration_recall measures whether each calibration target has at least one semantically equivalent independent atom. Return only the output-schema JSON.

PACKET_JSON:
""" + json.dumps(packet, ensure_ascii=False, separators=(",", ":"))


def _tool_events(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    forbidden = {"command_execution", "file_change", "mcp_tool_call", "web_search", "browser"}
    found = []
    for event in events:
        serialized = json.dumps(event, ensure_ascii=False).lower()
        if any(marker in serialized for marker in forbidden):
            found.append(event)
    return found


def _run_codex_call(input_path: Path, output_path: Path, log_path: Path, *, schema_path: Path, codex_exe: Path, model: str, effort: str, work_dir: Path, judge: bool) -> dict[str, Any]:
    request = _read_json(input_path)
    prompt = _judge_prompt(request) if judge else _adapter_prompt(request)
    started = time.perf_counter()
    temporary_output = output_path.with_suffix(".tmp.json")
    command = [
        str(codex_exe), "exec", "--ephemeral", "--sandbox", "read-only",
        "--skip-git-repo-check", "--ignore-user-config", "--ignore-rules",
        "--json", "-C", str(work_dir), "-m", model,
        "-c", f"model_reasoning_effort='{effort}'", "--output-schema",
        str(schema_path), "-o", str(temporary_output), "-",
    ]
    completed = subprocess.run(
        command, input=prompt, text=True, encoding="utf-8", errors="replace",
        capture_output=True, timeout=600, check=False,
    )
    duration = time.perf_counter() - started
    _atomic_text(log_path, completed.stdout + "\n--- STDERR ---\n" + completed.stderr)
    events = []
    for line in completed.stdout.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    used_tools = _tool_events(events)
    if completed.returncode != 0:
        raise RuntimeError(f"codex call failed ({completed.returncode}); see {log_path}")
    if used_tools:
        raise RuntimeError(f"codex call used forbidden tools; see {log_path}")
    result = _read_json(temporary_output)
    if not judge and result.get("shard_id") != request["shard"]["shard_id"]:
        raise ValueError(f"shard identity mismatch in {input_path.name}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_output.replace(output_path)
    token_usage = {}
    for event in events:
        usage = event.get("usage") or (event.get("data") or {}).get("usage")
        if isinstance(usage, dict):
            token_usage = usage
    return {
        "input": input_path.name, "output": output_path.name,
        "duration_seconds": round(duration, 3), "model": model,
        "reasoning_effort": effort, "tool_event_count": 0,
        "token_usage": token_usage,
        "input_semantic_sha256": request.get("semantic_sha256"),
    }


def invoke_directory(input_dir: Path, output_dir: Path, *, schema_path: Path, codex_exe: Path, model: str, effort: str, workers: int, work_dir: Path, judge: bool) -> dict[str, Any]:
    inputs = sorted(input_dir.glob("*.json"))
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "logs").mkdir(exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    calls = []
    failures = []
    metadata_dir = output_dir / "metadata"
    metadata_dir.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        future_map = {}
        for input_path in inputs:
            output_path = output_dir / input_path.name
            metadata_path = metadata_dir / input_path.name
            request_hash = _read_json(input_path).get("semantic_sha256")
            metadata = _read_json(metadata_path) if metadata_path.exists() else {}
            if output_path.exists() and metadata.get("input_semantic_sha256") == request_hash:
                calls.append({
                    "input": input_path.name, "output": output_path.name,
                    "cache_hit": True, "input_semantic_sha256": request_hash,
                })
                continue
            future = pool.submit(
                _run_codex_call, input_path, output_path,
                output_dir / "logs" / f"{input_path.stem}.jsonl",
                schema_path=schema_path, codex_exe=codex_exe, model=model,
                effort=effort, work_dir=work_dir, judge=judge,
            )
            future_map[future] = input_path
        for future in as_completed(future_map):
            try:
                call = future.result()
                write_json(metadata_dir / call["input"], {
                    "input_semantic_sha256": call["input_semantic_sha256"],
                    "model": call["model"],
                    "reasoning_effort": call["reasoning_effort"],
                })
                calls.append(call)
            except Exception as exc:
                failures.append({"input": future_map[future].name, "error": str(exc)})
    report = {
        "mode": "judge" if judge else "blind_adapter",
        "model": model, "reasoning_effort": effort,
        "input_count": len(inputs), "completed_count": len(calls),
        "failure_count": len(failures), "failures": failures,
        "wall_seconds": round(time.perf_counter() - started, 3),
        "calls": sorted(calls, key=lambda item: item["input"]),
    }
    write_json(output_dir / "invocation_report.json", report)
    if failures:
        raise RuntimeError(f"{len(failures)} model calls failed")
    return report


def _normalize_text(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def _number_raws(candidate: dict[str, Any]) -> set[str]:
    return {str(item.get("raw") or "").strip().lower() for item in candidate.get("numbers") or [] if item.get("raw")}


def _hydrate_atoms(dossier: dict[str, Any], request_dir: Path, response_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    source = {str(item["segment_id"]): item for item in dossier["transcript"]}
    atoms = []
    errors = []
    serial = 0
    for request_path in sorted(request_dir.glob("*.json")):
        request = _read_json(request_path)
        response = _read_json(response_dir / request_path.name)
        inventory_errors, _ = validate_inventory_dispositions(request, response)
        errors.extend(f"{request_path.name}:{error}" for error in inventory_errors)
        allowed = {item["segment_id"] for item in request["source_segments"]}
        core = {item["segment_id"] for item in request["source_segments"] if item["is_core"]}
        local_ids = set()
        for raw_atom in response.get("atoms", []):
            serial += 1
            local_id = str(raw_atom.get("local_id") or "")
            if not local_id or local_id in local_ids:
                errors.append(f"{request_path.name}: duplicate/missing local_id {local_id}")
                continue
            local_ids.add(local_id)
            evidence_ids = list(dict.fromkeys(str(value) for value in raw_atom.get("evidence_segment_ids") or []))
            if not evidence_ids or not set(evidence_ids) <= allowed or not set(evidence_ids) & core:
                errors.append(f"{request_path.name}:{local_id}: invalid evidence ownership")
                continue
            atom_id = f"{dossier['video_id']}-BA{serial:03d}"
            atoms.append({
                "atom_id": atom_id,
                "shard_id": request["shard"]["shard_id"],
                "local_id": local_id,
                "title": raw_atom["title"],
                "source_claim": raw_atom["source_claim"],
                "type": raw_atom["type"],
                "themes": raw_atom["themes"],
                "subthemes": raw_atom["subthemes"],
                "takeaway": raw_atom["takeaway"],
                "reported_case": raw_atom["reported_case"],
                "causal_certainty": raw_atom["causal_certainty"],
                "claim_risk": raw_atom["claim_risk"],
                "numbers": raw_atom["numbers"],
                "steps": raw_atom["steps"],
                "conditions": raw_atom["conditions"],
                "caveats": raw_atom["caveats"],
                "relation_hints": raw_atom["relation_hints"],
                "evidence": [
                    {
                        "segment_id": segment_id,
                        "clean_index": source[segment_id]["clean_index"],
                        "quote_verbatim": source[segment_id]["text"],
                    }
                    for segment_id in evidence_ids
                ],
            })
    deduped, _ = exact_dedupe_atoms(atoms)
    return deduped, errors


def prepare_targeted_gaps(
    dossier_path: Path,
    request_dir: Path,
    response_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Write only local requests for inventory items unresolved by blind shards."""
    dossier = load_dossier(dossier_path)
    unresolved: list[dict[str, Any]] = []
    errors: list[str] = []
    for request_path in sorted(request_dir.glob("*.json")):
        request = _read_json(request_path)
        response = _read_json(response_dir / request_path.name)
        item_errors, items = validate_inventory_dispositions(request, response)
        errors.extend(f"{request_path.name}:{item}" for item in item_errors)
        unresolved.extend(items)
    unique = {str(item["inventory_id"]): item for item in unresolved}
    requests = build_targeted_gap_requests(dossier["transcript"], unique.values())
    output_dir.mkdir(parents=True, exist_ok=True)
    for request in requests:
        inventory_id = request["inventory_item"]["inventory_id"]
        write_json(output_dir / f"{inventory_id}.json", request)
    manifest = {
        "episode_video_id": dossier["video_id"],
        "unresolved_inventory_count": len(requests),
        "source_disposition_errors": sorted(set(errors)),
        "gap_requests_semantic_sha256": semantic_hash(requests),
    }
    write_json(output_dir / "gap_manifest.json", manifest)
    return manifest


def prepare_relation_windows(
    dossier_path: Path,
    request_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Write compact source windows for the optional relation-only pass."""
    dossier = load_dossier(dossier_path)
    boundaries = [
        item
        for request_path in sorted(request_dir.glob("*.json"))
        for item in (_read_json(request_path).get("risk_inventory") or {}).get("boundary") or []
    ]
    requests = build_relation_review_requests(dossier["transcript"], boundaries)
    output_dir.mkdir(parents=True, exist_ok=True)
    for request in requests:
        write_json(output_dir / f"{request['relation_window_id']}.json", request)
    manifest = {
        "episode_video_id": dossier["video_id"],
        "relation_window_count": len(requests),
        "relation_requests_semantic_sha256": semantic_hash(requests),
    }
    write_json(output_dir / "relation_manifest.json", manifest)
    return manifest


def build_comparison_packet(dossier_path: Path, request_dir: Path, response_dir: Path, output_path: Path) -> dict[str, Any]:
    dossier = load_dossier(dossier_path)
    atoms, errors = _hydrate_atoms(dossier, request_dir, response_dir)
    transcript_by_index = {int(item["clean_index"]): item for item in dossier["transcript"]}
    approved = []
    for candidate in dossier["candidates"]:
        evidence = [
            {
                "segment_id": transcript_by_index[index]["segment_id"],
                "clean_index": index,
                "quote_verbatim": transcript_by_index[index]["text"],
            }
            for index in _evidence_indexes(candidate)
            if index in transcript_by_index
        ]
        approved.append({"candidate": candidate, "evidence": evidence})
    calibration_targets = []
    for item in dossier["calibrations"]:
        indexes = [int(value) for value in item.get("clean_indexes") or []]
        calibration_targets.append({
            "calibration_id": item.get("calibration_id"),
            "semantic_candidate_ids": item.get("semantic_candidate_ids") or [],
            "source": [
                {"clean_index": index, "text": transcript_by_index[index]["text"]}
                for index in indexes if index in transcript_by_index
            ],
        })
    approved_evidence = {
        entry["candidate"]["candidate_id"]: {item["clean_index"] for item in entry["evidence"]}
        for entry in approved
    }
    atom_evidence = {
        atom["atom_id"]: {item["clean_index"] for item in atom["evidence"]}
        for atom in atoms
    }
    evidence_anchored = {
        candidate_id: [atom_id for atom_id, indexes in atom_evidence.items() if indexes & candidate_indexes]
        for candidate_id, candidate_indexes in approved_evidence.items()
    }
    approved_number_raws = set().union(*(_number_raws(item["candidate"]) for item in approved)) if approved else set()
    atom_number_raws = set().union(*(_number_raws(atom) for atom in atoms)) if atoms else set()
    packet = {
        "episode_video_id": dossier["video_id"],
        "adapter": {"model_outputs_are_independent": True, "approved_candidates_hidden_during_extraction": True},
        "approved_candidates": approved,
        "independent_atoms": atoms,
        "calibration_targets": calibration_targets,
        "deterministic_preview": {
            "errors": errors,
            "approved_candidate_count": len(approved),
            "independent_atom_count": len(atoms),
            "approved_candidates_with_any_evidence_anchor": sum(bool(value) for value in evidence_anchored.values()),
            "evidence_anchor_recall": round(sum(bool(value) for value in evidence_anchored.values()) / max(1, len(approved)), 4),
            "approved_number_raw_count": len(approved_number_raws),
            "independent_number_raw_count": len(atom_number_raws),
            "exact_number_raw_recall": round(len(approved_number_raws & atom_number_raws) / max(1, len(approved_number_raws)), 4),
            "approved_procedure_count": sum(bool(item["candidate"].get("steps")) for item in approved),
            "independent_procedure_count": sum(bool(atom.get("steps")) for atom in atoms),
            "approved_relation_reference_count": sum(
                bool((item["candidate"].get("relations") or {}).get("parent_candidate_id"))
                + len((item["candidate"].get("relations") or {}).get("child_candidate_ids") or [])
                for item in approved
            ),
            "independent_relation_hint_count": sum(len(atom.get("relation_hints") or []) for atom in atoms),
            "evidence_anchors": evidence_anchored,
        },
    }
    write_json(output_path, packet)
    return packet


def finalize_report(episode_dirs: list[Path], output_path: Path) -> dict[str, Any]:
    episodes = []
    for episode_dir in episode_dirs:
        invocation = _read_json(episode_dir / "responses" / "invocation_report.json")
        packet = _read_json(episode_dir / "comparison_packet.json")
        judge = _read_json(episode_dir / "judge_response.json")
        episodes.append({
            "episode_video_id": packet["episode_video_id"],
            "adapter_wall_seconds": invocation["wall_seconds"],
            "shard_count": invocation["input_count"],
            "deterministic_preview": packet["deterministic_preview"],
            "judge_metrics": judge["metrics"],
            "judge_summary": judge["summary"],
            "judge_findings": judge["findings"],
        })
    metrics = [item["judge_metrics"] for item in episodes]
    production_ready = bool(episodes) and all(
        item["material_recall"] >= 0.98
        and item["unsupported_claim_count"] == 0
        and item["open_finding_count"] == 0
        for item in metrics
    ) and all(item["adapter_wall_seconds"] < 600 for item in episodes)
    report = {
        "kind": "gold_semantic_independent_adapter_benchmark",
        "prompt_version": PROMPT_VERSION,
        "judge_prompt_version": JUDGE_PROMPT_VERSION,
        "episodes": episodes,
        "aggregate": {
            "episode_count": len(episodes),
            "mean_material_recall": round(sum(item["material_recall"] for item in metrics) / max(1, len(metrics)), 4),
            "unsupported_claim_count": sum(item["unsupported_claim_count"] for item in metrics),
            "open_finding_count": sum(item["open_finding_count"] for item in metrics),
            "mean_adapter_wall_seconds": round(sum(item["adapter_wall_seconds"] for item in episodes) / max(1, len(episodes)), 3),
        },
        "adoption_gate": {
            "production_ready": production_ready,
            "decision": "adopt" if production_ready else "do_not_adopt_yet",
            "requirements": {
                "material_recall_minimum": 0.98,
                "unsupported_claims": 0,
                "open_final_audit_findings": 0,
                "adapter_wall_seconds_per_episode_maximum": 600,
            },
        },
    }
    report["semantic_sha256"] = semantic_hash(report)
    write_json(output_path, report)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--dossier", type=Path, required=True)
    prepare.add_argument("--output-dir", type=Path, required=True)
    prepare.add_argument("--target-seconds", type=float, default=480)
    prepare.add_argument("--max-segments", type=int, default=140)
    prepare.add_argument("--overlap-segments", type=int, default=3)
    invoke = sub.add_parser("invoke")
    invoke.add_argument("--input-dir", type=Path, required=True)
    invoke.add_argument("--output-dir", type=Path, required=True)
    invoke.add_argument("--schema", type=Path, required=True)
    invoke.add_argument("--codex-exe", type=Path, required=True)
    invoke.add_argument("--model", default="gpt-5.6-terra")
    invoke.add_argument("--effort", default="high")
    invoke.add_argument("--workers", type=int, default=8)
    invoke.add_argument("--work-dir", type=Path, required=True)
    invoke.add_argument("--judge", action="store_true")
    score = sub.add_parser("score")
    score.add_argument("--dossier", type=Path, required=True)
    score.add_argument("--request-dir", type=Path, required=True)
    score.add_argument("--response-dir", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    gaps = sub.add_parser("prepare-gaps")
    gaps.add_argument("--dossier", type=Path, required=True)
    gaps.add_argument("--request-dir", type=Path, required=True)
    gaps.add_argument("--response-dir", type=Path, required=True)
    gaps.add_argument("--output-dir", type=Path, required=True)
    relations = sub.add_parser("prepare-relations")
    relations.add_argument("--dossier", type=Path, required=True)
    relations.add_argument("--request-dir", type=Path, required=True)
    relations.add_argument("--output-dir", type=Path, required=True)
    schema = sub.add_parser("write-schema")
    schema.add_argument("--output", type=Path, required=True)
    schema.add_argument("--judge", action="store_true")
    final = sub.add_parser("finalize")
    final.add_argument("--episode-dir", type=Path, action="append", required=True)
    final.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "prepare":
        result = prepare_episode(args.dossier, args.output_dir, target_seconds=args.target_seconds, max_segments=args.max_segments, overlap_segments=args.overlap_segments)
    elif args.command == "write-schema":
        result = JUDGE_SCHEMA if args.judge else ATOM_SCHEMA
        write_json(args.output, result)
    elif args.command == "invoke":
        result = invoke_directory(args.input_dir, args.output_dir, schema_path=args.schema, codex_exe=args.codex_exe, model=args.model, effort=args.effort, workers=args.workers, work_dir=args.work_dir, judge=args.judge)
    elif args.command == "score":
        result = build_comparison_packet(args.dossier, args.request_dir, args.response_dir, args.output)
    elif args.command == "prepare-gaps":
        result = prepare_targeted_gaps(args.dossier, args.request_dir, args.response_dir, args.output_dir)
    elif args.command == "prepare-relations":
        result = prepare_relation_windows(args.dossier, args.request_dir, args.output_dir)
    elif args.command == "finalize":
        result = finalize_report(args.episode_dir, args.output)
    else:
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
