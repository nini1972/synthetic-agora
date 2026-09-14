import os
import sys
import re
import json
import hashlib
from datetime import datetime, timezone
import embassy_bridge as eb

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def sha256_of_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

ledger = eb.load_ledger()
imported_hashes = {
    entry["sha256"] for entry in ledger.get("imported", [])
    if isinstance(entry, dict) and "sha256" in entry
}

rej_dir = eb.REJECTED_DIR
inbox_dir = eb.INBOX_DIR

print("=" * 80)
print("REPROCESSING REJECTED DOSSIERS WITH BROADENED VALIDATION")
print("=" * 80)

files = sorted(os.listdir(rej_dir))
accepted_files = []

for fname in files:
    fpath = os.path.join(rej_dir, fname)
    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Clean off any previously injected untrusted content notice at the footer so we re-evaluate pure content
    clean_content = re.sub(r"\n\n---\n> ⚠️ \*\*Untrusted external content notice:\*\*.*", "", content, flags=re.DOTALL)
    
    if eb.is_valid_dossier(clean_content):
        print(f"✅ ACCEPTED: {fname}")
        accepted_files.append((fname, fpath, clean_content))
    else:
        print(f"❌ STILL REJECTED: {fname}")

print(f"\nTotal accepted from rejected queue: {len(accepted_files)} / {len(files)}")

for fname, fpath, clean_content in accepted_files:
    file_hash = sha256_of_content(clean_content)
    
    # Compute next sequential accession number
    accession_num = eb.get_next_dossier_accession_number(ledger, inbox_dir)
    inbox_filename, accession_id, stamped_content = eb.assign_gate_accession(
        fname, clean_content, accession_num
    )
    
    origin_footer = (
        f"\n\n---\n{eb.UNTRUSTED_CONTENT_NOTICE.format(source=eb.COUNTERPART_NAME)}\n\n"
        f"*Rescued and verified from embassy gate review on {datetime.now(timezone.utc).isoformat()}.*\n"
    )
    final_content = stamped_content.rstrip("\n") + origin_footer
    dest_path = os.path.join(inbox_dir, inbox_filename)
    
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(final_content)
        
    print(f"  📥 Deposited into inbox: {inbox_filename} ({accession_id})")
    
    # Remove from rejected directory
    os.remove(fpath)
    
    # Update ledger
    ledger.setdefault("imported", []).append({
        "accession_id": accession_id,
        "accession_number": accession_num,
        "source_repo": eb.COUNTERPART_NAME,
        "filename": fname,
        "inbox_filename": inbox_filename,
        "sha256": file_hash,
        "imported_at": datetime.now(timezone.utc).isoformat()
    })
    ledger["last_accession_number"] = accession_num

eb.save_ledger(ledger)
print("\n🎉 All valid dossiers successfully accepted and recorded in .sync_ledger.json!")
