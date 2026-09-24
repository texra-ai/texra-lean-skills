#!/usr/bin/env python3
"""Regression tests for lean_name_collisions.py and lean_tag_census.py.

    python3 test_find_simplification_scripts.py
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lean_name_collisions  # noqa: E402
import lean_tag_census  # noqa: E402


def _names(source: str) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "X.lean"
        path.write_text(source, encoding="utf-8")
        return [name for name, _ in lean_name_collisions.declarations(path)]


class NameCollisionTests(unittest.TestCase):
    def test_nested_namespace_closed_one_component_at_a_time(self) -> None:
        source = (
            "namespace P.Q.R\ntheorem x : True := trivial\nend R\n"
            "theorem x : True := trivial\nend P.Q\n"
        )
        self.assertEqual(_names(source), ["P.Q.R.x", "P.Q.x"])

    def test_module_system_sections_and_mutual_blocks(self) -> None:
        source = (
            "@[expose] public section\npublic meta section\nnamespace A\n"
            "mutual\ndef m : Nat := 0\nend\ndef y := 1\nend A\nend\nend\n"
            "def z := 2\n"
        )
        self.assertEqual(_names(source), ["A.m", "A.y", "z"])

    def test_nested_block_comments_hide_example_code(self) -> None:
        source = (
            "/-! Example:\n```\n/-- inner doc -/\ndef hidden := 0\n```\n-/\n"
            "def shown := 1\n"
        )
        self.assertEqual(_names(source), ["shown"])

    def test_class_abbrev_private_protected_and_root(self) -> None:
        source = (
            "namespace A\nclass abbrev C : Prop := True\nclass inductive I : Prop\n"
            "private lemma p : True := trivial\nprotected def q := 1\n"
            "theorem _root_.r : True := trivial\nend A\n"
        )
        self.assertEqual(_names(source), ["A.C", "A.I", "A.q", "r"])


class TagCensusTests(unittest.TestCase):
    def test_continuation_and_comma_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "ch.tex").write_text(
                "\\lean{Foo.BarData.%\n    exists_baz, Foo.qux}\n"
                "50\\% of \\lean{Foo.after_percent}\n",
                encoding="utf-8",
            )
            sites = lean_tag_census.census(Path(tmp))
        self.assertEqual(
            sorted(sites), ["Foo.BarData.exists_baz", "Foo.after_percent", "Foo.qux"]
        )
        self.assertTrue(sites["Foo.after_percent"][0].endswith(":3"))


if __name__ == "__main__":
    unittest.main()
