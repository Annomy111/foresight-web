#!/usr/bin/env python3
"""Debug script to check API key configuration"""
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from config.settings import get_settings

def check_api_key():
    # Check environment variables directly
    print("=== Environment Variables ===")
    api_key_env = os.getenv('OPENROUTER_API_KEY')
    api_key_env1 = os.getenv('OPENROUTER_API_KEY1')

    print(f"OPENROUTER_API_KEY: {api_key_env[:8] if api_key_env else 'NOT SET'}...")
    print(f"OPENROUTER_API_KEY1: {api_key_env1[:8] if api_key_env1 else 'NOT SET'}...")

    # Check through settings
    print("\n=== Settings Configuration ===")
    settings = get_settings()

    print(f"API Key from settings: {settings.api.api_key[:8] if settings.api.api_key else 'NOT SET'}...")
    print(f"API Key length: {len(settings.api.api_key) if settings.api.api_key else 0}")
    print(f"Base URL: {settings.api.base_url}")

    # Check if the key looks valid
    if settings.api.api_key:
        if settings.api.api_key.startswith('sk-or-'):
            print("✓ API key has correct prefix (sk-or-)")
        else:
            print("✗ API key doesn't have correct prefix")

        if len(settings.api.api_key) > 50:
            print("✓ API key has expected length")
        else:
            print("✗ API key seems too short")

    # Test the actual client initialization
    print("\n=== OpenRouter Client Test ===")
    try:
        from core.api_client import OpenRouterClient
        client = OpenRouterClient()
        print(f"Client API key: {client.api_key[:8] if client.api_key else 'NOT SET'}...")
        print(f"Client base URL: {client.base_url}")

        # Check the actual OpenAI client configuration
        print(f"\nAsyncOpenAI client api_key: {client.client.api_key[:8] if client.client.api_key else 'NOT SET'}...")

    except Exception as e:
        print(f"Error initializing client: {e}")

    return settings.api.api_key

if __name__ == "__main__":
    api_key = check_api_key()

    if api_key:
        print("\n=== Quick API Test ===")
        print(f"Full API key: {api_key}")
        print("\nIf this key is correct, the issue might be:")
        print("1. The API key is invalid or expired")
        print("2. The API key needs to be activated on OpenRouter")
        print("3. There's a rate limit or quota issue")
    else:
        print("\n❌ No API key found!")