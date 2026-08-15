import os
import argparse

INSTANCES = [
    "gemini_3_1_flash_lite",
    "claude_haiku",
    "llama_4_scout",
    "kimi_code",
    "minimax_m3",
    "deepseek_v4_flash",
    "gemini_flash",
    "claude_sonnet",
    "glm_5_2",
    "qwen_2_5_coder"
]

def setup_all():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for inst in INSTANCES:
        inst_dir = os.path.join(base_dir, "instances", inst)
        os.makedirs(os.path.join(inst_dir, "agent_workspace"), exist_ok=True)
        os.makedirs(os.path.join(inst_dir, "logs"), exist_ok=True)
        print(f"Initialized Agora Instance: {inst}")

if __name__ == "__main__":
    setup_all()
