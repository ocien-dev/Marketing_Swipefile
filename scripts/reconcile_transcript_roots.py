#!/usr/bin/env python3
"""Transactionally mirror canonical transcript sources from WSL to Windows.

The source root is read through ``wsl.exe --exec cat`` so the JSON bytes are
never normalized or re-serialized.  The destination only receives a complete
episode source set after the staged files, identifiers, and hashes validate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from scripts.audit_gold_source_inventory import build_inventory
from scripts.gold_extraction_common import sha256_semantic_json


EPIC_ID = "MSF-R20-TRANSCRIPT-ROOT-RECONCILIATION-111"
REQUIRED = ("metadata", "transcript_original", "content_segments")
OPTIONAL = "transcript_pt_br"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def hash_bytes(raw: bytes) -> dict[str, str]:
    try:
        decoded = raw.decode("utf-8")
        value = json.loads(decoded)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid UTF-8 JSON: {error}") from error
    return {
        "physical_sha256": hashlib.sha256(raw).hexdigest(),
        "semantic_sha256": sha256_semantic_json(value),
    }


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def artifact_paths(root: Path | PurePosixPath, video_id: str) -> dict[str, Path | PurePosixPath]:
    raw = root / "raw" / "youtube" / video_id
    return {
        "metadata": raw / "metadata.json",
        "transcript_original": raw / "transcript_original.json",
        OPTIONAL: raw / "transcript_pt_br.json",
        "content_segments": root / "processed" / video_id / "content_segments.json",
    }


def validate_source_set(video_id: str, raw_by_name: dict[str, bytes]) -> dict[str, dict[str, str]]:
    missing = [name for name in REQUIRED if name not in raw_by_name]
    if missing:
        raise ValueError(f"missing required artifacts: {', '.join(missing)}")
    values: dict[str, dict[str, Any]] = {}
    hashes: dict[str, dict[str, str]] = {}
    for name, raw in raw_by_name.items():
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f"{name}: invalid UTF-8 JSON: {error}") from error
        if not isinstance(value, dict):
            raise ValueError(f"{name}: JSON root is not an object")
        values[name] = value
        hashes[name] = hash_bytes(raw)
    metadata = values["metadata"]
    original = values["transcript_original"]
    content = values["content_segments"]
    metadata_id = metadata.get("youtube_video_id") or metadata.get("video_id")
    transcript_id = original.get("youtube_video_id") or original.get("video_id")
    transcript_status = metadata.get("transcript_status") or original.get("transcript_status")
    if metadata_id != video_id:
        raise ValueError("metadata video ID mismatch")
    if transcript_id != video_id:
        raise ValueError("transcript video ID mismatch")
    if transcript_status != "available":
        raise ValueError(f"transcript status is {transcript_status!r}, expected 'available'")
    if not isinstance(original.get("segments"), list) or not original["segments"]:
        raise ValueError("transcript segments are empty")
    if content.get("episode_video_id") != video_id:
        raise ValueError("content episode video ID mismatch")
    if not isinstance(content.get("segments"), list) or not content["segments"]:
        raise ValueError("content segments are empty")
    if OPTIONAL in values:
        translated_id = values[OPTIONAL].get("youtube_video_id") or values[OPTIONAL].get("video_id")
        if translated_id != video_id:
            raise ValueError("pt-BR transcript video ID mismatch")
        if not isinstance(values[OPTIONAL].get("segments"), list) or not values[OPTIONAL]["segments"]:
            raise ValueError("pt-BR transcript segments are empty")
    return hashes


def wsl_bytes(distribution: str, user: str, source_path: Path | PurePosixPath, *, optional: bool = False) -> bytes | None:
    command = ["wsl.exe", "--distribution", distribution, "--user", user, "--exec", "cat", str(source_path)]
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if completed.returncode == 0:
        return completed.stdout
    if optional and b"No such file" in completed.stderr:
        return None
    detail = completed.stderr.decode("utf-8", errors="replace").strip()[-1000:]
    raise RuntimeError(f"WSL source read failed for {source_path}: exit={completed.returncode} {detail}")


def fetch_source(video_id: str, args: argparse.Namespace) -> tuple[dict[str, bytes], dict[str, dict[str, str]]]:
    paths = artifact_paths(PurePosixPath(args.source_root), video_id)
    raw: dict[str, bytes] = {}
    for name in (*REQUIRED, OPTIONAL):
        received = wsl_bytes(args.distribution, args.wsl_user, paths[name], optional=name == OPTIONAL)
        if received is not None:
            raw[name] = received
    return raw, validate_source_set(video_id, raw)


def destination_bytes(video_id: str, root: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for name, path in artifact_paths(root, video_id).items():
        if path.is_file():
            result[name] = path.read_bytes()
    return result


def protected_fingerprints(root: Path, video_ids: list[str]) -> dict[str, str]:
    paths: list[Path] = [root / "exports" / "curated_insights.json", root / "exports" / "insights_v2_master.json"]
    for video_id in video_ids:
        gold = root / "processed" / video_id / "gold_extraction"
        if gold.is_dir():
            paths.extend(path for path in gold.rglob("*") if path.is_file())
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths if path.is_file()}


def manifest_core(manifest: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in manifest.items() if key != "semantic_sha256"}


def load_and_validate_manifest(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("kind") != "transcript_root_reconciliation_manifest":
        raise ValueError("unexpected manifest kind")
    if manifest.get("episode_count") != 111:
        raise ValueError("manifest episode_count must be exactly 111")
    if manifest.get("semantic_sha256") != sha256_semantic_json(manifest_core(manifest)):
        raise ValueError("manifest semantic hash mismatch")
    episodes = manifest.get("episodes")
    if not isinstance(episodes, list) or len(episodes) != 111:
        raise ValueError("manifest episodes must contain exactly 111 entries")
    ordered = sorted(episodes, key=lambda entry: int(entry["rank"]))
    ranks = [int(entry["rank"]) for entry in ordered]
    ids = [str(entry["video_id"]) for entry in ordered]
    if len(set(ranks)) != len(ranks) or ranks != sorted(ranks):
        raise ValueError("manifest ranks are not unique and ascending")
    if len(set(ids)) != len(ids):
        raise ValueError("manifest contains duplicate video IDs")
    queue = json.loads(args.priority_queue.read_text(encoding="utf-8"))
    queue_ranks = {str(item.get("video_id")): item.get("rank") for item in queue.get("entries", []) if isinstance(item, dict)}
    mismatches = [entry["video_id"] for entry in ordered if queue_ranks.get(entry["video_id"]) != entry["rank"]]
    if mismatches:
        raise ValueError(f"manifest queue rank mismatch: {mismatches[:5]}")
    return manifest, ordered


def preflight(args: argparse.Namespace, episodes: list[dict[str, Any]]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for entry in episodes:
        video_id = str(entry["video_id"])
        source_raw, source_hashes = fetch_source(video_id, args)
        destination = destination_bytes(video_id, args.data_root)
        destination_hashes = {name: hash_bytes(raw) for name, raw in destination.items()}
        records.append({
            "rank": entry["rank"], "video_id": video_id,
            "source_hashes": source_hashes,
            "destination_hashes_before": destination_hashes,
            "source_artifacts": sorted(source_raw),
        })
    return {
        "schema_version": "1.0.0", "kind": "transcript_root_reconciliation_preflight",
        "epic_id": EPIC_ID, "created_at": now(), "distribution": args.distribution,
        "source_root": str(args.source_root), "data_root": str(args.data_root),
        "terminal_count": len(records), "records": records,
    }


def same_hashes(left: dict[str, dict[str, str]], right: dict[str, dict[str, str]]) -> bool:
    return left == right


def transactional_publish(video_id: str, source_raw: dict[str, bytes], args: argparse.Namespace) -> tuple[dict[str, dict[str, str]], list[str]]:
    stage = args.staging_root / "stage" / video_id
    rollback = args.staging_root / "rollback" / video_id
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True, exist_ok=True)
    paths = artifact_paths(args.data_root, video_id)
    destination_before = destination_bytes(video_id, args.data_root)
    for name, raw in source_raw.items():
        (stage / f"{name}.json").write_bytes(raw)
    removed: list[str] = []
    if OPTIONAL not in source_raw and OPTIONAL in destination_before:
        try:
            validate_source_set(video_id, {name: destination_before[name] for name in REQUIRED})
        except ValueError:
            removed.append(OPTIONAL)
        else:
            raise ValueError("valid destination pt-BR transcript has no canonical source counterpart")
    changed = [name for name, raw in source_raw.items() if destination_before.get(name) != raw] + removed
    if not changed:
        return {name: hash_bytes(raw) for name, raw in destination_before.items()}, []
    # An already-valid but divergent destination is an ownership conflict, not a
    # permission to overwrite a separately curated source.
    if all(name in destination_before for name in REQUIRED):
        try:
            validate_source_set(video_id, {name: destination_before[name] for name in REQUIRED})
        except ValueError:
            pass
        else:
            raise ValueError("valid destination source differs from canonical source")
    if rollback.exists():
        shutil.rmtree(rollback)
    rollback.mkdir(parents=True, exist_ok=True)
    for name, raw in destination_before.items():
        (rollback / f"{name}.json").write_bytes(raw)
    staged_replacements: list[tuple[Path, Path, bytes | None]] = []
    replaced: list[tuple[Path, bytes | None]] = []
    try:
        for name in changed:
            path = paths[name]
            path.parent.mkdir(parents=True, exist_ok=True)
            if name in source_raw:
                temp = path.with_name(f".{path.name}.{os.getpid()}.reconcile")
                temp.write_bytes((stage / f"{name}.json").read_bytes())
                staged_replacements.append((path, temp, destination_before.get(name)))
        for path, temp, before in staged_replacements:
            os.replace(temp, path)
            replaced.append((path, before))
        for name in removed:
            paths[name].unlink(missing_ok=True)
            replaced.append((paths[name], destination_before.get(name)))
    except Exception:
        for path, before in reversed(replaced):
            if before is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(before)
        for _, temp, _ in staged_replacements:
            temp.unlink(missing_ok=True)
        raise
    return {name: hash_bytes(raw) for name, raw in destination_bytes(video_id, args.data_root).items()}, changed


def materialize(args: argparse.Namespace, episodes: list[dict[str, Any]], preflight_report: dict[str, Any]) -> dict[str, Any]:
    preflight_by_id = {record["video_id"]: record for record in preflight_report["records"]}
    results: list[dict[str, Any]] = []
    for entry in episodes:
        started = time.perf_counter()
        video_id = str(entry["video_id"])
        source_raw, source_hashes = fetch_source(video_id, args)
        expected = preflight_by_id[video_id]["source_hashes"]
        if not same_hashes(source_hashes, expected):
            raise RuntimeError(f"source_drift: {video_id}")
        before = destination_bytes(video_id, args.data_root)
        before_hashes = {name: hash_bytes(raw) for name, raw in before.items()}
        if same_hashes(before_hashes, source_hashes):
            result = {"rank": entry["rank"], "video_id": video_id, "status": "idempotent", "changed": []}
        else:
            after_hashes, changed = transactional_publish(video_id, source_raw, args)
            if not same_hashes(after_hashes, source_hashes):
                raise RuntimeError(f"destination parity mismatch after publish: {video_id}")
            result = {"rank": entry["rank"], "video_id": video_id, "status": "promoted", "changed": changed}
        result["source_hashes"] = source_hashes
        result["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 3)
        results.append(result)
        atomic_json(args.job_dir / "episode_receipts" / f"{entry['rank']:03d}_{video_id}.json", result)
        atomic_json(args.job_dir / "reconciliation_receipt.partial.json", {
            "schema_version": "1.0.0", "kind": "transcript_root_reconciliation_receipt",
            "epic_id": EPIC_ID, "updated_at": now(), "terminal_results": results,
            "next_rank": episodes[len(results)]["rank"] if len(results) < len(episodes) else None,
        })
    return {"schema_version": "1.0.0", "kind": "transcript_root_reconciliation_receipt", "epic_id": EPIC_ID,
            "completed_at": now(), "terminal_results": results,
            "status_counts": dict(Counter(result["status"] for result in results))}


def close(args: argparse.Namespace, episodes: list[dict[str, Any]], protected_before: dict[str, str]) -> dict[str, Any]:
    inventory = build_inventory(args.data_root, args.priority_queue)
    counts = inventory["source_state_counts"]
    if counts != {"ready_for_gold": 285}:
        raise RuntimeError(f"active source inventory is not 285 ready: {counts}")
    parity: list[dict[str, Any]] = []
    for entry in episodes:
        video_id = str(entry["video_id"])
        _, source_hashes = fetch_source(video_id, args)
        destination_hashes = {name: hash_bytes(raw) for name, raw in destination_bytes(video_id, args.data_root).items()}
        if not same_hashes(source_hashes, destination_hashes):
            raise RuntimeError(f"final parity mismatch: {video_id}")
        parity.append({"rank": entry["rank"], "video_id": video_id, "hashes": source_hashes})
    protected_after = protected_fingerprints(args.data_root, [str(item["video_id"]) for item in episodes])
    protected_diff = {"before": protected_before, "after": protected_after,
                      "changed": sorted({*protected_before, *protected_after} - {path for path in protected_before if protected_before.get(path) == protected_after.get(path)})}
    if protected_diff["changed"]:
        raise RuntimeError("protected artifact changed")
    return {"inventory": inventory, "parity": parity, "protected_diff": protected_diff}


def main() -> int:
    started = time.perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--priority-queue", required=True, type=Path)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--distribution", default="Ubuntu-24.04")
    parser.add_argument("--wsl-user", default="luish")
    parser.add_argument("--job-dir", required=True, type=Path)
    parser.add_argument("--staging-root", required=True, type=Path)
    args = parser.parse_args()
    manifest, episodes = load_and_validate_manifest(args)
    if manifest["source"]["distribution"] != args.distribution or args.source_root != manifest["source"]["data_root"]:
        raise ValueError("source distribution/root do not match manifest")
    args.job_dir.mkdir(parents=True, exist_ok=True)
    protected_before = protected_fingerprints(args.data_root, [str(item["video_id"]) for item in episodes])
    preflight_report = preflight(args, episodes)
    atomic_json(args.job_dir / "preflight_report.json", preflight_report)
    receipt = materialize(args, episodes, preflight_report)
    atomic_json(args.job_dir / "reconciliation_receipt.json", receipt)
    closure = close(args, episodes, protected_before)
    atomic_json(args.job_dir / "root_parity_report.json", {"schema_version": "1.0.0", "kind": "root_parity_report", "epic_id": EPIC_ID, "created_at": now(), **closure["inventory"], "parity": closure["parity"]})
    atomic_json(args.job_dir / "protected_artifact_diff.json", {"schema_version": "1.0.0", "kind": "protected_artifact_diff", "epic_id": EPIC_ID, "created_at": now(), **closure["protected_diff"]})
    atomic_json(args.job_dir / "reconciliation_receipt.json", {**receipt, "closed_at": now(), "status": "passed"})
    (args.job_dir / "process_learnings.md").write_text(
        "# MSF-R20 transcript-root reconciliation learnings\n\n"
        f"- Episodes terminal: {len(receipt['terminal_results'])}.\n"
        f"- Outcomes: {json.dumps(receipt['status_counts'], ensure_ascii=False)}.\n"
        f"- Total elapsed ms: {round((time.perf_counter() - started) * 1000, 3)}.\n"
        "- Source bytes were copied from Ubuntu through direct WSL `cat` calls; no ASR or JSON normalization occurred.\n"
        "- All protected-artifact fingerprints remained unchanged.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "passed", "terminal_count": len(receipt["terminal_results"]), "status_counts": receipt["status_counts"], "readiness": closure["inventory"]["source_state_counts"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({"status": "failed", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
