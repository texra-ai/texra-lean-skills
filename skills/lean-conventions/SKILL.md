---
name: lean-conventions
description: The shared convention documents for Lean 4 / Mathlib formalization projects — code style, naming, documentation, PR review criteria, proof-integrity rules, and prose style. Consult before writing or reviewing Lean code, docstrings, blueprint prose, or PRs in a project of this family; these are the canonical texts that per-repo copies mirror or point to.
---

# Lean Conventions

This skill is the canonical home of the family's convention documents. A
consuming repository keeps at most a thin pointer plus a "Project addendum"
of its own facts; everything normative lives here.

| Document | Covers |
|---|---|
| [references/MATHLIB_style.md](references/MATHLIB_style.md) | Code formatting, line length, declarations, tactic style, whitespace, deprecation |
| [references/MATHLIB_naming.md](references/MATHLIB_naming.md) | Capitalization rules, symbol-to-name dictionary, variable conventions |
| [references/MATHLIB_doc.md](references/MATHLIB_doc.md) | Module and definition docstrings, sectioning comments, citations |
| [references/MATHLIB_pr-review.md](references/MATHLIB_pr-review.md) | Review criteria: style, documentation, location, library integration |
| [references/PROOF_INTEGRITY.md](references/PROOF_INTEGRITY.md) | Blockers (sorry, axioms, kernel bypasses, circular reasoning) and warnings |
| [references/prose_style.md](references/prose_style.md) | Reader-facing prose: no Lean jargon in mathematics, banned terms and patterns |

When a project-specific rule seems to belong in one of these documents,
check its repository's addendum first; if the rule is genuinely general,
change it here and let the mirrors re-stamp.
