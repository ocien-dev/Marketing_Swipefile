from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

from scripts.gold_extraction_common import sha256_semantic_json
from scripts.gold_final_audit_bundle import (
    DOSSIER_CANDIDATE_COLUMNS,
    build_reaudit_delta,
    validate_reaudit_delta,
)
from scripts.gold_review_autocheck import (
    numeric_occurrence_matrix,
    review_audit_warnings,
    semantic_coverage_workbench,
    semantic_closure_index,
)
from scripts.gold_review_compiler import _compile_themes, _source_canonical_number_raw
from scripts import record_gold_external_audit


def _segment(video_id: str, index: int, text: str) -> dict:
    return {
        "segment_id": f"{video_id}-transcript-{index + 1:04d}",
        "clean_index": index,
        "start_seconds": float(index),
        "duration_seconds": 1.0,
        "text": text,
    }


def _candidate(video_id: str, evidence: list[dict], **overrides: object) -> dict:
    candidate = {
        "candidate_id": f"{video_id}-G001",
        "source_claim": "O metodo gerou sucesso em ofertas durante 2023.",
        "type": "reported_case",
        "numbers": [],
        "steps": [],
        "caveats": [],
        "relations": {"parent_candidate_id": None, "child_candidate_ids": []},
        "evidence": {"minimal_quote": evidence, "support_segments": []},
    }
    candidate.update(overrides)
    return candidate


def test_semantic_closure_prioritizes_trajectory_claim_support_and_counterexample():
    video_id = "pilot008"
    transcript = [
        _segment(video_id, 0, "O metodo foi demonstrado em ofertas."),
        _segment(video_id, 1, "Em 2023 foram 13 ofertas, cerca de 10 tiveram sucesso e passaram de 1 milhao."),
        _segment(video_id, 2, "Em outra demonstracao, o mesmo metodo falhou e nao vendeu."),
    ]
    candidate = _candidate(video_id, [{
        "segment_id": transcript[0]["segment_id"],
        "quote_verbatim": transcript[0]["text"],
    }])
    signals = [
        {"segment_id": transcript[1]["segment_id"], "signal_types": ["number", "comparison"]},
        {"segment_id": transcript[2]["segment_id"], "signal_types": ["experiment", "warning"]},
    ]

    closure = semantic_closure_index(transcript, [], [candidate], signals)

    assert any(
        item["review_requirement"] == "must_close"
        and {"numeric", "outcome"} <= set(item["risk_reasons"])
        for item in closure
    )
    assert any("claim_support_gap" in item.get("closure_kinds", []) for item in closure)
    assert any("counterexample" in item.get("closure_kinds", []) for item in closure)


def test_semantic_closure_audit_only_does_not_gate_but_high_risk_requires_source_scope():
    warnings = [{
        "category": "semantic_closure",
        "kind": "audit_warning",
        "items": [
            {
                "closure_kind": "evidence_containment",
                "review_requirement": "audit_only",
                "candidate_ids": ["episode-G001", "episode-G002"],
                "segment_ids": ["episode-transcript-0001"],
                "issue": "possible lexical overlap",
            },
            {
                "closure_kind": "adjacent_evidence_tail",
                "review_requirement": "must_close",
                "candidate_ids": ["episode-G001"],
                "segment_ids": ["episode-transcript-0002"],
                "risk_reasons": ["numeric", "outcome"],
                "issue": "material numeric outcome",
            },
        ],
    }]
    _, inventory, unresolved = review_audit_warnings(
        warnings, required_categories={"semantic_closure"},
    )
    assert len(unresolved) == 1
    must_close_id = next(
        item["warning_id"]
        for item in inventory
        if item["evidence"].get("review_requirement") == "must_close"
    )

    _, _, unresolved = review_audit_warnings(warnings, [{
        "warning_id": must_close_id,
        "disposition": "incidental",
        "justification": "Reviewed in source context.",
    }], required_categories={"semantic_closure"})
    assert unresolved

    _, _, unresolved = review_audit_warnings(warnings, [{
        "warning_id": must_close_id,
        "disposition": "incidental",
        "justification": "The value is a date marker, not a result claim.",
        "source_segment_ids": ["episode-transcript-0002"],
    }], required_categories={"semantic_closure"})
    assert unresolved == []


def test_semantic_workbench_covers_source_and_surfaces_economic_product_and_binding_gaps():
    video_id = "workbench"
    transcript = [
        _segment(video_id, 884, "O custo mensal caiu e a economia por funcionario mudou a margem."),
        _segment(video_id, 885, "O plano custa 30 por mes e substitui duas contratacoes."),
        _segment(video_id, 889, "O trial sem cadastro trouxe feedback de clientes para o roadmap."),
        _segment(video_id, 890, "Depois medimos ativacao, retencao e product market fit."),
        _segment(video_id, 989, "O PMF apareceu depois de entrevistar clientes e ajustar o produto."),
    ]
    wrong_evidence = [{
        "segment_id": transcript[0]["segment_id"],
        "quote_verbatim": transcript[0]["text"],
    }]
    candidate = _candidate(
        video_id,
        wrong_evidence,
        candidate_id=f"{video_id}-G051",
        source_claim="O product market fit apareceu apos entrevistas e ajustes no produto.",
        takeaway_applicavel="Use entrevistas para validar product market fit.",
    )
    calibration = {
        "tests": [{
            "calibration_id": "pmf-target",
            "segment_ids": [transcript[-1]["segment_id"]],
            "quote_verbatim": transcript[-1]["text"],
            "semantic_candidate_ids": [candidate["candidate_id"]],
        }],
    }
    decisions = [{
        "segment_id": transcript[0]["segment_id"],
        "disposition": "captured",
        "candidate_ids": [candidate["candidate_id"]],
    }]
    workbench = semantic_coverage_workbench(
        transcript, [candidate], [], calibration, decisions, max_block_segments=2
    )

    reconstructed = [
        index
        for block in workbench["coverage_blocks"]
        for index in range(block["clean_index_range"][0], block["clean_index_range"][1] + 1)
        if index in {item["clean_index"] for item in transcript}
    ]
    assert reconstructed == [item["clean_index"] for item in transcript]
    must_close_reasons = {
        reason
        for item in workbench["review_order"] if item.get("review_requirement") == "must_close"
        for reason in item.get("risk_reasons", [])
    }
    assert "economic_or_unit_economics" in must_close_reasons
    assert "product_or_customer_learning" in must_close_reasons
    assert workbench["candidate_bindings"][0]["requires_review"] is True
    assert workbench["calibration_bindings"][0]["requires_review"] is True
    assert workbench["calibration_bindings"][0]["suggested_candidate_ids"] == [candidate["candidate_id"]]


def test_numeric_matrix_detects_structured_value_mismatch_and_adjacent_trajectory():
    video_id = "numeric"
    transcript = [
        _segment(video_id, 0, "A versao atual tem 30 minutos."),
        _segment(video_id, 1, "Antes custava R$ 6 mil e depois caiu para R$ 2,5 mil."),
    ]
    candidate = _candidate(
        video_id,
        [{"segment_id": transcript[0]["segment_id"], "quote_verbatim": transcript[0]["text"]}],
        source_claim="A versao atual tem 30 minutos.",
        numbers=[{
            "raw": "30",
            "value": 2,
            "min_value": None,
            "max_value": None,
            "unit_kind": "duration",
            "unit": "minutes",
            "period": None,
            "role": "duration",
            "value_status": "reported",
        }],
    )
    signals = [
        {"segment_id": transcript[0]["segment_id"], "signal_types": ["number"]},
        {"segment_id": transcript[1]["segment_id"], "signal_types": ["number", "comparison"]},
    ]

    matrix = numeric_occurrence_matrix(transcript, [candidate], signals)

    assert matrix[0]["record_consistency_issues"][0]["literal_values"] == [30.0]
    assert matrix[0]["record_consistency_issues"][0]["structured_values"] == [2.0]
    adjacent_raw = {item["raw"] for item in matrix[0]["adjacent_occurrences"]}
    assert {"R$ 6 mil", "R$ 2,5 mil"} <= adjacent_raw


def test_numeric_matrix_allows_explicit_caveated_asr_scale_correction():
    video_id = "numeric-asr"
    transcript = [_segment(video_id, 0, "A conversao saiu de 0,17 para 030.")]
    candidate = _candidate(
        video_id,
        [{"segment_id": transcript[0]["segment_id"], "quote_verbatim": transcript[0]["text"]}],
        source_claim="A conversao relatada saiu de 0,17% para 0,30%.",
        numbers=[{
            "raw": "030",
            "value": 0.30,
            "min_value": None,
            "max_value": None,
            "unit_kind": "percent",
            "unit": "percentual de conversao",
            "period": None,
            "role": "result",
            "value_status": "inferred",
        }],
    )
    candidate["caveats"] = [
        "O literal ASR '030' foi estruturado como 0,30%; a quote permanece inalterada."
    ]

    matrix = numeric_occurrence_matrix(
        transcript,
        [candidate],
        [{"segment_id": transcript[0]["segment_id"], "signal_types": ["number", "comparison"]}],
    )

    assert matrix[0]["record_consistency_issues"] == []


def test_source_literal_is_copied_exactly_and_ambiguous_literal_is_rejected():
    segment = _segment("literal", 0, "Caiu de R$ 6 mil para R$ 2,5 mil.")
    record = {
        "source_segment_id": segment["segment_id"],
        "source_literal": "R$ 2,5 mil",
    }
    issues: list[dict] = []
    _source_canonical_number_raw(
        "literal-G001",
        record,
        evidence_segment_ids={segment["segment_id"]},
        segments={segment["segment_id"]: segment},
        segments_by_index={0: segment},
        issues=issues,
    )
    assert issues == []
    assert record["raw"] == "R$ 2,5 mil"

    ambiguous = _segment("literal", 1, "Foram 30 dias, depois mais 30 dias.")
    record = {
        "source_segment_id": ambiguous["segment_id"],
        "source_literal": "30 dias",
    }
    issues = []
    _source_canonical_number_raw(
        "literal-G002",
        record,
        evidence_segment_ids={ambiguous["segment_id"]},
        segments={ambiguous["segment_id"]: ambiguous},
        segments_by_index={1: ambiguous},
        issues=issues,
    )
    assert issues
    assert "raw" not in record


def test_unknown_theme_scaffold_suggests_closed_options_without_auto_mapping():
    for source, expected_suggestions in {
        "storytelling": {"copywriting"},
        "competitive_analysis": {"audience_market", "creative_strategy"},
        "affiliate_marketing": {"business_model", "sales_relationship"},
        "product_development": {"product_strategy", "delivery_support"},
    }.items():
        issues: list[dict] = []
        themes, subthemes = _compile_themes("episode-G001", [source], [], issues)
        assert themes == []
        assert subthemes == [source]
        assert len(issues) == 1
        assert all(value in issues[0]["expected"] for value in expected_suggestions)


def _dossier_row(candidate_id: str, evidence_index: int) -> list:
    values = {column: None for column in DOSSIER_CANDIDATE_COLUMNS}
    values.update({
        "candidate_id": candidate_id,
        "numbers": [],
        "relations": {"parent_candidate_id": None, "child_candidate_ids": []},
        "minimal_clean_indexes": [evidence_index],
        "support_clean_indexes": [],
    })
    return [values[column] for column in DOSSIER_CANDIDATE_COLUMNS]


def _write_dossier(path: Path, candidate_rows: list[list], verified_at: str) -> None:
    packet = {
        "valid_five_file_packet": True,
        "names": [
            "calibration_tests.json",
            "high_signal_coverage_ledger.json",
            "insights_exhaustive.json",
            "packet_manifest.json",
            "transcript_clean.json",
        ],
        "files": [],
    }
    records = [
        {
            "record_type": "header",
            "episode_video_id": "episode",
            "candidate_columns": DOSSIER_CANDIDATE_COLUMNS,
            "protected_fingerprints": {
                "before": {"raw": "same", "metadata": "same"},
                "after": {"raw": "same", "metadata": "same"},
                "verified_at": verified_at,
            },
            "packet": packet,
        },
        *({"record_type": "candidate", "value": row} for row in candidate_rows),
        {"record_type": "calibration", "value": {"status": "pass"}},
        {
            "record_type": "transcript_block",
            "value": [[10, 10.0, 1.0, "Em 2023 foram 13 ofertas.", "excluded", [], "low_signal", None]],
        },
    ]
    footer = {
        "record_type": "footer",
        "content_semantic_sha256": sha256_semantic_json(records),
    }
    path.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in [*records, footer]) + "\n",
        encoding="utf-8",
    )


def test_reaudit_delta_scopes_insert_by_finding_range_and_ignores_verified_at(tmp_path):
    before = tmp_path / "before.jsonl"
    after = tmp_path / "after.jsonl"
    _write_dossier(before, [_dossier_row("episode-G001", 0)], "before")
    _write_dossier(
        after,
        [_dossier_row("episode-G001", 0), _dossier_row("episode-G049", 10)],
        "after",
    )
    audit = {
        "episode_video_id": "episode",
        "findings": [{
            "finding_id": "AUD-001",
            "category": "numeric_recall",
            "required_action": "Capture the omitted 2023 trajectory.",
            "segment_range": [10, 10],
            "candidate_ids": [],
        }],
    }

    delta = build_reaudit_delta(before, after, audit)

    assert delta["changed_candidate_ids"] == ["episode-G049"]
    assert delta["range_scoped_candidate_ids"] == ["episode-G049"]
    assert delta["unscoped_changed_candidate_ids"] == []
    assert validate_reaudit_delta(delta) == []


def test_audit_envelope_base64_materializes_job_local_without_episode_write(
    tmp_path, monkeypatch, capsys,
):
    envelope = {
        "episode_video_id": "episode",
        "audit_route": "final_model_review",
        "reviewer": "Codex final model review",
        "reviewer_thread_id": "reviewer",
        "reviewer_model": "gpt-5.6-sol",
        "reasoning_effort": "high",
        "reviewed_at": "2026-07-17T00:00:00Z",
        "status": "passed",
        "summary": "The source-complete audit passed.",
        "findings": [],
        "open_findings": 0,
    }
    encoded = base64.b64encode(
        json.dumps(envelope, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")
    output = tmp_path / "job" / "audit.json"
    data_root = tmp_path / "data"
    monkeypatch.setattr(sys, "argv", [
        "record_gold_external_audit.py",
        "--video-id", "episode",
        "--data-root", str(data_root),
        "--input-base64", encoded,
        "--envelope-output", str(output),
    ])

    assert record_gold_external_audit.main() == 0

    result = json.loads(capsys.readouterr().out)
    assert result["episode_artifacts_written"] is False
    assert result["envelope"]["semantic_sha256"] == sha256_semantic_json(envelope)
    assert json.loads(output.read_text(encoding="utf-8")) == envelope
    assert not (data_root / "processed").exists()
