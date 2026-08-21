---
name: paper-gap-notes
description: Record and manage deviations between a formalization and its cited sources as standalone mathematical notes. Use when a Lean statement needs a hypothesis the paper does not provide, a source contains a typo or a false claim, a theorem is proved only in a restricted scope, or a proof takes a different route than the cited argument.
---

# Paper-Gap Notes

## The faithfulness rule

A theorem is formalized only when its signature has no hypothesis absent from the cited source's statement. A Lean theorem with stricter hypotheses than the source is a *different* theorem — a corollary or specialization — and must not be presented as the formalization of the source result. Every such deviation gets a paper-gap note.

## When to write a note

Write a note under `docs/paper-gaps/` whenever the formal statement is not literally the cited statement: a smuggled hypothesis, a scalar or constant correction, a scope restriction, a counterexample to the source as printed, a replacement proof route, or an internal audit of the theorem surface. The source text itself stays intact; the note carries the discrepancy.

## Workflow

1. State the source's assertion and the formal statement side by side, in ordinary mathematics. The note must be readable by a mathematician who has not seen the repository.
2. Name the file `<key>_<topic>.tex`, where `<key>` is a registered source key (author initials plus two-digit year, or a canonical short name for a book or review; a reserved key for internal audits with no single external source). File names are permanent once cited — no version suffixes; revise in place.
3. Classify the verdict: notational clarification, local correction, scope restriction, unfaithful theorem, source claim false as printed, or open gap. Follow the mathematics, not the amount of formal work.
4. Mark the affected Lean declarations. An **Unfaithful:** docstring marker (naming the deviation, citing the note, sketching the elimination plan) for deviations that would be wrong without follow-up work; **Scope restriction (...):** or **Local fix (...):** for deviations that are correct as stated but narrower than the source. Unfaithfulness propagates: any theorem transitively relying on an unfaithful one carries its own marker.
5. Cite the note from every load-bearing site — Lean docstrings, blueprint entries, other notes — by its repository path, and keep the references checkable (a CI pass should fail on a citation of a note that does not exist).
6. Keep each note a coherent account of present understanding, not a chronological log. When the gap closes, rewrite the note to show the derivation and remove the markers whose dependencies became faithful.

## Quality bar

- Traceability data (declaration names, file paths, issue links) supports the exposition, in footnotes — it never governs the exposition.
- The blueprint entry citing a source must point at a Lean statement with the source's hypothesis set; otherwise it loses its formalized status or the restriction is stated explicitly in the blueprint.
- A note exists before the deviating code merges, not after.

For the note skeleton, the marker grammar, and the naming registry pattern, see [references/note-conventions.md](references/note-conventions.md). When the work is realigning drifted formalizations to the paper (relaxed sorry rules, statement-first priorities), follow [references/paper-realignment.md](references/paper-realignment.md). To adopt the protocol in a project, copy the three files in [assets/](assets/) into `docs/paper-gaps/`: `command.tex` (shared preamble; edit the project-configuration block), `template.tex` (a model note kept as a writing reference, never compiled), and `policy.tex` (the conventions, published alongside the notes).
