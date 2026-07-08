#!/usr/bin/env python
"""Evaluate generated outputs with a keyword proxy or a Codex rubric judgment.

The old score was keyword based. It is now kept only as
`keyword_presence_check`; a real MSF-R09 evaluation requires a Codex-authored
judgment JSON with criterion scores, justifications, and citation-fidelity
notes, then this script validates and renders the final report.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from msf_common import (
    as_list,
    broken_accent_deletion_matches,
    data_path,
    first_evidence,
    load_json,
    normalize_text,
    write_json,
    write_text,
)


KEYWORD_CRITERIA = {
    "vsl": [
        ("clarity", ["promessa", "promise", "resultado", "beneficio"]),
        ("curiosity", ["curiosidade", "tensao", "lead", "abertura"]),
        ("specificity", ["especifico", "numero", "prazo", "caso"]),
        ("mechanism", ["mecanismo", "metodo", "sistema", "framework"]),
        ("proof", ["prova", "case", "resultado", "depoimento"]),
        ("objection_handling", ["objecao", "duvida", "risco", "crenca"]),
        ("offer_bridge", ["oferta", "cta", "garantia", "bonus", "preco"]),
        ("base_usage", ["insight_id", "insight-", "evidencia"]),
    ],
    "ads": [
        ("hook_strength", ["hook", "gancho", "primeira linha", "scroll"]),
        ("angle_clarity", ["angulo", "ideia", "hipotese"]),
        ("avatar_fit", ["avatar", "publico", "dor", "desejo"]),
        ("proof_or_plausibility", ["prova", "plausivel", "case", "resultado"]),
        ("testability", ["teste", "hipotese", "variacao"]),
        ("platform_fit", ["facebook", "instagram", "tiktok", "youtube", "meta"]),
        ("creative_direction", ["briefing", "visual", "video", "imagem", "cena"]),
        ("base_usage", ["insight_id", "insight-", "evidencia"]),
    ],
}

RUBRIC_CRITERIA = {
    "vsl": [
        "clarity",
        "curiosity",
        "specificity",
        "mechanism",
        "proof",
        "objection_handling",
        "offer_bridge",
        "base_usage",
    ],
    "ads": [
        "hook_strength",
        "angle_clarity",
        "avatar_fit",
        "proof_or_plausibility",
        "testability",
        "platform_fit",
        "creative_direction",
        "base_usage",
    ],
}

INSIGHT_ID_RE = re.compile(r"[A-Za-z0-9_-]+-(?:tr-insight|v2)-\d+")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def referenced_ids(text: str) -> set[str]:
    ids = set(INSIGHT_ID_RE.findall(text))
    ids.update(re.findall(r"insight_id\s*[:=]\s*([A-Za-z0-9_-]+)", text, flags=re.IGNORECASE))
    return ids


def score_keyword_criterion(text: str, keywords: list[str]) -> tuple[int, int]:
    normalized = normalize_text(text)
    hits = sum(1 for keyword in keywords if normalize_text(keyword) in normalized)
    if hits >= 3:
        return 5, hits
    if hits == 2:
        return 4, hits
    if hits == 1:
        return 3, hits
    return 1, hits


def ids_from_strategy_pack(path: Path | None) -> set[str]:
    if not path or not path.exists():
        return set()
    payload = load_json(path)
    ids: set[str] = set()
    for key in ["usable_insights", "recommended_angles", "frameworks", "warnings", "evidence"]:
        for item in payload.get(key, []):
            if isinstance(item, dict) and item.get("insight_id"):
                ids.add(str(item["insight_id"]))
    return ids


def keyword_presence_check(text: str, artifact_type: str, expected_ids: set[str]) -> dict[str, Any]:
    scores = []
    for name, keywords in KEYWORD_CRITERIA[artifact_type]:
        score, hit_count = score_keyword_criterion(text, keywords)
        scores.append(
            {
                "criterion": name,
                "score": score,
                "keywords": keywords,
                "keyword_hit_count": hit_count,
                "is_proxy": True,
            }
        )

    ids = referenced_ids(text)
    matched = sorted(ids & expected_ids) if expected_ids else sorted(ids)
    missing = sorted(expected_ids - ids) if expected_ids else []
    total = sum(item["score"] for item in scores)
    if not ids:
        decision = "fail"
    elif total >= 32:
        decision = "pass"
    elif total >= 22:
        decision = "needs_revision"
    else:
        decision = "fail"

    return {
        "schema_version": "1.1",
        "check_type": "keyword_presence_check",
        "artifact_type": artifact_type,
        "total_score": total,
        "max_score": len(scores) * 5,
        "decision": decision,
        "referenced_insight_ids": sorted(ids),
        "matched_strategy_pack_ids": matched,
        "unreferenced_strategy_pack_ids": missing,
        "scores": scores,
        "warning": "Proxy secundario: mede vocabulario, nao qualidade final nem fidelidade das citacoes.",
    }


def load_strategy_pack(path: Path | None) -> dict[str, Any]:
    if path and path.exists():
        payload = load_json(path)
        if isinstance(payload, dict):
            return payload
    return {}


def load_insight_index(paths: list[Path], strategy_pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for path in paths:
        if not path.exists():
            continue
        payload = load_json(path)
        for insight in payload.get("insights", []):
            if isinstance(insight, dict) and insight.get("insight_id"):
                index[str(insight["insight_id"])] = {"source": str(path), "insight": insight}

    for key in ["usable_insights", "recommended_angles", "frameworks", "warnings", "evidence"]:
        for item in strategy_pack.get(key, []):
            if not isinstance(item, dict) or not item.get("insight_id"):
                continue
            insight_id = str(item["insight_id"])
            existing = index.setdefault(insight_id, {"source": "strategy_pack", "insight": {}})
            existing.setdefault("strategy_pack_items", []).append(item)
    return index


def evidence_locator(evidence: dict[str, Any]) -> str:
    locator = evidence.get("locator") if isinstance(evidence.get("locator"), dict) else {}
    if locator.get("value"):
        return str(locator["value"])
    if evidence.get("segment_id"):
        return str(evidence["segment_id"])
    start = evidence.get("start_seconds")
    end = evidence.get("end_seconds")
    if start is not None or end is not None:
        return f"{start}-{end}"
    return ""


def text_for_insight(insight: dict[str, Any]) -> str:
    parts = [
        insight.get("specific_takeaway"),
        insight.get("insight_ptbr"),
        insight.get("summary_ptbr"),
        insight.get("use_case"),
        insight.get("when_to_use"),
    ]
    return " ".join(str(part) for part in parts if part)


def output_lines_for_id(text: str, insight_id: str) -> list[dict[str, Any]]:
    lines = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if insight_id in line:
            lines.append({"line": line_number, "text": line.strip()})
    return lines


def cited_insight_context(text: str, ids: set[str], index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    contexts: list[dict[str, Any]] = []
    for insight_id in sorted(ids):
        entry = index.get(insight_id)
        if not entry:
            contexts.append(
                {
                    "insight_id": insight_id,
                    "found": False,
                    "source": None,
                    "title": None,
                    "takeaway": None,
                    "evidence": [],
                    "output_mentions": output_lines_for_id(text, insight_id),
                }
            )
            continue
        insight = entry.get("insight") or {}
        evidence_items = []
        raw_evidence = as_list(insight.get("evidence"))
        if not raw_evidence and entry.get("strategy_pack_items"):
            raw_evidence = entry["strategy_pack_items"]
        for evidence in raw_evidence[:3]:
            if not isinstance(evidence, dict):
                continue
            evidence_items.append(
                {
                    "quote_original": evidence.get("quote_original") or evidence.get("evidence_quote"),
                    "locator": evidence_locator(evidence),
                    "episode_video_id": evidence.get("episode_video_id") or insight.get("episode_video_id"),
                    "evidence_strength": evidence.get("evidence_strength"),
                }
            )
        contexts.append(
            {
                "insight_id": insight_id,
                "found": True,
                "source": entry.get("source"),
                "title": insight.get("canonical_title") or insight.get("title"),
                "takeaway": text_for_insight(insight),
                "claim_risk": insight.get("claim_risk"),
                "confidence_score": insight.get("confidence_score"),
                "evidence": evidence_items,
                "output_mentions": output_lines_for_id(text, insight_id),
            }
        )
    return contexts


def load_briefing(args: argparse.Namespace, strategy_pack: dict[str, Any]) -> dict[str, Any]:
    if args.briefing_json:
        payload = load_json(args.briefing_json)
        if not isinstance(payload, dict):
            raise SystemExit(f"Briefing JSON must be an object: {args.briefing_json}")
        return payload
    if args.briefing_text:
        return {"text": args.briefing_text}
    briefing = strategy_pack.get("briefing")
    return briefing if isinstance(briefing, dict) else {}


def validate_criteria(artifact_type: str, criteria_scores: list[dict[str, Any]]) -> None:
    expected = RUBRIC_CRITERIA[artifact_type]
    found = [str(item.get("criterion")) for item in criteria_scores]
    if found != expected:
        raise SystemExit(f"Criterion order mismatch for {artifact_type}: expected {expected}, found {found}")
    for item in criteria_scores:
        score = item.get("score")
        if not isinstance(score, int) or score < 0 or score > 5:
            raise SystemExit(f"Invalid score for {item.get('criterion')}: {score!r}")
        if not item.get("justification"):
            raise SystemExit(f"Missing justification for {item.get('criterion')}")


def has_accented_letters(text: str) -> bool:
    return any(ord(char) > 127 and char.isalpha() for char in text)


def language_encoding_check(text: str) -> dict[str, Any]:
    broken_patterns = broken_accent_deletion_matches(text)
    has_accents = has_accented_letters(text)
    if broken_patterns:
        status = "fail"
        notes = "Known accent-deletion artifacts detected in final output text."
    elif not has_accents:
        status = "needs_revision"
        notes = "Final pt-BR output has no accented letters; verify full Portuguese accentuation before approval."
    else:
        status = "pass"
        notes = "Final output preserves pt-BR accented text and has no known accent-deletion artifacts."
    return {
        "status": status,
        "has_accented_letters": has_accents,
        "broken_accent_patterns": broken_patterns,
        "notes": notes,
    }


def decision_from_score(total: int, has_ids: bool, citation_fidelity: dict[str, Any], language_check: dict[str, Any]) -> str:
    unsupported = citation_fidelity.get("unsupported_or_overextended_claims") or []
    status = normalize_text(citation_fidelity.get("status"))
    language_status = normalize_text(language_check.get("status"))
    if not has_ids or status == "fail" or unsupported or language_status == "fail":
        return "fail"
    if language_status == "needs_revision":
        return "needs_revision"
    if total >= 32:
        return "pass"
    if total >= 22:
        return "needs_revision"
    return "fail"


def build_honest_report(args: argparse.Namespace, text: str, keyword_check: dict[str, Any]) -> dict[str, Any]:
    if not args.judgment_json:
        return {
            "schema_version": "1.1",
            "generated_at": utc_now(),
            "evaluation_route": "keyword_presence_check_only",
            "artifact_type": args.artifact_type,
            "artifact_path": str(args.output),
            "keyword_presence_check": keyword_check,
            "language_encoding_check": language_encoding_check(text),
            "warning": "MSF-R09 final score was not produced because --judgment-json was not provided.",
        }

    judgment = load_json(args.judgment_json)
    strategy_pack = load_strategy_pack(args.strategy_pack)
    insight_paths = args.insight_master or [
        data_path("exports", "insights_master.json"),
        data_path("exports", "insights_v2_master.json"),
    ]
    index = load_insight_index(insight_paths, strategy_pack)
    ids = referenced_ids(text)
    criteria_scores = judgment.get("criteria_scores")
    if not isinstance(criteria_scores, list):
        raise SystemExit(f"Missing criteria_scores array in {args.judgment_json}")
    validate_criteria(args.artifact_type, criteria_scores)
    citation_fidelity = judgment.get("citation_fidelity")
    if not isinstance(citation_fidelity, dict):
        raise SystemExit(f"Missing citation_fidelity object in {args.judgment_json}")
    total_score = sum(int(item["score"]) for item in criteria_scores)
    language_check = language_encoding_check(text)
    decision = decision_from_score(total_score, bool(ids), citation_fidelity, language_check)

    legacy_score = args.legacy_score
    if legacy_score is None:
        legacy_score = keyword_check.get("total_score")
    legacy_decision = args.legacy_decision or keyword_check.get("decision")

    return {
        "schema_version": "2.0",
        "generated_at": utc_now(),
        "evaluation_route": "codex_manual_no_api",
        "judge": judgment.get("judge", "Codex"),
        "artifact_type": args.artifact_type,
        "artifact_path": str(args.output),
        "briefing": load_briefing(args, strategy_pack),
        "rubric_path": str(args.rubric),
        "strategy_pack_path": str(args.strategy_pack) if args.strategy_pack else None,
        "keyword_presence_check": keyword_check,
        "referenced_insight_ids": sorted(ids),
        "cited_insights": cited_insight_context(text, ids, index),
        "citation_fidelity": citation_fidelity,
        "language_encoding_check": language_check,
        "criteria_scores": criteria_scores,
        "total_score": total_score,
        "max_score": len(criteria_scores) * 5,
        "decision": decision,
        "comparison_to_legacy_keyword_score": {
            "legacy_score": legacy_score,
            "legacy_max_score": keyword_check.get("max_score"),
            "legacy_decision": legacy_decision,
            "honest_score": total_score,
            "honest_decision": decision,
            "delta": total_score - int(legacy_score) if isinstance(legacy_score, int) else None,
            "interpretation": judgment.get("legacy_comparison_note", ""),
        },
        "overall_notes": judgment.get("overall_notes", ""),
    }


def validate_report(report: dict[str, Any], schema_path: Path) -> None:
    if report.get("schema_version") != "2.0":
        return
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(report), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        path = ".".join(str(part) for part in first.path) or "<root>"
        raise SystemExit(f"Output evaluation schema validation failed at {path}: {first.message}")


def render_markdown(report: dict[str, Any]) -> str:
    if report.get("schema_version") != "2.0":
        check = report["keyword_presence_check"]
        lines = [
            "# Keyword Presence Check",
            "",
            "- This is a proxy only, not the MSF-R09 final score.",
            f"- Artifact type: {check['artifact_type']}",
            f"- Proxy score: {check['total_score']} / {check['max_score']}",
            f"- Proxy decision: {check['decision']}",
            f"- Referenced insight ids: {len(check['referenced_insight_ids'])}",
            f"- Language encoding: {report['language_encoding_check']['status']}",
            "",
            "## Proxy Scores",
            "",
        ]
        for item in check["scores"]:
            lines.append(f"- {item['criterion']}: {item['score']}/5 ({item['keyword_hit_count']} keyword hits)")
        lines.append("")
        return "\n".join(lines)

    comparison = report["comparison_to_legacy_keyword_score"]
    lines = [
        "# Honest Output Evaluation",
        "",
        f"- Artifact type: {report['artifact_type']}",
        f"- Route: {report['evaluation_route']}",
        f"- Score: {report['total_score']} / {report['max_score']}",
        f"- Decision: {report['decision']}",
        f"- Referenced insight ids: {len(report['referenced_insight_ids'])}",
        f"- Legacy keyword score: {comparison['legacy_score']} / {comparison['legacy_max_score']} ({comparison['legacy_decision']})",
        f"- Delta vs legacy keyword score: {comparison['delta']}",
        "",
        "## Criteria Scores",
        "",
    ]
    for item in report["criteria_scores"]:
        lines.append(f"- {item['criterion']}: {item['score']}/5 - {item['justification']}")
    lines.extend(["", "## Citation Fidelity", ""])
    fidelity = report["citation_fidelity"]
    lines.append(f"- Status: {fidelity.get('status')}")
    lines.append(f"- Checked insight ids: {len(fidelity.get('checked_insight_ids') or [])}")
    if fidelity.get("unsupported_or_overextended_claims"):
        lines.append("- Unsupported or overextended claims:")
        for claim in fidelity["unsupported_or_overextended_claims"]:
            lines.append(f"  - {claim}")
    else:
        lines.append("- Unsupported or overextended claims: none.")
    if fidelity.get("notes"):
        lines.append(f"- Notes: {fidelity['notes']}")
    lines.extend(["", "## Language Encoding", ""])
    language = report["language_encoding_check"]
    lines.append(f"- Status: {language.get('status')}")
    lines.append(f"- Has accented letters: {language.get('has_accented_letters')}")
    patterns = language.get("broken_accent_patterns") or []
    lines.append(f"- Broken accent patterns: {', '.join(patterns) if patterns else 'none'}")
    if language.get("notes"):
        lines.append(f"- Notes: {language['notes']}")
    lines.extend(["", "## Keyword Presence Check", ""])
    check = report["keyword_presence_check"]
    lines.append(f"- Proxy score: {check['total_score']} / {check['max_score']} ({check['decision']})")
    lines.append("- Use only as cheap secondary signal.")
    if report.get("overall_notes"):
        lines.extend(["", "## Overall Notes", "", str(report["overall_notes"])])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="Markdown/text output to evaluate")
    parser.add_argument("--artifact-type", required=True, choices=sorted(KEYWORD_CRITERIA), help="vsl or ads")
    parser.add_argument("--strategy-pack", type=Path, help="Optional strategy pack JSON")
    parser.add_argument("--briefing-json", type=Path, help="Optional briefing JSON object")
    parser.add_argument("--briefing-text", help="Optional briefing text")
    parser.add_argument("--insight-master", action="append", type=Path, help="Insight master JSON to use for citation context")
    parser.add_argument("--judgment-json", type=Path, help="Codex-authored rubric judgment JSON")
    parser.add_argument("--schema", default=Path("schemas/output_evaluation.schema.json"), type=Path)
    parser.add_argument("--rubric", default=Path("docs/output-evaluation-rubric.md"), type=Path)
    parser.add_argument("--legacy-score", type=int, help="Previously reported keyword score for comparison")
    parser.add_argument("--legacy-decision", help="Previously reported keyword decision for comparison")
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--report-md", type=Path)
    args = parser.parse_args()

    text = args.output.read_text(encoding="utf-8")
    expected_ids = ids_from_strategy_pack(args.strategy_pack)
    keyword_check = keyword_presence_check(text, args.artifact_type, expected_ids)
    report = build_honest_report(args, text, keyword_check)
    validate_report(report, args.schema)
    markdown = render_markdown(report)
    if args.report_json:
        write_json(args.report_json, report)
    if args.report_md:
        write_text(args.report_md, markdown)
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
