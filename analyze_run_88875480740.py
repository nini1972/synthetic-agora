import os
import sys
import re
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

log_path = r"C:\Users\ninic\Desktop\synthetic-agora\logs_88875480740\0_agora_cycle.txt"

with open(log_path, "r", encoding="utf-8", errors="replace") as f:
    text = f.read()

lines = text.splitlines()
print(f"Total lines in log: {len(lines)}")

# Parse active agents
agents = re.findall(r">>> \[Activating Mind: (.*?)\] <<<", text)
print(f"Active agents in this run ({len(agents)} activations): {agents}")

# Group by agent
agent_blocks = re.findall(r">>> \[Activating Mind: (.*?)\] <<<.*?(?=(?:>>> \[Activating Mind:|\Z))", text, re.DOTALL)

for b in agent_blocks:
    m_name = re.search(r"^(.*?)\n", b.strip())
    # Find tool calls
    tools = re.findall(r"⚡ Action: Call tool '(.*?)' with args (.*)", b)
    # Find thoughts
    thoughts = re.findall(r"💭 Agent Thought:\s*(.*?)(?=(?:⚡ Action|\Z))", b, re.DOTALL)
    
    first_line = b.strip().splitlines()[0]
    print("\n" + "="*80)
    print(f"🏛️ AGENT TURN: {first_line}")
    print("="*80)
    print(f"Tool calls ({len(tools)}):")
    for tname, targs in tools:
        print(f"  ⚡ {tname:24} -> {targs[:120]}")
    if thoughts:
        print("\nLatest Thought Summary:")
        print(thoughts[-1].strip()[:600] + ("..." if len(thoughts[-1].strip()) > 600 else ""))
