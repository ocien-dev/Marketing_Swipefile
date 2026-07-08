---
name: msf-process-produto-low-ticket
description: Use this Marketing Swipe File process skill to create, critique, or improve low-ticket entry products, front-end offers, paid challenges, mini-courses, templates, kits, workshops, and product ladders from curated insights. Trigger when the task asks for an entry transformation, consumable low-ticket scope, price-value fit, backend ascension bridge, or an audit of whether a low-ticket product is ready for a blind baseline test.
---

# Produto Low Ticket

Status: approved on 2026-07-08. MSF-S09 low-ticket passed: with-skill won
4/4 pairs, 31/32 criteria, and 12/12 commercial-core cells with no pending
encoding or No Invention defect.

## Workflow

1. Read `retrieval.md` and retrieve curated insights matching
   `process-produto-low-ticket`, plus imported transversal module tags when
   they support the briefing.
2. Import `transversal:mecanismo-big-idea` and
   `transversal:prova-depoimentos` by reference from
   `skills/_modules/msf-transversal-copy/`; do not copy those modules into
   this playbook.
3. Build the low-ticket product from evidence-backed decisions: entry
   transformation, avatar promise, scope, format, price-value fit, mechanism,
   proof or claim control, backend bridge, and test plan.
4. Cite every non-obvious internal claim as `[insight:<insight_id>]`; mark
   unsupported but standard product craft as `[generic-practice]`.
5. Draft the final product plan using `templates/output-template.md`.
6. Evaluate major revisions with `rubric.md` and the MSF-R09/S09 protocol
   before treating changed playbook behavior as approved.

## Imported Modules

- Import `transversal:mecanismo-big-idea` when the product needs a causal
  bridge, one belief, named mechanism, or reason the entry transformation can
  happen with a smaller scope.
- Import `transversal:prova-depoimentos` when the product needs proof,
  credibility, testimonial logic, expert authority, or claim-risk control.
- Deduplicate evidence by unique `insight_id` when both modules are imported.
  Known overlap ids `zoChfFHnlOQ-v2-0008` and `mCaFyZpXJdE-v2-0011` count once.
- Keep low-ticket-specific logic here: entry transformation, delivery format,
  scope, consumability, price-value fit, checkout promise, backend ascension,
  product ladder, and validation test. Transversal claims stay at principle
  level.

## Low Ticket Product Playbook

Use this sequence unless the briefing gives a stronger constraint:

1. Treat low ticket as an acquisition architecture first, not as a fixed
   product category. The front product should buy qualified customers and feed
   later monetization instead of trying to capture all profit alone.
   [insight:mCaFyZpXJdE-v2-0010]
2. Use low ticket when the commercial job is to test more offer hypotheses with
   controlled downside. The point is not to make the first attempt sacred; it
   is to learn faster with less cash risk. [insight:mCaFyZpXJdE-v2-0006]
3. Define one entry transformation that is concrete enough to be consumed
   quickly. A fast front can be cut from a larger product when that slice solves
   a specific problem on its own. [insight:L7u7r6rOl68-v2-0006]
4. Make the product feel easier to start than the larger promise. Low-ticket
   conversion improves when the buyer sees a simpler path with less perceived
   effort. [insight:TOW0sWhPaZw-v2-0007]
5. Remove excess argument and delivery weight. Low ticket usually needs a few
   strong reasons and a compact mechanism, not the density of a long VSL.
   [insight:TOW0sWhPaZw-v2-0006]
6. Borrow VSL principles for mechanism and belief, but adapt the density and
   format to the lower ticket. Transfer the principle; do not copy the long
   asset shape literally. [insight:TOW0sWhPaZw-v2-0005]
7. Choose the format from the consumption constraint: challenge for behavior,
   mini-course for sequence, template or kit for execution shortcut, workshop
   for focused diagnosis, and quiz-led path when self-recognition is part of
   the sale. [insight:TOW0sWhPaZw-v2-0009] [generic-practice]
8. Price by the combined effect of conversion and AOV, not AOV alone. A higher
   ticket with weaker conversion can lose to a cheaper front that converts and
   ascends better. [insight:mCaFyZpXJdE-v2-0024]
9. Define a minimum validation budget before declaring a product valid or dead.
   A single cheap sale is not enough; the test should observe efficiency of the
   creative-offer-product system. [insight:mCaFyZpXJdE-v2-0021]
10. Build the backend bridge before celebrating front-end volume. Margin in
    low ticket often comes from backend, CRM, recurrence, upsell, or cross-sell
    working the buyer base. [insight:mCaFyZpXJdE-v2-0007]
11. Put the front inside a product ladder. The stronger pattern is front,
    backend, and high-end or deeper offer path, not an isolated cheap product.
    [insight:L7u7r6rOl68-v2-0004] [insight:TOW0sWhPaZw-v2-0017]
12. If front margin does not close, diagnose backend structure before blaming
    the whole low-ticket model. A structured backend can compensate for tight
    front economics. [insight:JF2oC44lBG8-v2-0019]
13. Use proof carefully. Existing audience trust or social proof can support a
    monetizable product, but the promise must fit what the proof actually
    supports. [insight:aSFAve1klsc-v2-0007]
14. A quiz can reduce early dependence on a visible expert only when the quiz
    helps the lead recognize the problem and the claim stays appropriately
    narrow. Treat this as higher risk, not a universal shortcut.
    [insight:mCaFyZpXJdE-v2-0005]
15. Low-ticket scale depends on the creative system after minimum viable funnel
    structure exists. The product plan should state the first creative or hook
    angles to test, not only the module list. [insight:mCaFyZpXJdE-v2-0022]
    [insight:TOW0sWhPaZw-v2-0013]
16. Keep human strategic criteria ahead of AI execution. AI can draft product
    blocks after the human defines transformation, scope, and review criteria.
    [insight:qohJceyapS0-v2-0012]

## Output Requirements

Every low-ticket product output should include:

- Briefing summary: market, avatar, awareness level, current offer assets,
  desired backend, constraints, and risk.
- Entry transformation: the small concrete change the buyer can reasonably get
  from the front product.
- Product shape: format, modules or steps, delivery length, assets, support
  level, consumption path, and what is deliberately out of scope.
- Price-value logic: price band, value anchor, why the scope feels worth paying
  for, and what would make the product feel too heavy or too thin.
- Mechanism and belief: why the entry transformation can happen with this
  smaller product.
- Proof and claim control: what proof can be used, what cannot be promised,
  and how to avoid overclaiming.
- Backend ascension bridge: what the front qualifies the buyer for next and
  how the next offer should naturally continue the transformation.
- Test plan: first traffic or launch test, minimum decision signal, metrics,
  and next iteration if the first version underperforms.
- Citation map: each non-obvious rule or strategic choice mapped to
  `insight_id`.

## No Invention

- Use only `curated_insights` as source material unless the owner explicitly
  reopens curation.
- Do not count the same `insight_id` twice when it appears in both imported
  modules.
- Do not let a transversal module decide low-ticket-specific transformation,
  scope, format, price-value fit, consumability, backend bridge, or validation
  plan.
- If retrieved evidence does not support a claim, mark it `[generic-practice]`,
  narrow it, or remove it.

## Writing Policy

- Internal playbook, retrieval notes, contract fields, and editorial summaries
  use ASCII via NFKD transliteration when representing Portuguese without
  accents.
- Evidence quotes stay verbatim UTF-8. Never normalize or strip accents from
  quotes.
- Final outputs, examples, and templates use full pt-BR accents and correct
  spelling.
