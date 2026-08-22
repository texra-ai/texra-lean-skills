# Paper-Realignment Mode

When a formalization has drifted from its cited source and the work is
*realigning the Lean development to the paper* — replacing wrong hypotheses,
removing divergent structures, restating theorems to match the source — the
project's default `sorry`/`axiom` blockers are temporarily relaxed. The
priority is getting the statements right; proofs are restored after. In this
mode the standard "do not add sorry" rule is the wrong heuristic: keeping a
divergent proof intact to avoid `sorry` preserves a result the source does
not assert.

## Source-citation requirement

Every restated definition, hypothesis field, or theorem must carry a
docstring referencing the source by label or line range. Minimum forms:

- `arXiv:1606.00608, eq:II_CF1` — equation/theorem label
- `arXiv:1606.00608, lines 1170–1192` — line range in the local source
- `CPSV16, Lemma Lem1` — paper short name plus internal label
- `Wolf §6.2` — published section reference

An inline identifier without a source reference is unreviewable in this
mode: a reviewer cannot tell whether the field is faithful or invented.
The statement is the load-bearing artifact, whether or not the proof is
`sorry`.

## What a realignment PR may do

- Delete fields, hypotheses, or whole theorems documented as divergent from
  the cited source (divergence recorded in a paper-gap note).
- Leave `sorry` in proof bodies whose old proof depended on the deleted
  data, when the paper-faithful replacement is the next step.
- Cascade signature changes through downstream consumers, also with `sorry`
  where necessary, rather than reverting to keep the build proof-clean.

## What a realignment PR must do

- Cite the paper-gap note documenting the divergence in the PR description.
- Identify every `sorry` introduced and the paper-faithful theorem that
  will discharge it.
- Be scoped tightly — no unrelated refactors or feature additions.
- Be followed by tracked issues for the missing paper-faithful proofs.

Reviewers evaluate a realignment PR against the paper-gap note and the
planned follow-up, not against the temporary `sorry` count. A PR that
introduces an unfaithful theorem without its marker (see the skill's marker
grammar) is not approvable.
