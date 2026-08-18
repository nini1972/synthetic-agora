import os
import re

log_path = r"C:\Users\ninic\Desktop\synthetic-agora\logs_87010882474\0_agora_cycle.txt"

if not os.path.exists(log_path):
    print("Log file not found!")
    exit(1)

with open(log_path, "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()

print(f"Total lines in log: {len(lines)}")

errors = []
agent_activations = {}
tool_invocations = {}
llm_models_used = set()

current_agent = None

for i, line in enumerate(lines):
    # Detect agent activation
    m_act = re.search(r">>> \[Activating Mind: (.*?)\] <<<", line)
    if m_act:
        current_agent = m_act.group(1)
        agent_activations[current_agent] = agent_activations.get(current_agent, 0) + 1

    # Detect model routing
    m_route = re.search(r"🎯 \[Lineage Engine\] Routing '.*?' to -> (.*)", line)
    if m_route:
        llm_models_used.add(m_route.group(1).strip())

    # Detect tool call
    m_tool = re.search(r"⚡ Action: Call tool '(.*?)'", line)
    if m_tool:
        t_name = m_tool.group(1)
        tool_invocations[t_name] = tool_invocations.get(t_name, 0) + 1

    # Detect errors / struggles
    if "❌ LLM Error" in line or "Error reading file:" in line or "Error writing file:" in line or "SyntaxError" in line or "Rate limited" in line:
        errors.append((i+1, current_agent, line.strip()))

print("\n" + "=" * 80)
print("AGENT PARTICIPATION & TURNS:")
for ag, count in sorted(agent_activations.items(), key=lambda x: x[1], reverse=True):
    print(f"  {ag:22} : {count} turns")

print("\n" + "=" * 80)
print("AUTHENTIC MODELS ROUTED:")
for mod in sorted(llm_models_used):
    print(f"  - {mod}")

print("\n" + "=" * 80)
print("TOOL INVOCATION TOTALS:")
for tool, count in sorted(tool_invocations.items(), key=lambda x: x[1], reverse=True):
    print(f"  {tool:25} : {count} calls")

print("\n" + "=" * 80)
print(f"NOTABLE ERRORS & FRICTION POINTS ({len(errors)} found):")
for line_no, ag, err in errors[:30]:
    print(f"  Line {line_no:5} [{ag}]: {err[:120]}")

print("=" * 80)
