#!/bin/bash
set -e

echo "=== Vercel Build Script ==="
echo "Current directory: $(pwd)"
echo "Checking if frontend-dashboard exists:"
test -d handoff/20250928/40_App/frontend-dashboard && echo "✓ Directory exists" || echo "✗ Directory NOT found"
test -f handoff/20250928/40_App/frontend-dashboard/package.json && echo "✓ package.json exists" || echo "✗ package.json NOT found"

echo ""
echo "Navigating to frontend-dashboard..."
cd handoff/20250928/40_App/frontend-dashboard || {
    echo "ERROR: Failed to cd into frontend-dashboard"
    echo "Listing current directory:"
    ls -la
    exit 1
}

echo "Running build with pnpm..."
pnpm run build
