import sys
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open(r"C:\Users\ninic\Desktop\synthetic-agora\logs_88391733278\0_agora_cycle.txt", "r", encoding="utf-8", errors="replace") as f:
    text = f.read()

def print_agent_turns(agent_name):
    print("=" * 80)
    print(f"DEEP DIVE: AGENT '{agent_name}'")
    print("=" * 80)
    pattern = rf">>> \[Activating Mind: {agent_name}\] <<<.*?(?=(?:>>> \[Activating Mind:|\Z))"
    blocks = re.findall(pattern, text, re.DOTALL)
    for b in blocks:
        # Extract thoughts and actions
        turns = re.findall(r"(--- Turn Tick \d+/\d+ ---.*?)(?=(?:--- Turn Tick|\Z))", b, re.DOTALL)
        for t in turns:
            lines = t.strip().splitlines()
            print("\n".join(lines[:35]))
            print("-" * 40)

print_agent_turns("glm_5_2")
print_agent_turns("qwen_2_5_coder")
