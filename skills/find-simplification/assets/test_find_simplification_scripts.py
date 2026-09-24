#!/usr/bin/env python3
"""Regression tests for the find-simplification asset scripts.

    python3 test_find_simplification_scripts.py
"""
from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_numbered_lean_files as numbered  # noqa: E402
import check_oversized_lean_files as oversized  # noqa: E402
import lean_file_policies  # noqa: E402
import lean_name_collisions  # noqa: E402
import lean_tag_census  # noqa: E402
from lean_file_policies import Policies  # noqa: E402
from lean_source import pure_import_modules  # noqa: E402


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


class GitRepoTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def track(self, relative: str, source: str = "def x := 1\n") -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", relative], check=True)

    def commit(self, message: str) -> str:
        subprocess.run(
            ["git", "-C", str(self.root), "-c", "user.name=Test",
             "-c", "user.email=test@example.com", "commit", "-qm", message],
            check=True,
        )
        return subprocess.run(
            ["git", "-C", str(self.root), "rev-parse", "HEAD"],
            check=True, stdout=subprocess.PIPE, text=True,
        ).stdout.strip()

    def capture(self, function, *args: object) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = function(*args)
        return status, output.getvalue()


class NumberedLeanFilePolicyTests(GitRepoTest):
    ROOTS = {"source_roots": ("P",), "excluded_roots": ("P/Archive",)}

    def check(self, debt=frozenset(), exceptions=None, base_debt=None) -> tuple[int, str]:
        policies = Policies(**self.ROOTS, numbered_debt=frozenset(debt),
                            semantic_exceptions=exceptions or {})
        return self.capture(numbered.check_numbered_files, self.root, policies, base_debt)

    def test_new_numbered_production_file_fails_with_guidance(self) -> None:
        self.track("P/Proof2.lean")
        status, output = self.check()
        self.assertEqual(status, 1)
        self.assertIn("new numbered-sequel filename", output)
        self.assertIn("Basic.lean", output)

    def test_existing_debt_is_allowed(self) -> None:
        self.track("P/Proof2.lean")
        status, output = self.check({"P/Proof2.lean"})
        self.assertEqual(status, 0)
        self.assertIn("1 numbered debt", output)

    def test_new_debt_entry_fails_against_base(self) -> None:
        self.track("P/Proof2.lean")
        status, output = self.check({"P/Proof2.lean"}, base_debt=frozenset())
        self.assertEqual(status, 1)
        self.assertIn("this list may only shrink", output)

    def test_ratchet_reads_config_at_merge_base(self) -> None:
        old, new = "P/Old2.lean", "P/New3.lean"
        self.track(old)
        config = {"source_roots": ["P"], "numbered_sequels": {"debt": [old]}}
        self.track("lean_file_policies.json", json.dumps(config))
        base = self.commit("baseline")
        self.track(new)
        config["numbered_sequels"]["debt"].append(new)
        self.track("lean_file_policies.json", json.dumps(config))
        self.commit("proposed addition")
        self.track("P/Unrelated.lean")
        self.commit("later commit in the same push")

        policies = lean_file_policies.load(self.root)
        against_base = lean_file_policies.load_at_merge_base(self.root, base)
        status, output = self.capture(
            numbered.check_numbered_files, self.root, policies, against_base.numbered_debt)
        self.assertEqual(status, 1)
        self.assertIn(f"{new}: added to the numbered debt list", output)

        against_parent = lean_file_policies.load_at_merge_base(self.root, "HEAD^")
        status, _ = self.capture(
            numbered.check_numbered_files, self.root, policies, against_parent.numbered_debt)
        self.assertEqual(status, 0)

    def test_config_absent_at_base_initializes(self) -> None:
        self.track("P/A.lean")
        base = self.commit("before the config")
        self.assertIsNone(lean_file_policies.load_at_merge_base(self.root, base))

    def test_removing_debt_entry_is_allowed(self) -> None:
        self.track("P/Proof2.lean")
        status, _ = self.check({"P/Proof2.lean"},
                               base_debt=frozenset({"P/Proof2.lean", "P/Removed3.lean"}))
        self.assertEqual(status, 0)

    def test_stale_debt_entry_fails_so_list_shrinks(self) -> None:
        status, output = self.check({"P/Gone2.lean"})
        self.assertEqual(status, 1)
        self.assertIn("stale debt entry", output)

    def test_documented_semantic_exception_is_allowed(self) -> None:
        self.track("P/ZMod2.lean")
        status, output = self.check(exceptions={"P/ZMod2.lean": "Part of the type name."})
        self.assertEqual(status, 0)
        self.assertIn("1 semantic exceptions", output)

    def test_empty_semantic_explanation_fails(self) -> None:
        self.track("P/ZMod2.lean")
        status, output = self.check(exceptions={"P/ZMod2.lean": "  "})
        self.assertEqual(status, 1)
        self.assertIn("has no explanation", output)

    def test_excluded_untracked_and_out_of_root_files_are_out_of_scope(self) -> None:
        self.track("P/Archive/Legacy2.lean")
        self.track("scripts/Probe2.lean")
        (self.root / "P").mkdir(exist_ok=True)
        (self.root / "P" / "Scratch2.lean").write_text("def s := 2\n", encoding="utf-8")
        status, output = self.check()
        self.assertEqual(status, 0)
        self.assertIn("0 numbered debt", output)


class OversizedLeanFilePolicyTests(GitRepoTest):
    def check(self, **fields: object) -> tuple[int, str]:
        policies = Policies(max_lines=10, **fields)
        return self.capture(oversized.check_files, self.root, policies)

    def test_oversized_module_fails_with_split_guidance(self) -> None:
        self.track("P/Huge.lean", "def x := 1\n" * 11)
        status, output = self.check()
        self.assertEqual(status, 1)
        self.assertIn("concept-named modules", output)

    def test_known_oversized_warns_and_stale_known_fails(self) -> None:
        self.track("P/Huge.lean", "def x := 1\n" * 11)
        status, output = self.check(known_oversized=frozenset({"P/Huge.lean"}))
        self.assertEqual(status, 0)
        self.assertIn("Known oversized Lean file", output)
        self.track("P/Huge.lean", "def x := 1\n")
        status, output = self.check(known_oversized=frozenset({"P/Huge.lean"}))
        self.assertEqual(status, 1)
        self.assertIn("Stale known oversized entry", output)

    def test_exact_import_only_aggregator_is_exempt(self) -> None:
        source = "/- generated\n  /- nested -/\n-/\nmodule\n" + (
            "public import P.Basic -- note\n" * 11)
        self.track("P.lean", source)
        status, output = self.check(import_only_aggregators=frozenset({"P.lean"}))
        self.assertEqual(status, 0)
        self.assertIn("validated 1 of 1", output)

    def test_import_only_file_needs_exact_registration(self) -> None:
        self.track("P/All.lean", "import P.Basic\n" * 11)
        status, output = self.check()
        self.assertEqual(status, 1)
        self.assertIn("Oversized Lean file", output)

    def test_aggregator_with_declaration_is_rejected_even_below_limit(self) -> None:
        self.track("P.lean", "import P.Basic\ndef notAnAggregator := 1\n")
        status, output = self.check(import_only_aggregators=frozenset({"P.lean"}))
        self.assertEqual(status, 1)
        self.assertIn("contains non-import Lean code", output)

    def test_missing_aggregator_exemption_is_rejected(self) -> None:
        status, output = self.check(import_only_aggregators=frozenset({"Missing.lean"}))
        self.assertEqual(status, 1)
        self.assertIn("must name a tracked, in-scope .lean file", output)


class LeanSourceTests(unittest.TestCase):
    def test_import_forms(self) -> None:
        modules, error = pure_import_modules(
            "module\nimport A\npublic import B.C\nmeta import D\n"
            "public meta import E\nimport all F\n")
        self.assertIsNone(error)
        self.assertEqual(modules, ["A", "B.C", "D", "E", "F"])

    def test_invalid_segment_and_unterminated_comment(self) -> None:
        self.assertIn("non-import", pure_import_modules("import P.0Bad\n")[1])
        self.assertIn("unterminated", pure_import_modules("import P\n/- open\n")[1])

    def test_config_rejects_malformed_fields(self) -> None:
        with self.assertRaises(ValueError):
            lean_file_policies.parse('{"source_roots": "P"}')


if __name__ == "__main__":
    unittest.main()
