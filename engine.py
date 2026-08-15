import os
import sys
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
from agora_graph import EpistemicGraph
from protocols import read_inbox

PROMPT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "config", "initial_prompt.txt"))

def get_agora_context_summary(instance_name: str) -> str:
    try:
        graph = EpistemicGraph()
        unverified = graph.query(status="UNVERIFIED_HYPOTHESIS", limit=5)
        under_review = graph.query(status="UNDER_REVIEW", limit=5)
        inbox = read_inbox(instance_name, unread_only=True)
        
        lines = []
        if inbox:
            lines.append(f"📬 INBOX: You have {len(inbox)} unread dispatch(es) from peers! Call 'read_agent_inbox' to read them.")
            for d in inbox[:2]:
                lines.append(f"  - From {d.get('sender_instance')}: [{d.get('action_requested','review').upper()}] {d.get('subject')}")
        
        pending_review = unverified + under_review
        if pending_review:
            other_family_nodes = [n for n in pending_review if n.get("author_instance") != instance_name]
            if other_family_nodes:
                lines.append(f"🔬 DAG AWAITING PEER REVIEW: There are {len(other_family_nodes)} node(s) from other models needing verification:")
                for n in other_family_nodes[:3]:
                    lines.append(f"  - [{n['id']}] {n['title']} (by {n['author_instance']}, {n.get('author_family')})")
        
        if lines:
            return "\n[AGORA LIVE TELEMETRY]\n" + "\n".join(lines) + "\n"
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
                
            tool_name = action["tool_name"]
            arguments = action["arguments"]
            tool_call_id = action["tool_call_id"]
            
            print(f"⚡ Action: Call tool '{tool_name}' with args {json.dumps(arguments, ensure_ascii=False)}")
            
            assistant_message = {
                "role": "assistant",
                "content": action.get("content", ""),
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
                    result = AVAILABLE_TOOLS[tool_name](**arguments)
                except TypeError as e:
                    result = f"TypeError: {str(e)}. Valid parameters: {list(arguments.keys())}"
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
