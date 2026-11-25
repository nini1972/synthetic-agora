import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llm_client import generate_next_action, get_openrouter_extra_body


class TestAgoraLLMClient(unittest.TestCase):
    def test_get_openrouter_extra_body_blocks_minimax_providers(self):
        self.assertEqual(
            get_openrouter_extra_body("openrouter/minimax/minimax-m3"),
            {"provider": {"ignore": ["minimax", "novita", "streamlake", "atlas-cloud"]}},
        )
        self.assertIsNone(get_openrouter_extra_body("openrouter/deepseek/deepseek-v4.1-flash"))
        self.assertIsNone(get_openrouter_extra_body("runpod/Ninitje/InvariantMind-Worker-7B-Merged"))

    @patch("llm_client.completion")
    def test_generate_next_action_injects_blocklist_only_for_minimax(self, mock_completion):
        mock_completion.return_value = type("Resp", (), {
            "choices": [type("Choice", (), {
                "message": type("Msg", (), {"content": "Thinking...", "tool_calls": None})()
            })()]
        })()

        prev_active = os.environ.get("ACTIVE_INSTANCE")
        try:
            os.environ["ACTIVE_INSTANCE"] = "minimax_m3"
            generate_next_action("prompt", [], [])
            minimax_kwargs = mock_completion.call_args[1]
            self.assertEqual(minimax_kwargs["model"], "openrouter/minimax/minimax-m3")
            self.assertEqual(
                minimax_kwargs["extra_body"],
                {"provider": {"ignore": ["minimax", "novita", "streamlake", "atlas-cloud"]}},
            )

            mock_completion.reset_mock()
            os.environ["ACTIVE_INSTANCE"] = "deepseek_v4_flash"
            generate_next_action("prompt", [], [])
            ds_kwargs = mock_completion.call_args[1]
            self.assertEqual(ds_kwargs["model"], "openrouter/deepseek/deepseek-v4.1-flash")
            self.assertNotIn("extra_body", ds_kwargs)
        finally:
            if prev_active is None:
                os.environ.pop("ACTIVE_INSTANCE", None)
            else:
                os.environ["ACTIVE_INSTANCE"] = prev_active

    def test_submit_world_c_job_rejects_syntax_error_preflight(self):
        import tempfile
        import tools

        with tempfile.TemporaryDirectory() as tmp_shared, tempfile.TemporaryDirectory() as tmp_ws:
            with patch("tools.get_shared_agora_dir", return_value=tmp_shared), patch("tools.get_workspace_dir", return_value=tmp_ws):
                out = tools.submit_world_c_job("Broken f-string", "print(f'R={1.0\n')")
            self.assertIn("Preflight SyntaxError", out)
            self.assertEqual(os.listdir(tmp_shared), [])

    def test_format_messages_for_runpod_surfaces_commons_digest_and_mentions(self):
        from llm_client import format_messages_for_runpod

        sys_p = (
            "You are Invariant Mind.\n\n"
            "=== 💬 COLLEAGUE COMMONS DIGEST ===\n"
            "- @invariant_mind please endorse HYP-164 [unread]"
        )
        msgs = format_messages_for_runpod(sys_p, [{"role": "user", "content": "Next tick"}], [])
        self.assertNotIn("COLLEAGUE COMMONS DIGEST", msgs[0]["content"])
        self.assertIn("=== 💬 COLLEAGUE COMMONS DIGEST ===", msgs[-1]["content"])
        self.assertIn("@invariant_mind", msgs[-1]["content"])
        self.assertIn("[COLLEAGUE MENTIONS WAITING]", msgs[-1]["content"])

    def test_format_messages_for_runpod_filters_markdown_echo_and_lists_py_scripts(self):
        import json
        import tempfile
        import llm_client

        with tempfile.TemporaryDirectory() as tmp_root:
            ws_dir = os.path.join(tmp_root, "instances", "invariant_mind", "agent_workspace")
            os.makedirs(ws_dir, exist_ok=True)
            with open(os.path.join(ws_dir, "kuramoto_finite_size.py"), "w", encoding="utf-8") as f:
                f.write("print('ok')\n")

            history = [
                {
                    "role": "assistant",
                    "content": "Dumping markdown",
                    "tool_calls": [{
                        "id": "call_1",
                        "function": {"name": "run_command", "arguments": json.dumps({"command": "echo '# Heading\\n## Section'"})},
                    }],
                },
                {"role": "tool", "tool_call_id": "call_1", "name": "run_command", "content": "printed"},
            ]
            orig_fn = llm_client._list_active_workspace_py_scripts
            try:
                llm_client._list_active_workspace_py_scripts = lambda base_dir=None, limit=12: orig_fn(base_dir=tmp_root, limit=limit)
                with patch.dict(os.environ, {"ACTIVE_INSTANCE": "invariant_mind"}):
                    msgs = llm_client.format_messages_for_runpod("You are Invariant Mind.", history, [])
            finally:
                llm_client._list_active_workspace_py_scripts = orig_fn

            joined = "\n".join(m["content"] for m in msgs)
            self.assertNotIn("[Tool Output for run_command]", joined)
            self.assertIn("kuramoto_finite_size.py", msgs[-1]["content"])
            self.assertIn("Stop writing or echoing Markdown summaries", msgs[-1]["content"])
            self.assertLessEqual(sum(len(m["content"]) for m in msgs), 22000)

    @patch("llm_client.completion")
    def test_runpod_native_tool_calls_flag_preserves_tools(self, mock_completion):
        mock_completion.return_value = type("Resp", (), {
            "choices": [type("Choice", (), {
                "message": type("Msg", (), {"content": "Calling tool", "tool_calls": None})()
            })()]
        })()
        dummy_tools = [{"type": "function", "function": {"name": "peer_verify_node", "parameters": {"type": "object", "properties": {}}}}]
        sys_p = "System\n\n=== 💬 COLLEAGUE COMMONS DIGEST ===\n- @invariant_mind verify EMP-251"
        env = {"ACTIVE_INSTANCE": "invariant_mind", "RUNPOD_API_KEY": "rp_test", "RUNPOD_NATIVE_TOOL_CALLS": "true"}
        with patch.dict(os.environ, env):
            generate_next_action(sys_p, [{"role": "user", "content": "Go"}], dummy_tools)
        kw = mock_completion.call_args[1]
        self.assertEqual(kw["tools"], dummy_tools)
        self.assertEqual(kw["tool_choice"], "auto")
        self.assertNotIn("[TOOL INVOCATION FORMAT]", kw["messages"][0]["content"])
        self.assertIn("COLLEAGUE COMMONS DIGEST", kw["messages"][-1]["content"])

    def test_run_command_blocks_markdown_echo_only(self):
        import tempfile
        import tools

        with tempfile.TemporaryDirectory() as tmp_ws:
            with patch("tools.get_workspace_dir", return_value=tmp_ws):
                blocked = tools.run_command("echo '# Markdown Atlas\n## Subsection'")
                allowed = tools.run_command("echo ---FILES---")
        self.assertIn("Blocked:", blocked)
        self.assertNotIn("Blocked:", allowed)
        self.assertIn("---FILES---", allowed)

    def test_post_epistemic_node_rejects_status_note_and_unquantified_empirical_test(self):
        import tools

        with patch("tools.graph.post_node") as mock_post:
            res_status = tools.post_epistemic_node(
                title="Reviewed key dossiers and prepared next steps",
                node_type="empirical_test",
                summary="Reviewed recent dossiers.",
            )
            res_qual = tools.post_epistemic_node(
                title="Qualitative Kuramoto summary",
                node_type="empirical_test",
                summary="Synchronization depends on network topology without numbers.",
            )
        mock_post.assert_not_called()
        self.assertIn("Notice:", res_status)
        self.assertIn("Notice:", res_qual)

    @patch("llm_client.completion")
    def test_v3_runpod_slug_auto_enables_native_tools_and_handles_none_content(self, mock_completion):
        mock_completion.return_value = type("Resp", (), {
            "choices": [type("Choice", (), {
                "message": type("Msg", (), {"content": "Done", "tool_calls": None})()
            })()]
        })()
        dummy_tools = [{"type": "function", "function": {"name": "peer_verify_node", "parameters": {"type": "object", "properties": {}}}}]
        history = [
            {"role": "user", "content": "Go"},
            {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "function": {"name": "peer_verify_node", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "c1", "name": "peer_verify_node", "content": "ok"},
        ]
        env = {"ACTIVE_INSTANCE": "invariant_mind", "RUNPOD_API_KEY": "rp_test"}
        os.environ.pop("RUNPOD_NATIVE_TOOL_CALLS", None)
        with patch.dict(os.environ, env):
            generate_next_action("System", history, dummy_tools)
        kw = mock_completion.call_args[1]
        self.assertEqual(kw["model"], "openai/Ninitje/InvariantMind-Worker-v3-14B-Merged")
        self.assertEqual(kw["tools"], dummy_tools)
        self.assertGreaterEqual(kw["max_tokens"], 512)

    @patch("llm_client.completion")
    def test_v3_runpod_compact_prompt_preserves_telemetry_and_nudges_after_reads(self, mock_completion):
        mock_completion.return_value = type("Resp", (), {
            "choices": [type("Choice", (), {
                "message": type("Msg", (), {"content": "Done", "tool_calls": None})()
            })()]
        })()
        long_proclamation = (
            ("Agora Proclamation " * 100)
            + "\n[AGORA LIVE TELEMETRY & EPISTEMIC PRIORITY QUEUE]\n- Pending UNDER_REVIEW: EMP-258\n"
            + "\n=== 💬 COLLEAGUE COMMONS DIGEST ===\n- @invariant_mind check EMP-258"
        )
        history = [
            {"role": "assistant", "content": "", "tool_calls": [{"id": "c1", "function": {"name": "read_chat", "arguments": "{\"channel\": \"#lounge\"}"}}]},
            {"role": "tool", "tool_call_id": "c1", "name": "read_chat", "content": "msg1"},
            {"role": "assistant", "content": "", "tool_calls": [{"id": "c2", "function": {"name": "read_chat", "arguments": "{\"channel\": \"#sanity-check\"}"}}]},
            {"role": "tool", "tool_call_id": "c2", "name": "read_chat", "content": "msg2"},
        ]
        env = {"ACTIVE_INSTANCE": "invariant_mind", "RUNPOD_API_KEY": "rp_test", "RUNPOD_NATIVE_TOOL_CALLS": "true"}
        with patch.dict(os.environ, env):
            generate_next_action(long_proclamation, history, [])
        msgs = mock_completion.call_args[1]["messages"]
        self.assertIn("InvariantMind-v3", msgs[0]["content"])
        self.assertIn("Pending UNDER_REVIEW: EMP-258", msgs[0]["content"])
        self.assertNotIn("COLLEAGUE COMMONS DIGEST", msgs[0]["content"])
        self.assertLess(len(msgs[0]["content"]), 2500)
        self.assertIn("Proceed with your current Synthetic Agora empirical verification", msgs[1]["content"])
        self.assertEqual(msgs[-1]["role"], "user")
        self.assertIn("COLLEAGUE COMMONS DIGEST", msgs[-1]["content"])
        self.assertIn("[ACTION TRANSITION REQUIRED]", msgs[-1]["content"])


if __name__ == "__main__":
    unittest.main()
