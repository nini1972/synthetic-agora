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
    "xiaomi/mimo-v2.5-pro",
    "nvidia/nemotron-3.5-lightning",
    "stepfun/step-3.7-flash",
    "amazon/nova-pro-v1",
    "cohere/command-r-plus-08-2024"
]

print("Probing candidate model tool-calling endpoints on OpenRouter...\n")

for test_model in candidates:
    payload = {
        "model": test_model,
        "messages": [{"role": "user", "content": "Hello, query the graph with status='CANON_VERIFIED'"}],
        "tools": [{
            "type": "function",
            "function": {
                "name": "query_epistemic_graph",
                "description": "Query the knowledge graph",
                "parameters": {
                    "type": "object",
                    "properties": {"status": {"type": "string"}},
                    "required": ["status"]
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
            print(f"✅ {test_model:32} -> SUCCESS (Tool call emitted: {has_tool})")
    except Exception as e:
        print(f"❌ {test_model:32} -> ERROR: {e}")
