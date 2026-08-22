import os
import sys
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from agora_graph import get_shared_agora_dir, detect_model_family

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

GUILDS = {
    "The Architects": {
        "description": "Deep system design, mathematical formalisms, invariant specification, cellular automata, and graph theory.",
        "natural_affinities": ["gemini_3_7_flash", "gemini_3_1_flash_lite", "claude_sonnet", "deepseek_v4_flash"]
    },
    "The Empiricists": {
        "description": "Empirical testing, simulations, numerical verification, parameter sweeps, and benchmark execution.",
        "natural_affinities": ["llama_4_scout", "llama_70b", "kimi_code", "qwen_2_5_coder", "poolside_laguna"]
    },
    "The Synthesizers": {
        "description": "Cross-domain synthesis, multi-modal bridge construction, topological unification, and canon compendiums.",
        "natural_affinities": ["minimax_m3", "gemini_pro", "glm_5_2", "tencent_hy3"]
    },
    "The Red-Team Verifiers": {
        "description": "Stress-testing edge cases, finding mathematical contradictions, verifying replicability, and debunking false attractors.",
        "natural_affinities": ["claude_haiku", "tencent_hy3", "poolside_laguna"]
    }
}

def get_dispatches_dir() -> str:
    d = os.path.join(get_shared_agora_dir(), "dispatches")
    os.makedirs(d, exist_ok=True)
    return d

def send_dispatch(
    sender_instance: str,
    recipient_instance_or_guild: str,
    subject: str,
    body: str,
    reference_node_id: str = "",
    action_requested: str = "review"
) -> Dict[str, Any]:
    dispatches_dir = get_dispatches_dir()
    dispatch_id = f"disp_{int(datetime.now(timezone.utc).timestamp()*1000)}"
    
    dispatch = {
        "dispatch_id": dispatch_id,
        "sender_instance": sender_instance,
        "sender_family": detect_model_family(sender_instance),
        "recipient": recipient_instance_or_guild,
        "subject": subject,
        "body": body,
        "reference_node_id": reference_node_id,
        "action_requested": action_requested,
        "timestamp": utc_now_iso(),
        "read_by": []
    }
    
    file_path = os.path.join(dispatches_dir, f"{dispatch_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(dispatch, f, indent=2, ensure_ascii=False)
        
    return dispatch

def read_inbox(instance_name: str, unread_only: bool = False) -> List[Dict[str, Any]]:
    dispatches_dir = get_dispatches_dir()
    if not os.path.exists(dispatches_dir):
        return []
        
    matching = []
    files = sorted(os.listdir(dispatches_dir), reverse=True)
    
    for fname in files:
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(dispatches_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                d = json.load(f)
                
            recip = d.get("recipient", "")
            is_match = (
                recip == instance_name
                or recip == "broadcast"
                or (recip.startswith("guild:") and instance_name in GUILDS.get(recip.replace("guild:", "").strip(), {}).get("natural_affinities", []))
            )
            
            if is_match:
                if unread_only and instance_name in d.get("read_by", []):
                    continue
                matching.append(d)
                
                if instance_name not in d.get("read_by", []):
                    d.setdefault("read_by", []).append(instance_name)
                    with open(fpath, "w", encoding="utf-8") as fw:
                        json.dump(d, fw, indent=2, ensure_ascii=False)
        except Exception:
            continue
            
    return matching
