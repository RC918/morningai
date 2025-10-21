#!/bin/bash
set -e

echo "Current directory: $(pwd)"
echo "Listing handoff directory:"
ls -la handoff/20250928/40_App/ || echo "handoff directory not found"

cd handoff/20250928/40_App/frontend-dashboard
npm run build
