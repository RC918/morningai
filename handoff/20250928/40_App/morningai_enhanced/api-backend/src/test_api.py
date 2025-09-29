#!/usr/bin/env python3
"""
Test script for Morning AI API endpoints
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

def test_health_endpoints():
    """Test health check endpoints"""
    print("Testing health endpoints...")
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"GET /health: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    
    response = requests.get(f"{BASE_URL}/healthz")
    print(f"GET /healthz: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Overall status: {data.get('status')}")
        print(f"Cloud resources: {list(data.get('cloud_resources', {}).keys())}")

def test_auth_endpoints():
    """Test authentication endpoints"""
    print("\nTesting authentication endpoints...")
    
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"POST /api/auth/login: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        print(f"Login successful, got token")
        
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f"{BASE_URL}/api/auth/verify", headers=headers)
        print(f"GET /api/auth/verify: {response.status_code}")
        if response.status_code == 200:
            print(f"Token verification successful: {response.json()}")
    else:
        print(f"Login failed: {response.text}")

def test_system_endpoints():
    """Test system endpoints"""
    print("\nTesting system endpoints...")
    
    response = requests.get(f"{BASE_URL}/api/system/metrics")
    print(f"GET /api/system/metrics: {response.status_code}")
    if response.status_code == 200:
        print(f"Metrics: {response.json()}")
    
    response = requests.get(f"{BASE_URL}/api/cloud/status")
    print(f"GET /api/cloud/status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        services = data.get('services', {})
        print(f"Cloud services status:")
        for service, status in services.items():
            print(f"  {service}: {status.get('status')}")

if __name__ == '__main__':
    print(f"Testing Morning AI API at {BASE_URL}")
    print("=" * 50)
    
    try:
        test_health_endpoints()
        test_auth_endpoints()
        test_system_endpoints()
        print("\n" + "=" * 50)
        print("API testing completed!")
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to API at {BASE_URL}")
        print("Make sure the API server is running.")
    except Exception as e:
        print(f"ERROR: {e}")
