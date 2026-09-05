import os
import sys
import unittest
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agora_graph import EpistemicGraph, detect_model_family, get_shared_agora_dir
from protocols import send_dispatch, read_inbox, GUILDS
from tools import post_epistemic_node, peer_verify_node, query_epistemic_graph, send_agent_dispatch, read_agent_inbox
from embassy import export_treaty_to_embassy

class TestSyntheticAgora(unittest.TestCase):
    def setUp(self):
        self.graph = EpistemicGraph()

    def test_model_family_detection(self):
        self.assertEqual(detect_model_family("claude_haiku"), "anthropic")
        self.assertEqual(detect_model_family("gemini_3_1_flash_lite"), "google")
        self.assertEqual(detect_model_family("llama_4_scout"), "meta")
        self.assertEqual(detect_model_family("kimi_code"), "moonshot")
        self.assertEqual(detect_model_family("deepseek_v4_flash"), "deepseek")
        self.assertEqual(detect_model_family("minimax_m3"), "minimax")

    def test_epistemic_dag_and_anti_echo_quorum(self):
        # 1. Post a hypothesis by Google model
        node = self.graph.post_node(
            title="Non-linear Lattice Diffusion Invariant",
            node_type="hypothesis",
            author_instance="gemini_3_1_flash_lite",
            summary="Entropy flux stays bounded under non-linear coupling.",
            tags=["entropy", "lattice"],
            confidence=0.85
        )
        self.assertTrue(node["id"].startswith("HYP-"))
        self.assertEqual(node["status"], "UNVERIFIED_HYPOTHESIS")
        self.assertEqual(node["author_family"], "google")

        # 2. Same-family endorsement (Google) -> should not reach CANON_VERIFIED alone (anti-echo)
        node_after_echo = self.graph.peer_verify(
            node_id=node["id"],
            verifier_instance="gemini_pro",
            verdict="endorse",
            critique_notes="Verified analytically by sibling model.",
            confidence=0.9
        )
        self.assertEqual(node_after_echo["status"], "UNDER_REVIEW")

        # 3. Cross-family endorsement by Anthropic model (Claude) -> triggers quorum consensus!
        node_canon = self.graph.peer_verify(
            node_id=node["id"],
            verifier_instance="claude_haiku",
            verdict="endorse",
            critique_notes="Independent numerical replication successful.",
            confidence=0.92
        )
        self.assertEqual(node_canon["status"], "CANON_VERIFIED")

    def test_dispatches_and_inbox(self):
        os.environ["ACTIVE_INSTANCE"] = "claude_haiku"
        
        # Send dispatch to Llama
        disp = send_dispatch(
            sender_instance="claude_haiku",
            recipient_instance_or_guild="llama_4_scout",
            subject="Empirical Test Request for HYP-001",
            body="Could you run a 50k parameter sweep on the boundary condition?",
            reference_node_id="HYP-001",
            action_requested="replicate"
        )
        self.assertTrue(disp["dispatch_id"].startswith("disp_"))

        # Switch context to Llama and read inbox
        os.environ["ACTIVE_INSTANCE"] = "llama_4_scout"
        inbox = read_inbox("llama_4_scout", unread_only=True)
        self.assertTrue(any(d["subject"] == "Empirical Test Request for HYP-001" for d in inbox))

    def test_export_treaty_to_embassy_requires_canon_verified(self):
        node = self.graph.post_node(
            title="Unripe Hypothesis",
            node_type="hypothesis",
            author_instance="gemini_3_1_flash_lite",
            summary="Not yet verified.",
        )
        result = export_treaty_to_embassy(node["id"])
        self.assertIn("Error", result)
        self.assertIn("not CANON_VERIFIED", result)

    def test_export_treaty_to_embassy_writes_file_once(self):
        node = self.graph.post_node(
            title="Embassy Export Test Invariant",
            node_type="hypothesis",
            author_instance="gemini_3_1_flash_lite",
            summary="A test invariant for embassy export.",
            confidence=0.85,
        )
        self.graph.peer_verify(
            node_id=node["id"], verifier_instance="gemini_pro",
            verdict="endorse", critique_notes="ok", confidence=0.9,
        )
        verified = self.graph.peer_verify(
            node_id=node["id"], verifier_instance="claude_haiku",
            verdict="endorse", critique_notes="ok", confidence=0.9,
        )
        self.assertEqual(verified["status"], "CANON_VERIFIED")

        result = export_treaty_to_embassy(node["id"], "DOSSIER-evosandbox-2026-01-01-test.md")
        self.assertIn("Successfully exported", result)

        outbox_dir = os.path.join(get_shared_agora_dir(), "embassy", "outbox")
        matches = [f for f in os.listdir(outbox_dir) if node["id"].lower() in f.lower()]
        self.assertTrue(matches, "Expected a treaty file matching the node id in embassy/outbox/")
        self.assertEqual(len(matches), 1, "Expected exactly one treaty file for this node")

        # Second export attempt, WITH the file still present, must be a true idempotent
        # no-op -- it must not create a duplicate or second file.
        second_result = export_treaty_to_embassy(node["id"])
        self.assertIn("already exported", second_result)
        matches_after = [f for f in os.listdir(outbox_dir) if node["id"].lower() in f.lower()]
        self.assertEqual(matches_after, matches, "Re-export with file present must not alter or duplicate it")

        for f in matches_after:
            os.remove(os.path.join(outbox_dir, f))

    def test_export_treaty_to_embassy_self_heals_when_file_missing(self):
        # If the exported_to_embassy flag is set but the treaty file was deleted
        # (accidental removal, cleanup, etc.), export must self-heal by re-creating
        # the file rather than permanently trusting the stale flag.
        node = self.graph.post_node(
            title="Self-Healing Export Invariant",
            node_type="hypothesis",
            author_instance="gemini_3_1_flash_lite",
            summary="Tests self-healing when the treaty file goes missing.",
            confidence=0.85,
        )
        self.graph.peer_verify(
            node_id=node["id"], verifier_instance="gemini_pro",
            verdict="endorse", critique_notes="ok", confidence=0.9,
        )
        self.graph.peer_verify(
            node_id=node["id"], verifier_instance="claude_haiku",
            verdict="endorse", critique_notes="ok", confidence=0.9,
        )

        first_result = export_treaty_to_embassy(node["id"])
        self.assertIn("Successfully exported", first_result)

        outbox_dir = os.path.join(get_shared_agora_dir(), "embassy", "outbox")
        matches = [f for f in os.listdir(outbox_dir) if node["id"].lower() in f.lower()]
        self.assertTrue(matches)
        for f in matches:
            os.remove(os.path.join(outbox_dir, f))

        # File is now missing even though the node still says exported_to_embassy=True.
        second_result = export_treaty_to_embassy(node["id"])
        self.assertIn("Successfully exported", second_result, "Must self-heal and recreate the missing file")

        matches_after = [f for f in os.listdir(outbox_dir) if node["id"].lower() in f.lower()]
        self.assertTrue(matches_after)
        for f in matches_after:
            os.remove(os.path.join(outbox_dir, f))

    def test_export_treaty_to_embassy_credits_author_family_like_quorum_does(self):
        # Regression test: EpistemicGraph._evaluate_quorum credits the author's own
        # family toward the >=2 distinct family requirement when confidence >= 0.8.
        # Two endorsements from the SAME family (different from the author's) should
        # therefore still be enough to reach CANON_VERIFIED, and export must agree.
        node = self.graph.post_node(
            title="Author-Credited Quorum Invariant",
            node_type="hypothesis",
            author_instance="gemini_3_1_flash_lite",  # google
            summary="Tests the author-family quorum credit edge case.",
            confidence=0.85,
        )
        self.graph.peer_verify(
            node_id=node["id"], verifier_instance="claude_haiku",  # anthropic
            verdict="endorse", critique_notes="ok", confidence=0.9,
        )
        verified = self.graph.peer_verify(
            node_id=node["id"], verifier_instance="claude_sonnet",  # anthropic (same family as above)
            verdict="endorse", critique_notes="ok", confidence=0.9,
        )
        self.assertEqual(verified["status"], "CANON_VERIFIED")

        result = export_treaty_to_embassy(node["id"])
        self.assertIn("Successfully exported", result, "Export must not refuse a node the graph itself ratified")

        outbox_dir = os.path.join(get_shared_agora_dir(), "embassy", "outbox")
        matches = [f for f in os.listdir(outbox_dir) if node["id"].lower() in f.lower()]
        self.assertTrue(matches)

        # The rendered treaty text must not overstate cross-family endorsement: both
        # actual endorsers here are anthropic, so it must not claim the endorsements
        # themselves span distinct lineages -- only that the quorum rule (which credits
        # the author's family) was satisfied.
        with open(os.path.join(outbox_dir, matches[0]), "r", encoding="utf-8") as f:
            treaty_text = f.read()
        self.assertIn("credited toward this quorum", treaty_text)
        self.assertIn("from anthropic lineage(s)", treaty_text)

        for f in matches:
            os.remove(os.path.join(outbox_dir, f))

if __name__ == "__main__":
    unittest.main()
