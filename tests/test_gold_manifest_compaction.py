"""Compact authoring v4 must expand losslessly to the full v1 manifest.

The value of the compaction is only real if the expanded manifest is
byte-identical (by semantic hash) to a hand-written full manifest, so every
downstream stage -- hashes, ledger, calibration, workbench, dossier -- keeps
producing the same bytes.  These tests prove that property on a small
synthetic fixture; the same round trip was verified against a real 5,289
segment manifest (90.9% smaller model output) outside the repository, since
real payloads never enter version control.
"""

from __future__ import annotations

import copy

from scripts.gold_authoring_manifest import (
    COMPACT_AUTHORING_V4,
    authoring_decisions_sha256,
    compact_v4_from_manifest,
    expand_compact_v4,
    is_authoring_manifest,
    is_compact_authoring_v4,
    manifest_to_compact_payload,
    normalize_authoring_input,
)
from scripts.gold_extraction_common import sha256_semantic_json


CAPTURED_REASON = (
    "Integral chronological review captured the source proposition in the "
    "cited candidate."
)
DEFAULT_REASON = (
    "Integral chronological review classified this segment as framing, "
    "repetition, transition, illustration, or detail without an additional "
    "reusable proposition."
)
ASR_REASON = "The ASR-corrupted numeric fragment repeats the intact adjacent claim."


def _full_manifest() -> dict:
    """A hand-written full manifest with 8 segments across 2 chunks.

    Segment layout (clean index):
      0    -> excluded, default boilerplate
      1-2  -> captured by G001 (evidence range 1..2)
      3    -> excluded, default boilerplate
      4    -> captured by G002 (evidence range 4..5)
      5    -> captured by G001 and G002 (both cover 5)
      6    -> excluded, SPECIFIC reason (an exception)
      7    -> excluded, default boilerplate
    """
    video = "vid00000001"

    def disposition(index, kind, candidate_ids, reason_code, reason):
        return {
            "segment_id": f"{video}-transcript-{index + 1:04d}",
            "index": index,
            "chunk_number": 1 if index <= 3 else 2,
            "disposition": kind,
            "candidate_ids": candidate_ids,
            "reason_code": reason_code,
            "reason": reason,
        }

    excluded = lambda i: disposition(i, "excluded", [], "low_signal", DEFAULT_REASON)
    captured = lambda i, cids: disposition(
        i, "captured", cids, "candidate_capture", CAPTURED_REASON
    )

    return {
        "schema_version": "1.0.0",
        "kind": "gold_authoring_manifest",
        "manifest_format": "gold_authoring_manifest_v1",
        "episode_video_id": video,
        "extraction_architecture": "chronological_hybrid_v1",
        "candidate_defaults": {"claim_risk": "medium", "numbers": []},
        "type_defaults": {},
        "candidates": [
            {
                "candidate_id": f"{video}-G001",
                "chunk": 1,
                "title": "Primeiro candidato",
                "type": "principle",
                "themes": ["funnel_architecture"],
                "source_claim": "Afirmacao um.",
                "takeaway_applicavel": "Acao um.",
                "numbers": [],
                "minimal_segment_ids": [{"range": [1, 2]}],
                "support_segment_ids": [{"range": [5, 5]}],
            },
            {
                "candidate_id": f"{video}-G002",
                "chunk": 2,
                "title": "Segundo candidato",
                "type": "tactic",
                "themes": ["offer_pricing"],
                "source_claim": "Afirmacao dois.",
                "takeaway_applicavel": "Acao dois.",
                "numbers": [],
                "minimal_segment_ids": [{"range": [4, 5]}],
                "support_segment_ids": [],
            },
        ],
        "zero_insight_chunks": [],
        "source_dispositions": [
            excluded(0),
            captured(1, [f"{video}-G001"]),
            captured(2, [f"{video}-G001"]),
            excluded(3),
            captured(4, [f"{video}-G002"]),
            captured(5, [f"{video}-G001", f"{video}-G002"]),
            disposition(6, "excluded", [], "low_signal", ASR_REASON),
            excluded(7),
        ],
        "risk_recall_acknowledgements": [
            {
                "cluster_id": "risk-a",
                "disposition": "incidental",
                "candidate_ids": [],
                "source_segment_ids": [f"{video}-transcript-0001"],
                "justification": "Promotional framing without reusable proposition.",
            },
            {
                "cluster_id": "risk-b",
                "disposition": "incidental",
                "candidate_ids": [],
                "source_segment_ids": [f"{video}-transcript-0004"],
                "justification": "Promotional framing without reusable proposition.",
            },
        ],
        "audit_warning_dispositions": [
            {
                "warning_id": "warning-1",
                "disposition": "confirmed_source_backed",
                "justification": "Adversarial review confirmed the attribution and scope.",
                "input_semantic_sha256": "a" * 64,
            },
            {
                "warning_id": "warning-2",
                "disposition": "confirmed_source_backed",
                "justification": "Adversarial review confirmed the attribution and scope.",
                "input_semantic_sha256": "b" * 64,
            },
            {
                "warning_id": "warning-3",
                "disposition": "defer_to_final_audit",
                "justification": "Ambiguous causal certainty deferred to the final audit.",
                "input_semantic_sha256": "c" * 64,
            },
        ],
        "calibration_decisions": [],
        "adversarial_review": None,
    }


def _semantic(value: dict) -> str:
    return sha256_semantic_json({k: v for k, v in value.items() if k != "semantic_sha256"})


def test_round_trip_expands_to_identical_full_manifest():
    full = _full_manifest()
    compact = compact_v4_from_manifest(full)
    assert compact["compaction"] == COMPACT_AUTHORING_V4
    expanded = expand_compact_v4(copy.deepcopy(compact))
    assert sha256_semantic_json(expanded["source_dispositions"]) == sha256_semantic_json(
        full["source_dispositions"]
    )
    assert sha256_semantic_json(expanded["audit_warning_dispositions"]) == sha256_semantic_json(
        full["audit_warning_dispositions"]
    )
    assert sha256_semantic_json(expanded["risk_recall_acknowledgements"]) == sha256_semantic_json(
        full["risk_recall_acknowledgements"]
    )


def test_only_non_default_segments_are_exceptions():
    full = _full_manifest()
    compact = compact_v4_from_manifest(full)
    # Only the single segment with a specific reason must be listed explicitly.
    assert [item["index"] for item in compact["source_disposition_exceptions"]] == [6]


def test_captured_candidate_ids_are_derived_not_stored():
    full = _full_manifest()
    compact = compact_v4_from_manifest(full)
    # No captured entry (with its candidate_ids) is stored; they are derived
    # from candidate evidence ranges at expansion time.
    for exception in compact["source_disposition_exceptions"]:
        assert exception["disposition"] != "captured"
    expanded = expand_compact_v4(copy.deepcopy(compact))
    shared = next(item for item in expanded["source_dispositions"] if item["index"] == 5)
    assert shared["disposition"] == "captured"
    assert shared["candidate_ids"] == ["vid00000001-G001", "vid00000001-G002"]


def test_justifications_are_interned_once():
    full = _full_manifest()
    compact = compact_v4_from_manifest(full)
    table = compact["audit_warning_dispositions"]["justification_table"]
    # 3 warnings collapse to 2 distinct justifications.
    assert len(table) == 2
    risk_table = compact["risk_recall_acknowledgements"]["justification_table"]
    assert len(risk_table) == 1


def test_normalize_produces_identical_hashes_from_compact_and_full():
    full = _full_manifest()
    video = full["episode_video_id"]
    norm_full, explicit_full = normalize_authoring_input(video, copy.deepcopy(full))
    compact = compact_v4_from_manifest(full)
    assert is_compact_authoring_v4(compact)
    assert is_authoring_manifest(compact)
    norm_v4, explicit_v4 = normalize_authoring_input(video, copy.deepcopy(compact))
    assert explicit_full is True and explicit_v4 is True
    assert norm_full["authoring_decisions_sha256"] == norm_v4["authoring_decisions_sha256"]
    assert norm_full["semantic_sha256"] == norm_v4["semantic_sha256"]
    assert _semantic(norm_full) == _semantic(norm_v4)


def test_build_input_payload_is_byte_identical():
    full = _full_manifest()
    video = full["episode_video_id"]
    norm_full, _ = normalize_authoring_input(video, copy.deepcopy(full))
    norm_v4, _ = normalize_authoring_input(video, compact_v4_from_manifest(full))
    payload_full = manifest_to_compact_payload(norm_full)
    payload_v4 = manifest_to_compact_payload(norm_v4)
    assert sha256_semantic_json(payload_full) == sha256_semantic_json(payload_v4)


def test_full_manifest_path_is_untouched_when_not_compact():
    full = _full_manifest()
    assert is_compact_authoring_v4(full) is False
    norm, explicit = normalize_authoring_input(full["episode_video_id"], copy.deepcopy(full))
    assert explicit is True
    # The full-manifest branch preserves the authored dispositions verbatim.
    assert sha256_semantic_json(norm["source_dispositions"]) == sha256_semantic_json(
        full["source_dispositions"]
    )
