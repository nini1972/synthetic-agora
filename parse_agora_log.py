import sys
import os
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

log_path = r"C:\Users\ninic\Desktop\synthetic-agora\logs_88875480740\0_agora_cycle.txt"

with open(log_path, "r", encoding="utf-8-sig", errors="replace") as f:
    lines = [re.sub(r"^\d{4}-\d{2}-\d{2}T[\d:\.]+Z\s*", "", l) for l in f.readlines()]

full_text = "".join(lines)

# Find where the agora run begins
start_idx = full_text.find("THE SYNTHETIC AGORA")
if start_idx == -1:
    print("Could not find Agora start banner!")
    print(full_text[:2000])
    sys.exit(1)

agora_text = full_text[start_idx:]

# Parse each agent turn
activations = re.split(r">>> \[Activating Mind:\s*(.*?)\] <<<", agora_text)

print(f"Total activation segments: {len(activations)//2}")

for i in range(1, len(activations), 2):
    agent_name = activations[i].strip()
    content = activations[i+1]
    
    # Extract thoughts and tool calls
    tools = re.findall(r"⚡ Action: Call tool '(.*?)' with args (.*?)(?=\n(?:📋 Result|\Z))", content, re.DOTALL)
    thoughts = re.findall(r"💭 Agent Thought:\s*(.*?)(?=\n(?:⚡ Action|\Z))", content, re.DOTALL)
    errors = re.findall(r"(?:❌|⚠️|Error:)(.*)", content)
    
    print("\n" + "="*80)
    print(f"🏛️ AGENT ACTIVATION: {agent_name}")
    print("="*80)
    if errors:
        print(f"⚠️ Errors/Warnings ({len(errors)}):")
        for err in errors[:3]:
            print(f"   {err.strip()}")
            
    print(f"Tool calls ({len(tools)}):")
    for tname, targs in tools:
        targs_clean = " ".join(targs.split())
        print(f"  ⚡ {tname:24} -> {targs_clean[:120]}")
        
    if thoughts:
        last_th = " ".join(thoughts[-1].split())
        print(f"Last Thought: {last_th[:300]}...")
