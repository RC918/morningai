#!/bin/bash

set -e

BASE_URL="${BASE_URL:-http://localhost:5000}"

echo "=== MCP API Demo ==="
echo ""

echo "1. List all tools:"
curl -s "${BASE_URL}/api/mcp/tools" | python3 -m json.tool
echo ""

echo "2. Get shell tool details:"
curl -s "${BASE_URL}/api/mcp/tools/shell" | python3 -m json.tool
echo ""

echo "3. Validate low-risk command:"
curl -s -X POST "${BASE_URL}/api/mcp/tools/shell/validate" \
  -H "Content-Type: application/json" \
  -d '{"command": "ls -la"}' | python3 -m json.tool
echo ""

echo "4. Validate high-risk command (requires approval):"
curl -s -X POST "${BASE_URL}/api/mcp/tools/shell/validate" \
  -H "Content-Type: application/json" \
  -d '{"command": "rm -rf /tmp/test"}' | python3 -m json.tool
echo ""

echo "=== Demo Complete ===" 
