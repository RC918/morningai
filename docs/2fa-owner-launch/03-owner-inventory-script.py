#!/usr/bin/env python3
"""
Owner Account 2FA Inventory Script

Purpose: Generate a comprehensive report of all Owner accounts and their 2FA status
Usage: python 03-owner-inventory-script.py [--env staging|production]
Output: owner_2fa_inventory_YYYY-MM-DD.csv

Requirements:
- SUPABASE_URL environment variable
- SUPABASE_SERVICE_ROLE_KEY environment variable
- supabase-py library: pip install supabase

Author: Devin AI (Week 0 Sprint - Task 1)
Date: 2025-11-04
"""

import os
import sys
import csv
from datetime import datetime, timezone
from typing import List, Dict, Any
from supabase import create_client, Client

ENVIRONMENTS = {
    'staging': {
        'url': os.environ.get('SUPABASE_URL_STAGING'),
        'key': os.environ.get('SUPABASE_SERVICE_ROLE_KEY_STAGING')
    },
    'production': {
        'url': os.environ.get('SUPABASE_URL'),
        'key': os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    }
}


def get_supabase_client(env: str = 'staging') -> Client:
    """
    Create Supabase client for specified environment
    
    Args:
        env: Environment name ('staging' or 'production')
        
    Returns:
        Supabase client instance
        
    Raises:
        ValueError: If environment variables not set
    """
    config = ENVIRONMENTS.get(env)
    if not config:
        raise ValueError(f"Invalid environment: {env}. Must be 'staging' or 'production'")
    
    url = config['url']
    key = config['key']
    
    if not url or not key:
        raise ValueError(
            f"Missing environment variables for {env}:\n"
            f"  SUPABASE_URL{'_STAGING' if env == 'staging' else ''}\n"
            f"  SUPABASE_SERVICE_ROLE_KEY{'_STAGING' if env == 'staging' else ''}"
        )
    
    return create_client(url, key)


def fetch_owner_accounts(supabase: Client) -> List[Dict[str, Any]]:
    """
    Fetch all Owner accounts with 2FA status
    
    Args:
        supabase: Supabase client instance
        
    Returns:
        List of owner account dictionaries
    """
    print("Fetching owner accounts from auth.users...")
    
    
    user_2fa_response = supabase.table('user_2fa').select('*').execute()
    user_2fa_map = {record['user_id']: record for record in user_2fa_response.data}
    
    print(f"Found {len(user_2fa_map)} users with 2FA records")
    
    
    owners = []
    
    print("\n⚠️  WARNING: This script requires direct database access to auth.users")
    print("Please run the SQL queries in 03-owner-inventory-template.sql instead")
    print("Or use Supabase Admin API to fetch user metadata")
    
    return owners


def calculate_risk_level(owner: Dict[str, Any]) -> str:
    """
    Calculate risk level for owner account
    
    Args:
        owner: Owner account dictionary
        
    Returns:
        Risk level string ('HIGH', 'MEDIUM', 'LOW')
    """
    has_2fa = owner.get('twofa_enabled', False)
    last_login = owner.get('last_sign_in_at')
    
    if has_2fa:
        return 'LOW'
    
    if not last_login:
        return 'LOW (Inactive)'
    
    days_since_login = (datetime.now(timezone.utc) - last_login).days
    
    if days_since_login <= 7:
        return 'HIGH'
    elif days_since_login <= 30:
        return 'MEDIUM'
    else:
        return 'LOW (Inactive)'


def generate_summary_stats(owners: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate summary statistics for owner accounts
    
    Args:
        owners: List of owner account dictionaries
        
    Returns:
        Dictionary of summary statistics
    """
    total = len(owners)
    with_2fa = sum(1 for o in owners if o.get('twofa_enabled', False))
    without_2fa = total - with_2fa
    
    active_without_2fa = sum(
        1 for o in owners 
        if not o.get('twofa_enabled', False) 
        and o.get('last_sign_in_at')
        and (datetime.now(timezone.utc) - o['last_sign_in_at']).days <= 30
    )
    
    inactive = sum(
        1 for o in owners
        if not o.get('last_sign_in_at')
        or (datetime.now(timezone.utc) - o['last_sign_in_at']).days > 90
    )
    
    return {
        'total_owners': total,
        'owners_with_2fa': with_2fa,
        'owners_without_2fa': without_2fa,
        'percent_with_2fa': round(100.0 * with_2fa / total, 2) if total > 0 else 0,
        'active_owners_without_2fa': active_without_2fa,
        'inactive_owners': inactive
    }


def export_to_csv(owners: List[Dict[str, Any]], filename: str):
    """
    Export owner accounts to CSV file
    
    Args:
        owners: List of owner account dictionaries
        filename: Output CSV filename
    """
    if not owners:
        print("No owner accounts to export")
        return
    
    fieldnames = [
        'user_id',
        'email',
        'role',
        'account_created',
        'last_login',
        'twofa_enabled',
        'twofa_verified_at',
        'twofa_last_used',
        'status',
        'days_since_last_login',
        'risk_level'
    ]
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for owner in owners:
            last_login = owner.get('last_sign_in_at')
            days_since_login = (
                (datetime.now(timezone.utc) - last_login).days 
                if last_login else None
            )
            
            row = {
                'user_id': owner.get('user_id'),
                'email': owner.get('email'),
                'role': owner.get('role', 'owner'),
                'account_created': owner.get('created_at'),
                'last_login': last_login,
                'twofa_enabled': owner.get('twofa_enabled', False),
                'twofa_verified_at': owner.get('twofa_verified_at'),
                'twofa_last_used': owner.get('twofa_last_used'),
                'status': '✅ Enabled' if owner.get('twofa_enabled') else '❌ Not Enabled',
                'days_since_last_login': days_since_login,
                'risk_level': calculate_risk_level(owner)
            }
            
            writer.writerow(row)
    
    print(f"\n✅ Exported {len(owners)} owner accounts to {filename}")


def print_summary(stats: Dict[str, Any]):
    """
    Print summary statistics to console
    
    Args:
        stats: Dictionary of summary statistics
    """
    print("\n" + "="*60)
    print("OWNER ACCOUNT 2FA INVENTORY SUMMARY")
    print("="*60)
    print(f"Total Owner Accounts:           {stats['total_owners']}")
    print(f"Owners with 2FA Enabled:        {stats['owners_with_2fa']} ({stats['percent_with_2fa']}%)")
    print(f"Owners without 2FA:             {stats['owners_without_2fa']}")
    print(f"Active Owners without 2FA:      {stats['active_owners_without_2fa']} ⚠️  HIGH RISK")
    print(f"Inactive Owners (90+ days):     {stats['inactive_owners']}")
    print("="*60)


def main():
    """Main execution function"""
    env = 'staging'
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--env', '-e']:
            env = sys.argv[2] if len(sys.argv) > 2 else 'staging'
        else:
            env = sys.argv[1]
    
    if env not in ENVIRONMENTS:
        print(f"Error: Invalid environment '{env}'. Must be 'staging' or 'production'")
        sys.exit(1)
    
    print(f"Environment: {env.upper()}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        supabase = get_supabase_client(env)
        print("✅ Connected to Supabase")
        
        owners = fetch_owner_accounts(supabase)
        
        if not owners:
            print("\n⚠️  No owner accounts found or unable to fetch from auth.users")
            print("\nPlease use one of these alternatives:")
            print("1. Run SQL queries in 03-owner-inventory-template.sql via Supabase SQL Editor")
            print("2. Use Supabase Admin API to fetch user metadata")
            print("3. Grant this script access to auth.users table")
            sys.exit(0)
        
        stats = generate_summary_stats(owners)
        print_summary(stats)
        
        timestamp = datetime.now().strftime('%Y-%m-%d')
        filename = f"owner_2fa_inventory_{env}_{timestamp}.csv"
        export_to_csv(owners, filename)
        
        high_risk = [o for o in owners if calculate_risk_level(o) == 'HIGH']
        if high_risk:
            print(f"\n⚠️  {len(high_risk)} HIGH RISK ACCOUNTS (Active without 2FA):")
            for owner in high_risk[:10]:  # Show first 10
                print(f"  - {owner['email']} (last login: {owner.get('last_sign_in_at')})")
            if len(high_risk) > 10:
                print(f"  ... and {len(high_risk) - 10} more")
        
        print("\n✅ Inventory generation complete")
        
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
