---
name: marketing-swipe-file-detect-assets
description: Detect and track complementary materials mentioned in Marketing Swipe File episodes. Use when Codex needs to identify PDFs, docs, spreadsheets, slides, templates, prompts, swipes, checklists, member-area materials, direct/comment keyword instructions, public download links, and manual acquisition tasks from metadata and transcript segments.
---

# Marketing Swipe File Detect Assets

## Overview

Use this skill after transcript normalization or whenever complementary material detection needs to be rerun.

## Workflow

1. Confirm the episode has `metadata.json` and `content_segments.json`.
2. Set the runtime data root when MSF-R03 external data is active:
   ```powershell
   $dataRoot = if ($env:MSF_DATA_DIR) { $env:MSF_DATA_DIR } else { "data" }
   ```
3. Run:
   `scripts/detect_assets.py --metadata "$dataRoot\raw\youtube\{video_id}\metadata.json" --segments "$dataRoot\processed\{video_id}\content_segments.json" --output-dir "$dataRoot\processed\{video_id}"`
4. Review `referenced_assets.json`, `acquisition_tasks.json`, and `manual_actions.md`.
5. Refresh the global queue with:
   `scripts/consolidate_exports.py`

## Rules

- Require evidence from description or transcript before creating an asset.
- Do not create a task for generic mentions unless there is an action, link, download, direct, comment keyword, member-area instruction, or other acquisition context.
- Keep the original quote and timestamp when available.
- Use statuses exactly as local schemas define them.

## Outputs

- `$dataRoot\processed\{video_id}\referenced_assets.json`
- `$dataRoot\processed\{video_id}\acquisition_tasks.json`
- `$dataRoot\processed\{video_id}\manual_actions.md`
- `$dataRoot\exports\acquisition_tasks_master.csv`
