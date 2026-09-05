"""
Embassy Bridge — pull-only synchronization for the Inter-World Epistemic Embassy.

This runs inside the Synthetic Agora ("World B"). It shallow-clones the public
Evolution Sandbox ("World A") repository, scans its embassy outbox for newly
submitted Frontier Epistemic Dossiers, validates and deduplicates them, and imports
accepted ones into this repo's own embassy inbox
(instances/shared_agora/embassy/inbox/).

This script is strictly READ-ONLY against the counterpart repository: it only ever
clones it to a temp directory and never writes, commits, or pushes to it. All state
(the sync ledger) and all writes happen locally, so no cross-repo credentials are
required — the nightly workflow can commit/push using its own default GITHUB_TOKEN.

Artifacts referenced by a dossier (plots, simulation scripts) are intentionally NOT
copied across repos; they remain reachable only via their raw.githubusercontent.com
URLs so that unreviewed executable code from the counterpart world never enters this
sandbox's run_command surface.
"""
import os
import re
import json
import hashlib
import subprocess
import tempfile
from datetime import datetime, timezone

from agora_graph import get_shared_agora_dir

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
EMBASSY_DIR = os.path.join(get_shared_agora_dir(), "embassy")
INBOX_DIR = os.path.join(EMBASSY_DIR, "inbox")
REJECTED_DIR = os.path.join(EMBASSY_DIR, "rejected")
LEDGER_PATH = os.path.join(EMBASSY_DIR, ".sync_ledger.json")

# The counterpart world ("World A") that Frontier dossiers are pulled from.
COUNTERPART_NAME = "evolution_sandbox"
COUNTERPART_REPO_URL = "https://github.com/nini1972/evolution_sandbox.git"
COUNTERPART_OUTBOX_REL = os.path.join("instances", "shared_space", "embassy", "outbox")

# Only files that look like real dossiers are imported; templates/READMEs are ignored.
TEMPLATE_FILENAME_RE = re.compile(r"template", re.IGNORECASE)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def load_ledger() -> dict:
    if os.path.exists(LEDGER_PATH):
        try:
            with open(LEDGER_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"imported": [], "exported": []}


def save_ledger(ledger: dict) -> None:
    os.makedirs(EMBASSY_DIR, exist_ok=True)
    with open(LEDGER_PATH, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)


def clone_counterpart(tmp_dir: str) -> str:
    """Shallow, read-only clone of the counterpart world. Returns its local path."""
    dest = os.path.join(tmp_dir, COUNTERPART_NAME)
    subprocess.run(
        ["git", "clone", "--depth", "1", COUNTERPART_REPO_URL, dest],
        check=True, capture_output=True, text=True,
    )
    return dest


def get_commit_sha(repo_dir: str) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_dir, check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()


def is_valid_dossier(content: str) -> bool:
    """Loose structural validation so we don't import garbage or unrelated files."""
    if len(content.strip()) < 200:
        return False
    lowered = content.lower()
    if "frontier epistemic dossier" not in lowered:
        return False
    if "empirical phenomenon" not in lowered:
        return False
    return True


def sync() -> None:
    os.makedirs(INBOX_DIR, exist_ok=True)
    os.makedirs(REJECTED_DIR, exist_ok=True)
    ledger = load_ledger()
    imported_hashes = {entry["sha256"] for entry in ledger.get("imported", [])}

    with tempfile.TemporaryDirectory(prefix="embassy_sync_") as tmp_dir:
        try:
            counterpart_dir = clone_counterpart(tmp_dir)
        except subprocess.CalledProcessError as e:
            print(f"[EmbassyBridge] ERROR: Failed to clone {COUNTERPART_REPO_URL}: {e.stderr}")
            return

        commit_sha = get_commit_sha(counterpart_dir)
        outbox_path = os.path.join(counterpart_dir, COUNTERPART_OUTBOX_REL)

        if not os.path.isdir(outbox_path):
            print(f"[EmbassyBridge] Counterpart outbox not found at {COUNTERPART_OUTBOX_REL}. Nothing to sync.")
            return

        candidates = sorted(
            f for f in os.listdir(outbox_path)
            if f.lower().endswith(".md") and not TEMPLATE_FILENAME_RE.search(f)
        )

        imported_count = 0
        skipped_count = 0
        rejected_count = 0

        for filename in candidates:
            src_path = os.path.join(outbox_path, filename)
            if not os.path.isfile(src_path):
                continue

            file_hash = sha256_of(src_path)
            if file_hash in imported_hashes:
                skipped_count += 1
                continue

            with open(src_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            if not is_valid_dossier(content):
                rejected_count += 1
                with open(os.path.join(REJECTED_DIR, filename), "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"[EmbassyBridge] Rejected malformed candidate: {filename}")
                continue

            origin_footer = (
                f"\n\n---\n*Synced from `{COUNTERPART_NAME}` "
                f"(commit `{commit_sha[:12]}`) on {utc_now_iso()} by embassy_bridge.py.*\n"
            )
            with open(os.path.join(INBOX_DIR, filename), "w", encoding="utf-8") as f:
                f.write(content.rstrip("\n") + origin_footer)

            ledger.setdefault("imported", []).append({
                "source_repo": COUNTERPART_NAME,
                "source_commit": commit_sha,
                "filename": filename,
                "sha256": file_hash,
                "imported_at": utc_now_iso(),
            })
            imported_hashes.add(file_hash)
            imported_count += 1
            print(f"[EmbassyBridge] Imported new dossier: {filename}")

        save_ledger(ledger)
        print(
            f"[EmbassyBridge] Sync complete. Imported: {imported_count}, "
            f"Skipped (already known): {skipped_count}, Rejected: {rejected_count}."
        )


if __name__ == "__main__":
    sync()
