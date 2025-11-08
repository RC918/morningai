#!/usr/bin/env python3
"""Test Vercel API with new token"""
import asyncio
import os
import sys
from common.config.settings import settings
from tools.deployment_tool import DeploymentTool

async def main():
    # Use VERCEL_TOKEN_2
    token = settings.vercel_token_2
    team_id = settings.vercel_org_id
    project_id = settings.vercel_project_id
    
    print(f"Testing with token: {token[:20]}...")
    print(f"Team ID: {team_id}")
    print(f"Project ID: {project_id}")
    print("\n" + "="*60)
    
    tool = DeploymentTool(token=token, team_id=team_id)
    
    # Test 1: List deployments
    print("\n📋 Test 1: List Deployments")
    print("-" * 60)
    result = await tool.list_deployments(project=project_id, limit=5)
    
    if result['success']:
        print(f"✅ SUCCESS! Found {result['total']} deployments")
        print(f"\nRecent deployments:")
        for i, dep in enumerate(result['deployments'][:3], 1):
            print(f"\n  {i}. {dep['name']}")
            print(f"     State: {dep['state']}")
            print(f"     URL: https://{dep['url']}")
            print(f"     Target: {dep.get('target', 'N/A')}")
    else:
        print(f"❌ FAILED: {result.get('error')}")
        print(f"   Status: {result.get('status_code')}")
        return False
    
    # Test 2: Get deployment details
    if result['deployments']:
        print("\n" + "="*60)
        print("\n🔍 Test 2: Get Deployment Details")
        print("-" * 60)
        dep_id = result['deployments'][0]['id']
        detail = await tool.get_deployment(dep_id)
        
        if detail['success']:
            dep = detail['deployment']
            print(f"✅ SUCCESS!")
            print(f"\n  Deployment ID: {dep['id']}")
            print(f"  Name: {dep['name']}")
            print(f"  URL: https://{dep['url']}")
            print(f"  State: {dep['state']}")
            print(f"  Created: {dep['created_at']}")
            print(f"  Ready: {dep.get('ready_at', 'N/A')}")
        else:
            print(f"❌ FAILED: {detail.get('error')}")
            return False
    
    print("\n" + "="*60)
    print("\n✨ All Vercel API tests passed!")
    print("="*60)
    return True

if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
