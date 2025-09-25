#!/usr/bin/env python3
"""Test OpenRouter API key directly"""

import requests
import json

# API key from .env.local (the one that was in DEPLOYMENT_GUIDE)
API_KEY = "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"
BASE_URL = "https://openrouter.ai/api/v1"

def test_api_key():
    """Test if the API key works"""

    print("🔍 Testing OpenRouter API Key...")
    print(f"Key: {API_KEY[:20]}...")

    # Test with a simple completion request
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://foresight-analyzer.netlify.app",
        "X-Title": "Foresight Analyzer Test"
    }

    # Try with a free model
    data = {
        "model": "x-ai/grok-4-fast:free",
        "messages": [
            {"role": "user", "content": "What is 2+2? Reply with just the number."}
        ],
        "max_tokens": 10,
        "temperature": 0.1
    }

    try:
        print(f"\n📤 Sending request to {BASE_URL}/chat/completions")
        print(f"Model: {data['model']}")

        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )

        print(f"\n📥 Response Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ API Key is VALID!")
            print(f"Response: {json.dumps(result, indent=2)}")
            if 'choices' in result:
                print(f"\nModel response: {result['choices'][0]['message']['content']}")
        else:
            print(f"❌ API Key might be invalid or there's an issue")
            print(f"Response: {response.text}")

            # Try to parse error
            try:
                error_data = response.json()
                if 'error' in error_data:
                    print(f"\nError details: {error_data['error']}")
            except:
                pass

    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_api_key()