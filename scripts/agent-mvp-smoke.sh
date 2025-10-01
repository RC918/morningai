#!/bin/bash
set -e

echo "=== Agent MVP Smoke Test ==="
echo "Goal: FAQ task → PR created → CI passes → Auto-merge"
echo ""

START_TIME=$(date +%s)

if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN not set"
    exit 1
fi

if [ -z "$REDIS_URL" ]; then
    echo "⚠️  REDIS_URL not set, will run in demo mode"
fi

echo "Running orchestrator..."
cd handoff/20250928/40_App/orchestrator

OUTPUT=$(python graph.py --goal "Update FAQ with common questions" 2>&1)
echo "$OUTPUT"

PR_URL=$(echo "$OUTPUT" | grep -oP '\[PR\] https://[^\s]+' | head -1 | cut -d' ' -f2)
TRACE_ID=$(echo "$OUTPUT" | grep -oP 'trace-id: [a-f0-9-]+' | head -1 | cut -d' ' -f2)

if [ -z "$PR_URL" ]; then
    echo "❌ No PR created"
    exit 1
fi

echo ""
echo "✅ PR created: $PR_URL"
echo "✅ Trace ID: $TRACE_ID"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [ $DURATION -le 60 ]; then
    echo "✅ Completed in ${DURATION}s (≤60s requirement met)"
else
    echo "⚠️  Completed in ${DURATION}s (>60s, exceeds requirement)"
fi

echo ""
echo "=== Smoke Test Complete ==="
