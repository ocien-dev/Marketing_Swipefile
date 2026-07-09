#!/usr/bin/env python
"""Fixture checks for process_tags retrieval filters."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_strategy_pack import build_pack, load_insights, rank_insights  # noqa: E402
from msf_common import CURATED_UNAVAILABLE_STATE, POOL_UNAVAILABLE_STATE, UNFOUNDED_OUTPUT_BANNER, retrieval_source_state  # noqa: E402
from search_insights import render_markdown as render_search_markdown  # noqa: E402
from search_insights import search  # noqa: E402


FIXTURE = ROOT / "tests" / "fixtures" / "strategy_pack_diversity_fixture.json"


def strategy_args(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "master": FIXTURE,
        "source": "curated",
        "task": "oferta",
        "product": "oferta low ticket",
        "avatar": "infoprodutor",
        "market": "infoprodutos",
        "asset_type": "strategy pack",
        "query": "prova oferta low ticket",
        "constraints": None,
        "process_tags": ["process-prova-depoimentos"],
        "process_tag_mode": "any",
        "min_confidence": 0.0,
        "min_editorial_score": 0.0,
        "limit": 5,
        "diversity_weight": 0.3,
        "episode_cap": 3,
        "thesis_cap": 1,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def search_args(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "query": None,
        "source": "curated",
        "master": FIXTURE,
        "theme": None,
        "level": None,
        "insight_type": None,
        "source_kind": None,
        "episode": None,
        "asset_id": None,
        "applicability": None,
        "process_tags": ["process-copy-vsl"],
        "process_tag_mode": "any",
        "min_confidence": 0.0,
        "min_editorial_score": 0.0,
        "limit": 20,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_search_filters_by_process_tags() -> None:
    results = search(load_insights(FIXTURE), search_args())
    assert results
    assert all("process-copy-vsl" in item["process_tags"] for item in results)
    assert "fixture-v2-0003" not in {item["insight_id"] for item in results}


def test_strategy_pack_filters_by_process_tags() -> None:
    args = strategy_args()
    selected = rank_insights(load_insights(FIXTURE), args)
    ids = [item["insight_id"] for item in selected]
    assert ids == ["fixture-v2-0005"]

    pack = build_pack(args, load_insights(FIXTURE))
    assert pack["process_tag_filter"]["process_tags"] == ["process-prova-depoimentos"]
    assert [item["insight_id"] for item in pack["usable_insights"]] == ["fixture-v2-0005"]


def test_missing_curated_source_returns_explicit_unavailable_state() -> None:
    missing = ROOT / "tests" / "fixtures" / "missing_curated_insights.json"
    assert retrieval_source_state("curated", missing) == CURATED_UNAVAILABLE_STATE

    args = search_args(master=missing, retrieval_state=CURATED_UNAVAILABLE_STATE)
    markdown = render_search_markdown([], args)
    assert markdown.startswith(UNFOUNDED_OUTPUT_BANNER)
    assert "Retrieval state: curated_unavailable" in markdown


def test_missing_pool_source_returns_explicit_unavailable_state() -> None:
    missing = ROOT / "tests" / "fixtures" / "missing_pool_insights.json"
    assert retrieval_source_state("pool", missing) == POOL_UNAVAILABLE_STATE


if __name__ == "__main__":
    test_search_filters_by_process_tags()
    test_strategy_pack_filters_by_process_tags()
    test_missing_curated_source_returns_explicit_unavailable_state()
    test_missing_pool_source_returns_explicit_unavailable_state()
    print("VALID process_tag_retrieval")
