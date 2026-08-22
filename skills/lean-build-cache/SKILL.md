---
name: lean-build-cache
description: Keep Lean 4 / Mathlib builds fast on a local machine — fetch prebuilt Mathlib artifacts before any build, keep the primary worktree's build hot, and APFS-clone it into fresh worktrees instead of rebuilding. Use when setting up a worktree, when a build is unexpectedly rebuilding Mathlib, when planning agent work across parallel worktrees, or when diagnosing slow lake builds.
---

# Lean Build Cache

## The two iron rules

1. **Never build Mathlib from source.** In any fresh, cloned, or
   cache-cleared worktree — and after any Mathlib/toolchain/dependency bump —
   run `lake exe cache get` *before* `lake build` or any local Lean check.
   Skipping it can silently trigger an hours-long rebuild.
2. **Keep the primary worktree hot, and seed from it.** The main checkout
   holds the authoritative warm `.lake`; fresh worktrees are APFS-clone-seeded
   from it, never rebuilt. Never seed while the source worktree is running a
   Lake command.

## The tools (copy from [assets/](assets/) into the project's `scripts/`)

- [`assets/seed_lake_build.sh`](assets/seed_lake_build.sh) — the seeder:
  `seed_lake_build.sh TARGET_WORKTREE [SOURCE] [--dry-run]`. Validates
  everything before touching anything and swaps the clone in atomically;
  contract and failure modes in
  [references/seeding-contract.md](references/seeding-contract.md).
- [`assets/lake_build_hotspots.py`](assets/lake_build_hotspots.py) —
  build-time triage: `lake build 2>&1 | tee log` then
  `python3 lake_build_hotspots.py log` lists slow jobs and gates changed
  modules (warn 25s, fail 50s; thresholds are flags).
- Each ships with its test harness
  ([`test_seed_lake_build.sh`](assets/test_seed_lake_build.sh),
  [`test_lake_build_hotspots.py`](assets/test_lake_build_hotspots.py)) —
  run them after copying.

## Verification that actually runs the linters

`lake build Project.Path.To.File` applies the package `leanOptions`
(including Mathlib's linter set) — but only when the module re-elaborates.
`lake env lean` is fast elaboration only, applies no package options, and is
not a linter-bearing check; only `lake build` reproduces CI.
