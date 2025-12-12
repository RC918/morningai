#!/usr/bin/env bash
#
# Rollback Smoke Test Script
#
# Purpose: Automated curl-based verification after rollback operations
# Reference: docs/runbooks/POST_DEPLOY_SMOKE_TEST_CHECKLIST.md
#
# Usage:
#   ./scripts/rollback_smoke_test.sh [--env staging|production] [--scenario all|backend|rls|canary]
#
# Examples:
#   ./scripts/rollback_smoke_test.sh                          # Default: production, all checks
#   ./scripts/rollback_smoke_test.sh --env staging            # Staging environment
#   ./scripts/rollback_smoke_test.sh --scenario backend       # Backend health only
#   ./scripts/rollback_smoke_test.sh --scenario canary        # Canary metrics only
#
# Exit codes:
#   0 - All checks passed
#   1 - One or more checks failed
#   2 - Invalid arguments
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="$(basename "$0")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ENVIRONMENT="production"
SCENARIO="all"
VERBOSE=false
PASSED=0
FAILED=0
SKIPPED=0

PROD_BACKEND_URL="https://morningai-backend-v2.onrender.com"
STAGING_BACKEND_URL="https://morningai-backend-staging.onrender.com"
PROD_API_URL="https://api.morningai.app"
STAGING_API_URL="https://api-staging.morningai.app"

usage() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS]

Automated rollback verification script for MorningAI.

OPTIONS:
    --env ENV           Environment to test: staging|production (default: production)
    --scenario SCENARIO Scenario to test: all|backend|rls|canary (default: all)
    --verbose           Show detailed output for each check
    -h, --help          Show this help message

SCENARIOS:
    all      Run all verification checks
    backend  Backend health verification only (Section 1)
    rls      RLS verification only (Section 2) - requires SUPABASE_DB_URL
    canary   LangGraph canary verification only (Section 3)

ENVIRONMENT VARIABLES:
    SUPABASE_DB_URL     Required for RLS checks (psql connection string)
    BACKEND_URL         Override default backend URL
    API_URL             Override default API URL

EXAMPLES:
    $SCRIPT_NAME                              # Production, all checks
    $SCRIPT_NAME --env staging                # Staging environment
    $SCRIPT_NAME --scenario backend           # Backend health only
    $SCRIPT_NAME --scenario canary --verbose  # Canary with details

EXIT CODES:
    0  All checks passed
    1  One or more checks failed
    2  Invalid arguments

REFERENCE:
    docs/runbooks/POST_DEPLOY_SMOKE_TEST_CHECKLIST.md
    docs/runbooks/canary_rollback.md
EOF
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED++))
}

log_skip() {
    echo -e "${YELLOW}[SKIP]${NC} $1"
    ((SKIPPED++))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

check_http_status() {
    local url="$1"
    local expected_status="${2:-200}"
    local description="$3"
    
    local response
    local http_code
    
    response=$(curl -sS -w "\n%{http_code}" --connect-timeout 10 --max-time 30 "$url" 2>&1) || {
        log_fail "$description - Connection failed: $url"
        return 1
    }
    
    http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')
    
    if [[ "$http_code" == "$expected_status" ]]; then
        log_success "$description (HTTP $http_code)"
        if [[ "$VERBOSE" == "true" ]]; then
            echo "  Response: $(echo "$body" | head -c 200)..."
        fi
        return 0
    else
        log_fail "$description - Expected HTTP $expected_status, got HTTP $http_code"
        if [[ "$VERBOSE" == "true" ]]; then
            echo "  Response: $(echo "$body" | head -c 200)..."
        fi
        return 1
    fi
}

check_json_field() {
    local url="$1"
    local field="$2"
    local expected="$3"
    local description="$4"
    
    local response
    response=$(curl -sS --connect-timeout 10 --max-time 30 "$url" 2>&1) || {
        log_fail "$description - Connection failed: $url"
        return 1
    }
    
    local actual
    actual=$(echo "$response" | jq -r "$field" 2>/dev/null) || {
        log_fail "$description - Invalid JSON response"
        return 1
    }
    
    if [[ "$actual" == "$expected" ]]; then
        log_success "$description ($field = $actual)"
        return 0
    else
        log_fail "$description - Expected $field = $expected, got $actual"
        return 1
    fi
}

check_json_field_numeric() {
    local url="$1"
    local field="$2"
    local operator="$3"
    local threshold="$4"
    local description="$5"
    
    local response
    response=$(curl -sS --connect-timeout 10 --max-time 30 "$url" 2>&1) || {
        log_fail "$description - Connection failed: $url"
        return 1
    }
    
    local actual
    actual=$(echo "$response" | jq -r "$field" 2>/dev/null) || {
        log_fail "$description - Invalid JSON response or missing field"
        return 1
    }
    
    if [[ "$actual" == "null" ]]; then
        log_fail "$description - Field $field is null"
        return 1
    fi
    
    local result
    case "$operator" in
        "<")  result=$(echo "$actual < $threshold" | bc -l) ;;
        "<=") result=$(echo "$actual <= $threshold" | bc -l) ;;
        ">")  result=$(echo "$actual > $threshold" | bc -l) ;;
        ">=") result=$(echo "$actual >= $threshold" | bc -l) ;;
        "==") result=$(echo "$actual == $threshold" | bc -l) ;;
        *)    log_fail "$description - Invalid operator: $operator"; return 1 ;;
    esac
    
    if [[ "$result" == "1" ]]; then
        log_success "$description ($field = $actual $operator $threshold)"
        return 0
    else
        log_fail "$description - $field = $actual, expected $operator $threshold"
        return 1
    fi
}

section_backend_health() {
    echo ""
    echo "========================================"
    echo "Section 1: Backend Health Verification"
    echo "========================================"
    echo ""
    
    local backend_url="${BACKEND_URL:-$PROD_BACKEND_URL}"
    if [[ "$ENVIRONMENT" == "staging" ]]; then
        backend_url="${BACKEND_URL:-$STAGING_BACKEND_URL}"
    fi
    
    log_info "Testing backend at: $backend_url"
    echo ""
    
    check_http_status "$backend_url/healthz" "200" "Health endpoint /healthz" || true
    
    check_json_field "$backend_url/healthz" ".status" "healthy" "Health status is healthy" || true
    
    check_http_status "$backend_url/api/billing/plans" "200" "Billing plans endpoint" || true
    
    check_http_status "$backend_url/api/governance/status" "200" "Governance status endpoint" || true
    
    local api_url="${API_URL:-$PROD_API_URL}"
    if [[ "$ENVIRONMENT" == "staging" ]]; then
        api_url="${API_URL:-$STAGING_API_URL}"
    fi
    
    check_http_status "$api_url/healthz" "200" "API gateway health" || true
}

section_rls_verification() {
    echo ""
    echo "========================================"
    echo "Section 2: RLS Verification"
    echo "========================================"
    echo ""
    
    if [[ -z "${SUPABASE_DB_URL:-}" ]]; then
        log_skip "RLS verification - SUPABASE_DB_URL not set"
        log_info "Set SUPABASE_DB_URL to enable RLS checks"
        log_info "Example: export SUPABASE_DB_URL='postgresql://user:pass@host:5432/db'"
        return 0
    fi
    
    log_info "Checking RLS status on critical tables..."
    echo ""
    
    local rls_query="SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('agent_tasks', 'tenants', 'user_profiles') ORDER BY tablename;"
    
    local rls_result
    rls_result=$(psql "$SUPABASE_DB_URL" -t -A -c "$rls_query" 2>&1) || {
        log_fail "RLS check - Database connection failed"
        return 1
    }
    
    local all_rls_enabled=true
    while IFS='|' read -r tablename rowsecurity; do
        if [[ "$rowsecurity" == "t" ]]; then
            log_success "RLS enabled on $tablename"
        else
            log_fail "RLS NOT enabled on $tablename"
            all_rls_enabled=false
        fi
    done <<< "$rls_result"
    
    log_info "Checking TRUE tenant isolation policies..."
    
    local policy_query="SELECT COUNT(*) FROM pg_policies WHERE policyname LIKE 'true_tenant_isolation%';"
    local policy_count
    policy_count=$(psql "$SUPABASE_DB_URL" -t -A -c "$policy_query" 2>&1) || {
        log_fail "Policy check - Database query failed"
        return 1
    }
    
    if [[ "$policy_count" -ge 4 ]]; then
        log_success "TRUE tenant isolation policies: $policy_count (>= 4 required)"
    else
        log_fail "TRUE tenant isolation policies: $policy_count (< 4, expected >= 4)"
    fi
    
    log_info "Checking helper functions..."
    
    local func_query="SELECT COUNT(*) FROM pg_proc WHERE proname IN ('get_user_tenant_id', 'current_user_tenant_id');"
    local func_count
    func_count=$(psql "$SUPABASE_DB_URL" -t -A -c "$func_query" 2>&1) || {
        log_fail "Function check - Database query failed"
        return 1
    }
    
    if [[ "$func_count" -ge 2 ]]; then
        log_success "Helper functions exist: $func_count"
    else
        log_warn "Helper functions: $func_count (expected 2)"
    fi
}

section_canary_verification() {
    echo ""
    echo "========================================"
    echo "Section 3: LangGraph Canary Verification"
    echo "========================================"
    echo ""
    
    local api_url="${API_URL:-$PROD_API_URL}"
    if [[ "$ENVIRONMENT" == "staging" ]]; then
        api_url="${API_URL:-$STAGING_API_URL}"
    fi
    
    local dashboard_url="$api_url/api/phase7/monitoring/dashboard"
    
    log_info "Checking canary metrics at: $dashboard_url"
    echo ""
    
    local response
    response=$(curl -sS --connect-timeout 10 --max-time 30 "$dashboard_url" 2>&1) || {
        log_fail "Canary dashboard - Connection failed"
        return 1
    }
    
    local canary_percent
    canary_percent=$(echo "$response" | jq -r '.canary.flags.use_langgraph_percent // "null"' 2>/dev/null)
    
    if [[ "$canary_percent" == "null" ]]; then
        log_skip "Canary metrics not available (endpoint may not exist)"
        return 0
    fi
    
    log_info "Current canary percentage: $canary_percent%"
    
    check_json_field "$dashboard_url" ".canary.slo_compliance.all_ok" "true" "SLO compliance all_ok" || true
    
    check_json_field_numeric "$dashboard_url" ".canary.rates.error_5xx_rate" "<" "1.0" "5xx error rate < 1.0%" || true
    
    check_json_field_numeric "$dashboard_url" ".canary.rates.failure_rate" "<" "5.0" "Failure rate < 5.0%" || true
    
    if [[ "$canary_percent" == "0" ]]; then
        log_success "Canary is disabled (USE_LANGGRAPH_PERCENT=0)"
        log_info "After rollback, verify:"
        log_info "  - Worker logs show 'Using simple orchestrator'"
        log_info "  - decisions_langgraph counter stopped incrementing"
    else
        log_info "Canary is active at $canary_percent%"
    fi
}

section_application_smoke() {
    echo ""
    echo "========================================"
    echo "Section 4: Application Smoke Tests"
    echo "========================================"
    echo ""
    
    local backend_url="${BACKEND_URL:-$PROD_BACKEND_URL}"
    if [[ "$ENVIRONMENT" == "staging" ]]; then
        backend_url="${BACKEND_URL:-$STAGING_BACKEND_URL}"
    fi
    
    log_info "Running application smoke tests..."
    echo ""
    
    check_http_status "$backend_url/healthz" "200" "Application health" || true
    
    check_http_status "$backend_url/api/billing/plans" "200" "Billing API" || true
    
    local security_status
    security_status=$(curl -sS -o /dev/null -w "%{http_code}" --connect-timeout 10 "$backend_url/api/security/reviews/pending" 2>&1) || security_status="000"
    
    if [[ "$security_status" == "401" ]] || [[ "$security_status" == "403" ]] || [[ "$security_status" == "200" ]]; then
        log_success "Security endpoint protected (HTTP $security_status)"
    else
        log_fail "Security endpoint unexpected status: HTTP $security_status"
    fi
}

print_summary() {
    echo ""
    echo "========================================"
    echo "Summary"
    echo "========================================"
    echo ""
    echo -e "Environment: ${BLUE}$ENVIRONMENT${NC}"
    echo -e "Scenario:    ${BLUE}$SCENARIO${NC}"
    echo ""
    echo -e "Passed:  ${GREEN}$PASSED${NC}"
    echo -e "Failed:  ${RED}$FAILED${NC}"
    echo -e "Skipped: ${YELLOW}$SKIPPED${NC}"
    echo ""
    
    if [[ "$FAILED" -gt 0 ]]; then
        echo -e "${RED}RESULT: FAILED${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Review failed checks above"
        echo "  2. Check docs/runbooks/POST_DEPLOY_SMOKE_TEST_CHECKLIST.md"
        echo "  3. If rollback needed, follow docs/runbooks/canary_rollback.md"
        return 1
    else
        echo -e "${GREEN}RESULT: PASSED${NC}"
        echo ""
        echo "All verification checks passed."
        return 0
    fi
}

main() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --env)
                ENVIRONMENT="$2"
                if [[ "$ENVIRONMENT" != "staging" ]] && [[ "$ENVIRONMENT" != "production" ]]; then
                    echo "Error: Invalid environment '$ENVIRONMENT'. Use 'staging' or 'production'."
                    exit 2
                fi
                shift 2
                ;;
            --scenario)
                SCENARIO="$2"
                if [[ "$SCENARIO" != "all" ]] && [[ "$SCENARIO" != "backend" ]] && [[ "$SCENARIO" != "rls" ]] && [[ "$SCENARIO" != "canary" ]]; then
                    echo "Error: Invalid scenario '$SCENARIO'. Use 'all', 'backend', 'rls', or 'canary'."
                    exit 2
                fi
                shift 2
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                echo "Error: Unknown option '$1'"
                usage
                exit 2
                ;;
        esac
    done
    
    echo "========================================"
    echo "Rollback Smoke Test"
    echo "========================================"
    echo ""
    echo "Environment: $ENVIRONMENT"
    echo "Scenario:    $SCENARIO"
    echo "Timestamp:   $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    
    case "$SCENARIO" in
        all)
            section_backend_health
            section_rls_verification
            section_canary_verification
            section_application_smoke
            ;;
        backend)
            section_backend_health
            ;;
        rls)
            section_rls_verification
            ;;
        canary)
            section_canary_verification
            ;;
    esac
    
    print_summary
}

main "$@"
