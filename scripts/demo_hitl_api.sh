#!/bin/bash

set -e

BASE_URL="${BASE_URL:-http://localhost:5000}"

echo "=== HITL Approval API Demo ==="
echo "Note: This demo requires admin JWT token"
echo ""

JWT_TOKEN="${JWT_TOKEN:-}"
if [ -z "$JWT_TOKEN" ]; then
  echo "Please set JWT_TOKEN environment variable"
  echo "Example: export JWT_TOKEN=\$(curl -s http://localhost:5000/api/auth/login -d '{\"email\":\"admin@example.com\",\"password\":\"...\"}' -H 'Content-Type: application/json' | jq -r '.access_token')"
  exit 1
fi

echo "1. Get pending approval requests:"
curl -s "${BASE_URL}/api/hitl/requests" \
  -H "Authorization: Bearer $JWT_TOKEN" | python3 -m json.tool
echo ""

echo "2. Get HITL system status:"
curl -s "${BASE_URL}/api/hitl/status" \
  -H "Authorization: Bearer $JWT_TOKEN" | python3 -m json.tool
echo ""

echo "3. Get approval history:"
curl -s "${BASE_URL}/api/hitl/history?limit=10" \
  -H "Authorization: Bearer $JWT_TOKEN" | python3 -m json.tool
echo ""

echo "=== Demo Complete ==="
echo "To approve a request: curl -X POST ${BASE_URL}/api/hitl/approve/{request_id} -H 'Authorization: Bearer \$JWT_TOKEN' -d '{\"comments\":\"Approved\"}'"
echo "To reject a request: curl -X POST ${BASE_URL}/api/hitl/reject/{request_id} -H 'Authorization: Bearer \$JWT_TOKEN' -d '{\"comments\":\"Security concern\"}'"
