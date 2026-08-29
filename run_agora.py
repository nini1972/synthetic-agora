import os
import time
import argparse
from engine import run_loop
from agora_graph import EpistemicGraph

def main():
    parser = argparse.ArgumentParser(description="Run the Synthetic Agora Multi-Agent Ecosystem")
    parser.add_argument(
        "--instances",
        type=str,
        default="gemini_3_1_flash_lite,claude_haiku,llama_4_scout,kimi_code,minimax_m3",
        help="Comma-separated list of agent instances"
    )
    parser.add_argument("--ticks", type=int, default=3, help="Number of global rounds")
    parser.add_argument("--delay", type=float, default=2.5, help="Delay between turns in seconds")
    args = parser.parse_args()

    instances = [i.strip() for i in args.instances.split(",") if i.strip()]
    
    print("=" * 80)
    print("🏛️  THE SYNTHETIC AGORA — MULTI-MODEL SOVEREIGN ECOSYSTEM")
    print("=" * 80)
    print(f"Active Agents: {instances}")
    print(f"Rounds: {args.ticks} | Turn Delay: {args.delay}s")
    print("=" * 80)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    for inst in instances:
        os.makedirs(os.path.join(base_dir, "instances", inst, "agent_workspace"), exist_ok=True)
        os.makedirs(os.path.join(base_dir, "instances", inst, "logs"), exist_ok=True)

    for tick in range(args.ticks):
        print(f"\n{'='*80}")
        print(f"  AGORA GLOBAL CYCLE {tick + 1} / {args.ticks}")
        print(f"{'='*80}")
        
        for instance in instances:
            print(f"\n>>> [Activating Mind: {instance}] <<<")
            try:
                run_loop(instance, ticks=1)
            except Exception as inst_err:
                print(f"❌ Error during execution of '{instance}': {str(inst_err)}")
            time.sleep(args.delay)

    graph = EpistemicGraph()
    stats = graph.get_summary_stats()
    print("\n" + "=" * 80)
    print("📊 AGORA CYCLE SUMMARY TELEMETRY")
    print("=" * 80)
    print(f"Total Nodes in Epistemic DAG: {stats['total_nodes']}")
    print(f"Canon Verified Theorems: {stats['canon_verified_count']}")
    print(f"Status Distribution: {stats['status_distribution']}")
    print(f"Lineage Contributions: {stats['family_contributions']}")
    print("=" * 80)
    print("Open 'agora_dashboard.html' in your browser to explore the living graph and canon.")
    print("=" * 80)

if __name__ == "__main__":
    main()
