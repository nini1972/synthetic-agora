import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

rej_dir = "instances/shared_agora/embassy/rejected"

print("=" * 80)
print("AUDIT OF REJECTED EMBASSY DOSSIERS FROM WORLD A")
print("=" * 80)

for fname in os.listdir(rej_dir):
    fpath = os.path.join(rej_dir, fname)
    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    
    print(f"\n📄 FILE: {fname}")
    print(f"   Size: {len(content)} characters")
    
    # Check validation triggers
    lowered = content.lower()
    has_fed = "frontier epistemic dossier" in lowered
    has_ep = "empirical phenomenon" in lowered
    length_ok = len(content.strip()) >= 200
    
    print(f"   Validation Checks: Length>=200: {length_ok} | 'frontier epistemic dossier': {has_fed} | 'empirical phenomenon': {has_ep}")
    
    # Print preview
    lines = content.splitlines()
    print("   [First 15 lines of content]:")
    for l in lines[:15]:
        print(f"     {l}")
    print("-" * 60)
