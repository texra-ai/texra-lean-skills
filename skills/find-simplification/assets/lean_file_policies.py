"""Load the project configuration shared by the Lean file-policy checks.

The configuration is one JSON file, by default ``lean_file_policies.json`` at
the repository root; see ``lean_file_policies.example.json``. Every field is
optional:

``source_roots``
    Directories holding production Lean modules (default: every tracked file).
``excluded_roots``
    Directories inside them that no policy applies to, such as an archive.
``numbered_sequels.debt``
    Existing numbered-sequel modules. A ratchet: it may only shrink.
``numbered_sequels.semantic_exceptions``
    Paths whose trailing number is mathematical (``ZMod2``, ``Corollary41``),
    each mapped to the reason.
``oversized.max_lines``
    Line limit per Lean file (default 1000).
``oversized.known``
    Existing oversized files, reported as warnings rather than errors.
``oversized.import_only_aggregators``
    Exact import-only files exempt from the line limit.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG = "lean_file_policies.json"
DEFAULT_MAX_LINES = 1000


@dataclass(frozen=True)
class Policies:
    source_roots: tuple[str, ...] = ()
    excluded_roots: tuple[str, ...] = ()
    numbered_debt: frozenset[str] = frozenset()
    semantic_exceptions: dict[str, str] = field(default_factory=dict)
    max_lines: int = DEFAULT_MAX_LINES
    known_oversized: frozenset[str] = frozenset()
    import_only_aggregators: frozenset[str] = frozenset()

    def in_scope(self, relative: str) -> bool:
        """Whether a repository-relative POSIX path is a production path.

        A root ``R`` covers its root module ``R.lean`` as well as ``R/``.
        """
        def under(root: str) -> bool:
            root = root.rstrip("/")
            return relative in (root, f"{root}.lean") or relative.startswith(root + "/")

        if self.source_roots and not any(under(r) for r in self.source_roots):
            return False
        return not any(under(r) for r in self.excluded_roots)


def parse(text: str) -> Policies:
    """Parse a configuration file's contents, rejecting malformed fields."""
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("configuration must be a JSON object")
    numbered = data.get("numbered_sequels", {})
    oversized = data.get("oversized", {})
    policies = Policies(
        source_roots=tuple(_strings(data, "source_roots")),
        excluded_roots=tuple(_strings(data, "excluded_roots")),
        numbered_debt=frozenset(_strings(numbered, "debt")),
        semantic_exceptions=dict(numbered.get("semantic_exceptions", {})),
        max_lines=int(oversized.get("max_lines", DEFAULT_MAX_LINES)),
        known_oversized=frozenset(_strings(oversized, "known")),
        import_only_aggregators=frozenset(_strings(oversized, "import_only_aggregators")),
    )
    if not all(isinstance(v, str) for v in policies.semantic_exceptions.values()):
        raise ValueError("numbered_sequels.semantic_exceptions values must be strings")
    return policies


def _strings(section: object, key: str) -> list[str]:
    values = section.get(key, []) if isinstance(section, dict) else []
    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        raise ValueError(f"{key} must be a list of strings")
    return values


def load(root: Path, config: str = DEFAULT_CONFIG) -> Policies:
    """Load the configuration from the working tree; absent means defaults."""
    path = root / config
    return parse(path.read_text(encoding="utf-8")) if path.is_file() else Policies()


def load_at_merge_base(root: Path, base_ref: str, config: str = DEFAULT_CONFIG) -> Policies | None:
    """Load the configuration as of the merge base with *base_ref*.

    ``None`` means the configuration is absent there, as when it is first added.
    """
    merge_base = _git(root, "merge-base", "HEAD", base_ref)
    if merge_base.returncode != 0:
        raise ValueError(f"cannot find merge base with {base_ref}: {merge_base.stderr.strip()}")
    commit = merge_base.stdout.strip()
    shown = _git(root, "show", f"{commit}:{config}")
    if shown.returncode != 0:
        if "does not exist in" in shown.stderr or "exists on disk, but not in" in shown.stderr:
            return None
        raise ValueError(f"cannot read {config} at {commit}: {shown.stderr.strip()}")
    return parse(shown.stdout)


def tracked_lean_files(root: Path, policies: Policies) -> set[str]:
    """Git-tracked production ``.lean`` files, as repository-relative paths."""
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--", "*.lean"],
        check=True,
        stdout=subprocess.PIPE,
    )
    paths = result.stdout.decode("utf-8").split("\0")
    return {p for p in paths if p.endswith(".lean") and policies.in_scope(p)}


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
