import urllib.request
import json

req = urllib.request.Request("https://openrouter.ai/api/v1/models")
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))

models = data.get("data", [])
print(f"Total models on OpenRouter: {len(models)}")

print("\n--- 01-AI / YI MODELS ---")
for m in models:
    mid = m.get("id", "")
    if "yi" in mid.lower() or "01-ai" in mid.lower():
        tools = "tools" in m.get("supported_parameters", [])
        print(f"{mid:45} | Tools: {tools} | Name: {m.get('name', '')}")

print("\n--- XIAOMI / MIMO MODELS ---")
for m in models:
    mid = m.get("id", "")
    if "mimo" in mid.lower() or "xiaomi" in mid.lower():
        tools = "tools" in m.get("supported_parameters", [])
        print(f"{mid:45} | Tools: {tools} | Name: {m.get('name', '')}")

print("\n--- OTHER EXCELLENT NEW CANDIDATES ---")
for m in models:
    mid = m.get("id", "")
    if any(k in mid.lower() for k in ["amazon/nova", "cohere/command-r", "nvidia/nemotron", "stepfun", "deepseek-r1"]):
        tools = "tools" in m.get("supported_parameters", [])
        print(f"{mid:45} | Tools: {tools} | Name: {m.get('name', '')}")
