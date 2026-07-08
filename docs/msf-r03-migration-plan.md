# MSF-R03 Data Migration Plan

Date: 2026-07-08

Status: `done`

Execution note 2026-07-08: phases 1-3 were executed for owner audit. Phase 4
cleanup/delete was then executed after owner approval. See
`docs/msf-r03-phase-1-3-report-2026-07-08.md` and
`docs/msf-r03-phase-4-report-2026-07-08.md`.

No files were moved in this planning pass. This document proposes how to move
large/local-only data out of the OneDrive-backed repo without losing tracked
files or breaking the pipeline.

## Source Scope

Canonical scope from `docs/marketing-swipe-file-remediation-backlog.md`:

- Problem: thousands of JSON/media files under `data/` can trigger OneDrive
  locks and sync conflicts; stale markers were already blocked by OneDrive
  permissions.
- Preferred option: move `data/raw/`, `data/processed/`, and `data/exports/`
  outside OneDrive, then point scripts through an environment variable or a
  constant/helper in `scripts/msf_common.py`.
- Alternative option: exclude data folders from OneDrive sync.
- Acceptance: the full pipeline runs from the new location, with no phantom
  `transcript_fallback_needed.md` or permission errors in a full validation.

This plan expands the move set as a proposal because the current inventory also
shows large/local-only data under `data/input/assets/`, `data/logs/`, and
`data/cache/`.

## Current Inventory

Workspace root:

`C:\Users\luish\OneDrive\Code\Marketing_Swipe_File`

Top-level `data/` inventory:

| Path | Files | Approx size | Git tracked | Ignored/local-only |
|---|---:|---:|---:|---:|
| `data/raw` | 861 | 5687.92 MB | 2 | 859 |
| `data/processed` | 7851 | 437.52 MB | 2 | 7849 |
| `data/cache` | 700 | 157.89 MB | 0 | 700 |
| `data/input` | 51 | 100.62 MB | 4 | 47 |
| `data/logs` | 150 | 16.57 MB | 1 | 149 |
| `data/exports` | 131 | 12.23 MB | 22 | 109 |

Largest subtrees:

| Path | Files | Approx size |
|---|---:|---:|
| `data/raw/academy_hls` | 136 | 3783.78 MB |
| `data/raw/academy_media` | 124 | 1779.23 MB |
| `data/processed` | 7851 | 437.52 MB |
| `data/input/assets` | 47 | 100.50 MB |
| `data/cache/pip` | 186 | 83.29 MB |
| `data/cache/faster_whisper` | 11 | 74.58 MB |
| `data/raw/assets` | 93 | 100.56 MB |
| `data/raw/youtube` | 508 | 24.36 MB |
| `data/logs` | 150 | 16.57 MB |
| `data/exports` | 131 | 12.23 MB |

Tracked files currently under `data/`:

- `data/exports/.gitkeep`
- S09 offer and VSL audit artifacts already versioned under `data/exports/`
  (22 tracked `data/exports` files total, including keys, blind samples, judged
  samples, encoding-fixed VSL sample, and strategy packs).
- `data/input/academy_video_transcription_queue.csv`
- `data/input/assets/.gitkeep`
- `data/input/youtube_urls.example.csv`
- `data/input/youtube_urls_academy_new.csv`
- `data/logs/.gitkeep`
- `data/processed/assets/.gitkeep`
- `data/processed/taxonomy_seed.json`
- `data/raw/assets/.gitkeep`
- `data/raw/youtube/.gitkeep`

Important implication: do not replace the whole `data/` tree with a junction
and do not delete whole top-level data directories. Several lightweight/tracked
files must remain versioned unless the owner explicitly approves de-tracking.

## Proposed Destination

Primary recommendation:

`C:\MSF-data\Marketing_Swipe_File`

Fallback if writing to `C:\` requires unwanted permissions:

`%LOCALAPPDATA%\MSF-data\Marketing_Swipe_File`

Rationale:

- Outside `C:\Users\luish\OneDrive\...`, so OneDrive stops syncing thousands of
  generated files.
- Durable project data, not temp/cache-only data.
- Short path reduces Windows path-length and escaping friction.
- Easy to inspect, back up, and set as `MSF_DATA_DIR`.

The external directory should contain these subfolders directly:

```text
C:\MSF-data\Marketing_Swipe_File\
  raw\
  processed\
  exports\
  input\
  logs\
  cache\
```

## Proposed Path Resolution

Add a small data-root API to `scripts/msf_common.py` before moving files:

- `repo_root() -> Path`: current repo root.
- `repo_data_root() -> Path`: `repo_root() / "data"`.
- `data_root() -> Path`: `Path($env:MSF_DATA_DIR)` when set, otherwise
  `repo_data_root()`.
- `data_path(*parts) -> Path`: `data_root().joinpath(*parts)`.
- Optional `repo_data_path(*parts) -> Path`: for tracked repo-only seeds or
  examples when intentionally not using external data.

Recommended behavior:

- If `MSF_DATA_DIR` is unset, fallback to the current repo-local `data/` layout
  so existing tests and lightweight use keep working.
- If `MSF_DATA_DIR` is set, local-only runtime reads/writes use the external
  data root.
- Tracked project scaffolding and seeds stay in Git. The main exception is
  `taxonomy_seed.json`: either keep validators reading the tracked repo file,
  or copy it to the external `processed/` directory during migration and verify
  both copies match. The lower-risk first pass is to keep the tracked taxonomy
  in the repo and update validators to use it explicitly.

Potential environment setup:

```powershell
$env:MSF_DATA_DIR = "C:\MSF-data\Marketing_Swipe_File"
```

Later, if approved, document this in `.env.example` or project setup docs. Do
not commit a user-local `.env`.

## Current Path Assumptions To Change

Most scripts already expose path flags, but their defaults still point to
`Path("data/...")`. These defaults should call `data_path(...)` instead.

High-impact scripts:

| Area | Files / defaults today | Proposed change |
|---|---|---|
| YouTube ingest | `collect_youtube_metadata.py`, `collect_youtube_transcript.py`, `collect_youtube_transcript_from_playwright_snapshot.py`, `capture_youtube_transcript_with_playwright_cli.py` default to `data/raw/youtube` | Default to `data_path("raw", "youtube")`; keep explicit `--output-root` override |
| Episode pipeline | `run_episode_pipeline.py`, `run_episode_batch.py` default to `data/raw/youtube`, `data/processed`, `data/input/youtube_urls.csv`, and `data/logs` | Defaults through `data_path`; tracked example queues stay repo-local |
| Processing/extraction | `extract_description_insights.py`, `extract_transcript_insights.py`, `extract_transcript_insights_llm.py`, `audit_insights_v2_text.py` default to `data/raw`, `data/processed`, `data/exports` | Defaults through `data_path`; all explicit flags still work |
| Consolidation | `consolidate_exports.py` defaults to `data/raw/youtube`, `data/raw/assets`, `data/processed`, `data/exports`, `data/input/youtube_urls.csv` | Defaults through `data_path`; optionally keep tracked queue fallback when external queue missing |
| Curated/retrieval | `generate_curated_insights.py`, `search_insights.py`, `generate_strategy_pack.py`, `evaluate_output.py`, `generate_insight_v1_v2_review.py` default to masters under `data/exports` | `DEFAULT_MASTERS` and output defaults through `data_path("exports", ...)` |
| Taxonomy | `classify_taxonomy.py`, `create_process_skill.py`, `validate_process_skill.py`, `validate_transversal_modules.py`, `prepare_extraction_packet.py`, `prepare_chunked_extraction_packets.py` read `data/processed/taxonomy_seed.json` | Prefer a repo-tracked taxonomy path helper or copy taxonomy into external root and verify equality |
| Assets | `register_assets.py`, `process_asset.py`, `run_asset_pipeline.py` default to `data/raw/assets`, `data/processed/assets`, `data/logs` | Defaults through `data_path`; input assets under `data_path("input", "assets")` |
| Academy transcription | `transcribe_academy_videos.py`, `transcribe_academy_hls.py` default to `data/cache/faster_whisper`, `data/raw/academy_media`, `data/raw/academy_hls`, `data/raw/youtube`, `data/processed`, `data/logs`, and queues | Defaults through `data_path`; tracked queue fallback may stay repo-local |
| Discovery | `discover_vturb_youtube_videos.py` defaults to `data/input/youtube_urls.csv` and `data/exports/vturb_channel_discovered_videos.csv` | Defaults through `data_path`, with explicit `--queue` override for repo-tracked queues |

Skills and docs with command examples to update after code changes:

- Process-skill retrieval files under `skills/msf-process-*/retrieval.md`.
- `skills/_templates/msf-process-skill/retrieval.md`.
- Transversal module retrieval examples.
- Older workflow skills: ingest, scale-batch, detect-assets, process-assets,
  retrieve, extract-insights.
- Current operational docs: `README.md`, `loops/episode-processing.md`,
  `loops/strategy-pack.md`, `docs/marketing-swipe-file-handoff.md`, and
  `docs/asset-acquisition-procedure.md`.

Historical audit docs can keep historical `data/...` paths; they should not be
mass-rewritten unless a current workflow depends on them.

## What Moves, Stays, Or Links

Move to external data root after code is prepared and owner approves execution:

- Ignored/local-only files under `data/raw/**`.
- Ignored/local-only files under `data/processed/**`.
- Ignored/local-only files under `data/exports/**`, including current local
  `curated_insights.json`, generated masters, S09 Ads/LowTicket/Quiz samples,
  keys, judged CSVs, encoding-fixed CSVs, and strategy packs.
- Ignored/local-only files under `data/input/assets/**`.
- Ignored/local-only files under `data/logs/**`.
- Ignored/local-only files under `data/cache/**`.
- Ignored/local-only `data/input/youtube_urls.csv` if present.

Stay versioned in the repo:

- All tracked files reported by `git ls-files data`.
- `.gitkeep` scaffold files.
- Lightweight tracked queues and examples:
  `data/input/academy_video_transcription_queue.csv`,
  `data/input/youtube_urls.example.csv`,
  `data/input/youtube_urls_academy_new.csv`.
- `data/processed/taxonomy_seed.json`.
- Previously tracked S09 offer/VSL audit artifacts under `data/exports/`.

Symlink/junction recommendation:

- Do not use a junction by default. The top-level `data/` tree is mixed:
  tracked repo files and ignored runtime artifacts coexist.
- A junction could hide tracked files, confuse Git, and reintroduce OneDrive
  sync behavior at the junction boundary.
- Only consider junctions as a temporary compatibility fallback for specific
  all-ignored child directories after code changes fail, and only with a
  separate owner approval.

## Migration Steps (Do Not Execute Yet)

Phase 1 - code preparation:

1. Add data-root helpers to `scripts/msf_common.py`.
2. Update script defaults from hardcoded `Path("data/...")` to `data_path(...)`
   or repo-tracked helper where appropriate.
3. Update current skill retrieval examples and current workflow docs to mention
   `MSF_DATA_DIR`.
4. Keep fallback behavior pointing to repo-local `data/` when `MSF_DATA_DIR` is
   unset.
5. Run current tests with `MSF_DATA_DIR` unset to prove no behavior regression.

Phase 2 - copy-only external seed:

1. Create `C:\MSF-data\Marketing_Swipe_File`.
2. Copy ignored/local-only data from repo `data/` into matching external
   subfolders. Use a manifest based on:
   `git ls-files --others --ignored --exclude-standard data`.
3. Do not delete source files yet.
4. Verify counts and byte sizes between source ignored/local-only manifest and
   external copy.
5. Set `MSF_DATA_DIR` for the validation shell only.

Phase 3 - validation before cleanup:

1. Run pipeline and skill validation with `MSF_DATA_DIR` set.
2. Confirm generated outputs are written to the external `exports/`, not repo
   `data/exports/`.
3. Confirm `git status` does not show deleted tracked data files.
4. Confirm no code path still requires repo-local ignored artifacts.

Phase 4 - OneDrive cleanup after green validation:

1. Rebuild the ignored/local-only manifest from the repo.
2. Remove only ignored/local-only files that are already verified in the
   external root.
3. Leave tracked files in place.
4. Re-run validation with `MSF_DATA_DIR` set.
5. Keep external root as the only runtime data location.

## Post-Move Validation Checklist

Run these with:

```powershell
$env:MSF_DATA_DIR = "C:\MSF-data\Marketing_Swipe_File"
```

Skill validation:

```powershell
.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-construcao-oferta --require-done
.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-copy-vsl --require-done
.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-copy-anuncios --require-done
.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-produto-low-ticket --require-done
.\.venv\Scripts\python.exe -B scripts\validate_process_skill.py skills\msf-process-quiz --require-done
.\.venv\Scripts\python.exe -B scripts\validate_transversal_modules.py skills\_modules\msf-transversal-copy
```

Retrieval and No Invention:

- Generate one strategy pack per approved skill using `--source curated` and
  each skill's `process_tags`.
- Confirm the pack source path resolves under `MSF_DATA_DIR\exports`.
- Re-run No Invention checks for the five approved skills against external
  `curated_insights.json`.
- Re-run the hardened mojibake guard against generated with-skill outputs and
  current `curated_insights.json`.

Pipeline smoke:

```powershell
.\.venv\Scripts\python.exe -B scripts\consolidate_exports.py --help
.\.venv\Scripts\python.exe -B scripts\run_episode_pipeline.py --help
.\.venv\Scripts\python.exe -B scripts\run_episode_batch.py --help
.\.venv\Scripts\python.exe -B scripts\transcribe_academy_videos.py --help
.\.venv\Scripts\python.exe -B scripts\transcribe_academy_hls.py --help
```

Data integrity:

- Compare external copy file count and byte count to the ignored/local-only
  manifest.
- Verify `data/raw/**`, `data/processed/**`, `data/exports/**`,
  `data/input/assets/**`, `data/logs/**`, and `data/cache/**` no longer contain
  ignored local-only payloads inside OneDrive after cleanup.
- Verify `git status --short --branch --untracked-files=all` shows no deleted
  tracked data files.
- Search for stale `transcript_fallback_needed.md` and confirm no new
  permission errors appear during validation.

## Rollback Plan

Before cleanup:

- Unset `MSF_DATA_DIR` and the repo falls back to current `data/`.
- Remove or ignore the external copy if needed.

After cleanup:

1. Stop any running pipeline.
2. Unset `MSF_DATA_DIR`.
3. Copy the external data tree back into repo `data/` using the saved manifest.
4. Verify tracked files with `git status` and `git ls-files data`.
5. Re-run the same validation commands with fallback repo-local data.
6. Only after validation, decide whether to remove the external copy.

Tracked-file safety:

- Never delete files returned by `git ls-files data`.
- Cleanup should target only paths returned by
  `git ls-files --others --ignored --exclude-standard data` and verified as
  copied.

## Gitignore Impact

Current `.gitignore` already ignores the right runtime roots and re-includes
lightweight scaffolding:

- Ignored: `data/raw/**`, `data/processed/**`, `data/exports/**`,
  `data/logs/**`, `data/cache/**`, `data/input/assets/**`,
  `data/input/youtube_urls.csv`.
- Re-included: `.gitkeep` scaffolding, `taxonomy_seed.json`, and lightweight
  tracked queues/examples.

Proposed `.gitignore` changes for the execution phase:

- No required broad ignore change.
- Optional: add a local-only config filename if the implementation introduces
  one, for example `.msf-data.local.json`.
- Optional: document `MSF_DATA_DIR` in `.env.example` or setup docs.

Do not de-track the already committed S09 offer/VSL artifacts in this R03
migration unless the owner explicitly approves a separate Git-history/data
policy change.

## Open Decisions For Owner

1. Confirm primary destination:
   `C:\MSF-data\Marketing_Swipe_File` vs `%LOCALAPPDATA%\MSF-data\Marketing_Swipe_File`.
2. Confirm whether `data/cache/**` should be moved or allowed to regenerate.
   Recommendation: move initially, then prune later if needed.
3. Confirm taxonomy strategy:
   keep `data/processed/taxonomy_seed.json` as repo-tracked canonical, or copy
   it into the external root and add an equality check.
4. Confirm whether any legacy junction is desired. Recommendation: no junction
   unless validation finds an unavoidable legacy path.

## Non-Goals

- Do not run MSF-R14 backfill in this migration.
- Do not start agents.
- Do not de-track committed data artifacts.
- Do not change historical audit docs just to rewrite old paths.
- Do not move files until the owner approves the execution plan.
