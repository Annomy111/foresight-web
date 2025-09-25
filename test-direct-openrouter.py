#!/usr/bin/env python3
"""Test OpenRouter API directly with same models as backend"""

import requests
import json

API_KEY = "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"
BASE_URL = "https://openrouter.ai/api/v1"

# Models from backend configuration
MODELS = [
    "x-ai/grok-4-fast:free",
    "google/gemma-2b-it:free",
    "mistralai/mistral-7b-instruct:free",
    "nousresearch/hermes-3-llama-3.1-8b:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "google/gemma-2-9b-it:free"
]

print("🔍 Testing OpenRouter API with backend models...")
print("="*50)

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://foresight-analyzer.netlify.app",
    "X-Title": "Foresight Analyzer"
}

working_models = []
failed_models = []

for model in MODELS:
    print(f"\nTesting {model}...")

    data = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "What is the probability (0-100) that it will rain tomorrow? Reply with just a number."
            }
        ],
        "max_tokens": 20,
        "temperature": 0.7
    }

    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"  ✅ SUCCESS: {content}")
                working_models.append(model)
            else:
                print(f"  ⚠️  Empty response")
                failed_models.append(model)
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            print(f"  ❌ FAILED ({response.status_code}): {error_msg}")
            failed_models.append(model)

    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        failed_models.append(model)

print("\n" + "="*50)
print("RESULTS:")
print(f"✅ Working models ({len(working_models)}): {working_models}")
print(f"❌ Failed models ({len(failed_models)}): {failed_models}")

if working_models:
    print("\n✨ At least some models are working!")
    print("The backend should be able to use these models.")
else:
    print("\n⚠️  No models are working!")
    print("This explains why the backend returns 'No valid model results obtained'")

print("\nPossible issues:")
print("1. The API key might not have access to free tier models")
print("2. The models might be temporarily unavailable")
print("3. The account might need credits even for free models")