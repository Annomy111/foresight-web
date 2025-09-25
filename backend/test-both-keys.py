import requests
import json

# Test both API keys
API_KEYS = {
    "NEW_KEY": "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"
}

BASE_URL = "https://openrouter.ai/api/v1"

print("🔍 Testing OpenRouter API Keys...")

for name, key in API_KEYS.items():
    print(f"\nTesting {name}: {key[:20]}...")

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://foresight-analyzer.netlify.app",
        "X-Title": "Foresight Test"
    }

    data = {
        "model": "x-ai/grok-4-fast:free",
        "messages": [{"role": "user", "content": "Reply with just: OK"}],
        "max_tokens": 10,
        "temperature": 0.1
    }

    try:
        response = requests.post(f"{BASE_URL}/chat/completions", headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', 'No response')
            print(f"✅ {name} is VALID! Response: {content}")
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            print(f"❌ {name} failed: {response.status_code} - {error_msg}")
    except Exception as e:
        print(f"❌ {name} error: {e}")

print("\n" + "="*50)
print("RECOMMENDATION:")
for name, key in API_KEYS.items():
    print(f"Testing {name}...")
    headers = {"Authorization": f"Bearer {key}"}
    try:
        response = requests.post(f"{BASE_URL}/chat/completions",
                                headers=headers,
                                json={"model": "x-ai/grok-4-fast:free", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5},
                                timeout=10)
        if response.status_code == 200:
            print(f"  → Use this key in backend/.env: {key[:30]}...")
            break
    except:
        pass