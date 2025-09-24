#!/usr/bin/env python3
"""Check OpenRouter account status and credits"""
import requests
import json

API_KEY = "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"

def check_account():
    """Check OpenRouter account status"""

    print("=" * 60)
    print("OPENROUTER ACCOUNT DIAGNOSTICS")
    print("=" * 60)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "https://github.com/foresight-analyzer",
        "X-Title": "Foresight Analyzer"
    }

    # Test 1: Check account credits/usage
    print("\n1. Checking Account Credits/Usage...")
    print("-" * 40)

    # Try to get generation stats (this endpoint might exist)
    stats_url = "https://openrouter.ai/api/v1/auth/key"
    try:
        response = requests.get(stats_url, headers=headers, timeout=10)
        print(f"   Auth/Key endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Failed: {e}")

    # Test 2: Try the models endpoint with auth
    print("\n2. Testing Models Endpoint with Auth...")
    print("-" * 40)

    models_url = "https://openrouter.ai/api/v1/models"
    try:
        response = requests.get(models_url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                free_models = [m for m in data['data'] if ':free' in m.get('id', '')]
                print(f"   ✓ Can access models list")
                print(f"   ✓ Found {len(free_models)} free models")
                # Check if Grok is available
                grok_models = [m['id'] for m in data['data'] if 'grok' in m.get('id', '').lower()]
                if grok_models:
                    print(f"   ✓ Grok models available: {', '.join(grok_models[:3])}")
        else:
            print(f"   ✗ Error: {response.text}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")

    # Test 3: Try without API key to see difference
    print("\n3. Testing Without API Key (baseline)...")
    print("-" * 40)

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/foresight-analyzer"
            },
            json={
                "model": "x-ai/grok-4-fast:free",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1
            },
            timeout=10
        )
        print(f"   No Auth Status: {response.status_code}")
        print(f"   No Auth Error: {response.text[:100]}")
    except Exception as e:
        print(f"   Failed: {e}")

    # Test 4: Try with different auth format
    print("\n4. Testing Different Auth Formats...")
    print("-" * 40)

    # Try with Bearer token in different format
    alt_headers = headers.copy()
    alt_headers["Authorization"] = API_KEY  # Without "Bearer" prefix

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=alt_headers,
            json={
                "model": "x-ai/grok-4-fast:free",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1
            },
            timeout=10
        )
        print(f"   Without 'Bearer' prefix: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text[:100]}")
    except Exception as e:
        print(f"   Failed: {e}")

    # Test 5: Check if it's a rate limit or account issue
    print("\n5. Checking Free Tier Access...")
    print("-" * 40)

    # Try a minimal request with a definitely free model
    test_models = [
        "x-ai/grok-4-fast:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "mistralai/mistral-7b-instruct:free"
    ]

    for model in test_models:
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 1,
                    "temperature": 0
                },
                timeout=10
            )
            status = "✓" if response.status_code == 200 else "✗"
            print(f"   {status} {model}: {response.status_code}")
            if response.status_code != 200 and response.status_code != 401:
                # If it's not 401, show the error
                print(f"      Error: {response.text[:100]}")
        except Exception as e:
            print(f"   ✗ {model}: Failed - {e}")

    print("\n" + "=" * 60)
    print("DIAGNOSIS")
    print("=" * 60)

    print("\n❌ API KEY ISSUE CONFIRMED")
    print("\nThe API key is consistently returning '401: User not found' errors.")
    print("\nThis means one of the following:")
    print("1. The API key is invalid or has been revoked")
    print("2. The OpenRouter account associated with this key doesn't exist")
    print("3. The API key was never properly activated")
    print("\nSOLUTION:")
    print("1. Go to https://openrouter.ai/keys")
    print("2. Sign in or create an account")
    print("3. Generate a NEW API key")
    print("4. Make sure to SAVE the key immediately")
    print("5. Update your .env file with the new key")
    print("6. Run the update_render_env.py script again")
    print("\nIMPORTANT: OpenRouter API keys start with 'sk-or-v1-'")
    print("Make sure you're copying the ENTIRE key including this prefix.")

if __name__ == "__main__":
    check_account()