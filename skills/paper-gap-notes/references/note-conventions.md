# Paper-Gap Note Conventions

## Note skeleton

A note is a short standalone LaTeX article. Start from `assets/template.tex`, which models the full form; the shared preamble is `assets/command.tex` (both `latexmk`-verified):

```latex
\title{<Mathematical subject of the discrepancy>}
\date{YYYY-MM-DD}
...
\section{The assertion}        % the source's statement, cited precisely
\section{The formal statement} % what the formalization actually proves
\section{The discrepancy}      % the mathematical difference, and why it matters
\section{Verdict}              % classification + elimination plan or closure
```

Cite sources by label or line range: `arXiv:1606.00608, eq:II_CF1`, `Wolf §6.2`, `CPSV16, Lemma Lem1`. Put issue links, PR links, declaration names, and file paths in footnotes.

## Verdict marker

Directly after `\maketitle`, every note declares
`\gapnote{<kind>}{<status>}` — kind from the classification vocabulary
(`clarification`, `local-correction`, `scope-restriction`, `unfaithful`,
`false-source`, `open-gap`), status `open`/`wip`/`resolved`/`historical`
(`wip` = elimination actively underway; still live debt).
Severity derives from the kind (unfaithful, false-source, open-gap are
high; scope-restriction and local-correction medium; clarification low) —
never stated separately. Resolving a gap changes the status, not the kind;
the published index sorts open notes first, dims the settled ones, and
reports the open/high-severity counts. CI can require the marker
(`require_verdict = true` in the `[paper_gaps]` config).

## Naming

`<key>_<topic>.tex`. Keys live in a registry (one dict or table per project) mapping key → source: `cpsv16 → arXiv:1606.00608`, `wolf → Wolf, Quantum Channels & Operations`. Reserve one key (e.g. `tnlean`) for internal theorem-surface audits. Enforce in CI: reject an unregistered key and any repository reference to a note file that does not exist. Never encode issue numbers, first names, or bare arXiv numbers as keys; never append `_v1` — the repository history is the version record.

## Marker grammar (Lean docstrings)

```
**Unfaithful:** This proof relies on `<hypothesis or lemma>`, which deviates
from `<source, label or line range>`. Documented in
`docs/paper-gaps/<note>.tex`. Elimination: <faithful substitute>; tracked in <issue>.
```

- `**Unfaithful:**` — the deviation would be mathematically wrong without follow-up work. Propagates to every transitive dependent; removed only when all cited dependencies are faithful.
- `**Scope restriction (...):**` — correct as stated, proved for a sub-case of the source theorem.
- `**Local fix (...):**` — a typo, constant, or off-by-one corrected relative to the source.

All three forms reference the note by path.

## Publishing

Compile the notes to PDF in CI and publish them with the project site: one generated index grouped by source key (titles parsed from `\title`), stable per-note URLs (`.../paper-gaps/<name>.pdf`), and a generated BibTeX file with one `@techreport` per note (key `gap:<name>`) so the notes are citable from the blueprint and from papers.

## Citing a note

Blueprint prose cites a note like any other source: `\cite{gap:<slug>}`, with the entry copied from the generated BibTeX file into the blueprint's bibliography:

```bibtex
@techreport{gap:<slug>,
  author      = {The {<Project>} contributors},
  title       = {<note title>},
  institution = {<Project>},
  type        = {Paper-gap note},
  number      = {<slug>},
  year        = {<YYYY>},
  url         = {<site base>/paper-gaps/<slug>.pdf},
}
```

The published URL lives only in the bibliography entry, never in prose. A cross-repository citation uses the same mechanism — the entry's `url` (and author/institution) name the repository that owns the note. Lean docstrings, code comments, and `%` comments keep the repository path form `docs/paper-gaps/<slug>.tex`. CI validates path-form references (a referenced note file must exist); validating the `\cite{gap:<slug>}` form is a package follow-up.
