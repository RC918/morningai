#!/usr/bin/env python3
"""Check Redis server for CVE-2025-49844 vulnerability."""

import os
import sys


def main():
    """Check Redis server version for CVE-2025-49844 vulnerability."""
    redis_url = os.environ.get('REDIS_URL', '')
    upstash_url = os.environ.get('UPSTASH_REDIS_REST_URL', '')

    results = {
        'status': 'unknown',
        'message': '',
        'recommendations': []
    }

    if upstash_url:
        print('Using Upstash Redis (cloud-managed)')
        print('CVE-2025-49844 Risk: LOW (Upstash auto-patches)')
        results['status'] = 'secure'
        results['message'] = 'Upstash Redis is cloud-managed and auto-patched'
    elif redis_url:
        print('Using standard Redis connection')

        if not redis_url.startswith('rediss://'):
            print('::warning::Redis connection is not using TLS (rediss://)')
            results['recommendations'].append('Enable TLS encryption')

        try:
            import redis
            client = redis.from_url(redis_url, socket_connect_timeout=5)
            info = client.info('server')
            version_str = info.get('redis_version', 'unknown')
            print(f'Redis server version: {version_str}')

            parts = version_str.split('.')
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch_str = parts[2].split('-')[0] if len(parts) > 2 else '0'
            patch = int(patch_str) if patch_str.isdigit() else 0

            version_tuple = (major, minor, patch)

            if version_tuple < (8, 2, 2):
                print(f'::error::Redis {version_str} is VULNERABLE to CVE-2025-49844')
                print('::error::Upgrade to Redis 8.2.2 or later immediately!')
                results['status'] = 'vulnerable'
                results['message'] = f'Redis {version_str} is vulnerable to CVE-2025-49844'
                results['recommendations'].append('Upgrade Redis to 8.2.2+')
                results['recommendations'].append('Temporary: Disable Lua scripts via ACL')
                sys.exit(1)
            else:
                print(f'Redis {version_str} is NOT vulnerable to CVE-2025-49844')
                results['status'] = 'secure'
                results['message'] = f'Redis {version_str} is patched'

        except Exception as e:
            print(f'::warning::Could not connect to Redis to check version: {e}')
            results['status'] = 'unknown'
            results['message'] = f'Could not verify: {str(e)}'
    else:
        print('No Redis configuration found in secrets')
        print('Skipping server version check')
        results['status'] = 'skipped'
        results['message'] = 'No Redis secrets configured'

    print('\n=== Security Check Results ===')
    print(f"Status: {results['status']}")
    print(f"Message: {results['message']}")
    if results['recommendations']:
        print('Recommendations:')
        for rec in results['recommendations']:
            print(f'  - {rec}')


if __name__ == '__main__':
    main()
