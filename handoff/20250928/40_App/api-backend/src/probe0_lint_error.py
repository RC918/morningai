#!/usr/bin/env python3

import pylint.lint

def main():
    try:
        pylint_opts = ['--errors-only', 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py']
        pylint.lint.Run(pylint_opts)
    except Exception as e:
        print(f"An error occurred when running pylint: {e}")

if __name__ == "__main__":
    main()