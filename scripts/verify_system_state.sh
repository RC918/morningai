#!/bin/bash

set -eo pipefail  # Exit on error, but allow grep to fail gracefully

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

VERBOSE=false
if [[ "$1" == "--verbose" ]]; then
    VERBOSE=true
fi

ERRORS=0
WARNINGS=0
CHECKS=0

check_pass() {
    CHECKS=$((CHECKS + 1))
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    CHECKS=$((CHECKS + 1))
    ERRORS=$((ERRORS + 1))
    echo -e "${RED}✗${NC} $1"
}

check_warn() {
    CHECKS=$((CHECKS + 1))
    WARNINGS=$((WARNINGS + 1))
    echo -e "${YELLOW}⚠${NC} $1"
}

log_verbose() {
    if [[ "$VERBOSE" == true ]]; then
        echo "  → $1"
    fi
}

echo "========================================="
echo "MorningAI System State Verification"
echo "========================================="
echo ""

echo "1. Verifying React versions..."
# Single source of truth: read expected React version from root package.json pnpm overrides
# This ensures the verification script stays in sync with the monorepo's version policy
EXPECTED_REACT=$(node -p "require('./package.json').pnpm.overrides.react.replace('^', '')" 2>/dev/null || echo "19.1.0")
log_verbose "Expected React version from pnpm overrides: $EXPECTED_REACT"

FRONTEND_REACT=$(grep '"react":' handoff/20250928/40_App/frontend-dashboard/package.json | sed -E 's/[^0-9]*([0-9]+\.[0-9]+\.[0-9]+).*/\1/' | head -1)
OWNER_REACT=$(grep '"react":' handoff/20250928/40_App/owner-console/package.json | sed -E 's/[^0-9]*([0-9]+\.[0-9]+\.[0-9]+).*/\1/' | head -1)

if [[ "$FRONTEND_REACT" == "$EXPECTED_REACT" ]]; then
    check_pass "frontend-dashboard React version: $FRONTEND_REACT (matches pnpm override)"
else
    check_fail "frontend-dashboard React version mismatch: expected $EXPECTED_REACT (from pnpm overrides), got $FRONTEND_REACT"
fi

if [[ "$OWNER_REACT" == "$EXPECTED_REACT" ]]; then
    check_pass "owner-console React version: $OWNER_REACT (matches pnpm override)"
else
    check_fail "owner-console React version mismatch: expected $EXPECTED_REACT (from pnpm overrides), got $OWNER_REACT"
fi

echo ""
echo "2. Verifying pgvector implementation..."

if grep -R -qE 'CREATE[[:space:]]+EXTENSION[[:space:]]+IF[[:space:]]+NOT[[:space:]]+EXISTS[[:space:]]+vector' migrations/ 2>/dev/null; then
    check_pass "pgvector (vector extension) in main migrations/"
else
    check_fail "pgvector (vector extension) NOT found in migrations/"
fi

if grep -R -qE 'CREATE[[:space:]]+EXTENSION[[:space:]]+IF[[:space:]]+NOT[[:space:]]+EXISTS[[:space:]]+vector' agents/dev_agent/migrations/ 2>/dev/null; then
    check_pass "pgvector (vector extension) in dev_agent migrations"
else
    check_fail "pgvector (vector extension) NOT found in agents/dev_agent/migrations/"
fi

if grep -R -qE 'CREATE[[:space:]]+EXTENSION[[:space:]]+IF[[:space:]]+NOT[[:space:]]+EXISTS[[:space:]]+vector' agents/faq_agent/migrations/ 2>/dev/null; then
    check_pass "pgvector (vector extension) in faq_agent migrations"
else
    check_fail "pgvector (vector extension) NOT found in agents/faq_agent/migrations/"
fi

if [ -f "handoff/20250928/40_App/api-backend/src/routes/vectors.py" ]; then
    check_pass "Vector API implementation exists (src/routes/vectors.py)"
else
    check_fail "Vector API NOT found at src/routes/vectors.py"
fi

if grep -R -qE 'vector\s*\(\s*[0-9]+\s*\)' migrations/ agents/*/migrations/ 2>/dev/null; then
    check_pass "pgvector columns actively used in migrations (e.g., vector(1536))"
    log_verbose "$(grep -R -E 'vector\s*\(\s*[0-9]+\s*\)' migrations/ agents/*/migrations/ 2>/dev/null | wc -l) vector column definitions found"
else
    check_warn "No vector column definitions found (extension created but not yet used)"
fi

echo ""
echo "3. Verifying dual orchestrator architecture..."

if command -v yq >/dev/null 2>&1; then
    USE_LANGGRAPH_VALUE=$(yq eval '.services[] | select(.envVars[] | select(.key == "USE_LANGGRAPH")) | .envVars[] | select(.key == "USE_LANGGRAPH") | .value' render.yaml 2>/dev/null | head -1)
    if [[ "$USE_LANGGRAPH_VALUE" == "false" ]]; then
        check_pass "USE_LANGGRAPH=false in render.yaml (verified with yq)"
    else
        check_fail "USE_LANGGRAPH flag not set to false in render.yaml (got: $USE_LANGGRAPH_VALUE)"
    fi
else
    if awk '/- key: USE_LANGGRAPH/{getline; if ($0 ~ /value: false/) ok=1} END{exit(ok?0:1)}' render.yaml 2>/dev/null; then
        check_pass "USE_LANGGRAPH=false in render.yaml (verified with awk)"
    else
        check_fail "USE_LANGGRAPH flag not set to false in render.yaml"
    fi
fi

if grep -q "handoff/.*/orchestrator" render.yaml; then
    check_pass "Legacy orchestrator path in render.yaml (worker deployment)"
else
    check_warn "Legacy orchestrator path not found in render.yaml"
fi

if grep -q "orchestrator/Dockerfile" render.yaml; then
    check_pass "New orchestrator Dockerfile reference in render.yaml"
else
    check_fail "New orchestrator Dockerfile not referenced in render.yaml"
fi

if ! grep -q "langgraph" orchestrator/requirements.txt 2>/dev/null; then
    check_pass "New orchestrator does NOT include langgraph"
else
    check_fail "New orchestrator should NOT include langgraph dependency"
fi

if [ -f "handoff/20250928/40_App/orchestrator/langgraph_orchestrator.py" ]; then
    check_pass "Legacy orchestrator with LangGraph exists"
else
    check_warn "Legacy orchestrator file not found (may have been removed)"
fi

echo ""
echo "4. Verifying production URL mapping..."

if grep -q "app.gm365.me" docs/TERMINOLOGY.md && grep -q "admin.gm365.me" docs/TERMINOLOGY.md; then
    check_pass "Production URLs documented in TERMINOLOGY.md"
else
    check_fail "Production URLs not properly documented in TERMINOLOGY.md"
fi

if grep -q "https://app.gm365.me" render.yaml && grep -q "https://admin.gm365.me" render.yaml; then
    check_pass "Production URLs in CORS configuration (render.yaml)"
else
    check_warn "Production URLs may not be in CORS configuration"
fi

echo ""
echo "5. Verifying Alembic status (should be implemented)..."

if [ -f "handoff/20250928/40_App/api-backend/alembic.ini" ]; then
    check_pass "Alembic implemented (alembic.ini exists)"
else
    check_fail "Alembic NOT implemented (alembic.ini missing)"
fi

if [ -d "handoff/20250928/40_App/api-backend/alembic" ]; then
    check_pass "Alembic implemented (alembic/ directory exists)"
else
    check_fail "Alembic NOT implemented (alembic/ directory missing)"
fi

if [ -d "handoff/20250928/40_App/api-backend/alembic/versions" ]; then
    check_pass "Alembic versions directory exists"
else
    check_fail "Alembic versions directory missing"
fi

if grep -q "^alembic" handoff/20250928/40_App/api-backend/requirements.txt; then
    check_pass "Alembic in requirements.txt"
else
    check_fail "Alembic NOT in requirements.txt"
fi

echo ""
echo "6. Verifying Phase API module status..."

PHASE_FILES=("phase4_meta_agent_api.py" "phase5_data_intelligence_api.py" "phase6_security_governance_api.py" "phase7_startup.py")
for file in "${PHASE_FILES[@]}"; do
    if [ -f "$file" ]; then
        check_pass "Phase API module exists: $file"
    else
        check_warn "Phase API module not found: $file"
    fi
done

if grep -qE '^(from|import)[[:space:]]+phase[4-7]' handoff/20250928/40_App/api-backend/src/main.py 2>/dev/null; then
    check_fail "main.py directly imports Phase API modules (should be lazy loaded)"
    log_verbose "Found: $(grep -E '^(from|import)[[:space:]]+phase[4-7]' handoff/20250928/40_App/api-backend/src/main.py 2>/dev/null)"
else
    check_pass "main.py does NOT directly import Phase API modules"
fi

echo ""
echo "7. Checking critical environment variables..."

if [ -n "$REDIS_URL" ]; then
    check_pass "REDIS_URL is set"
    log_verbose "REDIS_URL: ${REDIS_URL:0:20}..."
else
    check_warn "REDIS_URL not set (required for production)"
fi

if [ -n "$DATABASE_URL" ]; then
    check_pass "DATABASE_URL is set"
    log_verbose "DATABASE_URL: ${DATABASE_URL:0:20}..."
else
    check_warn "DATABASE_URL not set (required for production)"
fi

echo ""
echo "8. Verifying test framework..."

if [ -f "handoff/20250928/40_App/api-backend/tests/conftest.py" ]; then
    check_pass "pytest conftest.py exists"
else
    check_fail "pytest conftest.py NOT found"
fi

if [ -f "handoff/20250928/40_App/api-backend/pytest.ini" ]; then
    check_pass "pytest.ini configuration exists"
else
    check_warn "pytest.ini not found"
fi

echo ""
echo "9. Checking critical dependencies..."

cd handoff/20250928/40_App/api-backend

if grep -q "^PyJWT" requirements.txt; then
    check_pass "PyJWT in requirements.txt"
else
    check_fail "PyJWT NOT in requirements.txt"
fi

if grep -q "^rq" requirements.txt; then
    check_pass "rq (Redis Queue) in requirements.txt"
else
    check_fail "rq NOT in requirements.txt"
fi

if grep -q "^pyotp" requirements.txt; then
    check_pass "pyotp in requirements.txt"
else
    check_fail "pyotp NOT in requirements.txt"
fi

if grep -q "^numpy" requirements.txt; then
    check_pass "numpy in requirements.txt"
else
    check_fail "numpy NOT in requirements.txt"
fi

cd - > /dev/null

echo ""
echo "10. Verifying Architecture Decision Records..."

if [ -f "docs/adr/005-dual-orchestrator-architecture.md" ]; then
    check_pass "ADR-005 (Dual Orchestrator) exists"
else
    check_fail "ADR-005 NOT found"
fi

echo ""
echo "========================================="
echo "Verification Summary"
echo "========================================="
echo "Total checks: $CHECKS"
echo -e "${GREEN}Passed: $((CHECKS - ERRORS - WARNINGS))${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo -e "${RED}Errors: $ERRORS${NC}"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}❌ Verification FAILED${NC}"
    echo "Please fix the errors above before proceeding."
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Verification PASSED with warnings${NC}"
    echo "Consider addressing the warnings above."
    exit 0
else
    echo -e "${GREEN}✅ Verification PASSED${NC}"
    echo "All checks passed successfully!"
    exit 0
fi
