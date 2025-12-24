#!/usr/bin/env python3
"""Validate YAML syntax for all GitHub Actions workflow files."""

import sys
from pathlib import Path

import yaml


def main():
    """Validate all workflow YAML files."""
    errors = []
    for f in Path('.github/workflows').glob('*.yml'):
        try:
            yaml.safe_load(f.read_text())
            print(f'OK: {f}')
        except yaml.YAMLError as e:
            print(f'ERROR: {f}')
            print(f'  {e}')
            errors.append(str(f))

    if errors:
        print(f'\nFailed files: {len(errors)}')
        sys.exit(1)
    else:
        print('\nAll workflow files are valid YAML')


if __name__ == '__main__':
    main()
