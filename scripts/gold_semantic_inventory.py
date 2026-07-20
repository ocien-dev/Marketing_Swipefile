#!/usr/bin/env python3
"""Archived blind inventory research; never a production gold route.

The inventory is built solely from the transcript and calibration source
locations.  It never exposes approved candidates to a model request.  Each
item has one core-shard owner so a shard must either capture it, merge it into
another local atom, or exclude it with a source-grounded reason.  Only broken
or missing dispositions move to the much smaller gap-resolver queue.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from typing import Any, Iterable


INVENTORY_VERSION = "gold-semantic-pre-shard-inventory-v1"
NUMBER_RE = re.compile(
    r"(?i)(?:R\$\s*)?\d+(?:[.,]\d+)*(?:\s*%|\s*x|\s*vezes|\s*dias?|\s*meses?|\s*anos?)?"
    r"|\b(?:dois|duas|tr[eê]s|quatro|cinco|seis|sete|oito|nove|dez|"
    r"onze|doze|treze|catorze|quatorze|quinze|vinte|trinta|quarenta|cinquenta|"
    r"cem|cento|mil|milh[aã]o|milh[oõ]es|bilh[aã]o|bilh[oõ]es)\b"
)
BOUNDARY_RE = re.compile(
    r"(?i)\b(?:primeir[oa]|segund[oa]|terceir[oa]|quart[oa]|quint[oa]|"
    r"sext[oa]|s[eé]tim[oa]|[uú]ltim[oa]|passos?|etapas?|framework|"
    r"pilares?|alavancas?|antes|depois|por outro lado)\b"
)


def _fold(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value).lower()
        if not unicodedata.combining(character)
    )


def _source_item(segment: dict[str, Any]) -> dict[str, Any]:
    return {
        "segment_id": str(segment["segment_id"]),
        "clean_index": int(segment["clean_index"]),
        "quote_verbatim": str(segment["text"]),
    }


def build_pre_shard_inventory(
    transcript: Iterable[dict[str, Any]],
    calibrations: Iterable[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Build source-only numeric, calibration, and boundary inventories."""
    segments = sorted(transcript, key=lambda item: int(item["clean_index"]))
    by_index = {int(item["clean_index"]): item for item in segments}
    ordered_indexes = sorted(by_index)
    index_position = {index: position for position, index in enumerate(ordered_indexes)}
    numeric: list[dict[str, Any]] = []
    boundaries: list[dict[str, Any]] = []
    for segment in segments:
        source = _source_item(segment)
        for occurrence, match in enumerate(NUMBER_RE.finditer(source["quote_verbatim"]), 1):
            numeric.append({
                "inventory_id": f"NUM-{source['clean_index']:04d}-{occurrence:02d}",
                "kind": "numeric",
                "anchor_segment_id": source["segment_id"],
                "anchor_clean_index": source["clean_index"],
                "raw": match.group(0).strip(),
                "source": [source],
            })
        cues = sorted({_fold(match.group(0)) for match in BOUNDARY_RE.finditer(source["quote_verbatim"])})
        if cues:
            position = index_position[source["clean_index"]]
            source_indexes = ordered_indexes[max(0, position - 1) : position + 2]
            boundaries.append({
                "inventory_id": f"BND-{source['clean_index']:04d}",
                "kind": "boundary",
                "anchor_segment_id": source["segment_id"],
                "anchor_clean_index": source["clean_index"],
                "cues": cues,
                "source": [_source_item(by_index[index]) for index in source_indexes if index in by_index],
            })

    calibration: list[dict[str, Any]] = []
    for position, target in enumerate(calibrations, 1):
        indexes = sorted({int(value) for value in target.get("clean_indexes") or []})
        source = [_source_item(by_index[index]) for index in indexes if index in by_index]
        if not source:
            continue
        anchor = source[0]
        calibration.append({
            "inventory_id": f"CAL-{position:03d}",
            "kind": "calibration",
            "calibration_id": str(target.get("calibration_id") or f"calibration-{position}"),
            "anchor_segment_id": anchor["segment_id"],
            "anchor_clean_index": anchor["clean_index"],
            "source": source,
        })
    return {"numeric": numeric, "calibration": calibration, "boundary": boundaries}


def route_inventory_to_shards(
    inventory: dict[str, list[dict[str, Any]]],
    shards: Iterable[Any],
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Assign each inventory item to exactly one shard based on core ownership."""
    owner: dict[str, str] = {}
    names: list[str] = []
    for shard in shards:
        shard_id = str(shard.shard_id)
        names.append(shard_id)
        for segment_id in shard.core_segment_ids:
            if segment_id in owner:
                raise ValueError(f"duplicate shard owner for {segment_id}")
            owner[str(segment_id)] = shard_id
    routed: dict[str, dict[str, list[dict[str, Any]]]] = {
        name: {"numeric": [], "calibration": [], "boundary": []}
        for name in names
    }
    for category in ("numeric", "calibration", "boundary"):
        for item in inventory.get(category) or []:
            shard_id = owner.get(str(item.get("anchor_segment_id") or ""))
            if shard_id is None:
                raise ValueError(f"{item.get('inventory_id')}: anchor has no core-shard owner")
            routed[shard_id][category].append(item)
    for shard_id in names:
        for category in routed[shard_id]:
            routed[shard_id][category].sort(key=lambda item: str(item["inventory_id"]))
    return routed


def inventory_ids(inventory: dict[str, list[dict[str, Any]]]) -> set[str]:
    return {
        str(item["inventory_id"])
        for items in inventory.values()
        for item in items
    }


def validate_inventory_dispositions(
    request: dict[str, Any],
    response: dict[str, Any],
) -> tuple[list[str], list[dict[str, Any]]]:
    """Return hard disposition errors and the items still requiring resolution."""
    required = request.get("risk_inventory") or {}
    expected = {
        str(item["inventory_id"]): item
        for category in ("numeric", "calibration", "boundary")
        for item in required.get(category) or []
    }
    local_ids = {str(item.get("local_id") or "") for item in response.get("atoms") or []}
    actual: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for item in response.get("inventory_dispositions") or []:
        inventory_id = str(item.get("inventory_id") or "")
        if inventory_id in actual:
            errors.append(f"{inventory_id}: duplicate inventory disposition")
            continue
        actual[inventory_id] = item
        if inventory_id not in expected:
            errors.append(f"{inventory_id}: unknown inventory disposition")
            continue
        status = str(item.get("status") or "")
        candidates = [str(value) for value in item.get("candidate_local_ids") or []]
        reason = str(item.get("reason") or "").strip()
        if status not in {"captured", "merged", "excluded"}:
            errors.append(f"{inventory_id}: invalid inventory status")
        elif status in {"captured", "merged"} and (not candidates or not set(candidates) <= local_ids):
            errors.append(f"{inventory_id}: capture references missing local atom")
        elif status == "excluded" and not reason:
            errors.append(f"{inventory_id}: excluded inventory needs source-grounded reason")
    unresolved_ids = sorted(set(expected) - set(actual))
    errors.extend(f"{inventory_id}: missing inventory disposition" for inventory_id in unresolved_ids)
    unresolved = [expected[item] for item in unresolved_ids]
    for error in errors:
        inventory_id = error.split(":", 1)[0]
        if inventory_id in expected and expected[inventory_id] not in unresolved:
            unresolved.append(expected[inventory_id])
    return sorted(set(errors)), sorted(unresolved, key=lambda item: str(item["inventory_id"]))


def exact_dedupe_atoms(atoms: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Remove only byte-equivalent semantic duplicates; never infer a merge."""
    retained: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    seen: dict[tuple[str, tuple[str, ...], str], str] = {}
    for atom in atoms:
        evidence = tuple(sorted(str(value) for value in atom.get("evidence_segment_ids") or []))
        key = (_fold(str(atom.get("source_claim") or "")).strip(), evidence, str(atom.get("type") or ""))
        local_id = str(atom.get("local_id") or "")
        if key in seen:
            duplicates.append({"duplicate_local_id": local_id, "canonical_local_id": seen[key]})
            continue
        seen[key] = local_id
        retained.append(atom)
    return retained, duplicates


def build_targeted_gap_requests(
    transcript: Iterable[dict[str, Any]],
    unresolved: Iterable[dict[str, Any]],
    *,
    radius: int = 2,
) -> list[dict[str, Any]]:
    """Create local source windows for only the unresolved inventory items."""
    segments = sorted(transcript, key=lambda item: int(item["clean_index"]))
    by_index = {int(item["clean_index"]): item for item in segments}
    requests: list[dict[str, Any]] = []
    for item in sorted(unresolved, key=lambda value: str(value["inventory_id"])):
        anchor = int(item["anchor_clean_index"])
        source = [
            _source_item(by_index[index])
            for index in range(anchor - radius, anchor + radius + 1)
            if index in by_index
        ]
        requests.append({
            "kind": "gold_semantic_targeted_gap_request",
            "inventory_item": item,
            "source_window": source,
            "requirements": {
                "resolve_only_this_inventory_item": True,
                "preserve_quote_verbatim": True,
                "do_not_invent_candidate_or_relation": True,
            },
        })
    return requests


def build_relation_review_requests(
    transcript: Iterable[dict[str, Any]],
    boundary_items: Iterable[dict[str, Any]],
    *,
    radius: int = 2,
    merge_distance: int = 4,
) -> list[dict[str, Any]]:
    """Create compact windows for an optional relation-only review pass.

    Adjacent enumerations belong to one window, so the future model can decide
    parent/child edges without receiving unrelated atoms or the whole episode.
    """
    segments = sorted(transcript, key=lambda item: int(item["clean_index"]))
    by_index = {int(item["clean_index"]): item for item in segments}
    items = sorted(boundary_items, key=lambda item: int(item["anchor_clean_index"]))
    groups: list[list[dict[str, Any]]] = []
    for item in items:
        if not groups or int(item["anchor_clean_index"]) - int(groups[-1][-1]["anchor_clean_index"]) > merge_distance:
            groups.append([item])
        else:
            groups[-1].append(item)
    requests: list[dict[str, Any]] = []
    for number, group in enumerate(groups, 1):
        start = int(group[0]["anchor_clean_index"]) - radius
        end = int(group[-1]["anchor_clean_index"]) + radius
        requests.append({
            "kind": "gold_semantic_relation_review_request",
            "relation_window_id": f"REL-{number:03d}",
            "boundary_inventory_ids": [item["inventory_id"] for item in group],
            "source_window": [
                _source_item(by_index[index])
                for index in sorted(by_index)
                if start <= index <= end
            ],
            "requirements": {
                "relation_only": True,
                "propose_edges_only_when_source_proves_hierarchy": True,
                "preserve_quote_verbatim": True,
            },
        })
    return requests
