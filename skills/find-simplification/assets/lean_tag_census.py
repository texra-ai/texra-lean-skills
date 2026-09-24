#!/usr/bin/env python3
"""List every declaration named by a blueprint ``\\lean{...}`` tag.

Handles the two shapes that per-line greps miss: a ``%`` line continuation
inside the braces, and a comma-separated payload naming several declarations.

    lean_tag_census.py [BLUEPRINT_DIR]           # one name per line, sorted
    lean_tag_census.py BLUEPRINT_DIR --where     # name<TAB>file:line
    lean_tag_census.py BLUEPRINT_DIR --check N   # exit 0 iff N is tagged

BLUEPRINT_DIR defaults to ``blueprint/src``.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_CONTINUATION = re.compile(r"(?<!\\)%[^\n]*\n\s*")
_LEAN_TAG = re.compile(r"\\lean\{([^}]*)\}")


def split_payload(payload: str) -> list[str]:
    """Split one ``\\lean{...}`` payload into declaration names."""
    names = (re.sub(r"\s+", "", name) for name in payload.split(","))
    return [name for name in names if name]


def census(root: Path) -> dict[str, list[str]]:
    """Map each tagged declaration to the ``file:line`` sites that tag it."""
    sites: dict[str, list[str]] = {}
    for tex in sorted(root.rglob("*.tex")):
        text = tex.read_text(encoding="utf-8", errors="replace")
        # Blank each continuation to whitespace, keeping offsets and newlines,
        # so the split name rejoins once whitespace is removed.
        text = _CONTINUATION.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)
        for match in _LEAN_TAG.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            for name in split_payload(match.group(1)):
                sites.setdefault(name, []).append(f"{tex}:{line}")
    return sites


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", nargs="?", default="blueprint/src", type=Path)
    parser.add_argument("--where", action="store_true", help="print tag sites")
    parser.add_argument("--check", metavar="NAME", help="test one declaration")
    args = parser.parse_args()
    if not args.root.is_dir():
        print(f"lean_tag_census: no directory {args.root}", file=sys.stderr)
        return 2
    sites = census(args.root)
    if args.check:
        hits = sites.get(args.check, [])
        for site in hits:
            print(site)
        return 0 if hits else 1
    for name in sorted(sites):
        if args.where:
            for site in sites[name]:
                print(f"{name}\t{site}")
        else:
            print(name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
