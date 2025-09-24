#!/usr/bin/env python3
"""Test OpenRouter API key directly"""
import requests
import json

# The API key from your .env file
API_KEY = "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"

def test_api_key():
    """Test if the API key works with OpenRouter"""

    print("Testing OpenRouter API key...")
    print(f"API Key: {API_KEY[:15]}...")

    # Test 1: Simple completion request with Grok-4 Fast
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "https://github.com/foresight-analyzer",
        "X-Title": "Foresight Analyzer",
        "Content-Type": "application/json"
    }

    # Simple test payload with Grok-4 Fast
    payload = {
        "model": "x-ai/grok-4-fast:free",
        "messages": [
            {"role": "user", "content": "Say 'test successful' if you receive this"}
        ],
        "max_tokens": 10,
        "temperature": 0.1
    }

    print("\n1. Testing with Grok-4 Fast (x-ai/grok-4-fast:free)...")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            print("   ✅ API key is VALID and working!")
            data = response.json()
            if 'choices' in data and data['choices']:
                content = data['choices'][0]['message']['content']
                print(f"   Response: {content}")
        elif response.status_code == 401:
            print("   ❌ API key is INVALID or not activated")
            print(f"   Error: {response.text}")
        elif response.status_code == 404:
            print("   ❌ Model not found - trying with a different model")
        else:
            print(f"   ⚠️ Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")

    except Exception as e:
        print(f"   ❌ Request failed: {e}")

    # Test 2: Try with a different free model
    print("\n2. Testing with Google Gemma (google/gemma-2b-it:free)...")
    payload["model"] = "google/gemma-2b-it:free"

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            print("   ✅ This model works!")
        else:
            print(f"   ❌ Error: {response.text[:200]}")

    except Exception as e:
        print(f"   ❌ Request failed: {e}")

    # Test 3: Check account status
    print("\n3. Checking available models...")
    models_url = "https://openrouter.ai/api/v1/models"

    try:
        response = requests.get(models_url, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=10)

        if response.status_code == 200:
            models = response.json()
            if 'data' in models:
                free_models = [m['id'] for m in models['data'] if ':free' in m.get('id', '')]
                print(f"   Found {len(free_models)} free models")
                if 'x-ai/grok-4-fast:free' in free_models:
                    print("   ✅ Grok-4 Fast is available!")
                else:
                    print("   ❌ Grok-4 Fast not in available models")
                    print("   First 5 free models:", free_models[:5])
        else:
            print(f"   ❌ Could not fetch models: {response.status_code}")

    except Exception as e:
        print(f"   ❌ Request failed: {e}")

    print("\n" + "="*60)
    print("DIAGNOSIS:")
    print("="*60)

    if response.status_code == 401:
        print("The API key is INVALID or NOT ACTIVATED.")
        print("\nPossible issues:")
        print("1. The API key might be expired or revoked")
        print("2. The API key might not be activated on OpenRouter")
        print("3. Your OpenRouter account might have issues")
        print("\nSolution:")
        print("1. Go to https://openrouter.ai/settings/keys")
        print("2. Check if this key exists and is active")
        print("3. If not, create a new API key")
        print("4. Update the OPENROUTER_API_KEY in your .env and on Render")
    elif response.status_code == 200:
        print("The API key is VALID and WORKING!")
        print("\nThe issue might be:")
        print("1. The key is not properly set on Render")
        print("2. There's a different configuration issue on Render")
        print("3. The backend code has a different problem")

if __name__ == "__main__":
    test_api_key()