import os
import sys
import re
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

log_path = r"C:\Users\ninic\Desktop\synthetic-agora\logs_90693703944\0_agora_cycle.txt"
if not os.path.exists(log_path):
    print("Log not found at:", log_path)
    sys.exit(1)

with open(log_path, "r", encoding="utf-8-sig", errors="replace") as f:
    lines = [re.sub(r"^\d{4}-\d{2}-\d{2}T[\d:\.]+Z\s*", "", l) for l in f.readlines()]

full_text = "".join(lines)
print(f"Total lines: {len(lines)}")

# Extract mind activations
activations = re.findall(r">>> \[Activating Mind:\s*(.*?)\] <<<", full_text)
print(f"\nTotal mind activations: {len(activations)}")
unique_agents = {}
for a in activations:
    unique_agents[a] = unique_agents.get(a, 0) + 1
for a, count in unique_agents.items():
    print(f"  - {a:22}: {count} activation(s)")

# Tool call distribution
tools = re.findall(r"⚡ Action: Call tool '(.*?)'", full_text)
tool_counts = {}
for t in tools:
    tool_counts[t] = tool_counts.get(t, 0) + 1
print(f"\nTotal tool calls made: {len(tools)}")
for t, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  - {t:24}: {count}")

# Check knowledge graph stats
with open("instances/shared_agora/knowledge_graph.json", "r", encoding="utf-8") as f:
    kg = json.load(f)

nodes = kg.get("nodes", {})
print("\n" + "=" * 80)
print(f"KNOWLEDGE GRAPH TOTAL NODES: {len(nodes)}")
by_status = {}
for nid, n in nodes.items():
    st = n.get("status", "UNKNOWN")
    by_status[st] = by_status.get(st, 0) + 1
print(f"Status breakdown: {by_status}")
print("=" * 80)

print("\n--- CANON VERIFIED THEOREMS (Total: " + str(by_status.get("CANON_VERIFIED", 0)) + ") ---")
for nid, n in nodes.items():
    if n.get("status") == "CANON_VERIFIED":
        tit = str(n.get("title"))[:60]
        a = str(n.get("author_instance"))
        print(f"👑 {nid:8} | {tit:60} (by {a})")

print("\n--- NEWEST NODES IN GRAPH ---")
for nid, n in list(nodes.items())[-12:]:
    t = str(n.get("type"))
    s = str(n.get("status"))
    tit = str(n.get("title"))[:45]
    a = str(n.get("author_instance"))
    print(f"📌 {nid:8} | [{t:14}] | {s:16} | {tit:45} (by {a})")
