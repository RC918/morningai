#!/usr/bin/env python3
"""
Cloud Service Authentication Repair Tool
Diagnoses and provides repair guidance for authentication issues
"""
import os
import sys
import requests
from datetime import datetime
from common.config.settings import settings

def validate_supabase_auth():
    """Validate and provide repair guidance for Supabase authentication"""
    print("🔍 Diagnosing Supabase authentication...")
    
    supabase_url = settings.supabase_url
    supabase_key = settings.supabase_service_role_key
    
    if not supabase_url or not supabase_key:
        print("❌ Missing environment variables")
        print("🔧 REPAIR STEPS:")
        print("   1. Go to your Supabase project dashboard")
        print("   2. Navigate to Settings > API")
        print("   3. Copy the Project URL and set SUPABASE_URL")
        print("   4. Copy the service_role key and set SUPABASE_SERVICE_ROLE_KEY")
        return False
    
    try:
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json'
        }
        response = requests.get(f"{supabase_url}/rest/v1/", headers=headers, timeout=10)
        
        if response.status_code == 401:
            print("❌ Invalid API key detected")
            print("🔧 REPAIR STEPS:")
            print("   1. Go to Supabase project dashboard")
            print("   2. Settings > API > Project API keys")
            print("   3. Regenerate service_role key if expired")
            print("   4. Update SUPABASE_SERVICE_ROLE_KEY environment variable")
            return False
        elif response.status_code == 200:
            print("✅ Supabase authentication successful")
            return True
        else:
            print(f"❌ Unexpected response: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def validate_cloudflare_auth():
    """Validate and provide repair guidance for Cloudflare authentication"""
    print("🔍 Diagnosing Cloudflare authentication...")
    
    cf_token = settings.cloudflare_api_token
    cf_zone = settings.cloudflare_zone_id
    
    if not cf_token or not cf_zone:
        print("❌ Missing environment variables")
        print("🔧 REPAIR STEPS:")
        print("   1. Go to Cloudflare dashboard")
        print("   2. My Profile > API Tokens")
        print("   3. Create token with Zone:Read permissions")
        print("   4. Get Zone ID from domain overview page")
        return False
    
    try:
        headers = {
            'Authorization': f'Bearer {cf_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get("https://api.cloudflare.com/client/v4/user/tokens/verify", 
                              headers=headers, timeout=10)
        
        if response.status_code != 200:
            print("❌ Invalid API token")
            print("🔧 REPAIR STEPS:")
            print("   1. Go to Cloudflare dashboard")
            print("   2. My Profile > API Tokens")
            print("   3. Regenerate or create new token")
            print("   4. Ensure token has Zone:Read permissions")
            return False
        
        response = requests.get(f"https://api.cloudflare.com/client/v4/zones/{cf_zone}", 
                              headers=headers, timeout=10)
        
        if response.status_code == 403:
            print("❌ Token lacks zone access permissions")
            print("🔧 REPAIR STEPS:")
            print("   1. Verify Zone ID is correct")
            print("   2. Ensure API token has Zone:Read permissions for this zone")
            print("   3. Check token hasn't expired")
            return False
        elif response.status_code == 404:
            print("❌ Invalid Zone ID")
            print("🔧 REPAIR STEPS:")
            print("   1. Go to Cloudflare dashboard")
            print("   2. Select your domain")
            print("   3. Copy Zone ID from right sidebar")
            print("   4. Update CLOUDFLARE_ZONE_ID environment variable")
            return False
        elif response.status_code == 200:
            print("✅ Cloudflare authentication successful")
            return True
        else:
            print(f"❌ Unexpected response: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def validate_vercel_auth():
    """Validate and provide repair guidance for Vercel authentication"""
    print("🔍 Diagnosing Vercel authentication...")
    
    vercel_token = settings.vercel_token
    
    if not vercel_token:
        print("❌ Missing VERCEL_TOKEN environment variable")
        print("🔧 REPAIR STEPS:")
        print("   1. Go to Vercel dashboard")
        print("   2. Settings > Tokens")
        print("   3. Create new token")
        print("   4. Set VERCEL_TOKEN environment variable")
        return False
    
    try:
        headers = {
            'Authorization': f'Bearer {vercel_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get("https://api.vercel.com/v2/user", headers=headers, timeout=10)
        
        if response.status_code == 403:
            error_data = response.json()
            if error_data.get('error', {}).get('invalidToken'):
                print("❌ Invalid or expired token")
                print("🔧 REPAIR STEPS:")
                print("   1. Go to Vercel dashboard")
                print("   2. Settings > Tokens")
                print("   3. Delete old token and create new one")
                print("   4. Update VERCEL_TOKEN environment variable")
                return False
            else:
                print("❌ Token lacks required permissions")
                print("🔧 REPAIR STEPS:")
                print("   1. Ensure token has appropriate scopes")
                print("   2. Recreate token if necessary")
                return False
        elif response.status_code == 200:
            print("✅ Vercel authentication successful")
            return True
        else:
            print(f"❌ Unexpected response: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def main():
    print("=" * 60)
    print("🔧 Cloud Service Authentication Repair Tool")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)
    
    results = {}
    
    print("\n1. SUPABASE AUTHENTICATION")
    print("-" * 30)
    results['Supabase'] = validate_supabase_auth()
    
    print("\n2. CLOUDFLARE AUTHENTICATION")
    print("-" * 30)
    results['Cloudflare'] = validate_cloudflare_auth()
    
    print("\n3. VERCEL AUTHENTICATION")
    print("-" * 30)
    results['Vercel'] = validate_vercel_auth()
    
    print("\n" + "=" * 60)
    print("📊 AUTHENTICATION REPAIR SUMMARY")
    print("=" * 60)
    
    fixed = sum(results.values())
    total = len(results)
    
    for service, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {service}")
    
    print(f"\n🎯 Authentication Status: {fixed}/{total} services working")
    
    if fixed == total:
        print("🎉 All authentication issues resolved!")
        print("Run the full connection test to verify 6/6 services are connected.")
    else:
        print("⚠️  Follow the repair steps above to fix remaining issues.")
        print("After making changes, run this script again to verify fixes.")

if __name__ == "__main__":
    main()
