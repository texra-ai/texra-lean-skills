# Seeding Contract

`seed_lake_build.sh TARGET [SOURCE] [--dry-run] [--refresh]` — SOURCE defaults
to the repository's primary worktree.

Preconditions (the script dies rather than degrade):
- macOS with APFS; `/bin/cp -c` is used by absolute path so Homebrew GNU
  coreutils cannot shadow the clone-aware command. `cp -c` fails instead of
  silently falling back to a full copy when cloning is unavailable.
- Both paths belong to the same repository.
- `lean-toolchain`, `lake-manifest.json`, `lakefile.toml` byte-identical
  between source and target.
- Source `.lake`, `.lake/build`, `.lake/packages` exist, are regular
  directories, not symlinks (nested Lake build dirs included).
- Git dependency checkouts are clean and at the revisions recorded in the
  manifest.
- Prebuilt `Mathlib.olean` present in the source. If it is missing, the seed
  runs `lake exe cache get` in the source itself; when the artifact is already
  present the fetch is skipped, and `--refresh` forces it (e.g. to re-verify
  artifacts against the manifest revision).
- Target `.lake` absent.

Behavior:
- Same commit on both sides → full reuse: seeded target runs `lake build`
  with everything warm.
- Different commits → dependencies-only seed (no project `.lake/build`);
  run `lake build` in the target to rebuild the project against the seeded
  dependencies.
- The target `.lake` is an inaccessible reservation until the completed
  clone is atomically renamed into place.

Do not seed while the source worktree is running any Lake command.
