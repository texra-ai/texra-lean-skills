#!/usr/bin/env python3
"""Reject tracked production Lean files over the configured line limit.

The limit (``oversized.max_lines``, default 1000) comes from
``lean_file_policies.json``. Files in ``oversized.known`` are reported as
warnings and do not fail; remove each one from the list once it is split.
Exact paths in ``oversized.import_only_aggregators`` are exempt, but each
exemption is validated: after comments are removed the file must contain only
import commands (and an optional ``module`` header).

    check_oversized_lean_files.py [--root .] [--config lean_file_policies.json]

Output uses GitHub annotation syntax.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lean_file_policies  # noqa: E402
from lean_file_policies import Policies  # noqa: E402
from lean_source import pure_import_modules  # noqa: E402

SPLIT_GUIDANCE = (
    "Split by mathematical responsibility into concept-named modules; move shared "
    "definitions and setup into a family Basic.lean module; and keep only imports "
    "in a concept-named aggregator. Do not create numbered continuations such as "
    "Foo2.lean or Foo3.lean."
)


def _count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def validate_import_aggregator(path: Path) -> str | None:
    """Return ``None`` exactly when *path* is a nonempty import-only Lean file."""
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return f"cannot read file: {error}"
    _, error = pure_import_modules(source)
    return error


def check_files(root: Path, policies: Policies) -> int:
    """Check tracked Lean files under *root*; return 1 for any policy violation."""
    limit = policies.max_lines
    try:
        tracked = lean_file_policies.tracked_lean_files(root, policies)
    except (subprocess.CalledProcessError, UnicodeDecodeError) as error:
        print(f"::error title=Oversized Lean file check failed::git ls-files failed: {error}")
        return 1

    errors = 0
    valid_aggregators: set[str] = set()
    for relative in sorted(policies.import_only_aggregators):
        if relative not in tracked:
            reason = "exemption must name a tracked, in-scope .lean file"
        else:
            reason = validate_import_aggregator(root / relative)
        if reason is None:
            valid_aggregators.add(relative)
        else:
            print(f"::error file={relative},title=Invalid import-only aggregator exemption::"
                  f"{relative}: {reason}")
            errors += 1

    oversized: list[tuple[int, str]] = []
    known: list[tuple[int, str]] = []
    for relative in sorted(tracked):
        lines = _count_lines(root / relative)
        if lines <= limit or relative in valid_aggregators:
            continue
        (known if relative in policies.known_oversized else oversized).append((lines, relative))

    for relative in sorted(policies.known_oversized - {r for _, r in known}):
        print(f"::error file={relative},title=Stale known oversized entry::"
              f"{relative}: no longer oversized or tracked; remove it from oversized.known")
        errors += 1

    for lines, relative in sorted(known, reverse=True):
        print(f"::warning file={relative},line={limit + 1},title=Known oversized Lean file::"
              f"{relative}: {lines} lines (limit: {limit}) — known, tracked for splitting")
    for lines, relative in sorted(oversized, reverse=True):
        print(f"::error file={relative},line={limit + 1},title=Oversized Lean file::"
              f"{relative}: {lines} lines (limit: {limit}). {SPLIT_GUIDANCE}")

    print(
        f"Scanned {len(tracked)} tracked production Lean files: "
        f"{len(known) + len(oversized)} nonexempt files exceed {limit} lines "
        f"({len(known)} known, {len(oversized)} new); validated "
        f"{len(valid_aggregators)} of {len(policies.import_only_aggregators)} "
        "exact aggregator exemption(s)."
    )
    if oversized:
        print(f"Split guidance: {SPLIT_GUIDANCE}")
    return 1 if errors or oversized else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path("."), help="repository root")
    parser.add_argument("--config", default=lean_file_policies.DEFAULT_CONFIG,
                        help="configuration path relative to the root")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        policies = lean_file_policies.load(root, args.config)
    except ValueError as error:
        print(f"::error title=Oversized Lean file check failed::{error}")
        return 1
    return check_files(root, policies)


if __name__ == "__main__":
    raise SystemExit(main())
