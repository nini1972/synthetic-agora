import urllib.request
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

req = urllib.request.Request("https://openrouter.ai/api/v1/models")
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))

models = data.get("data", [])

print("--- ANTHROPIC & MISTRAL MODELS ON OPENROUTER ---")
for m in models:
    mid = m.get("id", "")
    if any(k in mid.lower() for k in ["anthropic", "mistral", "amazon/nova", "cohere/command-r"]):
        tools = "tools" in m.get("supported_parameters", [])
        print(f"{mid:45} | Tools: {tools} | Name: {m.get('name', '')[:30]}")
