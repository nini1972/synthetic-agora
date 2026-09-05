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
copied across repos. Instead, any bare `shared_space/...` reference inside the
dossier text is rewritten to an absolute `raw.githubusercontent.com` URL pinned to
the exact source commit, so the artifact remains inspectable without pulling
unreviewed executable code from the counterpart world into this sandbox's
run_command surface.
"""
import os
import re
import json
import hashlib
import subprocess
import tempfile
from datetime import datetime, timezone

from agora_graph import get_shared_agora_dir

EMBASSY_DIR = os.path.join(get_shared_agora_dir(), "embassy")
INBOX_DIR = os.path.join(EMBASSY_DIR, "inbox")
REJECTED_DIR = os.path.join(EMBASSY_DIR, "rejected")
LEDGER_PATH = os.path.join(EMBASSY_DIR, ".sync_ledger.json")

# The counterpart world ("World A") that Frontier dossiers are pulled from.
COUNTERPART_OWNER = "nini1972"
COUNTERPART_NAME = "evolution_sandbox"
COUNTERPART_REPO_URL = f"https://github.com/{COUNTERPART_OWNER}/{COUNTERPART_NAME}.git"
COUNTERPART_OUTBOX_REL = os.path.join("instances", "shared_space", "embassy", "outbox")

# Bare shorthand references like `shared_space/foo.png` inside dossier text are
# rewritten to the real repo-relative path before being turned into a raw URL.
ARTIFACT_SHORTHAND_PREFIX = "shared_space/"
ARTIFACT_REAL_PREFIX = "instances/shared_space/"

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
    """Shallow, read-only clone of the counterpart world. Returns its local path.

    Explicitly forces TLS certificate verification for this invocation regardless of
    any global git config (e.g. the workflow's `http.sslVerify false` override used
    for other steps), so this sync never fetches external content over unverified TLS.
    """
    dest = os.path.join(tmp_dir, COUNTERPART_NAME)
    subprocess.run(
        ["git", "-c", "http.sslVerify=true", "clone", "--depth", "1", COUNTERPART_REPO_URL, dest],
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


def rewrite_artifact_references(content: str, commit_sha: str) -> str:
    """Rewrites bare `shared_space/...` artifact shorthand references into absolute
    raw.githubusercontent.com URLs pinned to the exact source commit, so referenced
    plots/scripts remain inspectable without ever being physically copied into this
    sandbox (see module docstring)."""
    pattern = re.compile(r"`" + re.escape(ARTIFACT_SHORTHAND_PREFIX) + r"([^`]+)`")

    def _replace(match: "re.Match[str]") -> str:
        rel_path = match.group(1)
        real_path = f"{ARTIFACT_REAL_PREFIX}{rel_path}"
        url = f"https://raw.githubusercontent.com/{COUNTERPART_OWNER}/{COUNTERPART_NAME}/{commit_sha}/{real_path}"
        return f"`{url}`"

    return pattern.sub(_replace, content)


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
            rewritten_content = rewrite_artifact_references(content, commit_sha)
            with open(os.path.join(INBOX_DIR, filename), "w", encoding="utf-8") as f:
                f.write(rewritten_content.rstrip("\n") + origin_footer)

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
