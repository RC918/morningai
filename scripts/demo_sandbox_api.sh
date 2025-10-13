#!/bin/bash

set -e

BASE_URL="${BASE_URL:-http://localhost:5000}"

echo "=== Sandbox Runner API Demo ==="
echo ""

echo "1. Starting sandbox task..."
RESPONSE=$(curl -s -X POST "${BASE_URL}/api/sandbox/run" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "demo-agent-001",
    "agent_type": "ops_agent",
    "command": "sleep 5 && echo \"Task completed\" && ls -la",
    "timeout_seconds": 30
  }')

SANDBOX_ID=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['sandbox_id'])" 2>/dev/null || echo "")

if [ -z "$SANDBOX_ID" ]; then
  echo "Failed to start sandbox"
  echo "$RESPONSE" | python3 -m json.tool
  exit 1
fi

echo "Sandbox ID: $SANDBOX_ID"
echo "$RESPONSE" | python3 -m json.tool
echo ""

echo "2. Getting sandbox status..."
sleep 2
curl -s "${BASE_URL}/api/sandbox/status/${SANDBOX_ID}" | python3 -m json.tool
echo ""

echo "3. Getting sandbox logs..."
sleep 4
curl -s "${BASE_URL}/api/sandbox/logs/${SANDBOX_ID}" | python3 -m json.tool
echo ""

echo "4. Stopping sandbox..."
curl -s -X POST "${BASE_URL}/api/sandbox/stop/${SANDBOX_ID}" | python3 -m json.tool
echo ""

echo "=== Demo Complete ==="
