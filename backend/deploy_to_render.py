#!/usr/bin/env python3
"""
Deploy Foresight Analyzer Backend to Render
Uses Render API to create and deploy a web service
"""

import requests
import json
import time
import sys

# Configuration
RENDER_API_KEY = "rnd_OwZpGo4Bj1wsOnuTgene20w4OM8L"
GITHUB_REPO = "https://github.com/Annomy111/foresight-backend"
SERVICE_NAME = "foresight-analyzer-api"
OPENROUTER_API_KEY = "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"

# Render API base URL
BASE_URL = "https://api.render.com/v1"

# Headers for API requests
headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Content-Type": "application/json"
}

def create_web_service():
    """Create a new web service on Render"""

    print("🚀 Creating web service on Render...")

    # Service configuration
    service_config = {
        "type": "web_service",
        "name": SERVICE_NAME,
        "ownerId": None,  # Will use default owner
        "repo": GITHUB_REPO,
        "autoDeploy": "yes",
        "branch": "main",
        "buildFilter": {
            "paths": [],
            "ignoredPaths": []
        },
        "envVars": [
            {
                "key": "OPENROUTER_API_KEY",
                "value": OPENROUTER_API_KEY
            },
            {
                "key": "PYTHON_VERSION",
                "value": "3.11.0"
            },
            {
                "key": "OPENROUTER_BASE_URL",
                "value": "https://openrouter.ai/api/v1"
            },
            {
                "key": "ENABLED_MODELS",
                "value": "x-ai/grok-4-fast:free,deepseek/deepseek-r1:free,qwen/qwen3-8b:free,google/gemma-2-9b-it:free,meta-llama/llama-3.2-3b-instruct:free,qwen/qwen-2.5-72b-instruct:free,qwen/qwen-2.5-coder-32b-instruct:free,meta-llama/llama-4-maverick:free"
            },
            {
                "key": "ITERATIONS_PER_MODEL",
                "value": "3"
            },
            {
                "key": "CONCURRENT_REQUESTS",
                "value": "1"
            },
            {
                "key": "REQUEST_TIMEOUT",
                "value": "120"
            },
            {
                "key": "RATE_LIMIT_DELAY",
                "value": "5"
            }
        ],
        "serviceDetails": {
            "region": "oregon",
            "plan": "free",
            "pullRequestPreviewsEnabled": "no",
            "buildCommand": "pip install -r requirements.txt",
            "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            "healthCheckPath": "/health",
            "dockerCommand": "",
            "dockerContext": "",
            "dockerfilePath": ""
        }
    }

    # Create the service
    response = requests.post(
        f"{BASE_URL}/services",
        headers=headers,
        json=service_config
    )

    if response.status_code == 201:
        service = response.json()
        service_id = service["service"]["id"]
        service_url = f"https://{SERVICE_NAME}.onrender.com"

        print(f"✅ Service created successfully!")
        print(f"   Service ID: {service_id}")
        print(f"   Service URL: {service_url}")

        return service_id, service_url
    else:
        print(f"❌ Failed to create service: {response.status_code}")
        print(f"   Response: {response.text}")

        # Check if service already exists
        if "already exists" in response.text.lower():
            print("\n📋 Service may already exist. Checking existing services...")
            return check_existing_service()

        return None, None

def check_existing_service():
    """Check if the service already exists"""

    response = requests.get(
        f"{BASE_URL}/services",
        headers=headers
    )

    if response.status_code == 200:
        services = response.json()
        for service in services:
            if service["service"]["name"] == SERVICE_NAME:
                service_id = service["service"]["id"]
                service_url = f"https://{SERVICE_NAME}.onrender.com"
                print(f"✅ Found existing service!")
                print(f"   Service ID: {service_id}")
                print(f"   Service URL: {service_url}")
                return service_id, service_url

    return None, None

def check_deployment_status(service_id):
    """Check the deployment status of a service"""

    print("\n🔄 Checking deployment status...")

    response = requests.get(
        f"{BASE_URL}/services/{service_id}/deploys",
        headers=headers
    )

    if response.status_code == 200:
        deploys = response.json()
        if deploys:
            latest = deploys[0]
            status = latest["deploy"]["status"]
            print(f"   Status: {status}")

            if status == "live":
                print("   ✅ Deployment is live!")
                return True
            elif status == "build_failed" or status == "deploy_failed":
                print("   ❌ Deployment failed!")
                return False
            else:
                print("   ⏳ Deployment in progress...")
                return None

    return None

def main():
    """Main deployment function"""

    print("=" * 60)
    print("🚀 Foresight Analyzer Backend Deployment to Render")
    print("=" * 60)

    # Create or find the service
    service_id, service_url = create_web_service()

    if not service_id:
        print("\n❌ Failed to create or find service. Exiting.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("📝 Deployment Summary:")
    print("=" * 60)
    print(f"Service Name: {SERVICE_NAME}")
    print(f"Service URL: {service_url}")
    print(f"GitHub Repo: {GITHUB_REPO}")
    print(f"Region: Oregon (US West)")
    print(f"Plan: Free Tier")
    print("\n✨ The service will be deployed automatically from GitHub.")
    print("   First deployment may take 5-10 minutes.")

    # Check deployment status
    print("\n⏳ Waiting for deployment to complete...")
    print("   (This may take several minutes on first deployment)")

    max_checks = 30  # Check for up to 15 minutes
    check_count = 0

    while check_count < max_checks:
        time.sleep(30)  # Check every 30 seconds
        check_count += 1

        status = check_deployment_status(service_id)
        if status is True:
            print("\n🎉 Deployment successful!")
            print(f"   Your backend is live at: {service_url}")
            break
        elif status is False:
            print("\n❌ Deployment failed. Please check Render dashboard for details.")
            break

    if check_count >= max_checks:
        print("\n⏱️ Deployment is taking longer than expected.")
        print("   Please check the Render dashboard for status:")
        print(f"   https://dashboard.render.com/web/{service_id}")

    print("\n" + "=" * 60)
    print("📋 Next Steps:")
    print("=" * 60)
    print("1. ✅ Backend is deploying to Render")
    print("2. ⏰ Set up UptimeRobot at https://uptimerobot.com")
    print(f"   - Monitor URL: {service_url}/health")
    print(f"   - Interval: 5 minutes")
    print("3. 🔧 Update Netlify environment variable:")
    print(f"   - BACKEND_URL = {service_url}")
    print("4. 🧪 Test the deployment:")
    print(f"   - Health check: {service_url}/health")
    print(f"   - API docs: {service_url}/docs")
    print("\n✨ Total cost: $0/month!")

if __name__ == "__main__":
    main()