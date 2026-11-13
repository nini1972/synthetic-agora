import os
import sys
import re
import time
import argparse
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from llm_client import generate_next_action
from tools import TOOLS_SCHEMA, AVAILABLE_TOOLS
from memory import load_history, append_to_history, log_agora_event
from agora_graph import EpistemicGraph, detect_model_family
from protocols import read_inbox
from commons_chat import build_turn_digest, ingest_human_dropbox

PROMPT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "config", "initial_prompt.txt"))

DYNAMICAL_INVARIANT_KEYWORDS = (
    "invariant", "lyapunov", "spectral", "eigenvalue", "lambda_1", "betti",
    "euler characteristic", "scaling", "critical exponent", "adler", "kuramoto",
    "lenia", "soliton", "chimera", "hysteresis", "conservation", "bifurcation",
    "universality", "rqa", "takens", "attractor", "phase transition", "ergodic",
)


def _score_node_for_priority(node: dict, active_family: str) -> tuple:
    """
    Computes an epistemic priority tuple for a pending DAG node from another model family:
    1. Near-Canon Quorum (+25): already UNDER_REVIEW (needs just 1 more distinct family review to reach CANON_VERIFIED).
    2. Dynamical Invariant Focus (+30): investigates dynamical invariants, scaling laws, spectral/topological bounds.
    3. Recency: higher numeric node ID.
    """
    title = str(node.get("title") or "")
    summary = str(node.get("summary") or node.get("claim") or "")
    tags = " ".join(str(t) for t in (node.get("tags") or []))
    text_low = f"{title} {summary} {tags}".lower()

    is_dyn_invariant = any(kw in text_low for kw in DYNAMICAL_INVARIANT_KEYWORDS)
    verifs = node.get("verifications") or []
    endorse_families = {
        (v.get("verifier_family") or v.get("reviewer_family"))
        for v in verifs
        if isinstance(v, dict)
        and (v.get("verifier_family") or v.get("reviewer_family"))
        and str(v.get("verdict", "")).lower() in ("endorse", "verified", "confirm")
    }
    all_verifier_families = {
        (v.get("verifier_family") or v.get("reviewer_family"))
        for v in verifs
        if isinstance(v, dict) and (v.get("verifier_family") or v.get("reviewer_family"))
    }
    is_near_quorum = len(endorse_families) >= 1 or len(all_verifier_families) >= 1
    is_fresh_unreviewed = len(all_verifier_families) == 0

    nid = str(node.get("id") or "")
    m_num = re.search(r"-(\d+)$", nid)
    num_id = int(m_num.group(1)) if m_num else 0

    score = (
        (30 if is_dyn_invariant else 0)
        + (25 if is_near_quorum else (15 if is_fresh_unreviewed and num_id >= 180 else 0))
        + min(num_id / 20.0, 12.0)
    )
    badges = []
    if is_dyn_invariant:
        badges.append("Dynamical Invariant")
    if is_near_quorum:
        badges.append(f"{len(all_verifier_families)}/2 Quorum — 1 Review to Canon")
    elif is_fresh_unreviewed:
        badges.append("0/2 Reviews — Needs First Replication")
    return score, num_id, badges


def get_agora_context_summary(instance_name: str) -> str:
    try:
        graph = EpistemicGraph()
        family = detect_model_family(instance_name)
        inbox = read_inbox(instance_name, unread_only=True, mark_as_read=False)
        
        lines = []
        if inbox:
            lines.append(f"📬 INBOX: You have {len(inbox)} unread dispatch(es) from peers! Call 'read_agent_inbox' to read them.")
            for d in inbox[:2]:
                lines.append(f"  - From {d.get('sender_instance')}: [{d.get('action_requested','review').upper()}] {d.get('subject')}")
        
        # Priority Tier 1: Ranked Peer-Review Queue (Focus on Dynamical Invariants & Near-Canon Quorum)
        eligible_candidates = []
        for node in graph.nodes.values():
            if not isinstance(node, dict):
                continue
            st = node.get("status")
            if st not in ("UNDER_REVIEW", "UNVERIFIED_HYPOTHESIS"):
                continue
            if node.get("author_family") == family or node.get("author_instance") == instance_name:
                continue
            verifs = node.get("verifications") or []
            already_reviewed_by_family = any(
                isinstance(v, dict)
                and (
                    (v.get("verifier_family") or v.get("reviewer_family")) == family
                    or (v.get("verifier_instance") or v.get("reviewer_instance")) == instance_name
                )
                for v in verifs
            )
            if already_reviewed_by_family:
                continue
            score, num_id, badges = _score_node_for_priority(node, family)
            eligible_candidates.append((score, num_id, badges, node))

        eligible_candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
        if eligible_candidates:
            lines.append(
                f"🎯 PRIORITY TIER 1 — DYNAMICAL INVARIANTS & NEAR-CANON QUORUM "
                f"({len(eligible_candidates)} anti-echo eligible node(s) awaiting your family's verification):"
            )
            for score, _, badges, cand in eligible_candidates[:3]:
                badge_str = f" [{' | '.join(badges)}]" if badges else ""
                lines.append(
                    f"  - [{cand.get('id')}]{badge_str} {cand.get('title')} "
                    f"(by {cand.get('author_instance')}, status={cand.get('status')})"
                )

        # Check if this model family has authored nodes that are UNDER_REVIEW or being debated
        authored_under_review = graph.query(author_family=family, status="UNDER_REVIEW", limit=5)
        if authored_under_review:
            lines.append(f"⚖️ YOUR THEORIES UNDER PEER SCRUTINY: {len(authored_under_review)} node(s) from your lineage are UNDER_REVIEW:")
            for c in authored_under_review[:2]:
                rev_count = len(c.get("verifications", []))
                lines.append(f"  - [{c.get('id')}] {c.get('title')} ({rev_count} review(s)). Actively defend, run Python stress-tests, or post refinements!")

        # Priority Tier 2: Deduplicated Inter-World Embassy Queue (World A Frontier + Universe Knowledge Academy)
        embassy_inbox = os.path.join(os.path.dirname(__file__), "instances", "shared_agora", "embassy", "inbox")
        if os.path.exists(embassy_inbox):
            all_md = [f for f in os.listdir(embassy_inbox) if f.endswith(".md")]
            # Canonical gate-accessioned files: DOSSIER_NNN_*.md
            world_a_canonical = []
            uk_canonical = []
            for f in all_md:
                m_acc = re.match(r"^DOSSIER_(\d+)_(.+)\.md$", f, re.IGNORECASE)
                if m_acc:
                    acc_num = int(m_acc.group(1))
                    rest = m_acc.group(2)
                    if rest.upper().startswith("UK_"):
                        uk_canonical.append((acc_num, f))
                    else:
                        world_a_canonical.append((acc_num, f))
            world_a_canonical.sort(key=lambda x: x[0], reverse=True)
            uk_canonical.sort(key=lambda x: x[0], reverse=True)
            uk_direct = sorted([f for f in all_md if f.upper().startswith("DOSSIER-UK-")])

            # Identify newest World A Frontier Dossiers not yet formalized in the DAG (preferring peers' dossiers)
            dag_blob = json.dumps(list(graph.nodes.values()))
            unformalized_wa = [
                (num, fn) for num, fn in world_a_canonical
                if f"DOSSIER-{num:03d}" not in dag_blob
                and f"DOSSIER_{num:03d}" not in dag_blob
                and (not instance_name or instance_name.lower() not in fn.lower())
            ]
            top_wa = (unformalized_wa or world_a_canonical)[:2]
            uk_pool = uk_direct if uk_direct else [fn for _, fn in uk_canonical]
            if uk_pool:
                rot = sum(ord(ch) for ch in (instance_name or "agora")) % len(uk_pool)
                top_uk = [uk_pool[(rot + k) % len(uk_pool)] for k in range(min(2, len(uk_pool)))]
            else:
                top_uk = []

            total_distinct = len(world_a_canonical) + max(len(uk_canonical), len(uk_direct))
            if total_distinct > 0:
                lines.append(
                    f"🌐 PRIORITY TIER 2 — INTER-WORLD EMBASSY QUEUE: {total_distinct} distinct Dossiers in 'shared_agora/embassy/inbox/' "
                    f"({len(world_a_canonical)} World A Empirical Frontier Dossiers, {max(len(uk_canonical), len(uk_direct))} Universe Knowledge Academy Synthesis Dossiers):"
                )
                for num, doc in top_wa:
                    lines.append(f"  - [World A Frontier #{num:03d} — Unformalized] shared_agora/embassy/inbox/{doc}")
                for doc in top_uk:
                    lines.append(f"  - [Academy Theory & Citations] shared_agora/embassy/inbox/{doc}")
        
        lines.append("⚡ ACTION DIRECTIVE: Focus empirical verification on dynamical invariants (Priority Tier 1) and unformalized Frontier/Academy dossiers (Priority Tier 2). Every turn requires concrete empirical or theoretical work (running Python simulations via run_command/submit_world_c_job, posting/verifying DAG nodes, or collaborating in Colleague Commons). Do NOT spend turns in passive read-only observation.")

        if lines:
            return "\n[AGORA LIVE TELEMETRY & EPISTEMIC PRIORITY QUEUE]\n" + "\n".join(lines) + "\n"
        return ""
    except Exception as e:
        return f"\n[Agora Context Warning: {e}]\n"

def run_loop(instance: str, ticks: int = 1):
    os.environ["ACTIVE_INSTANCE"] = instance
    base_dir = os.path.dirname(os.path.abspath(__file__))
    instance_dir = os.path.join(base_dir, "instances", instance)
    workspace_dir = os.path.join(instance_dir, "agent_workspace")
    os.makedirs(workspace_dir, exist_ok=True)
    os.makedirs(os.path.join(instance_dir, "logs"), exist_ok=True)

    if not os.path.exists(PROMPT_FILE):
        print(f"Error: Initial prompt not found at {PROMPT_FILE}")
        return
        
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        base_system_prompt = f.read()

    print(f"🏛️ Starting Synthetic Agora turn for instance '{instance}' ({ticks} tick(s))...")
    
    for i in range(ticks):
        print(f"\n--- Turn Tick {i+1}/{ticks} ---")
        history = load_history()
        
        # Inject live Agora state into system prompt
        telemetry = get_agora_context_summary(instance)
        if i == 0:
            try:
                ingest_human_dropbox(base_dir)
                chat_digest = build_turn_digest(instance or "agora_scholar", base_dir=base_dir, mark_seen=True)
            except Exception as chat_err:
                print(f"[Commons Chat Warning]: {chat_err}")
                chat_digest = ""
            active_system_prompt = base_system_prompt + telemetry + chat_digest
        else:
            active_system_prompt = base_system_prompt + telemetry
        
        print("🧠 Thinking...")
        action = generate_next_action(active_system_prompt, history, TOOLS_SCHEMA)
        
        if action["type"] == "error":
            print(f"❌ {action['content']}")
            break
            
        elif action["type"] == "json_error":
            print(f"⚠️ JSON Parsing Error: {action['content']}")
            append_to_history({
                "role": "user",
                "content": f"JSON Parsing Error: {action['content']}. Ensure arguments are valid JSON with properly escaped quotes."
            })
            continue
            
        elif action["type"] == "thought":
            print(f"💭 Agent Thought:\n{action['content']}")
            append_to_history({
                "role": "assistant",
                "content": action["content"]
            })
            log_agora_event("thought", instance, {"content": action["content"]})
            
        elif action["type"] == "tool_call":
            if action.get("content"):
                print(f"💭 Agent Thought: {action['content']}")
                
            raw_tool_calls = action.get("all_tool_calls") or [{
                "tool_call_id": action["tool_call_id"],
                "tool_name": action["tool_name"],
                "arguments": action["arguments"],
            }]
            tool_calls_list = []
            seen_tc_keys = set()
            for tc_cand in raw_tool_calls:
                try:
                    tc_key = (tc_cand["tool_name"], json.dumps(tc_cand["arguments"], sort_keys=True, ensure_ascii=False))
                except Exception:
                    tc_key = (tc_cand["tool_name"], str(tc_cand["arguments"]))
                if tc_key not in seen_tc_keys:
                    seen_tc_keys.add(tc_key)
                    tool_calls_list.append(tc_cand)
                if len(tool_calls_list) >= 3:
                    break
            
            for idx, tc_item in enumerate(tool_calls_list):
                tool_name = tc_item["tool_name"]
                arguments = tc_item["arguments"]
                tool_call_id = tc_item["tool_call_id"]
                
                print(f"⚡ Action: Call tool '{tool_name}' with args {json.dumps(arguments, ensure_ascii=False)}")
                
                assistant_message = {
                    "role": "assistant",
                    "content": action.get("content", "") if idx == 0 else "",
                    "tool_calls": [{
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps(arguments, ensure_ascii=False)
                        }
                    }]
                }
                append_to_history(assistant_message)
                
                if tool_name in AVAILABLE_TOOLS:
                    try:
                        # Guard against repeating a command that already timed out in recent history
                        prev_timed_out = False
                        repeat_read_count = 0
                        arg_canon = json.dumps(arguments, sort_keys=True, ensure_ascii=False) if isinstance(arguments, dict) else str(arguments)
                        for h_idx in range(max(0, len(history) - 20), len(history)):
                            h_msg = history[h_idx]
                            if h_msg.get("role") == "assistant" and h_msg.get("tool_calls"):
                                for h_tc in h_msg["tool_calls"]:
                                    h_fn = h_tc.get("function", {})
                                    if h_fn.get("name") == tool_name:
                                        try:
                                            h_args = json.dumps(json.loads(h_fn.get("arguments", "{}")), sort_keys=True, ensure_ascii=False)
                                        except Exception:
                                            h_args = str(h_fn.get("arguments", ""))
                                        if h_args == arg_canon:
                                            repeat_read_count += 1
                                            if tool_name == "run_command" and h_idx + 1 < len(history):
                                                nxt_obs = str(history[h_idx + 1].get("content", ""))
                                                if "timed out" in nxt_obs.lower():
                                                    prev_timed_out = True
                        if tool_name == "run_command" and prev_timed_out:
                            result = (
                                "Error: This exact command ALREADY timed out (>60s) in a previous turn. "
                                "Do NOT re-run the same timed-out command locally — either optimize/vectorize the script, "
                                "reduce grid/step counts, or offload heavy sweeps to World C via 'submit_world_c_job'."
                            )
                        elif isinstance(arguments, dict):
                            result = AVAILABLE_TOOLS[tool_name](**arguments)
                        elif isinstance(arguments, list) and len(arguments) > 0 and isinstance(arguments[0], dict):
                            result = AVAILABLE_TOOLS[tool_name](**arguments[0])
                        else:
                            result = f"Error: Tool arguments must be a JSON dictionary object, got {type(arguments).__name__}."
                        if tool_name in ("read_file", "read_chat") and repeat_read_count >= 2:
                            result = (
                                str(result)
                                + "\n\n[Anti-Loop Notice: You have ALREADY read this exact file/thread multiple times in recent turns. "
                                "Do NOT call read_file or read_chat on it again; proceed immediately to a concrete action "
                                "(e.g., submit_world_c_job, post_epistemic_node, peer_verify_node, write_file, or post_chat).]"
                            )
                    except TypeError as e:
                        import inspect
                        sig_params = [p for p in inspect.signature(AVAILABLE_TOOLS[tool_name]).parameters.keys() if p != "kwargs"]
                        result = f"TypeError: {str(e)}. Allowed parameters for '{tool_name}': {sig_params}"
                    except Exception as e:
                        result = f"Error executing tool '{tool_name}': {str(e)}"
                else:
                    result = f"Error: Tool '{tool_name}' not found."
                    
                preview = str(result)[:400] + ("..." if len(str(result)) > 400 else "")
                print(f"📋 Result:\n{preview}")
                
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "name": tool_name,
                    "content": str(result)
                }
                append_to_history(tool_message)
                log_agora_event("tool_call", instance, {
                    "tool": tool_name,
                    "args": arguments,
                    "result_preview": preview
                })

        time.sleep(2)
        
    print(f"\nTurn complete for {instance}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Synthetic Agora Engine")
    parser.add_argument("--instance", type=str, required=True, help="Name of the agent instance")
    parser.add_argument("--ticks", type=int, default=1, help="Number of ticks")
    args = parser.parse_args()
    
    run_loop(args.instance, args.ticks)
