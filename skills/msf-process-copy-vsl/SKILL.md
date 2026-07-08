---
name: msf-process-copy-vsl
description: Use this Marketing Swipe File process skill to create, critique, or improve VSL copy from curated insights. Trigger when the task asks for a VSL, mini VSL, video sales letter, lead, one belief, mechanism, proof sequence, objection handling, offer bridge, CTA, or an audit of whether a VSL is ready for a blind baseline test.
---

# Copy VSL

Status: approved on 2026-07-08 after MSF-S09 VSL. Commercial PASS was
reconfirmed externally after the encoding correction: the fixed sample changed
only `cansa?o` to `cansaco`, preserving the blind judgment.

## Workflow

1. Read `retrieval.md` and retrieve curated insights matching
   `process-copy-vsl`, plus imported transversal module tags when they support
   the briefing.
2. Import `transversal:mecanismo-big-idea` and
   `transversal:prova-depoimentos` by reference from
   `skills/_modules/msf-transversal-copy/`; do not copy those modules into
   this playbook.
3. Build the VSL from evidence-backed decisions: asset job, lead, belief gap,
   one belief, mechanism, proof, objections, offer bridge, CTA, and test plan.
4. Cite every non-obvious internal claim as `[insight:<insight_id>]`; mark
   unsupported but standard craft guidance as `[generic-practice]`.
5. Draft the final VSL using `templates/output-template.md`.
6. Evaluate major revisions with `rubric.md` and the MSF-R09/S09 protocol
   before treating changed playbook behavior as approved.

## Imported Modules

- Import `transversal:mecanismo-big-idea` when the VSL needs a causal bridge,
  one belief, mechanism, promise logic, or a reason the offer can work now.
- Import `transversal:prova-depoimentos` when the VSL needs proof, expert
  authority, testimonial logic, credibility, or claim-risk control.
- Deduplicate evidence by unique `insight_id` when both modules are imported.
  Known overlap ids `zoChfFHnlOQ-v2-0008` and `mCaFyZpXJdE-v2-0011` count once.
- Keep VSL-specific logic here: lead, video structure, story placement,
  mechanism sequencing, proof placement, objection handling, offer bridge,
  CTA, retention tests, and whether the asset is a long VSL, mini VSL, or
  post-quiz bridge. Transversal claims stay at principle level.

## VSL Playbook

Use this sequence unless the briefing gives a stronger constraint:

1. Define the job of the asset before writing: full cold-traffic VSL, mini VSL
   after a quiz, bridge after a lead magnet, or sales video inside a broader
   funnel. A VSL is useful when selling can become repeatable acquisition
   instead of only launch timing. [insight:zoChfFHnlOQ-v2-0002]
   [insight:aSFAve1klsc-v2-0003]
2. Start with the avatar's belief gap, not with a script template. Reading the
   person supplies the arguments for the mechanism, story, and objections.
   [insight:aSFAve1klsc-v2-0009]
3. Choose one belief that makes the offer feel like the logical next step. It
   should connect the promise, mechanism, and central objection instead of
   opening several unrelated theses. [insight:cL3FuW8bAMA-v2-0005]
   [insight:cL3FuW8bAMA-v2-0006]
4. If the VSL follows a quiz or diagnostic, use the prior questions to raise
   awareness and make the mini VSL an anchoring point for the result. The VSL
   can then prove the "how" with less setup. [insight:TOW0sWhPaZw-v2-0003]
   [insight:TOW0sWhPaZw-v2-0012]
5. Do not jump from mechanism straight to offer. Build the product logic and
   the reason the delivery exists before price or CTA, or the pitch feels
   abrupt. [insight:TOW0sWhPaZw-v2-0011]
   [insight:cL3FuW8bAMA-v2-0013]
6. Sequence true, easy-to-accept arguments before the pitch so the offer feels
   consistent with what the viewer already accepted. [insight:L7u7r6rOl68-v2-0009]
7. Use expert story as proof only when it explains the method, the discovery,
   or the transformation behind the product. Expert history should create
   belief, not become generic biography. [insight:zoChfFHnlOQ-v2-0008]
   [insight:cL3FuW8bAMA-v2-0009]
8. Put proof next to the claim it supports. Authority, testimonial, and expert
   evidence should increase belief in the one belief or mechanism, not merely
   decorate the script. [insight:qohJceyapS0-v2-0015]
   [insight:zoChfFHnlOQ-v2-0014]
9. Match length and argument density to ticket and awareness. Low-ticket or
   warmed-up flows often need fewer arguments; long funnels only work when each
   step preserves engagement. [insight:TOW0sWhPaZw-v2-0006]
   [insight:mCaFyZpXJdE-v2-0015]
10. Make the mechanism tangible through the product and delivery. If the viewer
    understands the idea but cannot see what they receive, the pitch can hold
    attention while checkout conversion still falls. [insight:qohJceyapS0-v2-0010]
11. Treat the lead, headline, and creative-facing blocks as high-priority test
    surfaces. They saturate faster and receive more traffic than deeper story
    blocks; do not rewrite the whole VSL before testing exposed entrances.
    [insight:qohJceyapS0-v2-0013]
12. Watch the mini VSL as a potential drop-off point inside quiz or diagnostic
    funnels. Because video is a friction step, retention and transition into
    the offer need explicit testing. [insight:TOW0sWhPaZw-v2-0015]
13. Keep the classic sales structure visible: story, problem, solution, and
    offer still matter across formats, but the VSL must adapt the story and
    thesis to the specific project. [insight:aSFAve1klsc-v2-0002]
    [insight:cL3FuW8bAMA-v2-0010]
14. Build the offer bridge from the problem and mechanism, not as a separate
    sales block. The product should look like the concrete expression of the
    belief the VSL just created. [insight:zoChfFHnlOQ-v2-0009]
    [insight:qj04cUeaRAw-v2-0005]

## Output Requirements

Every VSL output should include:

- Briefing summary: product, avatar, awareness level, market, traffic source,
  asset job, and constraints.
- Core hypothesis: one belief, belief gap, mechanism, and commercial risk.
- Script map: lead, problem, mechanism of problem, mechanism of solution,
  proof, objections, offer bridge, CTA, and next step.
- Draft copy: usable pt-BR VSL sections, not only strategy notes.
- Proof plan: what claim each proof supports and where it appears.
- Objection plan: which objections are handled before, during, or after the
  offer bridge.
- Offer bridge: why the offer is the natural next step after the VSL logic.
- Test plan: first blocks to test, especially lead/headline, proof placement,
  objection handling, and CTA.
- Citations used: each non-obvious rule or strategic choice mapped to
  `insight_id`.

## No Invention

- Use only `curated_insights` as source material unless the owner explicitly
  reopens curation.
- Do not count the same `insight_id` twice when it appears in both imported
  modules.
- Do not let a transversal module decide VSL-specific lead, structure, proof
  placement, objection handling, offer bridge, or CTA.
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
