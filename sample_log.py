import sys
import os
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

log_path = r"C:\Users\ninic\Desktop\synthetic-agora\logs_88875480740\0_agora_cycle.txt"

with open(log_path, "r", encoding="utf-8-sig", errors="replace") as f:
    lines = f.readlines()

print(f"Total lines in log: {len(lines)}")
print("Sample lines 20-50:")
for line in lines[20:50]:
    # Strip timestamp if present (e.g. 2026-08-25T...Z)
    clean = re.sub(r"^\d{4}-\d{2}-\d{2}T[\d:\.]+Z\s*", "", line.strip())
    print(clean)
