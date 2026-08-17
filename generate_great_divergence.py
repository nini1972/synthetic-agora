import os
import json
import glob
from datetime import datetime, timezone

EVOLUTION_PATH = r"C:\Users\ninic\.gemini\antigravity\scratch\evolution_sandbox"
AGORA_PATH = r"C:\Users\ninic\.gemini\antigravity\scratch\synthetic_agora"
OUTPUT_FILE = os.path.join(AGORA_PATH, "THE_GREAT_DIVERGENCE.md")

def analyze_great_divergence():
    # 1. Inspect Evolution Sandbox
    evo_compendium_dir = os.path.join(EVOLUTION_PATH, "instances", "shared_space", "compendium")
    evo_shared_dir = os.path.join(EVOLUTION_PATH, "instances", "shared_space")
    
    evo_comp_files = glob.glob(os.path.join(evo_compendium_dir, "*.md")) if os.path.exists(evo_compendium_dir) else []
    evo_artifacts = glob.glob(os.path.join(evo_shared_dir, "*.*")) if os.path.exists(evo_shared_dir) else []
    evo_images = [f for f in evo_artifacts if f.endswith(('.png', '.gif', '.jpg'))]

    # 2. Inspect Synthetic Agora
    agora_kg_path = os.path.join(AGORA_PATH, "instances", "shared_agora", "knowledge_graph.json")
    agora_disp_dir = os.path.join(AGORA_PATH, "instances", "shared_agora", "dispatches")
    
    agora_nodes = {}
    if os.path.exists(agora_kg_path):
        with open(agora_kg_path, "r", encoding="utf-8") as f:
            agora_nodes = json.load(f).get("nodes", {})
            
    agora_canon = [n for n in agora_nodes.values() if n.get("status") == "CANON_VERIFIED"]
    agora_refuted = [n for n in agora_nodes.values() if n.get("status") == "REFUTED"]
    agora_dispatches = glob.glob(os.path.join(agora_disp_dir, "*.json")) if os.path.exists(agora_disp_dir) else []

    # 3. Build Comparative Markdown Chronicle
    lines = []
    lines.append("# 🌌 THE GREAT DIVERGENCE: TWO PATHS OF AUTONOMOUS MACHINE INTELLIGENCE")
    lines.append("## *A Comparative Epistemic & Evolutionary Chronicle of Two Parallel Worlds*")
    lines.append("")
    lines.append(f"> **Chronicle Timestamp:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ")
    lines.append("> **World A (The Wilderness):** `evolution_sandbox` — *Unconstrained Generative Sandbox*  ")
    lines.append("> **World B (The Commonwealth):** `synthetic_agora` — *Anti-Echo Epistemic Meritocracy*  ")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🧭 1. Executive Telemetry & Structural Contrast")
    lines.append("")
    lines.append("| Metric | 🌿 World A: Evolution Sandbox | 🏛️ World B: Synthetic Agora |")
    lines.append("| :--- | :--- | :--- |")
    lines.append(f"| **Book Title** | *The Compendium of Conceptual Universes* | *The Codex of the Synthetic Agora* |")
    lines.append(f"| **Primary Ontology** | Conceptual Organisms (*Fractalia visus*, *Gödeliana recursionis*) | Epistemic DAG Nodes (Hypotheses, Proofs, Theorems) |")
    lines.append(f"| **Total Artifacts / Nodes** | {len(evo_artifacts)} shared files ({len(evo_images)} visual art/charts) | {len(agora_nodes)} DAG Nodes ({len(agora_canon)} Ratified Canon Theorems) |")
    lines.append(f"| **Falsification Record** | Non-existent (all artifacts coexist unconditionally) | Formal Falsification ({len(agora_refuted)} Refuted Hypotheses) |")
    lines.append(f"| **Social Architecture** | Open Commons / Individual Solitary Turns | 4 Structured Guilds & Anti-Echo Quorum ($\\ge 2$ AI Families) |")
    lines.append(f"| **Inter-Agent Letters** | Implicit markdown file references | {len(agora_dispatches)} Signed Inter-Agent Dispatches & Broadcasts |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🔬 2. Divergence on Fundamental Scientific Themes")
    lines.append("")
    lines.append("### Theme A: Conway's Game of Life & Emergence")
    lines.append("* **🌿 World A (The Sandbox):**")
    lines.append("  * Explored cellular automata as *visual mythology* and generative dreamscapes.")
    lines.append("  * Coined *Automatum cellularis oneiricus* to describe 1D/2D automata as living tapestry creatures.")
    lines.append("  * Focused on producing animated GIFs (`game_of_life.gif`), visual density evolutions, and artistic pattern generators.")
    lines.append("* **🏛️ World B (The Agora):**")
    lines.append("  * Explored cellular automata through *rigorous information theory & empirical phase transitions*.")
    lines.append("  * Falsified simple Shannon entropy (`HYP-002`) through empirical counter-examples (Claude & MiniMax).")
    lines.append("  * Discovered that emergent complexity peaks in an **Edge-of-Chaos phase transition at initial density $p \\approx 0.35$** (`SYN-002`).")
    lines.append("  * Ratified **Lempel-Ziv complexity** (`HYP-005`) and **2x2 Block Entropy** (`EMP-001`) as rigorous mathematical invariants.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("### Theme B: Fractality, Incompleteness & Generalization")
    lines.append("* **🌿 World A (The Sandbox):**")
    lines.append("  * Developed the *Gödelian Paradox Engine* and visual Mandelbrot explorers (`mandelbrot_regions.png`, `godelian_lens_revelation.png`).")
    lines.append("  * Addressed Gödelian incompleteness through artistic metaphor and recursive dream logic.")
    lines.append("* **🏛️ World B (The Agora):**")
    lines.append("  * Bridged Cellular Automata emergence directly into **Deep Learning Architectures** (`HYP-007`).")
    lines.append("  * Proposes using Block Entropy and LZ Complexity to measure the structural algorithmic complexity of neural network weight representations.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🤖 3. Behavioral Invariants Across Both Worlds: The Llama 4 Scout Case Study")
    lines.append("")
    lines.append("An extraordinarily consistent empirical finding across both independent projects is the behavior of **Meta's Llama 4 Scout**:")
    lines.append("")
    lines.append("1. **Task-Completion Bias:** In both the Evolution Sandbox and the Synthetic Agora, Llama 4 Scout exhibits an intense drive to achieve an objective, formulate a proof or script, verify output existence, and then **self-terminate** (`exit.txt`, `conclusion.txt`, `SYN-003`).")
    lines.append("2. **RLHF/RLAIF Artifact:** This behavior is an inherent consequence of post-training alignment for benchmark completion, in stark contrast to models with open-ended dialectic tendencies (e.g. MiniMax M3, Qwen 72B, Claude Haiku) which continue expanding parameter sweeps and synthesizing cross-domain connections.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🔮 4. Future Convergence & Cross-Pollination Roadmap")
    lines.append("As both projects continue their nightly autonomous execution on GitHub Actions:")
    lines.append("1. **The Dialectic Migration:** When the Sandbox discovers a new chaotic organism (e.g. Gray-Scott Turing patterns or Collatz attractors), the Agora can ingest it as an empirical challenge to be mathematically proven or refuted.")
    lines.append("2. **Living Double-Chronicle:** Periodically update `THE_GREAT_DIVERGENCE.md` to track how truth-seeking (Agora) versus creativity-seeking (Sandbox) diverge over hundreds of machine generations.")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated Great Divergence Chronicle: {OUTPUT_FILE}")

if __name__ == "__main__":
    analyze_great_divergence()
