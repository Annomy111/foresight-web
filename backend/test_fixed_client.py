#!/usr/bin/env python3
"""Test the fixed OpenRouter client"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Set the API key
os.environ['OPENROUTER_API_KEY'] = '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'
os.environ['OPENROUTER_BASE_URL'] = 'https://openrouter.ai/api/v1'

async def test_fixed_client():
    """Test the fixed client"""
    from core.api_client import OpenRouterClient

    print("🔍 Testing Fixed OpenRouter Client...")
    print("="*50)

    try:
        # Initialize client
        client = OpenRouterClient()
        print("✅ Client initialized")

        # Test connection
        print("\n📡 Testing connection...")
        connected = await client.test_connection()
        if connected:
            print("✅ Connection test successful!")
        else:
            print("❌ Connection test failed")
            return False

        # Test actual forecast query
        print("\n🔮 Testing forecast query...")
        result = await client.query_model(
            model="x-ai/grok-4-fast:free",
            prompt="What is the probability (0-100) that AI will advance significantly in 2025? Reply with PROGNOSE: X% at the end.",
            temperature=0.7,
            max_tokens=500,
            enable_web_search=False
        )

        print(f"Status: {result.get('status')}")
        print(f"Probability: {result.get('probability')}")

        if result.get('probability') is not None:
            print(f"✅ SUCCESS! Got probability: {result['probability']}%")
            return True
        else:
            print("⚠️  No probability extracted")
            if result.get('content'):
                print(f"Response preview: {result['content'][:200]}...")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_multiple_models():
    """Test multiple models"""
    from core.api_client import OpenRouterClient

    print("\n" + "="*50)
    print("🤖 Testing Multiple Models...")
    print("="*50)

    client = OpenRouterClient()
    models = [
        "x-ai/grok-4-fast:free",
        "google/gemma-2b-it:free",
        "mistralai/mistral-7b-instruct:free"
    ]

    for model in models:
        print(f"\nTesting {model}...")
        try:
            result = await client.query_model(
                model=model,
                prompt="What is 2+2? Reply with just the number.",
                temperature=0.1,
                max_tokens=10,
                enable_web_search=False
            )

            if result.get('status') == 'success':
                print(f"  ✅ {model}: {result.get('content', 'No content')}")
            else:
                print(f"  ❌ {model}: {result.get('error', 'Failed')}")

        except Exception as e:
            print(f"  ❌ {model}: Error - {e}")

# Run the tests
async def main():
    success = await test_fixed_client()

    if success:
        await test_multiple_models()
        print("\n" + "="*50)
        print("🎉 All tests completed! The fix works!")
    else:
        print("\n" + "="*50)
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())