#!/usr/bin/env python3
"""Report fully qualified Lean names declared at more than one site.

Consumer counting starts from a declaration and cannot see two modules that
both declare ``Ns.foo``; this starts from the name instead. It tracks
``namespace``/``section``/``end`` and prefixes each declaration head. It is a
textual scan: ``private`` declarations are skipped (they may legally repeat),
and names built by macros or ``mutual`` blocks are not seen.

    lean_name_collisions.py [SRC_DIR ...]    # default: every *.lean under .

Exit status is 1 when a collision is found, 0 otherwise.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_KEYWORDS = (
    "theorem|lemma|def|abbrev|instance|structure|class|inductive|"
    "opaque|axiom|noncomputable def|irreducible_def"
)
_DECL = re.compile(
    r"^(?:@\[[^\]]*\]\s*)?"
    r"(?P<mods>(?:(?:private|protected|noncomputable|partial|unsafe|nonrec)\s+)*)"
    rf"(?:{_KEYWORDS})\s+(?P<name>[^\s({{\[:]+)"
)
_NAMESPACE = re.compile(r"^namespace\s+(\S+)")
_SECTION = re.compile(r"^(?:noncomputable\s+)?section(?:\s+(\S+))?\s*$")
_END = re.compile(r"^end(?:\s+(\S+))?\s*$")
_COMMENT = re.compile(r"/-.*?-/", re.DOTALL)


def declarations(path: Path) -> list[tuple[str, int]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    # Blank out block comments and docstrings, keeping line numbers.
    text = _COMMENT.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)
    scopes: list[tuple[str, int]] = []  # (kind, number of namespace parts)
    parts: list[str] = []
    found: list[tuple[str, int]] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("--", 1)[0].strip()
        if m := _NAMESPACE.match(line):
            new = m.group(1).split(".")
            parts.extend(new)
            scopes.append(("namespace", len(new)))
        elif _SECTION.match(line):
            scopes.append(("section", 0))
        elif _END.match(line) and scopes:
            _, count = scopes.pop()
            del parts[len(parts) - count:]
        elif (m := _DECL.match(line)) and "private" not in m.group("mods"):
            name = m.group("name")
            if name.startswith("_root_."):
                full = name.removeprefix("_root_.")
            else:
                full = ".".join([*parts, name])
            found.append((full, lineno))
    return found


def main() -> int:
    roots = [Path(p) for p in sys.argv[1:]] or [Path(".")]
    sites: dict[str, list[str]] = {}
    for root in roots:
        files = [root] if root.is_file() else sorted(root.rglob("*.lean"))
        for path in files:
            if ".lake" in path.parts:
                continue
            for name, lineno in declarations(path):
                sites.setdefault(name, []).append(f"{path}:{lineno}")
    collisions = {n: s for n, s in sites.items() if len(s) > 1}
    for name in sorted(collisions):
        print(name)
        for site in collisions[name]:
            print(f"  {site}")
    return 1 if collisions else 0


if __name__ == "__main__":
    sys.exit(main())
