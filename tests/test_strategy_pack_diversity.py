#!/usr/bin/env python
"""Fixture checks for strategy-pack diversity selection."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_strategy_pack import load_insights, rank_insights  # noqa: E402


FIXTURE = ROOT / "tests" / "fixtures" / "strategy_pack_diversity_fixture.json"


def args(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "task": "vsl",
        "product": "oferta low ticket",
        "avatar": "infoprodutor",
        "market": "infoprodutos",
        "asset_type": "VSL",
        "query": "low ticket VSL promessa oferta prova objecao trafego",
        "min_confidence": 0.0,
        "limit": 2,
        "diversity_weight": 0.8,
        "episode_cap": 3,
        "thesis_cap": 1,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_near_duplicates_are_suppressed() -> None:
    selected = rank_insights(load_insights(FIXTURE), args())
    ids = [item["insight_id"] for item in selected]
    assert ids[0] == "fixture-v2-0001", ids
    assert "fixture-v2-0002" not in ids, ids
    assert any(item["similarity_to_selected"] < 0.7 for item in selected[1:])


def test_episode_cap_limits_top_n() -> None:
    selected = rank_insights(
        load_insights(FIXTURE),
        args(limit=4, diversity_weight=0.0, episode_cap=3),
    )
    counts = Counter(item["episode_video_id"] for item in selected)
    assert len(selected) == 4
    assert counts["episode-a"] == 3
    assert counts["episode-b"] == 1


if __name__ == "__main__":
    test_near_duplicates_are_suppressed()
    test_episode_cap_limits_top_n()
    print("VALID strategy_pack_diversity_fixture")
