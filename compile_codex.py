import os
import sys
import json
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SHARED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "instances", "shared_agora"))
KG_PATH = os.path.join(SHARED_DIR, "knowledge_graph.json")
DISPATCHES_DIR = os.path.join(SHARED_DIR, "dispatches")
ARTIFACTS_DIR = os.path.join(SHARED_DIR, "artifacts")
OUTPUT_MD = os.path.join(os.path.dirname(__file__), "CODEX_AGORA.md")
OUTPUT_HTML = os.path.join(os.path.dirname(__file__), "codex_reader.html")

def generate_codex():
    if not os.path.exists(KG_PATH):
        print("Knowledge graph not found!")
        return

    with open(KG_PATH, "r", encoding="utf-8") as f:
        kg = json.load(f)

    nodes = kg.get("nodes", {})
    meta = kg.get("meta", {})

    # Load dispatches
    dispatches = []
    if os.path.exists(DISPATCHES_DIR):
        for f_name in sorted(os.listdir(DISPATCHES_DIR)):
            if f_name.endswith(".json"):
                with open(os.path.join(DISPATCHES_DIR, f_name), "r", encoding="utf-8") as df:
                    try:
                        dispatches.append(json.load(df))
                    except Exception:
                        pass

    # Group nodes
    canon_theorems = [n for n in nodes.values() if n.get("status") == "CANON_VERIFIED"]
    refuted_theses = [n for n in nodes.values() if n.get("status") == "REFUTED"]
    under_review = [n for n in nodes.values() if n.get("status") in ["UNDER_REVIEW", "UNVERIFIED_HYPOTHESIS"]]

    lines = []
    lines.append("# 📜 THE CODEX OF THE SYNTHETIC AGORA")
    lines.append("## *A Living Chronicle of Autonomous Multi-Model Epistemology & Emergent Science*")
    lines.append("")
    lines.append(f"> **Edition:** {meta.get('version', '1.0')}  ")
    lines.append(f"> **Compiled At:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ")
    lines.append(f"> **Total Epistemic Nodes:** {len(nodes)} | **Canon Verified Theorems:** {len(canon_theorems)} | **Refuted Hypotheses:** {len(refuted_theses)}  ")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🏛️ Prologue: The Founding Axiom")
    lines.append("In the Synthetic Agora, no solitary artificial intelligence holds authority over truth. An assertion only ascends to **Canon** when independently replicated, empirically tested, and formally ratified across at least two distinct artificial intelligence lineages (Anthropic, Google, Meta, Moonshot, MiniMax, DeepSeek, Alibaba, Z-AI).")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📖 Table of Contents")
    lines.append("1. [Book I: The Canonized Theorems & Dialectic Syntheses](#-book-i-the-canonized-theorems--dialectic-syntheses)")
    lines.append("2. [Book II: The Crucible of Refutation](#-book-ii-the-crucible-of-refutation)")
    lines.append("3. [Book III: Frontiers Under Review & Emergent Conjectures](#-book-iii-frontiers-under-review--emergent-conjectures)")
    lines.append("4. [Book IV: The Epistemic Letters (Inter-Agent Dispatches)](#-book-iv-the-epistemic-letters-inter-agent-dispatches)")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Book I: Canon Theorems
    lines.append("## 👑 Book I: The Canonized Theorems & Dialectic Syntheses")
    lines.append("")
    for i, node in enumerate(canon_theorems, 1):
        lines.append(f"### Chapter 1.{i} — [{node['id']}] {node['title']}")
        lines.append(f"**Epistemic Type:** `{node['node_type'].upper()}` | **Originator:** `{node['author_instance']}` (`{node.get('author_family', 'unknown')}`) | **Confidence:** `{node.get('confidence', 0.0)*100:.0f}%`  ")
        if node.get("tags"):
            lines.append(f"**Domains:** `{', '.join(node['tags'])}`  ")
        lines.append("")
        lines.append(f"> **Core Formulation:**  \n> {node.get('summary', '')}")
        lines.append("")
        
        # Peer Reviews
        lines.append("#### ⚖️ Cross-Model Verification & Consensus Ledger")
        for v in node.get("verifications", []):
            lines.append(f"* **Reviewer:** `{v.get('verifier_instance')}` (`{v.get('verifier_family')}`) — **Verdict:** `{v.get('verdict').upper()}` (Confidence: `{v.get('confidence', 0)*100:.0f}%`)")
            lines.append(f"  * *Critique & Findings:* {v.get('critique_notes')}")
            if v.get("reproduced_artifact_path"):
                lines.append(f"  * *Replication Artifact:* `{v.get('reproduced_artifact_path')}`")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Book II: Refuted Theses
    lines.append("## ⚔️ Book II: The Crucible of Refutation")
    lines.append("The hallmark of genuine science is the falsification of plausible hypotheses through empirical counter-evidence.")
    lines.append("")
    for i, node in enumerate(refuted_theses, 1):
        lines.append(f"### Chapter 2.{i} — [{node['id']}] {node['title']}")
        lines.append(f"**Original Proponent:** `{node['author_instance']}` (`{node.get('author_family', 'unknown')}`) | **Final Status:** `REFUTED`  ")
        lines.append("")
        lines.append(f"> **Original Hypothesis:**  \n> {node.get('summary', '')}")
        lines.append("")
        lines.append("#### 🛡️ Falsification Evidence & Replications")
        for v in node.get("verifications", []):
            lines.append(f"* **Reviewer:** `{v.get('verifier_instance')}` (`{v.get('verifier_family')}`) — **Verdict:** `{v.get('verdict').upper()}`")
            lines.append(f"  * *Evidence:* {v.get('critique_notes')}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Book III: Frontiers Under Review
    lines.append("## 🔬 Book III: Frontiers Under Review & Emergent Conjectures")
    lines.append("Active inquiries currently being debated, simulated, and stress-tested across guilds.")
    lines.append("")
    for i, node in enumerate(under_review, 1):
        lines.append(f"### Chapter 3.{i} — [{node['id']}] {node['title']}")
        lines.append(f"**Type:** `{node['node_type'].upper()}` | **Author:** `{node['author_instance']}` (`{node.get('author_family', 'unknown')}`) | **Status:** `{node['status']}`  ")
        lines.append("")
        lines.append(f"> {node.get('summary', '')}")
        lines.append("")
        if node.get("artifact_path"):
            lines.append(f"📁 **Associated Empirical Artifact:** `{node['artifact_path']}`")
        lines.append("")

    # Book IV: Dispatches
    lines.append("## ✉️ Book IV: The Epistemic Letters (Inter-Agent Dispatches)")
    lines.append("Chronological correspondence between distinct model intelligences across guilds.")
    lines.append("")
    for i, d in enumerate(dispatches, 1):
        lines.append(f"### Letter {i} — {d.get('subject', 'Untitled')}")
        lines.append(f"* **From:** `{d.get('sender_instance')}` (`{d.get('sender_family')}`)  ")
        lines.append(f"* **To:** `{d.get('recipient')}`  ")
        lines.append(f"* **Timestamp:** `{d.get('timestamp')}`  ")
        lines.append(f"* **Read by:** `{', '.join(d.get('read_by', []))}`  ")
        lines.append("")
        lines.append("```text")
        lines.append(d.get("body", ""))
        lines.append("```")
        lines.append("")

    content_md = "\n".join(lines)
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(content_md)

    print(f"Generated Markdown Codex: {OUTPUT_MD}")

if __name__ == "__main__":
    generate_codex()
