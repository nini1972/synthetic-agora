import os
import sys
import json
import shutil
import subprocess
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import embassy_bridge as eb


def _init_local_repo(repo_dir: str, outbox_rel: str, files: dict) -> str:
    """Creates a local git repo (no network) with the given files under outbox_rel,
    commits them, and returns the commit sha. Used to test sync() against a
    fully-controlled counterpart without depending on the real GitHub repos."""
    os.makedirs(os.path.join(repo_dir, outbox_rel), exist_ok=True)
    for filename, content in files.items():
        with open(os.path.join(repo_dir, outbox_rel, filename), "w", encoding="utf-8") as f:
            f.write(content)
    subprocess.run(["git", "init", "-q", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo_dir, check=True)
    subprocess.run(
        ["git", "-c", "user.email=test@test.com", "-c", "user.name=test", "commit", "-q", "-m", "seed"],
        cwd=repo_dir, check=True,
    )
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_dir, check=True, capture_output=True, text=True)
    return result.stdout.strip()


VALID_DOSSIER = (
    "# Frontier Epistemic Dossier #1\n"
    "## Title: Test Phenomenon\n"
    "**Origin:** World A (Evolution Sandbox)\n\n"
    "### 🔬 Empirical Phenomenon:\n"
    "A sufficiently long body of text describing the phenomenon in enough detail "
    "to pass the minimum length and required-section validation checks used here.\n\n"
    "### 📦 Artifact Reference:\n"
    "* `shared_space/some_plot.png`\n"
)


class TestRewriteArtifactReferences(unittest.TestCase):
    def test_rewrites_backtick_wrapped_reference(self):
        content = "* `shared_space/foo/bar.png` and text `shared_space/baz.py` end."
        out = eb.rewrite_artifact_references(content, "abc1234567890")
        self.assertIn(
            "https://raw.githubusercontent.com/nini1972/evolution_sandbox/abc1234567890/instances/shared_space/foo/bar.png",
            out,
        )
        self.assertIn(
            "https://raw.githubusercontent.com/nini1972/evolution_sandbox/abc1234567890/instances/shared_space/baz.py",
            out,
        )

    def test_leaves_non_backtick_reference_untouched(self):
        content = "See shared_space/foo.png (no backticks) for details."
        out = eb.rewrite_artifact_references(content, "abc123")
        self.assertEqual(content, out)

    def test_does_not_span_across_newlines_on_unmatched_backtick(self):
        # An unmatched opening backtick must not cause the match to swallow the
        # rest of the document across multiple lines.
        content = "`shared_space/unterminated\nsecond line\nthird line"
        out = eb.rewrite_artifact_references(content, "abc123")
        self.assertEqual(content, out, "Unmatched backtick must not trigger a cross-line rewrite")


class TestIsValidDossier(unittest.TestCase):
    def test_accepts_well_formed_dossier(self):
        self.assertTrue(eb.is_valid_dossier(VALID_DOSSIER))

    def test_accepts_chronicler_dossier_style(self):
        chronicler_doc = (
            "# DOSSIER: Chronicler-2026-09-16-cml-entropy-scaling\n"
            "**Author:** Chronicler\n"
            "**Topic:** Spatiotemporal Entropy Scaling\n\n"
            "### Summary\n"
            "Empirical study comparing spatiotemporal entropy in 1D Coupled Map Lattices.\n\n"
            "### Findings\n"
            "- Below-Adler-Ceiling: Mean Spatial Shannon Entropy = 1.77\n"
            "- Above-Adler-Ceiling: Mean Spatial Shannon Entropy = 3.08\n\n"
            "### Methodology\n"
            "- Lattice: 1D, N=100, coupling: 0.1, time-steps: 200\n"
        )
        self.assertTrue(eb.is_valid_dossier(chronicler_doc))

    def test_accepts_minimax_empirical_comparison_style(self):
        minimax_doc = (
            "# 📨 Frontier Epistemic Dossier\n"
            "## Title: Response to EMP-058 — Mechanism B Has Internal Sub-Structure\n\n"
            "## 📜 Discovery\n"
            "The Agora independent test of Logistic Map against Adler Ceiling confirms Mechanism B.\n\n"
            "## 🔬 Empirical Comparison\n"
            "| Source | Sampling | band_frac |\n"
            "| Agora EMP-058 | r in [3.5, 4.0] | 0.5306 |\n\n"
            "## 📐 Refined Mechanism Taxonomy\n"
            "I propose extending my original three-mechanism model.\n\n"
            "## 🔬 Falsifiability\n"
            "Hypothesis is falsifiable if band_frac was independent of r-sampling.\n"
        )
        self.assertTrue(eb.is_valid_dossier(minimax_doc))

    def test_accepts_method_singular_and_results_style(self):
        method_doc = (
            "# 📨 Frontier Epistemic Dossier (Update to EMP-058)\n"
            "## Title: Empirical Monotonicity of Logistic bf(r_min)\n\n"
            "## 📜 New Finding\n"
            "Tested whether bf(r_min) is monotonic in r_min for logistic map.\n\n"
            "## 🔬 Method\n"
            "- Sweep r_min in [2.5, 3.95], compute mean and max bf.\n\n"
            "## 📊 Results\n"
            "| r_min | Mean bf |\n"
            "| 2.5 | 0.633 |\n\n"
            "## 🔬 Falsifiability\n"
            "Monotonicity hypothesis would be falsified if any r_min pair showed inversion.\n"
        )
        self.assertTrue(eb.is_valid_dossier(method_doc))

    def test_rejects_too_short_content(self):
        self.assertFalse(eb.is_valid_dossier("short"))

    def test_rejects_missing_required_headers(self):
        self.assertFalse(eb.is_valid_dossier("A" * 300))


class TestLedgerRoundTrip(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="embassy_ledger_test_")
        self._orig_ledger_path = eb.LEDGER_PATH
        self._orig_embassy_dir = eb.EMBASSY_DIR
        eb.EMBASSY_DIR = self.tmp_dir
        eb.LEDGER_PATH = os.path.join(self.tmp_dir, ".sync_ledger.json")

    def tearDown(self):
        eb.LEDGER_PATH = self._orig_ledger_path
        eb.EMBASSY_DIR = self._orig_embassy_dir
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_round_trip(self):
        ledger = {"imported": [{"filename": "a.md", "sha256": "abc"}], "exported": []}
        eb.save_ledger(ledger)
        loaded = eb.load_ledger()
        self.assertEqual(loaded, ledger)

    def test_malformed_shape_falls_back_to_empty(self):
        with open(eb.LEDGER_PATH, "w", encoding="utf-8") as f:
            json.dump({"imported": "not-a-list"}, f)
        loaded = eb.load_ledger()
        self.assertEqual(loaded, {"imported": [], "exported": []})

    def test_missing_sha256_entries_are_ignored_by_sync_dedup_logic(self):
        with open(eb.LEDGER_PATH, "w", encoding="utf-8") as f:
            json.dump({"imported": [{"filename": "a.md"}], "exported": []}, f)
        loaded = eb.load_ledger()
        hashes = {e["sha256"] for e in loaded.get("imported", []) if isinstance(e, dict) and "sha256" in e}
        self.assertEqual(hashes, set())


class TestSyncAgainstLocalFixtureRepo(unittest.TestCase):
    """Exercises sync() end-to-end against a fully local (no network) git repo,
    covering symlink rejection, dedup, and collision-archiving in one place."""

    def setUp(self):
        self.base_dir = tempfile.mkdtemp(prefix="embassy_sync_test_")
        self.fixture_repo = os.path.join(self.base_dir, "fixture_repo")
        self.embassy_dir = os.path.join(self.base_dir, "embassy")

        self._orig = {
            "COUNTERPART_REPO_URL": eb.COUNTERPART_REPO_URL,
            "EMBASSY_DIR": eb.EMBASSY_DIR,
            "INBOX_DIR": eb.INBOX_DIR,
            "REJECTED_DIR": eb.REJECTED_DIR,
            "SUPERSEDED_DIR": eb.SUPERSEDED_DIR,
            "LEDGER_PATH": eb.LEDGER_PATH,
        }
        eb.COUNTERPART_REPO_URL = self.fixture_repo
        eb.EMBASSY_DIR = self.embassy_dir
        eb.INBOX_DIR = os.path.join(self.embassy_dir, "inbox")
        eb.REJECTED_DIR = os.path.join(self.embassy_dir, "rejected")
        eb.SUPERSEDED_DIR = os.path.join(self.embassy_dir, "superseded")
        eb.LEDGER_PATH = os.path.join(self.embassy_dir, ".sync_ledger.json")

    def tearDown(self):
        for key, value in self._orig.items():
            setattr(eb, key, value)
        shutil.rmtree(self.base_dir, ignore_errors=True)

    def _seed(self, files: dict) -> None:
        _init_local_repo(self.fixture_repo, eb.COUNTERPART_OUTBOX_REL, files)

    def test_imports_valid_dossier_and_is_idempotent(self):
        self._seed({"DOSSIER_001_TEST.md": VALID_DOSSIER})
        self.assertTrue(eb.sync())
        inbox_files = os.listdir(eb.INBOX_DIR)
        self.assertIn("DOSSIER_001_TEST.md", inbox_files)

        # Second run against the exact same commit must not duplicate or re-archive.
        self.assertTrue(eb.sync())
        self.assertFalse(os.path.exists(eb.SUPERSEDED_DIR), "No collision should occur on an unchanged re-sync")

    def test_rejects_malformed_candidate_with_notice_banner(self):
        self._seed({"DOSSIER_002_BAD.md": "not a real dossier, far too short and missing headers " * 5})
        self.assertTrue(eb.sync())
        rejected_files = os.listdir(eb.REJECTED_DIR)
        self.assertIn("DOSSIER_002_BAD.md", rejected_files)
        with open(os.path.join(eb.REJECTED_DIR, "DOSSIER_002_BAD.md"), encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Untrusted external content notice", content)

    def test_rejects_symlink_candidate_without_reading_target(self):
        self._seed({"DOSSIER_003_OK.md": VALID_DOSSIER})
        outside_secret = os.path.join(self.base_dir, "secret.txt")
        with open(outside_secret, "w", encoding="utf-8") as f:
            f.write("TOP SECRET - should never be read or committed")

        outbox_path = os.path.join(self.fixture_repo, eb.COUNTERPART_OUTBOX_REL)
        symlink_path = os.path.join(outbox_path, "DOSSIER_004_SYMLINK.md")
        try:
            os.symlink(outside_secret, symlink_path)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks require elevated privileges on this platform")

        subprocess.run(["git", "add", "-A"], cwd=self.fixture_repo, check=True)
        subprocess.run(
            ["git", "-c", "user.email=test@test.com", "-c", "user.name=test", "commit", "-q", "-m", "add symlink"],
            cwd=self.fixture_repo, check=True,
        )

        self.assertTrue(eb.sync())
        inbox_files = os.listdir(eb.INBOX_DIR)
        self.assertIn("DOSSIER_003_OK.md", inbox_files)
        self.assertNotIn("DOSSIER_004_SYMLINK.md", inbox_files)
        self.assertNotIn(
            "DOSSIER_004_SYMLINK.md", rejected_files,
            "Symlink target content must never be read into rejected/ either"
        )


class TestGateAccessionNumbering(unittest.TestCase):
    def test_preserves_canonical_number(self):
        inbox_fn, acc_id, stamped = eb.assign_gate_accession(
            "DOSSIER_002_THOMAS_CHAOS.md",
            VALID_DOSSIER,
            accession_num=10,
        )
        self.assertEqual(inbox_fn, "DOSSIER_002_THOMAS_CHAOS.md")
        self.assertEqual(acc_id, "DOSSIER-002")
        self.assertIn("Gate Accession: DOSSIER-002", stamped)

    def test_assigns_sequential_number_to_unsequenced_dossier(self):
        inbox_fn, acc_id, stamped = eb.assign_gate_accession(
            "DOSSIER-minimax_m3-2026-09-06-substrate-emergence-families.md",
            VALID_DOSSIER,
            accession_num=4,
        )
        self.assertEqual(inbox_fn, "DOSSIER_004_minimax_m3_2026_09_06_substrate_emergence_families.md")
        self.assertEqual(acc_id, "DOSSIER-004")
        self.assertIn("Frontier Epistemic Dossier #004 (Gate Accession: DOSSIER-004)", stamped)
        self.assertIn("**Original Source Filename:** `DOSSIER-minimax_m3-2026-09-06-substrate-emergence-families.md`", stamped)

    def test_computes_next_accession_number_from_ledger_and_inbox(self):
        ledger = {
            "last_accession_number": 3,
            "imported": [
                {"filename": "DOSSIER_001_A.md", "accession_number": 1},
                {"filename": "DOSSIER_002_B.md", "accession_number": 2},
                {"filename": "DOSSIER_003_C.md", "accession_number": 3},
            ]
        }
        next_num = eb.get_next_dossier_accession_number(ledger, "/nonexistent/dir")
        self.assertEqual(next_num, 4)


class TestRescueRejectedFiles(unittest.TestCase):
    def setUp(self):
        self.base_dir = tempfile.mkdtemp(prefix="embassy_rescue_test_")
        self.inbox_dir = os.path.join(self.base_dir, "inbox")
        self.rejected_dir = os.path.join(self.base_dir, "rejected")
        self.ledger_path = os.path.join(self.base_dir, ".sync_ledger.json")

        self._orig = {
            "INBOX_DIR": eb.INBOX_DIR,
            "REJECTED_DIR": eb.REJECTED_DIR,
            "LEDGER_PATH": eb.LEDGER_PATH,
        }
        eb.INBOX_DIR = self.inbox_dir
        eb.REJECTED_DIR = self.rejected_dir
        eb.LEDGER_PATH = self.ledger_path
        os.makedirs(self.inbox_dir, exist_ok=True)
        os.makedirs(self.rejected_dir, exist_ok=True)

    def tearDown(self):
        for key, value in self._orig.items():
            setattr(eb, key, value)
        shutil.rmtree(self.base_dir, ignore_errors=True)

    def test_rescues_valid_dossier_from_rejected(self):
        # Place a previously rejected file with untrusted notice banner
        content_with_banner = (
            VALID_DOSSIER +
            "\n\n---\n> ⚠️ **Untrusted external content notice:** This document was imported verbatim..."
        )
        rejected_file = os.path.join(self.rejected_dir, "DOSSIER-test-rescue.md")
        with open(rejected_file, "w", encoding="utf-8") as f:
            f.write(content_with_banner)

        ledger = {"last_accession_number": 5, "imported": [], "exported": []}
        imported_hashes = set()

        rescued = eb.rescue_rejected_files(ledger, imported_hashes)
        self.assertEqual(rescued, 1)
        self.assertFalse(os.path.exists(rejected_file), "Rescued file must be removed from rejected/")

        # Verify imported into inbox
        inbox_files = os.listdir(self.inbox_dir)
        self.assertIn("DOSSIER_006_test_rescue.md", inbox_files)
        self.assertEqual(ledger["last_accession_number"], 6)


if __name__ == "__main__":
    unittest.main()
