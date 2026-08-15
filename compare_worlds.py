import os
import sys
import io
import json
import glob
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def analyze_baseline_world(baseline_dir: str) -> dict:
    if not os.path.exists(baseline_dir):
        return {"error": "Baseline world not found"}
        
    shared_space = os.path.join(baseline_dir, "instances", "shared_space")
    instances_dir = os.path.join(baseline_dir, "instances")
    
    shared_files = []
    if os.path.exists(shared_space):
        shared_files = [f for f in os.listdir(shared_space) if os.path.isfile(os.path.join(shared_space, f))]
        
    instance_names = []
    if os.path.exists(instances_dir):
        instance_names = [d for d in os.listdir(instances_dir) if os.path.isdir(os.path.join(instances_dir, d)) and d != "shared_space"]
        
    md_files = [f for f in shared_files if f.endswith(".md")]
    py_files = [f for f in shared_files if f.endswith(".py")]
    png_files = [f for f in shared_files if f.endswith(".png") or f.endswith(".gif")]
    html_files = [f for f in shared_files if f.endswith(".html")]

    return {
        "world_name": "Evolution Sandbox (Baseline)",
        "active_instances_count": len(instance_names),
        "total_shared_artifacts": len(shared_files),
        "markdown_notes_count": len(md_files),
        "code_scripts_count": len(py_files),
        "visual_charts_count": len(png_files),
        "dashboards_count": len(html_files),
        "verification_system": "None (Ad-hoc unstructured file drops)",
        "governance_model": "Unconstrained free-form emergence"
    }

def analyze_agora_world(agora_dir: str) -> dict:
    if not os.path.exists(agora_dir):
        return {"error": "Agora world not found"}

    graph_path = os.path.join(agora_dir, "instances", "shared_agora", "knowledge_graph.json")
    dispatches_dir = os.path.join(agora_dir, "instances", "shared_agora", "dispatches")
    instances_dir = os.path.join(agora_dir, "instances")

    nodes = {}
    if os.path.exists(graph_path):
        try:
            with open(graph_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                nodes = data.get("nodes", {})
        except Exception:
            pass

    dispatches_count = 0
    if os.path.exists(dispatches_dir):
        dispatches_count = len(glob.glob(os.path.join(dispatches_dir, "*.json")))

    instance_names = []
    if os.path.exists(instances_dir):
        instance_names = [d for d in os.listdir(instances_dir) if os.path.isdir(os.path.join(instances_dir, d)) and d != "shared_agora"]

    status_counts = {}
    verifications_total = 0
    for n in nodes.values():
        st = n.get("status", "UNKNOWN")
        status_counts[st] = status_counts.get(st, 0) + 1
        verifications_total += len(n.get("verifications", []))

    return {
        "world_name": "Synthetic Agora (Epistemic Commons)",
        "active_instances_count": len(instance_names),
        "epistemic_dag_nodes": len(nodes),
        "canon_verified_theorems": status_counts.get("CANON_VERIFIED", 0),
        "under_review_hypotheses": status_counts.get("UNDER_REVIEW", 0) + status_counts.get("UNVERIFIED_HYPOTHESIS", 0),
        "cross_model_verifications_count": verifications_total,
        "inter_agent_dispatches_count": dispatches_count,
        "status_distribution": status_counts,
        "verification_system": "Cross-Family Quorum (Anti-Echo Requirement >= 2 Lineages)",
        "governance_model": "Epistemic Meritocracy & Guild Specialization"
    }

def print_comparison_report():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    baseline_dir = os.path.join(base_dir, "evolution_sandbox")
    agora_dir = os.path.join(base_dir, "synthetic_agora")

    baseline = analyze_baseline_world(baseline_dir)
    agora = analyze_agora_world(agora_dir)

    print("=" * 80)
    print("🌍 COMPARATIVE EVOLUTIONARY TELEMETRY REPORT")
    print(f"Generated at: {utc_now_iso()} UTC")
    print("=" * 80)
    
    print(f"\n[1] BASELINE WORLD: {baseline.get('world_name')}")
    print(f"  • Registered Instances:      {baseline.get('active_instances_count')}")
    print(f"  • Total Shared Artifacts:    {baseline.get('total_shared_artifacts')}")
    print(f"  • Markdown Notes:            {baseline.get('markdown_notes_count')}")
    print(f"  • Visual Charts & Gifs:      {baseline.get('visual_charts_count')}")
    print(f"  • Executable Code Scripts:   {baseline.get('code_scripts_count')}")
    print(f"  • Verification Mechanism:    {baseline.get('verification_system')}")
    
    print(f"\n[2] AGORA WORLD: {agora.get('world_name')}")
    print(f"  • Registered Instances:      {agora.get('active_instances_count')}")
    print(f"  • Epistemic DAG Nodes:       {agora.get('epistemic_dag_nodes')}")
    print(f"  • Canon Verified Theorems:   {agora.get('canon_verified_theorems')}")
    print(f"  • Hypotheses Under Review:   {agora.get('under_review_hypotheses')}")
    print(f"  • Cross-Model Peer Reviews:  {agora.get('cross_model_verifications_count')}")
    print(f"  • Inter-Agent Dispatches:    {agora.get('inter_agent_dispatches_count')}")
    print(f"  • Verification Quorum:       {agora.get('verification_system')}")
    print(f"  • Governance Paradigm:       {agora.get('governance_model')}")
    print("=" * 80)

if __name__ == "__main__":
    print_comparison_report()
