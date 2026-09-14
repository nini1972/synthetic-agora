import os
import sys
import re
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def analyze_log_dir(dir_path, label):
    print("=" * 80)
    print(f"ANALYSIS OF {label}: {dir_path}")
    print("=" * 80)
    
    if not os.path.exists(dir_path):
        print(f"Directory {dir_path} does not exist!")
        return

    files = [f for f in os.listdir(dir_path) if f.endswith(".txt") or f.endswith(".log")]
    print(f"Found files: {files}")
    
    for fname in files:
        fpath = os.path.join(dir_path, fname)
        size = os.path.getsize(fpath)
        print(f"\n--- File: {fname} ({size} bytes) ---")
        
        with open(fpath, "r", encoding="utf-8-sig", errors="replace") as f:
            lines = [re.sub(r"^\d{4}-\d{2}-\d{2}T[\d:\.]+Z\s*", "", l) for l in f.readlines()]
            
        full_text = "".join(lines)
        print(f"Total lines: {len(lines)}")
        
        # Check start and end
        print("\n[Start of Execution]:")
        for l in lines[:10]:
            print("  ", l.strip())
            
        print("\n[End of Execution (Last 20 lines)]:")
        for l in lines[-20:]:
            print("  ", l.strip())
            
        # Extract active agents
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

        # Check for errors/warnings
        errors = re.findall(r"(?:❌|⚠️|Traceback|Error:)(.*)", full_text)
        if errors:
            print(f"\nErrors / Warnings found ({len(errors)}):")
            for e in errors[:5]:
                print(f"   {e.strip()}")

analyze_log_dir(r"C:\Users\ninic\Desktop\synthetic-agora\logs_90221400690 (1)", "RUN 1: logs_90221400690")
print("\n\n")
analyze_log_dir(r"C:\Users\ninic\Desktop\synthetic-agora\logs_90385402142", "RUN 2: logs_90385402142")
