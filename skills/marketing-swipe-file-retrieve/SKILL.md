---
name: marketing-swipe-file-retrieve
description: Search the local Marketing Swipe File and build evidence-backed strategy packs for agents. Use when Codex needs to query consolidated insights by text, theme, source, episode, level, insight type, applicability, confidence, or source_kind, and when creating VSL, ads, offer, quiz, webinar, or copy strategy context from the local base.
---

# Marketing Swipe File Retrieve

## Overview

Use this skill whenever an agent needs references from the local base before producing strategy, VSLs, ads, offers, quizzes, or copy.

## Workflow

Set the runtime data root when MSF-R03 external data is active:

```powershell
$dataRoot = if ($env:MSF_DATA_DIR) { $env:MSF_DATA_DIR } else { "data" }
```

1. Refresh master exports:
   `scripts/consolidate_exports.py`
2. Search directly when exploring:
   `scripts/search_insights.py --source curated --process-tags process-copy-vsl --query "lead mecanismo" --limit 10`
3. Generate a task pack when creating an output:
   `scripts/generate_strategy_pack.py --source curated --task vsl --process-tags process-copy-vsl,process-mecanismo-big-idea --product "<produto>" --avatar "<avatar>" --market "<mercado>" --output-json "$dataRoot\exports\strategy_pack_vsl.json" --output-md "$dataRoot\exports\strategy_pack_vsl.md"`
4. Use `prompts/retrieval/strategy_pack_retrieval.md` when a model needs to turn retrieved records into a structured context package.

## Rules

- Always cite `insight_id` when using an insight in an output.
- Use `curated_insights` as the default source for process skills and post-R3 strategy packs.
- Prefer insights with strong evidence and higher confidence.
- Keep transcript and asset sources separate.
- If the strategy pack has few or zero results, say the base is not mature enough for that task yet.

## Useful Filters

- `--theme VSL`
- `--source-kind asset`
- `--level tactical`
- `--insight-type framework`
- `--applicability "copywriter de VSLs"`
- `--process-tags process-copy-vsl,process-prova-depoimentos`
- `--min-confidence 0.75`
