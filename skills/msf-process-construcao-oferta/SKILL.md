---
name: msf-process-construcao-oferta
description: Use this Marketing Swipe File process skill to build, critique, or improve offer-construction outputs from curated insights. Trigger when the task asks for an offer, offer stack, promise, mechanism, pricing/anchoring logic, bonuses, guarantee, value ladder, backend path, or an audit of whether an offer is ready for validation.
---

# Construcao De Oferta

Status: approved by MSF-S09 on 2026-07-08.

## Workflow

1. Read `retrieval.md` and retrieve curated insights matching
   `process-construcao-oferta`, plus the imported transversal module tags when
   they support the briefing.
2. Import `transversal:mecanismo-big-idea` and
   `transversal:prova-depoimentos` by reference from
   `skills/_modules/msf-transversal-copy/`; do not copy those modules into
   this playbook.
3. Build the offer from evidence-backed decisions: market signal, promise,
   mechanism, stack, price/anchor, bonuses, guarantee, proof, CTA, and backend.
4. Cite every non-obvious internal claim as `[insight:<insight_id>]`; mark
   unsupported but standard craft guidance as `[generic-practice]`.
5. Draft the final offer using `templates/output-template.md`.
6. Evaluate future major revisions with `rubric.md` and the MSF-R09/S09
   protocol before treating changed playbook behavior as approved.

## Imported Modules

- Import `transversal:mecanismo-big-idea` when the offer needs a causal bridge
  from current pain to desired future, a belief shift, or promise logic.
- Import `transversal:prova-depoimentos` when the offer needs proof, story,
  expert authority, credibility, or claim-risk control.
- Deduplicate evidence by unique `insight_id` when both modules are imported.
  Known overlap ids `zoChfFHnlOQ-v2-0008` and `mCaFyZpXJdE-v2-0011` count once.
- Keep offer-specific logic here: pricing, anchoring, stack, bonuses,
  guarantee, value ladder, order path, backend, and CTA sequencing.
  Transversal claims stay at principle level.

## Offer Construction Playbook

Use this sequence unless the briefing gives a stronger constraint:

1. Start with one market signal to validate. A dry test can isolate the offer
   name or promise before the full offer is built; keep other variables stable
   so the signal is readable. [insight:mCaFyZpXJdE-v2-0001]
2. Treat low-ticket or front-end offers as controlled experimentation when the
   economics allow multiple misses without killing learning.
   [insight:mCaFyZpXJdE-v2-0006]
3. Do not overbuild persuasion before signal. A mini VSL or heavier proof layer
   belongs after the offer is moving from discovery into real selling.
   [insight:mCaFyZpXJdE-v2-0014]
4. If speed matters, carve the front offer from a proven core product instead
   of inventing a disconnected deliverable. [insight:L7u7r6rOl68-v2-0006]
5. Make the promise fit the product that can actually be delivered and sold;
   product shape should follow the promise the sales asset can prove.
   [insight:qj04cUeaRAw-v2-0010]
6. Build the mechanism as the reason the promise is possible, not as a clever
   label. It must bridge current state to desired future and stay logical for
   the market. [insight:mCaFyZpXJdE-v2-0003]
   [insight:L7u7r6rOl68-v2-0007]
7. Sequence true, easy-to-accept logic before the ask so the offer feels like
   the next step instead of a sudden pitch. [insight:L7u7r6rOl68-v2-0009]
8. Prefer offer stacks that reduce buyer effort. Simplicity can be a conversion
   lever when it makes the path to the result feel easier.
   [insight:TOW0sWhPaZw-v2-0007]
9. Use origin story or expert proof only when it explains a concrete commercial
   shift, delivery edge, or buyer belief gap. [insight:JF2oC44lBG8-v2-0003]
   [insight:zoChfFHnlOQ-v2-0008]
10. After an offer is validated, decide whether the bottleneck is the offer or
    distribution. A validated offer can sometimes scale through fresh creative
    batches before changing the funnel or core promise. [insight:BbhJn8NXRso-v2-0003]
    [insight:wHdyTM-nVqg-v2-0002]
11. Do not stop at the first sale. A validated front offer needs backend,
    base monetization, or a next product path so acquisition does not become
    isolated campaign revenue. [insight:TOW0sWhPaZw-v2-0018]
    [insight:aSFAve1klsc-v2-0008] [insight:8WEvN5T7J0U-v2-0002]
12. If the offer uses a quiz, advertorial, or other pre-step, sell the value
    of that step before selling the final offer. [insight:TOW0sWhPaZw-v2-0001]

## Output Requirements

Every offer output should include:

- Offer hypothesis: the buyer, pain, desired future, and market signal.
- Core promise: specific result, time/context if known, and scope limits.
- Mechanism: why the promise can happen now.
- Stack: core deliverable, implementation aids, bonuses, and what each part
  does for the buyer.
- Price and anchor: price logic, comparison anchor, and risk of under/over
  promising.
- Proof plan: proof type, placement, and claim that each proof supports.
- Guarantee or risk reversal: only if coherent with delivery and risk.
- CTA/order path: next action, checkout/application path, and immediate reason
  to act.
- Backend or next-step path: how the front offer can lead to retention,
  ascension, subscription, or base monetization.
- Test plan: first variables to test without destroying learning.

## No Invention

- Use only `curated_insights` as source material unless the owner explicitly
  reopens curation.
- Do not count the same `insight_id` twice when it appears in both imported
  modules.
- Do not let a transversal module decide offer-specific pricing, bonuses,
  guarantee, CTA, or value ladder.
- If the retrieved evidence does not support a claim, mark it
  `[generic-practice]`, narrow it, or remove it.

## Writing Policy

- Internal playbook, retrieval notes, contract fields, and editorial summaries
  use ASCII via NFKD transliteration when representing Portuguese without
  accents.
- Evidence quotes stay verbatim UTF-8. Never normalize or strip accents from
  quotes.
- Final outputs, examples, and templates use full pt-BR accents and correct
  spelling.
