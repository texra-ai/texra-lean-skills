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

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lean_source import strip_lean_comments  # noqa: E402

_KEYWORDS = (
    "theorem|lemma|def|abbrev|instance|structure|class abbrev|class inductive|class|inductive|"
    "opaque|axiom|noncomputable def|irreducible_def"
)
_DECL = re.compile(
    r"^(?:@\[[^\]]*\]\s*)?"
    r"(?P<mods>(?:(?:private|protected|public|meta|noncomputable|partial|unsafe|nonrec)\s+)*)"
    rf"(?:{_KEYWORDS})\s+(?P<name>[^\s({{\[:]+)"
)
_NAMESPACE = re.compile(r"^namespace\s+(\S+)")
_SECTION = re.compile(
    r"^(?:@\[[^\]]*\]\s*)?(?:(?:public|private|meta|noncomputable)\s+)*"
    r"section(?:\s+(\S+))?\s*$"
)
_MUTUAL = re.compile(r"^mutual\s*$")
_END = re.compile(r"^end(?:\s+(\S+))?\s*$")


def declarations(path: Path) -> list[tuple[str, int]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    text, _ = strip_lean_comments(text)
    # One entry per open scope, as Lean counts them: `namespace A.B` and
    # `section A.B` open one scope per component, and `end A.B` closes as
    # many. A namespace scope carries its component; other scopes carry None.
    scopes: list[str | None] = []
    found: list[tuple[str, int]] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if m := _NAMESPACE.match(line):
            scopes.extend(m.group(1).split("."))
        elif m := _SECTION.match(line):
            scopes.extend([None] * (m.group(1).count(".") + 1 if m.group(1) else 1))
        elif _MUTUAL.match(line):
            scopes.append(None)
        elif m := _END.match(line):
            del scopes[len(scopes) - (m.group(1).count(".") + 1 if m.group(1) else 1):]
        elif (m := _DECL.match(line)) and "private" not in m.group("mods"):
            name = m.group("name")
            if name.startswith("_root_."):
                full = name.removeprefix("_root_.")
            else:
                full = ".".join([*filter(None, scopes), name])
            found.append((full, lineno))
    return found


def main() -> int:
    roots = [Path(p) for p in sys.argv[1:]] or [Path(".")]
    sites: dict[str, list[str]] = {}
    for root in roots:
        files = [root] if root.is_file() else sorted(root.rglob("*.lean"))
        for path in files:
            if ".lake" in path.relative_to(root).parts:
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
