import copy
import json
import sys
from pathlib import Path

import pytest

from scripts import export_gold_audit_packet as audit_packet
from scripts.gold_reaudit_delta import packet_delta
from scripts.gold_review_compiler import (
    COMPACT_EPISODE_PAYLOAD_FORMAT,
    COMPACT_EPISODE_PAYLOAD_FORMAT_V3,
    COMPACT_PAYLOAD_FORMAT,
    compile_payload,
)
from scripts.gold_review_autocheck import autocheck, exact_candidate_duplicate_groups, excluded_risk_clusters, review_audit_warnings, semantic_closure_index, sparse_recall_view
from scripts.gold_wave_gate import evaluate_wave
from scripts.gold_review_patch import apply_patch, generate_audit_remediation_scaffold, generate_source_assert_manifest
from scripts.finalize_gold_episode import finalize_episode
from scripts.gold_extraction_common import (
    candidate_numeric_coverage,
    json_hashes,
    load_json,
    numeric_mentions,
    resolve_data_path,
    sha256_json,
    sha256_semantic_json,
    write_json,
)
from scripts.record_gold_external_audit import record_audit
from scripts.record_gold_manual_reviews import main as record_main, record
from scripts.reprocess_gold_episode import chunk_work_order, legacy_chunk_work_order, prepare_episode, work_order_metrics
from scripts.run_gold_wave import detect_route, main as run_main, run_manifest
from scripts.run_gold_episode_fast import (
    CANONICAL_EXTRACTION_ARCHITECTURE,
    bootstrap_episode,
    build_compact_reading_context,
    build_reading_context,
    compact_cli_result,
    inspect_episode_draft,
    mark_semantic_phase,
    main as fast_main,
    make_preview_receipt,
    prelint_episode_draft,
    run_post_audit_remediation,
    run_episode,
    select_and_bootstrap_episode,
    select_next_episode,
    start_episode,
    validate_compact_reading_context,
    write_compact_reading_context,
    _validate_or_pin_runtime_snapshot,
)
from scripts.run_gold_episode_fast import _record_session_event, _risk_acknowledgement_for
from scripts.sync_wsl_runtime import main as sync_runtime_main, synchronize_runtime, validate_runtime_parity_receipt
from scripts.complete_gold_episode import _session_performance, complete_episode, performance_budget, validate_completion_receipt
from scripts.gold_final_audit_bundle import build_audit_dossier, build_reaudit_delta, validate_audit_dossier, validate_reaudit_delta, write_audit_dossier
from scripts.gold_audit_lifecycle import build_audit_request, write_audit_request
from scripts.gold_episode_priority import (
    CATEGORY_ORDER,
    advance_queue_state,
    build_priority_queue,
    build_queue_state,
    classify_episode,
    load_queue_state,
    merge_catalog_entries,
    queue_state_path,
    _repair_known_mojibake,
    write_queue_state,
)
from scripts.audit_gold_source_inventory import build_inventory as build_source_inventory
from scripts.verify_gold_runtime import verify_environment


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


def seed_unprepared(root: Path, video_id: str, segment_count: int) -> str:
    raw = root / "raw" / "youtube" / video_id
    processed = root / "processed" / video_id
    raw.mkdir(parents=True)
    processed.mkdir(parents=True)
    segments = [
        {"start_seconds": index * 5, "duration_seconds": 5, "text": f"Segmento fonte {index} com uma proposicao util."}
        for index in range(segment_count)
    ]
    write_json(raw / "metadata.json", {
        "youtube_video_id": video_id,
        "title": f"Episode {video_id}",
        "duration_seconds": segment_count * 5,
        "transcript_status": "available",
    })
    write_json(raw / "transcript_original.json", {
        "youtube_video_id": video_id,
        "transcript_status": "available",
        "segments": segments,
    })
    write_json(processed / "content_segments.json", {"episode_video_id": video_id, "segments": segments})
    return video_id


def test_verify_environment_certifies_repository_venv_and_writable_temp(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    data = tmp_path / "data"
    temp = tmp_path / "temp"
    (repo / ".venv" / "bin").mkdir(parents=True)
    data.mkdir()
    monkeypatch.setattr("scripts.verify_gold_runtime.inside_wsl", lambda: True)
    monkeypatch.setattr("scripts.verify_gold_runtime.sys.platform", "linux")
    monkeypatch.setattr("scripts.verify_gold_runtime.sys.executable", str(repo / ".venv" / "bin" / "python"))
    monkeypatch.setattr("scripts.verify_gold_runtime.sys.version_info", (3, 12, 0))
    monkeypatch.setattr("scripts.verify_gold_runtime.shutil.which", lambda name: f"/usr/bin/{name}")

    result = verify_environment(repo_root=repo, data_root=data, temp_root=temp, runtime="wsl_linux")

    assert result["status"] == "pass"
    assert result["runtime"] == "wsl_linux"
    assert result["temp_writable"] is True
    assert result["active_python"].startswith(str(repo / ".venv"))


def test_verify_environment_defaults_to_windows_native_runtime(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    data = tmp_path / "data"
    temp = tmp_path / "temp"
    (repo / ".venv" / "Scripts").mkdir(parents=True)
    data.mkdir()
    monkeypatch.delenv("MSF_GOLD_RUNTIME", raising=False)
    monkeypatch.setattr("scripts.verify_gold_runtime.sys.platform", "win32")
    monkeypatch.setattr("scripts.verify_gold_runtime.sys.executable", str(repo / ".venv" / "Scripts" / "python.exe"))
    monkeypatch.setattr("scripts.verify_gold_runtime.sys.version_info", (3, 12, 0))
    monkeypatch.setattr("scripts.verify_gold_runtime.shutil.which", lambda name: f"C:/tools/{name}.exe")

    result = verify_environment(repo_root=repo, data_root=data, temp_root=temp)

    assert result["status"] == "pass"
    assert result["runtime"] == "windows_native"
    assert "rsync" not in result["commands"]
    assert "rsync" in result["optional_commands"]


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


def approve_preview(
    root: Path,
    video_id: str,
    payload: dict,
    *,
    revision_id: str,
    export_suffix: str,
) -> Path:
    preview = inspect_episode_draft(video_id, root, payload)
    assert preview["status"] == "ready_to_apply"
    path = root / "job" / "clean_preview_receipt.json"
    write_json(path, make_preview_receipt(preview, revision_id=revision_id, export_suffix=export_suffix))
    return path


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


def test_select_next_bootstraps_nearest_source_complete_episode_and_starts_epic_timer(tmp_path):
    seed_unprepared(tmp_path, "far", 3)
    selected_video = seed_unprepared(tmp_path, "near", 5)
    seed(tmp_path, "already-gold")

    selection = select_next_episode(tmp_path, minimum_segments=1, maximum_segments=10, target_segments=5)
    assert selection["status"] == "selected"
    assert selection["selected"]["video_id"] == selected_video
    assert len(selection["selected"]["source_files"]) == 3

    job_dir = tmp_path / "job"
    result = select_and_bootstrap_episode(
        tmp_path,
        job_dir,
        selection_id="pilot-next",
        export_prefix="pilot_export",
        minimum_segments=1,
        maximum_segments=10,
        target_segments=5,
        epic_started_at="2026-07-15T12:00:00+00:00",
    )
    assert result["status"] == "ready"
    assert result["episode_video_id"] == selected_video
    assert result["revision_id"] == "pilot-next-near-final-001"
    assert result["export_suffix"] == "pilot_export_near"
    assert load_json(job_dir / "selection_receipt.json")["semantic_sha256"]
    assert load_json(job_dir / "bootstrap_request.json")["video_id"] == selected_video
    session = load_json(job_dir / "episode_fast_session.json")
    assert session["epic_started_at"] == "2026-07-15T12:00:00+00:00"
    assert [item["phase"] for item in session["events"][:2]] == ["selection", "preflight_and_context"]
    assert session["operation_counts"]["selections"] == 1


def test_start_episode_certifies_and_bootstraps_with_one_run_id(tmp_path, monkeypatch):
    selected_video = seed_unprepared(tmp_path, "certified", 5)
    monkeypatch.setattr("scripts.run_gold_episode_fast.verify_environment", lambda **kwargs: {
        "status": "pass", "paths": [{"name": "data_root", "path": str(kwargs["data_root"]), "linux_native": True}], "errors": [],
    })
    job_dir = tmp_path / "job"
    result = start_episode(
        tmp_path,
        job_dir,
        selection_id="pilot-start",
        export_prefix="pilot_export",
        minimum_segments=1,
        maximum_segments=10,
        target_segments=5,
        epic_started_at="2026-07-16T12:00:00+00:00",
    )
    assert result["status"] == "ready"
    assert result["episode_video_id"] == selected_video
    assert result["runtime_verification"]["status"] == "pass"
    assert result["startup_metrics"]["total_ms"] >= 0
    session = load_json(job_dir / "episode_fast_session.json")
    assert session["run_id"] == result["run_id"]
    assert session["epic_started_at"] == "2026-07-16T12:00:00+00:00"
    reading_spans = [
        item for item in session["semantic_spans"]
        if item["phase"] == "semantic_reading_and_authoring"
    ]
    assert len(reading_spans) == 1
    assert reading_spans[0]["ended_at"] is None


def test_priority_queue_classifies_by_theme_then_sorts_shortest_first(tmp_path):
    first = seed_unprepared(tmp_path, "vsl-long", 8)
    second = seed_unprepared(tmp_path, "vsl-short", 4)
    third = seed_unprepared(tmp_path, "copy-short", 2)
    for video_id, title, duration in (
        (first, "Como criar uma VSL", 800),
        (second, "VSL que converte", 400),
        (third, "Copy e headlines", 200),
    ):
        path = tmp_path / "raw" / "youtube" / video_id / "metadata.json"
        metadata = load_json(path)
        metadata.update({"title": title, "duration_seconds": duration})
        write_json(path, metadata)
    queue = build_priority_queue(tmp_path)
    assert CATEGORY_ORDER[:4] == ["vsl", "copy", "ads", "funnel"]
    assert [item["video_id"] for item in queue["entries"]] == [second, first, third]
    assert classify_episode("Quiz de diagnostico", [])["category"] == "quiz"
    assert classify_episode("Videos e copy para anuncios", [])["category"] == "vsl"
    assert classify_episode("Copy e criativos", [])["category"] == "copy"
    assert classify_episode("Como criar ofertas que convertem", [])["category"] == "copy"
    assert classify_episode("Funil com quiz", [])["category"] == "funnel"
    assert classify_episode("Ele trackeou vendas durante um ano", [])["category"] == "funnel"
    assert classify_episode("Webinario que converte", [])["category"] == "funnel"
    assert classify_episode("Como escalar uma oferta", [])["category"] == "copy"
    assert classify_episode("Venda no perpetuo", [])["category"] == "evergreen"
    assert classify_episode("Lancamento com experts", [])["category"] == "launch"
    assert classify_episode("Experts e afiliados", [])["category"] == "experts"
    assert classify_episode("Programa de afiliados", [])["category"] == "affiliate"
    assert classify_episode("Oferta de nutraceuticos", [])["category"] == "copy"
    assert classify_episode("Operacao criada com IA e automacoes", [])["category"] == "ai_automation"
    assert classify_episode("Campanhas de marketing direto", [])["category"] == "direct_response"
    assert classify_episode("Recuperacao de vendas com WhatsApp", [])["category"] == "crm_retention"
    assert classify_episode("Infoproduto no mercado americano", [])["category"] == "international"
    assert classify_episode("Conteudo organico no YouTube", [])["category"] == "content_organic"
    assert classify_episode("Como vender infoprodutos", [])["category"] == "infoproducts"
    assert classify_episode("Gestao de operacoes digitais", [])["category"] == "business_operations"
    assert classify_episode("Os bastidores da Queima Diaria", [])["category"] == "business_operations"
    assert classify_episode("Carreira no marketing digital", [])["category"] == "digital_business"
    assert classify_episode("Case que faturou milhoes", [])["category"] == "growth_cases"
    assert classify_episode("Entrevista qualquer - Segredos da Escala #123", [])["category"] == "other"


def test_select_next_uses_queue_order_only_within_requested_segment_band(tmp_path):
    short = seed_unprepared(tmp_path, "short", 2)
    preferred = seed_unprepared(tmp_path, "preferred", 20)
    queue_path = tmp_path / "priority.json"
    write_json(queue_path, {
        "schema_version": "1.0.0",
        "kind": "gold_episode_priority_queue",
        "semantic_sha256": "queue-hash",
        "entries": [
            {"rank": 1, "video_id": preferred, "category": "vsl", "category_label": "VSL"},
            {"rank": 2, "video_id": short, "category": "copy", "category_label": "Copy"},
        ],
    })
    result = select_next_episode(
        tmp_path,
        minimum_segments=1,
        maximum_segments=3,
        target_segments=2,
        priority_queue=queue_path,
    )
    assert result["status"] == "selected"
    assert result["selected"]["video_id"] == short
    assert result["selected"]["queue_rank"] == 2
    assert result["selection_policy"]["mode"] == "priority_queue"


def test_priority_queue_state_is_ordering_only_and_stale_terminal_is_rechecked(tmp_path):
    first = seed_unprepared(tmp_path, "first", 8)
    second = seed_unprepared(tmp_path, "second", 4)
    for video_id, title, duration in ((first, "VSL longa", 800), (second, "VSL curta", 400)):
        path = tmp_path / "raw" / "youtube" / video_id / "metadata.json"
        metadata = load_json(path)
        metadata.update({"title": title, "duration_seconds": duration})
        write_json(path, metadata)
    queue = build_priority_queue(tmp_path)
    queue_path = tmp_path / "priority.json"
    write_json(queue_path, queue)
    state = build_queue_state(queue, terminal_updates={second: "complete_passed"}, source="test")
    write_queue_state(queue_path, state)

    loaded, errors = load_queue_state(queue_path)
    assert errors == []
    assert loaded is not None
    assert loaded["next_episode"]["video_id"] == first
    assert "`first`" in queue_path.with_suffix(".md").read_text(encoding="utf-8")

    result = select_next_episode(
        tmp_path, minimum_segments=1, maximum_segments=10, priority_queue=queue_path
    )
    assert result["status"] == "selected"
    assert result["selected"]["video_id"] == second
    assert result["queue_next_episode"]["video_id"] == first
    assert result["selection_policy"]["mode"] == "priority_queue_state"
    assert result["eligible_count"] == 2


def test_advancing_queue_state_materializes_the_following_episode(tmp_path):
    first = seed_unprepared(tmp_path, "first", 4)
    second = seed_unprepared(tmp_path, "second", 8)
    queue = build_priority_queue(tmp_path)
    queue_path = tmp_path / "priority.json"
    write_json(queue_path, queue)
    write_queue_state(queue_path, build_queue_state(queue))

    advanced = advance_queue_state(queue_path, first, "finalized_pending_audit")

    assert advanced["remaining_count"] == 1
    assert advanced["next_episode"]["video_id"] == second
    assert queue_state_path(queue_path).is_file()


def test_priority_queue_skips_catalog_episode_awaiting_source_for_next_ready_item(tmp_path):
    source_complete = seed_unprepared(tmp_path, "source-ready", 4)
    queue_path = tmp_path / "priority.json"
    write_json(queue_path, {
        "schema_version": "1.1.0",
        "kind": "gold_episode_priority_queue",
        "semantic_sha256": "queue-hash",
        "entries": [
            {"rank": 1, "video_id": "missing-src", "youtube_url": "https://www.youtube.com/watch?v=missing-src", "category": "vsl", "category_label": "VSL", "source_status": "cataloged_unverified"},
            {"rank": 2, "video_id": source_complete, "category": "copy", "category_label": "Copy", "source_status": "runtime_ready"},
        ],
    })
    result = select_next_episode(
        tmp_path, minimum_segments=1, maximum_segments=10, priority_queue=queue_path
    )
    assert result["status"] == "selected"
    assert result["selected"]["video_id"] == source_complete
    assert result["selected"]["queue_rank"] == 2
    assert result["source_required"] is None
    assert result["skipped_source_required_count"] == 1
    skipped = result["skipped_source_required"][0]
    assert skipped["video_id"] == "missing-src"
    assert skipped["queue_rank"] == 1
    assert skipped["runtime_readiness"]["missing_artifacts"] == ["metadata", "transcript", "content_segments"]


def test_priority_queue_state_skips_unavailable_head_without_rewriting_state(tmp_path):
    source_ready = seed_unprepared(tmp_path, "state-source-ready", 4)
    queue_path = tmp_path / "priority.json"
    queue = {
        "schema_version": "1.2.0",
        "kind": "gold_episode_priority_queue",
        "semantic_sha256": "queue-hash",
        "total_episodes": 2,
        "entries": [
            {"rank": 1, "video_id": "state-missing", "category": "vsl", "category_label": "VSL"},
            {"rank": 2, "video_id": source_ready, "category": "copy", "category_label": "Copy"},
        ],
    }
    write_json(queue_path, queue)
    write_json(queue_state_path(queue_path), build_queue_state(queue))

    result = select_next_episode(
        tmp_path, minimum_segments=1, maximum_segments=10, priority_queue=queue_path
    )

    assert result["status"] == "selected"
    assert result["queue_next_episode"]["video_id"] == "state-missing"
    assert result["selected"]["video_id"] == source_ready
    assert result["skipped_source_required_count"] == 1


def test_priority_queue_reports_invalid_transcript_in_the_active_data_root(tmp_path):
    video_id = seed_unprepared(tmp_path, "invalid-transcript", 3)
    transcript_path = tmp_path / "raw" / "youtube" / video_id / "transcript_original.json"
    transcript = load_json(transcript_path)
    transcript["transcript_status"] = "missing"
    transcript["segments"] = []
    write_json(transcript_path, transcript)
    metadata_path = tmp_path / "raw" / "youtube" / video_id / "metadata.json"
    metadata = load_json(metadata_path)
    metadata["transcript_status"] = "missing"
    write_json(metadata_path, metadata)
    queue_path = tmp_path / "priority.json"
    write_json(queue_path, {
        "schema_version": "1.2.0",
        "kind": "gold_episode_priority_queue",
        "semantic_sha256": "queue-hash",
        "entries": [{"rank": 1, "video_id": video_id, "category": "vsl", "category_label": "VSL"}],
    })

    result = select_next_episode(
        tmp_path, minimum_segments=1, maximum_segments=10, priority_queue=queue_path
    )

    assert result["status"] == "source_required"
    assert result["source_required"]["runtime_readiness"]["invalid_artifacts"] == ["transcript_status_missing", "transcript_segments_empty"]


def test_catalog_merge_keeps_every_public_video_and_marks_missing_sources():
    merged = merge_catalog_entries(
        [{"video_id": "ready", "title": "Copy pronta", "duration_seconds": 200, "clean_segments": 10, "source_status": "runtime_ready", **classify_episode("Copy pronta")}],
        [
            {"video_id": "ready", "title": "Copy pronta | SDE #1", "duration_seconds": "200", "discovered_order": "2"},
            {"video_id": "new-video", "title": "VSL extra sem numero", "duration_seconds": "300", "discovered_order": "1", "youtube_url": "https://www.youtube.com/watch?v=new-video"},
        ],
    )
    assert [item["video_id"] for item in merged] == ["new-video", "ready"]
    assert merged[0]["source_status"] == "cataloged_unverified"
    assert merged[1]["source_status"] == "runtime_ready"


def test_priority_queue_repairs_known_catalog_mojibake_without_touching_normal_text():
    assert _repair_known_mojibake("LanÃƒÂ§amentos e VÃƒÂ­deos") == "Lançamentos e Vídeos"
    assert _repair_known_mojibake("Lançamentos e Vídeos") == "Lançamentos e Vídeos"


def test_gold_source_inventory_separates_missing_and_materialization_states(tmp_path):
    ready = seed_unprepared(tmp_path, "ready", 3)
    materialize = seed_unprepared(tmp_path, "materialize", 3)
    (tmp_path / "processed" / materialize / "content_segments.json").unlink()
    queue_path = tmp_path / "priority.json"
    queue = build_priority_queue(base_entries=[
        {"video_id": ready, "title": "VSL pronta", "duration_seconds": 30, "clean_segments": 3, **classify_episode("VSL pronta")},
        {"video_id": materialize, "title": "VSL materializar", "duration_seconds": 30, "clean_segments": 0, **classify_episode("VSL materializar")},
    ])
    write_json(queue_path, queue)
    write_queue_state(queue_path, build_queue_state(queue))

    inventory = build_source_inventory(tmp_path, queue_path)
    by_id = {item["video_id"]: item for item in inventory["items"]}

    assert by_id[ready]["source_state"] == "ready_for_gold"
    assert by_id[materialize]["source_state"] == "needs_materialization"


def test_prelint_reports_procedural_numeric_scope_and_does_not_create_preview_receipt(tmp_path):
    video_id = seed(tmp_path, "prelint")
    item = finalizable_candidate(tmp_path, video_id)
    item["steps"] = []
    item["numbers"] = []
    item["minimal_segment_ids"] = [f"{video_id}-transcript-0002"]
    item["support_segment_ids"] = [f"{video_id}-transcript-0001"]
    payload = review_payload(tmp_path, video_id, item)
    job_dir = tmp_path / "prelint-job"
    before = file_snapshot(tmp_path / "processed" / video_id / "gold_extraction")

    result = prelint_episode_draft(video_id, tmp_path, payload)

    assert result["status"] == "needs_revision"
    assert result["mode"] == "prelint"
    assert result["terminal"] is False
    assert result["continue_required"] is True
    assert result["workflow_disposition"] == "repair_payload_and_repeat_prelint"
    assert result["stopped_at"] is None
    assert result["diagnostic_stage"] == "compiler"
    assert "do not emit a final response" in result["next_action"]
    assert any("procedural type needs steps" in issue["evidence"] for issue in result["prelint_inventory"]["compiler_issues"])
    assert not (job_dir / "clean_preview_receipt.json").exists()
    assert file_snapshot(tmp_path / "processed" / video_id / "gold_extraction") == before


def test_prelint_surfaces_support_only_numeric_evidence_before_official_check(tmp_path):
    video_id = seed(tmp_path, "prelint-numeric-scope")
    item = finalizable_candidate(tmp_path, video_id)
    item["numbers"] = []
    item["minimal_segment_ids"] = [f"{video_id}-transcript-0002"]
    item["support_segment_ids"] = [f"{video_id}-transcript-0001"]
    payload = review_payload(tmp_path, video_id, item)

    result = prelint_episode_draft(video_id, tmp_path, payload)

    warnings = result["prelint_inventory"]["evidence_scope_warnings"]
    assert any(item["category"] == "support_only_numeric_evidence" for item in warnings)
    assert any(item["category"] == "numbers" for item in result["prelint_inventory"]["hard_blockers"])


def test_clean_prelint_requires_same_epic_one_shot_continuation(tmp_path):
    video_id = seed(tmp_path, "prelint-clean-continuation")
    payload = review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id))

    result = prelint_episode_draft(video_id, tmp_path, payload)

    assert result["status"] == "prelint_clean"
    assert result["prelint_clean"] is True
    assert result["terminal"] is False
    assert result["continue_required"] is True
    assert result["workflow_disposition"] == "run_one_shot"
    assert result["stopped_at"] is None
    assert "one-shot" in result["next_action"]


def test_dry_run_is_pure_and_returns_consolidated_repair_manifest(tmp_path, monkeypatch, capsys):
    video_id = seed(tmp_path, "dry-run")
    item = finalizable_candidate(tmp_path, video_id)
    item["steps"] = []
    payload = review_payload(tmp_path, video_id, item)
    payload_path = tmp_path / "payload.json"
    write_json(payload_path, payload)
    job_dir = tmp_path / "dry-run-job"
    before = file_snapshot(tmp_path / "processed" / video_id / "gold_extraction")
    monkeypatch.setattr(sys, "argv", [
        "run_gold_episode_fast.py",
        "--video-id", video_id,
        "--data-root", str(tmp_path),
        "--input", str(payload_path),
        "--job-dir", str(job_dir),
        "--dry-run",
        "--full-output",
    ])

    assert fast_main() == 0

    result = json.loads(capsys.readouterr().out)
    assert result["mode"] == "dry_run"
    assert result["status"] == "needs_revision"
    assert result["terminal"] is False
    assert result["continue_required"] is True
    assert result["workflow_disposition"] == "repair_payload_and_repeat_prelint"
    assert result["stopped_at"] is None
    assert result["diagnostic_stage"] == "compiler"
    assert result["prelint_inventory"]["repair_manifest"]["items"]
    assert not job_dir.exists()
    assert file_snapshot(tmp_path / "processed" / video_id / "gold_extraction") == before


def test_episode_fast_applies_one_review_transaction_and_one_finalization(tmp_path):
    video_id = seed(tmp_path)
    payload = review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id))

    preview_receipt = approve_preview(
        tmp_path, video_id, payload,
        revision_id="fast-episode-001", export_suffix="fast-episode-packet",
    )
    result = run_episode(
        video_id,
        tmp_path,
        payload,
        apply=True,
        revision_id="fast-episode-001",
        export_suffix="fast-episode-packet",
        preview_receipt_path=preview_receipt,
        audit_bundle_path=tmp_path / "job" / "final_audit_bundle.json",
        job_dir=tmp_path / "job",
    )

    assert result["status"] == "ready"
    assert result["persist"]["written_reviews"] == 1
    assert result["metrics"]["review_write_operations"] == 1
    assert result["metrics"]["finalizer_calls"] == 1
    assert result["metrics"]["compile_ms"] >= 0
    assert result["metrics"]["preflight_ms"] >= 0
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
    bundle = load_json(tmp_path / "job" / "final_audit_bundle.json")
    assert bundle["candidate_count"] == 1
    assert bundle["packet"]["valid_five_file_packet"] is True
    session = load_json(tmp_path / "job" / "episode_fast_session.json")
    assert session["events"][-1]["phase"] == "apply_and_finalize"
    assert session["events"][-1]["elapsed_since_preflight_ms"] >= result["metrics"]["total_ms"]


def test_episode_fast_one_shot_creates_preview_before_single_write(tmp_path):
    video_id = seed(tmp_path)
    payload = review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id))
    job_dir = tmp_path / "one-shot-job"
    receipt = job_dir / "clean_preview_receipt.json"

    result = run_episode(
        video_id,
        tmp_path,
        payload,
        apply=True,
        revision_id="fast-one-shot-001",
        export_suffix="fast-one-shot-packet",
        preview_receipt_path=receipt,
        create_preview_receipt=True,
        job_dir=job_dir,
        mirror_job_dir=tmp_path / "one-shot-mirror",
    )

    assert result["status"] == "ready"
    assert receipt.exists()
    assert load_json(receipt)["status"] == "ready_to_apply"
    assert result["metrics"]["review_write_operations"] == 1
    assert result["metrics"]["finalizer_calls"] == 1
    assert (job_dir / "final_audit_dossier.jsonl").exists()
    dossier = result["audit_dossier"]
    assert Path(dossier["mirror"]["path"]).read_bytes() == Path(dossier["path"]).read_bytes()
    assert dossier["mirror"]["physical_sha256"] == dossier["physical_sha256"]


def test_episode_fast_reapply_recovers_receipts_without_rewriting(tmp_path):
    video_id = seed(tmp_path)
    payload = review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id))
    preview_receipt = approve_preview(
        tmp_path, video_id, payload,
        revision_id="fast-episode-001", export_suffix="fast-episode-packet",
    )
    first = run_episode(
        video_id,
        tmp_path,
        payload,
        apply=True,
        revision_id="fast-episode-001",
        export_suffix="fast-episode-packet",
        preview_receipt_path=preview_receipt,
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
        preview_receipt_path=preview_receipt,
    )

    assert repeated["status"] == "ready"
    assert repeated["persist"]["idempotent"] is True
    assert repeated["finalization"]["idempotent"] is True
    assert repeated["metrics"]["review_write_operations"] == 0
    assert file_snapshot(tracked) == before_gold
    assert file_snapshot(tmp_path / "exports" / "fast-episode-packet") == before_packet


def test_episode_fast_refuses_apply_without_or_with_stale_preview_receipt(tmp_path):
    video_id = seed(tmp_path)
    payload = review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id))
    out = tmp_path / "processed" / video_id / "gold_extraction"
    before = file_snapshot(out)

    missing = run_episode(
        video_id, tmp_path, payload, apply=True,
        revision_id="fast-episode-001", export_suffix="fast-episode-packet",
    )
    assert missing["status"] == "blocked"
    assert missing["stopped_at"] == "preview_receipt"
    assert file_snapshot(out) == before

    receipt = approve_preview(
        tmp_path, video_id, payload,
        revision_id="fast-episode-001", export_suffix="fast-episode-packet",
    )
    changed = copy.deepcopy(payload)
    changed["reviews"][0]["candidates"][0]["title"] = "Outro titulo semanticamente diferente"
    stale = run_episode(
        video_id, tmp_path, changed, apply=True,
        revision_id="fast-episode-001", export_suffix="fast-episode-packet",
        preview_receipt_path=receipt,
    )
    assert stale["status"] == "conflict"
    assert stale["stopped_at"] == "preview_receipt"
    assert file_snapshot(out) == before


def test_finalizer_rejects_persisted_reviews_that_do_not_match_clean_preview(tmp_path):
    video_id = seed(tmp_path)
    payload = review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id))
    revision_id = "fast-episode-001"
    export_suffix = "fast-episode-packet"
    receipt = approve_preview(
        tmp_path, video_id, payload,
        revision_id=revision_id, export_suffix=export_suffix,
    )
    payload_hash = record(video_id, tmp_path, payload)["semantic_sha256"]
    review_path = tmp_path / "processed" / video_id / "gold_extraction" / "manual_reviews" / "chunk_001_review.json"
    review = load_json(review_path)
    review["candidates"][0]["title"] = "Titulo alterado depois da previa"
    write_json(review_path, review)

    result = finalize_episode(
        video_id,
        tmp_path,
        export_suffix=export_suffix,
        revision_id=revision_id,
        preview_receipt_path=receipt,
        required_preview_sha256=payload_hash,
    )

    assert result["status"] == "blocked"
    assert result["stopped_at"] == "preview_receipt"
    assert not (tmp_path / "exports" / export_suffix).exists()


def test_compact_episode_payload_expands_defaults_aliases_and_evidence_ranges(tmp_path):
    video_id = seed(tmp_path)
    out = tmp_path / "processed" / video_id / "gold_extraction"
    status = load_json(out / "gold_extraction_status.json")
    transcript = load_json(out / "transcript_clean.json")["segments"]
    verbose_candidates = []
    compact_candidates = []
    base = finalizable_candidate(tmp_path, video_id)
    for index in range(1, 9):
        verbose = copy.deepcopy(base)
        verbose["candidate_id"] = f"{video_id}-G{index:03d}"
        verbose["title"] = f"Teste estruturado numero {index}"
        verbose_candidates.append(verbose)
        compact_candidates.append({
            "id": verbose["candidate_id"],
            "title": verbose["title"],
            "claim": verbose["source_claim"],
            "takeaway": verbose["takeaway_applicavel"],
        })
    verbose_payload = {"episode_video_id": video_id, "reviews": [{"chunk_number": 1, "candidates": verbose_candidates, "ledger_decisions": []}]}
    compact_payload = {
        "payload_format": COMPACT_PAYLOAD_FORMAT,
        "episode_video_id": video_id,
        "candidate_defaults": {
            key: copy.deepcopy(value)
            for key, value in base.items()
            if key not in {"candidate_id", "title", "source_claim", "takeaway_applicavel", "chunk_id", "minimal_segment_ids", "support_segment_ids"}
        } | {
            "minimal": [{"range": [0, 0]}],
            "support": [{"range": [1, 1]}],
        },
        "reviews": [{"chunk_number": 1, "candidates": compact_candidates, "ledger_decisions": []}],
    }
    compiled = compile_payload(video_id, compact_payload, status, transcript, {})
    assert compiled["issues"] == []
    assert compiled["candidate_count"] == 8
    assert compiled["reviews"][0]["candidates"][0]["evidence"]["minimal_quote"][0]["quote_verbatim"] == transcript[0]["text"]
    compact_bytes = len(json.dumps(compact_payload, ensure_ascii=False).encode("utf-8"))
    verbose_bytes = len(json.dumps(verbose_payload, ensure_ascii=False).encode("utf-8"))
    assert compact_bytes <= verbose_bytes * 0.4


def test_episode_level_compact_v2_hydrates_ids_reviews_and_verbatim_quotes(tmp_path):
    video_id = seed(tmp_path, "compact-v2")
    out = tmp_path / "processed" / video_id / "gold_extraction"
    status = load_json(out / "gold_extraction_status.json")
    transcript = load_json(out / "transcript_clean.json")["segments"]
    payload = {
        "payload_format": COMPACT_EPISODE_PAYLOAD_FORMAT,
        "episode_video_id": video_id,
        "segment_index_mode": "zero_based",
        "candidate_defaults": {
            "type": "framework", "themes": ["testing_measurement"],
            "reported_case": True, "causal_certainty": "reported_attribution", "claim_risk": "medium",
            "numbers": [structured_number()], "steps": ["Testar.", "Comparar."],
            "conditions": [], "caveats": ["Caso reportado."],
            "relations": {"parent_candidate_id": None, "child_candidate_ids": []},
        },
        "candidates": [{
            "chunk": 1,
            "title": "Testar desconto antes de escalar",
            "claim": "O entrevistado testa desconto antes de escalar.",
            "takeaway": "Teste a variante e compare o resultado antes de escalar o investimento.",
            "minimal": [0], "support": [1],
        }],
        "zero_insight_chunks": [],
    }
    compiled = compile_payload(video_id, payload, status, transcript, {})
    assert compiled["issues"] == []
    assert len(compiled["reviews"]) == 1
    hydrated = compiled["reviews"][0]["candidates"][0]
    assert hydrated["candidate_id"] == f"{video_id}-G001"
    assert hydrated["evidence"]["minimal_quote"][0]["quote_verbatim"] == transcript[0]["text"]


def test_episode_level_compact_v3_expands_to_v2_with_local_relations_and_verbatim_quotes(tmp_path):
    video_id = seed(tmp_path, "compact-v3")
    out = tmp_path / "processed" / video_id / "gold_extraction"
    status = load_json(out / "gold_extraction_status.json")
    transcript = load_json(out / "transcript_clean.json")["segments"]
    common = {
        "themes": ["testing_measurement"],
        "subthemes": [],
        "reported_case": False,
        "causal_certainty": "not_applicable",
        "claim_risk": "low",
        "conditions": [],
        "caveats": [],
    }
    v2 = {
        "payload_format": COMPACT_EPISODE_PAYLOAD_FORMAT,
        "episode_video_id": video_id,
        "candidate_defaults": common,
        "candidates": [
            {
                "chunk": 1,
                "candidate_id": f"{video_id}-G001",
                "title": "Medir o impacto do desconto antes de escalar a oferta",
                "type": "framework",
                "source_claim": "O entrevistado testa desconto antes de escalar.",
                "takeaway_applicavel": "Meca o impacto do desconto antes de escalar a oferta.",
                "minimal_segment_ids": [{"range": [0, 0]}],
                "support_segment_ids": [],
                "numbers": [structured_number()],
                "steps": ["Aplicar o desconto.", "Comparar o resultado."],
                "relations": {"parent_candidate_id": None, "child_candidate_ids": [f"{video_id}-G002"]},
            },
            {
                "chunk": 1,
                "candidate_id": f"{video_id}-G002",
                "title": "Comparar o resultado medido",
                "type": "playbook_step",
                "source_claim": "O entrevistado orienta medir e comparar o resultado.",
                "takeaway_applicavel": "Compare o resultado medido com o baseline.",
                "minimal_segment_ids": [{"range": [1, 1]}],
                "support_segment_ids": [],
                "numbers": [],
                "steps": ["Medir.", "Comparar."],
                "relations": {"parent_candidate_id": f"{video_id}-G001", "child_candidate_ids": []},
            },
        ],
        "zero_insight_chunks": [],
    }
    v3 = {
        "payload_format": COMPACT_EPISODE_PAYLOAD_FORMAT_V3,
        "episode_video_id": video_id,
        "d": {"th": ["testing_measurement"], "st": [], "rc": False, "cc": "not_applicable", "cr": "low", "co": [], "ca": []},
        "td": {
            "framework": {"p": ["Aplicar o desconto.", "Comparar o resultado."]},
            "playbook_step": {"p": ["Medir.", "Comparar."]},
        },
        "c": [
            {
                "id": f"{video_id}-G001", "a": "framework", "k": 1,
                "t": "Medir o impacto do desconto antes de escalar a oferta", "y": "framework",
                "cl": "O entrevistado testa desconto antes de escalar.",
                "ta": "Meca o impacto do desconto antes de escalar a oferta.", "m": [[0, 0]], "s": [],
                "n": [["20%", 20, None, None, "percent", "percent", None, "result", "reported"]],
                "rel": {"c": ["step"]},
            },
            {
                "id": f"{video_id}-G002", "a": "step", "k": 1,
                "t": "Comparar o resultado medido", "y": "playbook_step",
                "cl": "O entrevistado orienta medir e comparar o resultado.",
                "ta": "Compare o resultado medido com o baseline.", "m": [[1, 1]], "s": [],
                "n": [], "rel": {"p": "framework"},
            },
        ],
        "z": [],
    }
    compiled_v2 = compile_payload(video_id, v2, status, transcript, {})
    compiled_v3 = compile_payload(video_id, v3, status, transcript, {})
    assert compiled_v2["issues"] == []
    assert compiled_v3["issues"] == []
    assert compiled_v3["reviews"] == compiled_v2["reviews"]
    assert compiled_v3["reviews"][0]["candidates"][0]["evidence"]["minimal_quote"][0]["quote_verbatim"] == transcript[0]["text"]
    assert len(json.dumps(v3, ensure_ascii=False).encode("utf-8")) < len(json.dumps(v2, ensure_ascii=False).encode("utf-8"))


def test_compact_v3_copies_number_raw_from_selected_source_span(tmp_path):
    video_id = seed(tmp_path, "source-number")
    out = tmp_path / "processed" / video_id / "gold_extraction"
    status = load_json(out / "gold_extraction_status.json")
    transcript = load_json(out / "transcript_clean.json")["segments"]
    transcript[0]["text"] = "We interviewed 70 people before launch."
    payload = {
        "payload_format": COMPACT_EPISODE_PAYLOAD_FORMAT_V3,
        "episode_video_id": video_id,
        "d": {
            "y": "quantitative_case", "th": ["audience_market"], "st": [],
            "rc": True, "cc": "reported_attribution", "cr": "medium",
            "p": [], "co": [], "ca": ["Caso reportado; a amostra depende da fonte."],
            "rel": {"p": None, "c": []},
        },
        "c": [{
            "k": 1, "t": "Entrevistar a amostra antes do lancamento",
            "cl": "O entrevistado relata uma amostra de entrevistas antes do lancamento.",
            "ta": "Valide a mensagem com uma amostra antes de lancar.",
            "m": [[0, 0]], "s": [],
            "n": [{
                "si": 0, "sp": [15, 24], "v": 70, "lo": None, "hi": None,
                "k": "count", "u": "people", "p": None, "o": "capacity", "s": "reported",
            }],
        }],
        "z": [],
    }
    compiled = compile_payload(video_id, payload, status, transcript, {})
    assert compiled["issues"] == []
    number = compiled["reviews"][0]["candidates"][0]["numbers"][0]
    assert number["raw"] == "70 people"
    assert not ({"source_segment_id", "source_clean_index", "source_span", "source_occurrence"} & set(number))


def test_compiler_returns_complete_repair_scaffold_for_source_and_semantic_errors(tmp_path):
    video_id = seed(tmp_path, "repair-scaffold")
    out = tmp_path / "processed" / video_id / "gold_extraction"
    payload = review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id))
    payload["reviews"][0]["candidates"][0]["themes"] = ["unknown-theme"]
    payload["reviews"][0]["candidates"][0]["minimal_segment_ids"] = []
    compiled = compile_payload(
        video_id, payload,
        load_json(out / "gold_extraction_status.json"),
        load_json(out / "transcript_clean.json")["segments"],
        {},
    )
    fields = {item["field"] for item in compiled["repair_scaffold"]["issues"]}
    assert {"themes", "minimal_segment_ids"} <= fields
    assert compiled["repair_scaffold"]["issue_count"] == len(compiled["issues"])


def test_compact_jsonl_context_is_source_complete_and_smaller_than_slab_context(tmp_path):
    video_id = seed(tmp_path, "compact-context")
    compact = build_compact_reading_context(video_id, tmp_path)
    path = tmp_path / "job" / "episode_context.jsonl"
    identity = write_compact_reading_context(path, compact)
    transcript = load_json(tmp_path / "processed" / video_id / "gold_extraction" / "transcript_clean.json")["segments"]
    assert validate_compact_reading_context(path, transcript) == []
    assert identity["segment_count"] == len(transcript)
    assert compact["header"]["number_inventory"]
    assert compact["header"]["extraction_architecture"] == CANONICAL_EXTRACTION_ARCHITECTURE
    assert compact["header"]["draft_contract"]["semantic_authority"] == "complete_chronological_transcript"
    assert compact["header"]["draft_contract"]["blind_semantic_compiler"] == "research_only_not_a_production_route"
    assert compact["header"]["draft_contract"]["prelint_before_preview"] is True
    assert compact["header"]["draft_contract"]["procedural_types_requiring_steps"] == ["framework", "playbook_step", "script"]
    assert compact["header"]["semantic_route_map"]
    assert compact["header"]["risk_recall_index"] is not None
    assert compact["header"]["payload_format"] == COMPACT_EPISODE_PAYLOAD_FORMAT_V3
    assert compact["header"]["draft_contract"]["authoring_checklist"]["procedural"]
    body = path.read_text(encoding="utf-8")
    assert json.loads(body.splitlines()[0])["episode_video_id"] == video_id
    assert body.count("Testamos 20% de desconto antes de escalar.") == 1
    assert body.count("Primeiro mede, depois compara o resultado.") == 1
    assert all(body.count(item["text"]) == 1 for item in transcript)


def test_exact_source_duplicate_candidates_block_without_automatic_merge(tmp_path):
    video_id = seed(tmp_path, "exact-duplicate")
    first = finalizable_candidate(tmp_path, video_id)
    second = copy.deepcopy(first)
    second["candidate_id"] = f"{video_id}-G002"
    payload = review_payload(tmp_path, video_id, first)
    payload["reviews"][0]["candidates"].append(second)

    preview = inspect_episode_draft(video_id, tmp_path, payload)

    assert preview["status"] == "blocked"
    groups = preview["autocheck"]["exact_candidate_duplicates"]
    assert groups == exact_candidate_duplicate_groups([first, second])
    assert groups[0]["candidate_ids"] == [f"{video_id}-G001", f"{video_id}-G002"]
    assert any(
        item["category"] == "exact_candidate_duplicates"
        for item in preview["hard_blockers"]
    )


def test_runtime_manifest_keeps_blind_semantic_compiler_research_only():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads(
        (root / "scripts" / "gold_runtime_sync_manifest.json").read_text(encoding="utf-8")
    )
    expected = {
        "scripts/gold_semantic_compiler.py",
        "scripts/gold_semantic_adapter_benchmark.py",
        "scripts/gold_semantic_global_reducer.py",
        "scripts/gold_semantic_inventory.py",
    }

    assert set(manifest["research_only_files"]) == expected
    assert expected.isdisjoint(manifest["execution_files"])


def test_bootstrap_request_preflights_and_writes_one_run_manifest(tmp_path):
    video_id = seed(tmp_path, "bootstrap")
    job_dir = tmp_path / "job"
    result = bootstrap_episode({"video_id": video_id, "data_root": str(tmp_path), "job_dir": str(job_dir)})
    assert result["status"] == "ready"
    assert result["pending_chunks"] == [1]
    assert (job_dir / "episode_context.jsonl").exists()
    assert load_json(job_dir / "episode_run_manifest.json")["semantic_sha256"] == result["semantic_sha256"]


def test_reading_context_emits_every_segment_once_in_at_most_three_slabs(tmp_path, monkeypatch, capsys):
    video_id = seed(tmp_path)
    raw = tmp_path / "raw" / "youtube" / video_id
    segments = [
        {"start_seconds": index * 5, "duration_seconds": 5, "text": f"Segmento {index} com teste e resultado."}
        for index in range(130)
    ]
    write_json(raw / "metadata.json", {"youtube_video_id": video_id, "duration_seconds": 650, "transcript_status": "available"})
    write_json(raw / "transcript_original.json", {"youtube_video_id": video_id, "transcript_status": "available", "segments": segments})
    prepare_episode(video_id, tmp_path)

    context = build_reading_context(video_id, tmp_path, slab_count=3)
    emitted = [item["segment_id"] for slab in context["slabs"] for item in slab["segments"]]
    assert 1 <= len(context["slabs"]) <= 3
    assert len(emitted) == context["segment_count"] == 130
    assert len(set(emitted)) == 130
    assert any(slab["boundary_from_previous_slab"] for slab in context["slabs"][1:])

    output = tmp_path / "job" / "context.json"
    monkeypatch.setattr(sys, "argv", [
        "run_gold_episode_fast",
        "--video-id", video_id,
        "--data-root", str(tmp_path),
        "--context",
        "--output", str(output),
    ])
    assert fast_main() == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["status"] == "context_ready"
    assert summary["output"] == str(output)
    assert load_json(output)["model_context_bytes"] == context["model_context_bytes"]


def test_fast_runner_rejects_mnt_job_dir_when_runtime_is_wsl(monkeypatch):
    from scripts import run_gold_episode_fast as fast

    monkeypatch.setattr(fast, "_is_wsl", lambda: True)

    with pytest.raises(ValueError, match="Linux-native"):
        fast._validate_job_dir(Path("/mnt/c/Users/job"))


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


def test_source_canonical_patch_asserts_ignore_derived_fields_and_detect_source_drift(tmp_path):
    video_id = seed(tmp_path, "source-assert")
    record(video_id, tmp_path, review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id)))
    out = tmp_path / "processed" / video_id / "gold_extraction"
    review_path = out / "manual_reviews" / "chunk_001_review.json"
    review = load_json(review_path)
    review["candidates"][0]["numbers"][0]["legacy_value"] = 20
    write_json(review_path, review)
    before = file_snapshot(out)
    replacement = copy.deepcopy(review["candidates"][0]["numbers"])
    replacement[0]["role"] = "baseline"
    intent = {
        "episode_video_id": video_id,
        "revision_id": "source-canonical-001",
        "revision_kind": "audit_remediation",
        "reason": "Correct the source-backed numeric role.",
        "updates": [{
            "candidate_id": f"{video_id}-G001",
            "assert_paths": ["numbers"],
            "set": {"numbers": replacement},
        }],
    }

    manifest = generate_source_assert_manifest(video_id, tmp_path, intent)

    assert file_snapshot(out) == before
    assert manifest["assertion_mode"] == "source_canonical"
    assert "legacy_value" not in manifest["updates"][0]["assert"]["numbers"][0]
    assert "legacy_value" not in manifest["updates"][0]["set"]["numbers"][0]
    checked = apply_patch(video_id, tmp_path, manifest, apply=False)
    assert checked["mode"] == "check"
    changed = load_json(review_path)
    changed["candidates"][0]["numbers"][0]["role"] = "target"
    write_json(review_path, changed)
    with pytest.raises(ValueError, match="current_source"):
        apply_patch(
            video_id, tmp_path, manifest, apply=True,
            preview_receipt=checked["preview"],
        )
    write_json(review_path, review)
    applied = apply_patch(
        video_id, tmp_path, manifest, apply=True,
        preview_receipt=checked["preview"],
    )
    assert applied["mode"] == "apply"
    final = load_json(review_path)["candidates"][0]["numbers"][0]
    assert final["role"] == "baseline"
    assert "legacy_value" not in final


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


def test_risk_recall_surfaces_three_historical_omission_patterns():
    texts = [
        "A velocidade de reproducao pode mudar a conversao.",
        "A substancia do argumento e mais importante do que a estrutura.",
        "A qualidade do sono exige um teste rapido de avaliacao.",
    ]
    transcript = [
        {"segment_id": f"risk-transcript-{index:04d}", "clean_index": index * 3, "start_seconds": index * 10, "duration_seconds": 5, "text": text}
        for index, text in enumerate(texts)
    ]
    signals = [
        {"segment_id": transcript[0]["segment_id"], "clean_index": 0, "signal_types": ["comparison", "experiment"]},
        {"segment_id": transcript[1]["segment_id"], "clean_index": 3, "signal_types": ["warning", "comparison"]},
        {"segment_id": transcript[2]["segment_id"], "clean_index": 6, "signal_types": ["procedure", "warning"]},
    ]
    decisions = [{"segment_id": item["segment_id"], "disposition": "excluded", "reason_code": "low_signal"} for item in transcript]
    clusters = excluded_risk_clusters(transcript, signals, decisions)
    assert len(clusters) == 3
    assert all(item["score"] >= 8 for item in clusters)
    assert {item["clean_index_range"][0] for item in clusters} == {0, 3, 6}


def test_risk_recall_residual_keeps_source_lineage_after_partial_coverage():
    transcript = [
        {"segment_id": f"episode-transcript-{index:04d}", "clean_index": index, "start_seconds": index * 5, "duration_seconds": 5, "text": text}
        for index, text in enumerate([
            "Teste rapido de uma hipotese.",
            "A promocao apenas repete a ideia.",
            "A promocao continua sem nova proposicao.",
        ], 1)
    ]
    signals = [
        {"segment_id": item["segment_id"], "clean_index": item["clean_index"], "signal_types": ["experiment", "warning"]}
        for item in transcript
    ]
    decisions = [
        {"segment_id": item["segment_id"], "disposition": "excluded", "reason_code": "low_signal"}
        for item in transcript
    ]
    source = excluded_risk_clusters(transcript, signals, decisions, threshold=1)
    residual = excluded_risk_clusters(
        transcript,
        signals,
        decisions,
        covered_segment_ids={transcript[0]["segment_id"]},
        source_clusters=source,
        threshold=1,
    )
    assert len(source) == len(residual) == 1
    assert residual[0]["cluster_id"] != source[0]["cluster_id"]
    assert residual[0]["source_cluster_id"] == source[0]["source_cluster_id"]
    assert residual[0]["source_segment_ids"] == source[0]["segment_ids"]
    assert residual[0]["residual_segment_ids"] == [item["segment_id"] for item in transcript[1:]]


def test_risk_recall_does_not_inherit_lineage_for_new_material_segment():
    source = [{
        "cluster_id": "risk-source",
        "source_cluster_id": "risk-source",
        "source_segment_ids": ["episode-transcript-0001"],
        "source_semantic_sha256": "source-hash",
    }]
    transcript = [{
        "segment_id": "episode-transcript-0002",
        "clean_index": 2,
        "start_seconds": 10,
        "duration_seconds": 5,
        "text": "O teste novo gerou 30% de aumento.",
    }]
    signals = [{"segment_id": "episode-transcript-0002", "clean_index": 2, "signal_types": ["number", "experiment", "comparison"]}]
    decisions = [{"segment_id": "episode-transcript-0002", "disposition": "excluded", "reason_code": "low_signal"}]
    residual = excluded_risk_clusters(transcript, signals, decisions, source_clusters=source)
    assert residual[0]["source_cluster_id"] == residual[0]["cluster_id"]
    assert residual[0]["source_cluster_id"] != "risk-source"


def test_risk_recall_prefers_scoped_residual_acknowledgement_over_source_disposition():
    cluster = {
        "cluster_id": "risk-residual-new",
        "source_cluster_id": "risk-source",
        "source_segment_ids": ["s1", "s2", "s3", "s4"],
        "residual_segment_ids": ["s3"],
    }
    acknowledgements = [
        {"cluster_id": "risk-source", "disposition": "retained_support", "justification": "Support retained."},
        {
            "cluster_id": "risk-residual-old",
            "source_cluster_id": "risk-source",
            "source_segment_ids": ["s2", "s3"],
            "disposition": "incidental",
            "justification": "Residual promotion only.",
        },
    ]
    selected = _risk_acknowledgement_for(cluster, acknowledgements)
    assert selected["cluster_id"] == "risk-residual-old"
    new_material = {**cluster, "residual_segment_ids": ["s3", "s5"]}
    assert _risk_acknowledgement_for(new_material, acknowledgements) is None


def test_compact_v2_requires_explicit_risk_acknowledgement(tmp_path, monkeypatch):
    video_id = seed(tmp_path, "risk-ack")
    payload = {
        "payload_format": COMPACT_EPISODE_PAYLOAD_FORMAT,
        "episode_video_id": video_id,
        "candidates": [{
            "chunk": 1, **{key: value for key, value in finalizable_candidate(tmp_path, video_id).items() if key not in {"candidate_id", "chunk_id"}},
        }],
        "zero_insight_chunks": [],
    }
    monkeypatch.setattr("scripts.gold_review_autocheck.excluded_risk_clusters", lambda *args, **kwargs: [{
        "cluster_id": "risk-required", "segment_ids": [f"{video_id}-transcript-0002"], "score": 9,
    }])
    blocked = inspect_episode_draft(video_id, tmp_path, payload)
    assert any(item["category"] == "risk_recall_unreviewed" for item in blocked["hard_blockers"])
    payload["risk_recall_acknowledgements"] = [{
        "cluster_id": "risk-required",
        "disposition": "incidental",
        "justification": "O trecho apenas repete o procedimento capturado.",
        "source_segment_ids": [f"{video_id}-transcript-0002"],
    }]
    ready = inspect_episode_draft(video_id, tmp_path, payload)
    assert not any(item["category"] == "risk_recall_unreviewed" for item in ready["hard_blockers"])


def test_compact_v2_fixed_point_requires_retained_support_acknowledgement(tmp_path, monkeypatch):
    video_id = seed(tmp_path, "risk-fixed-point")
    payload = {
        "payload_format": COMPACT_EPISODE_PAYLOAD_FORMAT,
        "episode_video_id": video_id,
        "candidates": [{
            "chunk": 1,
            **{key: value for key, value in finalizable_candidate(tmp_path, video_id).items() if key not in {"candidate_id", "chunk_id"}},
        }],
        "zero_insight_chunks": [],
    }
    cluster = {"cluster_id": "risk-support-only", "segment_ids": [f"{video_id}-transcript-0002"], "score": 9}
    monkeypatch.setattr("scripts.run_gold_episode_fast._fixed_point_risk_clusters", lambda *args, **kwargs: [cluster])
    blocked = inspect_episode_draft(video_id, tmp_path, payload)
    assert blocked["stopped_at"] == "review_gate"
    assert blocked["prelint_inventory"]["fixed_point_risk_clusters"] == [cluster]
    payload["risk_recall_acknowledgements"] = [{
        "cluster_id": "risk-support-only",
        "disposition": "retained_support",
        "justification": "O suporte preserva a condicao que completa a proposicao principal.",
    }]
    ready = inspect_episode_draft(video_id, tmp_path, payload)
    assert not ready["prelint_inventory"]["review_gate"]


def test_audit_warning_review_has_stable_id_and_requires_disposition():
    warnings = [{"category": "claim_evidence_alignment", "kind": "audit_warning", "items": [{
        "candidate_id": "episode-G001", "issue": "claim has no meaningful lexical support in minimal evidence",
        "source_claim": "A parafrase editorial completa.",
        "minimal_quote": ["A citacao literal da fonte."],
    }]}]
    reviewed, inventory, unresolved = review_audit_warnings(
        warnings, required_categories={"claim_evidence_alignment"},
    )
    assert reviewed[0]["items"][0]["warning_id"] == inventory[0]["warning_id"]
    assert inventory[0]["evidence"]["minimal_quote"] == ["A citacao literal da fonte."]
    assert unresolved[0]["warning_id"] == inventory[0]["warning_id"]
    disposition = [{
        "warning_id": inventory[0]["warning_id"],
        "disposition": "defer_to_final_audit",
        "justification": "A citacao e verbatim; a equivalencia parafraseada deve permanecer visivel ao auditor final.",
    }]
    reviewed, inventory, unresolved = review_audit_warnings(
        warnings, disposition, required_categories={"claim_evidence_alignment"},
    )
    assert unresolved == []
    assert reviewed[0]["items"][0]["review"]["disposition"] == "defer_to_final_audit"


def test_semantic_closure_surfaces_adjacent_tail_episode_tail_and_containment():
    video_id = "closure"
    transcript = [
        {"segment_id": f"{video_id}-transcript-{index + 1:04d}", "clean_index": index, "text": text}
        for index, text in enumerate([
            "Introducao.", "A tese principal.", "Primeiro passo.", "Segundo passo.",
            "Tambem use este formato.", "Fechamento da unidade.", "Fim do episodio.",
        ])
    ]
    chunks = [{
        "chunk_id": "closure-gold-chunk-001", "first_segment_id": transcript[0]["segment_id"],
        "last_segment_id": transcript[-1]["segment_id"],
    }]
    candidates = [
        {
            "candidate_id": "closure-G010",
            "evidence": {
                "minimal_quote": [{"segment_id": transcript[1]["segment_id"]}],
                "support_segments": [{"segment_id": transcript[2]["segment_id"]}],
            },
            "relations": {"parent_candidate_id": None, "child_candidate_ids": []},
        },
        {
            "candidate_id": "closure-G011",
            "evidence": {
                "minimal_quote": [{"segment_id": transcript[2]["segment_id"]}],
                "support_segments": [],
            },
            "relations": {"parent_candidate_id": None, "child_candidate_ids": []},
        },
    ]
    signals = [{"segment_id": transcript[4]["segment_id"], "signal_types": ["procedure"]}]
    closure = semantic_closure_index(transcript, chunks, candidates, signals)
    kinds = {item["closure_kind"] for item in closure}
    assert "adjacent_evidence_tail" in kinds
    assert "episode_tail" in kinds
    assert any(item["closure_kind"] == "evidence_containment" and item["candidate_ids"] == ["closure-G010", "closure-G011"] for item in closure)


def test_semantic_closure_reproduces_pilot_006_adjacent_ranges():
    video_id = "pilot006"
    transcript = [
        {"segment_id": f"{video_id}-transcript-{index + 1:04d}", "clean_index": index, "text": f"Segment {index}."}
        for index in range(930)
    ]
    candidates = [
        {
            "candidate_id": f"{video_id}-G014",
            "evidence": {"minimal_quote": [{"segment_id": transcript[762]["segment_id"]}], "support_segments": []},
            "relations": {"parent_candidate_id": None, "child_candidate_ids": []},
        },
        {
            "candidate_id": f"{video_id}-G020",
            "evidence": {"minimal_quote": [{"segment_id": transcript[912]["segment_id"]}], "support_segments": []},
            "relations": {"parent_candidate_id": None, "child_candidate_ids": []},
        },
    ]
    signals = [
        {"segment_id": transcript[index]["segment_id"], "signal_types": ["procedure"]}
        for index in [*range(763, 771), *range(913, 924)]
    ]
    closure = semantic_closure_index(transcript, [], candidates, signals)
    ranges = {
        tuple(item["clean_index_range"])
        for item in closure if item["closure_kind"] == "adjacent_evidence_tail"
    }
    assert (763, 770) in ranges
    assert (913, 923) in ranges


def test_semantic_closure_incidental_requires_nonempty_justification():
    warnings = [{"category": "semantic_closure", "kind": "audit_warning", "items": [{
        "closure_kind": "adjacent_evidence_tail", "candidate_ids": ["episode-G001"],
        "segment_ids": ["episode-transcript-0002"], "issue": "adjacent_evidence_tail",
    }]}]
    _, inventory, unresolved = review_audit_warnings(warnings, required_categories={"semantic_closure"})
    assert unresolved
    warning_id = inventory[0]["warning_id"]
    _, _, still_unresolved = review_audit_warnings(warnings, [{
        "warning_id": warning_id, "disposition": "incidental", "justification": "",
    }], required_categories={"semantic_closure"})
    assert still_unresolved
    _, _, resolved = review_audit_warnings(warnings, [{
        "warning_id": warning_id, "disposition": "incidental",
        "justification": "O trecho apenas encerra a fala e nao acrescenta uma proposicao reutilizavel.",
        "source_segment_ids": ["episode-transcript-0002"],
    }], required_categories={"semantic_closure"})
    assert resolved == []


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


@pytest.mark.parametrize("text", ["Ela virou uma lead qualificada.", "Ele vende um produto digital."])
def test_autocheck_does_not_treat_portuguese_articles_as_material_counts(tmp_path, text):
    video_id = seed(tmp_path)
    record(video_id, tmp_path, review_payload(tmp_path, video_id))
    path = tmp_path / "processed" / video_id / "gold_extraction" / "manual_reviews" / "chunk_001_review.json"
    review = load_json(path)
    review["candidates"][0]["numbers"] = []
    review["candidates"][0]["evidence"]["minimal_quote"][0]["quote_verbatim"] = text
    review["candidates"][0]["evidence"]["support_segments"] = []
    write_json(path, review)

    report = autocheck(video_id, tmp_path)

    assert not any(item["candidate_id"] == f"{video_id}-G001" for item in report["numbers"])


def _numeric_candidate(text, numbers, *, candidate_type="quantitative_case", support_text=None):
    item = candidate("numeric", "numeric-gold-chunk-001")
    item["type"] = candidate_type
    item["source_claim"] = text
    item["takeaway_applicavel"] = "Preserve cada valor material da comparacao."
    item["numbers"] = numbers
    item["caveats"] = ["Caso reportado; a leitura numerica depende do contexto da fonte."]
    item["evidence"] = {
        "minimal_quote": [{"segment_id": "numeric-transcript-0001", "quote_verbatim": text}],
        "support_segments": (
            [{"segment_id": "numeric-transcript-0002", "quote_verbatim": support_text}]
            if support_text else []
        ),
    }
    return item


def _number(raw, value, unit_kind="percent", role="result", value_status="reported"):
    return {
        "raw": raw, "value": value, "min_value": None, "max_value": None,
        "unit_kind": unit_kind, "unit": unit_kind, "period": None,
        "role": role, "value_status": value_status, "denominator": None,
        "attribution_window": None,
    }


def test_numeric_coverage_blocks_material_percentage_omitted_after_partial_capture():
    item = _numeric_candidate(
        "O resultado saiu de 20% para 35%.",
        [_number("20%", 20, role="baseline")],
    )
    coverage = candidate_numeric_coverage(
        item, {"numeric-transcript-0001": {"number", "comparison"}},
    )
    assert coverage["status"] == "blocked"
    assert [entry["raw"] for entry in coverage["missing_material"]] == ["35%"]
    assert coverage["mentions"][0]["record"]["role"] == "baseline"


def test_numeric_coverage_preserves_repeated_quantitative_sequence_multiplicity():
    text = "A taxa saiu de 40% para 35% e depois voltou a 40%."
    partial = _numeric_candidate(text, [
        _number("40%", 40, role="baseline"),
        _number("35%", 35, role="result"),
    ])
    blocked = candidate_numeric_coverage(
        partial, {"numeric-transcript-0001": {"number", "comparison", "test_result"}},
    )
    assert [entry["raw"] for entry in blocked["missing_material"]] == ["40%"]
    complete = copy.deepcopy(partial)
    complete["numbers"].append(_number("40%", 40, role="result"))
    assert candidate_numeric_coverage(
        complete, {"numeric-transcript-0001": {"number", "comparison", "test_result"}},
    )["status"] == "pass"


def test_numeric_mentions_treats_portuguese_dot_as_thousands_separator():
    assert numeric_mentions("O caso reportou R$ 500.000 por mes.")[0]["canonical"] == "500000"
    item = _numeric_candidate(
        "O caso reportou R$ 500.000 por mes.",
        [_number("R$ 500.000", 500_000, unit_kind="currency")],
    )
    assert candidate_numeric_coverage(
        item, {"numeric-transcript-0001": {"number", "test_result"}},
    )["status"] == "pass"


def test_numeric_mentions_applies_adjacent_k_suffix_multiplier():
    assert numeric_mentions("O investimento foi 16k.")[0]["canonical"] == "16:k"
    item = _numeric_candidate(
        "O investimento foi 16k.",
        [_number("16k", 16_000, unit_kind="currency", role="budget")],
    )
    assert candidate_numeric_coverage(
        item, {"numeric-transcript-0001": {"number", "test_result"}},
    )["status"] == "pass"


def test_numeric_coverage_requires_inferred_caveated_asr_decimal_and_separate_ratio():
    text = "A conversao chegou a 86,8 5% e ficou 1.2x maior."
    assert [item["canonical"] for item in numeric_mentions(text)] == ["86.85", "1.2"]
    complete = _numeric_candidate(text, [
        _number("86,8 5%", 86.85, value_status="inferred"),
        _number("1.2x", 1.2, unit_kind="ratio"),
    ])
    coverage = candidate_numeric_coverage(
        complete, {"numeric-transcript-0001": {"number", "comparison", "test_result"}},
    )
    assert coverage["status"] == "pass"
    assert any(item["disposition"] == "covered_asr_ambiguous" for item in coverage["audit_warnings"])
    broken = copy.deepcopy(complete)
    broken["numbers"][0]["value_status"] = "reported"
    broken["caveats"] = []
    assert candidate_numeric_coverage(
        broken, {"numeric-transcript-0001": {"number", "comparison", "test_result"}},
    )["status"] == "blocked"


def test_numeric_coverage_binds_literal_portuguese_word_ratio():
    text = "A conversao aumentou quatro vezes."
    assert numeric_mentions(text) == [{
        "raw": "quatro vezes",
        "kind": "ratio",
        "canonical": "quatro vezes",
        "asr_separated_decimal": False,
        "start": 21,
        "end": 33,
    }]
    complete = _numeric_candidate(text, [
        _number("quatro vezes", 4, unit_kind="ratio"),
    ])
    coverage = candidate_numeric_coverage(
        complete, {"numeric-transcript-0001": {"number", "comparison", "test_result"}},
    )
    assert coverage["status"] == "pass"
    assert coverage["covered_record_indexes"] == [0]


def test_numeric_coverage_keeps_incidental_support_number_as_warning():
    item = _numeric_candidate(
        "A equipe documentou a rotina operacional.", [],
        candidate_type="tactic", support_text="O exemplo ocorreu durante 3 meses.",
    )
    coverage = candidate_numeric_coverage(
        item, {"numeric-transcript-0002": {"number"}},
    )
    assert coverage["status"] == "pass"
    assert coverage["missing_material"] == []
    assert [item["raw"] for item in coverage["audit_warnings"]] == ["3 meses"]


@pytest.mark.parametrize("text", ["Ela conseguiu uma unica venda.", "Ela conseguiu apenas uma venda.", "Ela conseguiu duas vendas."])
def test_autocheck_keeps_unambiguous_word_counts_material(tmp_path, text):
    video_id = seed(tmp_path)
    record(video_id, tmp_path, review_payload(tmp_path, video_id))
    path = tmp_path / "processed" / video_id / "gold_extraction" / "manual_reviews" / "chunk_001_review.json"
    review = load_json(path)
    review["candidates"][0]["numbers"] = []
    review["candidates"][0]["evidence"]["minimal_quote"][0]["quote_verbatim"] = text
    review["candidates"][0]["evidence"]["support_segments"] = []
    write_json(path, review)

    report = autocheck(video_id, tmp_path)

    assert any(item["candidate_id"] == f"{video_id}-G001" for item in report["numbers"])


def test_sparse_recall_view_omits_empty_inventories_and_preserves_real_issues(tmp_path):
    video_id = seed(tmp_path)
    record(video_id, tmp_path, review_payload(tmp_path, video_id))
    report = autocheck(video_id, tmp_path)

    sparse = sparse_recall_view(report)

    assert sparse["hard_blockers"] == report["hard_blockers"]
    assert "numbers" in sparse["inventories"]
    assert all(sparse["inventories"].values())
    assert "candidate_with_promo_or_interviewer_language" not in sparse["inventories"]


def test_prelint_cli_summary_is_bounded_and_exposes_pending_acknowledgements(tmp_path):
    cluster = {
        "cluster_id": "risk-residual",
        "source_cluster_id": "risk-source",
        "clean_index_range": [10, 20],
        "segment_ids": [f"episode-transcript-{index:04d}" for index in range(10, 21)],
        "residual_segment_ids": [f"episode-transcript-{index:04d}" for index in range(14, 21)],
        "exclusion_reasons": ["low_signal"],
        "text": "texto repetido " * 10_000,
    }
    result = {
        "status": "needs_revision",
        "mode": "prelint",
        "stopped_at": "autocheck",
        "episode_video_id": "episode",
        "hard_blockers": [{"category": "risk_recall_unreviewed", "kind": "hard_blocker", "items": [cluster]}],
        "audit_warnings": [{"category": "promo_or_interviewer", "kind": "audit_warning", "items": [{"candidate_id": f"episode-G{index:03d}", "text": "x" * 2000} for index in range(20)]}],
        "prelint_inventory": {"review_gate": [], "evidence_scope_warnings": []},
        "autocheck": {"calibration": {"status": "pass", "covered_count": 6, "minimum_required": 6}},
        "metrics": {"candidate_count": 17, "final_review_count": 9},
    }
    output = tmp_path / "prelint.json"
    compact = compact_cli_result(result, output_path=output, max_bytes=8192)
    encoded = json.dumps(compact, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    assert len(encoded) <= 8192
    assert compact["full_report"] == str(output)
    assert compact["pending_acknowledgements"][0]["cluster_id"] == "risk-residual"
    assert compact["pending_acknowledgements"][0]["source_cluster_id"] == "risk-source"
    assert compact["pending_acknowledgements"][0]["source_segment_ids"] == cluster["residual_segment_ids"]
    assert "text" not in json.dumps(compact, ensure_ascii=False)


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


def test_finalizer_carries_reviewed_warning_into_packet(tmp_path, monkeypatch):
    video_id = seed(tmp_path, "reviewed-warning")
    record(video_id, tmp_path, review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id)))
    warning = [{"category": "claim_evidence_alignment", "kind": "audit_warning", "items": [{
        "candidate_id": f"{video_id}-G001", "issue": "claim has no meaningful lexical support in minimal evidence",
    }]}]
    _, inventory, _ = review_audit_warnings(warning, required_categories={"claim_evidence_alignment"})
    dispositions = [{
        "warning_id": inventory[0]["warning_id"],
        "disposition": "confirmed_source_backed",
        "justification": "A citacao literal e o contexto sustentam a parafrase editorial.",
    }]
    from scripts import finalize_gold_episode as finalizer
    real_autocheck = finalizer.autocheck

    def warning_autocheck(*args, **kwargs):
        report = real_autocheck(*args, **kwargs)
        report["audit_warnings"] = warning
        return report

    monkeypatch.setattr(finalizer, "autocheck", warning_autocheck)
    result = finalize_episode(
        video_id,
        tmp_path,
        export_suffix="reviewed-warning-packet",
        revision_id="reviewed-warning-001",
        audit_warning_dispositions=dispositions,
        require_warning_dispositions=True,
    )
    assert result["status"] == "ready"
    assert result["audit_warnings"][0]["items"][0]["review"]["disposition"] == "confirmed_source_backed"
    manifest = load_json(Path(result["packet"]) / "packet_manifest.json")
    assert manifest["audit_warnings"] == result["audit_warnings"]


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
    assert fresh["status"] == "ready", fresh
    assert fresh["revision_id"] == "revision-two"


def test_finalizer_rederives_ledger_after_review_change_without_manual_cleanup(tmp_path):
    video_id = seed(tmp_path, "rederive-ledger")
    record(video_id, tmp_path, review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id)))
    first = finalize_episode(video_id, tmp_path, export_suffix="rederive-packet", revision_id="revision-one")
    assert first["status"] == "ready"
    out = tmp_path / "processed" / video_id / "gold_extraction"
    ledger_path = out / "high_signal_coverage_ledger.json"
    assert next(item for item in load_json(ledger_path)["entries"] if item["segment_id"].endswith("0002"))["disposition"] == "captured"

    review_path = out / "manual_reviews" / "chunk_001_review.json"
    review = load_json(review_path)
    review["ledger_decisions"] = [{
        "segment_id": f"{video_id}-transcript-0002",
        "disposition": "merged",
        "candidate_ids": [f"{video_id}-G001"],
    }]
    write_json(review_path, review)

    fresh = finalize_episode(video_id, tmp_path, export_suffix="rederive-packet", revision_id="revision-two")
    assert fresh["status"] == "ready", fresh
    rebuilt = next(item for item in load_json(ledger_path)["entries"] if item["segment_id"].endswith("0002"))
    assert rebuilt["disposition"] == "merged"
    assert rebuilt["candidate_ids"] == [f"{video_id}-G001"]


def test_fast_route_rejects_legacy_insight_content_but_context_only_fingerprints_remain(tmp_path):
    video_id = seed(tmp_path, "source-only")
    payload = review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id))
    payload["legacy_insights"] = load_json(tmp_path / "processed" / video_id / "insights_v2.json")
    report = inspect_episode_draft(video_id, tmp_path, payload)
    assert report["status"] == "blocked"
    assert report["stopped_at"] == "source_policy"
    assert report["issues"][0]["category"] == "legacy_context_forbidden"
    context = build_reading_context(video_id, tmp_path)
    assert context["legacy_content_reads"] == 0
    assert context["model_context_bytes"] > 0


def test_fast_session_uses_wall_clock_across_processes_and_durable_counts(tmp_path):
    job_dir = tmp_path / "session"
    _record_session_event(job_dir, "episode", "preflight_and_context", {"context_ms": 1})
    path = job_dir / "episode_fast_session.json"
    session = load_json(path)
    session["started_monotonic_ns"] = 2**63
    write_json(path, session)
    _record_session_event(job_dir, "episode", "preview", {"compile_ms": 1})
    current = load_json(path)
    assert current["events"][-1]["elapsed_since_preflight_ms"] >= 0
    assert current["operation_counts"] == {"checks": 1, "context_generations": 1}


def test_session_performance_separates_command_time_from_judgment_and_tracks_bytes():
    session = {
        "events": [
            {
                "phase": "preflight_and_context",
                "elapsed_since_previous_event_ms": 2000,
                "metrics": {"context_ms": 100, "context_bytes": 83_000},
            },
            {
                "phase": "prelint",
                "elapsed_since_previous_event_ms": 8000,
                "metrics": {"total_ms": 60, "payload_bytes": 31_600, "full_result_bytes": 155_000},
            },
            {
                "phase": "apply_and_finalize",
                "elapsed_since_previous_event_ms": 1000,
                "metrics": {"total_ms": 500, "audit_dossier_bytes": 42_000},
            },
        ]
    }
    result = _session_performance(session, 11_000)
    assert result["deterministic_command_ms"] == 660
    assert result["active_wall_ms"] == 660
    assert result["judgment_and_orchestration_ms"] == 0
    assert result["phase_transition_ms"] == 10_340
    assert result["inter_turn_idle_ms"] == 0
    assert result["artifact_bytes"] == {
        "context": 83_000,
        "payload": 31_600,
        "prelint_report": 155_000,
        "audit_dossier": 42_000,
    }
    assert result["phase_wall_ms"]["prelint"] == 60


def test_session_event_records_synthetic_pause_as_unattributed_not_prelint(tmp_path):
    job_dir = tmp_path / "telemetry-job"
    job_dir.mkdir()
    write_json(job_dir / "episode_fast_session.json", {
        "schema_version": "1.3.0",
        "episode_video_id": "episode",
        "started_at": "2026-07-16T12:00:00+00:00",
        "epic_started_at": "2026-07-16T12:00:00+00:00",
        "events": [{
            "phase": "preflight_and_context",
            "recorded_at": "2026-07-16T12:00:01+00:00",
            "started_at": "2026-07-16T12:00:00+00:00",
            "completed_at": "2026-07-16T12:00:01+00:00",
            "active_wall_ms": 1000,
            "runtime_command_ms": 1000,
            "model_judgment_ms": 0,
            "inter_turn_idle_ms": 0,
            "phase_transition_ms": 0,
            "metrics": {"context_ms": 1000},
        }],
        "operation_counts": {},
    })

    _record_session_event(
        job_dir, "episode", "prelint", {"total_ms": 100},
        started_at="2026-07-16T12:05:00+00:00",
        completed_at="2026-07-16T12:05:00.100000+00:00",
    )

    session = load_json(job_dir / "episode_fast_session.json")
    event = session["events"][-1]
    assert event["active_wall_ms"] == 100
    assert event["inter_turn_idle_ms"] == 0
    assert event["unattributed_gap_ms"] == 299_000
    assert event["phase_transition_ms"] == 0
    performance = _session_performance(session, 300_100)
    assert performance["phase_wall_ms"]["prelint"] == 100
    assert performance["inter_turn_idle_ms"] == 0
    assert performance["unattributed_wall_ms"] == 299_000


def test_semantic_spans_reconcile_model_work_inside_command_gaps(tmp_path, monkeypatch):
    job_dir = tmp_path / "semantic-spans"
    timestamps = iter([
        "2026-07-16T12:00:00+00:00",
        "2026-07-16T12:01:00+00:00",
        "2026-07-16T12:03:00+00:00",
    ])
    monkeypatch.setattr("scripts.run_gold_episode_fast._utc_now", lambda: next(timestamps))
    mark_semantic_phase(job_dir, "episode", "semantic_reading_and_authoring", "start")
    mark_semantic_phase(job_dir, "episode", "semantic_reading_and_authoring", "end")
    session = load_json(job_dir / "episode_fast_session.json")
    performance = _session_performance(session, 120_000)
    assert performance["semantic_wall_ms"] == 120_000
    assert performance["semantic_phase_wall_ms"]["semantic_reading_and_authoring"] == 120_000
    assert performance["wall_reconciliation_delta_ms"] == 0


def test_runtime_sync_is_no_delete_and_blocks_bilateral_drift(tmp_path):
    source = tmp_path / "windows"
    destination = tmp_path / "linux"
    source.mkdir()
    destination.mkdir()
    (source / "runtime.py").write_text("print('one')\n", encoding="utf-8")
    (destination / "unrelated.txt").write_text("keep\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    receipt = tmp_path / "receipt.json"
    write_json(manifest, {"schema_version": "1.0.0", "files": ["runtime.py"]})
    first = synchronize_runtime(source, destination, manifest, receipt)
    assert first["status"] == "pass"
    assert (destination / "unrelated.txt").read_text(encoding="utf-8") == "keep\n"
    assert validate_runtime_parity_receipt(receipt, destination, manifest) == []

    (source / "runtime.py").write_text("print('two')\n", encoding="utf-8")
    assert any("source changed" in error for error in validate_runtime_parity_receipt(receipt, destination, manifest))
    (destination / "runtime.py").write_text("print('linux edit')\n", encoding="utf-8")
    blocked = synchronize_runtime(source, destination, manifest, receipt)
    assert blocked["status"] == "blocked"
    assert blocked["conflicts"][0]["reason"] == "destination_drift"


def test_runtime_sync_reuses_valid_receipt_without_rewrite(tmp_path):
    source = tmp_path / "windows"
    destination = tmp_path / "linux"
    source.mkdir()
    destination.mkdir()
    (source / "runtime.py").write_text("print('one')\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    receipt = tmp_path / "receipt.json"
    write_json(manifest, {"schema_version": "1.0.0", "files": ["runtime.py"]})
    synchronize_runtime(source, destination, manifest, receipt)
    before = (receipt.stat().st_mtime_ns, receipt.read_bytes())
    reused = synchronize_runtime(source, destination, manifest, receipt, reuse_valid=True)
    assert reused["status"] == "pass" and reused["read_only"] is True and reused["reused"] is True
    assert (receipt.stat().st_mtime_ns, receipt.read_bytes()) == before


def test_runtime_parity_blocks_execution_drift_but_not_documentation_drift(tmp_path):
    source = tmp_path / "windows"
    destination = tmp_path / "linux"
    (source / "docs").mkdir(parents=True)
    destination.mkdir()
    (source / "runtime.py").write_text("print('one')\n", encoding="utf-8")
    (source / "docs" / "plan.md").write_text("planned\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    receipt = tmp_path / "receipt.json"
    write_json(manifest, {
        "schema_version": "1.1.0",
        "files": ["runtime.py", "docs/plan.md"],
        "execution_files": ["runtime.py"],
    })
    synchronized = synchronize_runtime(source, destination, manifest, receipt)
    assert synchronized["status"] == "pass"
    parity = load_json(receipt)
    assert parity["execution_signature"]
    assert parity["documentation_signature"]

    (source / "docs" / "plan.md").write_text("implemented\n", encoding="utf-8")
    assert validate_runtime_parity_receipt(receipt, destination, manifest) == []

    (source / "runtime.py").write_text("print('two')\n", encoding="utf-8")
    assert any(
        "runtime source changed" in error
        for error in validate_runtime_parity_receipt(receipt, destination, manifest)
    )


def test_job_runtime_snapshot_ignores_later_source_drift_but_blocks_linux_mutation(tmp_path):
    source = tmp_path / "windows"
    destination = tmp_path / "linux"
    job_dir = tmp_path / "job"
    source.mkdir()
    destination.mkdir()
    (source / "runtime.py").write_text("print('one')\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    receipt = tmp_path / "receipt.json"
    write_json(manifest, {"schema_version": "1.1.0", "files": ["runtime.py"], "execution_files": ["runtime.py"]})
    synchronize_runtime(source, destination, manifest, receipt)
    pinned, errors = _validate_or_pin_runtime_snapshot(job_dir, receipt, manifest, destination)
    assert errors == [] and pinned == job_dir / "runtime_snapshot_receipt.json"

    (source / "runtime.py").write_text("print('next run')\n", encoding="utf-8")
    _, errors = _validate_or_pin_runtime_snapshot(job_dir, receipt, manifest, destination)
    assert errors == []

    (destination / "runtime.py").write_text("print('mutated snapshot')\n", encoding="utf-8")
    _, errors = _validate_or_pin_runtime_snapshot(job_dir, receipt, manifest, destination)
    assert any("runtime mirror" in error for error in errors)


def test_runtime_sync_check_cli_summarizes_existing_receipt_without_type_error(tmp_path, monkeypatch, capsys):
    source = tmp_path / "windows"
    destination = tmp_path / "linux"
    source.mkdir()
    destination.mkdir()
    (source / "runtime.py").write_text("print('one')\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    receipt = tmp_path / "receipt.json"
    write_json(manifest, {"schema_version": "1.0.0", "files": ["runtime.py"]})
    synchronize_runtime(source, destination, manifest, receipt)
    monkeypatch.setattr(sys, "argv", [
        "sync_wsl_runtime.py",
        "--source-root", str(source),
        "--destination-root", str(destination),
        "--manifest", str(manifest),
        "--receipt", str(receipt),
        "--check",
    ])

    assert sync_runtime_main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "pass"
    assert result["read_only"] is True
    assert result["receipt"]["semantic_sha256"] == load_json(receipt)["receipt_semantic_sha256"]


def test_runtime_sync_exec_after_replaces_same_process_with_explicit_array(tmp_path, monkeypatch):
    source = tmp_path / "windows"
    destination = tmp_path / "linux"
    source.mkdir()
    destination.mkdir()
    (source / "runtime.py").write_text("print('one')\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    receipt = tmp_path / "receipt.json"
    write_json(manifest, {"schema_version": "1.0.0", "files": ["runtime.py"]})
    called = {}

    class ExecCalled(RuntimeError):
        pass

    def fake_exec(executable, argv):
        called["executable"] = executable
        called["argv"] = argv
        called["cwd"] = Path.cwd()
        raise ExecCalled

    monkeypatch.setattr("scripts.sync_wsl_runtime.os.execv", fake_exec)
    monkeypatch.setattr(sys, "argv", [
        "sync_wsl_runtime.py",
        "--source-root", str(source),
        "--destination-root", str(destination),
        "--manifest", str(manifest),
        "--receipt", str(receipt),
        "--exec-after", "/bin/echo", "ready",
    ])
    with pytest.raises(ExecCalled):
        sync_runtime_main()
    assert called == {
        "executable": "/bin/echo",
        "argv": ["/bin/echo", "ready"],
        "cwd": destination,
    }
    assert validate_runtime_parity_receipt(receipt, destination, manifest) == []


def test_direct_wsl_launcher_uses_argument_arrays_without_nested_shell():
    text = (Path(__file__).parents[1] / "scripts" / "invoke_gold_wsl.ps1").read_text(encoding="utf-8")
    lowered = text.lower()
    assert "bash -lc" not in lowered
    assert "invoke-expression" not in lowered
    assert "& wsl.exe @syncarguments" in lowered
    assert "& wsl.exe @runtimearguments" in lowered
    assert "'-d', $distribution, '-u', $linuxuser" in lowered
    assert "valuefromremainingarguments" not in lowered
    assert "explicit array through -commandarguments" in lowered
    assert "'--cd', $linuxrepo, '--exec'" in lowered
    assert "'--bootstrap-request', $mountedrequest" in lowered
    assert "windows_fallback_used = $false" in lowered
    assert "'/usr/bin/git', 'clone'" in lowered
    assert "selectbootstrap" in lowered
    assert "startepisode" in lowered
    assert "& wsl.exe @startarguments" in lowered
    assert "'--exec-after'" in lowered
    assert "'--start-episode'" in lowered
    assert "'--data-root', $linuxdataroot" in lowered
    assert "'--job-dir', $startjobdir" in lowered
    assert "'--select-next'" in lowered
    assert "$usepinnedruntime = $action -in @('fast', 'completeaudit')" in lowered
    assert "if (-not $usepinnedruntime)" in lowered
    assert "'--epic-started-at'" in lowered
    assert "explicit_contract_no_distro_enumeration" in lowered
    assert "wsl.exe -l" not in lowered
    assert "path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" in lowered
    assert "pythonnousersite=1" in lowered
    assert "msf_gold_runtime=wsl_linux" in lowered
    assert "$linuxenvironment" in lowered
    assert "'--exec'\n) + $linuxenvironment + @(" in lowered
    assert "'--exec',\n    $linuxenvironment" not in lowered


def test_post_audit_remediation_updates_complete_reviews_without_recorder_reentry(tmp_path):
    video_id = seed(tmp_path, "post-audit-remediation")
    item = finalizable_candidate(tmp_path, video_id)
    record(video_id, tmp_path, review_payload(tmp_path, video_id, item))
    first = finalize_episode(
        video_id,
        tmp_path,
        export_suffix="post-audit-remediation-packet",
        revision_id="initial-revision",
    )
    assert first["status"] == "ready"
    manifest = {
        "episode_video_id": video_id,
        "revision_id": "audit-remediation-001",
        "revision_kind": "post_audit_remediation",
        "reason": "Apply the source-backed final audit correction.",
        "updates": [{
            "candidate_id": f"{video_id}-G001",
            "assert": {"caveats": item["caveats"]},
            "set": {"caveats": [
                "Caso reportado; valide o desconto no proprio contexto antes de escalar.",
            ]},
        }],
    }
    job = tmp_path / "remediation-job"
    result = run_post_audit_remediation(
        video_id,
        tmp_path,
        manifest,
        revision_id="audit-remediation-001",
        export_suffix="post-audit-remediation-packet",
        job_dir=job,
    )
    assert result["status"] == "ready", result
    assert result["check"]["review_count"] == 1
    assert result["patch"]["mode"] == "apply"
    assert result["finalization"]["revision_id"] == "audit-remediation-001"
    assert Path(result["audit_dossier"]["path"]).exists()
    review = load_json(
        tmp_path / "processed" / video_id / "gold_extraction" / "manual_reviews" / "chunk_001_review.json"
    )
    assert review["candidates"][0]["caveats"] == manifest["updates"][0]["set"]["caveats"]
    receipt = load_json(job / "episode_fast_session.json")
    assert receipt["operation_counts"]["patches"] == 1
    assert receipt["operation_counts"]["finalizers"] == 1

    recovered = run_post_audit_remediation(
        video_id,
        tmp_path,
        manifest,
        revision_id="audit-remediation-001",
        export_suffix="post-audit-remediation-packet",
        job_dir=job,
    )
    assert recovered["status"] == "ready"
    assert recovered["patch"]["mode"] == "already_applied"
    assert recovered["finalization"]["idempotent"] is True


def test_runtime_sync_manifest_syncs_itself():
    manifest = load_json(Path(__file__).parents[1] / "scripts" / "gold_runtime_sync_manifest.json")
    assert "scripts/gold_runtime_sync_manifest.json" in manifest["files"]
    assert manifest["sync_scope"] == "full_worktree"
    assert manifest["require_git_clone"] is True


def test_fast_cli_blocks_stale_runtime_receipt_before_episode_access(tmp_path, monkeypatch, capsys):
    manifest = tmp_path / "manifest.json"
    receipt = tmp_path / "receipt.json"
    write_json(manifest, {"schema_version": "1.0.0", "files": ["missing.py"]})
    write_json(receipt, {"status": "pass"})
    monkeypatch.setattr(sys, "argv", [
        "run_gold_episode_fast",
        "--video-id", "never-opened",
        "--data-root", str(tmp_path / "missing-data"),
        "--context",
        "--runtime-parity-receipt", str(receipt),
        "--runtime-manifest", str(manifest),
    ])
    assert fast_main() == 1
    result = json.loads(capsys.readouterr().out)
    assert result["stopped_at"] == "runtime_parity"


def test_post_audit_completion_runs_registration_build_and_required_validation_once(tmp_path):
    video_id = seed(tmp_path, "post-audit")
    write_json(
        tmp_path / "processed" / video_id / "content_segments.json",
        {"segments": load_json(tmp_path / "processed" / video_id / "gold_extraction" / "transcript_clean.json")["segments"]},
    )
    record(video_id, tmp_path, review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id)))
    ready = finalize_episode(
        video_id,
        tmp_path,
        executor_thread_id="executor-thread",
        export_suffix="post-audit-packet",
        revision_id="executor-revision",
    )
    assert ready["status"] == "ready"
    job_dir = tmp_path / "post-audit-job"
    dossier_path = job_dir / "final_audit_dossier.jsonl"
    write_audit_dossier(
        dossier_path,
        build_audit_dossier(video_id, tmp_path, packet=Path(ready["packet"])),
    )
    write_audit_request(job_dir, build_audit_request(video_id, dossier_path))
    audit = {
        "episode_video_id": video_id,
        "audit_route": "final_model_review",
        "reviewer": "Final auditor",
        "reviewer_thread_id": "audit-phase-thread",
        "reviewer_model": "gpt-5.6-sol",
        "reasoning_effort": "high",
        "executor_thread_id": "executor-thread",
        "status": "passed",
        "open_findings": 0,
        "reviewed_at": "2026-07-15T12:00:00+00:00",
        "summary": "Packet passed the final source-backed audit.",
        "findings": [],
    }
    completed = complete_episode(
        video_id,
        tmp_path,
        audit,
        executor_thread_id="executor-thread",
        export_suffix="post-audit-packet",
        job_dir=job_dir,
        mirror_job_dir=tmp_path / "post-audit-mirror",
    )
    assert completed["status"] == "complete"
    assert completed["validation"] == {"status": "pass", "errors": []}
    artifacts = completed["completion_artifacts"]
    receipt = load_json(Path(artifacts["receipt"]))
    assert validate_completion_receipt(receipt) == []
    tampered = copy.deepcopy(receipt)
    tampered["packet"]["names"] = tampered["packet"]["names"][:-1]
    assert validate_completion_receipt(tampered)
    assert Path(artifacts["summary"]).read_text(encoding="utf-8").startswith("# Gold episode completion")
    assert Path(artifacts["performance_report"]).exists()
    assert Path(artifacts["final_response"]).read_text(encoding="utf-8").startswith("# EPIC COMPLETED")
    assert set(artifacts["mirror"]) >= {"episode_completion_receipt.json", "completion_summary.md", "episode_performance_report.json", "final_response.md"}
    assert receipt["epic_timing"]["elapsed_ms"] >= 0
    assert receipt["epic_timing"]["final_response_generated_at"]
    assert receipt["terminal_authority"] == {"terminal": True, "additional_verify_required": False, "next_action": "stop"}
    assert receipt["performance_budget"] == performance_budget(2)
    assert completed["terminal_receipt"] is True
    assert completed["additional_verify_required"] is False
    historical = copy.deepcopy(receipt)
    historical["schema_version"] = "1.0.0"
    historical.pop("terminal_authority")
    historical.pop("performance_budget")
    historical["receipt_semantic_sha256"] = sha256_semantic_json({
        key: value for key, value in historical.items() if key != "receipt_semantic_sha256"
    })
    assert not any("terminal authority" in error for error in validate_completion_receipt(historical))
    status = load_json(tmp_path / "processed" / video_id / "gold_extraction" / "gold_extraction_status.json")
    assert status["status"] == "complete"
    assert status["audit_status"] == "passed"
    session = load_json(tmp_path / "post-audit-job" / "episode_fast_session.json")
    assert session["operation_counts"]["audit_registrations"] == 1
    assert session["operation_counts"]["required_audit_validations"] == 1
    out = tmp_path / "processed" / video_id / "gold_extraction"
    packet = tmp_path / "exports" / "post-audit-packet"
    before_gold = file_snapshot(out)
    before_packet = file_snapshot(packet)
    repeated = complete_episode(
        video_id, tmp_path, audit,
        executor_thread_id="executor-thread",
        export_suffix="post-audit-packet",
        job_dir=tmp_path / "post-audit-job",
    )
    assert repeated["status"] == "protected"
    assert repeated["additional_verify_required"] is False
    assert file_snapshot(out) == before_gold
    assert file_snapshot(packet) == before_packet


def test_changes_requested_creates_only_nonterminal_audit_state(tmp_path):
    video_id = seed(tmp_path, "audit-remediation-state")
    record(video_id, tmp_path, review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id)))
    ready = finalize_episode(
        video_id, tmp_path,
        executor_thread_id="executor-thread",
        export_suffix="audit-remediation-packet",
        revision_id="executor-revision",
    )
    assert ready["status"] == "ready"
    out = tmp_path / "processed" / video_id / "gold_extraction"
    before = file_snapshot(out)
    job_dir = tmp_path / "audit-remediation-job"
    dossier_path = job_dir / "final_audit_dossier.jsonl"
    write_audit_dossier(
        dossier_path,
        build_audit_dossier(video_id, tmp_path, packet=Path(ready["packet"])),
    )
    write_audit_request(job_dir, build_audit_request(video_id, dossier_path))
    audit = {
        "episode_video_id": video_id,
        "audit_route": "final_model_review",
        "reviewer": "Final auditor",
        "reviewer_thread_id": "audit-phase-thread",
        "reviewer_model": "gpt-5.6-sol",
        "reasoning_effort": "high",
        "executor_thread_id": "executor-thread",
        "reviewed_at": "2026-07-16T12:00:00+00:00",
        "status": "changes_requested",
        "open_findings": 1,
        "summary": "One source-backed correction remains.",
        "findings": [{
            "finding_id": "AUD-001", "severity": "major", "status": "open",
            "category": "numeric_recall", "segment_range": [0, 1],
            "candidate_ids": [f"{video_id}-G001"], "summary": "A value is missing.",
            "evidence": "The literal source contains an additional value.",
            "required_action": "Add the source-backed number record.",
        }],
    }

    result = complete_episode(
        video_id, tmp_path, audit,
        executor_thread_id="executor-thread",
        export_suffix="audit-remediation-packet",
        job_dir=job_dir,
    )

    assert result["status"] == "remediation_required"
    assert result["next_gate"] == "post_audit_remediation"
    assert result["terminal_receipt"] is False
    assert load_json(job_dir / "episode_audit_state.json")["finding_ids"] == ["AUD-001"]
    assert not (job_dir / "final_response.md").exists()
    assert not (job_dir / "episode_completion_receipt.json").exists()
    assert not (out / "editorial_audit_report.json").exists()
    assert file_snapshot(out) == before


def test_final_audit_dossier_is_source_complete_and_self_verifying(tmp_path):
    video_id = seed(tmp_path, "audit-dossier")
    record(video_id, tmp_path, review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id)))
    finalized = finalize_episode(video_id, tmp_path, export_suffix="audit-dossier-packet", revision_id="audit-dossier-001")
    packet = Path(finalized["packet"])
    dossier = build_audit_dossier(video_id, tmp_path, packet=packet, revision_id="audit-dossier-001")
    path = tmp_path / "job" / "final_audit_dossier.jsonl"
    identity = write_audit_dossier(path, dossier)
    assert identity["bytes"] > 0
    assert identity["navigation_target_bytes"] == 500_000
    assert validate_audit_dossier(path, video_id, tmp_path, packet) == []
    lines = path.read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0])
    assert header["schema_version"] == "3.2.0"
    workbench_record = next(
        json.loads(line) for line in lines
        if json.loads(line).get("record_type") == "semantic_workbench"
    )
    assert workbench_record["value"]["semantic_sha256"] == header["semantic_workbench"]["semantic_sha256"]
    assert "audit_navigation" not in header
    assert workbench_record["value"]["source_workbench_semantic_sha256"]
    assert "coverage_rows" in workbench_record["value"]
    assert "coverage_blocks" not in workbench_record["value"]
    assert header["transcript_columns"][-4:] == [
        "ledger_disposition", "ledger_candidate_ids", "ledger_reason_code", "ledger_reason_reference",
    ]
    assert header["numeric_coverage"]["missing_material_count"] == 0
    assert header["candidate_columns"][0] == "candidate_id"
    assert header["ledger_group_columns"] == [
        "disposition", "candidate_ids", "reason_code", "reason_reference", "clean_indexes",
    ]
    candidate_record = next(json.loads(line) for line in lines if json.loads(line).get("record_type") == "candidate")
    assert isinstance(candidate_record["value"], list)
    numeric_record = next(json.loads(line) for line in lines if json.loads(line).get("record_type") == "numeric_coverage")
    assert numeric_record["value"]["mentions"][0]["record"]["raw"] == "20%"
    ledger_records = [json.loads(line) for line in lines if json.loads(line).get("record_type") == "ledger_group"]
    assert ledger_records
    assert sum(len(item["value"][-1]) for item in ledger_records) == header["ledger_entry_count"]
    transcript_rows = [
        row
        for line in lines
        if json.loads(line).get("record_type") == "transcript_block"
        for row in json.loads(line)["value"]
    ]
    assert len(transcript_rows) == 2
    transcript_line_index = next(
        index for index, line in enumerate(lines)
        if json.loads(line).get("record_type") == "transcript_block"
    )
    changed = json.loads(lines[transcript_line_index])
    changed["value"][0][3] = "fabricated"
    lines[transcript_line_index] = json.dumps(changed)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert any("transcript" in error or "receipt" in error for error in validate_audit_dossier(path, video_id, tmp_path, packet))


def test_audit_remediation_scaffold_is_source_canonical_and_read_only(tmp_path):
    video_id = seed(tmp_path, "audit-scaffold")
    record(video_id, tmp_path, review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id)))
    out = tmp_path / "processed" / video_id / "gold_extraction"
    before = file_snapshot(out)
    audit = {
        "episode_video_id": video_id,
        "status": "changes_requested",
        "open_findings": 1,
        "findings": [{
            "finding_id": "AUD-001", "segment_range": [0, 0],
            "candidate_ids": [f"{video_id}-G001"],
            "required_action": "Preserve the literal result and clarify the caveat.",
        }],
    }
    scaffold = generate_audit_remediation_scaffold(video_id, tmp_path, audit)
    finding = scaffold["findings"][0]
    assert finding["source_segments"][0]["quote_verbatim"] == "Testamos 20% de desconto antes de escalar."
    assert finding["candidate_asserts"][0]["candidate_id"] == f"{video_id}-G001"
    assert finding["source_numeric_occurrences"][0]["raw"] == "20%"
    assert finding["review_assertions"][0]["chunk_id"] == f"{video_id}-gold-chunk-001"
    assert finding["suggested_insert_candidate_id"] == f"{video_id}-G002"
    assert scaffold["patch_manifest_template"]["revision_kind"] == "audit_remediation"
    assert scaffold["patch_manifest_template"]["review_assertions"] == finding["review_assertions"]
    assert scaffold["writes_gold"] is False
    assert file_snapshot(out) == before


def test_reaudit_delta_rejects_any_integral_invariant_drift(tmp_path):
    video_id = seed(tmp_path, "reaudit-delta")
    record(video_id, tmp_path, review_payload(tmp_path, video_id, finalizable_candidate(tmp_path, video_id)))
    finalized = finalize_episode(video_id, tmp_path, export_suffix="reaudit-delta-packet")
    packet = Path(finalized["packet"])
    before_dossier = build_audit_dossier(video_id, tmp_path, packet=packet)
    after_dossier = copy.deepcopy(before_dossier)
    header = after_dossier["records"][0]
    claim_index = header["candidate_columns"].index("source_claim")
    candidate_record = next(item for item in after_dossier["records"] if item.get("record_type") == "candidate")
    candidate_record["value"][claim_index] = "A claim corrigida para o finding focal."
    after_dossier["records"][-1]["content_semantic_sha256"] = sha256_semantic_json(after_dossier["records"][:-1])
    before_path = tmp_path / "before.jsonl"
    after_path = tmp_path / "after.jsonl"
    write_audit_dossier(before_path, before_dossier)
    write_audit_dossier(after_path, after_dossier)
    audit = {
        "episode_video_id": video_id,
        "findings": [{"finding_id": "AUD-001", "candidate_ids": [f"{video_id}-G001"], "segment_range": [0, 0]}],
    }
    delta = build_reaudit_delta(before_path, after_path, audit)
    assert validate_reaudit_delta(delta) == []

    drifted = copy.deepcopy(after_dossier)
    transcript_record = next(item for item in drifted["records"] if item.get("record_type") == "transcript_block")
    transcript_record["value"][1][3] = "Transcript drifted outside the finding."
    drifted["records"][-1]["content_semantic_sha256"] = sha256_semantic_json(drifted["records"][:-1])
    drifted_path = tmp_path / "drifted.jsonl"
    write_audit_dossier(drifted_path, drifted)
    rejected = build_reaudit_delta(before_path, drifted_path, audit)
    assert any("transcript" in error for error in validate_reaudit_delta(rejected))


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
    receipt["packet"] = r"Z:\MSF-data\Marketing_Swipe_File\exports\packet-a"
    write_json(receipt_path, receipt)
    rebased = evaluate_wave(valid_manifest, tmp_path)
    assert rebased["wave_status"] == "ready_for_audit"
    assert rebased["episode_results"][0]["packet_identity"] is True

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
