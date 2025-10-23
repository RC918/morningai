#!/usr/bin/env python3
"""
Production Log Monitor - Checks for 401 authentication errors after RLS deployment
Monitors logs from Render backend and Sentry for 24 hours
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
import requests
from collections import defaultdict

RENDER_API_KEY = os.environ.get('RENDER_API_KEY')
SENTRY_AUTH_TOKEN = os.environ.get('SENTRY_AUTH_TOKEN')
SENTRY_DSN = os.environ.get('SENTRY_DSN')

if not RENDER_API_KEY:
    print("ERROR: RENDER_API_KEY not set")
    sys.exit(1)

if not SENTRY_AUTH_TOKEN:
    print("ERROR: SENTRY_AUTH_TOKEN not set")
    sys.exit(1)


def get_render_services():
    """Get list of Render services"""
    headers = {
        'Authorization': f'Bearer {RENDER_API_KEY}',
        'Accept': 'application/json'
    }

    response = requests.get('https://api.render.com/v1/services', headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get Render services: {response.status_code}")
        return []


def get_render_logs(service_id, start_time):
    """Get logs from Render service"""
    headers = {
        'Authorization': f'Bearer {RENDER_API_KEY}',
        'Accept': 'application/json'
    }

    params = {
        'startTime': start_time.isoformat(),
        'limit': 1000
    }

    response = requests.get(
        f'https://api.render.com/v1/services/{service_id}/logs',
        headers=headers,
        params=params
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get logs for service {service_id}: {response.status_code}")
        return []


def check_sentry_issues(start_time):
    """Check Sentry for 401 errors"""
    if not SENTRY_DSN:
        print("SENTRY_DSN not configured, skipping Sentry check")
        return []

    org_slug = SENTRY_DSN.split('@')[1].split('.')[0] if '@' in SENTRY_DSN else None
    if not org_slug:
        print("Could not parse Sentry org from DSN")
        return []

    headers = {
        'Authorization': f'Bearer {SENTRY_AUTH_TOKEN}',
        'Content-Type': 'application/json'
    }

    params = {
        'query': 'status:unresolved 401',
        'start': start_time.isoformat(),
        'statsPeriod': '24h'
    }

    try:
        response = requests.get(
            f'https://sentry.io/api/0/organizations/{org_slug}/issues/',
            headers=headers,
            params=params
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get Sentry issues: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error checking Sentry: {e}")
        return []


def analyze_logs_for_401(logs):
    """Analyze logs for 401 errors"""
    errors = []
    error_counts = defaultdict(int)

    for log in logs:
        log_text = log.get('message', '') if isinstance(log, dict) else str(log)

        if '401' in log_text or 'Unauthorized' in log_text or 'authentication' in log_text.lower():
            errors.append({
                'timestamp': log.get('timestamp', datetime.now().isoformat()) if isinstance(log, dict) else datetime.now().isoformat(),
                'message': log_text[:200]
            })

            if 'RLS' in log_text or 'row level security' in log_text.lower():
                error_counts['RLS_related'] += 1
            elif 'JWT' in log_text or 'token' in log_text.lower():
                error_counts['JWT_related'] += 1
            else:
                error_counts['other_401'] += 1

    return errors, error_counts


def main():
    print("=" * 80)
    print("Production Log Monitor - Post RLS Deployment")
    print("=" * 80)
    print(f"Start Time: {datetime.now().isoformat()}")
    print("Monitoring Duration: 24 hours")
    print()

    start_time = datetime.now()
    end_time = start_time + timedelta(hours=24)

    print("Getting Render services...")
    services = get_render_services()

    if not services:
        print("No Render services found or API error")
        return

    backend_services = [s for s in services if 'backend' in s.get('name', '').lower() or 'api' in s.get('name', '').lower()]

    if not backend_services:
        print("No backend services found")
        print(f"Available services: {[s.get('name') for s in services]}")
        return

    print(f"Found {len(backend_services)} backend service(s):")
    for svc in backend_services:
        print(f"  - {svc.get('name')} (ID: {svc.get('id')})")
    print()

    check_interval = 300
    total_401_errors = 0
    all_errors = []

    print(f"Starting monitoring (checking every {check_interval} seconds)...")
    print("Press Ctrl+C to stop early and generate report")
    print()

    try:
        while datetime.now() < end_time:
            current_time = datetime.now()
            print(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] Checking logs...")

            for service in backend_services:
                service_id = service.get('id')
                service_name = service.get('name')

                logs = get_render_logs(service_id, start_time)
                errors, error_counts = analyze_logs_for_401(logs)

                if errors:
                    print(f"  ⚠️  {service_name}: Found {len(errors)} 401 errors")
                    for error_type, count in error_counts.items():
                        print(f"      - {error_type}: {count}")
                    all_errors.extend(errors)
                    total_401_errors += len(errors)
                else:
                    print(f"  ✅ {service_name}: No 401 errors")

            sentry_issues = check_sentry_issues(start_time)
            if sentry_issues:
                print(f"  ⚠️  Sentry: Found {len(sentry_issues)} unresolved 401-related issues")
            else:
                print("  ✅ Sentry: No 401-related issues")

            print()

            remaining = end_time - current_time
            if remaining.total_seconds() > check_interval:
                time.sleep(check_interval)
            else:
                break

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")

    print("\n" + "=" * 80)
    print("MONITORING REPORT")
    print("=" * 80)
    print(f"Duration: {datetime.now() - start_time}")
    print(f"Total 401 Errors Found: {total_401_errors}")
    print()

    if all_errors:
        print("Recent 401 Errors (last 10):")
        for error in all_errors[-10:]:
            print(f"  [{error['timestamp']}] {error['message']}")
    else:
        print("✅ No 401 errors detected during monitoring period")

    report_file = f'/tmp/production_monitoring_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(report_file, 'w') as f:
        json.dump({
            'start_time': start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'total_401_errors': total_401_errors,
            'errors': all_errors
        }, f, indent=2)

    print(f"\nFull report saved to: {report_file}")

    if total_401_errors > 0:
        print("\n⚠️  WARNING: 401 errors detected! Review the report and check application authentication.")
        sys.exit(1)
    else:
        print("\n✅ SUCCESS: No 401 errors detected during monitoring period")
        sys.exit(0)

if __name__ == '__main__':

    main()
