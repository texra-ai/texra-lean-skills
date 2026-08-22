#!/usr/bin/env python3
"""Unit tests for the Lake build hotspot parser."""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import lake_build_hotspots as hotspots


class LakeBuildHotspotTests(unittest.TestCase):
    def test_parses_units_ansi_and_optional_progress_prefix(self) -> None:
        jobs = hotspots.parse_timed_jobs(
            "\n".join(
                [
                    "✔ [9622/9713] Built Example.Slow (831s)",
                    "\x1b[32m⚠ [2/3] Built Example.Fast:c.o (250ms)\x1b[0m",
                    "Replayed Example.Middle (1.5m)",
                    "✖ [3/3] Built Example.Failed (98s)",
                    "info: unrelated output",
                ]
            )
        )
        self.assertEqual(
            jobs,
            [
                hotspots.TimedJob("Example.Slow", 831.0),
                hotspots.TimedJob("Example.Failed", 98.0),
                hotspots.TimedJob("Example.Middle", 90.0),
                hotspots.TimedJob("Example.Fast:c.o", 0.25),
            ],
        )

    def test_report_is_ranked_filtered_and_limited(self) -> None:
        jobs = [
            hotspots.TimedJob("Example.A", 10.0),
            hotspots.TimedJob("Example.B", 5.0),
            hotspots.TimedJob("Example.C", 1.0),
        ]
        self.assertEqual(
            hotspots.render_tsv(jobs, threshold=5.0, limit=1),
            "seconds\tjob\n10.000\tExample.A\n",
        )

    def test_equal_timings_are_deterministic(self) -> None:
        jobs = hotspots.parse_timed_jobs(
            "[1/2] Built Example.Z (12s)\n[2/2] Built Example.A (12s)\n"
        )
        self.assertEqual([job.job for job in jobs], ["Example.A", "Example.Z"])

    def test_changed_file_gate_warns_at_twenty_five_and_fails_at_fifty(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "lake.log"
            changed = Path(directory) / "changed.txt"
            log.write_text(
                "\n".join(
                    [
                        "Built Example.Unchanged (80s)",
                        "Built Example.Warning (25s)",
                        "Built Example.TooSlow (50s)",
                        "Built LintStyle (30s)",
                        "Built Example.Σlow (26s)",
                    ]
                ),
                encoding="utf-8",
            )
            changed.write_text(
                "Example/Warning.lean\nExample/TooSlow.lean\nscripts/LintStyle.lean\n"
                "Example/Σlow.lean\nREADME.md\n",
                encoding="utf-8",
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = hotspots.main([str(log), "--changed-files-from", str(changed)])
        self.assertEqual(status, hotspots.TIMING_LIMIT_EXIT)
        self.assertEqual(
            output.getvalue(),
            "\n".join(
                [
                    "seconds\tjob",
                    "50.000\tExample.TooSlow",
                    "30.000\tLintStyle",
                    "26.000\tExample.Σlow",
                    "25.000\tExample.Warning",
                    "::error file=Example/TooSlow.lean::Example.TooSlow compiled in 50.000s "
                    "(warning at 25s, error at 50s)",
                    "::warning file=scripts/LintStyle.lean::LintStyle compiled in 30.000s "
                    "(warning at 25s, error at 50s)",
                    "::warning file=Example/Σlow.lean::Example.Σlow compiled in 26.000s "
                    "(warning at 25s, error at 50s)",
                    "::warning file=Example/Warning.lean::Example.Warning compiled in 25.000s "
                    "(warning at 25s, error at 50s)",
                    "",
                ]
            ),
        )

    def test_changed_file_gate_ignores_unmodified_slow_modules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "lake.log"
            changed = Path(directory) / "changed.txt"
            log.write_text("Built Example.Unchanged (80s)\n", encoding="utf-8")
            changed.write_text("Example/Changed.lean\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                status = hotspots.main([str(log), "--changed-files-from", str(changed)])
        self.assertEqual(status, 0)

    def test_annotations_ignore_jobs_without_a_matching_path(self) -> None:
        self.assertEqual(
            hotspots.render_github_annotations(
                [hotspots.TimedJob("Example.Unchanged", 80.0)],
                ["Example/Changed.lean"],
                warn_threshold=25.0,
                error_threshold=50.0,
            ),
            "",
        )

    def test_changed_file_gate_includes_native_facets(self) -> None:
        jobs = [hotspots.TimedJob("LintStyle:c.o", 51.0)]
        paths = ["scripts/LintStyle.lean"]
        self.assertEqual(hotspots.changed_jobs(jobs, paths), jobs)
        self.assertIn(
            "::error file=scripts/LintStyle.lean::LintStyle:c.o compiled in 51.000s",
            hotspots.render_github_annotations(jobs, paths, 25.0, 50.0),
        )


if __name__ == "__main__":
    unittest.main()
