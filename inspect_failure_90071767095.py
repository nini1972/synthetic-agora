import sys
import os
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

log_path = r"C:\Users\ninic\Desktop\synthetic-agora\logs_90071767095\0_agora_cycle.txt"

with open(log_path, "r", encoding="utf-8-sig", errors="replace") as f:
    lines = [re.sub(r"^\d{4}-\d{2}-\d{2}T[\d:\.]+Z\s*", "", l) for l in f.readlines()]

print(f"Total lines: {len(lines)}")

print("\n" + "=" * 80)
print("LAST 50 LINES OF LOG:")
print("=" * 80)
for l in lines[-50:]:
    print(l.rstrip())

print("\n" + "=" * 80)
print("ALL ERROR PATTERNS IN LOG:")
print("=" * 80)
for i, l in enumerate(lines):
    if any(k in l.lower() for k in ["traceback", "error:", "exit code", "failed", "fatal", "##[error]"]):
        print(f"Line {i+1}: {l.strip()[:140]}")
