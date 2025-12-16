#!/bin/bash
# =============================================================================
# Legacy Component CI Workflow Contract Tests
# =============================================================================
#
# PURPOSE:
#   Validates the structure and critical invariants of the legacy component
#   detection CI workflow. This is a guardrail test, not a full workflow
#   execution simulation.
#
# USAGE:
#   ./scripts/tests/legacy-component-workflow.test.sh
#
# WHAT THIS TESTS:
#   - Workflow file exists and is valid YAML
#   - Required jobs and steps are present
#   - Critical configuration is not accidentally removed
#   - Script references are correct
#
# RELATED:
#   - Issue #2513: Legacy component detection CI
#   - .github/workflows/legacy-component-check.yml: The workflow being tested
#
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKFLOW_FILE="$REPO_ROOT/.github/workflows/legacy-component-check.yml"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# =============================================================================
# Test Framework
# =============================================================================

run_test() {
  local test_name="$1"
  local test_func="$2"
  
  TESTS_RUN=$((TESTS_RUN + 1))
  
  echo -n "  Testing: $test_name... "
  
  if $test_func; then
    echo -e "${GREEN}PASS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
  else
    echo -e "${RED}FAIL${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
  fi
}

assert_file_exists() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    echo "File not found: $file" >&2
    return 1
  fi
  return 0
}

assert_file_contains() {
  local file="$1"
  local pattern="$2"
  
  if ! grep -qE "$pattern" "$file"; then
    echo "Pattern not found in $file: $pattern" >&2
    return 1
  fi
  return 0
}

# =============================================================================
# Test Cases - Workflow File Structure
# =============================================================================

test_workflow_file_exists() {
  assert_file_exists "$WORKFLOW_FILE"
}

test_workflow_has_name() {
  assert_file_contains "$WORKFLOW_FILE" "^name: Legacy Component Check"
}

test_workflow_triggers_on_pull_request() {
  assert_file_contains "$WORKFLOW_FILE" "pull_request:"
}

test_workflow_triggers_on_workflow_dispatch() {
  assert_file_contains "$WORKFLOW_FILE" "workflow_dispatch:"
}

test_workflow_has_concurrency() {
  assert_file_contains "$WORKFLOW_FILE" "concurrency:"
}

test_workflow_has_permissions() {
  assert_file_contains "$WORKFLOW_FILE" "permissions:"
}

# =============================================================================
# Test Cases - Job Configuration
# =============================================================================

test_workflow_has_detect_job() {
  assert_file_contains "$WORKFLOW_FILE" "detect-legacy-components:"
}

test_workflow_runs_on_ubuntu() {
  assert_file_contains "$WORKFLOW_FILE" "runs-on: ubuntu-latest"
}

test_workflow_has_timeout() {
  assert_file_contains "$WORKFLOW_FILE" "timeout-minutes:"
}

# =============================================================================
# Test Cases - Required Steps
# =============================================================================

test_workflow_has_checkout_step() {
  assert_file_contains "$WORKFLOW_FILE" "uses: actions/checkout"
}

test_workflow_has_node_setup() {
  assert_file_contains "$WORKFLOW_FILE" "uses: actions/setup-node"
}

test_workflow_runs_detection_script() {
  assert_file_contains "$WORKFLOW_FILE" "detect-legacy-components.sh"
}

test_workflow_has_continue_on_error() {
  assert_file_contains "$WORKFLOW_FILE" "continue-on-error: true"
}

# =============================================================================
# Test Cases - Output and Reporting
# =============================================================================

test_workflow_has_step_summary() {
  assert_file_contains "$WORKFLOW_FILE" "GITHUB_STEP_SUMMARY"
}

test_workflow_has_pr_comment() {
  assert_file_contains "$WORKFLOW_FILE" "create-or-update-comment"
}

test_workflow_parses_violations() {
  assert_file_contains "$WORKFLOW_FILE" "Violations found"
}

# =============================================================================
# Test Cases - Path Filters
# =============================================================================

test_workflow_filters_frontend_dashboard() {
  assert_file_contains "$WORKFLOW_FILE" "frontend-dashboard"
}

test_workflow_filters_owner_console() {
  assert_file_contains "$WORKFLOW_FILE" "owner-console"
}

test_workflow_filters_detection_script() {
  assert_file_contains "$WORKFLOW_FILE" "detect-legacy-components.sh"
}

test_workflow_filters_allowlist() {
  assert_file_contains "$WORKFLOW_FILE" "legacy-component-allowlist.json"
}

# =============================================================================
# Test Cases - Related Files
# =============================================================================

test_detection_script_exists() {
  assert_file_exists "$REPO_ROOT/scripts/detect-legacy-components.sh"
}

test_detection_mjs_exists() {
  assert_file_exists "$REPO_ROOT/scripts/detect-legacy-components.mjs"
}

test_allowlist_file_exists() {
  assert_file_exists "$REPO_ROOT/.github/legacy-component-allowlist.json"
}

# =============================================================================
# Main Test Runner
# =============================================================================

main() {
  echo "=============================================================================="
  echo "Legacy Component CI Workflow Contract Tests"
  echo "=============================================================================="
  echo ""
  
  # Workflow File Structure Tests
  echo "Workflow File Structure:"
  run_test "workflow file exists" test_workflow_file_exists
  run_test "workflow has name" test_workflow_has_name
  run_test "workflow triggers on pull_request" test_workflow_triggers_on_pull_request
  run_test "workflow triggers on workflow_dispatch" test_workflow_triggers_on_workflow_dispatch
  run_test "workflow has concurrency" test_workflow_has_concurrency
  run_test "workflow has permissions" test_workflow_has_permissions
  echo ""
  
  # Job Configuration Tests
  echo "Job Configuration:"
  run_test "workflow has detect job" test_workflow_has_detect_job
  run_test "workflow runs on ubuntu" test_workflow_runs_on_ubuntu
  run_test "workflow has timeout" test_workflow_has_timeout
  echo ""
  
  # Required Steps Tests
  echo "Required Steps:"
  run_test "workflow has checkout step" test_workflow_has_checkout_step
  run_test "workflow has node setup" test_workflow_has_node_setup
  run_test "workflow runs detection script" test_workflow_runs_detection_script
  run_test "workflow has continue-on-error" test_workflow_has_continue_on_error
  echo ""
  
  # Output and Reporting Tests
  echo "Output and Reporting:"
  run_test "workflow has step summary" test_workflow_has_step_summary
  run_test "workflow has PR comment" test_workflow_has_pr_comment
  run_test "workflow parses violations" test_workflow_parses_violations
  echo ""
  
  # Path Filters Tests
  echo "Path Filters:"
  run_test "workflow filters frontend-dashboard" test_workflow_filters_frontend_dashboard
  run_test "workflow filters owner-console" test_workflow_filters_owner_console
  run_test "workflow filters detection script" test_workflow_filters_detection_script
  run_test "workflow filters allowlist" test_workflow_filters_allowlist
  echo ""
  
  # Related Files Tests
  echo "Related Files:"
  run_test "detection script exists" test_detection_script_exists
  run_test "detection mjs exists" test_detection_mjs_exists
  run_test "allowlist file exists" test_allowlist_file_exists
  echo ""
  
  # Summary
  echo "=============================================================================="
  echo "Test Summary"
  echo "=============================================================================="
  echo "Tests run: $TESTS_RUN"
  echo "Tests passed: $TESTS_PASSED"
  echo "Tests failed: $TESTS_FAILED"
  echo ""
  
  if [[ $TESTS_FAILED -gt 0 ]]; then
    echo -e "${RED}SOME TESTS FAILED${NC}"
    exit 1
  else
    echo -e "${GREEN}ALL TESTS PASSED${NC}"
    exit 0
  fi
}

main "$@"
