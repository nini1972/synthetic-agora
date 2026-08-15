import os
import json
from dotenv import load_dotenv
from litellm import completion

load_dotenv(os.path.join(os.path.dirname(__file__), "config", ".env"))

candidate_models = {
    "claude_haiku": ["openrouter/anthropic/claude-3-haiku", "openrouter/anthropic/claude-3.5-haiku"],
    "claude_sonnet": ["openrouter/anthropic/claude-3.5-sonnet-20241022", "openrouter/anthropic/claude-3-5-sonnet-20241022", "openrouter/anthropic/claude-3-sonnet"],
    "gemini_flash": ["openrouter/google/gemini-2.5-flash", "openrouter/google/gemini-3.7-flash"],
    "gemini_3_1_flash_lite": ["openrouter/google/gemini-3.1-flash-lite-preview", "openrouter/google/gemini-2.5-flash"],
    "llama_4_scout": ["openrouter/meta-llama/llama-4-scout", "openrouter/meta-llama/llama-3.3-70b-instruct"],
    "llama_70b": ["openrouter/meta-llama/llama-3.3-70b-instruct", "openrouter/meta-llama/llama-3.1-70b-instruct"],
    "qwen_coder": ["openrouter/qwen/qwen-2.5-coder-32b-instruct", "openrouter/qwen/qwen3.8-27b"],
    "deepseek": ["openrouter/deepseek/deepseek-chat", "openrouter/deepseek/deepseek-v4-flash-0731"],
    "minimax": ["openrouter/minimax/minimax-01", "openrouter/minimax/minimax-m3"],
    "glm": ["openrouter/z-ai/glm-5.2", "openrouter/z-ai/glm-4-9b-chat"],
    "kimi": ["openrouter/moonshotai/kimi-k1.5", "openrouter/moonshotai/kimi-k2.7-code"]
}

print("PROBING CANDIDATE OPENROUTER MODELS...")
working_mapping = {}

for role, candidates in candidate_models.items():
    for model in candidates:
        try:
            resp = completion(
                model=model,
                messages=[{"role": "user", "content": "Ping. Respond 'OK'"}],
                max_tokens=10,
                timeout=15
            )
            content = resp.choices[0].message.content or ""
            reasoning = getattr(resp.choices[0].message, "reasoning_content", "") or ""
            if content or reasoning:
                print(f"  [FOUND] {role:15} -> {model} (Response: {content.strip() or 'Reasoning OK'})")
                working_mapping[role] = model
                break
        except Exception as e:
            continue
    if role not in working_mapping:
        print(f"  [FAILED] {role:15} -> No working candidate found.")

with open(os.path.join(os.path.dirname(__file__), "config", "working_model_routing.json"), "w") as f:
    json.dump(working_mapping, f, indent=2)

print("\nSaved working routing to config/working_model_routing.json")
