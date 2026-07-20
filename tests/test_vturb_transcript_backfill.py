import csv
import json
import sys
from pathlib import Path

import pytest

from scripts import backfill_vturb_transcripts as backfill
from scripts import capture_youtube_transcript_with_playwright_cli as playwright_capture
from scripts.capture_youtube_transcript_with_playwright_cli import normalize_dom_segments, segments_are_monotonic


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def row(video_id: str, priority: int, discovered: int = 1) -> dict[str, str]:
    return {
        "video_id": video_id,
        "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
        "channel_name": "VTurb",
        "title": f"Episode {video_id}",
        "duration_seconds": "100",
        "category": "copy",
        "episode_priority": str(priority),
        "discovered_order": str(discovered),
        "published_time_text": "today",
    }


def payload(video_id: str, text: str = "source text") -> dict:
    return {
        "schema_version": "1.0",
        "youtube_video_id": video_id,
        "source_kind": "transcript",
        "language": "pt",
        "provider": "test",
        "segments": [
            {"index": 0, "start_seconds": 0, "duration_seconds": 50, "text": text},
            {"index": 1, "start_seconds": 50, "duration_seconds": 50, "text": text},
        ],
    }


def make_args(tmp_path: Path, routes: set[str]) -> object:
    return type("Args", (), {
        "data_root": tmp_path,
        "repo_root": Path(__file__).parents[1],
        "state": tmp_path / "state.json",
        "ledger": tmp_path / "ledger.jsonl",
        "staging_root": tmp_path / "cache" / "staging",
        "snapshot_root": tmp_path / "cache" / "snapshots",
        "media_root": tmp_path / "cache" / "audio",
        "model_cache": tmp_path / "cache" / "models",
        "browser_import_dir": tmp_path / "cache" / "browser_import",
        "browser_checkpoint_dir": None,
        "browser_checkpoint_results": {},
        "routes": routes,
        "minimum_bytes": 1,
        "minimum_coverage": 0.5,
        "retry_ui": False,
        "allow_asr": False,
        "playwright_session": "test",
        "playwright_timeout": 1,
        "ui_process_timeout": 1,
        "direct_timeout": 1,
        "asr_model": "tiny",
        "asr_batch_size": 0,
        "asr_clip_seconds": None,
        "asr_chunk_seconds": 1200,
        "asr_overlap_seconds": 2,
        "asr_checkpoint_root": tmp_path / "cache" / "asr-checkpoints",
        "_audio_futures": {},
        "_asr_rtfs": [],
        "_asr_remaining_media_seconds": 0.0,
    })()


def test_inventory_distinguishes_valid_empty_and_missing_metadata(tmp_path):
    rows = [row("validvid001", 1), row("emptyvid001", 2), row("missing0001", 3)]
    for item in rows[:2]:
        write_json(backfill.metadata_path(tmp_path, item["video_id"]), backfill.metadata_from_queue(item))
    write_json(backfill.transcript_path(tmp_path, "validvid001"), payload("validvid001"))
    write_json(backfill.transcript_path(tmp_path, "emptyvid001"), {
        "youtube_video_id": "emptyvid001", "provider": "missing:caption_fetch_error", "segments": []
    })
    inventory = backfill.build_inventory(rows, tmp_path, {"entries": {}}, minimum_bytes=1, minimum_coverage=0.5)
    assert [item["status"] for item in inventory] == ["completed", "pending_ui", "pending_metadata"]
    assert [item["materialization_status"] for item in inventory] == ["needs_materialization", "transcript_invalid", "transcript_invalid"]


def test_materialize_ready_promotes_only_a_valid_existing_transcript(tmp_path):
    item = row("materialize1", 1)
    args = make_args(tmp_path, set())
    write_json(backfill.metadata_path(tmp_path, item["video_id"]), backfill.metadata_from_queue(item))
    write_json(backfill.transcript_path(tmp_path, item["video_id"]), payload(item["video_id"]))
    validation = backfill.validate_transcript_file(
        backfill.transcript_path(tmp_path, item["video_id"]),
        video_id=item["video_id"],
        duration_seconds=100,
        minimum_bytes=1,
        minimum_coverage=0.5,
    )

    assert backfill.materialize_existing_transcript(item, validation, args) == "materialized"
    assert backfill.content_path(tmp_path, item["video_id"]).is_file()
    assert backfill.read_json(backfill.metadata_path(tmp_path, item["video_id"]))["transcript_status"] == "available"


def test_inventory_recovers_interrupted_asr_as_resumable(tmp_path):
    item = row("resumeasr01", 1)
    write_json(backfill.metadata_path(tmp_path, item["video_id"]), backfill.metadata_from_queue(item))
    state = {"entries": {item["video_id"]: {"status": "running_asr"}}}
    inventory = backfill.build_inventory([item], tmp_path, state, minimum_bytes=1, minimum_coverage=0.5)
    assert inventory[0]["status"] == "pending_asr"


def test_selection_preserves_priority_and_supports_recent_limit():
    inventory = [
        {**row("older000001", 1, 5), "status": "pending_direct"},
        {**row("newest00001", 9, 1), "status": "pending_direct"},
        {**row("newer000001", 7, 2), "status": "pending_direct"},
    ]
    selected = backfill.select_inventory(inventory, start_priority=None, recent_limit=2, max_items=None)
    assert [item["video_id"] for item in selected] == ["newer000001", "newest00001"]


def test_selection_filters_explicit_ids_and_skips_non_actionable_waiting_chrome():
    inventory = [
        {**row("direct00001", 1), "status": "pending_direct"},
        {**row("chrome00001", 2), "status": "pending_chrome"},
        {**row("other000001", 3), "status": "pending_direct"},
    ]
    selected = backfill.select_inventory(
        inventory,
        start_priority=None,
        recent_limit=None,
        max_items=None,
        video_ids={"direct00001", "chrome00001"},
        actionable_statuses={"pending_direct", "pending_ui"},
    )
    assert [item["video_id"] for item in selected] == ["direct00001"]


def test_direct_success_promotes_transcript_and_normalized_segments(tmp_path, monkeypatch):
    item = {**row("success0001", 1), "status": "pending_metadata"}
    args = make_args(tmp_path, {"metadata", "direct"})
    monkeypatch.setattr(backfill, "run_direct", lambda current, runtime: payload(current["video_id"]))
    state = {"entries": {}}
    outcome = backfill.process_item(item, state, args)
    assert outcome == "completed"
    transcript = json.loads(backfill.transcript_path(tmp_path, item["video_id"]).read_text())
    normalized = json.loads(backfill.content_path(tmp_path, item["video_id"]).read_text())
    assert len(transcript["segments"]) == len(normalized["segments"]) == 2
    assert state["entries"][item["video_id"]]["validation"]["valid"] is True


def test_invalid_direct_never_overwrites_existing_empty_and_moves_to_ui(tmp_path, monkeypatch):
    item = {**row("invalid00001", 1), "status": "pending_direct"}
    args = make_args(tmp_path, {"direct"})
    write_json(backfill.metadata_path(tmp_path, item["video_id"]), backfill.metadata_from_queue(item))
    empty = {"youtube_video_id": item["video_id"], "provider": "missing:old", "segments": []}
    write_json(backfill.transcript_path(tmp_path, item["video_id"]), empty)
    monkeypatch.setattr(backfill, "run_direct", lambda current, runtime: {
        "youtube_video_id": current["video_id"], "provider": "missing:new", "segments": []
    })
    state = {"entries": {item["video_id"]: {"status": "pending_direct"}}}
    outcome = backfill.process_item(item, state, args)
    assert outcome == "pending_ui"
    assert json.loads(backfill.transcript_path(tmp_path, item["video_id"]).read_text()) == empty


def test_direct_failure_chains_to_ui_in_same_run(tmp_path, monkeypatch):
    item = {**row("chainui0001", 1), "status": "pending_direct"}
    args = make_args(tmp_path, {"direct", "ui"})
    write_json(backfill.metadata_path(tmp_path, item["video_id"]), backfill.metadata_from_queue(item))
    monkeypatch.setattr(backfill, "run_direct", lambda current, runtime: {
        "youtube_video_id": current["video_id"], "provider": "missing:direct", "segments": []
    })
    monkeypatch.setattr(backfill, "run_ui", lambda current, runtime: payload(current["video_id"]))
    state = {"entries": {}}
    assert backfill.process_item(item, state, args) == "completed"
    assert state["entries"][item["video_id"]]["attempts"] == {"direct": 1, "ui": 1}


def test_browser_import_is_validated_and_promoted(tmp_path):
    item = {**row("browser0001", 1), "status": "pending_chrome"}
    args = make_args(tmp_path, {"browser"})
    write_json(backfill.metadata_path(tmp_path, item["video_id"]), backfill.metadata_from_queue(item))
    write_json(args.browser_import_dir / f"{item['video_id']}.json", payload(item["video_id"]))
    state = {"entries": {item["video_id"]: {"status": "pending_chrome"}}}
    assert backfill.process_item(item, state, args) == "completed"
    assert json.loads(backfill.transcript_path(tmp_path, item["video_id"]).read_text())["provider"] == "test"
    assert state["entries"][item["video_id"]]["attempts"] == {"browser": 1}


def test_browser_import_recovers_item_already_queued_for_asr(tmp_path):
    item = {**row("browserasr1", 1), "status": "pending_asr"}
    args = make_args(tmp_path, {"browser"})
    write_json(backfill.metadata_path(tmp_path, item["video_id"]), backfill.metadata_from_queue(item))
    write_json(args.browser_import_dir / f"{item['video_id']}.json", payload(item["video_id"]))
    state = {"entries": {item["video_id"]: {"status": "pending_asr"}}}
    assert backfill.process_item(item, state, args) == "completed"
    assert state["entries"][item["video_id"]]["last_route"] == "browser"


def test_browser_checkpoint_applies_no_ui_and_imports_only_bound_capture(tmp_path):
    manifest = "a" * 64
    checkpoint = tmp_path / "browser"
    write_json(checkpoint / "manifest.json", {"manifest_sha256": manifest})
    write_json(checkpoint / "results" / "noui0000001.json", {
        "video_id": "noui0000001", "status": "no_ui", "manifest_sha256": manifest,
        "reason": "description_transcript_button_absent", "finished_at": "2026-01-01T00:00:00Z",
    })
    write_json(checkpoint / "results" / "captured001.json", {
        "video_id": "captured001", "status": "captured", "manifest_sha256": manifest,
    })
    write_json(checkpoint / "captures" / "captured001.json", payload("captured001"))
    results, loaded_manifest = backfill.load_browser_checkpoint_results(checkpoint)
    state = {"entries": {"captured001": {"status": "pending_chrome"}}}
    counts = backfill.apply_browser_checkpoint_results(state, results, {"noui0000001", "captured001"})
    assert loaded_manifest == manifest
    assert counts == {"no_ui": 1, "captured": 1}
    assert state["entries"]["noui0000001"]["status"] == "pending_asr"
    args = make_args(tmp_path, {"browser"})
    args.browser_checkpoint_dir = checkpoint
    args.browser_checkpoint_results = results
    assert backfill.browser_capture_available("captured001", args)
    assert not backfill.browser_capture_available("noui0000001", args)


def test_mixed_browser_wave_keeps_valid_item_when_neighbor_is_invalid(tmp_path):
    args = make_args(tmp_path, {"browser"})
    valid = {**row("validwave01", 1), "status": "pending_chrome"}
    invalid = {**row("invalidwave1", 2), "status": "pending_chrome"}
    for item in (valid, invalid):
        write_json(backfill.metadata_path(tmp_path, item["video_id"]), backfill.metadata_from_queue(item))
    write_json(args.browser_import_dir / "validwave01.json", payload("validwave01"))
    write_json(args.browser_import_dir / "invalidwave1.json", payload("different01"))
    state = {"entries": {item["video_id"]: {"status": "pending_chrome"} for item in (valid, invalid)}}
    assert backfill.process_item(valid, state, args) == "completed"
    assert backfill.process_item(invalid, state, args) == "pending_chrome"
    assert backfill.transcript_path(tmp_path, "validwave01").is_file()
    assert not backfill.transcript_path(tmp_path, "invalidwave1").is_file()


def test_asr_chunks_resume_and_remove_overlap_duplicates():
    specs = backfill.chunk_specs(2500, 1200, 2)
    assert [(item["clip_start"], item["clip_end"]) for item in specs] == [
        (0.0, 1202.0), (1198.0, 2402.0), (2398.0, 2500),
    ]
    receipt = {
        "status": "completed", "video_id": "chunkvideo1", "media_sha256": "hash",
        "config_key": "config", "chunk_index": 0, "nominal_start": 0.0,
        "nominal_end": 1200.0, "segments": [],
    }
    assert backfill.valid_chunk_receipt(
        receipt, video_id="chunkvideo1", media_sha256="hash", config_key="config", spec=specs[0]
    )
    receipts = [
        {"nominal_start": 0, "nominal_end": 10, "final_chunk": False, "segments": [
            {"start_seconds": 8, "duration_seconds": 1, "text": "left"},
            {"start_seconds": 9.8, "duration_seconds": 1, "text": "duplicate"},
        ]},
        {"nominal_start": 10, "nominal_end": 20, "final_chunk": True, "segments": [
            {"start_seconds": 9.8, "duration_seconds": 1, "text": "duplicate"},
            {"start_seconds": 11, "duration_seconds": 1, "text": "right"},
        ]},
    ]
    assembled = backfill._assemble_chunk_segments(receipts)
    assert [item["text"] for item in assembled] == ["left", "duplicate", "right"]
    assert assembled[1]["start_seconds"] == 10.0


def test_asr_chunk_boundary_cannot_move_assembled_timeline_backwards():
    receipts = [
        {"nominal_start": 0, "nominal_end": 10, "final_chunk": False, "segments": [
            {"start_seconds": 9.7, "duration_seconds": 0.4, "text": "left boundary"},
        ]},
        {"nominal_start": 10, "nominal_end": 20, "final_chunk": True, "segments": [
            {"start_seconds": 9.5, "duration_seconds": 1.2, "text": "right boundary"},
        ]},
    ]
    assembled = backfill._assemble_chunk_segments(receipts)
    assert [item["start_seconds"] for item in assembled] == [9.7, 10.0]
    assert [item["duration_seconds"] for item in assembled] == [0.3, 0.7]


def test_ui_failure_is_not_declared_missing_and_requires_chrome(tmp_path, monkeypatch):
    item = {**row("uifailure01", 1), "status": "pending_ui"}
    args = make_args(tmp_path, {"ui"})
    write_json(backfill.metadata_path(tmp_path, item["video_id"]), backfill.metadata_from_queue(item))
    monkeypatch.setattr(backfill, "run_ui", lambda current, runtime: (_ for _ in ()).throw(RuntimeError("button missing")))
    state = {"entries": {item["video_id"]: {"status": "pending_ui"}}}
    outcome = backfill.process_item(item, state, args)
    assert outcome == "pending_chrome"
    assert state["entries"][item["video_id"]]["last_error"] == "button missing"


def test_validation_rejects_low_coverage_and_out_of_order():
    bad = payload("coverage001")
    bad["segments"][1]["start_seconds"] = -1
    result = backfill.validate_transcript_payload(
        bad, video_id="coverage001", duration_seconds=1000, minimum_bytes=1, minimum_coverage=0.6
    )
    assert result["valid"] is False
    assert any("order_invalid" in error for error in result["errors"])
    assert any("coverage_too_low" in error for error in result["errors"])


def test_browser_capture_rejects_stale_out_of_order_tail():
    raw = [
        {"timestamp": "0:00", "text": "current start"},
        {"timestamp": "1:00", "text": "current end"},
        {"timestamp": "0:30", "text": "stale previous panel"},
    ]
    assert normalize_dom_segments(raw) == []
    assert not segments_are_monotonic([
        {"start_seconds": 0}, {"start_seconds": 60}, {"start_seconds": 30}
    ])


def test_linux_browser_capture_never_selects_windows_npx(monkeypatch):
    monkeypatch.setattr(playwright_capture.os, "name", "posix")
    monkeypatch.setattr(
        playwright_capture.shutil,
        "which",
        lambda executable: "/usr/bin/npx" if executable == "npx" else "/mnt/c/Program Files/nodejs/npx.cmd",
    )
    seen = {}

    def fake_run(command, **kwargs):
        seen["command"] = command
        return type("Completed", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(playwright_capture.subprocess, "run", fake_run)
    playwright_capture.run_cli("test", ["open", "https://example.com"], timeout=1)
    assert seen["command"][0] == "/usr/bin/npx"
    assert seen["command"][3] == playwright_capture.NODE_PACKAGE
    assert seen["command"][5] == playwright_capture.PLAYWRIGHT_CLI_PACKAGE
    assert seen["command"][7] == "-s=test"


def test_capability_error_classification_is_global_and_deterministic():
    assert playwright_capture.classify_capability_error("Exec format error: npx.cmd") == "path_mixed"
    assert playwright_capture.classify_capability_error("Playwright requires Node.js 20 or higher") == "node_engine"
    assert playwright_capture.classify_capability_error("Unknown command: undefined") == "cli_protocol"
    assert playwright_capture.classify_capability_error("libnspr4.so: cannot open shared object file") == "system_library_missing"


def test_failed_ui_capability_uses_one_probe_and_zero_item_attempts(tmp_path, monkeypatch):
    queue = tmp_path / "queue.csv"
    rows = [row(f"preflight{i:02d}", i + 1) for i in range(5)]
    with queue.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    for item in rows:
        write_json(backfill.metadata_path(tmp_path, item["video_id"]), backfill.metadata_from_queue(item))
        write_json(backfill.transcript_path(tmp_path, item["video_id"]), {
            "youtube_video_id": item["video_id"], "provider": "missing:caption_fetch_error", "segments": [],
        })
    calls = {"probe": 0, "ui": 0}

    def failed_probe(args):
        calls["probe"] += 1
        return {"available": False, "error_class": "system_library_missing", "error": "lib missing"}

    def forbidden_ui(item, args):
        calls["ui"] += 1
        raise AssertionError("UI route must be globally disabled")

    monkeypatch.setattr(backfill, "probe_ui_capability", failed_probe)
    monkeypatch.setattr(backfill, "run_ui", forbidden_ui)
    monkeypatch.setattr(sys, "argv", [
        "backfill_vturb_transcripts.py", "--data-root", str(tmp_path), "--queue", str(queue), "--routes", "ui",
        "--minimum-bytes", "1",
    ])
    assert backfill.main() == 0
    assert calls == {"probe": 1, "ui": 0}


def test_exclusive_lock_blocks_concurrent_runner(tmp_path):
    lock = tmp_path / "backfill.lock"
    with backfill.exclusive_lock(lock):
        with pytest.raises(RuntimeError, match="already exists"):
            with backfill.exclusive_lock(lock):
                pass
