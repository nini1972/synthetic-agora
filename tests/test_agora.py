import os
import sys
import unittest
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agora_graph import EpistemicGraph, detect_model_family
from protocols import send_dispatch, read_inbox, GUILDS
from tools import post_epistemic_node, peer_verify_node, query_epistemic_graph, send_agent_dispatch, read_agent_inbox

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

if __name__ == "__main__":
    unittest.main()
