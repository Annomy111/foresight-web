#!/usr/bin/env python3
"""
Update Render environment variables programmatically
"""
import os
import requests
import json
from typing import Dict, Optional

def get_render_api_key() -> Optional[str]:
    """Get Render API key from environment or prompt user"""
    # Check common locations for API key
    api_key = os.getenv('RENDER_API_KEY')

    if not api_key:
        print("❌ No RENDER_API_KEY found in environment")
        print("\nTo get your Render API key:")
        print("1. Go to https://dashboard.render.com/u/settings")
        print("2. Click on 'API Keys'")
        print("3. Create a new API key or use an existing one")
        print("\nYou can set it as environment variable:")
        print("export RENDER_API_KEY=your-api-key-here")
        print("\nOr enter it now (it will be used only for this session):")
        api_key = input("Render API Key: ").strip()

    return api_key if api_key else None

def find_service(api_key: str, service_name: str = "foresight-backend-api") -> Optional[str]:
    """Find the service ID by name"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json'
    }

    print(f"\n🔍 Looking for service: {service_name}")

    # Get all services
    response = requests.get(
        'https://api.render.com/v1/services',
        headers=headers,
        params={'limit': 100}
    )

    if response.status_code != 200:
        print(f"❌ Failed to list services: {response.status_code}")
        print(f"Response: {response.text}")
        return None

    services = response.json()

    # Find our service
    for service in services:
        if service.get('service', {}).get('name') == service_name:
            service_id = service.get('service', {}).get('id')
            print(f"✅ Found service: {service_id}")
            return service_id

    print(f"❌ Service '{service_name}' not found")
    print("Available services:")
    for service in services[:5]:  # Show first 5
        print(f"  - {service.get('service', {}).get('name')}")

    return None

def get_current_env_vars(api_key: str, service_id: str) -> Dict:
    """Get current environment variables"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json'
    }

    response = requests.get(
        f'https://api.render.com/v1/services/{service_id}/env-vars',
        headers=headers
    )

    if response.status_code != 200:
        print(f"❌ Failed to get env vars: {response.status_code}")
        return {}

    env_vars = response.json()
    return {item['envVar']['key']: item['envVar']['value'] for item in env_vars}

def update_env_vars(api_key: str, service_id: str, updates: Dict) -> bool:
    """Update environment variables"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    # Prepare the updates
    env_updates = []
    for key, value in updates.items():
        env_updates.append({
            'key': key,
            'value': value
        })

    print(f"\n📝 Updating {len(env_updates)} environment variables...")

    # Update each variable
    success = True
    for env_var in env_updates:
        response = requests.put(
            f'https://api.render.com/v1/services/{service_id}/env-vars/{env_var["key"]}',
            headers=headers,
            json={'value': env_var['value']}
        )

        if response.status_code in [200, 201]:
            print(f"  ✅ Updated: {env_var['key']}")
        else:
            print(f"  ❌ Failed to update {env_var['key']}: {response.status_code}")
            success = False

    return success

def trigger_deploy(api_key: str, service_id: str) -> bool:
    """Trigger a new deploy to apply environment changes"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    print("\n🚀 Triggering new deployment...")

    response = requests.post(
        f'https://api.render.com/v1/services/{service_id}/deploys',
        headers=headers,
        json={}
    )

    if response.status_code in [201, 202]:
        deploy = response.json()
        deploy_id = deploy.get('id', 'unknown')
        print(f"✅ Deployment triggered: {deploy_id}")
        print(f"   Monitor at: https://dashboard.render.com/web/{service_id}/deploys/{deploy_id}")
        return True
    else:
        print(f"❌ Failed to trigger deploy: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def main():
    """Main function to update Render environment variables"""

    print("=" * 60)
    print("🔧 RENDER ENVIRONMENT VARIABLES UPDATER")
    print("=" * 60)

    # Get API key
    api_key = get_render_api_key()
    if not api_key:
        print("❌ Cannot proceed without API key")
        return

    # Find service
    service_id = find_service(api_key)
    if not service_id:
        return

    # Get current environment variables
    print("\n📋 Current environment variables:")
    current_vars = get_current_env_vars(api_key, service_id)

    # Show relevant variables
    relevant_keys = ['OPENROUTER_API_KEY', 'OPENROUTER_API_KEY1', 'ENABLED_MODELS']
    for key in relevant_keys:
        if key in current_vars:
            value = current_vars[key]
            if 'API_KEY' in key and value:
                # Mask API keys
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            elif key == 'ENABLED_MODELS':
                # Show model count
                models = value.split(',') if value else []
                display_value = f"{len(models)} models configured"
            else:
                display_value = value[:50] + "..." if len(value) > 50 else value

            print(f"  {key}: {display_value}")

    # Prepare updates
    print("\n📝 Preparing updates...")

    # Load from .env file
    from dotenv import load_dotenv
    load_dotenv()

    updates = {}

    # Get OPENROUTER_API_KEY (check both variants)
    api_key_value = os.getenv('OPENROUTER_API_KEY') or current_vars.get('OPENROUTER_API_KEY1', '')
    if api_key_value:
        updates['OPENROUTER_API_KEY'] = api_key_value
        print(f"  ✓ Will set OPENROUTER_API_KEY: {api_key_value[:8]}...")

    # Get ENABLED_MODELS from .env or use our verified list
    enabled_models = os.getenv('ENABLED_MODELS')
    if not enabled_models:
        # Use our verified working free models including Grok-4 Fast
        enabled_models = "x-ai/grok-4-fast:free,google/gemma-2b-it:free,mistralai/mistral-7b-instruct:free,nousresearch/hermes-3-llama-3.1-8b:free,qwen/qwen-2.5-72b-instruct:free,meta-llama/llama-3.2-3b-instruct:free,google/gemma-2-9b-it:free"

    updates['ENABLED_MODELS'] = enabled_models
    models_list = enabled_models.split(',')
    print(f"  ✓ Will set ENABLED_MODELS: {len(models_list)} models")
    print(f"    Including: {models_list[0]} (Grok-4 Fast)")

    # Add other important settings
    other_vars = {
        'ITERATIONS_PER_MODEL': os.getenv('ITERATIONS_PER_MODEL', '5'),
        'CONCURRENT_REQUESTS': os.getenv('CONCURRENT_REQUESTS', '2'),
        'REQUEST_TIMEOUT': os.getenv('REQUEST_TIMEOUT', '120'),
        'RETRY_ATTEMPTS': os.getenv('RETRY_ATTEMPTS', '3'),
        'RETRY_DELAY': os.getenv('RETRY_DELAY', '5'),
        'RATE_LIMIT_DELAY': os.getenv('RATE_LIMIT_DELAY', '3'),
        'MAX_RETRIES_FREE': os.getenv('MAX_RETRIES_FREE', '10'),
        'BACKOFF_MULTIPLIER': os.getenv('BACKOFF_MULTIPLIER', '2'),
    }

    for key, value in other_vars.items():
        updates[key] = value
        print(f"  ✓ Will set {key}: {value}")

    # Confirm before updating
    print(f"\n⚠️  About to update {len(updates)} environment variables on Render")
    print("This will trigger a new deployment of your service.")

    confirm = input("\nProceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled")
        return

    # Update environment variables
    if update_env_vars(api_key, service_id, updates):
        print("\n✅ Environment variables updated successfully!")

        # Trigger deployment
        if trigger_deploy(api_key, service_id):
            print("\n🎉 SUCCESS! Your backend is being redeployed with:")
            print(f"   - Grok-4 Fast and {len(models_list)-1} other free models")
            print(f"   - Proper API key configuration")
            print("\n⏱️  Deployment usually takes 2-3 minutes")
            print("   Check status at: https://dashboard.render.com")
        else:
            print("\n⚠️  Environment updated but deployment failed")
            print("   You may need to manually trigger a deploy from the Render dashboard")
    else:
        print("\n❌ Failed to update some environment variables")
        print("   Please check the Render dashboard")

if __name__ == "__main__":
    main()