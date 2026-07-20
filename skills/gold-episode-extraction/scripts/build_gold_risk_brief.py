#!/usr/bin/env python3
"""Build a compact, deterministic navigation brief from gold review artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "1.0.0"
CAPTURED_DISPOSITIONS = {"captured", "merged"}
NUMBER_RE = re.compile(
    r"(?<!\w)(?:R\$|US\$|\$)?\s*\d+(?:[.,]\d+)?(?:\s*(?:%|x|mil|milhao|milhoes|dolar|dolares|reais))?",
    re.IGNORECASE,
)
NUMBER_WORD_UNIT_RE = re.compile(
    r"\b(?:um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito|nove|dez|quinze|vinte|trinta|quarenta|cinquenta|cem)\s+"
    r"(?:segundo|segundos|minuto|minutos|hora|horas|dia|dias|semana|semanas|mes|meses|ano|anos|porcento|por cento)\b",
    re.IGNORECASE,
)

CUE_TERMS = {
    "outcome": (
        "aument*", "reduz*", "dimin*", "caiu", "subiu", "cresceu", "melhorou", "piorou",
        "vendeu", "vendas", "conversao", "resultado", "performance", "retorno", "lucro",
        "roas", "roi", "cpa", "escalou", "escalar", "funcionou", "falhou",
    ),
    "mechanism": (
        "mecanismo", "som", "barulho", "efeito", "abertura", "hook", "vsl", "video",
        "anuncio", "criativo", "edicao", "visual", "algoritmo", "headline", "script",
    ),
    "sequence": (
        "depois", "antes", "primeiro", "segunda", "segundo", "seguida", "passo", "etapa",
        "semana", "semanas", "dia", "dias", "mes", "meses", "minuto", "minutos", "durante",
    ),
    "attribution": (
        "acho", "talvez", "exemplo", "cliente", "relat", "entrevist", "segundo", "afirma",
    ),
}

WARNING_SCORES = {
    "numeric_support_ambiguity": 120,
    "numeric_completeness": 120,
    "numeric_recall": 115,
    "risk_recall_unreviewed": 110,
    "fixed_point_risk_review_required": 105,
    "compiler_issue": 100,
    "hard_blocker": 100,
    "claim_evidence_alignment": 80,
    "semantic_workbench": 85,
    "semantic_closure": 55,
    "promo_or_interviewer": 25,
}


def _canonical_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char)).lower()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _semantic_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _trim(value: Any, limit: int = 240) -> Any:
    if isinstance(value, str) and len(value) > limit:
        return value[: limit - 1].rstrip() + "..."
    return value


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _dict_items(value: Any) -> Iterable[dict[str, Any]]:
    for item in _as_list(value):
        if isinstance(item, dict):
            yield item


def _segment_ids(item: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("segment_ids", "source_segment_ids", "residual_segment_ids"):
        for value in _as_list(item.get(key)):
            if value and str(value) not in values:
                values.append(str(value))
    mention = item.get("numeric_mention")
    if isinstance(mention, dict) and mention.get("segment_id"):
        value = str(mention["segment_id"])
        if value not in values:
            values.append(value)
    return values


def _candidate_ids(item: dict[str, Any]) -> list[str]:
    values = [str(value) for value in _as_list(item.get("candidate_ids")) if value]
    if item.get("candidate_id"):
        values.append(str(item["candidate_id"]))
    return sorted(set(values))


def _range_from_item(item: dict[str, Any]) -> list[int] | None:
    clean_range = item.get("clean_index_range") or item.get("segment_range")
    if isinstance(clean_range, list) and len(clean_range) == 2:
        try:
            return [int(clean_range[0]), int(clean_range[1])]
        except (TypeError, ValueError):
            pass
    indexes = [value for value in _as_list(item.get("clean_indexes")) if isinstance(value, int)]
    if indexes:
        return [min(indexes), max(indexes)]
    parsed = []
    for segment_id in _segment_ids(item):
        match = re.search(r"-(\d+)$", segment_id)
        if match:
            parsed.append(max(0, int(match.group(1)) - 1))
    return [min(parsed), max(parsed)] if parsed else None


def _cue_flags(text: str) -> dict[str, bool]:
    canonical = _canonical_text(text)
    numeric = bool(NUMBER_RE.search(text) or NUMBER_WORD_UNIT_RE.search(canonical))
    def contains(term: str) -> bool:
        if term.endswith("*"):
            return bool(re.search(rf"\b{re.escape(term[:-1])}\w*", canonical))
        return bool(re.search(rf"\b{re.escape(term)}\b", canonical))

    flags = {name: any(contains(term) for term in terms) for name, terms in CUE_TERMS.items()}
    flags["numeric"] = numeric
    flags["before_after"] = (
        ("antes" in canonical and "depois" in canonical)
        or bool(re.search(r"\bde\s+\d[^.]{0,80}\bpara\s+\d", canonical))
        or any(contains(term) for term in ("caiu", "subiu", "aumentou", "reduziu", "diminuiu"))
    )
    return flags


def _surface_category(flags: dict[str, bool]) -> tuple[str, int]:
    if flags["numeric"] and flags["outcome"] and flags["sequence"]:
        return "numeric_trajectory", 100
    if flags["numeric"] and flags["outcome"]:
        return "numeric_result", 95
    if flags["mechanism"] and flags["sequence"]:
        return "mechanism_sequence", 90
    if flags["before_after"]:
        return "before_after", 85
    if flags["outcome"] and flags["mechanism"]:
        return "reported_outcome", 80
    if flags["numeric"] and flags["sequence"]:
        return "numeric_sequence", 75
    if flags["numeric"]:
        return "numeric_claim", 65
    if flags["outcome"]:
        return "reported_outcome", 60
    return "generic_tail", 20


def _priority_label(score: int) -> str:
    if score >= 90:
        return "P0"
    if score >= 70:
        return "P1"
    if score >= 50:
        return "P2"
    return "P3"


def _warning_surface(category: str, item: dict[str, Any]) -> dict[str, Any]:
    text = str(item.get("text") or item.get("evidence") or item.get("issue") or item.get("summary") or "")
    cue_category, cue_score = _surface_category(_cue_flags(text))
    score = max(WARNING_SCORES.get(category, 50), cue_score)
    return {
        "priority": _priority_label(score),
        "score": score,
        "category": category if category != "semantic_closure" else cue_category,
        "source_category": category,
        "item_id": item.get("warning_id") or item.get("closure_id") or item.get("cluster_id") or item.get("issue_id"),
        "lineage_id": item.get("lineage_id") or item.get("source_cluster_id"),
        "review_requirement": item.get("review_requirement"),
        "candidate_ids": _candidate_ids(item),
        "segment_ids": _segment_ids(item),
        "clean_index_range": _range_from_item(item),
        "cues": [name for name, enabled in _cue_flags(text).items() if enabled],
        "evidence": _trim(text),
        "expected_action": _trim(item.get("expected") or item.get("required_action") or item.get("issue")),
    }


def _is_reviewed_incidental(item: dict[str, Any]) -> bool:
    review = item.get("review")
    return isinstance(review, dict) and review.get("disposition") in {"incidental", "relation_not_useful"}


def _dedupe_surfaces(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(
        items,
        key=lambda item: (
            item.get("source_category") == "transcript_risk_scan",
            -int(item.get("score", 0)),
            item.get("clean_index_range") or [10**12, 10**12],
            str(item.get("item_id") or ""),
        ),
    )
    kept: list[dict[str, Any]] = []
    for item in ordered:
        lineage_id = item.get("lineage_id")
        if lineage_id and any(prior.get("lineage_id") == lineage_id for prior in kept):
            continue
        current_range = item.get("clean_index_range")
        duplicate = False
        if current_range:
            current = set(range(current_range[0], current_range[1] + 1))
            for prior in kept:
                prior_range = prior.get("clean_index_range")
                if not prior_range or prior.get("category") != item.get("category"):
                    continue
                previous = set(range(prior_range[0], prior_range[1] + 1))
                overlap = len(current & previous) / max(1, min(len(current), len(previous)))
                if overlap >= 0.3:
                    duplicate = True
                    break
        if not duplicate:
            kept.append(item)
    return kept


def _scan_transcript(rows: list[list[Any]]) -> list[dict[str, Any]]:
    surfaces: list[dict[str, Any]] = []
    window_size = 12
    stride = 8
    captured_indexes = [
        int(row[0]) for row in rows
        if len(row) > 4 and str(row[4]) in CAPTURED_DISPOSITIONS
    ]
    for start in range(0, len(rows), stride):
        window = rows[start : start + window_size]
        if not window:
            continue
        dispositions = {str(row[4]) for row in window if len(row) > 4 and row[4] is not None}
        if dispositions and dispositions <= CAPTURED_DISPOSITIONS:
            continue
        text = " ".join(str(row[3]) for row in window if len(row) > 3)
        flags = _cue_flags(text)
        category, score = _surface_category(flags)
        if score < 60:
            continue
        indexes = [int(row[0]) for row in window]
        if "excluded" in dispositions:
            score += 5
        if captured_indexes:
            distance = min(abs(index - captured) for index in (indexes[0], indexes[-1]) for captured in captured_indexes)
            if distance <= 20:
                score += 10
            elif distance > 50:
                score -= 15
        surfaces.append({
            "priority": _priority_label(score),
            "score": score,
            "category": category,
            "source_category": "transcript_risk_scan",
            "item_id": f"transcript-{indexes[0]:04d}-{indexes[-1]:04d}",
            "candidate_ids": sorted({str(value) for row in window if len(row) > 5 for value in _as_list(row[5])}),
            "segment_ids": [],
            "clean_index_range": [indexes[0], indexes[-1]],
            "cues": [name for name, enabled in flags.items() if enabled],
            "evidence": _trim(text),
            "expected_action": "verify atomic recall, numeric multiplicity, attribution, caveats, and candidate coverage",
        })
    return _dedupe_surfaces(surfaces)


def _candidate_dict(row: list[Any], columns: list[str]) -> dict[str, Any]:
    return {column: row[index] if index < len(row) else None for index, column in enumerate(columns)}


def _numeric_matrix(
    candidates: list[dict[str, Any]],
    coverage: dict[str, dict[str, Any]],
    transcript_by_index: dict[int, list[Any]],
) -> list[dict[str, Any]]:
    matrix = []
    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id") or "")
        report = coverage.get(candidate_id, {})
        numbers = _as_list(candidate.get("numbers"))
        mentions = [item for item in _dict_items(report.get("mentions"))]
        if not numbers and not mentions and not report.get("missing_material"):
            continue
        evidence_indexes = sorted({
            int(value)
            for key in ("minimal_clean_indexes", "support_clean_indexes")
            for value in _as_list(candidate.get(key))
            if isinstance(value, int)
        })
        if not mentions:
            for clean_index in evidence_indexes:
                row = transcript_by_index.get(clean_index)
                if not row:
                    continue
                text = str(row[3])
                for match in NUMBER_RE.finditer(text):
                    mentions.append({
                        "clean_index": clean_index,
                        "raw": match.group(0).strip(),
                        "canonical": _canonical_text(match.group(0).strip()),
                        "kind": "literal_scan",
                        "layer": "candidate_evidence",
                        "disposition": "requires_semantic_confirmation",
                        "record_index": None,
                    })
        occurrence_keys = [
            (item.get("segment_id"), item.get("clean_index"), item.get("raw"), item.get("layer"))
            for item in mentions
        ]
        occurrence_count = len(set(occurrence_keys))
        record_count = int(report.get("record_count") or len(numbers))
        matrix.append({
            "candidate_id": candidate_id,
            "status": report.get("status") or "not_evaluated",
            "record_count": record_count,
            "occurrence_count": occurrence_count,
            "potential_multiplicity_gap": max(0, occurrence_count - record_count),
            "records": [
                {key: number.get(key) for key in ("raw", "value", "min_value", "max_value", "unit_kind", "unit", "period", "role", "value_status") if key in number}
                for number in numbers if isinstance(number, dict)
            ],
            "occurrences": [
                {key: item.get(key) for key in ("segment_id", "clean_index", "layer", "raw", "canonical", "kind", "disposition", "record_index") if item.get(key) is not None}
                for item in mentions
            ],
            "missing_material": report.get("missing_material", []),
            "audit_warnings": report.get("audit_warnings", []),
        })
    return sorted(matrix, key=lambda item: (-item["potential_multiplicity_gap"], item["status"] == "pass", item["candidate_id"]))


def _read_dossier(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at line {line_number}: {exc}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"dossier line {line_number} is not an object")
            rows.append(item)
    header = next((item for item in rows if item.get("record_type") == "header"), None)
    footer = next((item for item in rows if item.get("record_type") == "footer"), None)
    if not header or not footer:
        raise ValueError("dossier header or footer is missing")
    return header, rows


def build_dossier_brief(path: Path, *, max_surfaces: int = 32) -> dict[str, Any]:
    header, records = _read_dossier(path)
    candidate_columns = _as_list(header.get("candidate_columns"))
    candidates = [
        _candidate_dict(_as_list(item.get("value")), candidate_columns)
        for item in records if item.get("record_type") == "candidate"
    ]
    coverage = {
        str(item["value"].get("candidate_id")): item["value"]
        for item in records
        if item.get("record_type") == "numeric_coverage" and isinstance(item.get("value"), dict)
    }
    transcript_rows = [
        row
        for item in records if item.get("record_type") == "transcript_block"
        for row in _as_list(item.get("value")) if isinstance(row, list) and len(row) >= 4
    ]
    transcript_rows.sort(key=lambda row: int(row[0]))
    transcript_by_index = {int(row[0]): row for row in transcript_rows}
    workbench = next((
        item.get("value") for item in records
        if item.get("record_type") == "semantic_workbench" and isinstance(item.get("value"), dict)
    ), None)
    collapsed = Counter()
    warning_surfaces = []
    for group in _dict_items(header.get("audit_warnings")):
        category = str(group.get("category") or "audit_warning")
        for item in _dict_items(group.get("items")):
            if item.get("review_requirement") == "audit_only":
                collapsed[f"audit_only_{category}"] += 1
                continue
            if _is_reviewed_incidental(item) and category == "semantic_closure":
                collapsed["reviewed_incidental_semantic_closure"] += 1
                continue
            warning_surfaces.append(_warning_surface(category, item))
    if workbench:
        workbench_surfaces = [
            _warning_surface("semantic_workbench", item)
            for item in _dict_items(workbench.get("review_order"))
        ]
        surfaces = _dedupe_surfaces([*workbench_surfaces, *warning_surfaces])
        navigation_source = "semantic_workbench"
    else:
        surfaces = _dedupe_surfaces([*warning_surfaces, *_scan_transcript(transcript_rows)])
        navigation_source = "legacy_transcript_scan"
    shown = surfaces[:max_surfaces]
    full_numeric_matrix = _numeric_matrix(candidates, coverage, transcript_by_index)
    numeric_matrix = [
        item for item in full_numeric_matrix
        if item.get("potential_multiplicity_gap", 0) > 0
        or item.get("status") not in {"pass", "covered"}
        or item.get("missing_material")
        or item.get("audit_warnings")
    ][:16]
    numeric_candidate_index = [
        {
            "candidate_id": item["candidate_id"],
            "status": item.get("status"),
            "record_count": item.get("record_count", 0),
            "occurrence_count": item.get("occurrence_count", 0),
            "potential_multiplicity_gap": item.get("potential_multiplicity_gap", 0),
        }
        for item in full_numeric_matrix
    ]
    result = {
        "schema_version": SCHEMA_VERSION,
        "source_kind": "audit_dossier",
        "episode_video_id": header.get("episode_video_id"),
        "source": {"path": str(path), "physical_sha256": _sha256(path), "bytes": path.stat().st_size},
        "summary": {
            "segment_count": header.get("segment_count"),
            "candidate_count": header.get("candidate_count"),
            "risk_surface_count": len(surfaces),
            "shown_risk_surfaces": len(shown),
            "p0_total_count": sum(item["priority"] == "P0" for item in surfaces),
            "shown_p0_count": sum(item["priority"] == "P0" for item in shown),
            "numeric_candidate_count": len(full_numeric_matrix),
            "numeric_review_count": len(numeric_matrix),
            "navigation_source": navigation_source,
        },
        "review_order": shown,
        "coverage_workbench": {
            "semantic_sha256": workbench.get("semantic_sha256"),
            "summary": workbench.get("summary", {}),
            "coverage_blocks": workbench.get("coverage_blocks", []),
        } if workbench else None,
        "candidate_bindings": [
            item for item in _dict_items(workbench.get("candidate_bindings") if workbench else [])
            if item.get("requires_review")
        ],
        "calibration_bindings": [
            item for item in _dict_items(workbench.get("calibration_bindings") if workbench else [])
            if item.get("requires_review")
        ],
        "numeric_occurrence_matrix": numeric_matrix,
        "numeric_candidate_index": numeric_candidate_index,
        "numeric_matrix_semantic_sha256": _semantic_hash(full_numeric_matrix),
        "collapsed_low_risk": dict(sorted(collapsed.items())),
        "guardrails": [
            "brief is navigation only; final Sol audit still reads the source-complete dossier once",
            "potential_multiplicity_gap requires semantic confirmation and is not an automatic blocker",
            "quotes and transcript text remain verbatim",
            "semantic workbench is preferred over a second broad transcript scan when present",
        ],
    }
    result["semantic_sha256"] = _semantic_hash(result)
    return result


def _prelint_groups(document: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any]]]:
    inventory = document.get("prelint_inventory") if isinstance(document.get("prelint_inventory"), dict) else {}
    for key in ("compiler_issues", "hard_blockers", "evidence_scope_warnings", "fixed_point_risk_clusters", "review_gate", "semantic_closure_index"):
        for group in _dict_items(inventory.get(key)):
            if isinstance(group.get("items"), list):
                category = str(group.get("category") or key)
                for item in _dict_items(group.get("items")):
                    yield category, {**item, "expected": group.get("expected") or item.get("expected")}
            else:
                yield str(group.get("category") or key), group
    workbench = inventory.get("semantic_workbench")
    if isinstance(workbench, dict):
        for item in _dict_items(workbench.get("review_order")):
            yield "semantic_workbench", item
    for group in _dict_items(document.get("audit_warnings")):
        category = str(group.get("category") or "audit_warning")
        for item in _dict_items(group.get("items")):
            yield category, item


def _collect_numeric_mentions(value: Any, found: list[dict[str, Any]]) -> None:
    if isinstance(value, dict):
        mention = value.get("numeric_mention")
        if isinstance(mention, dict):
            found.append(mention)
        if value.get("raw") is not None and value.get("canonical") is not None and (value.get("segment_id") or value.get("clean_index") is not None):
            found.append(value)
        for child in value.values():
            _collect_numeric_mentions(child, found)
    elif isinstance(value, list):
        for child in value:
            _collect_numeric_mentions(child, found)


def build_prelint_brief(path: Path, document: dict[str, Any], *, max_surfaces: int = 32) -> dict[str, Any]:
    collapsed = Counter()
    surfaces = []
    for category, item in _prelint_groups(document):
        if _is_reviewed_incidental(item) and category == "semantic_closure":
            collapsed["reviewed_incidental_semantic_closure"] += 1
            continue
        surfaces.append(_warning_surface(category, item))
    surfaces = _dedupe_surfaces(surfaces)
    mentions: list[dict[str, Any]] = []
    _collect_numeric_mentions(document.get("prelint_inventory", {}), mentions)
    grouped_mentions: dict[str, list[dict[str, Any]]] = {}
    for mention in mentions:
        candidate_id = str(mention.get("candidate_id") or "unassigned")
        grouped_mentions.setdefault(candidate_id, []).append(mention)
    matrix = []
    for candidate_id, items in sorted(grouped_mentions.items()):
        unique = {
            (item.get("segment_id"), item.get("clean_index"), item.get("raw"), item.get("layer"))
            for item in items
        }
        covered_records = {item.get("record_index") for item in items if item.get("record_index") is not None}
        matrix.append({
            "candidate_id": candidate_id,
            "occurrence_count": len(unique),
            "covered_record_count": len(covered_records),
            "potential_multiplicity_gap": max(0, len(unique) - len(covered_records)),
            "occurrences": [
                {key: item.get(key) for key in ("segment_id", "clean_index", "layer", "raw", "canonical", "kind", "disposition", "record_index") if item.get(key) is not None}
                for item in items
            ],
        })
    result = {
        "schema_version": SCHEMA_VERSION,
        "source_kind": "prelint",
        "episode_video_id": document.get("episode_video_id"),
        "source": {"path": str(path), "physical_sha256": _sha256(path), "bytes": path.stat().st_size},
        "summary": {
            "status": document.get("status"),
            "risk_surface_count": len(surfaces),
            "shown_risk_surfaces": min(len(surfaces), max_surfaces),
            "p0_total_count": sum(item["priority"] == "P0" for item in surfaces),
            "shown_p0_count": sum(item["priority"] == "P0" for item in surfaces[:max_surfaces]),
            "numeric_candidate_count": len(matrix),
        },
        "review_order": surfaces[:max_surfaces],
        "numeric_occurrence_matrix": matrix,
        "collapsed_low_risk": dict(sorted(collapsed.items())),
        "guardrails": [
            "resolve source-backed issues before apply",
            "brief does not replace the full prelint report",
            "potential_multiplicity_gap requires semantic confirmation",
        ],
    }
    result["semantic_sha256"] = _semantic_hash(result)
    return result


def build_brief(path: Path, *, max_surfaces: int = 32) -> dict[str, Any]:
    if path.suffix.lower() == ".jsonl":
        return build_dossier_brief(path, max_surfaces=max_surfaces)
    with path.open("r", encoding="utf-8") as handle:
        document = json.load(handle)
    if not isinstance(document, dict):
        raise ValueError("input JSON must be an object")
    return build_prelint_brief(path, document, max_surfaces=max_surfaces)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-surfaces", type=int, default=32)
    args = parser.parse_args()
    if args.max_surfaces < 1:
        parser.error("--max-surfaces must be positive")
    try:
        result = build_brief(args.input, max_surfaces=args.max_surfaces)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False))
        return 1
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ok",
        "source_kind": result["source_kind"],
        "episode_video_id": result.get("episode_video_id"),
        "risk_surface_count": result["summary"]["risk_surface_count"],
        "shown_risk_surfaces": result["summary"]["shown_risk_surfaces"],
        "numeric_candidate_count": result["summary"]["numeric_candidate_count"],
        "output": str(args.output) if args.output else None,
        "semantic_sha256": result["semantic_sha256"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
