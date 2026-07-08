#!/usr/bin/env python
"""Fixture checks for shared MSF encoding helpers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_insights_v2_text import audit_generated_text  # noqa: E402
from msf_common import orphan_question_mark_contexts, transliterate_ascii  # noqa: E402


def test_transliterate_ascii_removes_accents_by_nfkd() -> None:
    assert transliterate_ascii("cansaco, objecao, prototipo") == "cansaco, objecao, prototipo"
    assert transliterate_ascii("cansa\u00e7o, obje\u00e7\u00e3o, prot\u00f3tipo") == "cansaco, objecao, prototipo"


def test_orphan_question_mark_flags_single_and_repeated_mid_word_mojibake() -> None:
    text = "A obje??o aparece no briefing. Prot?tipo tambem aparece."
    contexts = orphan_question_mark_contexts(text)
    assert any("obje??o" in context for context in contexts)
    assert any("Prot?tipo" in context for context in contexts)


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


def test_orphan_question_mark_allows_legitimate_final_question_marks() -> None:
    text = 'Funciona? Sim. "Qual o proximo passo?" E agora?\nPronto?'
    assert orphan_question_mark_contexts(text) == []


if __name__ == "__main__":
    test_transliterate_ascii_removes_accents_by_nfkd()
    test_orphan_question_mark_flags_single_and_repeated_mid_word_mojibake()
    test_auditor_flags_repeated_mid_word_question_marks()
    test_orphan_question_mark_allows_legitimate_final_question_marks()
    print("VALID msf_common_encoding")
