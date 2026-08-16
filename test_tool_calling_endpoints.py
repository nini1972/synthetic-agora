import os
import json
from dotenv import load_dotenv
from litellm import completion

load_dotenv(os.path.join(os.path.dirname(__file__), "config", ".env"))

# Import tools schema from tools.py (once updated)
from tools import TOOLS_SCHEMA

test_candidates = {
    "gemini_3_7_flash": [
        "openrouter/google/gemini-3.7-flash",
        "openrouter/google/gemini-2.5-flash"
    ],
    "minimax": [
        "openrouter/minimax/minimax-m3",
        "openrouter/minimax/minimax-01"
    ],
    "qwen": [
        "openrouter/qwen/qwen-2.5-coder-32b-instruct",
        "openrouter/qwen/qwen-2.5-72b-instruct",
        "openrouter/qwen/qwen3.8-27b",
        "openrouter/qwen/qwen-2.5-coder-32b-instruct:free"
    ]
}

print("=" * 80)
print("TESTING TOOL CALLING SUPPORT ACROSS OPENROUTER CANDIDATES")
print("=" * 80)

for role, models in test_candidates.items():
    print(f"\n--- Testing candidates for: {role} ---")
    for model in models:
        print(f"Testing {model} with TOOLS_SCHEMA...")
        try:
            resp = completion(
                model=model,
                messages=[
                    {"role": "user", "content": "Query the epistemic graph for any unverified hypotheses."}
                ],
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                max_tokens=300,
                timeout=30
            )
            msg = resp.choices[0].message
            print(f"  [SUCCESS] {model}")
            if msg.tool_calls:
                print(f"    -> Tool called: {msg.tool_calls[0].function.name} with args: {msg.tool_calls[0].function.arguments}")
            else:
                print(f"    -> Content text: {msg.content[:60] if msg.content else 'No text'}")
            break
        except Exception as e:
            print(f"  [FAILED] {model} -> Error: {str(e)[:120]}")

print("=" * 80)
