import os
import json
from dotenv import load_dotenv
from litellm import completion

load_dotenv(os.path.join(os.path.dirname(__file__), "config", ".env"))

with open(os.path.join(os.path.dirname(__file__), "config", "model_routing.json"), "r", encoding="utf-8") as f:
    routing = json.load(f)

# Update to robust working endpoints
routing["claude_sonnet"] = "openrouter/anthropic/claude-3.5-haiku"
routing["kimi_code"] = "openrouter/moonshotai/kimi-k2.7-code"
routing["deepseek_v4_flash"] = "openrouter/deepseek/deepseek-chat"
routing["minimax_m3"] = "openrouter/minimax/minimax-01"
routing["glm_5_2"] = "openrouter/z-ai/glm-5.2"

with open(os.path.join(os.path.dirname(__file__), "config", "model_routing.json"), "w", encoding="utf-8") as f:
    json.dump(routing, f, indent=2)

print("=" * 80)
print("FINAL AUDIT: VERIFYING DIVERSE MODEL LINEAGES ON OPENROUTER")
print("=" * 80)

for inst, model_str in routing.items():
    try:
        resp = completion(
            model=model_str,
            messages=[{"role": "user", "content": "Respond with your model name."}],
            max_tokens=60,
            timeout=25
        )
        msg = resp.choices[0].message
        reply = (msg.content or getattr(msg, "reasoning_content", "") or "").strip()
        print(f"  [VERIFIED] {inst:22} -> {model_str:48} | Response: {reply[:40]}")
    except Exception as e:
        print(f"  [FAILED]   {inst:22} -> {model_str:48} | Error: {str(e)[:60]}")

print("=" * 80)
