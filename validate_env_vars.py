#!/usr/bin/env python3
"""
Environment Variables Validation Script
Checks all required environment variables for cloud services
"""
import os
from datetime import datetime

REQUIRED_ENV_VARS = {
    'Supabase': ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'SUPABASE_SERVICE_ROLE_KEY'],
    'Cloudflare': ['CLOUDFLARE_API_TOKEN', 'CLOUDFLARE_ZONE_ID'],
    'Vercel': ['VERCEL_TOKEN', 'VERCEL_ORG_ID', 'VERCEL_PROJECT_ID'],
    'Render': ['RENDER_API_KEY'],
    'Sentry': ['SENTRY_DSN', 'SENTRY_AUTH_TOKEN'],
    'Upstash Redis': ['UPSTASH_REDIS_REST_URL', 'UPSTASH_REDIS_REST_TOKEN']
}

def validate_env_vars():
    print("=" * 60)
    print("🔍 Environment Variables Validation")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)
    
    all_valid = True
    
    for service, vars_list in REQUIRED_ENV_VARS.items():
        print(f"\n{service}:")
        print("-" * len(service))
        
        service_valid = True
        for var in vars_list:
            value = os.getenv(var)
            if value:
                if len(value) > 20:
                    display_value = f"{value[:10]}...{value[-5:]}"
                else:
                    display_value = f"{value[:5]}..."
                print(f"  ✅ {var}: {display_value}")
            else:
                print(f"  ❌ {var}: NOT SET")
                service_valid = False
                all_valid = False
        
        if service_valid:
            print(f"  🎯 {service}: All variables set")
        else:
            print(f"  ⚠️  {service}: Missing variables")
    
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    if all_valid:
        print("🎉 All required environment variables are set!")
    else:
        print("⚠️  Some environment variables are missing.")
        print("💡 Check your .env file or system environment variables.")
    
    return all_valid

if __name__ == "__main__":
    validate_env_vars()
