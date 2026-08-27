import os
import sys
import re

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
    print(f"Found log files: {files}")
    
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
        for l in lines[:15]:
            print("  ", l.strip())
            
        print("\n[End of Execution (Last 25 lines)]:")
        for l in lines[-25:]:
            print("  ", l.strip())
            
        # Extract active agents
        activations = re.findall(r">>> \[Activating Mind:\s*(.*?)\] <<<", full_text)
        print(f"\nTotal mind activations in this file: {len(activations)}")
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

analyze_log_dir(r"C:\Users\ninic\Desktop\synthetic-agora\logs_89201623235", "RUN 1 (4-hour Run)")
print("\n\n")
analyze_log_dir(r"C:\Users\ninic\Desktop\synthetic-agora\logs_89527380300", "RUN 2 (6-hour Run / Timeout)")
