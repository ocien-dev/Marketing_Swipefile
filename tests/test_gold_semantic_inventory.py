from __future__ import annotations

from scripts.gold_semantic_compiler import plan_shards
from scripts.gold_semantic_inventory import (
    build_pre_shard_inventory,
    build_relation_review_requests,
    build_targeted_gap_requests,
    exact_dedupe_atoms,
    route_inventory_to_shards,
    validate_inventory_dispositions,
)


def _transcript() -> list[dict]:
    return [
        {
            "segment_id": f"fixture-transcript-{index:04d}",
            "clean_index": index - 1,
            "start_seconds": float((index - 1) * 60),
            "duration_seconds": 60.0,
            "text": text,
        }
        for index, text in enumerate([
            "O primeiro passo custa R$ 19,90.",
            "Depois teste duas headlines antes de escalar.",
            "O resultado reportado foi 42% em tres meses.",
            "A ultima etapa e medir a retencao.",
        ], 1)
    ]


def test_inventory_is_source_only_and_each_item_has_one_core_owner():
    transcript = _transcript()
    shards = plan_shards("fixture", transcript, target_seconds=120, max_segments=2)
    inventory = build_pre_shard_inventory(
        transcript,
        [{"calibration_id": "c1", "clean_indexes": [2], "semantic_candidate_ids": ["fixture-G001"]}],
    )
    routed = route_inventory_to_shards(inventory, shards)
    flattened = [
        item["inventory_id"]
        for per_shard in routed.values()
        for values in per_shard.values()
        for item in values
    ]
    expected = [
        item["inventory_id"]
        for values in inventory.values()
        for item in values
    ]
    assert sorted(flattened) == sorted(expected)
    assert len(flattened) == len(set(flattened))
    assert "fixture-G001" not in str(routed)


def test_dispositions_require_local_atom_or_exclusion_reason_and_emit_gap():
    transcript = _transcript()
    shards = plan_shards("fixture", transcript, target_seconds=500)
    inventory = build_pre_shard_inventory(transcript, [])
    routed = route_inventory_to_shards(inventory, shards)
    request = {
        "risk_inventory": routed[shards[0].shard_id],
        "source_segments": transcript,
    }
    required = [
        item["inventory_id"]
        for values in request["risk_inventory"].values()
        for item in values
    ]
    response = {
        "atoms": [{"local_id": "A001"}],
        "inventory_dispositions": [{
            "inventory_id": required[0], "status": "captured",
            "candidate_local_ids": ["A001"], "reason": "Literal source capture.",
        }],
    }
    errors, unresolved = validate_inventory_dispositions(request, response)
    assert errors
    assert {item["inventory_id"] for item in unresolved} == set(required[1:])
    gaps = build_targeted_gap_requests(transcript, unresolved, radius=1)
    assert len(gaps) == len(unresolved)
    assert all(len(item["source_window"]) <= 3 for item in gaps)
    assert all(item["requirements"]["resolve_only_this_inventory_item"] for item in gaps)


def test_exact_dedupe_removes_only_same_claim_evidence_and_type():
    atoms = [
        {"local_id": "A001", "source_claim": "Testar oferta.", "type": "principle", "evidence_segment_ids": ["s1"]},
        {"local_id": "A002", "source_claim": "Testar oferta.", "type": "principle", "evidence_segment_ids": ["s1"]},
        {"local_id": "A003", "source_claim": "Testar oferta.", "type": "procedure", "evidence_segment_ids": ["s1"]},
    ]
    retained, duplicates = exact_dedupe_atoms(atoms)
    assert [item["local_id"] for item in retained] == ["A001", "A003"]
    assert duplicates == [{"duplicate_local_id": "A002", "canonical_local_id": "A001"}]


def test_relation_windows_merge_nearby_framework_boundaries_only():
    transcript = _transcript()
    inventory = build_pre_shard_inventory(transcript, [])
    requests = build_relation_review_requests(transcript, inventory["boundary"], radius=1)
    assert len(requests) == 1
    assert requests[0]["requirements"]["relation_only"] is True
    assert len(requests[0]["source_window"]) <= len(transcript)
