# MSF-R03 Phase 1-3 Execution Report

Date: 2026-07-08

Status: `phase_1_3_complete_phase_4_done_separately`

Phase 4 cleanup/delete was not executed during this phase 1-3 pass. It was
executed later after owner approval and is documented in
`docs/msf-r03-phase-4-report-2026-07-08.md`.

## Owner Decisions Applied

- External runtime root: `C:\MSF-data\Marketing_Swipe_File`.
- Fallback: repo-local `data/` when `MSF_DATA_DIR` is unset.
- Cache: copied/moved candidate, low priority, regenerable.
- `data/processed/taxonomy_seed.json`: stays repo-tracked canonical; not copied
  to the external root.
- Junction: none.

## Phase 1 - Code Preparation

Added data-root helpers in `scripts/msf_common.py`:

- `repo_root()`
- `repo_data_root()`
- `data_root()`
- `data_path(*parts)`
- `repo_data_path(*parts)`

Runtime defaults that read/write local-only data now use `data_path(...)`.
Taxonomy defaults that must use the repo-tracked seed now use
`repo_data_path("processed", "taxonomy_seed.json")`.

Updated current operational docs and skill retrieval examples to mention
`MSF_DATA_DIR` and avoid hardcoded output paths to `data/exports`.

## Phase 1 Validation With `MSF_DATA_DIR` Unset

Fallback root resolved to:

```text
C:\Users\luish\OneDrive\Code\Marketing_Swipe_File\data
```

Validation results:

| Check | Result |
|---|---|
| 5 process skills with `--require-done` | PASS |
| `validate_transversal_modules.py skills\_modules\msf-transversal-copy` | PASS |
| Direct test entrypoints | PASS |
| Script in-memory compile | PASS, 38 scripts |
| Strategy-pack smoke read | PASS, source was repo `data\exports\curated_insights.json` |

Note: `.venv` did not have `pytest` installed, so tests were run through their
direct `__main__` entrypoints instead of installing dependencies during R03.

## Phase 2 - Copy Only

Disk guard:

| Drive | Available |
|---|---:|
| `C:\` | 174.67 GB |

Destination created:

```text
C:\MSF-data\Marketing_Swipe_File
```

Manifest command:

```powershell
git ls-files --others --ignored --exclude-standard data
```

Copy summary:

| Metric | Value |
|---|---:|
| Manifest files copied | 9,713 |
| Source logical bytes | 6,723,139,609 |
| Source size | 6,411.69 MB |
| External physical bytes by manifest path | 6,801,343,228 |
| Source deletions | 0 |
| External `processed\taxonomy_seed.json` | absent |

Per top-level verification:

| Path | Files | Source MB | External MB | Notes |
|---|---:|---:|---:|---|
| `cache` | 700 | 157.89 | 232.48 | 4 symlink snapshots materialized as real files |
| `exports` | 109 | 11.30 | 11.30 | matched |
| `input` | 47 | 100.52 | 100.52 | matched |
| `logs` | 149 | 16.57 | 16.57 | matched |
| `processed` | 7,849 | 437.48 | 437.48 | matched |
| `raw` | 859 | 5,687.92 | 5,687.92 | matched |

Cache exception:

`Copy-Item` materialized 4 HuggingFace/Faster Whisper cache symlinks under
`cache/faster_whisper/.../snapshots/...` as real files in the external root:

- `config.json`
- `model.bin`
- `tokenizer.json`
- `vocabulary.txt`

This is restricted to cache, which the owner approved as low priority and
regenerable. No non-cache manifest path had a byte-size mismatch.

Critical export SHA256 checks:

| File | SHA256 prefix | Match |
|---|---|---|
| `exports\curated_insights.json` | `BA20BC81C41B` | yes |
| `exports\insights_master.json` | `2B0639F7B957` | yes |
| `exports\insights_master.csv` | `E6C12394CFB9` | yes |
| `exports\insights_v2_master.json` | `58597D7296BE` | yes |
| `exports\insights_v2_master.csv` | `4202FDE117FB` | yes |
| `exports\episodes_master.json` | `88960F820334` | yes |
| `exports\assets_master.json` | `66402D487C86` | yes |
| `exports\referenced_assets_master.json` | `77B1CCBCE97D` | yes |
| `exports\acquisition_tasks_master.csv` | `D51A2984CB24` | yes |
| `exports\insights_v2_status.json` | `BD6C597DBCF3` | yes |
| `exports\insights_v2_episode_status.csv` | `B730B0A4888C` | yes |
| `exports\insights_v2_title_distribution.csv` | `54385BEE57F7` | yes |

## Phase 3 - Validation With `MSF_DATA_DIR` Set

Validation shell:

```powershell
$env:MSF_DATA_DIR = "C:\MSF-data\Marketing_Swipe_File"
```

Validators:

| Check | Result |
|---|---|
| 5 process skills with `--require-done` | PASS |
| `validate_transversal_modules.py skills\_modules\msf-transversal-copy` | PASS |

Generated one real strategy pack per approved first-wave skill:

| Pack | Source path | Results |
|---|---|---:|
| `offer` | `C:\MSF-data\Marketing_Swipe_File\exports\curated_insights.json` | 5 |
| `vsl` | `C:\MSF-data\Marketing_Swipe_File\exports\curated_insights.json` | 5 |
| `ads` | `C:\MSF-data\Marketing_Swipe_File\exports\curated_insights.json` | 5 |
| `lowticket` | `C:\MSF-data\Marketing_Swipe_File\exports\curated_insights.json` | 5 |
| `quiz` | `C:\MSF-data\Marketing_Swipe_File\exports\curated_insights.json` | 5 |

No Invention against external curated, allowing any `process_tag` declared in
each skill contract:

| Skill | Unique citations | Missing | Wrong declared tag |
|---|---:|---:|---:|
| `msf-process-construcao-oferta` | 17 | 0 | 0 |
| `msf-process-copy-vsl` | 23 | 0 | 0 |
| `msf-process-copy-anuncios` | 18 | 0 | 0 |
| `msf-process-produto-low-ticket` | 18 | 0 | 0 |
| `msf-process-quiz` | 17 | 0 | 0 |

Encoding guard:

- Hardened mojibake guard on the 10 newly generated R03 smoke pack files:
  PASS, 0 findings.
- Broad audit over the copied external historical base returned 293 findings.
  These are pre-existing copied data issues or false positives in historical
  CSV/MD exports, including `watch?v=` URL fragments and known old mojibake
  lines. They are not introduced by R03 and were not in the newly generated
  smoke packs.

Split-root verification:

```text
data_root=C:\MSF-data\Marketing_Swipe_File
repo_data_root=C:\Users\luish\OneDrive\Code\Marketing_Swipe_File\data
curated_default=C:\MSF-data\Marketing_Swipe_File\exports\curated_insights.json
taxonomy_validate_process_skill=C:\Users\luish\OneDrive\Code\Marketing_Swipe_File\data\processed\taxonomy_seed.json
same_parent=False
```

## Git State

`git ls-files --deleted` returned no files.

`git diff --check` passed. It emitted only normal Windows line-ending warnings.

Non-ASCII scan:

- Added-line scan for this change: PASS, 0 new non-ASCII characters.
- Whole-file scan over changed files finds pre-existing non-ASCII literals in
  `scripts/collect_youtube_transcript_from_playwright_snapshot.py` and
  `scripts/extract_description_insights.py`; these were not introduced by the
  R03 edits.

Expected working tree state:

- Code/docs/skill examples modified for R03 path resolution.
- `docs/msf-r03-migration-plan.md` remains untracked from the planning phase.
- This report is new.
- No tracked data file was deleted.

## Stop Point

STOP before Phase 4:

- Do not delete repo-local ignored files yet.
- Do not create junctions.
- Do not commit yet.
- Await owner audit before cleanup/delete.
