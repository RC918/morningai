#!/usr/bin/env python3
"""Check Redis Python package version for security compliance."""

import os
import subprocess
import sys

from packaging import version


def main():
    """Check if Redis Python package version is acceptable."""
    result = subprocess.run(['pip', 'show', 'redis'], capture_output=True, text=True)
    pkg_version = None
    for line in result.stdout.split('\n'):
        if line.startswith('Version:'):
            pkg_version = line.split(':')[1].strip()
            break

    print(f'Redis Python package version: {pkg_version}')

    if pkg_version:
        v = version.parse(pkg_version)
        if v < version.parse('5.0.0'):
            print('::warning::Redis Python package is outdated. Recommend upgrading to >= 5.0.0')
            with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
                f.write('package_outdated=true\n')
        else:
            print('Redis Python package version is acceptable')
            with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
                f.write('package_outdated=false\n')


if __name__ == '__main__':
    main()
