import copy
import json
import sys
from pathlib import Path

import pytest

from scripts import export_gold_audit_packet as audit_packet
from scripts.gold_reaudit_delta import packet_delta
from scripts.gold_review_compiler import compile_payload
from scripts.gold_review_autocheck import autocheck
from scripts.gold_wave_gate import evaluate_wave
from scripts.gold_review_patch import apply_patch
from scripts.finalize_gold_episode import finalize_episode
from scripts.gold_extraction_common import json_hashes, load_json, resolve_data_path, sha256_json, write_json
from scripts.record_gold_external_audit import record_audit
from scripts.record_gold_manual_reviews import main as record_main, record
from scripts.reprocess_gold_episode import chunk_work_order, legacy_chunk_work_order, prepare_episode, work_order_metrics
from scripts.run_gold_wave import detect_route, main as run_main, run_manifest
from scripts.run_gold_episode_fast import inspect_episode_draft, run_episode


def seed(root: Path, video_id: str = "episode") -> str:
    raw = root / "raw" / "youtube" / video_id
    processed = root / "processed" / video_id
    exports = root / "exports"
    raw.mkdir(parents=True)
    processed.mkdir(parents=True)
    exports.mkdir(parents=True, exist_ok=True)
    write_json(raw / "metadata.json", {"youtube_video_id": video_id, "duration_seconds": 20, "transcript_status": "available"})
    write_json(raw / "transcript_original.json", {"youtube_video_id": video_id, "transcript_status": "available", "segments": [
        {"start_seconds": 0, "duration_seconds": 5, "text": "Testamos 20% de desconto antes de escalar."},
        {"start_seconds": 5, "duration_seconds": 5, "text": "Primeiro mede, depois compara o resultado."},
    ]})
    write_json(processed / "insights_v2.json", {"frozen": True})
    write_json(exports / "curated_insights.json", {"frozen": True})
    write_json(exports / "insights_v2_master.json", {"frozen": True})
    prepare_episode(video_id, root)
    return video_id


def candidate(video_id: str, chunk_id: str, candidate_id: str = "G001") -> dict:
    return {
        "candidate_id": f"{video_id}-{candidate_id}", "chunk_id": chunk_id,
        "title": "Testar desconto antes de escalar investimento", "type": "framework",
        "themes": ["testing_measurement"], "subthemes": [], "process_tags": ["process-metricas-analise"],
        "source_claim": "O entrevistado descreve testar desconto e comparar antes de escalar.",
        "takeaway_applicavel": "Teste a variante, compare contra o baseline e escale somente quando o resultado for sustentado.",
        "context": {"episode_video_id": video_id, "source_kind": "transcript"}, "reported_case": True,
        "causal_certainty": "reported_attribution", "claim_risk": "medium", "numbers": [],
        "steps": ["Testar a variante.", "Comparar com o baseline."], "conditions": [], "caveats": [],
        "minimal_segment_ids": [f"{video_id}-transcript-0001"], "support_segment_ids": [f"{video_id}-transcript-0002"],
        "relations": {"parent_candidate_id": None, "child_candidate_ids": []},
    }


def review_payload(root: Path, video_id: str, candidate_data: dict | None = None) -> dict:
    status = load_json(root / "processed" / video_id / "gold_extraction" / "gold_extraction_status.json")
    chunk = status["chunks"][0]
    item = candidate_data or candidate(video_id, chunk["chunk_id"])
    return {"episode_video_id": video_id, "reviews": [{"chunk_number": 1, "candidates": [item], "ledger_decisions": []}]}


def structured_number() -> dict:
    return {"raw": "20%", "value": 20, "min_value": None, "max_value": None, "unit_kind": "percent", "unit": "percent", "period": None, "role": "result", "value_status": "reported", "denominator": None, "attribution_window": None}


def finalizable_candidate(root: Path, video_id: str) -> dict:
    chunk_id = load_json(root / "processed" / video_id / "gold_extraction" / "gold_extraction_status.json")["chunks"][0]["chunk_id"]
    item = candidate(video_id, chunk_id)
    item["numbers"] = [structured_number()]
    item["caveats"] = ["Caso reportado; o resultado pode variar conforme o contexto."]
    return item


def add_second_chunk(root: Path, video_id: str) -> None:
    status_path = root / "processed" / video_id / "gold_extraction" / "gold_extraction_status.json"
    status = load_json(status_path)
    first = copy.deepcopy(status["chunks"][0])
    first.update({"chunk_id": f"{video_id}-gold-chunk-002", "chunk_number": 2, "status": "pending", "review_hash": None, "candidate_count": 0})
    status["chunks"].append(first)
    write_json(status_path, status)


def file_snapshot(directory: Path) -> dict[Path, tuple[int, bytes]]:
    return {path: (path.stat().st_mtime_ns, path.read_bytes()) for path in directory.rglob("*") if path.is_file()}


def test_resolve_data_path_rebases_windows_provenance_to_wsl_root(tmp_path: Path):
    target = tmp_path / "processed" / "episode" / "gold_extraction" / "chunks" / "chunk_001.json"
    target.parent.mkdir(parents=True)
    target.write_text("{}\n", encoding="utf-8")
    historical = r"C:\MSF-data\Marketing_Swipe_File\processed\episode\gold_extraction\chunks\chunk_001.json"
    assert resolve_data_path(historical, tmp_path) == target.resolve()


def test_resolve_data_path_rejects_unknown_external_path(tmp_path: Path):
    with pytest.raises(ValueError, match="known anchor"):
        resolve_data_path(r"D:\unrelated\chunk_001.json", tmp_path)


def test_compact_work_order_preserves_references_and_reduces_wave_style_bytes():
    text = "Testamos 20% de desconto e depois medimos a conversao. " * 80
    segments = [{"segment_id": "wave-transcript-0000", "clean_index": 0, "start_seconds": 0, "duration_seconds": 5, "text": text}]
    chunk = {"chunk_id": "wave-gold-chunk-001", "chunk_number": 1, "segments": segments}
    signals = [{"segment_id": segments[0]["segment_id"], "clean_index": 0, "signal_types": ["number", "experiment"], "evidence": [{"quote_verbatim": text}]}]
    calibrations = [{"calibration_id": "wave-cal-1", "segment_ids": [segments[0]["segment_id"]], "quote": text}]
    compact = chunk_work_order("wave", chunk, signals, calibrations)
    legacy = legacy_chunk_work_order("wave", chunk, signals, calibrations)
    compact_bytes = len(json.dumps(compact, ensure_ascii=False).encode("utf-8"))
    legacy_bytes = len(json.dumps(legacy, ensure_ascii=False).encode("utf-8"))
    assert compact["segment_refs"][0]["segment_id"] == segments[0]["segment_id"]
    assert compact["signal_segment_ids"] == [segments[0]["segment_id"]]
    assert compact["calibration_target_ids"] == ["wave-cal-1"]
    assert compact_bytes <= legacy_bytes * 0.75
    assert work_order_metrics("wave", [chunk], signals, calibrations)["reduction_percent"] >= 25


def test_episode_fast_check_blocks_before_any_episode_or_export_write(tmp_path):
    video_id = seed(tmp_path)
    payload = review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id))
    payload["reviews"][0]["candidates"][0]["numbers"] = []
    out = tmp_path / "processed" / video_id / "gold_extraction"
    exports = tmp_path / "exports"
    before_out = file_snapshot(out)
    before_exports = file_snapshot(exports)

    result = inspect_episode_draft(video_id, tmp_path, payload)

    assert result["status"] == "blocked"
    assert result["stopped_at"] == "autocheck"
    assert any(item["category"] == "numbers" for item in result["hard_blockers"])
    assert file_snapshot(out) == before_out
    assert file_snapshot(exports) == before_exports


def test_episode_fast_applies_one_review_transaction_and_one_finalization(tmp_path):
    video_id = seed(tmp_path)
    payload = review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id))

    result = run_episode(
        video_id,
        tmp_path,
        payload,
        apply=True,
        revision_id="fast-episode-001",
        export_suffix="fast-episode-packet",
    )

    assert result["status"] == "ready"
    assert result["persist"]["written_reviews"] == 1
    assert result["metrics"]["review_write_operations"] == 1
    assert result["metrics"]["finalizer_calls"] == 1
    assert result["metrics"]["compile_ms"] >= 0
    assert result["metrics"]["autocheck_ms"] >= 0
    assert result["metrics"]["persist_ms"] >= 0
    assert result["metrics"]["finalize_ms"] >= 0
    assert result["metrics"]["total_ms"] < 60_000
    receipt = load_json(tmp_path / "processed" / video_id / "gold_extraction" / "manual_review_batch_receipts.json")
    assert len(receipt["batches"]) == 1
    operation_receipt = load_json(tmp_path / "processed" / video_id / "gold_extraction" / "fastpath_operation_receipt.json")
    assert sum(event["operation"] == "episode_one_shot" for event in operation_receipt["events"]) == 1
    assert {path.name for path in (tmp_path / "exports" / "fast-episode-packet").iterdir()} == {
        "packet_manifest.json",
        "transcript_clean.json",
        "insights_exhaustive.json",
        "high_signal_coverage_ledger.json",
        "calibration_tests.json",
    }


def test_episode_fast_reapply_recovers_receipts_without_rewriting(tmp_path):
    video_id = seed(tmp_path)
    payload = review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id))
    first = run_episode(
        video_id,
        tmp_path,
        payload,
        apply=True,
        revision_id="fast-episode-001",
        export_suffix="fast-episode-packet",
    )
    assert first["status"] == "ready"
    tracked = tmp_path / "processed" / video_id / "gold_extraction"
    before_gold = file_snapshot(tracked)
    before_packet = file_snapshot(tmp_path / "exports" / "fast-episode-packet")

    repeated = run_episode(
        video_id,
        tmp_path,
        payload,
        apply=True,
        revision_id="fast-episode-001",
        export_suffix="fast-episode-packet",
    )

    assert repeated["status"] == "ready"
    assert repeated["persist"]["idempotent"] is True
    assert repeated["finalization"]["idempotent"] is True
    assert repeated["metrics"]["review_write_operations"] == 0
    assert file_snapshot(tracked) == before_gold
    assert file_snapshot(tmp_path / "exports" / "fast-episode-packet") == before_packet


def test_episode_fast_requires_every_prepared_chunk_before_apply(tmp_path):
    video_id = seed(tmp_path)
    add_second_chunk(tmp_path, video_id)
    payload = review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id))
    out = tmp_path / "processed" / video_id / "gold_extraction"
    before = file_snapshot(out)

    result = run_episode(video_id, tmp_path, payload, apply=True)

    assert result["status"] == "blocked"
    assert any(item["category"] == "missing_reviews" for item in result["hard_blockers"])
    assert file_snapshot(out) == before


def test_recorder_validates_all_reviews_before_persisting(tmp_path):
    video_id = seed(tmp_path)
    payload = review_payload(tmp_path, video_id)
    invalid = copy.deepcopy(payload["reviews"][0])
    invalid["chunk_number"] = 99
    payload["reviews"].append(invalid)
    review_dir = tmp_path / "processed" / video_id / "gold_extraction" / "manual_reviews"
    with pytest.raises(ValueError, match="unknown chunk_number"):
        record(video_id, tmp_path, payload)
    assert not list(review_dir.glob("*.json"))


def test_json_batch_rolls_back_when_a_later_replace_fails(tmp_path, monkeypatch):
    from scripts import gold_extraction_common as common

    first, second = tmp_path / "first.json", tmp_path / "second.json"
    write_json(first, {"value": "before-first"})
    write_json(second, {"value": "before-second"})
    original = {first: first.read_bytes(), second: second.read_bytes()}
    real_replace = common.os.replace
    calls = 0

    def fail_second(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated replace failure")
        return real_replace(source, destination)

    monkeypatch.setattr(common.os, "replace", fail_second)
    with pytest.raises(OSError, match="simulated"):
        common.write_json_batch({first: {"value": "after-first"}, second: {"value": "after-second"}})
    assert first.read_bytes() == original[first]
    assert second.read_bytes() == original[second]


def test_transactional_patch_inserts_before_forward_relation_and_prevents_reapply(tmp_path):
    video_id = seed(tmp_path)
    record(video_id, tmp_path, review_payload(tmp_path, video_id))
    out = tmp_path / "processed" / video_id / "gold_extraction"
    status = load_json(out / "gold_extraction_status.json")
    chunk = status["chunks"][0]
    existing = load_json(out / "manual_reviews" / "chunk_001_review.json")["candidates"][0]
    inserted = copy.deepcopy(existing)
    inserted["candidate_id"] = f"{video_id}-G002"
    manifest = {
        "episode_video_id": video_id,
        "review_assertions": [{"chunk_number": 1, "chunk_id": chunk["chunk_id"], "input_hash": chunk["input_hash"], "candidate_ids": [f"{video_id}-G001"]}],
        "inserts": [{"chunk_number": 1, "candidate": inserted}],
        "relations": [{"candidate_id": f"{video_id}-G001", "parent_candidate_id": None, "child_candidate_ids": [f"{video_id}-G002"]}],
    }
    review_path = out / "manual_reviews" / "chunk_001_review.json"
    before = review_path.read_bytes()
    checked = apply_patch(video_id, tmp_path, manifest, apply=False)
    assert checked["mode"] == "check"
    assert review_path.read_bytes() == before
    applied = apply_patch(video_id, tmp_path, manifest, apply=True)
    assert applied["mode"] == "apply"
    review = load_json(review_path)
    by_id = {item["candidate_id"]: item for item in review["candidates"]}
    assert by_id[f"{video_id}-G002"]["relations"]["parent_candidate_id"] == f"{video_id}-G001"
    assert apply_patch(video_id, tmp_path, manifest, apply=True)["mode"] == "already_applied"


def test_recorder_composes_cross_chunk_relations_and_rejects_global_duplicate(tmp_path):
    video_id = seed(tmp_path)
    add_second_chunk(tmp_path, video_id)
    record(video_id, tmp_path, review_payload(tmp_path, video_id))
    status = load_json(tmp_path / "processed" / video_id / "gold_extraction" / "gold_extraction_status.json")
    child = candidate(video_id, status["chunks"][1]["chunk_id"], "G002")
    child["relations"] = {"parent_candidate_id": f"{video_id}-G001", "child_candidate_ids": []}
    second = {"episode_video_id": video_id, "reviews": [{"chunk_number": 2, "candidates": [child], "ledger_decisions": []}]}
    result = record(video_id, tmp_path, second)
    assert result["normalized_existing_reviews"] == 1
    parent_review = load_json(tmp_path / "processed" / video_id / "gold_extraction" / "manual_reviews" / "chunk_001_review.json")
    child_review = load_json(tmp_path / "processed" / video_id / "gold_extraction" / "manual_reviews" / "chunk_002_review.json")
    assert parent_review["candidates"][0]["relations"]["child_candidate_ids"] == [f"{video_id}-G002"]
    assert child_review["candidates"][0]["relations"]["parent_candidate_id"] == f"{video_id}-G001"
    duplicate = copy.deepcopy(child); duplicate["candidate_id"] = f"{video_id}-G001"
    with pytest.raises(ValueError, match="duplicate candidate_id across"):
        record(video_id, tmp_path, {"episode_video_id": video_id, "reviews": [{"chunk_number": 2, "candidates": [duplicate], "ledger_decisions": []}]})


def test_patch_removes_candidate_and_replaces_ledger_transactionally(tmp_path):
    video_id = seed(tmp_path)
    record(video_id, tmp_path, review_payload(tmp_path, video_id))
    out = tmp_path / "processed" / video_id / "gold_extraction"
    status = load_json(out / "gold_extraction_status.json"); chunk = status["chunks"][0]
    review_path = out / "manual_reviews" / "chunk_001_review.json"
    before = review_path.read_bytes()
    manifest = {
        "episode_video_id": video_id,
        "review_assertions": [{"chunk_number": 1, "input_hash": chunk["input_hash"], "candidate_ids": [f"{video_id}-G001"]}],
        "removals": [{"candidate_id": f"{video_id}-G001", "assert": {"title": "Testar desconto antes de escalar investimento"}}],
        "ledger_updates": [{"chunk_number": 1, "assert": [], "set": [{"segment_id": f"{video_id}-transcript-0001", "disposition": "excluded", "reason_code": "promo"}]}],
    }
    assert apply_patch(video_id, tmp_path, manifest, apply=False)["mode"] == "check"
    assert review_path.read_bytes() == before
    assert apply_patch(video_id, tmp_path, manifest, apply=True)["mode"] == "apply"
    review = load_json(review_path)
    assert review["candidates"] == []
    assert review["ledger_decisions"][0]["reason_code"] == "promo"
    assert apply_patch(video_id, tmp_path, manifest, apply=True)["mode"] == "already_applied"


def test_patch_rejects_removal_without_real_precondition_without_writes(tmp_path):
    video_id = seed(tmp_path)
    record(video_id, tmp_path, review_payload(tmp_path, video_id))
    out = tmp_path / "processed" / video_id / "gold_extraction"
    before = file_snapshot(out)
    manifest = {"episode_video_id": video_id, "removals": [{"candidate_id": f"{video_id}-G001"}]}
    with pytest.raises(ValueError, match="removal needs"):
        apply_patch(video_id, tmp_path, manifest, apply=False)
    assert file_snapshot(out) == before


def test_patch_rejects_ledger_update_without_assert_without_writes(tmp_path):
    video_id = seed(tmp_path)
    record(video_id, tmp_path, review_payload(tmp_path, video_id))
    out = tmp_path / "processed" / video_id / "gold_extraction"
    before = file_snapshot(out)
    manifest = {"episode_video_id": video_id, "ledger_updates": [{"chunk_number": 1, "set": []}]}
    with pytest.raises(ValueError, match="needs assert"):
        apply_patch(video_id, tmp_path, manifest, apply=False)
    assert file_snapshot(out) == before


@pytest.mark.parametrize(
    ("ledger", "expected", "remove_candidate"),
    [
        ([{"segment_id": "episode-transcript-0001", "disposition": "captured", "candidate_ids": ["episode-G001"]}], "missing candidate_ids", True),
        ([{"segment_id": "episode-transcript-0001", "disposition": "merged", "candidate_ids": ["episode-G999"]}], "missing candidate_ids", False),
        ([{"segment_id": "episode-transcript-9999", "disposition": "captured", "candidate_ids": ["episode-G001"]}], "segment_id is missing or unknown", False),
        ([
            {"segment_id": "episode-transcript-0001", "disposition": "captured", "candidate_ids": ["episode-G001"]},
            {"segment_id": "episode-transcript-0001", "disposition": "merged", "candidate_ids": ["episode-G001"]},
        ], "duplicate ledger decision", False),
    ],
)
def test_patch_rejects_invalid_final_ledger_without_writes(tmp_path, ledger, expected, remove_candidate):
    video_id = seed(tmp_path)
    record(video_id, tmp_path, review_payload(tmp_path, video_id))
    out = tmp_path / "processed" / video_id / "gold_extraction"
    before = file_snapshot(out)
    manifest = {
        "episode_video_id": video_id,
        "review_assertions": [{"chunk_number": 1, "chunk_id": load_json(out / "gold_extraction_status.json")["chunks"][0]["chunk_id"], "input_hash": load_json(out / "gold_extraction_status.json")["chunks"][0]["input_hash"], "candidate_ids": [f"{video_id}-G001"]}],
        "removals": [{"candidate_id": f"{video_id}-G001", "assert": {"title": "Testar desconto antes de escalar investimento"}}] if remove_candidate else [],
        "ledger_updates": [{"chunk_number": 1, "assert": [], "set": ledger}],
    }
    with pytest.raises(ValueError, match=expected):
        apply_patch(video_id, tmp_path, manifest, apply=False)
    assert file_snapshot(out) == before


def test_autocheck_is_read_only_and_reports_numeric_gap(tmp_path):
    video_id = seed(tmp_path)
    record(video_id, tmp_path, review_payload(tmp_path, video_id))
    out = tmp_path / "processed" / video_id / "gold_extraction"
    before = {path: path.read_bytes() for path in out.rglob("*") if path.is_file()}
    report = autocheck(video_id, tmp_path)
    repeated = autocheck(video_id, tmp_path)
    after = {path: path.read_bytes() for path in out.rglob("*") if path.is_file()}
    assert before == after
    assert report == repeated
    assert any(item["candidate_id"] == f"{video_id}-G001" for item in report["numbers"])
    assert "chunk_boundaries_to_review" in report


def test_autocheck_flags_interviewer_restate_and_material_word_numbers(tmp_path):
    video_id = seed(tmp_path)
    record(video_id, tmp_path, review_payload(tmp_path, video_id))
    path = tmp_path / "processed" / video_id / "gold_extraction" / "manual_reviews" / "chunk_001_review.json"
    review = load_json(path)
    review["candidates"][0]["numbers"] = []
    review["candidates"][0]["evidence"]["minimal_quote"][0]["quote_verbatim"] = "Do you think three percent or five percent works? Voce disse tres dias, certo?"
    write_json(path, review)
    report = autocheck(video_id, tmp_path)
    assert f"{video_id}-G001" in report["candidate_with_promo_or_interviewer_language"]
    assert any(item["candidate_id"] == f"{video_id}-G001" for item in report["numbers"])


def test_runner_auto_routes_new_resumable_and_protected_without_writing_protected(tmp_path):
    new_id = "new"
    raw = tmp_path / "raw" / "youtube" / new_id
    raw.mkdir(parents=True)
    write_json(raw / "metadata.json", {"youtube_video_id": new_id, "duration_seconds": 10, "transcript_status": "available"})
    write_json(raw / "transcript_original.json", {"youtube_video_id": new_id, "transcript_status": "available", "segments": [{"start_seconds": 0, "duration_seconds": 5, "text": "Teste 20%."}]})
    (tmp_path / "processed" / new_id).mkdir(parents=True)
    (tmp_path / "exports").mkdir(exist_ok=True)
    write_json(tmp_path / "processed" / new_id / "insights_v2.json", {})
    write_json(tmp_path / "exports" / "curated_insights.json", {})
    write_json(tmp_path / "exports" / "insights_v2_master.json", {})
    assert detect_route(new_id, tmp_path)["mode"] == "new_raw_episode"
    result = run_manifest({"episodes": [{"video_id": new_id, "mode": "auto"}]}, tmp_path, execute=True)
    assert result["episodes"][0]["next_gate"] == "semantic_review"

    resumable = seed(tmp_path, "resumable")
    assert detect_route(resumable, tmp_path)["mode"] == "resumable_incomplete_gold"
    resumable_status_path = tmp_path / "processed" / resumable / "gold_extraction" / "gold_extraction_status.json"
    resumable_status = load_json(resumable_status_path); resumable_status["chunks"][0]["status"] = "completed"; write_json(resumable_status_path, resumable_status)
    assert detect_route(resumable, tmp_path)["next_gate"] == "blocked_inconsistent_checkpoint"
    protected = seed(tmp_path, "protected")
    status_path = tmp_path / "processed" / protected / "gold_extraction" / "gold_extraction_status.json"
    status = load_json(status_path); status.update({"status": "complete", "audit_status": "passed"}); write_json(status_path, status)
    before = status_path.read_bytes()
    result = run_manifest({"episodes": [{"video_id": protected, "mode": "auto"}]}, tmp_path, execute=True)
    assert result["episodes"][0]["status"] == "protected"
    assert status_path.read_bytes() == before


def test_runner_blocks_partial_gold_without_status_and_runs_complete_resumable(tmp_path):
    partial = "partial"
    partial_dir = tmp_path / "processed" / partial / "gold_extraction"; partial_dir.mkdir(parents=True)
    sentinel = partial_dir / "sentinel.txt"; sentinel.write_text("keep", encoding="utf-8")
    route = detect_route(partial, tmp_path)
    assert route["next_gate"] == "blocked_inconsistent_checkpoint"
    result = run_manifest({"episodes": [{"video_id": partial, "mode": "auto"}]}, tmp_path, execute=True)
    assert result["episodes"][0]["status"] == "blocked"
    assert sentinel.read_text(encoding="utf-8") == "keep"

    video_id = seed(tmp_path, "ready")
    item = finalizable_candidate(tmp_path, video_id)
    record(video_id, tmp_path, review_payload(tmp_path, video_id, item))
    result = run_manifest({"episodes": [{"video_id": video_id, "mode": "auto", "export_suffix": "ready-packet"}]}, tmp_path, execute=True)
    execution = result["episodes"][0]["execution"]
    assert execution["status"] == "ready"
    assert execution["validation"]["status"] == "pass"
    assert (tmp_path / "exports" / "ready-packet" / "packet_manifest.json").exists()


def test_reaudit_delta_is_read_only(tmp_path):
    before = tmp_path / "before"; after = tmp_path / "after"; before.mkdir(); after.mkdir()
    base = {"insights": [{"candidate_id": "G001", "title": "One", "type": "tactic", "themes": ["copywriting"], "subthemes": [], "process_tags": [], "context": {}, "reported_case": False, "causal_certainty": "uncertain", "claim_risk": "low", "numbers": [], "relations": {}, "evidence": {}, "steps": [], "conditions": [], "caveats": [], "source_claim": "a", "takeaway_applicavel": "b"}]}
    changed = copy.deepcopy(base); changed["insights"][0].update({"type": "framework", "themes": ["copy_vsl"], "context": {"changed": True}, "numbers": [{"raw": "20"}]})
    for directory, insights in ((before, base), (after, changed)):
        write_json(directory / "packet_manifest.json", {"packet": directory.name, "version": 1 if directory == before else 2})
        write_json(directory / "transcript_clean.json", {"segments": [{"segment_id": "s1", "text": "before" if directory == before else "after"}]})
        write_json(directory / "insights_exhaustive.json", insights)
        write_json(directory / "high_signal_coverage_ledger.json", {"entries": [{"segment_id": "s1", "segment_range": [0, 0] if directory == before else [0, 1], "signal_types": ["number"] if directory == before else ["number", "comparison"], "disposition": "captured", "candidate_ids": ["G001"]}]})
        write_json(directory / "calibration_tests.json", {"status": "pass"})
    before_bytes = {path: path.read_bytes() for path in before.rglob("*.json")} | {path: path.read_bytes() for path in after.rglob("*.json")}
    delta = packet_delta(before, after)
    after_bytes = {path: path.read_bytes() for path in before.rglob("*.json")} | {path: path.read_bytes() for path in after.rglob("*.json")}
    assert before_bytes == after_bytes
    assert {"numbers", "type", "themes", "context"} <= set(delta["candidates"]["changed"][0]["changed_fields"])
    assert {"segment_range", "signal_types"} <= set(delta["ledger"]["changed"][0]["changed_fields"])
    assert delta["transcript"]["content_changed"] is True
    assert delta["packet_manifest"]["changed"] is True
    duplicate = copy.deepcopy(base); duplicate["insights"].append(copy.deepcopy(base["insights"][0]))
    write_json(after / "insights_exhaustive.json", duplicate)
    with pytest.raises(ValueError, match="duplicate candidate_id"):
        packet_delta(before, after)


def test_patch_redirects_calibration_atomically_and_allows_distinct_revisions(tmp_path):
    video_id = seed(tmp_path)
    record(video_id, tmp_path, review_payload(tmp_path, video_id))
    out = tmp_path / "processed" / video_id / "gold_extraction"
    calibration_path = out / "calibration_tests.json"
    write_json(calibration_path, {"episode_video_id": video_id, "tests": [{"calibration_id": "cal-1", "segment_ids": [f"{video_id}-transcript-0001"], "semantic_candidate_ids": []}]})
    review_path = out / "manual_reviews" / "chunk_001_review.json"
    before = file_snapshot(out)
    redirect = {
        "episode_video_id": video_id,
        "patch_window": "post_packet",
        "calibration_redirects": [{"calibration_id": "cal-1", "assert": {"segment_ids": [f"{video_id}-transcript-0001"]}, "set": {"semantic_candidate_ids": [f"{video_id}-G001"]}}],
    }
    assert apply_patch(video_id, tmp_path, redirect, apply=False)["mode"] == "check"
    assert file_snapshot(out) == before
    assert apply_patch(video_id, tmp_path, redirect, apply=True)["mode"] == "apply"
    assert load_json(calibration_path)["tests"][0]["semantic_candidate_ids"] == [f"{video_id}-G001"]
    assert load_json(out / "fastpath_patch_history.json")["applied"][0]["legacy_patch_window"] == "post_packet"

    for index, value in enumerate(("Primeiro titulo protegido", "Segundo titulo protegido", "Terceiro titulo protegido"), start=1):
        current = load_json(review_path)["candidates"][0]["title"]
        manifest = {
            "episode_video_id": video_id,
            "revision_id": f"revision-{index}",
            "revision_kind": "editorial_remediation",
            "reason": "Fixture verifies revision history without an artificial cap.",
            "updates": [{"candidate_id": f"{video_id}-G001", "assert": {"title": current}, "set": {"title": value}}],
        }
        assert apply_patch(video_id, tmp_path, manifest, apply=True)["mode"] == "apply"
        assert apply_patch(video_id, tmp_path, manifest, apply=True)["mode"] == "already_applied"
    history = load_json(out / "fastpath_patch_history.json")
    assert [entry["revision_id"] for entry in history["applied"][-3:]] == ["revision-1", "revision-2", "revision-3"]


@pytest.mark.parametrize(
    ("replacement", "message"),
    [
        ({"semantic_candidate_ids": ["episode-G999"]}, "missing semantic_candidate_ids"),
        ({"segment_ids": ["episode-transcript-9999"]}, "missing segment_ids"),
        ({"segment_ids": ["episode-transcript-0002"]}, "duplicate target segments"),
    ],
)
def test_calibration_redirect_rejects_invalid_final_state_without_writes(tmp_path, replacement, message):
    video_id = seed(tmp_path)
    record(video_id, tmp_path, review_payload(tmp_path, video_id))
    out = tmp_path / "processed" / video_id / "gold_extraction"
    calibration_path = out / "calibration_tests.json"
    write_json(calibration_path, {"episode_video_id": video_id, "tests": [
        {"calibration_id": "cal-1", "segment_ids": [f"{video_id}-transcript-0001"], "semantic_candidate_ids": []},
        {"calibration_id": "cal-2", "segment_ids": [f"{video_id}-transcript-0002"], "semantic_candidate_ids": []},
    ]})
    before = file_snapshot(out)
    manifest = {"episode_video_id": video_id, "patch_window": "post_packet", "calibration_redirects": [{"calibration_id": "cal-1", "assert": {"segment_ids": [f"{video_id}-transcript-0001"]}, "set": replacement}]}
    with pytest.raises(ValueError, match=message):
        apply_patch(video_id, tmp_path, manifest, apply=False)
    assert file_snapshot(out) == before


def test_runner_budget_blocks_before_preparation_and_emits_chunk_ranges(tmp_path):
    video_id = "over-budget"
    raw = tmp_path / "raw" / "youtube" / video_id
    raw.mkdir(parents=True)
    segments = [{"start_seconds": index, "duration_seconds": 1, "text": "Teste 20%."} for index in range(20)]
    write_json(raw / "metadata.json", {"youtube_video_id": video_id, "duration_seconds": 30, "transcript_status": "available"})
    write_json(raw / "transcript_original.json", {"youtube_video_id": video_id, "transcript_status": "available", "segments": segments})
    (tmp_path / "processed" / video_id).mkdir(parents=True)
    (tmp_path / "exports").mkdir(exist_ok=True)
    for name in ("insights_v2.json",):
        write_json(tmp_path / "processed" / video_id / name, {})
    for name in ("curated_insights.json", "insights_v2_master.json"):
        write_json(tmp_path / "exports" / name, {})
    result = run_manifest({"active_budget": {"max_raw_segments": 10}, "review_range_size": 8, "episodes": [{"video_id": video_id, "mode": "auto"}]}, tmp_path, execute=True)
    item = result["episodes"][0]
    assert item["next_gate"] == "blocked_active_budget"
    assert not (tmp_path / "processed" / video_id / "gold_extraction").exists()
    assert result["metrics"]["active_raw_segments"] == 20
    assert item["review_plan"]["range_size"] == 8


def test_audit_check_and_json_hashes_are_read_only_and_newline_semantic(tmp_path):
    video_id = seed(tmp_path)
    out = tmp_path / "processed" / video_id / "gold_extraction"
    audit = {
        "episode_video_id": video_id, "audit_route": "external_blind_reviewer", "reviewer": "Reviewer",
        "reviewer_thread_id": "reviewer", "reviewer_model": "gpt-test", "reasoning_effort": "high",
        "reviewed_at": "2026-07-13T00:00:00Z", "status": "changes_requested", "summary": "Review.", "open_findings": 1,
        "findings": [{"finding_id": "F1", "severity": "minor", "status": "open", "category": "editorial", "segment_range": [0, 1], "candidate_ids": [f"{video_id}-G001"], "summary": "Gap.", "evidence": "Evidence.", "required_action": "Fix."}],
    }
    assert record_audit(video_id, tmp_path, audit, persist=False)["open_findings"] == 1
    assert not (out / "editorial_audit_report.json").exists()
    lf = tmp_path / "lf.json"; crlf = tmp_path / "crlf.json"
    lf.write_bytes(b'{\n  "value": 1\n}\n')
    crlf.write_bytes(b'{\r\n  "value": 1\r\n}\r\n')
    assert json_hashes(lf)["semantic_sha256"] == json_hashes(crlf)["semantic_sha256"]
    assert json_hashes(lf)["physical_sha256"] != json_hashes(crlf)["physical_sha256"]


def test_autocheck_reports_claim_ledger_caveat_relation_and_interviewer_risks(tmp_path):
    video_id = seed(tmp_path)
    item = candidate(video_id, load_json(tmp_path / "processed" / video_id / "gold_extraction" / "gold_extraction_status.json")["chunks"][0]["chunk_id"])
    item["numbers"] = [structured_number()]
    record(video_id, tmp_path, review_payload(tmp_path, video_id, item))
    path = tmp_path / "processed" / video_id / "gold_extraction" / "manual_reviews" / "chunk_001_review.json"
    review = load_json(path)
    edited = review["candidates"][0]
    edited["source_claim"] = "Uma proposicao distante sem termo compartilhado."
    edited["caveats"] = []
    edited["relations"] = {"parent_candidate_id": f"{video_id}-missing", "child_candidate_ids": []}
    edited["evidence"]["minimal_quote"][0]["quote_verbatim"] = "Do you think three percent works?"
    review["ledger_decisions"] = [{"segment_id": f"{video_id}-transcript-0002", "disposition": "captured", "candidate_ids": [f"{video_id}-G001"]}]
    write_json(path, review)
    write_json(tmp_path / "processed" / video_id / "gold_extraction" / "calibration_tests.json", {
        "episode_video_id": video_id,
        "tests": [{"calibration_id": "semantic-gap", "segment_ids": [f"{video_id}-transcript-0001"], "quote_verbatim": "Distinct runway calculation.", "semantic_candidate_ids": [f"{video_id}-G001"]}],
    })
    report = autocheck(video_id, tmp_path)
    assert report["claim_evidence_alignment"]
    assert report["reported_case_without_caveat"] == [f"{video_id}-G001"]
    assert report["relation_integrity"]
    assert report["candidate_supported_only_by_interviewer_or_promo"] == []
    assert not report["ledger_semantic_alignment"]
    assert report["calibration_semantic_alignment"]


def test_active_load_uses_pending_and_stale_chunk_segments_not_full_raw(tmp_path):
    video_id = seed(tmp_path, "large")
    raw_path = tmp_path / "raw" / "youtube" / video_id / "transcript_original.json"
    raw = load_json(raw_path)
    raw["segments"] *= 200
    write_json(raw_path, raw)
    result = run_manifest({"active_budget": {"max_raw_segments": 3, "max_chunks": 1}, "episodes": [{"video_id": video_id, "mode": "auto"}]}, tmp_path)
    route = result["episodes"][0]
    assert result["metrics"]["active_raw_segments"] == 2
    assert route["review_plan"]["ranges"] == [[f"{video_id}-gold-chunk-001"]]
    record(video_id, tmp_path, review_payload(tmp_path, video_id))
    review_path = tmp_path / "processed" / video_id / "gold_extraction" / "manual_reviews" / "chunk_001_review.json"
    status_path = tmp_path / "processed" / video_id / "gold_extraction" / "gold_extraction_status.json"
    status = load_json(status_path); review = load_json(review_path)
    status["chunks"][0].update({"status": "completed", "review_hash": sha256_json(review)})
    write_json(status_path, status)
    review["review_route"] = "changed"; write_json(review_path, review)
    stale = run_manifest({"episodes": [{"video_id": video_id, "mode": "auto"}]}, tmp_path)["episodes"][0]
    assert stale["stale_chunks"] == [f"{video_id}-gold-chunk-001"]
    assert stale["active_load"]["active_chunks"] == 1
    assert stale["review_plan"]["ranges"] == [[f"{video_id}-gold-chunk-001"]]


def test_warning_only_autocheck_does_not_block_finalization_and_metrics_are_receipt_based(tmp_path):
    video_id = seed(tmp_path)
    item = finalizable_candidate(tmp_path, video_id)
    item["caveats"] = []
    record(video_id, tmp_path, review_payload(tmp_path, video_id, item))
    report = autocheck(video_id, tmp_path)
    assert report["review_required"]
    result = run_manifest({"episodes": [{"video_id": video_id, "mode": "auto"}]}, tmp_path, execute=True)
    assert result["episodes"][0]["execution"]["status"] == "ready"
    metrics = result["episodes"][0]["metrics"]["operation_metrics"]
    assert metrics["status"] == "measured" and metrics["review_batch"] == 1


def test_autocheck_uses_persisted_evidence_ids_for_ledger_and_keeps_uncovered_signal(tmp_path):
    video_id = seed(tmp_path)
    item = candidate(video_id, load_json(tmp_path / "processed" / video_id / "gold_extraction" / "gold_extraction_status.json")["chunks"][0]["chunk_id"])
    item["numbers"] = [structured_number()]
    record(video_id, tmp_path, review_payload(tmp_path, video_id, item))
    path = tmp_path / "processed" / video_id / "gold_extraction" / "manual_reviews" / "chunk_001_review.json"
    review = load_json(path)
    persisted = review["candidates"][0]
    persisted.pop("minimal_segment_ids", None); persisted.pop("support_segment_ids", None)
    review["ledger_decisions"] = [
        {"segment_id": f"{video_id}-transcript-0001", "disposition": "captured", "candidate_ids": [f"{video_id}-G001"]},
        {"segment_id": f"{video_id}-transcript-0002", "disposition": "excluded", "reason_code": "low_signal", "candidate_ids": []},
    ]
    write_json(path, review)
    report = autocheck(video_id, tmp_path)
    assert not report["automatic_ledger_preview"]
    assert not report["ledger_semantic_alignment"]
    review["ledger_decisions"] = []
    persisted["evidence"] = {"minimal_quote": [], "support_segments": []}
    write_json(path, review)
    uncovered = autocheck(video_id, tmp_path)
    assert not uncovered["automatic_ledger_preview"]


@pytest.mark.parametrize(
    ("decision", "preview_empty"),
    [
        ({"disposition": "excluded", "reason_code": "low_signal", "candidate_ids": []}, True),
        ({"disposition": "excluded", "reason_code": "not_valid", "candidate_ids": []}, False),
        ({"disposition": "captured", "candidate_ids": ["episode-G001"]}, False),
    ],
)
def test_automatic_ledger_preview_reconciles_final_decisions(tmp_path, decision, preview_empty):
    video_id = seed(tmp_path)
    item = candidate(video_id, load_json(tmp_path / "processed" / video_id / "gold_extraction" / "gold_extraction_status.json")["chunks"][0]["chunk_id"])
    item["numbers"] = [structured_number()]
    record(video_id, tmp_path, review_payload(tmp_path, video_id, item))
    path = tmp_path / "processed" / video_id / "gold_extraction" / "manual_reviews" / "chunk_001_review.json"
    review = load_json(path)
    review["candidates"][0]["evidence"] = {"minimal_quote": [], "support_segments": []}
    review["ledger_decisions"] = [{"segment_id": f"{video_id}-transcript-0001", **decision}]
    write_json(path, review)
    report = autocheck(video_id, tmp_path)
    target = [item for item in report["automatic_ledger_preview"] if item["segment_id"] == f"{video_id}-transcript-0001"]
    assert not target if preview_empty else target


def test_autocheck_derives_builder_ledger_before_a_final_ledger_exists(tmp_path):
    video_id = seed(tmp_path)
    item = candidate(video_id, load_json(tmp_path / "processed" / video_id / "gold_extraction" / "gold_extraction_status.json")["chunks"][0]["chunk_id"])
    item["numbers"] = [structured_number()]
    record(video_id, tmp_path, review_payload(tmp_path, video_id, item))

    report = autocheck(video_id, tmp_path)

    assert not report["automatic_ledger_preview"]
    assert not [issue for issue in report["review_required"] if issue["category"] == "high_signal"]


def test_autocheck_keeps_final_ledger_gaps_and_invalid_exclusions_pending(tmp_path):
    video_id = seed(tmp_path)
    item = candidate(video_id, load_json(tmp_path / "processed" / video_id / "gold_extraction" / "gold_extraction_status.json")["chunks"][0]["chunk_id"])
    item["numbers"] = [structured_number()]
    record(video_id, tmp_path, review_payload(tmp_path, video_id, item))
    out = tmp_path / "processed" / video_id / "gold_extraction"
    write_json(out / "high_signal_coverage_ledger.json", {"entries": [{
        "segment_id": f"{video_id}-transcript-0001",
        "disposition": "captured",
        "candidate_ids": [f"{video_id}-G001"],
    }]})

    missing = autocheck(video_id, tmp_path)
    assert any(item["segment_id"] == f"{video_id}-transcript-0002" for item in missing["automatic_ledger_preview"])

    write_json(out / "high_signal_coverage_ledger.json", {"entries": [{
        "segment_id": f"{video_id}-transcript-0001",
        "disposition": "captured",
        "candidate_ids": [f"{video_id}-G001"],
    }, {
        "segment_id": f"{video_id}-transcript-0002",
        "disposition": "excluded",
        "reason_code": "not_valid",
        "candidate_ids": [],
    }]})

    invalid = autocheck(video_id, tmp_path)
    assert any(item["segment_id"] == f"{video_id}-transcript-0002" for item in invalid["automatic_ledger_preview"])
    assert invalid["ledger_semantic_alignment"]


def _overlap_report(tmp_path, left_title, right_title, *, related=False):
    video_id = seed(tmp_path)
    chunk_id = load_json(tmp_path / "processed" / video_id / "gold_extraction" / "gold_extraction_status.json")["chunks"][0]["chunk_id"]
    left = candidate(video_id, chunk_id, "G001")
    right = candidate(video_id, chunk_id, "G002")
    left["title"] = left_title
    right["title"] = right_title
    left["numbers"] = [structured_number()]
    right["numbers"] = [structured_number()]
    if related:
        left["relations"] = {"parent_candidate_id": None, "child_candidate_ids": [f"{video_id}-G002"]}
        right["relations"] = {"parent_candidate_id": f"{video_id}-G001", "child_candidate_ids": []}
    record(video_id, tmp_path, {"episode_video_id": video_id, "reviews": [{"chunk_number": 1, "candidates": [left, right], "ledger_decisions": []}]})
    return autocheck(video_id, tmp_path)


def test_autocheck_ignores_generic_and_short_title_terms_for_overlap(tmp_path):
    report = _overlap_report(
        tmp_path,
        "Antes da VSL com copy",
        "Depois da VSL com copy",
    )
    assert not report["overlapping_candidates_without_relation"]


def test_autocheck_keeps_material_three_term_overlap_pending(tmp_path):
    report = _overlap_report(
        tmp_path,
        "Testar mecanismo de oferta para conversao",
        "Validar mecanismo de oferta para conversao",
    )
    overlaps = report["overlapping_candidates_without_relation"]
    assert len(overlaps) == 1
    assert overlaps[0]["shared_title_terms"] == ["conversao", "mecanismo", "oferta"]
    assert any(item["category"] == "overlap" for item in report["review_required"])


def test_autocheck_accepts_symmetric_parent_child_overlap_relation(tmp_path):
    report = _overlap_report(
        tmp_path,
        "Testar mecanismo de oferta para conversao",
        "Validar mecanismo de oferta para conversao",
        related=True,
    )
    assert not report["overlapping_candidates_without_relation"]


def test_finalizer_exports_warning_only_packet_and_is_idempotent(tmp_path):
    video_id = seed(tmp_path)
    item = finalizable_candidate(tmp_path, video_id)
    item["caveats"] = []
    record(video_id, tmp_path, review_payload(tmp_path, video_id, item))

    first = finalize_episode(video_id, tmp_path, export_suffix="warning-packet", revision_id="warning-revision")
    assert first["status"] == "ready"
    assert first["audit_warnings"]
    packet = tmp_path / "exports" / "warning-packet"
    assert {path.name for path in packet.glob("*.json")} == {
        "packet_manifest.json", "transcript_clean.json", "insights_exhaustive.json",
        "high_signal_coverage_ledger.json", "calibration_tests.json",
    }
    assert load_json(packet / "packet_manifest.json")["audit_warnings"] == first["audit_warnings"]
    packet_before = file_snapshot(packet)
    second = finalize_episode(video_id, tmp_path, export_suffix="warning-packet", revision_id="warning-revision")
    assert second["idempotent"] is True
    assert file_snapshot(packet) == packet_before


def test_finalizer_blocks_unsupported_number_before_packet(tmp_path):
    video_id = seed(tmp_path)
    item = finalizable_candidate(tmp_path, video_id)
    record(video_id, tmp_path, review_payload(tmp_path, video_id, item))
    review_path = tmp_path / "processed" / video_id / "gold_extraction" / "manual_reviews" / "chunk_001_review.json"
    review = load_json(review_path)
    review["candidates"][0]["numbers"][0].update({"raw": "999%", "value": 999})
    write_json(review_path, review)

    result = finalize_episode(video_id, tmp_path, export_suffix="must-not-exist")
    assert result["status"] == "blocked"
    assert result["stopped_at"] == "autocheck"
    assert not (tmp_path / "exports" / "must-not-exist").exists()


def test_finalizer_blocks_structurally_invalid_calibration_before_packet(tmp_path):
    video_id = seed(tmp_path)
    record(video_id, tmp_path, review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id)))
    out = tmp_path / "processed" / video_id / "gold_extraction"
    write_json(out / "calibration_tests.json", {
        "episode_video_id": video_id,
        "minimum_required": 1,
        "tests": [{"calibration_id": "broken-target", "segment_ids": [f"{video_id}-transcript-9999"]}],
    })

    result = finalize_episode(video_id, tmp_path, export_suffix="broken-calibration")
    assert result["status"] == "blocked"
    assert result["stopped_at"] == "autocheck"
    assert any(item["category"] == "calibration_structure" for item in result["hard_blockers"])
    assert not (tmp_path / "exports" / "broken-calibration").exists()


def test_finalizer_surfaces_semantic_calibration_ambiguity_as_warning(tmp_path):
    video_id = seed(tmp_path)
    item = finalizable_candidate(tmp_path, video_id)
    item["source_claim"] = "A fonte descreve uma estrategia de runway sem repetir a formulacao literal."
    record(video_id, tmp_path, review_payload(tmp_path, video_id, item))
    out = tmp_path / "processed" / video_id / "gold_extraction"
    write_json(out / "calibration_tests.json", {
        "episode_video_id": video_id,
        "minimum_required": 1,
        "tests": [{
            "calibration_id": "semantic-warning",
            "segment_ids": [f"{video_id}-transcript-0001"],
            "quote_verbatim": "Testamos 20% de desconto antes de escalar.",
            "semantic_candidate_ids": [f"{video_id}-G001"],
        }],
    })

    result = finalize_episode(video_id, tmp_path, export_suffix="semantic-warning")
    assert result["status"] == "ready"
    assert any(item["category"] == "calibration_semantic_ambiguity" for item in result["audit_warnings"])


def test_runner_isolates_a_hard_blocker_and_finalizes_an_independent_episode(tmp_path):
    ready_id = seed(tmp_path, "ready-episode")
    blocked_id = seed(tmp_path, "blocked-episode")
    record(ready_id, tmp_path, review_payload(tmp_path, ready_id, finalizable_candidate(tmp_path, ready_id)))
    record(blocked_id, tmp_path, review_payload(tmp_path, blocked_id, finalizable_candidate(tmp_path, blocked_id)))
    blocked_out = tmp_path / "processed" / blocked_id / "gold_extraction"
    review_path = blocked_out / "manual_reviews" / "chunk_001_review.json"
    review = load_json(review_path)
    review["candidates"][0]["numbers"][0].update({"raw": "999%", "value": 999})
    write_json(review_path, review)
    status_path = blocked_out / "gold_extraction_status.json"
    status = load_json(status_path)
    status["chunks"][0]["review_hash"] = sha256_json(review)
    write_json(status_path, status)

    result = run_manifest({"episodes": [
        {"video_id": ready_id, "mode": "auto", "export_suffix": "ready-isolated"},
        {"video_id": blocked_id, "mode": "auto", "export_suffix": "blocked-isolated"},
    ]}, tmp_path, execute=True)
    by_id = {item["video_id"]: item for item in result["episodes"]}
    assert by_id[ready_id]["execution"]["status"] == "ready"
    assert by_id[blocked_id]["execution"]["status"] == "blocked"
    assert (tmp_path / "exports" / "ready-isolated" / "packet_manifest.json").exists()
    assert not (tmp_path / "exports" / "blocked-isolated").exists()


def test_finalization_receipt_conflicts_after_review_change_and_new_revision_can_finish(tmp_path):
    video_id = seed(tmp_path)
    record(video_id, tmp_path, review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id)))
    first = finalize_episode(video_id, tmp_path, export_suffix="receipt-packet", revision_id="revision-one")
    assert first["status"] == "ready"
    out = tmp_path / "processed" / video_id / "gold_extraction"
    review_path = out / "manual_reviews" / "chunk_001_review.json"
    review = load_json(review_path)
    review["candidates"][0]["title"] = "Comparar desconto antes de escalar investimento"
    write_json(review_path, review)
    before = file_snapshot(out)

    stale = finalize_episode(video_id, tmp_path, export_suffix="receipt-packet", revision_id="revision-one")
    assert stale["status"] == "conflict"
    assert file_snapshot(out) == before

    fresh = finalize_episode(video_id, tmp_path, export_suffix="receipt-packet", revision_id="revision-two")
    assert fresh["status"] == "ready"
    assert fresh["revision_id"] == "revision-two"


def test_finalization_receipt_accepts_crlf_only_review_rewrite(tmp_path):
    video_id = seed(tmp_path)
    record(video_id, tmp_path, review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id)))
    first = finalize_episode(video_id, tmp_path, export_suffix="crlf-packet", revision_id="crlf-revision")
    assert first["status"] == "ready"
    out = tmp_path / "processed" / video_id / "gold_extraction"
    review_path = out / "manual_reviews" / "chunk_001_review.json"
    review_path.write_bytes(review_path.read_bytes().replace(b"\n", b"\r\n"))
    before = file_snapshot(out)
    packet_before = file_snapshot(Path(first["packet"]))

    second = finalize_episode(video_id, tmp_path, export_suffix="crlf-packet", revision_id="crlf-revision")
    assert second["idempotent"] is True
    assert file_snapshot(out) == before
    assert file_snapshot(Path(first["packet"])) == packet_before


@pytest.mark.parametrize("tamper", ["missing", "extra", "renamed", "changed"])
def test_finalization_receipt_rejects_packet_integrity_mismatch(tmp_path, tamper):
    video_id = seed(tmp_path)
    record(video_id, tmp_path, review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id)))
    first = finalize_episode(video_id, tmp_path, export_suffix="tampered-packet", revision_id="packet-revision")
    packet = Path(first["packet"])
    if tamper == "missing":
        (packet / "transcript_clean.json").unlink()
    elif tamper == "extra":
        (packet / "unexpected.json").write_text("{}", encoding="utf-8")
    elif tamper == "renamed":
        (packet / "transcript_clean.json").rename(packet / "wrong-name.json")
    else:
        (packet / "transcript_clean.json").write_text("{}", encoding="utf-8")
    result = finalize_episode(video_id, tmp_path, export_suffix="tampered-packet", revision_id="packet-revision")
    assert result["status"] == "conflict"
    assert result["stopped_at"] == "receipt"
    assert not result.get("idempotent", False)


def test_export_packet_rolls_back_when_staging_copy_fails(tmp_path, monkeypatch):
    video_id = seed(tmp_path)
    record(video_id, tmp_path, review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id)))
    first = finalize_episode(video_id, tmp_path, export_suffix="atomic-packet", revision_id="atomic-one")
    packet = Path(first["packet"])
    before = file_snapshot(packet)
    real_copy = audit_packet.shutil.copy2
    calls = 0

    def fail_second_copy(source, destination, *args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated staging copy failure")
        return real_copy(source, destination, *args, **kwargs)

    monkeypatch.setattr(audit_packet.shutil, "copy2", fail_second_copy)
    with pytest.raises(OSError, match="simulated staging"):
        audit_packet.export_packet(video_id, tmp_path, "atomic-packet")
    assert file_snapshot(packet) == before


def test_export_packet_restores_previous_packet_when_publish_swap_fails(tmp_path, monkeypatch):
    video_id = seed(tmp_path)
    record(video_id, tmp_path, review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id)))
    first = finalize_episode(video_id, tmp_path, export_suffix="swap-packet", revision_id="swap-one")
    packet = Path(first["packet"])
    before = file_snapshot(packet)
    real_replace = audit_packet.os.replace
    calls = 0

    def fail_publish_swap(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated publish swap failure")
        return real_replace(source, destination)

    monkeypatch.setattr(audit_packet.os, "replace", fail_publish_swap)
    with pytest.raises(OSError, match="simulated publish swap"):
        audit_packet.export_packet(video_id, tmp_path, "swap-packet")
    assert file_snapshot(packet) == before


def test_finalizer_blocks_nonverbatim_calibration_quote_before_packet(tmp_path):
    video_id = seed(tmp_path)
    record(video_id, tmp_path, review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id)))
    out = tmp_path / "processed" / video_id / "gold_extraction"
    write_json(out / "calibration_tests.json", {
        "episode_video_id": video_id,
        "minimum_required": 1,
        "tests": [{
            "calibration_id": "fabricated-quote",
            "segment_ids": [f"{video_id}-transcript-0001"],
            "quote_verbatim": "A quote that is not in the transcript.",
        }],
    })
    result = finalize_episode(video_id, tmp_path, export_suffix="fabricated-quote")
    assert result["status"] == "blocked"
    assert any(item["category"] == "calibration_structure" for item in result["hard_blockers"])
    assert not (tmp_path / "exports" / "fabricated-quote").exists()


def test_review_compiler_normalizes_editorial_only_and_preserves_verbatim_quote(tmp_path):
    video_id = seed(tmp_path)
    out = tmp_path / "processed" / video_id / "gold_extraction"
    status = load_json(out / "gold_extraction_status.json")
    item = candidate(video_id, status["chunks"][0]["chunk_id"])
    item.update({
        "title": "Frustração em teste de tráfego",
        "source_claim": "O entrevistado descreve uma frustração ao testar tráfego.",
        "themes": ["traffic_creatives"],
        "type": "reported_case",
    })
    payload = review_payload(tmp_path, video_id, item)
    transcript = load_json(out / "transcript_clean.json")["segments"]
    compiled = compile_payload(video_id, payload, status, transcript, {})

    assert compiled["status"] == "ok"
    compiled_candidate = compiled["reviews"][0]["candidates"][0]
    assert compiled_candidate["title"] == "Frustracao em teste de trafego"
    assert compiled_candidate["type"] == "example"
    assert compiled_candidate["reported_case"] is True
    assert compiled_candidate["themes"] == ["creative_strategy"]
    assert "traffic_creatives" in compiled_candidate["subthemes"]
    assert compiled_candidate["evidence"]["minimal_quote"][0]["quote_verbatim"].encode("utf-8") == transcript[0]["text"].encode("utf-8")
    assert item["title"] == "Frustração em teste de tráfego"


def test_review_compiler_returns_multiple_issues_without_writing(tmp_path):
    video_id = seed(tmp_path)
    out = tmp_path / "processed" / video_id / "gold_extraction"
    status = load_json(out / "gold_extraction_status.json")
    first = candidate(video_id, status["chunks"][0]["chunk_id"], "G001")
    first["minimal_segment_ids"] = []
    second = candidate(video_id, status["chunks"][0]["chunk_id"], "G002")
    second["minimal_segment_ids"] = [f"{video_id}-transcript-9999"]
    payload = {"episode_video_id": video_id, "reviews": [{"chunk_number": 1, "candidates": [first, second], "ledger_decisions": []}]}
    before = file_snapshot(out)
    compiled = compile_payload(video_id, payload, status, load_json(out / "transcript_clean.json")["segments"], {})

    assert compiled["status"] == "error"
    assert len(compiled["issues"]) >= 2
    assert {item["candidate_id"] for item in compiled["issues"]} >= {f"{video_id}-G001", f"{video_id}-G002"}
    assert file_snapshot(out) == before


def test_compiler_rejects_unknown_theme_and_collects_independent_candidate_issues(tmp_path, monkeypatch, capsys):
    video_id = seed(tmp_path)
    out = tmp_path / "processed" / video_id / "gold_extraction"
    status = load_json(out / "gold_extraction_status.json")
    invalid = candidate(video_id, status["chunks"][0]["chunk_id"], "G001")
    invalid.update({
        "themes": ["tema_inventado"], "type": "not_a_type", "causal_certainty": "not_a_cause",
        "claim_risk": "not_a_risk", "title": "curto", "takeaway_applicavel": "curto",
        "minimal_segment_ids": [],
    })
    payload = {"episode_video_id": video_id, "reviews": [{"chunk_number": 1, "candidates": [invalid], "ledger_decisions": []}]}
    before = file_snapshot(out)
    compiled = compile_payload(video_id, payload, status, load_json(out / "transcript_clean.json")["segments"], {})
    fields = {item["field"] for item in compiled["issues"]}
    assert {"themes", "minimal_segment_ids", "candidate"} <= fields
    assert any(item["field"] == "themes" and item["evidence"] == "tema_inventado" for item in compiled["issues"])
    assert compiled["reviews"][0]["candidates"][0]["themes"] == []
    assert file_snapshot(out) == before

    checked = record(video_id, tmp_path, payload, check=True)
    assert checked["status"] == "error"
    assert checked["mode"] == "check"
    assert checked["issues"] == compiled["issues"]
    payload_path = tmp_path / "invalid-payload.json"
    write_json(payload_path, payload)
    monkeypatch.setattr(sys, "argv", ["record_gold_manual_reviews.py", "--video-id", video_id, "--data-root", str(tmp_path), "--input", str(payload_path), "--check"])
    assert record_main() == 1
    cli_result = json.loads(capsys.readouterr().out)
    assert cli_result["status"] == "error"
    assert cli_result["issues"] == compiled["issues"]
    assert file_snapshot(out) == before


def test_compiler_reports_malformed_review_shapes_without_traceback(tmp_path):
    video_id = seed(tmp_path)
    out = tmp_path / "processed" / video_id / "gold_extraction"
    status = load_json(out / "gold_extraction_status.json")
    payload = {"episode_video_id": video_id, "reviews": [
        {"chunk_number": "not-a-number", "candidates": "not-a-list"},
        "not-a-review-object",
    ]}
    result = compile_payload(video_id, payload, status, load_json(out / "transcript_clean.json")["segments"], {})
    assert result["status"] == "error"
    assert {item["field"] for item in result["issues"]} >= {"chunk_number", "review"}


def test_recorder_check_receipt_idempotence_and_recovery(tmp_path):
    video_id = seed(tmp_path)
    payload = review_payload(tmp_path, video_id)
    out = tmp_path / "processed" / video_id / "gold_extraction"
    before_check = file_snapshot(out)
    checked = record(video_id, tmp_path, payload, check=True)
    assert checked["mode"] == "check"
    assert file_snapshot(out) == before_check

    first = record(video_id, tmp_path, payload)
    receipt = out / "manual_review_batch_receipts.json"
    assert receipt.exists()
    after_first = file_snapshot(out)
    recovered = record(video_id, tmp_path, payload)

    assert first["idempotent"] is False
    assert recovered["idempotent"] is True
    assert file_snapshot(out) == after_first


def test_wave_gate_refuses_in_progress_receipts_and_persists_only_terminal_receipts(tmp_path, monkeypatch, capsys):
    video_ids = [f"one-shot-{index}" for index in range(1, 6)]
    for video_id in video_ids:
        seed(tmp_path, video_id)
        record(video_id, tmp_path, review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id)))
        assert finalize_episode(video_id, tmp_path, export_suffix=f"packet-{video_id}", revision_id=f"revision-{video_id}")["status"] == "ready"

    manifest = {
        "required_episode_count": 5,
        "episodes": [{"video_id": video_id, "mode": "auto", "export_suffix": f"packet-{video_id}"} for video_id in video_ids[:4]],
    }
    receipt_path = tmp_path / "wave-receipt.json"
    incomplete = run_manifest(manifest, tmp_path, wave_receipt=receipt_path)
    assert incomplete["wave_gate"]["wave_status"] == "in_progress"
    assert not receipt_path.exists()
    write_json(receipt_path, {"sentinel": "must-not-change"})
    repeated = run_manifest(manifest, tmp_path, wave_receipt=receipt_path)
    assert repeated["receipt_refused"].startswith("wave gate is in_progress")
    assert load_json(receipt_path) == {"sentinel": "must-not-change"}
    manifest_path = tmp_path / "in-progress-wave.json"
    write_json(manifest_path, manifest)
    monkeypatch.setattr(sys, "argv", ["run_gold_wave.py", "--manifest", str(manifest_path), "--data-root", str(tmp_path), "--wave-receipt", str(receipt_path)])
    assert run_main() == 2
    assert json.loads(capsys.readouterr().out)["receipt_refused"].startswith("wave gate is in_progress")
    assert load_json(receipt_path) == {"sentinel": "must-not-change"}

    manifest["episodes"].append({"video_id": video_ids[4], "mode": "auto", "export_suffix": f"packet-{video_ids[4]}"})
    complete = run_manifest(manifest, tmp_path, wave_receipt=receipt_path)
    assert complete["wave_gate"]["wave_status"] == "ready_for_audit"
    assert load_json(receipt_path)["wave_status"] == "ready_for_audit"
    assert evaluate_wave(manifest, tmp_path)["semantic_sha256"] == complete["wave_gate"]["semantic_sha256"]


def _protect_completed_episode(root: Path, video_id: str, suffix: str) -> dict:
    seed(root, video_id)
    record(video_id, root, review_payload(root, video_id, finalizable_candidate(root, video_id)))
    assert finalize_episode(video_id, root, executor_thread_id="executor", export_suffix=suffix, revision_id=f"revision-{video_id}")["status"] == "ready"
    out = root / "processed" / video_id / "gold_extraction"
    status_path = out / "gold_extraction_status.json"
    status = load_json(status_path)
    status.update({"status": "complete", "audit_status": "passed", "open_audit_findings": 0, "executor_thread_id": "executor"})
    write_json(status_path, status)
    report = {
        "episode_video_id": video_id, "audit_route": "external_blind_reviewer", "reviewer": "Independent reviewer",
        "reviewer_thread_id": "reviewer", "reviewer_model": "gpt-5.6-terra", "reasoning_effort": "high",
        "reviewed_at": "2026-07-14T00:00:00Z", "status": "passed", "summary": "All findings resolved.",
        "findings": [], "open_findings": 0,
    }
    write_json(out / "editorial_audit_report.json", report)
    return {"video_id": video_id, "mode": "auto", "export_suffix": suffix, "executor_thread_id": "executor"}


def _pending_episode(root: Path, video_id: str, suffix: str) -> dict:
    seed(root, video_id)
    record(video_id, root, review_payload(root, video_id, finalizable_candidate(root, video_id)))
    assert finalize_episode(video_id, root, export_suffix=suffix, revision_id=f"revision-{video_id}")["status"] == "ready"
    return {"video_id": video_id, "mode": "auto", "export_suffix": suffix}


def test_wave_gate_requires_complete_protected_packet_audit_and_fingerprints(tmp_path):
    entry = _protect_completed_episode(tmp_path, "protected", "protected-packet")
    manifest = {"required_episode_count": 1, "episodes": [entry]}
    assert evaluate_wave(manifest, tmp_path)["wave_status"] == "ready_for_audit"

    missing = _protect_completed_episode(tmp_path, "missing", "missing-packet")
    (tmp_path / "exports" / "missing-packet" / "calibration_tests.json").unlink()
    assert evaluate_wave({"required_episode_count": 1, "episodes": [missing]}, tmp_path)["wave_status"] == "in_progress"

    foreign = _protect_completed_episode(tmp_path, "foreign", "foreign-packet")
    manifest_path = tmp_path / "exports" / "foreign-packet" / "packet_manifest.json"
    packet_manifest = load_json(manifest_path)
    packet_manifest["episode_video_id"] = "other-episode"
    write_json(manifest_path, packet_manifest)
    foreign_result = evaluate_wave({"required_episode_count": 1, "episodes": [foreign]}, tmp_path)
    assert foreign_result["wave_status"] == "in_progress"
    assert foreign_result["episode_results"][0]["packet_identity"] is False

    no_audit = _protect_completed_episode(tmp_path, "noaudit", "noaudit-packet")
    (tmp_path / "processed" / "noaudit" / "gold_extraction" / "editorial_audit_report.json").unlink()
    assert evaluate_wave({"required_episode_count": 1, "episodes": [no_audit]}, tmp_path)["wave_status"] == "in_progress"

    invalid_audit = _protect_completed_episode(tmp_path, "invalidaudit", "invalidaudit-packet")
    invalid_audit_path = tmp_path / "processed" / "invalidaudit" / "gold_extraction" / "editorial_audit_report.json"
    invalid_report = load_json(invalid_audit_path)
    invalid_report["open_findings"] = 1
    write_json(invalid_audit_path, invalid_report)
    assert evaluate_wave({"required_episode_count": 1, "episodes": [invalid_audit]}, tmp_path)["wave_status"] == "in_progress"

    divergent = _protect_completed_episode(tmp_path, "divergent", "divergent-packet")
    fingerprints_path = tmp_path / "processed" / "divergent" / "gold_extraction" / "protected_fingerprints.json"
    fingerprints = load_json(fingerprints_path)
    fingerprints["after"] = {"changed": "hash"}
    write_json(fingerprints_path, fingerprints)
    assert evaluate_wave({"required_episode_count": 1, "episodes": [divergent]}, tmp_path)["wave_status"] == "in_progress"


def test_wave_gate_binds_pending_receipt_to_manifest_packet_identity(tmp_path):
    pending_a = _pending_episode(tmp_path, "pending-a", "packet-a")
    pending_b = _pending_episode(tmp_path, "pending-b", "packet-b")
    valid_manifest = {"required_episode_count": 1, "episodes": [pending_a]}
    assert evaluate_wave(valid_manifest, tmp_path)["wave_status"] == "ready_for_audit"

    out_a = tmp_path / "processed" / "pending-a" / "gold_extraction"
    receipt_path = out_a / "gold_finalization_receipt.json"
    receipt = load_json(receipt_path)
    packet_b = tmp_path / "exports" / "packet-b"
    from scripts.finalize_gold_episode import _packet_snapshot
    receipt["packet"] = str(packet_b)
    receipt["packet_files"] = _packet_snapshot(packet_b)
    write_json(receipt_path, receipt)
    wave_receipt = tmp_path / "pending-wave-receipt.json"
    cross_packet = run_manifest(valid_manifest, tmp_path, wave_receipt=wave_receipt)
    assert cross_packet["wave_gate"]["wave_status"] == "in_progress"
    assert cross_packet["wave_gate"]["episode_results"][0]["packet_identity"] is False
    assert not wave_receipt.exists()

    # Restore the valid receipt, then independently prove foreign identity and
    # a mismatched snapshot are both rejected at the same expected destination.
    receipt["packet"] = str(tmp_path / "exports" / "packet-a")
    receipt["packet_files"] = _packet_snapshot(tmp_path / "exports" / "packet-a")
    write_json(receipt_path, receipt)
    packet_manifest_path = tmp_path / "exports" / "packet-a" / "packet_manifest.json"
    packet_manifest = load_json(packet_manifest_path)
    packet_manifest["episode_video_id"] = "foreign-video"
    write_json(packet_manifest_path, packet_manifest)
    foreign_packet = evaluate_wave(valid_manifest, tmp_path)
    assert foreign_packet["wave_status"] == "in_progress"
    assert foreign_packet["episode_results"][0]["packet_identity"] is False

    packet_manifest["episode_video_id"] = "pending-a"
    write_json(packet_manifest_path, packet_manifest)
    receipt["packet_files"] = {"names": [], "files": []}
    write_json(receipt_path, receipt)
    snapshot_mismatch = evaluate_wave(valid_manifest, tmp_path)
    assert snapshot_mismatch["wave_status"] == "in_progress"
    assert snapshot_mismatch["episode_results"][0]["packet_identity"] is True
    assert snapshot_mismatch["episode_results"][0]["packet_snapshot_valid"] is False


def test_terminally_blocked_wave_can_persist_a_final_receipt(tmp_path):
    manifest = {"required_episode_count": 1, "episodes": [{"video_id": "missing", "mode": "auto"}]}
    receipt_path = tmp_path / "terminal-wave-receipt.json"
    result = run_manifest(manifest, tmp_path, wave_receipt=receipt_path)
    assert result["wave_gate"]["wave_status"] == "terminally_blocked"
    assert load_json(receipt_path)["wave_status"] == "terminally_blocked"
