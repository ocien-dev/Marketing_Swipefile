# MSF-R03 Phase 4 Cleanup Report

Date: 2026-07-08

Status: `done`

Phase 4 cleanup/delete was executed after owner approval. No junction was
created. Backfill MSF-R14 was not started.

## Pre-Delete Coverage Check

Manifest command:

```powershell
git ls-files --others --ignored --exclude-standard data
```

Coverage result:

| Metric | Value |
|---|---:|
| Manifest files | 9,713 |
| Regular files | 9,709 |
| Symlink files | 4 |
| Missing in external | 0 |
| Mismatch | 0 |
| Unsafe paths | 0 |
| Tracked hits in manifest | 0 |

Regular files were checked by source-vs-external byte-size. The 4 symlink files
were cache-only Faster Whisper snapshot links; they were verified by resolved
payload byte-size and SHA256 hash against the external materialized files.

External root:

```text
C:\MSF-data\Marketing_Swipe_File
```

## Delete

Deleted only files from the ignored/local-only manifest under repo `data/`.
No recursive directory delete was used.

| Path | Deleted files |
|---|---:|
| `cache` | 700 |
| `exports` | 109 |
| `input` | 47 |
| `logs` | 149 |
| `processed` | 7,849 |
| `raw` | 859 |
| Total | 9,713 |

One initial non-elevated deletion attempt hit a OneDrive permission denial on
`data\cache\academy_lessons_for_media_probe.json`. The manifest was rechecked
after that failed attempt and still contained all 9,713 files with full
external coverage, then the same manifest-scoped deletion was rerun with
permission escalation and completed.

## Persistent Data Root

Persisted user environment variable:

```powershell
setx MSF_DATA_DIR "C:\MSF-data\Marketing_Swipe_File"
```

Confirmed:

| Check | Result |
|---|---|
| User env value | `C:\MSF-data\Marketing_Swipe_File` |
| New process with fresh environment | `data_root=C:\MSF-data\Marketing_Swipe_File` |
| Current host process with env unset | falls back to repo `data/` as expected |

## Post-Delete Validation

Validation shell used the persisted user value for `MSF_DATA_DIR`.

| Check | Result |
|---|---|
| 5 process skills with `--require-done` | PASS |
| `validate_transversal_modules.py skills\_modules\msf-transversal-copy` | PASS |
| 5 strategy packs generated | PASS |
| Pack source path | `C:\MSF-data\Marketing_Swipe_File\exports\curated_insights.json` |
| No Invention against external curated | PASS |
| Mojibake guard on post-delete packs | PASS, 0 findings |
| Repo ignored payload under `data/` | 0 files |
| Repo tracked data deletions | 0 |
| `git diff --check` | PASS, LF/CRLF warnings only |

Post-delete strategy packs generated:

| Pack | Results |
|---|---:|
| `offer` | 5 |
| `vsl` | 5 |
| `ads` | 5 |
| `lowticket` | 5 |
| `quiz` | 5 |

No Invention summary:

| Skill | Unique citations | Missing | Wrong declared tag |
|---|---:|---:|---:|
| `msf-process-construcao-oferta` | 17 | 0 | 0 |
| `msf-process-copy-vsl` | 23 | 0 | 0 |
| `msf-process-copy-anuncios` | 18 | 0 | 0 |
| `msf-process-produto-low-ticket` | 18 | 0 | 0 |
| `msf-process-quiz` | 17 | 0 | 0 |

Repo `data/` state:

| Metric | Value |
|---|---:|
| Tracked data files | 31 |
| Actual repo data files | 31 |
| Extra untracked/ignored payload files | 0 |
| Missing tracked data files | 0 |

## Decision State

MSF-R03 is complete. The next milestone is MSF-R14 backfill of the remaining
chunks using Route B/Codex-first and `MSF_DATA_DIR`, but it remains not started
until the owner explicitly starts it.
