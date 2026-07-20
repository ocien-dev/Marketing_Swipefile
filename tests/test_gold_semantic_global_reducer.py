from __future__ import annotations

import json
from pathlib import Path

from scripts.gold_semantic_compiler import write_json
from scripts.gold_semantic_global_reducer import (
    build_compact_judge_packet,
    build_numeric_inventory,
    prepare_reducer_request,
    reconcile_numeric_evidence,
    validate_reducer_output,
)


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    video_id = "fixture"
    request_dir = tmp_path / "requests"
    request_dir.mkdir()
    segments = [
        {"segment_id": f"{video_id}-transcript-0001", "clean_index": 0, "text": "O primeiro framework tem duas etapas.", "is_core": True},
        {"segment_id": f"{video_id}-transcript-0002", "clean_index": 1, "text": "O resultado reportado foi 42%.", "is_core": True},
        {"segment_id": f"{video_id}-transcript-0003", "clean_index": 2, "text": "Depois execute o teste automatico.", "is_core": True},
    ]
    write_json(request_dir / "s1.json", {
        "episode_video_id": video_id,
        "shard": {"shard_id": "s1"},
        "source_segments": segments,
    })
    approved = {
        "candidate_id": f"{video_id}-G001", "title": "Framework de duas etapas",
        "source_claim": "O framework tem duas etapas.", "takeaway_applicavel": "Aplicar duas etapas.",
        "minimal_clean_indexes": [0], "support_clean_indexes": [], "numbers": [{"raw": "duas"}],
        "steps": [], "relations": {"parent_candidate_id": None, "child_candidate_ids": []},
    }
    atom = {
        "atom_id": f"{video_id}-BA001", "title": "Resultado", "source_claim": "O resultado foi 42%.",
        "type": "reported_case", "themes": ["testing"], "subthemes": [], "takeaway": "Medir o resultado.",
        "reported_case": True, "causal_certainty": "reported", "claim_risk": "medium",
        "numbers": [{"raw": "42%", "role": "result", "value_status": "reported"}],
        "steps": [], "conditions": [], "caveats": [], "relation_hints": [],
        "evidence": [{"segment_id": f"{video_id}-transcript-0002", "clean_index": 1, "quote_verbatim": segments[1]["text"]}],
    }
    comparison = tmp_path / "comparison.json"
    write_json(comparison, {
        "episode_video_id": video_id,
        "approved_candidates": [{"candidate": approved, "evidence": [{"segment_id": segments[0]["segment_id"], "clean_index": 0, "quote_verbatim": segments[0]["text"]}]}],
        "independent_atoms": [atom],
        "calibration_targets": [{"calibration_id": "c1", "semantic_candidate_ids": [approved["candidate_id"]], "source": [{"clean_index": 0, "text": segments[0]["text"]}]}],
    })
    return comparison, request_dir


def _valid_response(request: dict) -> dict:
    video_id = request["episode_video_id"]
    numeric = []
    for item in request["numeric_inventory"]:
        numeric.append({
            "inventory_id": item["inventory_id"], "status": "captured",
            "candidate_local_ids": ["R001" if item["clean_index"] == 0 else "R002"],
            "reason": "Material number captured literally.",
        })
    return {
        "episode_video_id": video_id,
        "summary": "Reduced fixture.",
        "candidates": [
            {
                "local_id": "R001", "source_atom_ids": [], "title": "Framework de duas etapas",
                "source_claim": "O framework tem duas etapas.", "type": "framework", "themes": ["testing"],
                "subthemes": [], "takeaway": "Aplicar as duas etapas.", "reported_case": False,
                "causal_certainty": "asserted", "claim_risk": "low",
                "numbers": [{"raw": "duas", "role": "step_count", "value_status": "reported"}],
                "steps": [], "conditions": [], "caveats": [],
                "evidence_segment_ids": [f"{video_id}-transcript-0001"],
                "relations": {"parent_local_id": None, "child_local_ids": ["R002"]},
            },
            {
                "local_id": "R002", "source_atom_ids": [f"{video_id}-BA001"], "title": "Resultado de 42%",
                "source_claim": "O resultado reportado foi 42%.", "type": "reported_case", "themes": ["testing"],
                "subthemes": [], "takeaway": "Medir o resultado reportado.", "reported_case": True,
                "causal_certainty": "reported", "claim_risk": "medium",
                "numbers": [{"raw": "42%", "role": "result", "value_status": "reported"}],
                "steps": [], "conditions": [], "caveats": ["Resultado reportado."],
                "evidence_segment_ids": [f"{video_id}-transcript-0002"],
                "relations": {"parent_local_id": "R001", "child_local_ids": []},
            },
        ],
        "numeric_dispositions": numeric,
        "calibration_dispositions": [{
            "inventory_id": "CAL-001", "status": "captured", "candidate_local_ids": ["R001"],
            "reason": "Calibration proposition captured.",
        }],
    }


def test_prepare_is_blind_and_builds_literal_inventories(tmp_path: Path):
    comparison, request_dir = _fixture(tmp_path)
    request = prepare_reducer_request(comparison, request_dir, tmp_path / "request.json", tmp_path / "schema.json")
    serialized = json.dumps(request, ensure_ascii=False)
    assert "fixture-G001" not in serialized
    raws = {item["raw"] for item in request["numeric_inventory"]}
    assert {"duas", "42%"} <= raws
    assert request["calibration_inventory"][0]["source"][0]["clean_index"] == 0


def test_validation_requires_complete_inventories_and_symmetric_relations(tmp_path: Path):
    comparison, request_dir = _fixture(tmp_path)
    request_path = tmp_path / "request.json"
    prepare_reducer_request(comparison, request_dir, request_path, tmp_path / "schema.json")
    request = json.loads(request_path.read_text(encoding="utf-8"))
    response = _valid_response(request)
    response["numeric_dispositions"] = response["numeric_dispositions"][:-1]
    response["candidates"][1]["relations"]["parent_local_id"] = None
    response_path = tmp_path / "response.json"
    write_json(response_path, response)
    report = validate_reducer_output(request_path, response_path, tmp_path / "reduced.json", tmp_path / "report.json")
    assert report["status"] == "fail"
    assert any("missing dispositions" in item for item in report["hard_errors"])
    assert any("asymmetric relation" in item for item in report["hard_errors"])


def test_validation_rejects_nonliteral_numbers_and_unsupported_procedure(tmp_path: Path):
    comparison, request_dir = _fixture(tmp_path)
    request_path = tmp_path / "request.json"
    prepare_reducer_request(comparison, request_dir, request_path, tmp_path / "schema.json")
    request = json.loads(request_path.read_text(encoding="utf-8"))
    response = _valid_response(request)
    response["candidates"][1]["numbers"][0]["raw"] = "99%"
    response["candidates"][1]["steps"] = ["Configurar um pixel externo invisivel."]
    response_path = tmp_path / "response.json"
    write_json(response_path, response)
    report = validate_reducer_output(request_path, response_path, tmp_path / "reduced.json", tmp_path / "report.json")
    assert any("number raw not literal" in item for item in report["hard_errors"])
    assert any("procedure steps lack evidence" in item for item in report["hard_errors"])


def test_reconcile_adds_literal_source_and_removes_fabricated_number(tmp_path: Path):
    comparison, request_dir = _fixture(tmp_path)
    request_path = tmp_path / "request.json"
    prepare_reducer_request(comparison, request_dir, request_path, tmp_path / "schema.json")
    request = json.loads(request_path.read_text(encoding="utf-8"))
    response = _valid_response(request)
    response["candidates"][0]["numbers"].append({"raw": "42%", "role": "result", "value_status": "reported"})
    response["candidates"][0]["numbers"].append({"raw": "99%", "role": "fabricated", "value_status": "reported"})
    response_path = tmp_path / "response.json"
    write_json(response_path, response)
    report = reconcile_numeric_evidence(request_path, response_path, tmp_path / "reconciled.json", tmp_path / "reconciliation.json")
    assert report["added_evidence_count"] == 1
    assert report["removed_number_count"] == 1
    reconciled = json.loads((tmp_path / "reconciled.json").read_text(encoding="utf-8"))
    assert "fixture-transcript-0002" in reconciled["candidates"][0]["evidence_segment_ids"]
    assert "99%" not in {item["raw"] for item in reconciled["candidates"][0]["numbers"]}


def test_reconcile_uses_nearest_literal_match_only(tmp_path: Path):
    comparison, request_dir = _fixture(tmp_path)
    request_path = tmp_path / "request.json"
    prepare_reducer_request(comparison, request_dir, request_path, tmp_path / "schema.json")
    request = json.loads(request_path.read_text(encoding="utf-8"))
    request["source_segments"].append({
        "segment_id": "fixture-transcript-0100", "clean_index": 99,
        "text": "Outro resultado de 42% sem relacao.",
    })
    write_json(request_path, request)
    response = _valid_response(request)
    response["candidates"][0]["numbers"].append({"raw": "42%", "role": "result", "value_status": "reported"})
    response_path = tmp_path / "response.json"
    write_json(response_path, response)
    report = reconcile_numeric_evidence(request_path, response_path, tmp_path / "reconciled.json", tmp_path / "reconciliation.json")
    assert report["additions"][-1]["segment_id"] == "fixture-transcript-0002"


def test_compact_judge_packet_uses_valid_reduced_candidates(tmp_path: Path):
    comparison, request_dir = _fixture(tmp_path)
    request_path = tmp_path / "request.json"
    prepare_reducer_request(comparison, request_dir, request_path, tmp_path / "schema.json")
    request = json.loads(request_path.read_text(encoding="utf-8"))
    response_path = tmp_path / "response.json"
    write_json(response_path, _valid_response(request))
    report = validate_reducer_output(request_path, response_path, tmp_path / "reduced.json", tmp_path / "report.json")
    assert report["status"] == "pass"
    packet = build_compact_judge_packet(comparison, tmp_path / "reduced.json", tmp_path / "report.json", tmp_path / "judge.json")
    assert packet["adapter"]["cached_shard_calls_reused"] is True
    assert packet["deterministic_matches"]["fixture-G001"][0]["local_id"] == "R001"
    assert len(packet["independent_atoms"]) == 2
    assert "source_atom_ids" not in packet["independent_atoms"][0]
    assert "numeric_dispositions" not in packet
    assert packet["numeric_inventory_summary"]["total_count"] >= 2
