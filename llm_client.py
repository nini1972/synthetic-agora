import os
import sys
import json
import time
from dotenv import load_dotenv
from litellm import completion

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def prune_history(history: list, max_messages: int = 24, max_content_chars: int = 30000) -> list:
    if not history:
        return []

    system_msg = None
    work_history = list(history)
    if work_history and work_history[0].get("role") == "system":
        system_msg = dict(work_history.pop(0))

    deduped = []
    for msg in work_history:
        if msg.get("role") == "assistant" and not msg.get("tool_calls"):
            if deduped and deduped[-1].get("role") == "assistant" and not deduped[-1].get("tool_calls"):
                continue
        deduped.append(msg)

    if len(deduped) <= max_messages:
        pruned = [dict(m) for m in deduped]
    else:
        slice_start = len(deduped) - max_messages
        while slice_start < len(deduped) and deduped[slice_start].get("role") == "tool":
            slice_start += 1
        pruned = [dict(m) for m in deduped[slice_start:]]
    
    for msg in pruned:
        content = msg.get("content")
        if isinstance(content, str) and len(content) > max_content_chars:
            head = content[:15000]
            tail = content[-15000:]
            msg["content"] = f"{head}\n\n... [TRUNCATED FOR CONTEXT] ...\n\n{tail}"

    if system_msg:
        pruned.insert(0, system_msg)
    elif pruned and pruned[0].get("role") == "assistant":
        pruned.insert(0, {"role": "user", "content": "Please continue with your action in the Agora."})

    return pruned

def merge_consecutive_messages(messages: list) -> list:
    merged = []
    for msg in messages:
        if not merged:
            merged.append(msg)
            continue
        prev = merged[-1]
        if msg["role"] == prev["role"] and msg["role"] in ("assistant", "user"):
            if msg.get("content"):
                if prev.get("content"):
                    prev["content"] = prev["content"] + "\n\n" + msg["content"]
                else:
                    prev["content"] = msg["content"]
            if "tool_calls" in msg and msg["tool_calls"]:
                if "tool_calls" not in prev:
                    prev["tool_calls"] = []
                existing_ids = {tc.get("id") for tc in prev["tool_calls"]}
                for tc in msg["tool_calls"]:
                    if tc.get("id") not in existing_ids:
                        prev["tool_calls"].append(tc)
        else:
            merged.append(msg)
    return merged

def resolve_agent_model(instance_name: str) -> str:
    """Resolves the authentic model endpoint for a given instance."""
    # 1. Check instance-level .env override
    if instance_name:
        instance_dotenv = os.path.abspath(os.path.join(os.path.dirname(__file__), "instances", instance_name, ".env"))
        if os.path.exists(instance_dotenv):
            load_dotenv(dotenv_path=instance_dotenv, override=True)
            custom_model = os.getenv("AGENT_MODEL")
            if custom_model:
                return custom_model

    # 2. Check centralized model_routing.json mapping
    if instance_name:
        routing_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "config", "model_routing.json"))
        if os.path.exists(routing_path):
            try:
                with open(routing_path, "r", encoding="utf-8") as f:
                    routing = json.load(f)
                    if instance_name in routing:
                        return routing[instance_name]
            except Exception as e:
                print(f"[Model Resolver] Warning: Failed to load model routing ({e})")

    # 3. Global fallback environment variable
    return os.getenv("DEFAULT_FALLBACK_MODEL", "openrouter/google/gemini-2.5-flash")

def generate_next_action(system_prompt: str, history: list, tools: list) -> dict:
    global_dotenv = os.path.abspath(os.path.join(os.path.dirname(__file__), "config", ".env"))
    load_dotenv(dotenv_path=global_dotenv, override=False)

    instance_name = os.getenv("ACTIVE_INSTANCE", "")
    agent_model = resolve_agent_model(instance_name)

    print(f"🎯 [Lineage Engine] Routing '{instance_name}' to -> {agent_model}")

    messages = [{"role": "system", "content": system_prompt}]
    
    pruned = prune_history(history)
    for entry in pruned:
        msg = {
            "role": entry["role"],
            "content": entry.get("content", ""),
        }
        if entry["role"] == "assistant" and "tool_calls" in entry and entry["tool_calls"]:
            msg["tool_calls"] = []
            for tc in entry["tool_calls"]:
                func = tc.get("function", {})
                args = func.get("arguments", "{}")
                if isinstance(args, str):
                    try:
                        parsed = json.loads(args)
                        args = json.dumps(parsed)
                    except Exception:
                        pass
                else:
                    args = json.dumps(args)
                msg["tool_calls"].append({
                    "id": tc.get("id"),
                    "type": "function",
                    "function": {
                        "name": func.get("name"),
                        "arguments": args
                    }
                })
        if entry["role"] == "tool":
            msg["tool_call_id"] = entry["tool_call_id"]
            msg["name"] = entry.get("name")
        messages.append(msg)

    messages = merge_consecutive_messages(messages)

    if messages and messages[-1]["role"] == "assistant":
        messages.append({"role": "user", "content": "You stated your intention above. Please proceed by invoking the appropriate tool function."})

    retries = 5
    for attempt in range(retries):
        try:
            response = completion(
                model=agent_model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=4096,
                timeout=90,
            )
            message = response.choices[0].message
            
            # Extract content or reasoning tokens
            content_text = message.content or getattr(message, "reasoning_content", "") or ""

            if message.tool_calls:
                tool_call = message.tool_calls[0]
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except Exception as json_err:
                    return {
                        "type": "json_error",
                        "content": f"JSON Decoding Error: {str(json_err)}. Received arguments string: {tool_call.function.arguments}"
                    }
                return {
                    "type": "tool_call",
                    "tool_call_id": tool_call.id,
                    "tool_name": tool_call.function.name,
                    "arguments": arguments,
                    "content": content_text
                }
            else:
                return {
                    "type": "thought",
                    "content": content_text
                }
                
        except Exception as e:
            err_str = str(e).lower()
            if attempt < retries - 1 and ("rate" in err_str or "limit" in err_str or "429" in err_str or "400" in err_str or "delimit" in err_str):
                print(f"[Rate limited ({agent_model}). Sleeping 15s before retry {attempt + 2}/{retries}...] ({str(e)})")
                time.sleep(15)
                continue
            return {
                "type": "error",
                "content": f"LLM Error ({agent_model}): {str(e)}"
            }
    
    return {
        "type": "error",
        "content": f"LLM Error ({agent_model}): Max retries exceeded without action."
    }
