#!/usr/bin/env python
"""Fixture checks for shared MSF encoding helpers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_insights_v2_text import audit_generated_text  # noqa: E402
from msf_common import (  # noqa: E402
    evidence_traceability_findings,
    mojibake_artifact_contexts,
    orphan_question_mark_contexts,
    transliterate_ascii,
)


def test_transliterate_ascii_removes_accents_by_nfkd() -> None:
    assert transliterate_ascii("cansaco, objecao, prototipo") == "cansaco, objecao, prototipo"
    assert transliterate_ascii("cansa\u00e7o, obje\u00e7\u00e3o, prot\u00f3tipo") == "cansaco, objecao, prototipo"


def test_orphan_question_mark_flags_single_and_repeated_mid_word_mojibake() -> None:
    text = "A obje??o aparece no briefing. Prot?tipo tambem aparece. Tambem tem \ufffd."
    contexts = mojibake_artifact_contexts(text)
    excerpts = [item["excerpt"] for item in contexts]
    finding_types = [item["finding_type"] for item in contexts]
    assert "replacement_character" in finding_types
    assert any("obje??o" in context for context in excerpts)
    assert any("Prot?tipo" in context for context in excerpts)


def test_orphan_question_mark_legacy_helper_returns_question_mark_contexts_only() -> None:
    text = "A obje??o aparece no briefing. Prot?tipo tambem aparece." + (" " * 120) + "Tambem tem \ufffd."
    contexts = orphan_question_mark_contexts(text)
    assert any("obje??o" in context for context in contexts)
    assert any("Prot?tipo" in context for context in contexts)
    assert not any("\ufffd" in context for context in contexts)


def test_auditor_flags_repeated_mid_word_question_marks() -> None:
    fixture = ROOT / ".tmp" / "encoding-tests" / "audit_fixture.md"
    fixture.parent.mkdir(parents=True, exist_ok=True)
    fixture.write_text("A obje??o e o Prot?tipo devem falhar.\nFunciona? Sim.\n", encoding="utf-8")

    findings = audit_generated_text(fixture)

    assert [item["finding_type"] for item in findings] == [
        "orphan_question_mark",
        "orphan_question_mark",
    ]
    assert any("obje??o" in item["excerpt"] for item in findings)
    assert any("Prot?tipo" in item["excerpt"] for item in findings)


def test_auditor_flags_replacement_character() -> None:
    fixture = ROOT / ".tmp" / "encoding-tests" / "replacement_fixture.md"
    fixture.parent.mkdir(parents=True, exist_ok=True)
    fixture.write_text("A palavra com \ufffd deve falhar.\nFunciona? Sim.\n", encoding="utf-8")

    findings = audit_generated_text(fixture)

    assert [item["finding_type"] for item in findings] == ["replacement_character"]
    assert "\ufffd" in findings[0]["excerpt"]


def test_orphan_question_mark_allows_legitimate_final_question_marks() -> None:
    text = 'Funciona? Sim. "Qual o proximo passo?" E agora?\nPronto? conjunto?Onde'
    assert orphan_question_mark_contexts(text) == []


def test_evidence_traceability_matches_segment_text() -> None:
    insights_payload = {
        "insights": [
            {
                "insight_id": "ok-1",
                "evidence": [
                    {
                        "segment_id": "seg-1",
                        "quote_original": "Trecho original inteiro.",
                    }
                ],
            }
        ]
    }
    segments_payload = {
        "segments": [
            {
                "segment_id": "seg-1",
                "text_original": "Trecho original inteiro.",
            }
        ]
    }

    assert evidence_traceability_findings(insights_payload, segments_payload) == []


def test_evidence_traceability_flags_non_matching_quote() -> None:
    insights_payload = {
        "insights": [
            {
                "insight_id": "bad-1",
                "evidence": [
                    {
                        "segment_id": "seg-1",
                        "quote_original": "Trecho inventado.",
                    }
                ],
            }
        ]
    }
    segments_payload = {
        "segments": [
            {
                "segment_id": "seg-1",
                "text_original": "Trecho original inteiro.",
            }
        ]
    }

    findings = evidence_traceability_findings(insights_payload, segments_payload)
    assert findings[0]["finding_type"] == "quote_not_in_segment"


if __name__ == "__main__":
    test_transliterate_ascii_removes_accents_by_nfkd()
    test_orphan_question_mark_flags_single_and_repeated_mid_word_mojibake()
    test_orphan_question_mark_legacy_helper_returns_question_mark_contexts_only()
    test_auditor_flags_repeated_mid_word_question_marks()
    test_auditor_flags_replacement_character()
    test_orphan_question_mark_allows_legitimate_final_question_marks()
    test_evidence_traceability_matches_segment_text()
    test_evidence_traceability_flags_non_matching_quote()
    print("VALID msf_common_encoding")
