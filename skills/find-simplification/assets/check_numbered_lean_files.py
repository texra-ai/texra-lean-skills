#!/usr/bin/env python3
"""Reject new numbered-sequel names among tracked production Lean modules.

A file named ``Foo2.lean`` usually continues a proof that outgrew ``Foo.lean``
instead of naming what it proves. The debt list in ``lean_file_policies.json``
is a ratchet: existing sequels may remain, new ones fail, and a removed or
renamed file must leave the list in the same change. Trailing numbers that are
mathematics (``ZMod2``, ``Corollary41``) go in ``semantic_exceptions`` with a
reason.

    check_numbered_lean_files.py [--root .] [--config lean_file_policies.json]
                                 [--base-ref origin/main]

With ``--base-ref``, the debt list is also compared against its state at the
merge base and may only shrink. Output uses GitHub annotation syntax.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lean_file_policies  # noqa: E402
from lean_file_policies import Policies  # noqa: E402

NUMBERED_STEM = re.compile(r"\d+[A-Za-z]?$")
SPLIT_GUIDANCE = (
    "Name modules for their mathematical responsibility (for example, "
    "BoundaryRecovery.lean), move shared definitions into a family Basic.lean "
    "module, and use a concept-named import aggregator. Do not continue a proof "
    "as Foo2.lean/Foo3.lean."
)


def has_numbered_suffix(path: str) -> bool:
    return NUMBERED_STEM.search(Path(path).stem) is not None


def check_numbered_files(
    root: Path,
    policies: Policies,
    base_debt: frozenset[str] | None = None,
) -> int:
    """Check the numbered-name ratchet and return a process exit status."""
    debt = policies.numbered_debt
    exceptions = policies.semantic_exceptions
    try:
        tracked = lean_file_policies.tracked_lean_files(root, policies)
    except (subprocess.CalledProcessError, UnicodeDecodeError) as error:
        print(f"::error title=Numbered Lean file check failed::git ls-files failed: {error}")
        return 1

    errors: list[str] = []
    if base_debt is not None:
        for path in sorted(debt - base_debt):
            errors.append(f"{path}: added to the numbered debt list; this list may only shrink")

    for path in sorted(debt & exceptions.keys()):
        errors.append(f"{path}: listed as both numbered debt and a semantic exception")

    for path in sorted(debt):
        if path not in tracked:
            errors.append(f"{path}: stale debt entry; remove it now that the file is gone")
        elif not has_numbered_suffix(path):
            errors.append(f"{path}: no longer has a numbered suffix; remove its debt entry")

    for path, reason in sorted(exceptions.items()):
        if not reason.strip():
            errors.append(f"{path}: semantic exception has no explanation")
        if path not in tracked:
            errors.append(f"{path}: stale semantic exception; remove or update it")
        elif not has_numbered_suffix(path):
            errors.append(f"{path}: semantic exception is unnecessary; remove it")

    numbered = {path for path in tracked if has_numbered_suffix(path)}
    unexplained = numbered - debt - exceptions.keys()
    for path in sorted(unexplained):
        errors.append(f"{path}: new numbered-sequel filename; name the module for what it proves")

    for message in errors:
        path = message.split(":", 1)[0]
        print(f"::error file={path},title=Numbered Lean module policy::{message}")

    print(
        f"Checked {len(tracked)} tracked production Lean files: "
        f"{len(numbered & debt)} numbered debt, "
        f"{len(numbered & exceptions.keys())} semantic exceptions, "
        f"{len(unexplained)} new violations."
    )
    if errors:
        print(f"Split guidance: {SPLIT_GUIDANCE}")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path("."), help="repository root")
    parser.add_argument("--config", default=lean_file_policies.DEFAULT_CONFIG,
                        help="configuration path relative to the root")
    parser.add_argument("--base-ref", help="ref whose merge base fixes the debt baseline")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        policies = lean_file_policies.load(root, args.config)
        base = None
        if args.base_ref is not None:
            base = lean_file_policies.load_at_merge_base(root, args.base_ref, args.config)
            if base is None:
                print(f"Initializing the numbered debt baseline: {args.config} is absent "
                      f"from {args.base_ref}.")
    except ValueError as error:
        print(f"::error title=Numbered Lean file check failed::{error}")
        return 1
    return check_numbered_files(root, policies, None if base is None else base.numbered_debt)


if __name__ == "__main__":
    raise SystemExit(main())
