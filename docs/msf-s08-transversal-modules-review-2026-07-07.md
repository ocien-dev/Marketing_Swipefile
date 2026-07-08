# MSF-S08 Transversal Modules Review - 2026-07-07

Status: `approved`

## Scope

MSF-S08 creates two shared copy modules for the first process-skill wave:

- `transversal:mecanismo-big-idea`
- `transversal:prova-depoimentos`

They are not standalone skills. They live in
`skills/_modules/msf-transversal-copy/` and should be imported by S03-S07 by
reference, without duplicating shared playbook content inside each skill.

## Source Coverage

Current local `curated_insights` coverage:

| module | process_tag | curated items |
|---|---|---:|
| mecanismo-big-idea | `process-mecanismo-big-idea` | 30 |
| prova-depoimentos | `process-prova-depoimentos` | 33 |

## Files For Audit

- `skills/_modules/msf-transversal-copy/module.contract.json`
- `skills/_modules/msf-transversal-copy/module-index.md`
- `skills/_modules/msf-transversal-copy/retrieval.md`
- `skills/_modules/msf-transversal-copy/modules/mecanismo-big-idea.md`
- `skills/_modules/msf-transversal-copy/modules/prova-depoimentos.md`

## Import Matrix

Both modules are declared consumable by:

- `msf-process-construcao-oferta`
- `msf-process-copy-vsl`
- `msf-process-copy-anuncios`
- `msf-process-produto-low-ticket`
- `msf-process-quiz`

This satisfies the S08 requirement that each module can be consumed by at
least two first-wave skills.

## Audit Questions

1. Does `mecanismo-big-idea` draw the right boundary between causal mechanism,
   one belief, promise, and next action?
2. Does `prova-depoimentos` draw the right boundary between proof, expert
   authority, story, validation, and claim-risk control?
3. Should any playbook claim be removed, narrowed, or moved into a future
   process-specific skill instead of staying transversal?
4. Should either module be approved for S03-S07 inheritance, or remain blocked
   for another pass?

## Validation

- `scripts/validate_transversal_modules.py` validates contract shape,
  required files, active process tags, consumer count, citations, placeholders,
  and internal ASCII policy.
- `tests/test_transversal_modules_contract.py` validates the real module
  folder and confirms the consumer-count rule fails when a module has fewer
  than two consuming skills.
- Smoke retrieval generated 8-item packs for each module tag:
  - `process-mecanismo-big-idea`: all 8 selected insights contained the tag.
  - `process-prova-depoimentos`: all 8 selected insights contained the tag.
- Existing S01/S02 tests still pass:
  - `tests/test_process_skill_contract.py`
  - `tests/test_process_tag_retrieval.py`
  - `tests/test_strategy_pack_diversity.py`

## Decision

Owner audit approved MSF-S08 on 2026-07-07.

- All 17 citations resolve to real `curated_insights` and carry the declared
  process tag.
- No Invention passes for the audited claims.
- The mechanism/proof boundaries are approved.
- S04 is released as the next process skill. S03/S05-S07 remain after S04
  validates the skill -> retrieval -> rubric -> blind-test pipeline.

Inherited restrictions for S04+:

- Deduplicate evidence counts by `insight_id` when importing both transversal
  modules. Known overlap ids `zoChfFHnlOQ-v2-0008` and
  `mCaFyZpXJdE-v2-0011` count once.
- Process-specific logic such as quiz, low-ticket, and CTA decisions belongs
  in the process skill. Transversal claims stay at principle level.
