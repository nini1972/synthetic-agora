import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 1. Knowledge graph contributions
with open("instances/shared_agora/knowledge_graph.json", "r", encoding="utf-8") as f:
    kg = json.load(f)

print("=" * 80)
print("GLM 5.2 (Z-AI) NODES IN THE EPISTEMIC GRAPH")
print("=" * 80)
for nid, n in kg.get("nodes", {}).items():
    author = n.get("author_instance", "")
    family = n.get("author_family", "")
    if "glm" in author.lower() or "z-ai" in family.lower():
        print(f"📌 {nid}: [{n.get('type')}] {n.get('title')}")
        print(f"   Status: {n.get('status')} | Confidence: {n.get('confidence')}")
        print(f"   Summary: {n.get('summary')}")
        print(f"   Artifact: {n.get('artifact_path')}")
        print(f"   Reviews ({len(n.get('verifications', []))}):")
        for v in n.get("verifications", []):
            print(f"     - By {v.get('verifier_instance')}: {v.get('verdict')} -> {v.get('critique_notes')[:120]}...")
        print("-" * 60)

# 2. Local workspace files
ws = "instances/glm_5_2/agent_workspace"
if os.path.exists(ws):
    print("\n" + "=" * 80)
    print("GLM 5.2 LOCAL WORKSPACE FILES & CODE")
    print("=" * 80)
    for root, dirs, files in os.walk(ws):
        for f in files:
            fp = os.path.join(root, f)
            print(f"  📁 {os.path.relpath(fp, ws)} ({os.path.getsize(fp)} bytes)")

# 3. Recent history thoughts
hist_path = "instances/glm_5_2/logs/history.jsonl"
if os.path.exists(hist_path):
    print("\n" + "=" * 80)
    print("GLM 5.2 RECENT INTERNAL DIALOGUE & REASONING (history.jsonl)")
    print("=" * 80)
    with open(hist_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    for l in lines[-10:]:
        try:
            entry = json.loads(l)
            role = entry.get("role", "")
            content = entry.get("content", "")
            if role == "assistant" and content:
                print(f"\n🧠 [ASSISTANT THOUGHT]:\n{content[:600]}...")
            elif role == "tool":
                print(f"⚡ [TOOL RESULT]: {entry.get('content', '')[:200]}...")
        except Exception:
            pass
