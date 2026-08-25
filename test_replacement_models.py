import sys
import os
import urllib.request
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

api_key = os.environ.get("OPENROUTER_API_KEY", "")
if not api_key:
    env_path = "config/.env"
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("OPENROUTER_API_KEY="):
                    api_key = line.strip().split("=", 1)[1].strip("\"'")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

candidates = [
    "meta-llama/llama-3.3-70b-instruct",
    "amazon/nova-pro-v1",
    "mistralai/mistral-large-2407",
    "cohere/command-r-plus-08-2024",
    "anthropic/claude-sonnet-4",
    "anthropic/claude-haiku-4.5"
]

print("Testing top candidates on OpenRouter...\n")

for test_model in candidates:
    payload = {
        "model": test_model,
        "messages": [{"role": "user", "content": "Query the epistemic graph for UNDER_REVIEW nodes"}],
        "tools": [{
            "type": "function",
            "function": {
                "name": "query_epistemic_graph",
                "description": "Query the knowledge graph",
                "parameters": {
                    "type": "object",
                    "properties": {"status": {"type": "string"}}
                }
            }
        }],
        "max_tokens": 80
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            choice = data.get("choices", [{}])[0].get("message", {})
            has_tool = "tool_calls" in choice
            print(f"SUCCESS {test_model:35} -> Tool call emitted: {has_tool}")
    except Exception as e:
        print(f"ERROR   {test_model:35} -> {e}")
