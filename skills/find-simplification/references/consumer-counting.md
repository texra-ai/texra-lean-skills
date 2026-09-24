# Counting Consumers Without Fooling Yourself

Grep is the cheap filter, and in a Lean codebase it is wrong by default. Every rule below was paid for by a survey that reported live declarations as dead, or dead ones as live.

## Grep rules

- **Search the final component, not the full name.** A declaration `Ns.Pred.foo` is invoked as `h.foo` or `W.foo`; the token `Ns.Pred.foo` never appears at the call site, so `rg -w 'Ns.Pred.foo'` returns zero for a lemma used three lines below. Match the last component with an optional dotted prefix and permit a leading `.`. The over-count from homonyms is the safe direction — resolve it by reading the hits.
- **Beware the upstream twin, but keep receiver notation.** Projects often mirror names from Mathlib or a companion library, so `Upstream.foo` and `Local.foo` share a suffix and upstream calls look like local consumers. Filter only *namespace qualifiers* — a capitalised dotted path — accepting the hit when that path is empty or a suffix of the declaring namespace. A lowercase prefix is receiver notation on a local hypothesis or variable (`hA.span_eq_top`) and is a genuine consumer.
- **Lean identifiers are not ASCII words.** Names carry `σ`, `ₗ`, `₂`, `'`, `ᵀ`. `rg -w` and any hand-built `[A-Za-z0-9_]` class truncate them silently and manufacture pages of false zeros. Use `rg -F` on the full name, and extract declaration names with a negated class such as `[^\s({\[:]+`.
- **Never `rg -F -f namelist`.** Ripgrep's leftmost-first alternation lets a short name shadow a longer one containing it, and the shadowed names come back with zero hits and no error. Loop one name at a time, or tokenize the corpus once and join against the declaration list.
- **Run a control.** Before trusting a pipeline, run it on a name you know is used, and on the declaration itself. A declaration always references itself, so **a count of zero is a bug in your matcher, never evidence.**
- **Subtract the self-inventory, not every docstring.** When modules list their results under a `## Main results` docstring section, a genuinely dead declaration scores 2, not 1, and a naive `count > 0` filter discards your best finds. Subtract exactly the declaration itself and its module's inventory entry. Do not strip doc comments wholesale: a name referenced from another surviving declaration's docstring is a live reference.
- **Dead weight is a closure, not a grep.** Zero-reference declarations are only the tips; a dead subgraph keeps itself alive by internal references. Attribute every reference to its enclosing declaration, then iterate "dead if all its references live inside declarations already marked dead" to a fixpoint. Repeat after each deletion — removing a lemma strands the private helpers only it used.

## Blueprint exposure comes first

In a blueprint-heavy chapter the normal shape of a *finished* theorem is "no Lean consumer, one `\lean{}` tag". Ranking by reference count before intersecting with the tag set wastes most of a survey. Build the tag set for the area first, intersect, then rank what remains.

Tags wrap across lines with a LaTeX `%` continuation *inside* the braces:

```latex
\lean{Foo.BarData.%
    exists_baz, Foo.qux}
```

A per-line grep and a naive `\lean\{([^}]*)\}` scan both miss these. Strip `%\s*\n\s*` before matching, then split each payload on commas — one tag may name several declarations — then cross-check by grepping the bare short name. [`../assets/lean_tag_census.py`](../assets/lean_tag_census.py) does both. Treating a payload as one set member undercounts the tagged set and can clear a still-exposed declaration for deletion.

Measure density before choosing a lens. Above roughly two-thirds tag coverage the tag-visible shapes are exhausted; what remains is what a tag cannot name — `private` forwarders, structure-parent aliases, carrier restatements. If an area's zero-reference rate is under about 2%, that lens is spent; pivot.

## Then let the compiler answer

Confirm by deleting the declaration and rebuilding; the consumer count is the elaboration result.

- **Rebuild the importers, not only the module.** `lake build Project.Path.To.Module` builds that module's *dependencies*, not its importers, so a declaration whose only consumer is downstream still looks dead. The module target is the fast inner loop; the verdict needs a root `lake build` or an explicit build of the reverse dependents.
- **Use `lake build`, not `lake env lean`, when linters matter.** `lake env lean` drops the lakefile `leanOptions` and runs no linters (unused variables, unused simp arguments, missing docstrings).
- **Attribute-carrying lemmas need the build.** A `@[simp]`/`@[grind]`/`@[ext]` lemma with no named call site may be firing inside a bare `simp`, or may be unfireable. Grep cannot separate these; do not silently exclude them. Collect them into a build-checked batch, delete the attribute, and let the build rule.
- **Probe semantics instead of reasoning about them.** When a survey is read-only, settle a question such as "does dot notation resolve through `extends` into the parent structure?" with a five-line standalone file elaborated by `lake env lean`.
- **Run the blueprint check after removal.** `leanblueprint checkdecls` catches a `\lean{}` tag left pointing at a deleted name; make sure any blueprint dependencies it loads are fetched first, or a setup failure reads like a clean result.
- **Scan for forbidden tokens before each commit.** A repaired downstream proof can introduce `sorry`, `admit`, `native_decide`, or `unsafeCast` while the build stays green. Match against the working-tree diff, not the whole branch: a textual scan over the branch fires on ordinary English ("the factors admit…") and buries real hits.
- **Never rebuild Mathlib.** In a fresh or cache-cleared worktree fetch the prebuilt cache first (see [`lean-build-cache`](../../lean-build-cache/SKILL.md)).
