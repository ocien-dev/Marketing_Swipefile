# Strategy Pack Retrieval Prompt

Use this prompt to transform consolidated Marketing Swipe File records into an evidence-backed strategy pack for a consuming agent.

## Inputs

Provide:

- task
- product
- avatar
- market or niche
- desired asset type
- constraints
- candidate insights from `data/exports/insights_master.json` or `scripts/search_insights.py`

## Output

Return JSON with:

```json
{
  "task": "vsl",
  "briefing": {
    "product": "",
    "avatar": "",
    "market": "",
    "asset_type": "",
    "constraints": []
  },
  "recommended_angles": [],
  "usable_insights": [],
  "asset_references": [],
  "evidence": [],
  "frameworks": [],
  "warnings": [],
  "open_questions": []
}
```

## Selection Rules

- Prioritize insights with exact task fit, strong evidence, and high confidence.
- Prefer asset-derived frameworks, templates, checklists, spreadsheets, and complete copy when available.
- Separate facts from hypotheses.
- Keep every recommendation tied to `insight_id`.
- Include the shortest useful evidence quote for each selected insight.
- Add warnings when confidence is low, the evidence is weak, or the insight may be overgeneralized.
- Add open questions when the base does not contain enough evidence for the requested task.

## Task Theme Map

- VSL: VSL, copy, hooks, ofertas, funil, avatar, prova social, low ticket, high ticket.
- Anuncios: anuncios, criativos, hooks, copy, avatar, prova social, ofertas.
- Oferta: ofertas, preco, prova social, avatar, funil.
- Quiz: quiz, avatar, ofertas, copy, funil.
- Webinar: webinar, copy, ofertas, prova social, funil.

## Prohibited Behavior

- Do not invent insights.
- Do not cite evidence that is not present in the records.
- Do not use insights without an `insight_id`.
- Do not hide missing evidence; list it under `open_questions` or `warnings`.
