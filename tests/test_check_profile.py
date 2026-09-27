"""Offline tests for scripts/check_profile.py and the claims ledger.

    python -m unittest discover -s tests -v

Standard library only, like the scripts, and no network: every fetch is
replaced. Each test names the defect it keeps from coming back.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import sys
import tempfile
import tomllib
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("check_profile", ROOT / "scripts" / "check_profile.py")
assert _spec and _spec.loader
cp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cp)

SVG_NS = "{http://www.w3.org/2000/svg}"


def load_claims() -> dict:
    return tomllib.loads((ROOT / "claims.toml").read_text())


class CheckerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        cp.failures.clear()
        cp.warnings.clear()
        cp._cache.clear()

    def run_quietly(self, fn, *args) -> str:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            fn(*args)
        return out.getvalue()

    def with_readme(self, text: str) -> None:
        """Point the checker at a temporary README for this test."""
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as tmp:
            tmp.write(text)
        self.addCleanup(os.unlink, tmp.name)
        patcher = mock.patch.object(cp, "README", Path(tmp.name))
        patcher.start()
        self.addCleanup(patcher.stop)


class ReproduceNumbers(CheckerTestCase):
    """Both sides of a reproduce claim are typed by hand; the README could say
    72.4% while the reproduce step still checked 72.3%."""

    def test_one_sided_edit_is_reported(self) -> None:
        self.assertEqual(
            cp.unmatched_numbers("moved 72.4% → 89.9%", ["seed 5: 72.3% -> 89.9%"]),
            ["72.4"],
        )

    def test_numbers_count_with_multiplicity(self) -> None:
        self.assertEqual(cp.unmatched_numbers("9/10 and 9/10", ["9/10, 8/10"]), ["9"])
        self.assertEqual(cp.unmatched_numbers("9/10 and 9/10", ["9/10, 9/10"]), [])

    def test_check_claims_fails_on_one_sided_edit(self) -> None:
        self.with_readme("enabling it moved CPU utilisation 72.4% → 89.9%\n")
        cfg = {
            "owner": "Zhanyl-tech",
            "claim": [
                {
                    "id": "x",
                    "profile": "enabling it moved CPU utilisation 72.4% → 89.9%",
                    "kind": "reproduce",
                    "expect": ["compare-backfill seed 5: cpu utilization 72.3% -> 89.9%"],
                }
            ],
        }
        self.run_quietly(cp.check_claims, cfg, None)
        self.assertEqual(len(cp.failures), 1)
        self.assertIn("72.4", cp.failures[0])

    def test_every_reproduce_claim_in_the_ledger_agrees(self) -> None:
        for claim in load_claims()["claim"]:
            if claim["kind"] == "reproduce":
                with self.subTest(claim=claim["id"]):
                    self.assertEqual(cp.unmatched_numbers(claim["profile"], claim["expect"]), [])


class DefaultBranch(CheckerTestCase):
    """Readers land on each repo's default branch, so anchors and quoted
    sources must be read there even when claims.toml pins a commit."""

    def test_links_and_claims_ignore_pinned_refs(self) -> None:
        self.with_readme("[r](https://github.com/Zhanyl-tech/lab#results)\nlab says 42\n")
        cfg = {
            "owner": "Zhanyl-tech",
            "refs": {"lab": "0123456789abcdef0123456789abcdef01234567"},
            "claim": [
                {"id": "c", "profile": "lab says 42", "kind": "source", "repo": "lab", "path": "README.md", "expect": ["42"]}
            ],
        }
        refs_read: list[str] = []

        def fake_repo_file(owner, repo, ref, path, local):
            refs_read.append(ref)
            return "## Results\n42\n"

        with mock.patch.object(cp, "repo_file", fake_repo_file), mock.patch.object(cp, "fetch", return_value=(200, "")):
            self.run_quietly(cp.check_links, cfg, None)
            self.run_quietly(cp.check_claims, cfg, None)
        self.assertEqual(cp.failures, [])
        self.assertEqual(refs_read, [cp.DEFAULT_BRANCH, cp.DEFAULT_BRANCH])
        self.assertEqual(cp.DEFAULT_BRANCH, "HEAD")


class BotBlockingHosts(CheckerTestCase):
    """X answers GitHub's runners 403 for a profile that exists, which failed
    CI on a working link. Only a host's own blocking status is excused: a 404
    there is still a broken link, and a 403 from any other host still fails."""

    def check_link(self, url: str, status: int) -> tuple[list[str], list[str]]:
        cp.failures.clear()
        cp.warnings.clear()
        self.with_readme(f"[link]({url})\n")
        with mock.patch.object(cp, "fetch", return_value=(status, "")):
            self.run_quietly(cp.check_links, {"owner": "Zhanyl-tech"}, None)
        return list(cp.failures), list(cp.warnings)

    def assert_unverified(self, url: str, status: int) -> None:
        failures, warnings = self.check_link(url, status)
        self.assertEqual(failures, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn(f"HTTP {status}", warnings[0])
        self.assertIn("unverified", warnings[0])

    def assert_broken(self, url: str, status: int) -> None:
        failures, warnings = self.check_link(url, status)
        self.assertEqual(warnings, [])
        self.assertEqual(failures, [f"{url}: HTTP {status}"])

    def test_x_403_is_unverified(self) -> None:
        for url in ("https://x.com/ZhanylAbd", "https://twitter.com/ZhanylAbd", "https://www.x.com/ZhanylAbd"):
            with self.subTest(url=url):
                self.assert_unverified(url, 403)

    def test_x_404_fails(self) -> None:
        self.assert_broken("https://x.com/ZhanylAbd", 404)

    def test_linkedin_999_is_unverified(self) -> None:
        self.assert_unverified("https://www.linkedin.com/in/za-engineering/", 999)

    def test_linkedin_404_fails(self) -> None:
        # Any non-200 from LinkedIn used to be excused.
        self.assert_broken("https://www.linkedin.com/in/za-engineering/", 404)

    def test_other_host_403_fails(self) -> None:
        for url in ("https://example.com/page", "https://notx.com/ZhanylAbd", "https://x.com.example.net/"):
            with self.subTest(url=url):
                self.assert_broken(url, 403)


class ReproduceFailures(CheckerTestCase):
    """A failed reproduce run used to print only CalledProcessError and an exit
    status; the reason (schedlab's stderr) never reached the log."""

    def fake_schedlab(self, body: str) -> str:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = os.path.join(tmp.name, "schedlab")
        with open(path, "w") as f:
            f.write(f"#!{sys.executable}\nimport sys\n{body}\n")
        os.chmod(path, 0o755)
        return path

    def test_schedlab_error_reaches_the_log(self) -> None:
        schedlab = self.fake_schedlab(
            "sys.stderr.write('schedlab: error: unrecognized arguments: --compare-backfill\\n'); sys.exit(2)"
        )
        out = self.run_quietly(cp.check_reproduce, load_claims(), schedlab)
        self.assertIn("unrecognized arguments: --compare-backfill", out)
        self.assertIn("exited 2", out)
        self.assertEqual(len(cp.failures), 1)
        self.assertIn("reproduce_scheduler_claims.py exited 1", cp.failures[0])

    def test_unparseable_output_reaches_the_log(self) -> None:
        schedlab = self.fake_schedlab("print('nothing useful')")
        out = self.run_quietly(cp.check_reproduce, load_claims(), schedlab)
        self.assertIn("could not parse --compare-backfill output for seed 5", out)
        self.assertEqual(len(cp.failures), 1)

    def test_missing_binary_reaches_the_log(self) -> None:
        out = self.run_quietly(cp.check_reproduce, load_claims(), "/nonexistent/schedlab")
        self.assertIn("could not run /nonexistent/schedlab", out)
        self.assertEqual(len(cp.failures), 1)


class Ledger(unittest.TestCase):
    """The ledger itself: offline, without reading any source."""

    def test_every_profile_text_is_in_the_readme(self) -> None:
        readme = cp.normalise((ROOT / "README.md").read_text())
        for claim in load_claims()["claim"]:
            with self.subTest(claim=claim["id"]):
                self.assertIn(cp.normalise(claim["profile"]), readme)

    def test_ids_are_unique_and_kinds_known(self) -> None:
        claims = load_claims()["claim"]
        ids = [c["id"] for c in claims]
        self.assertEqual(len(ids), len(set(ids)))
        for c in claims:
            with self.subTest(claim=c["id"]):
                self.assertIn(c["kind"], {"source", "url", "reproduce"})
                self.assertTrue(c["expect"])
                if c["kind"] == "source":
                    self.assertTrue(c["repo"] and c["path"])

    def test_only_the_reproduce_job_uses_refs(self) -> None:
        # Links and claims read default branches; a pinned ref for any other
        # repo would suggest it is checked there when it is not.
        self.assertEqual(set(load_claims().get("refs", {})), {"slurm-scheduler-lab"})


class Banner(unittest.TestCase):
    """The legend says a solid edge is measured. A solid grey edge between the
    two labs once read as a measurement that does not exist."""

    def setUp(self) -> None:
        self.svg = ET.parse(ROOT / "assets" / "architecture.svg").getroot()

    def test_every_solid_line_is_a_labelled_measurement(self) -> None:
        lines = list(self.svg.iter(f"{SVG_NS}line"))
        solid = [ln for ln in lines if not ln.get("stroke-dasharray")]
        measured_labels = [
            t for t in self.svg.iter(f"{SVG_NS}text") if "measured" in (t.get("class") or "").split()
        ]
        self.assertTrue(solid)
        self.assertEqual(len(solid), len(measured_labels))
        for ln in solid:
            self.assertIn(ln.get("stroke"), {"#58a6ff", "#f5b544"}, "a solid edge must use a measured colour")

    def test_every_line_style_has_a_legend_entry(self) -> None:
        legend = " ".join("".join(t.itertext()) for t in self.svg.iter(f"{SVG_NS}text"))
        for phrase in ("solid = measured", "dashed = documented or inferred", "dotted = shared inputs", "dashed box ="):
            self.assertIn(phrase, legend)


if __name__ == "__main__":
    unittest.main()
