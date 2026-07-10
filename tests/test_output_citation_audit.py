from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_output_citations import (  # noqa: E402
    CLASS_CROSS_RELEVANT,
    CLASS_CROSS_WEAK,
    CLASS_LOW_SCORE,
    CLASS_MISSING,
    CLASS_ON_TAG,
    audit_citation_audit,
    reviewed_cross_tags_from_audit,
)


def item(insight_id: str, tags: list[str], score: int = 95) -> dict[str, object]:
    return {
        "insight_id": insight_id,
        "episode_video_id": "podcast-001",
        "title": insight_id,
        "editorial_score": score,
        "process_tags": tags,
    }


def test_audit_classifies_all_citation_types() -> None:
    pool = {
        "on": item("on", ["process-copy-anuncios"]),
        "reviewed": item("reviewed", ["process-mecanismo-big-idea"]),
        "weak": item("weak", ["process-prova-depoimentos"]),
        "low": item("low", ["process-copy-anuncios"], score=89),
    }
    citation_audit = {
        "pairs": [
            {
                "pair_id": "P1",
                "briefing_id": "fixture",
                "insights": [
                    {"insight_id": "on"},
                    {"insight_id": "reviewed"},
                    {"insight_id": "weak"},
                    {"insight_id": "low"},
                    {"insight_id": "missing"},
                ],
            }
        ]
    }

    result = audit_citation_audit(
        citation_audit,
        pool,
        target_tag="process-copy-anuncios",
        min_editorial_score=90,
        reviewed_cross_tags={("P1", "reviewed")},
    )

    counts = result["classification_counts"]
    assert counts[CLASS_ON_TAG] == 1
    assert counts[CLASS_CROSS_RELEVANT] == 1
    assert counts[CLASS_CROSS_WEAK] == 1
    assert counts[CLASS_LOW_SCORE] == 1
    assert counts[CLASS_MISSING] == 1
    assert result["status"] == "FAIL"


def test_reviewed_cross_tag_can_pass_when_no_weak_or_missing() -> None:
    pool = {
        "on": item("on", ["process-copy-anuncios"]),
        "reviewed": item("reviewed", ["process-mecanismo-big-idea"]),
    }
    citation_audit = {
        "pairs": [
            {
                "pair_id": "P2",
                "briefing_id": "fixture",
                "with_skill_insight_ids": ["on", "reviewed"],
            }
        ]
    }

    result = audit_citation_audit(
        citation_audit,
        pool,
        target_tag="process-copy-anuncios",
        min_editorial_score=90,
        reviewed_cross_tags={("P2", "reviewed")},
    )

    assert result["classification_counts"][CLASS_ON_TAG] == 1
    assert result["classification_counts"][CLASS_CROSS_RELEVANT] == 1
    assert result["classification_counts"][CLASS_CROSS_WEAK] == 0
    assert result["status"] == "PASS"


def test_reviewed_cross_tag_can_come_from_audit_payload() -> None:
    payload = {
        "cross_tag_reviews": [
            {
                "pair_id": "P3",
                "insight_id": "reviewed",
                "classification": CLASS_CROSS_RELEVANT,
            }
        ]
    }

    assert reviewed_cross_tags_from_audit(payload) == {("P3", "reviewed")}
