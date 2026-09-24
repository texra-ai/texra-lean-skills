---
name: find-simplification
description: Find non-obvious, evidence-backed simplification candidates in a Lean 4 / Mathlib development and record them for a later deletion PR. Use when asked to audit a directory, review a PR, or run a cleanup pass for zero-reference declarations, pass-through wrappers, Mathlib shadows, hand-mirrored files, numbered or suffix-ladder sequels, stricter-hypothesis specializations kept beside their general theorem, degenerate-case apparatus, parallel predicate families with bridge lemmas, and unused imports.
---

# Find Simplification

This skill turns a broad "find things to simplify" request into evidence-backed candidates that remove or collapse existing surface area. It is guidance, not a checklist: follow the dependencies, keep judgment active, and prefer a few proven candidates over a pile of thin guesses. It *finds and proves* a candidate; [`lean-simplifier`](../lean-simplifier/SKILL.md) executes a cleanup on a file once the candidate is chosen.

## What simplification means

Simplification is the removal of structure that the problem does not demand. Every codebase accumulates two kinds of structure: the kind the subject forces (a theorem needs its hypotheses) and the kind the *process* of building left behind — exploration branches, staging, defensive generality, copies made under deadline, seams built for a second consumer that never arrived. Only the second kind is simplifiable, and most of it hides in plain sight because each piece was reasonable when written.

The recurring shapes, in any language:

- **Dead weight.** Things with no consumer: unused exports, unreachable files, tests that pin retired behavior, documentation of deleted features. The cheapest wins; the only question is proving the absence of consumers.
- **Duplication.** The same fact represented twice — copied code, mirrored modules, a value re-derived at several call sites, two APIs for one concept with bridges between them. The fix is one owner; the risk is that the copies drifted and one drift is load-bearing.
- **Speculative generality.** Parameters with one value, registries with one entry, abstractions with one implementation. Generality is only free when it is used.
- **Indirection that only relocates complexity.** Wrappers and helper layers that add a name without adding a decision.
- **Scaffolding after the capstone.** Intermediate results, compatibility shims, and staged variants kept after the thing they supported landed.
- **Special cases beside the general case.** The narrow version proved first, still present after the general version subsumed it.
- **Hand-rolled code the platform already provides.** The find is the exact upstream name it duplicates.
- **Degenerate-case apparatus.** Machinery for inputs the problem never produces: empty collections, zero dimensions, the null configuration. When the intended domain excludes the case, model the exclusion once in the definition and delete the machinery.

Three disciplines separate a find from a guess. **Consumers, not impressions**: classify every reference and prove the count by the strongest available means — for code, by removing the thing and building. **Net, not gross**: count what the replacement adds against what leaves. **Deletion outranks abstraction**: when a duplication can be resolved by abstracting or by deleting one side, deletion is smaller, safer, and more honest. And respect settled decisions: a design with a recorded rationale is challenged with new evidence, not re-litigated.

## How the shapes look in Lean

A proof assistant makes these shapes unusually sharp: a declaration's consumers are exactly the identifiers that elaborate against it, and a statement's content is exactly its hypotheses and conclusion.

- **Dead weight** is a declaration referenced only by itself, or a file reachable only through an import aggregator. The compiler is the oracle: delete it and build.
- **Duplication** is the same lemma re-proved under two names, or two developments related by a rename (left/right, row/column) when a transport lemma would carry one to the other.
- **Speculative generality** is a typeclass or universe parameter instantiated once, or a bundled hypothesis structure with one instance. Its opposite is also debt: a special-case theorem kept after the general one landed, when the special case is a one-line corollary.
- **Indirection** is the pass-through: `exact foo`, a field projection, a `simpa using` of one lemma, exported under a second name.
- **Scaffolding** is the sequel chain (`Foo`, `Foo2`, `FooV2`, `FooCore` + `FooBridge`) whose intermediate lemmas each have one consumer in the next file.
- **Hand-rolled code** is the Mathlib shadow: a local lemma that `exact?` closes from the library alone, or a local definition the library carries under another name. Toolchain bumps create new shadows silently.
- **Degenerate cases** are `≠ 0` / `0 <` side conditions repeated on every downstream statement, and a parallel `raw`/`active` predicate pair with bridge lemmas, where the definition could carry the exclusion once.
- **Hypotheses** are their own category. A hypothesis every caller discharges by the same lemma belongs inside the theorem; a hypothesis no caller can discharge marks its whole route as superseded; when the project formalizes a cited source, a hypothesis absent from that source is not a simplification target but a faithfulness defect (see [`paper-gap-notes`](../paper-gap-notes/SKILL.md)).

Three shapes are invisible to consumer counting, because counting starts from a declaration and asks who uses it:

- **Name collisions.** The same fully qualified name declared in two modules of the import closure. Start from a *name* and count its definitions: [`assets/lean_name_collisions.py`](assets/lean_name_collisions.py) walks `namespace`/`end` and reports every name with more than one site.
- **`private` re-declaration.** A `private` helper has no cross-module consumers by construction, and privacy is exactly what provokes a downstream file to re-declare it. Compare private bodies across files in the same directory.
- **Unused imports.** One import line can drag a large compile cone into a module. For every import, name an identifier it supplies.

Two dialect notes. The sequel chain is often not `Foo2.lean` but a **hypothesis-strength suffix ladder** — `foo`, `foo_c1`, `foo_c1_of_bar` — where each suffix weakens a hypothesis and the unsuffixed root is the abandoned strict version. And a systematic name-pair is a **mirror only when a transport map exists** that carries one side to the other; without one, the pair is content, and collapsing it deletes mathematics.

Proof text is the one place where shorter is not automatically simpler. The proof-level find is a missing helper or simp lemma that several proofs re-derive inline, not a golfed tactic block.

## Start with project context

Before surveying, read what the project already decided, so that finds are new and rejections are cheap:

- The agent instructions (`CLAUDE.md`, `AGENTS.md`) and contributing or convention docs: the deprecation policy and its window, whether pass-throughs may go without an alias, and any rules on faithfulness to cited sources or on degenerate cases.
- Whatever record of past cleanup the project keeps — a debt ledger, dated audit notes, cleanup issues, or only the git log. A candidate that duplicates an open entry is an evidence update to that entry, not a find; re-proposing an item retained on purpose must beat the recorded reason. Counts in old notes are snapshots — the newest note for the area wins.
- Open *and* closed issues labelled for cleanup or proof debt.
- The settled surfaces, such as boundaries with upstream dependencies, generated import aggregators (their import lists are a build artifact, not a consumer count), project tactics and simp sets, archive directories excluded from the root import, blueprint-cited declarations, and CI policy scripts. Trimming an unused declaration *inside* one is fine; collapsing the seam is not. Proposing to make a file pass a CI policy is welcome; proposing to loosen the policy is not.

## Survey broadly

Use parallel subagents when the user asks for breadth. Give each agent one directory and require `path:line` evidence, not impressions. Do not let the first good candidate stop the survey. Start with the largest files, the slowest-to-build modules, and the modules with the most importers (`rg -l "^import Project.X.Y$" Project` counts importers).

Thin candidates are not enough: a single non-terminal `simp`, a stray `set_option`, "this proof is long" without a slicker argument in hand, or reformatting. Batch those into a hygiene PR or leave them.

## Audit hypotheses and layer boundaries

For every hypothesis on a candidate theorem, name where it is discharged downstream. For every structure field, name a consumer that projects it; fields read only by the structure's own constructor lemmas are staging. For every layer crossing, check the direction: a lemma stated purely about library objects but living in a domain-specific file is a candidate to replace by its upstream form, and relocating it to a local general-purpose layer only creates the next shadow — upstream it, or leave it and record why.

## Local lemma versus Mathlib

The default runs toward the upstream library. For each local lemma that smells standard, try, in order: `exact?` on the statement with the local proof deleted; `rg` of the conclusion's head symbol under `.lake/packages/*/` (Mathlib and any other dependency); the Mathlib changelog or the project's own notes from its last toolchain bump.

Search by the shape of the statement, not by the name. The hardest shadows share no token with their upstream twin; what finds them is reading a bare lemma sitting in a domain file and grepping the conclusion's form. A local lemma that strictly generalizes the upstream one, or states it for a different carrier, stays — record why in its docstring. A genuinely new Mathlib-shaped lemma can be the right answer when it deletes several local variants; state which variants it retires.

## Prove or reject each candidate

Classify consumers before writing. **Production**: the source tree outside archives, blueprint `\lean{...}` tags if the project has a blueprint, Lean scripts and tests, and the docstrings of surviving declarations. **Non-production**: archives, dated snapshots, notes, and non-docstring comments. **Ambiguous**: documentation that names a declaration as public API — migrate the reference rather than counting it as a blocker.

Grep proposes; elaboration decides. The rules for counting without fooling yourself — dot-notation call sites, upstream twins, non-ASCII identifiers, ripgrep alternation shadowing, controls, self-inventory, and the dead-subgraph fixpoint — are in [references/consumer-counting.md](references/consumer-counting.md). In a blueprint-heavy area, build the `\lean{}` tag set **before** ranking by reference count: [`assets/lean_tag_census.py`](assets/lean_tag_census.py) handles `%`-continued and comma-separated tags. The build-side verdict (which target to rebuild, attribute-carrying lemmas, linters) is in the same reference.

Reject or downgrade a candidate when:

- A production consumer exists and removing it would change what is proved — a feature decision, not a cleanup.
- A recorded rationale (a design note, an audit record, a documented source deviation) justifies the design and the new evidence does not beat that reason. Check the *module path* too, not only the declaration.
- The deletion was already made and rolled back. `git log -S'<name>' --all -- <path>` finds commits where the occurrence count changed; `--diff-filter=D` matches only whole-file deletions and misses exactly this.
- The declaration sits in a counterexample or witness module whose docstring advertises it as the file's claim.
- It is `@[deprecated]` inside the project's transition window.
- It is a substantive public declaration rather than a pass-through. A green root build proves only that nothing *in this repository* consumes it; downstream projects may. Such a name enters dated deprecation unless project policy says otherwise.
- The removal forces unrelated churn without reducing the public surface or the hypothesis lists.
- The candidate is correct but tiny; batch it with related finds.
- The "simplification" is a net-positive-line abstraction that names no future deletion it enables.

## Record the candidate

Durable findings go to the project's existing record, in its own format — a debt-ledger entry, a cleanup issue, or a dated note for a finding that needs an argument (a retirement decision, a retained-on-purpose ruling, a mirror-collapse plan). Dedupe against open and closed issues; consolidate into the record that owns the topic.

Be concrete enough that an implementing PR can follow the trail: declarations by full name, the survivor each maps to, blueprint labels to redirect (if any), grepped-then-built consumer counts, risk, and the net line estimate. One entry per durable candidate; do not pad the count.

A PR implementing the simplification states its net line delta, the record it burns down, each removed declaration with its replacement, and any blueprint labels redirected. A PR that leaves old and new side by side is in progress, not done.

When reporting back, summarize: how many candidates went to which record or were rejected with evidence; the directories surveyed; what was excluded as settled; which checks passed.
