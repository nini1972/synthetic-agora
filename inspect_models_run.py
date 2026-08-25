import os
import sys
import re
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

log_path = r"C:\Users\ninic\Desktop\synthetic-agora\logs_88391733278\0_agora_cycle.txt"
if not os.path.exists(log_path):
    print("Log not found at", log_path)
    exit(1)

with open(log_path, "r", encoding="utf-8", errors="replace") as f:
    text = f.read()

lines = text.splitlines()
print(f"Total lines in log: {len(lines)}")

# Parse agents and turns
current_agent = None
agent_actions = {}

for line in lines:
    m_act = re.search(r">>> \[Activating Mind: (.*?)\] <<<", line)
    if m_act:
        current_agent = m_act.group(1).strip()
        if current_agent not in agent_actions:
            agent_actions[current_agent] = []
        continue

    m_tool = re.search(r"⚡ Action: Call tool '(.*?)' with args (.*)", line)
    if m_tool and current_agent:
        tname = m_tool.group(1)
        targs = m_tool.group(2)
        agent_actions[current_agent].append((tname, targs))

print("\n" + "="*80)
print("AGENT ACTIVITY BREAKDOWN:")
print("="*80)
for agent, acts in agent_actions.items():
    print(f"\n🧠 AGENT: {agent} ({len(acts)} tool calls)")
    for i, (tname, targs) in enumerate(acts, 1):
        print(f"   {i}. {tname:24} -> {targs[:100]}")
