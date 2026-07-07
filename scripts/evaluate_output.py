#!/usr/bin/env python
"""Evaluate whether a generated output uses Marketing Swipe File evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from msf_common import load_json, normalize_text, write_json, write_text


CRITERIA = {
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


def insight_ids_from_pack(path: Path | None) -> set[str]:
    if not path or not path.exists():
        return set()
    payload = load_json(path)
    ids: set[str] = set()
    for key in ["usable_insights", "recommended_angles", "frameworks", "warnings"]:
        for item in payload.get(key, []):
            if isinstance(item, dict) and item.get("insight_id"):
                ids.add(str(item["insight_id"]))
    return ids


def referenced_ids(text: str) -> set[str]:
    ids = set(re.findall(r"[A-Za-z0-9_-]+-insight-[A-Za-z0-9_-]+", text))
    ids.update(re.findall(r"insight_id\s*[:=]\s*([A-Za-z0-9_-]+)", text, flags=re.IGNORECASE))
    return ids


def score_criterion(text: str, keywords: list[str]) -> int:
    normalized = normalize_text(text)
    hits = sum(1 for keyword in keywords if normalize_text(keyword) in normalized)
    if hits >= 3:
        return 5
    if hits == 2:
        return 4
    if hits == 1:
        return 3
    return 1


def evaluate(text: str, artifact_type: str, expected_ids: set[str]) -> dict[str, Any]:
    criteria = CRITERIA[artifact_type]
    scores = []
    for name, keywords in criteria:
        scores.append({"criterion": name, "score": score_criterion(text, keywords), "keywords": keywords})

    ids = referenced_ids(text)
    if expected_ids:
        matched = sorted(ids & expected_ids)
        missing = sorted(expected_ids - ids)
    else:
        matched = sorted(ids)
        missing = []

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
        "schema_version": "1.0",
        "artifact_type": artifact_type,
        "total_score": total,
        "max_score": len(criteria) * 5,
        "decision": decision,
        "referenced_insight_ids": sorted(ids),
        "matched_strategy_pack_ids": matched,
        "missing_strategy_pack_ids": missing,
        "scores": scores,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Output Evaluation",
        "",
        f"- Artifact type: {report['artifact_type']}",
        f"- Score: {report['total_score']} / {report['max_score']}",
        f"- Decision: {report['decision']}",
        f"- Referenced insight ids: {len(report['referenced_insight_ids'])}",
        f"- Matched strategy pack ids: {len(report['matched_strategy_pack_ids'])}",
        "",
        "## Scores",
        "",
    ]
    for item in report["scores"]:
        lines.append(f"- {item['criterion']}: {item['score']}/5")
    if report["missing_strategy_pack_ids"]:
        lines.extend(["", "## Missing Strategy Pack IDs", ""])
        lines.extend(f"- {insight_id}" for insight_id in report["missing_strategy_pack_ids"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="Markdown/text output to evaluate")
    parser.add_argument("--artifact-type", required=True, choices=sorted(CRITERIA), help="vsl or ads")
    parser.add_argument("--strategy-pack", type=Path, help="Optional strategy pack JSON")
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--report-md", type=Path)
    args = parser.parse_args()

    text = args.output.read_text(encoding="utf-8")
    report = evaluate(text, args.artifact_type, insight_ids_from_pack(args.strategy_pack))
    markdown = render_markdown(report)
    if args.report_json:
        write_json(args.report_json, report)
    if args.report_md:
        write_text(args.report_md, markdown)
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

