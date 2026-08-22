# texra-lean-skills

Agent skills for Lean 4 / Mathlib formalization. Distributed as a [Claude Code plugin](https://docs.claude.com/en/docs/claude-code/plugins) and as a [Codex](https://github.com/openai/codex) skills bundle. Skills follow the standard `SKILL.md` format, so any agent that reads it can use them.

## Skills

| Skill | Purpose |
| --- | --- |
| [`lean-conventions`](skills/lean-conventions/SKILL.md) | Canonical convention documents: Mathlib style, naming, docs, PR review, proof integrity, prose style. |
| [`lean-build-cache`](skills/lean-build-cache/SKILL.md) | Fast local Lean 4 / Mathlib builds: cache-first rule, hot primary worktree, APFS clone-seeding of fresh worktrees. |
| [`lean-blueprint`](skills/lean-blueprint/SKILL.md) | Author and maintain Lean blueprint documents that connect informal mathematics to Lean 4 declarations. |
| [`paper-gap-notes`](skills/paper-gap-notes/SKILL.md) | Record deviations between a formalization and its cited sources as standalone, citable mathematical notes. |
| [`lean-proof-assistant`](skills/lean-proof-assistant/SKILL.md) | Develop and debug Lean 4 proofs in project context — inspect goals, search for lemmas, iterate on tactic scripts. |
| [`lean-search`](skills/lean-search/SKILL.md) | Find existing Lean 4 / Mathlib lemmas, APIs, imports, and formalization patterns before writing new code. |
| [`lean-simplifier`](skills/lean-simplifier/SKILL.md) | Refactor Lean 4 code toward Mathlib-quality style without changing theorem statements or computational meaning. |

## Install

### Claude Code

```
/plugin marketplace add texra-ai/texra-lean-skills
/plugin install texra-lean-skills@texra-lean-skills
```

Update: `/plugin marketplace update texra-lean-skills`.

### Codex

```bash
git clone https://github.com/texra-ai/texra-lean-skills.git ~/.codex/texra-lean-skills
mkdir -p ~/.codex/skills
ln -sfn ~/.codex/texra-lean-skills/skills ~/.codex/skills/texra-lean-skills
```

Restart Codex. Update: `cd ~/.codex/texra-lean-skills && git pull`.

### Any other agent

Clone and copy or symlink individual skill directories into your agent's skill location.

```bash
git clone https://github.com/texra-ai/texra-lean-skills.git
ln -s "$PWD/texra-lean-skills/skills/lean-proof-assistant" ~/.claude/skills/lean-proof-assistant
```

## Layout

```
skills/<skill-name>/
├── SKILL.md           # frontmatter + workflow / quality bar
├── references/        # deeper checklists referenced from SKILL.md
└── agents/            # optional sub-agent definitions
```

## Related

- [`texra-ai/texra-scientific-skills`](https://github.com/texra-ai/texra-scientific-skills) — companion collection for scientific writing, reviewing, and figure work.

## License

[MIT](LICENSE) © texra-ai
