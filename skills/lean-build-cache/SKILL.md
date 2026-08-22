---
name: lean-build-cache
description: Keep Lean 4 / Mathlib builds fast on a local machine — fetch prebuilt Mathlib artifacts before any build, keep the primary worktree's build hot, and APFS-clone it into fresh worktrees instead of rebuilding. Use when setting up a worktree, when a build is unexpectedly rebuilding Mathlib, when planning agent work across parallel worktrees, or when diagnosing slow lake builds.
---

# Lean Build Cache

## The two iron rules

1. **Never build Mathlib from source.** In any fresh, cloned, or cache-cleared
   worktree, run `lake exe cache get` *before* `lake build` or any local Lean
   check. Skipping it can silently trigger an hours-long Mathlib rebuild. The
   same applies after any Mathlib, toolchain, or dependency bump.
2. **Keep the primary worktree hot.** The repository's main checkout holds the
   authoritative warm `.lake`; fresh worktrees are seeded *from* it rather than
   rebuilt. Never run a seed while the source worktree has a Lake command
   running.

## Seeding a fresh worktree (macOS/APFS)

```bash
git worktree add -b agent/my-branch /private/tmp/proj-my-branch origin/main
scripts/seed_lake_build.sh /private/tmp/proj-my-branch --dry-run   # preflight
scripts/seed_lake_build.sh /private/tmp/proj-my-branch             # clone
```

The seed uses APFS copy-on-write cloning (`/bin/cp -c`): instant, disk-cheap,
and the clones are independent writable files — no shared mutable state
between worktrees. The script validates before touching anything: same
repository, identical `lean-toolchain` / `lake-manifest.json` / `lakefile.toml`,
clean dependency checkouts at the manifest revisions, prebuilt `Mathlib.olean`
present in the source, and no pre-existing target `.lake`. The target is
reserved and the completed clone is swapped in atomically, so a concurrent
Lake process can never observe a partial cache.

**Commit-match rule:** full project build artifacts are reused only when
source and target are at the same commit. Across commits the seed carries only
the validated dependency packages (including Mathlib) and leaves the project's
own `.lake/build` absent — run `lake build` afterward so the project rebuilds
against the seeded dependencies. This prevents stale `.olean` files whose
declarations no longer match the target sources.

## Verification that actually runs the linters

- `lake build Project.Path.To.File` — linter-bearing check of one module,
  applying the package `leanOptions` (including Mathlib's standard linter
  set). Diagnostics appear only when the module is re-elaborated; an
  unchanged, already-built module prints nothing.
- `lake env lean Project/Path/To/File.lean` — fast elaboration only; it does
  **not** apply the package options and is not a linter-bearing verification.
  Only `lake build` reproduces what CI checks.

## Diagnosing slow builds

```bash
lake build 2>&1 | tee /tmp/build.log
python3 scripts/lake_build_hotspots.py /tmp/build.log   # jobs ≥ threshold
```

Compile-time regressions in changed modules are a reviewable defect, not
noise; projects in this family gate on a per-module compile-time limit in CI.

For the seed script's full validation contract and failure modes, see
[references/seeding-contract.md](references/seeding-contract.md).
