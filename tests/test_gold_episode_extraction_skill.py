from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "gold-episode-extraction" / "scripts" / "build_gold_risk_brief.py"
SKILL = ROOT / "skills" / "gold-episode-extraction" / "SKILL.md"
SPEC = importlib.util.spec_from_file_location("build_gold_risk_brief", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write_dossier(path: Path) -> None:
    columns = [
        "candidate_id", "chunk_id", "title", "type", "themes", "subthemes", "process_tags",
        "source_claim", "takeaway_applicavel", "context", "reported_case", "causal_certainty",
        "claim_risk", "numbers", "steps", "conditions", "caveats", "relations",
        "minimal_clean_indexes", "support_clean_indexes",
    ]
    candidate = {
        "candidate_id": "episode-G001",
        "chunk_id": "episode-gold-chunk-001",
        "title": "Testar o limite",
        "type": "principle",
        "themes": ["testing_measurement"],
        "subthemes": [],
        "process_tags": [],
        "source_claim": "O limite pode ser 95.",
        "takeaway_applicavel": "Preserve o limite reportado.",
        "context": {},
        "reported_case": True,
        "causal_certainty": "reported_attribution",
        "claim_risk": "medium",
        "numbers": [{"raw": "95", "value": 95, "unit_kind": "percentage", "role": "threshold"}],
        "steps": [],
        "conditions": [],
        "caveats": ["Sem validacao independente."],
        "relations": {"parent_candidate_id": None, "child_candidate_ids": []},
        "minimal_clean_indexes": [8, 9],
        "support_clean_indexes": [],
    }
    rows = [
        [0, 0.0, 1.0, "primeiro entregue valor", "excluded", [], "low_signal", None],
        [1, 1.0, 1.0, "por cinco segundos", "excluded", [], "low_signal", None],
        [2, 2.0, 1.0, "depois introduza o mecanismo", "excluded", [], "low_signal", None],
        [3, 3.0, 1.0, "e puxe para a mensagem de vendas", "excluded", [], "low_signal", None],
        [4, 4.0, 1.0, "um som escolhido pelo publico", "excluded", [], "low_signal", None],
        [5, 5.0, 1.0, "aumentou as vendas", "excluded", [], "low_signal", None],
        [6, 6.0, 1.0, "na segunda semana foram 50 mil", "excluded", [], "low_signal", None],
        [7, 7.0, 1.0, "depois caiu para 30 mil", "excluded", [], "low_signal", None],
        [8, 8.0, 1.0, "pode ser 95", "captured", ["episode-G001"], None, None],
        [9, 9.0, 1.0, "95 como limite", "captured", ["episode-G001"], None, None],
    ]
    records = [
        {
            "record_type": "header",
            "kind": "gold_final_audit_dossier",
            "schema_version": "3.0.0",
            "episode_video_id": "episode",
            "candidate_columns": columns,
            "segment_count": len(rows),
            "candidate_count": 1,
            "audit_warnings": [{
                "category": "numeric_support_ambiguity",
                "items": [{
                    "candidate_id": "episode-G001",
                    "segment_ids": ["episode-transcript-0009", "episode-transcript-0010"],
                    "issue": "support-only numeric evidence needs semantic confirmation: 95",
                    "warning_id": "warning-95",
                }],
            }],
        },
        {"record_type": "candidate", "value": [candidate.get(column) for column in columns]},
        {
            "record_type": "numeric_coverage",
            "value": {
                "candidate_id": "episode-G001",
                "status": "warning",
                "record_count": 1,
                "mentions": [
                    {"segment_id": "episode-transcript-0009", "layer": "minimal", "raw": "95", "canonical": "95", "kind": "bare", "record_index": 0},
                    {"segment_id": "episode-transcript-0010", "layer": "minimal", "raw": "95", "canonical": "95", "kind": "bare", "record_index": None},
                ],
                "missing_material": [],
                "audit_warnings": [],
            },
        },
        {"record_type": "transcript_block", "value": rows},
        {"record_type": "footer", "record_count": 3, "content_semantic_sha256": "fixture"},
    ]
    path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in records) + "\n", encoding="utf-8")


def test_dossier_brief_prioritizes_mechanism_outcome_trajectory_and_numeric_multiplicity(tmp_path):
    dossier = tmp_path / "dossier.jsonl"
    _write_dossier(dossier)

    brief = MODULE.build_brief(dossier)

    categories = {item["category"] for item in brief["review_order"]}
    assert "numeric_support_ambiguity" in categories
    assert {"mechanism_sequence", "numeric_trajectory", "numeric_result", "reported_outcome"} & categories
    matrix = brief["numeric_occurrence_matrix"]
    assert matrix[0]["candidate_id"] == "episode-G001"
    assert matrix[0]["occurrence_count"] == 2
    assert matrix[0]["record_count"] == 1
    assert matrix[0]["potential_multiplicity_gap"] == 1


def test_dossier_brief_prefers_semantic_workbench_over_second_broad_scan(tmp_path):
    dossier = tmp_path / "dossier-workbench.jsonl"
    _write_dossier(dossier)
    records = [json.loads(line) for line in dossier.read_text(encoding="utf-8").splitlines()]
    records.insert(-1, {
        "record_type": "semantic_workbench",
        "value": {
            "semantic_sha256": "workbench-hash",
            "summary": {"must_close_count": 1},
            "coverage_blocks": [{"clean_index_range": [4, 7], "state": "unreviewed"}],
            "review_order": [{
                "closure_kind": "uncovered_material",
                "clean_index_range": [4, 7],
                "segment_ids": ["episode-transcript-0005"],
                "risk_score": 10,
                "risk_reasons": ["economic_or_unit_economics"],
                "review_requirement": "must_close",
                "issue": "material source block is not bound",
            }],
            "candidate_bindings": [{"candidate_id": "episode-G001", "requires_review": True}],
            "calibration_bindings": [{"calibration_id": "cal-1", "requires_review": True}],
        },
    })
    dossier.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in records) + "\n",
        encoding="utf-8",
    )

    brief = MODULE.build_brief(dossier)

    assert brief["summary"]["navigation_source"] == "semantic_workbench"
    assert brief["coverage_workbench"]["semantic_sha256"] == "workbench-hash"
    assert brief["candidate_bindings"][0]["candidate_id"] == "episode-G001"
    assert brief["calibration_bindings"][0]["calibration_id"] == "cal-1"


def test_prelint_brief_collapses_reviewed_incidental_and_keeps_real_numeric_risk(tmp_path):
    prelint = tmp_path / "prelint.json"
    prelint.write_text(json.dumps({
        "episode_video_id": "episode",
        "status": "needs_revision",
        "prelint_inventory": {
            "hard_blockers": [{
                "category": "numbers",
                "items": [{
                    "candidate_id": "episode-G002",
                    "numeric_mention": {
                        "candidate_id": "episode-G002",
                        "segment_id": "episode-transcript-0020",
                        "raw": "40 semana",
                        "canonical": "40 semana",
                        "kind": "count",
                        "record_index": None,
                    },
                    "issue": "material number is missing",
                }],
            }],
            "semantic_closure_index": [{
                "category": "semantic_closure",
                "items": [{
                    "warning_id": "closure-incidental",
                    "text": "transicao sem proposicao nova",
                    "review": {"disposition": "incidental", "justification": "restatement"},
                }],
            }],
        },
    }, ensure_ascii=False), encoding="utf-8")

    brief = MODULE.build_brief(prelint)

    assert brief["review_order"][0]["source_category"] == "numbers"
    assert brief["numeric_occurrence_matrix"][0]["occurrences"][0]["raw"] == "40 semana"
    assert brief["collapsed_low_risk"] == {"reviewed_incidental_semantic_closure": 1}


def test_brief_is_deterministic_and_does_not_modify_source(tmp_path):
    dossier = tmp_path / "dossier.jsonl"
    _write_dossier(dossier)
    before = dossier.read_bytes()

    first = MODULE.build_brief(dossier)
    second = MODULE.build_brief(dossier)

    assert first == second
    assert dossier.read_bytes() == before


def test_risk_brief_deduplicates_lineage_and_stays_below_50_kb(tmp_path):
    dossier = tmp_path / "dossier.jsonl"
    _write_dossier(dossier)
    records = [json.loads(line) for line in dossier.read_text(encoding="utf-8").splitlines()]
    records[0]["audit_warnings"] = [{
        "category": "semantic_closure",
        "items": [
            {
                "closure_id": f"closure-{index}",
                "lineage_id": "lineage-material-trajectory",
                "review_requirement": "must_close",
                "candidate_ids": ["episode-G001"],
                "segment_ids": ["episode-transcript-0007", "episode-transcript-0008"],
                "clean_index_range": [6, 7],
                "text": "Na segunda semana foram 50 mil e depois caiu para 30 mil.",
                "issue": "numeric trajectory must be reviewed",
            }
            for index in range(120)
        ],
    }]
    dossier.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in records) + "\n",
        encoding="utf-8",
    )

    brief = MODULE.build_brief(dossier)
    encoded = json.dumps(brief, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    assert sum(item.get("lineage_id") == "lineage-material-trajectory" for item in brief["review_order"]) == 1
    assert len(encoded) < 50_000


def test_skill_uses_semantic_index_as_navigation_without_replacing_full_read():
    instructions = SKILL.read_text(encoding="utf-8")

    assert "transcript_semantic_index_status.json" in instructions
    assert "transcript_semantic_index" in instructions
    assert "sem pular a leitura cronologica" in instructions
    assert "o transcript cronologico continua obrigatorio" in instructions
