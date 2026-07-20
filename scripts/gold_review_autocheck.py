#!/usr/bin/env python
"""Read-only directed-recall inventory for a prepared gold episode."""

from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any

from scripts.gold_extraction_common import (
    EXCLUSION_REASON_CODES,
    calibration_coverage,
    calibration_target_errors,
    candidate_numeric_coverage,
    editorial_ascii_errors,
    evidence_quotes,
    ledger_for_signals,
    load_json,
    normalize_ascii,
    normalize_relations,
    numeric_mentions,
    validate_numbers,
    sha256_semantic_json,
)


WORD_NUMBER_MATERIAL_RE = re.compile(
    r"\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|dois|duas|tres|quatro|cinco|seis|sete|oito|nove|dez)\b"
    r"(?:\s+(?:to|a|ate)\s+\b(?:one|two|three|four|five|six|seven|eight|nine|ten|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito|nove|dez)\b)?"
    r"\s+(?:percent|por cento|days?|dias?|weeks?|semanas?|months?|meses?|minutes?|minutos?|hours?|horas?|leads?|buyers?|compradores?|sales?|vendas?)\b",
    re.I,
)
ONE_WORD_MATERIAL_RE = re.compile(
    r"\b(?:(?:apenas|somente|so|exatamente|pelo menos|no maximo)\s+(?:um|uma)"
    r"|(?:um|uma)\s+(?:unico|unica))\s+"
    r"(?:days?|dias?|weeks?|semanas?|months?|meses?|minutes?|minutos?|hours?|horas?|leads?|buyers?|compradores?|sales?|vendas?)\b"
    r"|\b(?:um|uma)\s+(?:leads?|compradores?|buyers?|sales?|vendas?)\s+(?:por|a cada)\s+"
    r"(?:dia|day|semana|week|mes|month)\b",
    re.I,
)
INTERVIEWER_OR_PROMO_RE = re.compile(
    r"\b(?:subscribe|sign up|link in the description|podcast|website|you said|do you|what do you think|so you actually|right\?|"
    r"voce disse|o que voce acha|entao voce|nao e\?|certo\?)",
    re.I,
)


def read_reviews(directory: Path) -> list[dict[str, Any]]:
    return [load_json(path) for path in sorted(directory.glob("chunk_*_review.json"))]


def _quote_text(candidate: dict[str, Any]) -> str:
    return " ".join(item.get("quote_verbatim", "") for item in evidence_quotes(candidate))


def _has_material_numeric_text(text: str) -> bool:
    normalized = normalize_ascii(text)
    return bool(
        re.search(r"\d|%|\bpercent\b|\bpor cento\b", normalized, re.I)
        or WORD_NUMBER_MATERIAL_RE.search(normalized)
        or ONE_WORD_MATERIAL_RE.search(normalized)
    )


def _candidate_evidence_segment_ids(candidate: dict[str, Any]) -> set[str]:
    """Read persisted evidence first, with legacy draft arrays as fallback."""
    persisted = {str(item.get("segment_id")) for item in evidence_quotes(candidate) if item.get("segment_id")}
    if persisted:
        return persisted
    return {str(item) for item in candidate.get("minimal_segment_ids", []) + candidate.get("support_segment_ids", []) if item}


def exact_candidate_duplicate_groups(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Find only source-identical candidate duplicates; never infer a merge."""
    groups: dict[tuple[str, str, tuple[str, ...]], list[str]] = {}
    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id") or "")
        claim = " ".join(normalize_ascii(candidate.get("source_claim", "")).split())
        evidence = tuple(sorted(_candidate_evidence_segment_ids(candidate)))
        candidate_type = str(candidate.get("type") or "")
        if not candidate_id or not claim or not evidence or not candidate_type:
            continue
        groups.setdefault((claim, candidate_type, evidence), []).append(candidate_id)
    results: list[dict[str, Any]] = []
    for (claim, candidate_type, evidence), candidate_ids in sorted(groups.items()):
        if len(candidate_ids) < 2:
            continue
        core = {
            "candidate_ids": sorted(candidate_ids),
            "source_claim_normalized": claim,
            "type": candidate_type,
            "segment_ids": list(evidence),
        }
        results.append({
            **core,
            "duplicate_key": sha256_semantic_json(core)[:16],
            "issue": "candidates have the same normalized source claim, type, and source evidence",
            "expected": "merge deliberately or keep distinct source-backed propositions",
        })
    return results


def _meaningful_words(text: str) -> set[str]:
    ignored = {"about", "antes", "com", "como", "depois", "entre", "from", "para", "sobre", "testar", "teste", "that", "this", "uma", "with"}
    return {word for word in re.findall(r"[a-z0-9]+", normalize_ascii(text)) if len(word) >= 5 and word not in ignored}


def _title_content_words(title: str) -> set[str]:
    """Return title terms that can indicate a material semantic overlap."""
    return _meaningful_words(title)


def _has_symmetric_parent_child_relation(
    left_id: str | None,
    right_id: str | None,
    relations: dict[str | None, dict[str, Any]],
) -> bool:
    if not left_id or not right_id:
        return False
    left = relations.get(left_id, {})
    right = relations.get(right_id, {})
    return (
        left.get("parent_candidate_id") == right_id
        and left_id in right.get("child_candidate_ids", [])
    ) or (
        right.get("parent_candidate_id") == left_id
        and right_id in left.get("child_candidate_ids", [])
    )


def _classified(category: str, values: list[Any], kind: str) -> list[dict[str, Any]]:
    return [{"category": category, "kind": kind, "items": values}] if values else []


AUDIT_WARNING_DISPOSITIONS = {
    "confirmed_source_backed", "defer_to_final_audit",
    "captured", "retained_support", "incidental", "relation_not_useful",
}
SEMANTIC_CLOSURE_CATEGORY = "semantic_closure"
SEMANTIC_WORKBENCH_CATEGORY = "semantic_workbench"


def review_audit_warnings(
    warnings: list[dict[str, Any]],
    dispositions: list[dict[str, Any]] | None = None,
    *,
    required_categories: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Attach stable review dispositions without promoting warnings to blockers."""
    required_categories = required_categories or set()
    disposition_by_id = {
        str(item.get("warning_id")): item
        for item in dispositions or []
        if isinstance(item, dict) and item.get("warning_id")
    }
    reviewed = copy.deepcopy(warnings)
    inventory: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for group in reviewed:
        category = str(group.get("category", "unknown"))
        for item in group.get("items", []):
            if not isinstance(item, dict):
                continue
            candidate_ids = sorted(item.get("candidate_ids", [item["candidate_id"]] if item.get("candidate_id") else []))
            segment_ids = sorted(item.get("segment_ids", [item["segment_id"]] if item.get("segment_id") else []))
            source_range = item.get("clean_index_range") or segment_ids
            proposition = (
                item.get("source_claim")
                or item.get("proposition")
                or item.get("issue")
                or item.get("closure_kind")
            )
            warning_input = {
                "category": category,
                "candidate_ids": candidate_ids,
                "segment_ids": segment_ids,
                "source_range": source_range,
                "proposition_fingerprint": sha256_semantic_json(proposition),
            }
            warning_input_sha256 = sha256_semantic_json(warning_input)
            warning_id = "warning-" + warning_input_sha256[:16]
            legacy_warning_id = "warning-" + sha256_semantic_json({
                "category": category,
                "candidate_ids": candidate_ids,
                "segment_ids": segment_ids,
                "issue": item.get("issue"),
            })[:16]
            disposition = disposition_by_id.get(warning_id) or disposition_by_id.get(legacy_warning_id)
            selected_disposition = disposition.get("disposition") if disposition else None
            valid = bool(
                disposition
                and selected_disposition in AUDIT_WARNING_DISPOSITIONS
                and str(disposition.get("justification", "")).strip()
            )
            closure_kind = item.get("closure_kind")
            review_requirement = item.get("review_requirement")
            if valid and category in {SEMANTIC_CLOSURE_CATEGORY, SEMANTIC_WORKBENCH_CATEGORY}:
                if selected_disposition in {"captured", "retained_support"}:
                    destinations = disposition.get("candidate_ids") or disposition.get("destination_candidate_ids") or []
                    valid = isinstance(destinations, list) and bool(destinations)
                elif selected_disposition == "relation_not_useful":
                    valid = closure_kind == "evidence_containment"
                elif selected_disposition == "confirmed_source_backed":
                    valid = category == SEMANTIC_WORKBENCH_CATEGORY and closure_kind in {
                        "candidate_binding", "calibration_binding"
                    } and review_requirement != "must_close"
                elif selected_disposition == "defer_to_final_audit":
                    valid = category == SEMANTIC_WORKBENCH_CATEGORY and review_requirement != "must_close"
                else:
                    valid = selected_disposition == "incidental"
                    if valid and review_requirement == "must_close":
                        reviewed_ids = {
                            str(value) for value in disposition.get("source_segment_ids", [])
                        }
                        valid = bool(segment_ids) and set(segment_ids) <= reviewed_ids
            item["warning_id"] = warning_id
            if valid:
                item["review"] = {
                    key: value for key, value in disposition.items()
                    if key != "warning_id"
                } | {
                    "input_semantic_sha256": warning_input_sha256,
                    "justification": str(disposition["justification"]).strip(),
                }
            row = {
                "warning_id": warning_id,
                "input_semantic_sha256": warning_input_sha256,
                "matched_disposition_warning_id": disposition.get("warning_id") if disposition else None,
                "category": category,
                "candidate_ids": candidate_ids,
                "segment_ids": segment_ids,
                "evidence": {key: value for key, value in item.items() if key not in {"review", "warning_id"}},
                "review": item.get("review"),
            }
            inventory.append(row)
            requires_item_review = category in required_categories and review_requirement != "audit_only"
            if requires_item_review and not valid:
                unresolved.append({
                    "category": "audit_warning_review_required",
                    "kind": "review_gate",
                    "warning_id": warning_id,
                    "warning_category": category,
                    "candidate_ids": candidate_ids,
                    "expected": (
                        "add captured/retained_support with candidate_ids, incidental with source_segment_ids and justification, "
                        "or relation_not_useful for evidence containment"
                        if category in {SEMANTIC_CLOSURE_CATEGORY, SEMANTIC_WORKBENCH_CATEGORY}
                        else "add confirmed_source_backed or defer_to_final_audit with a source-based justification"
                    ),
                })
    return reviewed, inventory, unresolved


def source_complete_invariant_issues(
    report: dict[str, Any],
    *,
    reviewed_warnings: list[dict[str, Any]] | None = None,
    review_gate: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return the single source-completeness verdict shared by every gold gate."""
    issues: list[dict[str, Any]] = []
    summary = report.get("semantic_workbench", {}).get("summary", {})
    transcript_segments = int(summary.get("transcript_segments", report.get("transcript_segments", 0)) or 0)
    covered = int(summary.get("covered_segments", 0) or 0)
    excluded = int(summary.get("excluded_segments", 0) or 0)
    unreviewed = int(summary.get("unreviewed_segments", 0) or 0)
    if covered + excluded + unreviewed != transcript_segments:
        issues.append({
            "issue": "semantic workbench coverage does not reconstruct the complete transcript",
            "transcript_segments": transcript_segments,
            "accounted_segments": covered + excluded + unreviewed,
        })
    if unreviewed:
        issues.append({
            "issue": "source segments remain without a terminal semantic disposition",
            "unreviewed_segments": unreviewed,
        })
    unresolved_must_close = []
    for group in reviewed_warnings or report.get("audit_warnings", []):
        if not isinstance(group, dict):
            continue
        for item in group.get("items", []):
            if (
                isinstance(item, dict)
                and item.get("review_requirement") == "must_close"
                and not item.get("review")
            ):
                unresolved_must_close.append(item.get("warning_id") or item.get("closure_id") or item.get("issue"))
    if unresolved_must_close:
        issues.append({
            "issue": "must-close semantic risks remain unresolved",
            "warning_ids": sorted(str(value) for value in unresolved_must_close if value),
        })
    numeric_missing = sum(
        len(item.get("missing_material", []))
        for item in report.get("numeric_coverage", [])
        if isinstance(item, dict)
    )
    if numeric_missing:
        issues.append({
            "issue": "material numeric occurrences remain unresolved",
            "missing_material_count": numeric_missing,
        })
    calibration = report.get("calibration", {})
    if calibration and calibration.get("status") != "pass":
        issues.append({"issue": "calibration coverage is not compatible with finalization"})
    return issues


RISK_SIGNAL_WEIGHTS = {
    "number": 4,
    "procedure": 3,
    "warning": 3,
    "experiment": 3,
    "comparison": 2,
    "funnel": 2,
    "copy": 1,
    "traffic": 1,
}
RISK_PROMINENCE_RE = re.compile(
    r"\b(?:mais importante|nao importa|muito melhor|tende a aumentar|mudar a conversao|"
    r"teste rapido|de acordo com|velocidade de reproducao|substancia do argumento|"
    r"qualidade do sono|sleep assessment|playback speed)\b",
    re.I,
)


def excluded_risk_clusters(
    transcript: list[dict[str, Any]],
    signals: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    *,
    covered_segment_ids: set[str] | None = None,
    source_clusters: list[dict[str, Any]] | None = None,
    threshold: int = 8,
) -> list[dict[str, Any]]:
    """Surface high-risk excluded spans for semantic review, never auto-capture."""
    covered_segment_ids = covered_segment_ids or set()
    transcript_by_id = {item["segment_id"]: item for item in transcript}
    signal_by_id = {item["segment_id"]: item for item in signals}
    excluded = []
    for decision in decisions:
        segment_id = decision.get("segment_id")
        if decision.get("disposition") != "excluded" or segment_id in covered_segment_ids:
            continue
        segment = transcript_by_id.get(segment_id)
        signal = signal_by_id.get(segment_id)
        if not segment or not signal or not signal.get("signal_types"):
            continue
        excluded.append((int(segment["clean_index"]), segment, signal, decision))
    excluded.sort(key=lambda item: item[0])
    groups: list[list[tuple[int, dict[str, Any], dict[str, Any], dict[str, Any]]]] = []
    for item in excluded:
        if not groups or item[0] > groups[-1][-1][0] + 1:
            groups.append([item])
        else:
            groups[-1].append(item)
    clusters: list[dict[str, Any]] = []
    for group in groups:
        signal_types = sorted({kind for _, _, signal, _ in group for kind in signal.get("signal_types", [])})
        text = " ".join(str(segment.get("text", "")) for _, segment, _, _ in group)
        normalized = normalize_ascii(text)
        score = sum(RISK_SIGNAL_WEIGHTS.get(kind, 0) for kind in signal_types)
        prominence = sorted(set(match.group(0) for match in RISK_PROMINENCE_RE.finditer(normalized)))
        if prominence:
            score += 4
        if score < threshold:
            continue
        segment_ids = [segment["segment_id"] for _, segment, _, _ in group]
        core = {
            "segment_ids": segment_ids,
            "clean_index_range": [group[0][0], group[-1][0]],
            "signal_types": signal_types,
            "score": score,
            "prominence_cues": prominence,
            "text": text,
            "exclusion_reasons": sorted({str(decision.get("reason_code")) for _, _, _, decision in group}),
        }
        residual_sha256 = sha256_semantic_json(core)
        cluster = {
            "cluster_id": f"risk-{residual_sha256[:16]}",
            **core,
            "residual_segment_ids": segment_ids,
            "residual_semantic_sha256": residual_sha256,
        }
        matches = []
        for source in source_clusters or []:
            source_ids = {
                str(item) for item in source.get("source_segment_ids", source.get("segment_ids", []))
            }
            if set(segment_ids) <= source_ids:
                matches.append((len(source_ids), source))
        if matches:
            source = min(matches, key=lambda item: item[0])[1]
            source_ids = [
                str(item) for item in source.get("source_segment_ids", source.get("segment_ids", []))
            ]
            cluster["source_cluster_id"] = source.get("source_cluster_id") or source.get("cluster_id")
            cluster["source_segment_ids"] = source_ids
            cluster["source_semantic_sha256"] = source.get("source_semantic_sha256") or sha256_semantic_json({
                "segment_ids": source_ids,
                "signal_types": source.get("signal_types", []),
                "exclusion_reasons": source.get("exclusion_reasons", []),
            })
        else:
            cluster["source_cluster_id"] = cluster["cluster_id"]
            cluster["source_segment_ids"] = segment_ids
            cluster["source_semantic_sha256"] = sha256_semantic_json({
                "segment_ids": segment_ids,
                "signal_types": signal_types,
                "exclusion_reasons": core["exclusion_reasons"],
            })
        clusters.append(cluster)
    return clusters


SCOPE_CONTINUATION_RE = re.compile(
    r"\b(?:primeiro|segundo|terceiro|quarto|passo|etapa|formato|estrutura|"
    r"alem disso|tambem|por exemplo|outro ponto|ou seja)\b",
    re.I,
)

OUTCOME_CUE_RE = re.compile(
    r"\b(?:resultado|vendeu|vendas|fatur|convers|lucro|roas|roi|retorno|"
    r"funcionou|falhou|sucesso|escal|aument|reduz|caiu|subiu|sustent)\w*\b",
    re.I,
)
MECHANISM_CUE_RE = re.compile(
    r"\b(?:mecanismo|metodo|estrutura|roteiro|script|hook|vsl|anuncio|criativo|"
    r"edicao|gravacao|processo|sequencia|etapa|passo)\w*\b",
    re.I,
)
COMPARISON_CUE_RE = re.compile(
    r"\b(?:antes|depois|contra|compar|maior|menor|mais que|menos que|de\s+\d.{0,80}\s+para\s+\d)\w*",
    re.I,
)
COUNTEREXAMPLE_CUE_RE = re.compile(
    r"\b(?:nao funcion|falhou|fracass|deu errado|sem resultado|nao vendeu|"
    r"nao converteu|tentou mas|porem nao|so que nao)\w*\b",
    re.I,
)
LIMITATION_CUE_RE = re.compile(
    r"\b(?:depende|limit|excecao|ressalva|cuidado|risco|pode variar|"
    r"nao significa|nao garante|incerto|talvez)\w*\b",
    re.I,
)
ECONOMIC_CUE_RE = re.compile(
    r"\b(?:cust|preco|mensal|mensalidade|taxa|econom|invest|orcamento|budget|"
    r"salario|funcionario|contrat|headcount|margem|receita|ticket|cac|ltv|payback|lucro)\w*\b",
    re.I,
)
PRODUCT_CUE_RE = re.compile(
    r"\b(?:produto|feature|funcionalidade|roadmap|trial|cadastro|integracao|cliente|"
    r"feedback|retencao|churn|verticaliz|product.market.fit|pmf|onboarding|ativacao)\w*\b",
    re.I,
)
GENERIC_BINDING_WORDS = {
    "agora", "ainda", "assim", "cliente", "coisa", "empresa", "entao", "fazer",
    "forma", "mercado", "melhor", "mesmo", "muito", "negocio", "parte", "pessoa",
    "poder", "porque", "produto", "resultado", "sobre", "trabalho", "usar", "voce",
}


def _closure_risk(kind: str, text: str) -> dict[str, Any]:
    normalized = normalize_ascii(text)
    reasons: list[str] = []
    score = 0
    if numeric_mentions(text):
        reasons.append("numeric")
        score += 4
    if OUTCOME_CUE_RE.search(normalized):
        reasons.append("outcome")
        score += 4
    if COMPARISON_CUE_RE.search(normalized):
        reasons.append("before_after_or_comparator")
        score += 3
    if MECHANISM_CUE_RE.search(normalized) and SCOPE_CONTINUATION_RE.search(normalized):
        reasons.append("mechanism_continuation")
        score += 3
    if COUNTEREXAMPLE_CUE_RE.search(normalized):
        reasons.append("counterexample")
        score += 6
    if LIMITATION_CUE_RE.search(normalized):
        reasons.append("limitation")
        score += 3
    if kind == "claim_support_gap":
        reasons.append("claim_support_gap")
        score = max(score, 8)
    if kind == "counterexample":
        reasons.append("counterexample")
        score = max(score, 9)
    if kind == "evidence_containment":
        score = min(score, 3)
    requirement = "must_close" if score >= 6 else "audit_only"
    tier = "high" if score >= 9 else "medium" if score >= 6 else "low"
    return {
        "risk_score": score,
        "risk_tier": tier,
        "risk_reasons": sorted(set(reasons)),
        "review_requirement": requirement,
    }


def _binding_words(text: str) -> set[str]:
    words = _meaningful_words(text) - GENERIC_BINDING_WORDS
    normalized: set[str] = set()
    for word in words:
        if word in {"product", "products"}:
            normalized.add("produto")
        elif word.startswith("entrevist"):
            normalized.add("entrevista")
        elif word.startswith("ajust"):
            normalized.add("ajuste")
        else:
            normalized.add(word)
    return normalized


def _clean_index_ranges(segment_ids: set[str], index_by_id: dict[str, int]) -> list[list[int]]:
    indexes = sorted(index_by_id[segment_id] for segment_id in segment_ids if segment_id in index_by_id)
    if not indexes:
        return []
    ranges: list[list[int]] = []
    start = previous = indexes[0]
    for index in indexes[1:]:
        if index != previous + 1:
            ranges.append([start, previous])
            start = index
        previous = index
    ranges.append([start, previous])
    return ranges


def semantic_coverage_workbench(
    transcript: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    signals: list[dict[str, Any]],
    calibration: dict[str, Any],
    decisions: list[dict[str, Any]],
    *,
    max_block_segments: int = 12,
    max_review_items: int = 30,
) -> dict[str, Any]:
    """Build one chronological source-to-claim workbench for review and audit.

    This remains an advisory semantic surface: invalid source identities are
    handled by the existing deterministic validators, while proposition-level
    ambiguity stays visible for model review.
    """
    ordered = sorted(transcript, key=lambda item: int(item["clean_index"]))
    by_id = {str(item["segment_id"]): item for item in ordered}
    index_by_id = {segment_id: int(item["clean_index"]) for segment_id, item in by_id.items()}
    signal_types_by_id = {
        str(item.get("segment_id")): sorted(set(item.get("signal_types", [])))
        for item in signals if item.get("segment_id")
    }
    candidate_by_id = {str(item.get("candidate_id")): item for item in candidates if item.get("candidate_id")}
    evidence_candidates: dict[str, set[str]] = {}
    for candidate_id, candidate in candidate_by_id.items():
        for segment_id in _candidate_evidence_segment_ids(candidate):
            evidence_candidates.setdefault(segment_id, set()).add(candidate_id)
    decision_by_id = {
        str(item.get("segment_id")): item for item in decisions if item.get("segment_id")
    }
    if not any(
        isinstance(test, dict) and "semantic_candidate_ids" in test
        for test in calibration.get("tests", [])
    ):
        calibration = calibration_coverage(calibration, candidates, decisions)

    rows: list[dict[str, Any]] = []
    for segment in ordered:
        segment_id = str(segment["segment_id"])
        decision = decision_by_id.get(segment_id, {})
        candidate_ids = sorted(
            set(evidence_candidates.get(segment_id, set()))
            | {
                str(candidate_id)
                for candidate_id in decision.get("candidate_ids", [])
                if candidate_id
            }
        )
        disposition = str(decision.get("disposition", "pending"))
        if candidate_ids:
            state = "merged" if disposition == "merged" or len(candidate_ids) > 1 else "covered"
        elif disposition == "excluded":
            state = "excluded"
        else:
            state = "unreviewed"
        rows.append({
            "clean_index": int(segment["clean_index"]),
            "segment_id": segment_id,
            "text": str(segment.get("text", "")),
            "state": state,
            "candidate_ids": candidate_ids,
            "signal_types": signal_types_by_id.get(segment_id, []),
            "reason_code": decision.get("reason_code"),
            "reason": decision.get("reason"),
        })

    coverage_blocks: list[dict[str, Any]] = []
    for row in rows:
        current = coverage_blocks[-1] if coverage_blocks else None
        if (
            current is None
            or current["state"] != row["state"]
            or current["segment_count"] >= max_block_segments
            or current["_last_clean_index"] + 1 != row["clean_index"]
        ):
            current = {
                "block_id": f"coverage-{row['clean_index']:04d}",
                "clean_index_range": [row["clean_index"], row["clean_index"]],
                "segment_count": 0,
                "state": row["state"],
                "candidate_ids": [],
                "signal_types": [],
                "reason_codes": [],
                "_texts": [],
                "_segment_ids": [],
                "_last_clean_index": row["clean_index"],
            }
            coverage_blocks.append(current)
        current["clean_index_range"][1] = row["clean_index"]
        current["segment_count"] += 1
        current["candidate_ids"] = sorted(set(current["candidate_ids"]) | set(row["candidate_ids"]))
        current["signal_types"] = sorted(set(current["signal_types"]) | set(row["signal_types"]))
        if row["reason_code"]:
            current["reason_codes"] = sorted(set(current["reason_codes"]) | {row["reason_code"]})
        current["_texts"].append(row["text"])
        current["_segment_ids"].append(row["segment_id"])
        current["_last_clean_index"] = row["clean_index"]

    block_review_items: list[dict[str, Any]] = []
    for block in coverage_blocks:
        text = " ".join(block.pop("_texts"))
        segment_ids = block.pop("_segment_ids")
        block.pop("_last_clean_index")
        risk = _closure_risk("coverage_block", text)
        reasons = set(risk["risk_reasons"])
        score = int(risk["risk_score"])
        if ECONOMIC_CUE_RE.search(normalize_ascii(text)):
            reasons.add("economic_or_unit_economics")
            score += 4
        if PRODUCT_CUE_RE.search(normalize_ascii(text)):
            reasons.add("product_or_customer_learning")
            score += 3
        if block["signal_types"]:
            score += min(3, len(block["signal_types"]))
            reasons.add("signal_inventory")
        explicitly_incidental = (
            block["state"] == "excluded"
            and block["reason_codes"]
            and set(block["reason_codes"]).issubset({"promo", "interviewer_restate", "anecdote"})
        )
        if block["state"] in {"covered", "merged"}:
            requirement = "covered"
        elif explicitly_incidental:
            # A source-scoped exclusion for host promotion, interviewer
            # restatement, or anecdote is a deliberate closure, not an
            # unreviewed material claim.  Keep the state visible as excluded
            # in the dossier while preventing a false must_close escalation.
            requirement = "closed"
        elif score >= 6:
            requirement = "must_close"
        else:
            requirement = "audit_only"
        block.update({
            "risk_score": score,
            "risk_tier": "high" if score >= 9 else "medium" if score >= 6 else "low",
            "risk_reasons": sorted(reasons),
            "review_requirement": requirement,
        })
        if requirement != "covered":
            block["text_preview"] = text[:600]
        if requirement == "must_close":
            block_review_items.append({
                "closure_kind": "uncovered_material",
                "issue": "material source block is not bound to a final candidate",
                "segment_ids": segment_ids,
                "candidate_ids": [],
                **{key: block[key] for key in (
                    "block_id", "clean_index_range", "state", "risk_score", "risk_tier",
                    "risk_reasons", "review_requirement", "text_preview",
                )},
            })

    calibration_ids_by_candidate: dict[str, list[str]] = {}
    for test in calibration.get("tests", []):
        for candidate_id in test.get("semantic_candidate_ids", []):
            calibration_ids_by_candidate.setdefault(str(candidate_id), []).append(str(test.get("calibration_id")))
    candidate_bindings: list[dict[str, Any]] = []
    candidate_review_items: list[dict[str, Any]] = []
    for candidate_id, candidate in sorted(candidate_by_id.items()):
        evidence_ids = _candidate_evidence_segment_ids(candidate)
        evidence_text = " ".join(str(by_id[item].get("text", "")) for item in evidence_ids if item in by_id)
        claim_words = _binding_words(str(candidate.get("source_claim", "")))
        evidence_words = _binding_words(evidence_text)
        shared = claim_words & evidence_words
        overlap_ratio = round(len(shared) / max(1, len(claim_words)), 3)
        structural_missing = not evidence_ids or any(item not in by_id for item in evidence_ids)
        requires_review = structural_missing or (len(claim_words) >= 4 and len(shared) < 2 and overlap_ratio < 0.25)
        binding = {
            "candidate_id": candidate_id,
            "evidence_clean_index_ranges": _clean_index_ranges(evidence_ids, index_by_id),
            "evidence_segment_count": len(evidence_ids),
            "claim_term_count": len(claim_words),
            "shared_proposition_terms": sorted(shared),
            "proposition_overlap_ratio": overlap_ratio,
            "number_record_count": len(candidate.get("numbers") or []),
            "caveat_count": len(candidate.get("caveats") or []),
            "calibration_ids": sorted(calibration_ids_by_candidate.get(candidate_id, [])),
            "requires_review": requires_review,
            "structural_missing_evidence": structural_missing,
        }
        candidate_bindings.append(binding)
        if requires_review:
            candidate_review_items.append({
                "closure_kind": "candidate_binding",
                "issue": "candidate claim and cited evidence need proposition-level confirmation",
                "candidate_ids": [candidate_id],
                "segment_ids": sorted(evidence_ids),
                "clean_index_range": (
                    [min(index_by_id[item] for item in evidence_ids if item in index_by_id),
                     max(index_by_id[item] for item in evidence_ids if item in index_by_id)]
                    if any(item in index_by_id for item in evidence_ids) else []
                ),
                "review_requirement": "must_close" if structural_missing else "audit_only",
                "risk_score": 10 if structural_missing else 5,
                "risk_tier": "high" if structural_missing else "low",
                "risk_reasons": ["missing_source_evidence"] if structural_missing else ["weak_proposition_overlap"],
                "binding": binding,
            })

    calibration_bindings: list[dict[str, Any]] = []
    calibration_review_items: list[dict[str, Any]] = []
    for test in calibration.get("tests", []):
        calibration_id = str(test.get("calibration_id", ""))
        target_ids = {str(item) for item in test.get("segment_ids", []) if item}
        target_text = str(test.get("quote_verbatim", "")) or " ".join(
            str(by_id[item].get("text", "")) for item in target_ids if item in by_id
        )
        target_words = _binding_words(target_text)
        target_numbers = {item["canonical"] for item in numeric_mentions(target_text)}
        linked = [str(item) for item in test.get("semantic_candidate_ids", []) if item]
        linked_results = []
        for candidate_id in linked:
            candidate = candidate_by_id.get(candidate_id)
            if candidate is None:
                linked_results.append({"candidate_id": candidate_id, "status": "missing_candidate"})
                continue
            candidate_words = _binding_words(
                f"{candidate.get('source_claim', '')} {candidate.get('takeaway_applicavel', '')}"
            )
            candidate_numbers = {
                mention["canonical"]
                for record in candidate.get("numbers") or []
                for mention in numeric_mentions(str(record.get("raw", "")))
            }
            evidence_intersection = sorted(target_ids & _candidate_evidence_segment_ids(candidate))
            shared = sorted(target_words & candidate_words)
            numeric_ok = not target_numbers or bool(target_numbers & candidate_numbers)
            status = "covered" if evidence_intersection and shared and numeric_ok else "needs_semantic_confirmation"
            linked_results.append({
                "candidate_id": candidate_id,
                "status": status,
                "evidence_intersection": evidence_intersection,
                "shared_proposition_terms": shared,
                "numeric_anchor_match": numeric_ok,
            })
        suggestions = []
        if not linked or any(item["status"] != "covered" for item in linked_results):
            for candidate_id, candidate in candidate_by_id.items():
                candidate_words = _binding_words(
                    f"{candidate.get('source_claim', '')} {candidate.get('takeaway_applicavel', '')}"
                )
                shared = target_words & candidate_words
                evidence_intersection = target_ids & _candidate_evidence_segment_ids(candidate)
                score = len(shared) + (4 if evidence_intersection else 0)
                if score >= 3:
                    suggestions.append({
                        "candidate_id": candidate_id,
                        "score": score,
                        "shared_proposition_terms": sorted(shared),
                        "evidence_intersection": sorted(evidence_intersection),
                    })
            suggestions.sort(key=lambda item: (-item["score"], item["candidate_id"]))
        requires_review = bool(linked) and any(item["status"] != "covered" for item in linked_results)
        binding = {
            "calibration_id": calibration_id,
            "target_clean_index_ranges": _clean_index_ranges(target_ids, index_by_id),
            "target_segment_ids": sorted(target_ids),
            "semantic_candidate_ids": linked,
            "linked_candidates": linked_results,
            "suggested_candidate_ids": [item["candidate_id"] for item in suggestions[:3]],
            "suggestions": suggestions[:3],
            "requires_review": requires_review,
        }
        calibration_bindings.append(binding)
        if requires_review:
            calibration_review_items.append({
                "closure_kind": "calibration_binding",
                "issue": "calibration target and linked candidate need proposition-level confirmation",
                "candidate_ids": linked,
                "segment_ids": sorted(target_ids),
                "clean_index_range": binding["target_clean_index_ranges"][0] if binding["target_clean_index_ranges"] else [],
                "review_requirement": "audit_only",
                "risk_score": 5,
                "risk_tier": "low",
                "risk_reasons": ["calibration_proposition_ambiguity"],
                "binding": binding,
            })

    all_review_items = sorted(
        [*block_review_items, *candidate_review_items, *calibration_review_items],
        key=lambda item: (-int(item.get("risk_score", 0)), item.get("clean_index_range") or [10**12]),
    )
    core = {
        "schema_version": "1.0.0",
        "coverage_blocks": coverage_blocks,
        "candidate_bindings": candidate_bindings,
        "calibration_bindings": calibration_bindings,
        "review_order": all_review_items[:max_review_items],
        "review_overflow": [
            {key: item.get(key) for key in (
                "closure_kind", "candidate_ids", "segment_ids", "clean_index_range",
                "risk_score", "risk_tier", "risk_reasons", "review_requirement",
            )}
            for item in all_review_items[max_review_items:]
        ],
        "summary": {
            "transcript_segments": len(ordered),
            "coverage_block_count": len(coverage_blocks),
            "covered_segments": sum(item["segment_count"] for item in coverage_blocks if item["state"] in {"covered", "merged"}),
            "excluded_segments": sum(item["segment_count"] for item in coverage_blocks if item["state"] == "excluded"),
            "unreviewed_segments": sum(item["segment_count"] for item in coverage_blocks if item["state"] == "unreviewed"),
            "must_close_count": sum(item.get("review_requirement") == "must_close" for item in all_review_items),
            "audit_only_count": sum(item.get("review_requirement") == "audit_only" for item in all_review_items),
            "candidate_binding_review_count": len(candidate_review_items),
            "calibration_binding_review_count": len(calibration_review_items),
        },
    }
    return {**core, "semantic_sha256": sha256_semantic_json(core)}


def _dedupe_semantic_closure(
    items: list[dict[str, Any]],
    by_index: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge repeated source windows while retaining every candidate lineage."""
    ordered = sorted(
        items,
        key=lambda item: (
            -int(item.get("risk_score", 0)),
            item.get("clean_index_range", [10**12, 10**12]),
            item.get("closure_id", ""),
        ),
    )
    kept: list[dict[str, Any]] = []
    for item in ordered:
        current_ids = set(item.get("segment_ids", []))
        merged = None
        for prior in kept:
            if prior.get("review_requirement") != item.get("review_requirement"):
                continue
            prior_ids = set(prior.get("segment_ids", []))
            overlap = len(current_ids & prior_ids) / max(1, min(len(current_ids), len(prior_ids)))
            if overlap >= 0.6 and prior.get("closure_kind") == item.get("closure_kind"):
                merged = prior
                break
        if merged is None:
            kept.append(copy.deepcopy(item))
            continue
        merged["candidate_ids"] = sorted(set(merged.get("candidate_ids", [])) | set(item.get("candidate_ids", [])))
        merged["segment_ids"] = sorted(
            set(merged.get("segment_ids", [])) | current_ids,
            key=lambda segment_id: next(
                (index for index, row in by_index.items() if str(row.get("segment_id")) == segment_id),
                10**12,
            ),
        )
        indexes = sorted(
            int(row["clean_index"])
            for row in by_index.values()
            if str(row.get("segment_id")) in set(merged["segment_ids"])
        )
        merged["clean_index_range"] = [indexes[0], indexes[-1]]
        merged["text"] = " ".join(str(by_index[index].get("text", "")) for index in indexes)
        merged["risk_score"] = max(int(merged.get("risk_score", 0)), int(item.get("risk_score", 0)))
        merged["risk_tier"] = "high" if merged["risk_score"] >= 9 else "medium" if merged["risk_score"] >= 6 else "low"
        merged["risk_reasons"] = sorted(set(merged.get("risk_reasons", [])) | set(item.get("risk_reasons", [])))
        merged["closure_kinds"] = sorted(
            set(merged.get("closure_kinds", [merged.get("closure_kind")]))
            | set(item.get("closure_kinds", [item.get("closure_kind")]))
        )
        lineage_core = {
            "review_requirement": merged.get("review_requirement"),
            "risk_reasons": merged["risk_reasons"],
            "segment_ids": merged["segment_ids"],
        }
        merged["lineage_id"] = "lineage-" + sha256_semantic_json(lineage_core)[:16]
    return sorted(
        kept,
        key=lambda item: (
            item.get("review_requirement") != "must_close",
            -int(item.get("risk_score", 0)),
            item.get("clean_index_range", [10**12, 10**12]),
        ),
    )


def semantic_closure_index(
    transcript: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    signals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build source-only review windows around evidence and episode borders."""
    by_index = {int(item["clean_index"]): item for item in transcript}
    index_by_id = {str(item["segment_id"]): int(item["clean_index"]) for item in transcript}
    signal_ids = {
        str(item.get("segment_id")) for item in signals
        if item.get("segment_id") and item.get("signal_types")
    }
    evidence_by_candidate: dict[str, dict[str, set[int]]] = {}
    covered: set[int] = set()
    relations: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id", ""))
        evidence = candidate.get("evidence", {}) if isinstance(candidate.get("evidence"), dict) else {}
        minimal = {
            index_by_id[str(item.get("segment_id"))]
            for item in evidence.get("minimal_quote", [])
            if isinstance(item, dict) and str(item.get("segment_id")) in index_by_id
        }
        support = {
            index_by_id[str(item.get("segment_id"))]
            for item in evidence.get("support_segments", [])
            if isinstance(item, dict) and str(item.get("segment_id")) in index_by_id
        }
        evidence_by_candidate[candidate_id] = {"minimal": minimal, "all": minimal | support}
        covered.update(minimal | support)
        relations[candidate_id] = candidate.get("relations", {}) if isinstance(candidate.get("relations"), dict) else {}

    results: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(kind: str, indexes: list[int], candidate_ids: list[str], **extra: Any) -> None:
        indexes = sorted({index for index in indexes if index in by_index})
        if not indexes:
            return
        segment_ids = [str(by_index[index]["segment_id"]) for index in indexes]
        identity = sha256_semantic_json({
            "closure_kind": kind,
            "candidate_ids": sorted(candidate_ids),
            "segment_ids": segment_ids,
        })
        if identity in seen:
            return
        seen.add(identity)
        text = " ".join(str(by_index[index].get("text", "")) for index in indexes)
        risk = _closure_risk(kind, text)
        lineage_core = {
            "review_requirement": risk["review_requirement"],
            "risk_reasons": risk["risk_reasons"],
            "segment_ids": segment_ids,
        }
        results.append({
            "closure_id": f"closure-{identity[:16]}",
            "lineage_id": "lineage-" + sha256_semantic_json(lineage_core)[:16],
            "closure_kind": kind,
            "closure_kinds": [kind],
            "candidate_ids": sorted(candidate_ids),
            "segment_ids": segment_ids,
            "clean_index_range": [indexes[0], indexes[-1]],
            "text": text,
            "issue": kind,
            **risk,
            **extra,
        })

    for candidate_id, evidence in sorted(evidence_by_candidate.items()):
        indexes = evidence["all"]
        if not indexes:
            continue
        first, last = min(indexes), max(indexes)
        for direction, raw_range in (
            ("before", range(max(min(by_index), first - 12), first)),
            ("after", range(last + 1, min(max(by_index), last + 12) + 1)),
        ):
            window: list[int] = []
            iterable = reversed(list(raw_range)) if direction == "before" else raw_range
            for index in iterable:
                if index in covered:
                    break
                window.append(index)
            window = sorted(window)
            if not window:
                continue
            meaningful = [
                index for index in window
                if str(by_index[index]["segment_id"]) in signal_ids
                or SCOPE_CONTINUATION_RE.search(normalize_ascii(str(by_index[index].get("text", ""))))
            ]
            if meaningful:
                window = (
                    [index for index in window if index >= min(meaningful)]
                    if direction == "before"
                    else [index for index in window if index <= max(meaningful)]
                )
                add("adjacent_evidence_tail", window, [candidate_id], direction=direction)

    if evidence_by_candidate and covered:
        last_covered = max(covered)
        tail = [index for index in sorted(by_index) if index > last_covered]
        if tail:
            add("episode_tail", tail, [])

    for left, right in zip(chunks, chunks[1:]):
        left_index = index_by_id.get(str(left.get("last_segment_id")))
        right_index = index_by_id.get(str(right.get("first_segment_id")))
        if left_index is None or right_index is None:
            continue
        window = [
            index for index in range(max(min(by_index), left_index - 1), min(max(by_index), right_index + 1) + 1)
            if index not in covered
        ]
        if window:
            add(
                "chunk_boundary", window, [],
                between_chunks=[left.get("chunk_id"), right.get("chunk_id")],
            )

    candidate_ids = sorted(evidence_by_candidate)
    for left_index, left_id in enumerate(candidate_ids):
        left = evidence_by_candidate[left_id]
        if not left["minimal"]:
            continue
        for right_id in candidate_ids[left_index + 1:]:
            right = evidence_by_candidate[right_id]
            if not right["minimal"]:
                continue
            containment = (
                left["minimal"] <= right["all"] or right["minimal"] <= left["all"]
            )
            if not containment or _has_symmetric_parent_child_relation(left_id, right_id, relations):
                continue
            add(
                "evidence_containment",
                sorted(left["minimal"] | right["minimal"]),
                [left_id, right_id],
            )

    candidate_by_id = {
        str(candidate.get("candidate_id", "")): candidate
        for candidate in candidates
        if candidate.get("candidate_id")
    }
    for candidate_id, evidence in sorted(evidence_by_candidate.items()):
        indexes = evidence["all"]
        candidate = candidate_by_id.get(candidate_id)
        if not indexes or candidate is None:
            continue
        first, last = min(indexes), max(indexes)
        adjacent = [
            index
            for index in range(max(min(by_index), first - 3), min(max(by_index), last + 3) + 1)
            if index not in indexes
        ]
        if not adjacent:
            continue
        claim_words = _meaningful_words(str(candidate.get("source_claim", "")))
        evidence_text = " ".join(str(by_index[index].get("text", "")) for index in sorted(indexes))
        evidence_words = _meaningful_words(evidence_text)
        missing_claim_words = claim_words - evidence_words
        claim_support_indexes = [
            index for index in adjacent
            if missing_claim_words & _meaningful_words(str(by_index[index].get("text", "")))
        ]
        if claim_support_indexes:
            add(
                "claim_support_gap",
                claim_support_indexes,
                [candidate_id],
                missing_claim_terms=sorted(missing_claim_words)[:24],
            )
        proposition_words = claim_words | evidence_words
        counterexample_indexes = [
            index for index in adjacent
            if COUNTEREXAMPLE_CUE_RE.search(normalize_ascii(str(by_index[index].get("text", ""))))
            and proposition_words & _meaningful_words(str(by_index[index].get("text", "")))
        ]
        if counterexample_indexes:
            add("counterexample", counterexample_indexes, [candidate_id])

    return _dedupe_semantic_closure(results, by_index)


def sparse_recall_view(report: dict[str, Any]) -> dict[str, Any]:
    """Return only unresolved or audit-relevant inventories for model review."""
    fields = {
        "missing_reviews": report.get("missing_reviews", []),
        "numbers": report.get("numbers", []),
        "numeric_occurrence_matrix": report.get("numeric_occurrence_matrix", []),
        "steps": report.get("steps", []),
        "calibration_target_errors": report.get("calibration_target_errors", []),
        "calibration_semantic_alignment": report.get("calibration_semantic_alignment", []),
        "ledger_semantic_alignment": report.get("ledger_semantic_alignment", []),
        "high_signals_without_direct_destination": report.get("high_signals_without_direct_destination", []),
        "automatic_ledger_preview": report.get("automatic_ledger_preview", []),
        "overlapping_candidates_without_relation": report.get("overlapping_candidates_without_relation", []),
        "chunk_boundaries_to_review": report.get("chunk_boundaries_to_review", []),
        "candidate_supported_only_by_interviewer_or_promo": report.get("candidate_supported_only_by_interviewer_or_promo", []),
        "reported_case_without_caveat": report.get("reported_case_without_caveat", []),
        "risk_recall_clusters": report.get("risk_recall_clusters", []),
        "semantic_closure_index": report.get("semantic_closure_index", []),
        "semantic_workbench": report.get("semantic_workbench", {}),
    }
    return {
        "episode_video_id": report.get("episode_video_id"),
        "reviewed_chunks": report.get("reviewed_chunks"),
        "candidate_count": report.get("candidate_count"),
        "transcript_segments": report.get("transcript_segments"),
        "calibration": report.get("calibration"),
        "hard_blockers": report.get("hard_blockers", []),
        "audit_warnings": report.get("audit_warnings", []),
        "inventories": {key: value for key, value in fields.items() if value},
        "semantic_report_hash": report.get("semantic_report_hash"),
    }


def _numeric_value_from_canonical(canonical: str) -> float | None:
    base, _, magnitude = canonical.partition(":")
    try:
        value = float(base)
    except (TypeError, ValueError):
        return None
    multiplier = {
        "k": 1_000.0,
        "mil": 1_000.0,
        "milhao": 1_000_000.0,
        "milhoes": 1_000_000.0,
    }.get(magnitude, 1.0)
    return value * multiplier


def _number_record_consistency(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    candidate_id = candidate.get("candidate_id")
    for record_index, record in enumerate(candidate.get("numbers") or []):
        if not isinstance(record, dict):
            continue
        mentions = numeric_mentions(record.get("raw", ""))
        if not mentions or any(item.get("asr_separated_decimal") for item in mentions):
            continue
        values = [
            _numeric_value_from_canonical(str(item.get("canonical", "")))
            for item in mentions
        ]
        values = [value for value in values if value is not None]
        expected: list[float] = []
        if record.get("min_value") is not None and record.get("max_value") is not None:
            expected = [float(record["min_value"]), float(record["max_value"])]
        elif record.get("value") is not None and len(values) == 1:
            expected = [float(record["value"])]
        if not expected or len(expected) != len(values):
            continue
        mismatch = any(
            abs(left - right) > max(1e-9, abs(right) * 1e-9)
            for left, right in zip(values, expected)
        )
        caveat_text = normalize_ascii(" ".join(
            str(item) for item in candidate.get("caveats") or []
        )).casefold()
        raw_text = normalize_ascii(str(record.get("raw") or "")).casefold()
        explicit_asr_correction = (
            mismatch
            and record.get("value_status") == "inferred"
            and bool(raw_text)
            and raw_text in caveat_text
            and "asr" in caveat_text
        )
        if mismatch and not explicit_asr_correction:
            issues.append({
                "candidate_id": candidate_id,
                "record_index": record_index,
                "raw": record.get("raw"),
                "literal_values": values,
                "structured_values": expected,
                "issue": "structured numeric value does not match raw literal",
            })
    return issues


def numeric_occurrence_matrix(
    transcript: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    signals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return source-complete candidate numeric rows, including risky adjacencies."""
    by_id = {str(item["segment_id"]): item for item in transcript}
    by_index = {int(item["clean_index"]): item for item in transcript}
    signal_types_by_segment = {
        str(item.get("segment_id")): set(item.get("signal_types", []))
        for item in signals if item.get("segment_id")
    }
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        coverage = candidate_numeric_coverage(candidate, signal_types_by_segment)
        evidence_ids = _candidate_evidence_segment_ids(candidate)
        evidence_indexes = sorted(
            int(by_id[segment_id]["clean_index"])
            for segment_id in evidence_ids if segment_id in by_id
        )
        adjacent_occurrences: list[dict[str, Any]] = []
        if evidence_indexes:
            first, last = min(evidence_indexes), max(evidence_indexes)
            adjacent_indexes = [
                index
                for index in range(max(min(by_index), first - 3), min(max(by_index), last + 3) + 1)
                if index not in evidence_indexes
            ]
            for clean_index in adjacent_indexes:
                segment = by_index[clean_index]
                text = str(segment.get("text", ""))
                risk = _closure_risk("adjacent_numeric", text)
                if risk["review_requirement"] != "must_close":
                    continue
                for mention in numeric_mentions(text):
                    adjacent_occurrences.append({
                        "segment_id": segment["segment_id"],
                        "clean_index": clean_index,
                        "raw": mention["raw"],
                        "canonical": mention["canonical"],
                        "kind": mention["kind"],
                        "risk_reasons": risk["risk_reasons"],
                        "disposition": "requires_semantic_confirmation",
                    })
        rows.append({
            "candidate_id": candidate.get("candidate_id"),
            "status": coverage.get("status"),
            "record_count": coverage.get("record_count", 0),
            "occurrences": coverage.get("mentions", []),
            "adjacent_occurrences": adjacent_occurrences,
            "record_consistency_issues": _number_record_consistency(candidate),
            "sequence": coverage.get("sequence", {}),
        })
    return rows


def autocheck_state(
    video_id: str,
    *,
    status: dict[str, Any],
    transcript: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
    signals: list[dict[str, Any]],
    calibration: dict[str, Any],
    reviews: list[dict[str, Any]] | dict[str, dict[str, Any]],
    stored_ledger: list[dict[str, Any]] | None = None,
    prefer_stored_ledger: bool = True,
) -> dict[str, Any]:
    """Evaluate the final candidate state without requiring persisted reviews."""
    review_values = list(reviews.values()) if isinstance(reviews, dict) else list(reviews)
    reviews = {review.get("chunk_id"): review for review in review_values}
    candidates = [candidate for review in reviews.values() for candidate in review.get("candidates", [])]
    evidence_ids = {segment_id for candidate in candidates for segment_id in _candidate_evidence_segment_ids(candidate)}
    stored_ledger = stored_ledger or []
    review_decisions = [decision for review in reviews.values() for decision in review.get("ledger_decisions", [])]
    manual_decisions = {
        str(decision["segment_id"]): decision
        for decision in review_decisions
        if decision.get("segment_id")
    }
    # Preparation creates pending placeholders. Once a derived ledger has real
    # dispositions it is the final source of truth for this read-only preview.
    final_decisions = (
        stored_ledger
        if prefer_stored_ledger and any(item.get("disposition") != "pending" for item in stored_ledger)
        else ledger_for_signals(signals, candidates, manual_decisions)
    )
    number_issues: list[dict[str, Any]] = []
    numeric_coverage: list[dict[str, Any]] = []
    numeric_coverage_warnings: list[dict[str, Any]] = []
    steps_issues: list[str] = []
    encoding: list[str] = []
    interview_or_promo: list[str] = []
    interviewer_only: list[str] = []
    claim_evidence: list[dict[str, Any]] = []
    caveat_issues: list[str] = []
    ledger_issues: list[dict[str, Any]] = []
    signal_types_by_segment = {
        str(item.get("segment_id")): set(item.get("signal_types", []))
        for item in signals
        if item.get("segment_id")
    }
    numeric_matrix = numeric_occurrence_matrix(transcript, candidates, signals)
    consistency_by_candidate = {
        str(item.get("candidate_id")): item.get("record_consistency_issues", [])
        for item in numeric_matrix
    }
    for candidate in candidates:
        quote_text = _quote_text(candidate)
        numbers = candidate.get("numbers", [])
        coverage = candidate_numeric_coverage(candidate, signal_types_by_segment)
        numeric_coverage.append(coverage)
        for missing in coverage["missing_material"]:
            number_issues.append({
                "candidate_id": candidate.get("candidate_id"),
                "segment_ids": [missing["segment_id"]] if missing.get("segment_id") else [],
                "issue": f"material numeric evidence is not represented in numbers: {missing['raw']}",
                "numeric_mention": missing,
            })
        for warning in coverage["audit_warnings"]:
            numeric_coverage_warnings.append({
                "candidate_id": candidate.get("candidate_id"),
                "segment_ids": [warning["segment_id"]] if warning.get("segment_id") else [],
                "issue": f"support-only numeric evidence needs semantic confirmation: {warning['raw']}",
                "numeric_mention": warning,
            })
        number_issues.extend(copy.deepcopy(
            consistency_by_candidate.get(str(candidate.get("candidate_id")), [])
        ))
        if _has_material_numeric_text(quote_text) and not numbers and not coverage["missing_material"]:
            number_issues.append({"candidate_id": candidate.get("candidate_id"), "issue": "possible material numeric evidence without structured numbers"})
        for error in validate_numbers(candidate.get("candidate_id", "<unknown>"), numbers, [quote_text]):
            number_issues.append({"candidate_id": candidate.get("candidate_id"), "issue": error})
        if candidate.get("type") in {"playbook_step", "framework", "script"} and not candidate.get("steps"):
            steps_issues.append(candidate.get("candidate_id", "<unknown>"))
        encoding.extend(editorial_ascii_errors(candidate))
        normalized = normalize_ascii(quote_text)
        if INTERVIEWER_OR_PROMO_RE.search(normalized):
            interview_or_promo.append(candidate.get("candidate_id", "<unknown>"))
        quote_parts = [normalize_ascii(item.get("quote_verbatim", "")) for item in evidence_quotes(candidate)]
        if quote_parts and all(INTERVIEWER_OR_PROMO_RE.search(item) for item in quote_parts):
            interviewer_only.append(candidate.get("candidate_id", "<unknown>"))
        claim_words = _meaningful_words(str(candidate.get("source_claim", "")))
        evidence_words = _meaningful_words(quote_text)
        if claim_words and not (claim_words & evidence_words):
            claim_evidence.append({
                "candidate_id": candidate.get("candidate_id"),
                "issue": "claim has no meaningful lexical support in minimal evidence",
                "source_claim": candidate.get("source_claim"),
                "minimal_quote": [
                    item.get("quote_verbatim", "")
                    for item in candidate.get("evidence", {}).get("minimal_quote", [])
                ],
            })
        if candidate.get("reported_case") and candidate.get("numbers") and not candidate.get("caveats"):
            caveat_issues.append(candidate.get("candidate_id", "<unknown>"))
    candidate_by_id = {candidate.get("candidate_id"): candidate for candidate in candidates}
    calibration_target_ids = {
        str(source_id)
        for test in calibration.get("tests", [])
        for source_id in test.get("segment_ids", [])
    }

    def explicit_calibration_duplicate(decision: dict[str, Any]) -> bool:
        destination_ids = decision.get("candidate_ids") or []
        return (
            decision.get("disposition") == "merged"
            and decision.get("reason_code") == "duplicate_of"
            and decision.get("reason_reference") in destination_ids
            and str(decision.get("segment_id")) in calibration_target_ids
            and str(decision.get("reason", "")).startswith("source_equivalent_duplicate:")
        )

    decisions_by_segment: dict[str, list[dict[str, Any]]] = {}
    for decision in final_decisions:
            segment_id = decision.get("segment_id")
            if segment_id:
                decisions_by_segment.setdefault(segment_id, []).append(decision)
            if decision.get("disposition") == "excluded":
                reason = decision.get("reason_code")
                reference = decision.get("reason_reference")
                if reason not in EXCLUSION_REASON_CODES or (reason == "duplicate_of" and reference not in candidate_by_id):
                    ledger_issues.append({"segment_id": segment_id, "issue": "excluded ledger decision has invalid reason or reference"})
                continue
            if decision.get("disposition") not in {"captured", "merged"}:
                ledger_issues.append({"segment_id": segment_id, "issue": "ledger decision has invalid disposition"})
                continue
            destination_ids = decision.get("candidate_ids") or []
            if not destination_ids:
                ledger_issues.append({"segment_id": decision.get("segment_id"), "issue": "captured or merged decision has no candidate destination"})
                continue
            matching = [candidate_by_id.get(candidate_id) for candidate_id in destination_ids]
            if any(candidate is None for candidate in matching) or (
                not explicit_calibration_duplicate(decision)
                and not any(
                    decision.get("segment_id") in _candidate_evidence_segment_ids(candidate)
                    for candidate in matching if candidate
                )
            ):
                ledger_issues.append({"segment_id": decision.get("segment_id"), "candidate_ids": destination_ids, "issue": "ledger destination does not cite the same segment"})
    high_signals = [signal for signal in signals if signal.get("signal_types")]
    automatic_ledger_preview: list[dict[str, Any]] = []
    for signal in high_signals:
        segment_decisions = decisions_by_segment.get(signal["segment_id"], [])
        resolved = False
        for decision in segment_decisions:
            if decision.get("disposition") == "excluded":
                reason = decision.get("reason_code")
                resolved = reason in EXCLUSION_REASON_CODES and (reason != "duplicate_of" or decision.get("reason_reference") in candidate_by_id)
            elif decision.get("disposition") in {"captured", "merged"}:
                resolved = explicit_calibration_duplicate(decision) or any(
                    candidate_id in candidate_by_id and signal["segment_id"] in _candidate_evidence_segment_ids(candidate_by_id[candidate_id])
                    for candidate_id in decision.get("candidate_ids", [])
                )
            if resolved:
                break
        if not resolved:
            automatic_ledger_preview.append({"segment_id": signal["segment_id"], "signal_types": signal["signal_types"], "issue": "automatic ledger final decision is missing or unsupported"})
    uncovered = [
        {"segment_id": signal["segment_id"], "signal_types": signal["signal_types"]}
        for signal in high_signals
        if signal["segment_id"] not in evidence_ids and signal["segment_id"] not in decisions_by_segment
    ]
    relations = {candidate.get("candidate_id"): candidate.get("relations", {}) for candidate in candidates}
    overlaps: list[dict[str, Any]] = []
    for left_index, left in enumerate(candidates):
        left_words = _title_content_words(str(left.get("title", "")))
        for right in candidates[left_index + 1:]:
            right_words = _title_content_words(str(right.get("title", "")))
            shared = left_words & right_words
            if len(shared) >= 3:
                left_id, right_id = left.get("candidate_id"), right.get("candidate_id")
                if not _has_symmetric_parent_child_relation(left_id, right_id, relations):
                    overlaps.append({"candidate_ids": [left_id, right_id], "shared_title_terms": sorted(shared)})
    signal_by_id = {item["segment_id"]: item for item in signals}
    boundaries: list[dict[str, Any]] = []
    for left, right in zip(chunks, chunks[1:]):
        left_signal = signal_by_id.get(left["last_segment_id"])
        right_signal = signal_by_id.get(right["first_segment_id"])
        if left_signal or right_signal:
            boundaries.append({
                "between_chunks": [left["chunk_id"], right["chunk_id"]],
                "segment_ids": [left["last_segment_id"], right["first_segment_id"]],
                "signal_types": [left_signal.get("signal_types", []) if left_signal else [], right_signal.get("signal_types", []) if right_signal else []],
            })
    calibration_target_issues = calibration_target_errors(calibration, {item["segment_id"]: item for item in transcript})
    calibration_result = calibration_coverage(calibration, candidates, final_decisions)
    calibration_semantic_issues: list[dict[str, Any]] = []
    for test in calibration.get("tests", []):
        for candidate_id in test.get("semantic_candidate_ids", []):
            candidate = candidate_by_id.get(candidate_id)
            if candidate is None:
                calibration_semantic_issues.append({"calibration_id": test.get("calibration_id"), "candidate_id": candidate_id, "issue": "missing candidate"})
                continue
            target_words = _meaningful_words(str(test.get("quote_verbatim", "")))
            candidate_words = _meaningful_words(f"{candidate.get('source_claim', '')} {candidate.get('takeaway_applicavel', '')}")
            target_numbers = set(re.findall(r"\d+(?:[.,]\d+)?", normalize_ascii(str(test.get("quote_verbatim", "")))))
            candidate_numbers = set(re.findall(r"\d+(?:[.,]\d+)?", " ".join(str(item.get("raw", "")) for item in candidate.get("numbers", []))))
            if (target_words and not (target_words & candidate_words)) or (target_numbers and not (target_numbers & candidate_numbers)):
                calibration_semantic_issues.append({"calibration_id": test.get("calibration_id"), "candidate_id": candidate_id, "issue": "candidate may not express calibration proposition"})
    missing_reviews = [chunk["chunk_id"] for chunk in status.get("chunks", []) if chunk["chunk_id"] not in reviews]
    risk_clusters = excluded_risk_clusters(
        transcript,
        signals,
        final_decisions,
        covered_segment_ids=evidence_ids,
    )
    closure_index = semantic_closure_index(transcript, chunks, candidates, signals)
    workbench = semantic_coverage_workbench(
        transcript, candidates, signals, calibration_result, final_decisions
    )
    exact_duplicates = exact_candidate_duplicate_groups(candidates)
    report = {
        "episode_video_id": video_id,
        "read_only": True,
        "reviewed_chunks": len(reviews),
        "missing_reviews": missing_reviews,
        "candidate_count": len(candidates),
        "numbers": number_issues,
        "numeric_coverage": numeric_coverage,
        "numeric_occurrence_matrix": numeric_matrix,
        "steps": steps_issues,
        "calibration": calibration_result,
        "calibration_target_errors": calibration_target_issues,
        "editorial_encoding": sorted(set(encoding)),
        "candidate_with_promo_or_interviewer_language": sorted(set(interview_or_promo)),
        "candidate_supported_only_by_interviewer_or_promo": sorted(set(interviewer_only)),
        "claim_evidence_alignment": claim_evidence,
        "ledger_semantic_alignment": ledger_issues,
        "calibration_semantic_alignment": calibration_semantic_issues,
        "reported_case_without_caveat": sorted(set(caveat_issues)),
        "relation_integrity": normalize_relations(candidates),
        "high_signals_without_direct_destination": uncovered,
        "automatic_ledger_preview": automatic_ledger_preview,
        "overlapping_candidates_without_relation": overlaps,
        "chunk_boundaries_to_review": boundaries,
        "risk_recall_clusters": risk_clusters,
        "semantic_closure_index": closure_index,
        "semantic_workbench": workbench,
        "exact_candidate_duplicates": exact_duplicates,
        "transcript_segments": len(transcript),
    }
    hard_categories = {
        "missing_reviews": [{"chunk_id": item} for item in missing_reviews],
        "numbers": number_issues,
        "steps": [{"candidate_id": item, "issue": "procedural candidate needs steps"} for item in steps_issues],
        "editorial_encoding": [{"issue": item} for item in sorted(set(encoding))],
        "ledger": ledger_issues,
        "relation": [{"issue": item} for item in normalize_relations(candidates)],
        "high_signal": uncovered + automatic_ledger_preview,
        "calibration_structure": [{"issue": item} for item in calibration_target_issues],
        "exact_candidate_duplicates": exact_duplicates,
    }
    if calibration_result["status"] != "pass":
        hard_categories["calibration_coverage"] = [{"issue": "calibration coverage below episode minimum or has duplicate targets"}]
    warning_categories = {
        "promo_or_interviewer": [{"candidate_id": item} for item in sorted(set(interview_or_promo))],
        "interviewer_or_promo_only": [{"candidate_id": item} for item in sorted(set(interviewer_only))],
        "overlap": overlaps,
        "calibration_semantic_ambiguity": calibration_semantic_issues,
        "claim_evidence_alignment": claim_evidence,
        "reported_case_caveat": [{"candidate_id": item, "issue": "reported case has no caveat"} for item in caveat_issues],
        "numeric_support_ambiguity": numeric_coverage_warnings,
        SEMANTIC_CLOSURE_CATEGORY: closure_index,
        SEMANTIC_WORKBENCH_CATEGORY: workbench.get("review_order", []),
    }
    report["hard_blockers"] = [
        item for category, values in hard_categories.items() for item in _classified(category, values, "hard_blocker")
    ]
    report["audit_warnings"] = [
        item for category, values in warning_categories.items() for item in _classified(category, values, "audit_warning")
    ]
    review_categories = {
        "claim_evidence": claim_evidence,
        "ledger": ledger_issues,
        "calibration": calibration_semantic_issues,
        "caveat": [{"candidate_id": item, "issue": "reported case has no caveat"} for item in caveat_issues],
        "relation": [{"issue": item} for item in normalize_relations(candidates)],
        "interviewer_promo": [{"candidate_id": item, "issue": "all evidence is interviewer or promo language"} for item in interviewer_only],
        "overlap": overlaps,
        "high_signal": uncovered + automatic_ledger_preview,
    }
    issues: list[dict[str, Any]] = []
    for category, values in review_categories.items():
        for value in values:
            candidate_ids = sorted(value.get("candidate_ids", [value["candidate_id"]] if value.get("candidate_id") else []))
            segment_ids = sorted(value.get("segment_ids", [value["segment_id"]] if value.get("segment_id") else []))
            issue_id = sha256_semantic_json({"category": category, "candidate_ids": candidate_ids, "segment_ids": segment_ids, "issue": value.get("issue", "")})[:16]
            issues.append({"issue_id": f"semantic-{issue_id}", "category": category, "candidate_ids": candidate_ids, "segment_ids": segment_ids, "evidence": value, "resolution_required": category not in {"claim_evidence", "calibration", "caveat", "interviewer_promo", "overlap"}})
    report["review_required"] = issues
    report["semantic_report_hash"] = sha256_semantic_json(report)
    return report


def autocheck(
    video_id: str,
    data_root: Path,
    *,
    prefer_persisted_ledger: bool = True,
) -> dict[str, Any]:
    out = data_root / "processed" / video_id / "gold_extraction"
    stored_ledger_path = out / "high_signal_coverage_ledger.json"
    return autocheck_state(
        video_id,
        status=load_json(out / "gold_extraction_status.json"),
        transcript=load_json(out / "transcript_clean.json")["segments"],
        chunks=load_json(out / "chunks" / "chunk_index.json")["chunks"],
        signals=load_json(out / "signal_inventory.json").get("signals", []),
        calibration=load_json(out / "calibration_tests.json"),
        reviews=read_reviews(out / "manual_reviews"),
        stored_ledger=(
            load_json(stored_ledger_path).get("entries", [])
            if prefer_persisted_ledger and stored_ledger_path.exists()
            else []
        ),
        prefer_stored_ledger=prefer_persisted_ledger,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when deterministic gaps are found.")
    args = parser.parse_args()
    result = autocheck(args.video_id, args.data_root)
    print(json.dumps(result, ensure_ascii=False))
    return 1 if args.strict and result["hard_blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
