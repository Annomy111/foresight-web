#!/usr/bin/env python3
"""Test backend directly to diagnose issues"""

import requests
import json
import time

BACKEND_URL = "https://foresight-backend-api.onrender.com"

print("🔍 Testing Foresight Backend...")
print("="*50)

# Test 1: Check if backend is online
print("\n1. Checking backend status...")
response = requests.get(BACKEND_URL)
if response.status_code == 200:
    data = response.json()
    print(f"✅ Backend online: {data['status']}")
    print(f"   Version: {data['version']}")
else:
    print(f"❌ Backend offline: {response.status_code}")

# Test 2: Check available models
print("\n2. Checking available models...")
response = requests.get(f"{BACKEND_URL}/api/models")
if response.status_code == 200:
    data = response.json()
    print(f"✅ Found {len(data['models'])} models:")
    for model in data['models']:
        print(f"   - {model}")
else:
    print(f"❌ Failed to get models: {response.status_code}")

# Test 3: Try a forecast with minimal parameters
print("\n3. Testing forecast endpoint...")
forecast_data = {
    "question": "Will it rain tomorrow?",
    "definition": "",
    "timeframe": "2024",
    "iterations": 1
}

print(f"   Request: {json.dumps(forecast_data, indent=2)}")
response = requests.post(
    f"{BACKEND_URL}/forecast",
    headers={"Content-Type": "application/json"},
    json=forecast_data,
    timeout=60
)

print(f"   Status Code: {response.status_code}")
data = response.json()

if data.get('success'):
    print(f"✅ Forecast successful!")
    if data.get('result'):
        print(f"   Probability: {data['result'].get('ensemble_probability')}%")
        stats = data['result'].get('statistics', {})
        print(f"   Models used: {stats.get('successful_queries', 0)}")
else:
    print(f"❌ Forecast failed: {data.get('error', 'Unknown error')}")

# Test 4: Try with different model
print("\n4. Testing with specific free model...")
forecast_data = {
    "question": "Test question",
    "definition": "",
    "timeframe": "2024",
    "iterations": 1,
    "models": ["x-ai/grok-4-fast:free"]
}

response = requests.post(
    f"{BACKEND_URL}/forecast",
    headers={"Content-Type": "application/json"},
    json=forecast_data,
    timeout=60
)

data = response.json()
if data.get('success'):
    print(f"✅ Model-specific forecast successful!")
else:
    print(f"❌ Model-specific forecast failed: {data.get('error', 'Unknown error')}")

print("\n" + "="*50)
print("Diagnosis complete!")
print("\nIf forecasts are failing, check:")
print("1. Is OPENROUTER_API_KEY updated on Render?")
print("2. Does the API key have credits/access to free models?")
print("3. Are the free models currently available?")