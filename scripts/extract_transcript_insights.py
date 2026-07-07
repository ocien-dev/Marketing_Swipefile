#!/usr/bin/env python
"""Extract evidence-backed candidate insights from transcript chunks."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from msf_common import load_json, normalize_text, slugify, unique_preserve_order, write_json, write_text


@dataclass(frozen=True)
class Rule:
    rule_id: str
    title: str
    insight: str
    keywords: tuple[str, ...]
    themes: tuple[str, ...]
    applicability: tuple[str, ...]
    level: str
    insight_type: str
    funnel_stages: tuple[str, ...] = ()
    anchors: tuple[str, ...] = ()


RULES = [
    Rule(
        "low_ticket_validation_cost",
        "Low ticket reduz o custo de validacao de oferta",
        "Use uma oferta low ticket para validar promessa, criativo e funil com menos caixa antes de escalar uma oferta maior.",
        ("low ticket", "validar", "menos gasto", "r$ 19", "testar"),
        ("ofertas", "low ticket", "anuncios", "copy"),
        ("CMO", "copy strategist", "copywriter de anuncios"),
        "strategic",
        "principle",
        ("conversion",),
        ("low ticket",),
    ),
    Rule(
        "low_ticket_acquisition_model",
        "Low ticket deve ser tratado como aquisicao, nao so como produto",
        "O low ticket ganha forca quando vira mecanismo de aquisicao e aprendizado comercial, nao apenas uma venda barata isolada.",
        ("aquisicao", "comprador", "low ticket", "base", "lista"),
        ("funil", "low ticket", "ofertas"),
        ("CMO", "copy strategist"),
        "strategic",
        "principle",
        ("conversion", "retention"),
        ("aquisicao", "comprador", "lista"),
    ),
    Rule(
        "offer_first_transformation",
        "A oferta low ticket precisa vender uma transformacao pequena e concreta",
        "A primeira oferta deve prometer uma transformacao especifica, facil de entender e suficiente para justificar a primeira compra.",
        ("oferta", "produto", "entregavel", "transformacao", "comprar"),
        ("ofertas", "produto", "copy", "low ticket"),
        ("CMO", "copy strategist", "head de produto"),
        "tactical",
        "framework",
        ("conversion",),
        ("oferta", "produto", "entregavel"),
    ),
    Rule(
        "sticky_naming",
        "Nome chiclete aumenta lembranca e clareza da oferta",
        "Um nome simples, memoravel e repetivel ajuda o mercado a entender e lembrar a promessa da oferta.",
        ("nome", "chiclete", "lembrar", "promessa", "headline"),
        ("copy", "ofertas", "produto"),
        ("copy strategist", "head de produto"),
        "tactical",
        "tactic",
        ("conversion",),
        ("nome", "chiclete"),
    ),
    Rule(
        "one_belief_one_pager",
        "One belief e one pager forcam clareza antes da producao",
        "Antes de gravar ou construir uma VSL, comprima a tese em uma crenca central e em uma pagina para remover excesso de complexidade.",
        ("one belief", "one pager", "crenca", "pagina", "vsl"),
        ("VSL", "copy", "ofertas"),
        ("copywriter de VSLs", "copy strategist"),
        "tactical",
        "framework",
        ("conversion",),
        ("one belief", "one pager"),
    ),
    Rule(
        "real_expert_low_ticket",
        "Expert real aumenta autoridade no low ticket",
        "Usar um expert real pode aumentar percepcao de autoridade e prova em ofertas de entrada quando a promessa depende de credibilidade.",
        ("expert", "autoridade", "pessoa", "prova", "low ticket"),
        ("ofertas", "prova social", "low ticket", "copy"),
        ("CMO", "copy strategist"),
        "strategic",
        "principle",
        ("conversion",),
        ("expert", "autoridade"),
    ),
    Rule(
        "quiz_self_recognition",
        "Quiz faz o lead se reconhecer antes do pitch",
        "O quiz funciona melhor quando segmenta intencao e faz a pessoa se enxergar no problema antes da mini VSL ou da oferta.",
        ("quiz", "pergunta", "responder", "resultado", "pessoa"),
        ("quiz", "funil", "copy", "low ticket"),
        ("copywriter de quiz", "CMO", "copy strategist"),
        "tactical",
        "framework",
        ("awareness", "conversion"),
        ("quiz",),
    ),
    Rule(
        "quiz_question_structure",
        "Perguntas do quiz devem mapear dor, desejo e nivel de consciencia",
        "As perguntas do quiz devem coletar sinais comerciais uteis, nao apenas entreter; elas precisam revelar dor, desejo e prontidao de compra.",
        ("pergunta", "quiz", "dor", "desejo", "consciencia"),
        ("quiz", "avatar", "copy"),
        ("copywriter de quiz", "copy strategist"),
        "operational",
        "checklist",
        ("awareness", "conversion"),
        ("quiz", "pergunta"),
    ),
    Rule(
        "mini_vsl_middle",
        "Mini VSL pode destravar a pagina de low ticket",
        "Inserir uma mini VSL no funil pode explicar o mecanismo com menos friccao que uma pagina estatica, especialmente para trafego frio.",
        ("mini vsl", "pagina de vendas", "explodiu", "resultado", "30.000", "100.000"),
        ("VSL", "low ticket", "copy", "funil"),
        ("copywriter de VSLs", "copy strategist", "CMO"),
        "tactical",
        "case",
        ("conversion",),
        ("mini vsl",),
    ),
    Rule(
        "two_mini_vsls",
        "Duas mini VSLs podem separar aquecimento e decisao",
        "Um funil pode usar duas mini VSLs para separar educacao, mecanismo e decisao de compra em momentos diferentes.",
        ("duas mini", "duas vsl", "mini vsl", "segunda vsl", "funil"),
        ("VSL", "funil", "copy", "low ticket"),
        ("copywriter de VSLs", "CMO"),
        "tactical",
        "framework",
        ("conversion",),
        ("duas mini", "duas vsl", "segunda vsl"),
    ),
    Rule(
        "creative_variation_system",
        "Um criativo validado deve virar uma esteira de variacoes",
        "Depois que um criativo valida um angulo, derive novas versoes mudando hook, prova, visual e objecao em vez de recomecar do zero.",
        ("criativo", "variacao", "10", "validado", "anuncio"),
        ("anuncios", "criativos", "hooks", "copy"),
        ("copywriter de anuncios", "copy strategist"),
        "operational",
        "playbook_step",
        ("awareness",),
        ("criativo", "anuncio"),
    ),
    Rule(
        "image_creative_can_scale",
        "Imagem simples pode escalar quando o angulo e forte",
        "Um criativo em imagem simples pode performar muito bem se a promessa, prova e angulo estiverem claros.",
        ("imagem", "criativo", "400", "vendas", "simples"),
        ("anuncios", "criativos", "copy"),
        ("copywriter de anuncios",),
        "operational",
        "case",
        ("awareness",),
        ("imagem",),
    ),
    Rule(
        "traffic_testing_cost",
        "O custo de teste cai quando a variacao e sistematica",
        "Organize testes de criativos por variaveis controladas para reduzir desperdicio de verba e acelerar aprendizado.",
        ("trafego", "teste", "custo", "criativo", "campanha"),
        ("anuncios", "criativos", "gestao"),
        ("copywriter de anuncios", "CMO"),
        "operational",
        "tactic",
        ("awareness",),
        ("trafego", "campanha", "criativo"),
    ),
    Rule(
        "metrics_to_watch",
        "Otimizar exige separar metrica de criativo, VSL e checkout",
        "A leitura de metricas precisa separar onde o funil quebrou: anuncio, quiz, VSL, checkout, upsell ou recorrencia.",
        ("metrica", "olhar", "checkout", "vsl", "criativo", "taxa"),
        ("funil", "anuncios", "VSL", "checkout"),
        ("CMO", "copywriter de anuncios", "copywriter de VSLs"),
        "operational",
        "checklist",
        ("conversion",),
        ("metrica", "olhar", "taxa"),
    ),
    Rule(
        "backend_upsell_recurring",
        "Backend, upsell e recorrencia mudam a economia do low ticket",
        "A oferta de entrada deve ser pensada junto com upsell, backend e recorrencia para melhorar LTV e capacidade de aquisicao.",
        ("upsell", "backend", "recorrencia", "ltv", "assinatura"),
        ("funil", "ofertas", "checkout", "low ticket"),
        ("CMO", "copy strategist"),
        "strategic",
        "principle",
        ("conversion", "retention"),
        ("upsell", "backend", "recorrencia", "ltv"),
    ),
    Rule(
        "asymmetric_bets",
        "Apostas assimetricas permitem testar upside grande com risco controlado",
        "Busque iniciativas em que o downside seja limitado e o upside possa mudar o patamar do negocio.",
        ("aposta", "assimetrica", "risco", "upside", "downside"),
        ("gestao", "produto", "estrategias"),
        ("CMO", "COO", "head de produto"),
        "strategic",
        "principle",
        (),
        ("aposta", "assimetrica", "upside", "downside"),
    ),
    Rule(
        "strategy_vs_execution",
        "Estrategia so vira vantagem quando encontra execucao consistente",
        "A ideia estrategica precisa virar rotina, responsavel e criterio de qualidade para produzir resultado repetivel.",
        ("estrategia", "execucao", "rotina", "consistente", "fazer"),
        ("gestao", "estrategias", "operacao"),
        ("COO", "CMO"),
        "strategic",
        "principle",
        (),
        ("estrategia", "execucao"),
    ),
    Rule(
        "founder_mode",
        "Founder mode preserva velocidade e criterio em decisoes importantes",
        "Em decisoes de alto impacto, o fundador precisa manter proximidade com produto, marketing e barra de qualidade.",
        ("founder", "fundador", "decisao", "produto", "marketing"),
        ("gestao", "produto", "operacao"),
        ("CEO", "COO", "head de produto"),
        "strategic",
        "principle",
        (),
        ("founder", "fundador"),
    ),
    Rule(
        "high_performance_team",
        "Times fortes precisam de barra alta e contexto claro",
        "Contratacao e gestao de time dependem de criterio alto, contexto claro e capacidade de remover gargalos de execucao.",
        ("time", "contratar", "barra", "alta performance", "gestao"),
        ("gestao", "operacao"),
        ("COO", "CEO"),
        "operational",
        "framework",
        (),
        ("time", "contratar", "alta performance"),
    ),
    Rule(
        "excellent_product",
        "Produto excelente aumenta retencao e reduz dependencia de forca bruta em marketing",
        "Quando o produto entrega valor real, marketing, indicacao e retencao tendem a trabalhar juntos em vez de compensar uma entrega fraca.",
        ("produto", "excelente", "cliente", "valor", "retencao"),
        ("produto", "retencao", "gestao"),
        ("head de produto", "CMO"),
        "strategic",
        "principle",
        ("retention",),
        ("produto", "cliente", "retencao"),
    ),
    Rule(
        "unsophisticated_market_copy_opportunity",
        "Mercado pouco sofisticado aumenta o upside de uma copy melhor",
        "Quando o mercado ainda aceita copy basica, uma sales letter com promessa, mecanismo e prova mais bem construidos pode criar vantagem competitiva rapida.",
        ("market", "unsophisticated", "sales letters", "copy", "convert", "benefit copy", "opportunity"),
        ("copy", "mercado", "ofertas", "VSL"),
        ("copy strategist", "copywriter de VSLs", "CMO"),
        "strategic",
        "principle",
        ("conversion",),
        ("unsophisticated", "market"),
    ),
    Rule(
        "localized_proof_and_mechanism",
        "Mecanismo importado precisa de prova e contexto local",
        "Ao adaptar uma promessa de outro mercado, traduza tambem os elementos de prova, exemplos e mecanismo para referencias que o publico local reconhece.",
        ("proof", "proof elements", "mechanism", "american sales letter", "brazilian market", "market", "keto", "harvard"),
        ("copy", "prova social", "mecanismo", "mercado"),
        ("copy strategist", "copywriter de VSLs"),
        "tactical",
        "framework",
        ("conversion",),
        ("proof", "mechanism"),
    ),
    Rule(
        "long_form_sales_copy_still_works",
        "Copy longa continua forte quando o mecanismo exige educacao",
        "Nao encurte a pagina ou VSL por reflexo; quando a oferta precisa educar, provar e quebrar objecoes, o formato longo pode converter melhor.",
        ("long form", "sales letter", "sales copy", "attention spans", "short", "benefit oriented", "still remains the king"),
        ("copy", "VSL", "ofertas"),
        ("copywriter de VSLs", "copy strategist"),
        "strategic",
        "principle",
        ("conversion",),
        ("sales letter", "long form"),
    ),
    Rule(
        "rmbc_copy_sequence",
        "RMBC organiza copy em pesquisa, mecanismo, crenca e fechamento",
        "Use uma metodologia sequencial para sair da pesquisa de mercado, construir mecanismo e crenca central, e so depois escrever a promessa e a VSL.",
        ("rmbc", "research", "mechanism", "belief", "copywriting methodology", "sales copy", "step-by-step"),
        ("copy", "VSL", "mecanismo", "pesquisa"),
        ("copy strategist", "copywriter de VSLs"),
        "tactical",
        "framework",
        ("conversion",),
        ("rmbc", "mechanism", "belief"),
    ),
    Rule(
        "lead_depends_on_mechanism",
        "Lead forte nasce do mecanismo, nao so do hook",
        "Antes de escrever a lead, defina o mecanismo causal que torna a promessa crivel; isso evita uma abertura chamativa sem substancia.",
        ("lead", "mechanism", "headline", "hook", "sales letter", "copy", "big idea", "opening"),
        ("copy", "hooks", "mecanismo", "VSL"),
        ("copy strategist", "copywriter de VSLs", "copywriter de anuncios"),
        "tactical",
        "framework",
        ("awareness", "conversion"),
        ("lead", "mechanism"),
    ),
    Rule(
        "vsl_optimization_from_copy_assets",
        "Otimizacao de VSL deve partir dos ativos de copy que ja provaram valor",
        "Reescreva a VSL observando quais partes da copy, prova, mecanismo e objecoes ja sustentam conversao, em vez de trocar tudo de uma vez.",
        ("vsl", "optimize", "optimization", "sales copy", "offer", "proof", "mechanism", "conversion"),
        ("VSL", "copy", "ofertas", "metricas"),
        ("copywriter de VSLs", "CMO", "copy strategist"),
        "operational",
        "playbook_step",
        ("conversion",),
        ("vsl", "optimize"),
    ),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def segment_text(segment: dict[str, Any]) -> str:
    return str(segment.get("text_ptbr") or segment.get("text_original") or "").strip()


def score_rule(text: str, rule: Rule) -> int:
    normalized = normalize_text(text)
    anchors = rule.anchors or rule.keywords[:1]
    if not any(normalize_text(anchor) in normalized for anchor in anchors):
        return 0
    return sum(1 for keyword in rule.keywords if normalize_text(keyword) in normalized)


def has_number_or_money(text: str) -> bool:
    normalized = normalize_text(text)
    return any(char.isdigit() for char in normalized) or any(marker in normalized for marker in ["r$", "$", "mil", "milhao", "milhoes"])


def window_for(segments: list[dict[str, Any]], index: int, radius: int = 1) -> list[dict[str, Any]]:
    start = max(0, index - radius)
    end = min(len(segments), index + radius + 1)
    return segments[start:end]


def quote_from_window(items: list[dict[str, Any]], max_chars: int = 700) -> str:
    quote = " ".join(segment_text(item) for item in items if segment_text(item))
    quote = " ".join(quote.split())
    if len(quote) <= max_chars:
        return quote
    return quote[:max_chars].rsplit(" ", 1)[0].rstrip() + "..."


def find_candidates(video_id: str, chunks_dir: Path, max_per_rule: int, max_per_chunk: int) -> list[dict[str, Any]]:
    chunk_paths = sorted(path for path in chunks_dir.glob("chunk_*.json") if path.name != "chunk_index.json")
    candidates: list[dict[str, Any]] = []
    per_rule_count: dict[str, int] = {}

    for chunk_path in chunk_paths:
        chunk = load_json(chunk_path)
        segments = [item for item in chunk.get("segments", []) if isinstance(item, dict)]
        chunk_candidates: list[tuple[int, Rule, int, list[dict[str, Any]], str]] = []
        for index, segment in enumerate(segments):
            text = segment_text(segment)
            if len(text) < 25:
                continue
            local_window = window_for(segments, index, radius=1)
            window_text = quote_from_window(local_window, max_chars=900)
            for rule in RULES:
                score = score_rule(window_text, rule)
                if score < 2:
                    continue
                weighted = score * 10 + (4 if has_number_or_money(window_text) else 0) + min(len(window_text) // 120, 4)
                chunk_candidates.append((weighted, rule, index, local_window, chunk.get("title") or chunk_path.stem))

        chunk_candidates.sort(key=lambda item: item[0], reverse=True)
        used_rules_in_chunk: set[str] = set()
        used_segments: set[str] = set()
        kept_for_chunk = 0
        for weighted, rule, index, evidence_segments, chunk_title in chunk_candidates:
            if kept_for_chunk >= max_per_chunk:
                break
            if rule.rule_id in used_rules_in_chunk:
                continue
            if per_rule_count.get(rule.rule_id, 0) >= max_per_rule:
                continue
            primary_segment = evidence_segments[min(1, len(evidence_segments) - 1)]
            primary_id = str(primary_segment.get("segment_id") or "")
            if primary_id and primary_id in used_segments:
                continue
            used_rules_in_chunk.add(rule.rule_id)
            used_segments.add(primary_id)
            per_rule_count[rule.rule_id] = per_rule_count.get(rule.rule_id, 0) + 1
            kept_for_chunk += 1
            candidates.append(
                {
                    "rule": rule,
                    "weighted": weighted,
                    "chunk_title": chunk_title,
                    "primary_segment": primary_segment,
                    "evidence_segments": evidence_segments,
                    "quote": quote_from_window(evidence_segments),
                }
            )

    return candidates


def build_insight(video_id: str, candidate: dict[str, Any], index: int) -> dict[str, Any]:
    rule: Rule = candidate["rule"]
    primary_segment = candidate["primary_segment"]
    evidence_segments = candidate["evidence_segments"]
    quote = candidate["quote"]
    start_seconds = primary_segment.get("start_seconds")
    end_seconds = primary_segment.get("end_seconds")
    evidence_strength = "strong" if candidate["weighted"] >= 28 else "medium"
    confidence = 0.82 if evidence_strength == "strong" else 0.76
    title = f"{rule.title} ({candidate['chunk_title']})"
    segment_ids = "-".join(str(item.get("segment_index", "")) for item in evidence_segments if item.get("segment_index") is not None)
    return {
        "insight_id": f"{video_id}-tr-insight-{index + 1:04d}",
        "source_kind": "transcript",
        "title": title[:160],
        "insight_original": None,
        "insight_ptbr": rule.insight,
        "summary_ptbr": rule.title,
        "level": rule.level,
        "insight_type": rule.insight_type,
        "themes": list(rule.themes),
        "subthemes": [candidate["chunk_title"]],
        "applicability": list(rule.applicability),
        "niches": ["infoprodutos"],
        "funnel_stages": list(rule.funnel_stages),
        "confidence_score": confidence,
        "review_status": "auto_accepted" if confidence >= 0.8 else "needs_review",
        "source_agent": "transcript_chunk_heuristic_extractor",
        "dedupe_key": f"transcript-{video_id}-{rule.rule_id}-{slugify(candidate['chunk_title'], max_length=60)}-{segment_ids}",
        "evidence": [
            {
                "evidence_id": f"{video_id}-tr-evidence-{index + 1:04d}",
                "segment_id": primary_segment.get("segment_id"),
                "episode_video_id": video_id,
                "asset_id": None,
                "start_seconds": start_seconds,
                "end_seconds": end_seconds,
                "page_number": None,
                "sheet_name": None,
                "cell_range": None,
                "slide_number": None,
                "quote_original": quote,
                "quote_ptbr": None,
                "evidence_strength": evidence_strength,
            }
        ],
        "relations": [],
    }


def extract_episode(video_id: str, processed_root: Path, output_name: str, max_per_rule: int, max_per_chunk: int) -> dict[str, Any]:
    chunks_dir = processed_root / video_id / "chunks"
    if not chunks_dir.exists():
        raise FileNotFoundError(f"Missing chunks directory: {chunks_dir}")
    candidates = find_candidates(video_id, chunks_dir, max_per_rule=max_per_rule, max_per_chunk=max_per_chunk)
    insights = [build_insight(video_id, candidate, index) for index, candidate in enumerate(candidates)]
    payload = {
        "schema_version": "1.0",
        "episode_video_id": video_id,
        "asset_id": None,
        "generated_at": utc_now(),
        "insights": insights,
    }
    output_path = processed_root / video_id / output_name
    write_json(output_path, payload)
    write_text(
        processed_root / video_id / "transcript_insights_summary.md",
        render_summary(video_id, output_path, insights),
    )
    return payload


def render_summary(video_id: str, output_path: Path, insights: list[dict[str, Any]]) -> str:
    theme_counts: dict[str, int] = {}
    for insight in insights:
        for theme in insight.get("themes") or []:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
    lines = [
        f"# Transcript Insights - {video_id}",
        "",
        f"- Output: `{output_path}`",
        f"- Insights: {len(insights)}",
        "",
        "## Themes",
        "",
    ]
    for theme, count in sorted(theme_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- {theme}: {count}")
    lines.extend(["", "## Sample", ""])
    for insight in insights[:10]:
        evidence = (insight.get("evidence") or [{}])[0]
        lines.append(f"- `{insight['insight_id']}` {insight['title']}")
        lines.append(f"  - {insight['insight_ptbr']}")
        lines.append(f"  - Evidence: {evidence.get('quote_original')}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", action="append", dest="video_ids", help="Episode video id. Can be repeated.")
    parser.add_argument("--all-processed", action="store_true", help="Process every episode with a chunks directory.")
    parser.add_argument("--processed-root", default=Path("data/processed"), type=Path)
    parser.add_argument("--output-name", default="insights.json")
    parser.add_argument("--max-per-rule", default=8, type=int)
    parser.add_argument("--max-per-chunk", default=3, type=int)
    args = parser.parse_args()

    if args.all_processed:
        video_ids = sorted(path.name for path in args.processed_root.iterdir() if (path / "chunks").exists())
    else:
        video_ids = args.video_ids or []
    if not video_ids:
        parser.error("Provide --video-id or --all-processed")

    total = 0
    for video_id in video_ids:
        payload = extract_episode(video_id, args.processed_root, args.output_name, args.max_per_rule, args.max_per_chunk)
        count = len(payload["insights"])
        total += count
        print(f"Wrote {count} transcript insight(s) for {video_id} to {args.processed_root / video_id / args.output_name}")
    print(f"Wrote {total} transcript insight(s) total.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
