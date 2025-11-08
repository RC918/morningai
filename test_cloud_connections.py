#!/usr/bin/env python3
"""
Cloud Service Connection Status Test
Tests connection status for the 6 primary cloud services:
Sentry, Cloudflare, Upstash Redis, Vercel, Render, Supabase
"""
import os
import sys
import requests
from datetime import datetime

from common.config.settings import settings

def test_supabase_connection():
    """Test Supabase connection using environment variables"""
    print("🔍 Testing Supabase connection...")
    
    supabase_url = settings.supabase_url
    supabase_key = settings.supabase_service_role_key
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase: Environment variables not set")
        print(f"   SUPABASE_URL: {'SET' if supabase_url else 'NOT SET'}")
        print(f"   SUPABASE_SERVICE_ROLE_KEY: {'SET' if supabase_key else 'NOT SET'}")
        return False
    
    try:
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json'
        }
        response = requests.get(f"{supabase_url}/rest/v1/", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Supabase: Connection successful")
            return True
        else:
            print(f"❌ Supabase: Connection failed (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Supabase: Connection error - {e}")
        return False

def test_upstash_redis():
    """Test Upstash Redis connection"""
    print("🔍 Testing Upstash Redis connection...")
    
    redis_url = settings.redis_url
    upstash_url = settings.upstash_redis_rest_url
    upstash_token = settings.upstash_redis_rest_token
    
    if upstash_url and upstash_token:
        try:
            headers = {'Authorization': f'Bearer {upstash_token}'}
            response = requests.post(f"{upstash_url}/ping", headers=headers, timeout=10)
            if response.status_code == 200:
                print("✅ Upstash Redis: Connection successful")
                return True
            else:
                print(f"❌ Upstash Redis: Connection failed (HTTP {response.status_code})")
                return False
        except Exception as e:
            print(f"❌ Upstash Redis: Connection error - {e}")
            return False
    elif redis_url:
        print(f"⚠️ Upstash Redis: Only generic REDIS_URL found: {redis_url}")
        print("   No Upstash-specific credentials detected")
        return False
    else:
        print("❌ Upstash Redis: No Redis configuration found")
        return False

def test_sentry_integration():
    """Test Sentry integration"""
    print("🔍 Testing Sentry integration...")
    
    sentry_dsn = settings.sentry_dsn
    
    if not sentry_dsn:
        print("❌ Sentry: SENTRY_DSN environment variable not set")
        return False
    
    try:
        if sentry_dsn.startswith('https://'):
            print(f"✅ Sentry: DSN configured - {sentry_dsn[:30]}...")
            return True
        else:
            print(f"❌ Sentry: Invalid DSN format - {sentry_dsn}")
            return False
    except Exception as e:
        print(f"❌ Sentry: Configuration error - {e}")
        return False

def test_cloudflare_integration():
    """Test Cloudflare integration"""
    print("🔍 Testing Cloudflare integration...")
    
    cf_token = settings.cloudflare_api_token
    cf_zone = settings.cloudflare_zone_id
    
    if not cf_token or not cf_zone:
        print("❌ Cloudflare: Environment variables not set")
        print(f"   CLOUDFLARE_API_TOKEN: {'SET' if cf_token else 'NOT SET'}")
        print(f"   CLOUDFLARE_ZONE_ID: {'SET' if cf_zone else 'NOT SET'}")
        return False
    
    try:
        headers = {
            'Authorization': f'Bearer {cf_token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(f"https://api.cloudflare.com/client/v4/zones/{cf_zone}", 
                              headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Cloudflare: API connection successful")
            return True
        else:
            print(f"❌ Cloudflare: API connection failed (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Cloudflare: Connection error - {e}")
        return False

def test_vercel_integration():
    """Test Vercel integration"""
    print("🔍 Testing Vercel integration...")
    
    vercel_token = settings.vercel_token
    vercel_org = settings.vercel_org_id
    vercel_project = settings.vercel_project_id
    
    if not vercel_token:
        print("❌ Vercel: VERCEL_TOKEN environment variable not set")
        return False
    
    try:
        headers = {
            'Authorization': f'Bearer {vercel_token}',
            'Content-Type': 'application/json'
        }
        response = requests.get("https://api.vercel.com/v2/user", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Vercel: API connection successful")
            print(f"   ORG_ID: {'SET' if vercel_org else 'NOT SET'}")
            print(f"   PROJECT_ID: {'SET' if vercel_project else 'NOT SET'}")
            return True
        else:
            print(f"❌ Vercel: API connection failed (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Vercel: Connection error - {e}")
        return False

def test_render_integration():
    """Test Render integration"""
    print("🔍 Testing Render integration...")
    
    render_key = settings.render_api_key
    
    if not render_key:
        print("❌ Render: RENDER_API_KEY environment variable not set")
        return False
    
    try:
        headers = {
            'Authorization': f'Bearer {render_key}',
            'Content-Type': 'application/json'
        }
        response = requests.get("https://api.render.com/v1/services", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Render: API connection successful")
            return True
        else:
            print(f"❌ Render: API connection failed (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Render: Connection error - {e}")
        return False

def main():
    print("=" * 60)
    print("🔍 Morning AI Cloud Service Connection Status Report")
    print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)
    
    results = {}
    
    results['Supabase'] = test_supabase_connection()
    print()
    results['Upstash Redis'] = test_upstash_redis()
    print()
    results['Sentry'] = test_sentry_integration()
    print()
    results['Cloudflare'] = test_cloudflare_integration()
    print()
    results['Vercel'] = test_vercel_integration()
    print()
    results['Render'] = test_render_integration()
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    connected = sum(results.values())
    total = len(results)
    
    for service, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {service}")
    
    print(f"\n🎯 Overall Status: {connected}/{total} services connected")
    
    if connected == total:
        print("🎉 All cloud services are properly configured and connected!")
    else:
        print("⚠️  Some services need configuration or have connection issues.")
        print("💡 Run 'python fix_cloud_auth.py' for detailed repair guidance.")

if __name__ == "__main__":
    main()
