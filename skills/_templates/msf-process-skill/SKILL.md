---
name: __SKILL_NAME__
description: Use this Marketing Swipe File process skill to create or critique __DISPLAY_NAME__ outputs from curated insights. Trigger when the task needs process-specific marketing execution, retrieval by process_tags, evidence-backed playbook guidance, citation of insight_id, and validation against the process rubric.
---

# __DISPLAY_NAME__

## Workflow

1. Read `retrieval.md` and retrieve only curated insights matching:
   __PROCESS_TAGS_INLINE__.
2. Build or update the internal playbook from `curated_insights`, citing every
   non-obvious claim as `[insight:<insight_id>]`.
3. Mark generic practices as `[generic-practice]`; do not present them as
   learned from the base.
4. Draft the final output with the template in `templates/`.
5. Evaluate the output with `rubric.md` and the MSF-R09 evaluator.
6. Do not treat this skill as production-ready until the checklist in
   `skill.contract.json` is `pass` for all required checks.

## Transversal Modules

Before writing a process-specific playbook, check whether the skill needs
shared copy modules from `skills/_modules/msf-transversal-copy/`.

- Import `transversal:mecanismo-big-idea` when the output needs belief,
  mechanism, promise logic, or a causal bridge.
- Import `transversal:prova-depoimentos` when the output needs proof,
  testimonials, expert authority, credibility, or claim-risk control.
- Reference the module path instead of copying shared module playbook content
  into this skill.
- When importing both transversal modules, count evidence by unique
  `insight_id`; known overlap ids `zoChfFHnlOQ-v2-0008` and
  `mCaFyZpXJdE-v2-0011` count once, not once per module.
- Keep process-specific logic such as quiz flow, low-ticket offer mechanics,
  and CTA sequencing inside this skill. Transversal modules only support
  principle-level claims.

## Writing Policy

- Internal playbook, retrieval notes, contract fields, and editorial summaries
  use ASCII via NFKD transliteration when representing Portuguese without
  accents.
- Evidence quotes stay verbatim UTF-8. Never normalize or strip accents from
  quotes.
- Final outputs, examples, VSLs, ads, quizzes, and user-facing templates use
  full pt-BR accents and correct spelling.

## No Invention

- Every non-obvious process rule must cite `[insight:<insight_id>]`.
- If no curated insight supports a claim, mark it `[generic-practice]` or
  remove it.
- Do not use raw/v1 insights as source material for this skill unless the owner
  explicitly reopens curation.

## Required Files

- `skill.contract.json`
- `retrieval.md`
- `rubric.md`
- `templates/output-template.md`
- `examples/briefing.md`
- `examples/output-approved.md`
