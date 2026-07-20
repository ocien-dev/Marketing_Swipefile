from __future__ import annotations

import json
from pathlib import Path

from scripts.gold_semantic_adapter_benchmark import (
    _hydrate_atoms,
    _tool_events,
    finalize_report,
    prepare_episode,
    prepare_targeted_gaps,
    invoke_directory,
)
from tests.test_gold_semantic_compiler import _write_dossier


def test_prepare_is_oracle_free(tmp_path: Path):
    dossier = tmp_path / "dossier.jsonl"
    _write_dossier(dossier)
    manifest = prepare_episode(dossier, tmp_path / "episode", target_seconds=120, max_segments=2, overlap_segments=1)
    payload = "\n".join(path.read_text(encoding="utf-8") for path in (tmp_path / "episode" / "blind_requests").glob("*.json"))
    assert manifest["blindness"]["approved_candidate_ids_in_requests"] is False
    assert "fixture-G001" not in payload
    requests = [json.loads(path.read_text(encoding="utf-8")) for path in (tmp_path / "episode" / "blind_requests").glob("*.json")]
    assert manifest["risk_inventory_counts"]["calibration"] == 1
    assert all("risk_inventory" in request for request in requests)
    assert sum(
        len(items)
        for request in requests
        for items in request["risk_inventory"].values()
    ) >= 1


def test_targeted_gap_requests_cover_only_missing_dispositions(tmp_path: Path):
    dossier = tmp_path / "dossier.jsonl"
    _write_dossier(dossier)
    episode = tmp_path / "episode"
    prepare_episode(dossier, episode, target_seconds=120, max_segments=2, overlap_segments=1)
    responses = tmp_path / "responses"
    responses.mkdir()
    for request_path in sorted((episode / "blind_requests").glob("*.json")):
        request = json.loads(request_path.read_text(encoding="utf-8"))
        expected = [
            item["inventory_id"]
            for items in request["risk_inventory"].values()
            for item in items
        ]
        dispositions = [{
            "inventory_id": item, "status": "excluded", "candidate_local_ids": [],
            "reason": "Incidental source-only fixture item.",
        } for item in expected]
        if request_path.name == sorted((episode / "blind_requests").glob("*.json"))[0].name and dispositions:
            dispositions.pop()
        (responses / request_path.name).write_text(
            json.dumps({"shard_id": request["shard"]["shard_id"], "atoms": [], "inventory_dispositions": dispositions}),
            encoding="utf-8",
        )
    result = prepare_targeted_gaps(dossier, episode / "blind_requests", responses, tmp_path / "gaps")
    assert result["unresolved_inventory_count"] == 1
    gap = next(path for path in (tmp_path / "gaps").glob("*.json") if path.name != "gap_manifest.json")
    assert len(json.loads(gap.read_text(encoding="utf-8"))["source_window"]) <= 5


def test_adapter_cache_rejects_response_when_request_inventory_changes(tmp_path: Path, monkeypatch):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    request_path = input_dir / "s1.json"
    request_path.write_text(json.dumps({
        "semantic_sha256": "before", "shard": {"shard_id": "s1"},
    }), encoding="utf-8")
    calls = []

    def fake_call(input_path, output_path, _log_path, **_kwargs):
        request = json.loads(input_path.read_text(encoding="utf-8"))
        output_path.write_text(json.dumps({"shard_id": "s1", "atoms": [], "inventory_dispositions": []}), encoding="utf-8")
        calls.append(request["semantic_sha256"])
        return {
            "input": input_path.name, "output": output_path.name,
            "duration_seconds": 0, "model": "fixture", "reasoning_effort": "low",
            "tool_event_count": 0, "token_usage": {},
            "input_semantic_sha256": request["semantic_sha256"],
        }

    monkeypatch.setattr("scripts.gold_semantic_adapter_benchmark._run_codex_call", fake_call)
    kwargs = {
        "schema_path": tmp_path / "schema.json", "codex_exe": tmp_path / "codex",
        "model": "fixture", "effort": "low", "workers": 1,
        "work_dir": tmp_path / "work", "judge": False,
    }
    invoke_directory(input_dir, tmp_path / "output", **kwargs)
    request_path.write_text(json.dumps({
        "semantic_sha256": "after", "shard": {"shard_id": "s1"},
    }), encoding="utf-8")
    report = invoke_directory(input_dir, tmp_path / "output", **kwargs)
    assert calls == ["before", "after"]
    assert report["calls"][0].get("cache_hit") is None


def test_hydrator_rejects_context_only_or_missing_evidence(tmp_path: Path):
    dossier_path = tmp_path / "dossier.jsonl"
    _write_dossier(dossier_path)
    prepare_episode(dossier_path, tmp_path / "episode", target_seconds=120, max_segments=2, overlap_segments=1)
    requests = sorted((tmp_path / "episode" / "blind_requests").glob("*.json"))
    responses = tmp_path / "responses"
    responses.mkdir()
    for request_path in requests:
        request = json.loads(request_path.read_text(encoding="utf-8"))
        response = {"shard_id": request["shard"]["shard_id"], "atoms": []}
        if request_path == requests[0]:
            context_only = next((item for item in request["source_segments"] if not item["is_core"]), None)
            response["atoms"] = [{
                "local_id": "A001", "title": "T", "source_claim": "C",
                "type": "principle", "themes": [], "subthemes": [],
                "takeaway": "T", "reported_case": False,
                "causal_certainty": "not_applicable", "claim_risk": "low",
                "numbers": [], "steps": [], "conditions": [], "caveats": [],
                "evidence_segment_ids": [context_only["segment_id"] if context_only else "missing"],
                "relation_hints": [],
            }]
        request_path_out = responses / request_path.name
        request_path_out.write_text(json.dumps(response), encoding="utf-8")
    from scripts.gold_semantic_compiler import load_dossier
    atoms, errors = _hydrate_atoms(load_dossier(dossier_path), tmp_path / "episode" / "blind_requests", responses)
    assert atoms == []
    assert any("invalid evidence ownership" in error for error in errors)


def test_tool_event_detection():
    assert _tool_events([{"type": "item.completed", "item": {"type": "command_execution"}}])
    assert _tool_events([{"type": "mcp_tool_call"}])
    assert _tool_events([{"type": "agent_message", "text": "ok"}]) == []


def test_finalize_requires_quality_and_speed(tmp_path: Path):
    episode = tmp_path / "episode"
    (episode / "responses").mkdir(parents=True)
    (episode / "responses" / "invocation_report.json").write_text(json.dumps({"wall_seconds": 100, "input_count": 2}), encoding="utf-8")
    (episode / "comparison_packet.json").write_text(json.dumps({"episode_video_id": "e", "deterministic_preview": {}}), encoding="utf-8")
    (episode / "judge_response.json").write_text(json.dumps({"metrics": {"material_recall": 1, "unsupported_claim_count": 0, "open_finding_count": 0}, "summary": "pass", "findings": []}), encoding="utf-8")
    report = finalize_report([episode], tmp_path / "report.json")
    assert report["adoption_gate"]["production_ready"] is True
    data = json.loads((episode / "judge_response.json").read_text(encoding="utf-8"))
    data["metrics"]["unsupported_claim_count"] = 1
    (episode / "judge_response.json").write_text(json.dumps(data), encoding="utf-8")
    report = finalize_report([episode], tmp_path / "report2.json")
    assert report["adoption_gate"]["production_ready"] is False
