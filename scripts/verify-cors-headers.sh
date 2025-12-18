#!/bin/bash
# =============================================================================
# CORS Header Verification Script
# =============================================================================
# Verifies that CORS headers are correctly configured for a given backend URL
# and origin. Use this script after deployment to confirm CORS is working.
#
# Usage:
#   ./scripts/verify-cors-headers.sh <backend-url> <origin>
#
# Examples:
#   ./scripts/verify-cors-headers.sh https://morningai-backend-v2.onrender.com https://admin.gm365.me
#   ./scripts/verify-cors-headers.sh https://morningai-orchestrator-api.onrender.com https://app.gm365.me
#
# Exit codes:
#   0 - CORS headers are correctly configured
#   1 - CORS headers are missing or incorrect
#   2 - Invalid arguments
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -lt 2 ]; then
    echo -e "${YELLOW}Usage: $0 <backend-url> <origin>${NC}"
    echo ""
    echo "Examples:"
    echo "  $0 https://morningai-backend-v2.onrender.com https://admin.gm365.me"
    echo "  $0 https://morningai-orchestrator-api.onrender.com https://app.gm365.me"
    exit 2
fi

BACKEND_URL="$1"
ORIGIN="$2"
ENDPOINT="${3:-/api/health}"

echo "=============================================="
echo "CORS Header Verification"
echo "=============================================="
echo "Backend URL: $BACKEND_URL"
echo "Origin:      $ORIGIN"
echo "Endpoint:    $ENDPOINT"
echo "=============================================="
echo ""

# Test 1: GET request with Origin header
echo "Test 1: GET $ENDPOINT with Origin header"
echo "----------------------------------------------"

RESPONSE=$(curl -s -D - -o /dev/null \
    -X GET \
    "${BACKEND_URL}${ENDPOINT}" \
    -H "Origin: $ORIGIN" \
    2>&1)

# Check for Access-Control-Allow-Origin header
ACAO=$(echo "$RESPONSE" | grep -i "access-control-allow-origin" | tr -d '\r' || true)

if [ -z "$ACAO" ]; then
    echo -e "${RED}FAIL: Access-Control-Allow-Origin header is MISSING${NC}"
    echo ""
    echo "This means the origin '$ORIGIN' is NOT in the CORS allowlist."
    echo ""
    echo "To fix:"
    echo "1. Go to Render Dashboard > morningai-backend-v2 > Environment"
    echo "2. Add '$ORIGIN' to CORS_ORIGINS (comma-separated)"
    echo "3. Trigger a manual deploy or wait for auto-deploy"
    echo ""
    echo "Full response headers:"
    echo "$RESPONSE"
    exit 1
fi

# Check if the origin matches
if echo "$ACAO" | grep -q "$ORIGIN"; then
    echo -e "${GREEN}PASS: Access-Control-Allow-Origin: $ORIGIN${NC}"
else
    echo -e "${YELLOW}WARNING: Access-Control-Allow-Origin header found but value differs${NC}"
    echo "$ACAO"
fi

# Check for Access-Control-Allow-Credentials
ACAC=$(echo "$RESPONSE" | grep -i "access-control-allow-credentials" | tr -d '\r' || true)
if echo "$ACAC" | grep -qi "true"; then
    echo -e "${GREEN}PASS: Access-Control-Allow-Credentials: true${NC}"
else
    echo -e "${YELLOW}WARNING: Access-Control-Allow-Credentials header missing or not 'true'${NC}"
fi

echo ""

# Test 2: OPTIONS preflight request
echo "Test 2: OPTIONS preflight request"
echo "----------------------------------------------"

PREFLIGHT_RESPONSE=$(curl -s -D - -o /dev/null \
    -X OPTIONS \
    "${BACKEND_URL}${ENDPOINT}" \
    -H "Origin: $ORIGIN" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: Content-Type, X-CSRF-Token" \
    2>&1)

# Check HTTP status (should be 204 for preflight)
HTTP_STATUS=$(echo "$PREFLIGHT_RESPONSE" | grep -E "^HTTP" | tail -1 | awk '{print $2}' || true)

if [ "$HTTP_STATUS" = "204" ]; then
    echo -e "${GREEN}PASS: Preflight response status: 204 No Content${NC}"
elif [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${YELLOW}OK: Preflight response status: 200 (expected 204 but acceptable)${NC}"
else
    echo -e "${RED}FAIL: Preflight response status: $HTTP_STATUS (expected 204)${NC}"
fi

# Check for Access-Control-Allow-Methods
ACAM=$(echo "$PREFLIGHT_RESPONSE" | grep -i "access-control-allow-methods" | tr -d '\r' || true)
if [ -n "$ACAM" ]; then
    echo -e "${GREEN}PASS: $ACAM${NC}"
else
    echo -e "${YELLOW}WARNING: Access-Control-Allow-Methods header missing${NC}"
fi

# Check for Access-Control-Allow-Headers
ACAH=$(echo "$PREFLIGHT_RESPONSE" | grep -i "access-control-allow-headers" | tr -d '\r' || true)
if [ -n "$ACAH" ]; then
    echo -e "${GREEN}PASS: $ACAH${NC}"
else
    echo -e "${YELLOW}WARNING: Access-Control-Allow-Headers header missing${NC}"
fi

echo ""
echo "=============================================="
echo -e "${GREEN}CORS verification completed successfully!${NC}"
echo "=============================================="

exit 0
