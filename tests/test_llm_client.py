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


if __name__ == "__main__":
    unittest.main()
