#!/bin/bash
# ============================================================================
# Unit Tests for sync-react-versions.sh
# ============================================================================
#
# Tests the React version synchronization script, specifically:
#   - Version validation
#   - Check mode (--check)
#   - Dry-run mode (--dry-run)
#   - Version extraction from pnpm overrides
#   - Workspace version detection
#
# USAGE:
#   ./scripts/tests/sync-react-versions.test.sh
#
# REQUIREMENTS:
#   - Bash 4.0+
#   - Node.js
#
# ============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Temporary directory for test fixtures
TEST_DIR=""

# Script under test
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SYNC_SCRIPT="$SCRIPT_DIR/sync-react-versions.sh"

# ============================================================================
# TEST FRAMEWORK
# ============================================================================

setup() {
  TEST_DIR=$(mktemp -d)
  echo "Test directory: $TEST_DIR"
  
  # Create minimal monorepo structure
  mkdir -p "$TEST_DIR/handoff/20250928/40_App/frontend-dashboard"
  mkdir -p "$TEST_DIR/handoff/20250928/40_App/owner-console"
  mkdir -p "$TEST_DIR/packages/shared-ui"
  
  # Create root package.json with pnpm overrides
  cat > "$TEST_DIR/package.json" << 'EOF'
{
  "name": "test-monorepo",
  "pnpm": {
    "overrides": {
      "react": "^19.1.0",
      "react-dom": "^19.1.0",
      "@types/react": "^19.1.2",
      "@types/react-dom": "^19.1.2"
    }
  }
}
EOF
}

teardown() {
  if [[ -n "$TEST_DIR" ]] && [[ -d "$TEST_DIR" ]]; then
    rm -rf "$TEST_DIR"
  fi
}

assert_equals() {
  local expected="$1"
  local actual="$2"
  local message="${3:-}"
  
  if [[ "$expected" == "$actual" ]]; then
    return 0
  else
    echo -e "${RED}FAIL${NC}: Expected '$expected', got '$actual' ${message:+- $message}"
    return 1
  fi
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  local message="${3:-}"
  
  if [[ "$haystack" == *"$needle"* ]]; then
    return 0
  else
    echo -e "${RED}FAIL${NC}: '$haystack' does not contain '$needle' ${message:+- $message}"
    return 1
  fi
}

assert_exit_code() {
  local expected="$1"
  local actual="$2"
  local message="${3:-}"
  
  if [[ "$expected" == "$actual" ]]; then
    return 0
  else
    echo -e "${RED}FAIL${NC}: Expected exit code $expected, got $actual ${message:+- $message}"
    return 1
  fi
}

run_test() {
  local test_name="$1"
  local test_func="$2"
  
  TESTS_RUN=$((TESTS_RUN + 1))
  echo -n "  $test_name... "
  
  # Setup fresh test environment
  setup
  
  if $test_func; then
    echo -e "${GREEN}PASS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
  else
    TESTS_FAILED=$((TESTS_FAILED + 1))
  fi
  
  # Cleanup
  teardown
}

# ============================================================================
# TEST: Help and usage
# ============================================================================

test_help_flag() {
  local output
  output=$("$SYNC_SCRIPT" --help 2>&1) || true
  
  assert_contains "$output" "Usage:" "Help should show usage"
}

test_unknown_option() {
  local output
  local exit_code=0
  output=$("$SYNC_SCRIPT" --unknown-option 2>&1) || exit_code=$?
  
  assert_exit_code "1" "$exit_code" "Unknown option should exit with 1"
}

# ============================================================================
# TEST: Version validation
# ============================================================================

test_valid_version_format() {
  # Test that valid semver is accepted
  local output
  local exit_code=0
  
  cd "$TEST_DIR"
  
  # Create aligned workspace
  cat > "$TEST_DIR/handoff/20250928/40_App/frontend-dashboard/package.json" << 'EOF'
{
  "dependencies": {
    "react": "^19.1.0",
    "react-dom": "^19.1.0"
  },
  "devDependencies": {
    "@types/react": "^19.1.2",
    "@types/react-dom": "^19.1.2"
  }
}
EOF
  
  cat > "$TEST_DIR/handoff/20250928/40_App/owner-console/package.json" << 'EOF'
{
  "dependencies": {
    "react": "^19.1.0",
    "react-dom": "^19.1.0"
  },
  "devDependencies": {
    "@types/react": "^19.1.2",
    "@types/react-dom": "^19.1.2"
  }
}
EOF
  
  output=$("$SYNC_SCRIPT" --check 2>&1) || exit_code=$?
  
  assert_exit_code "0" "$exit_code" "Aligned versions should pass check"
}

test_invalid_version_format() {
  local output
  local exit_code=0
  
  cd "$TEST_DIR"
  output=$("$SYNC_SCRIPT" --version "invalid" 2>&1) || exit_code=$?
  
  assert_exit_code "1" "$exit_code" "Invalid version should exit with 1"
}

# ============================================================================
# TEST: Check mode
# ============================================================================

test_check_mode_aligned() {
  local output
  local exit_code=0
  
  cd "$TEST_DIR"
  
  # Create aligned workspaces
  cat > "$TEST_DIR/handoff/20250928/40_App/frontend-dashboard/package.json" << 'EOF'
{
  "dependencies": {
    "react": "^19.1.0",
    "react-dom": "^19.1.0"
  },
  "devDependencies": {
    "@types/react": "^19.1.2",
    "@types/react-dom": "^19.1.2"
  }
}
EOF
  
  cat > "$TEST_DIR/handoff/20250928/40_App/owner-console/package.json" << 'EOF'
{
  "dependencies": {
    "react": "^19.1.0",
    "react-dom": "^19.1.0"
  },
  "devDependencies": {
    "@types/react": "^19.1.2",
    "@types/react-dom": "^19.1.2"
  }
}
EOF
  
  output=$("$SYNC_SCRIPT" --check 2>&1) || exit_code=$?
  
  assert_exit_code "0" "$exit_code" "Aligned versions should pass"
  assert_contains "$output" "aligned" "Output should mention aligned"
}

test_check_mode_misaligned() {
  local output
  local exit_code=0
  
  cd "$TEST_DIR"
  
  # Create misaligned workspace
  cat > "$TEST_DIR/handoff/20250928/40_App/frontend-dashboard/package.json" << 'EOF'
{
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  }
}
EOF
  
  cat > "$TEST_DIR/handoff/20250928/40_App/owner-console/package.json" << 'EOF'
{
  "dependencies": {
    "react": "^19.1.0",
    "react-dom": "^19.1.0"
  }
}
EOF
  
  output=$("$SYNC_SCRIPT" --check 2>&1) || exit_code=$?
  
  assert_exit_code "1" "$exit_code" "Misaligned versions should fail"
  assert_contains "$output" "misaligned" "Output should mention misaligned"
}

# ============================================================================
# TEST: Dry-run mode
# ============================================================================

test_dry_run_no_changes() {
  local output
  local exit_code=0
  
  cd "$TEST_DIR"
  
  # Create misaligned workspace
  cat > "$TEST_DIR/handoff/20250928/40_App/frontend-dashboard/package.json" << 'EOF'
{
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  }
}
EOF
  
  cat > "$TEST_DIR/handoff/20250928/40_App/owner-console/package.json" << 'EOF'
{
  "dependencies": {
    "react": "^19.1.0",
    "react-dom": "^19.1.0"
  }
}
EOF
  
  # Save original content
  local original_content
  original_content=$(cat "$TEST_DIR/handoff/20250928/40_App/frontend-dashboard/package.json")
  
  output=$("$SYNC_SCRIPT" --dry-run 2>&1) || exit_code=$?
  
  # Verify file was not modified
  local new_content
  new_content=$(cat "$TEST_DIR/handoff/20250928/40_App/frontend-dashboard/package.json")
  
  assert_equals "$original_content" "$new_content" "Dry-run should not modify files"
  assert_contains "$output" "DRY-RUN" "Output should mention DRY-RUN"
}

# ============================================================================
# TEST: Sync mode
# ============================================================================

test_sync_updates_versions() {
  local output
  local exit_code=0
  
  cd "$TEST_DIR"
  
  # Create misaligned workspace
  cat > "$TEST_DIR/handoff/20250928/40_App/frontend-dashboard/package.json" << 'EOF'
{
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  }
}
EOF
  
  cat > "$TEST_DIR/handoff/20250928/40_App/owner-console/package.json" << 'EOF'
{
  "dependencies": {
    "react": "^19.1.0",
    "react-dom": "^19.1.0"
  }
}
EOF
  
  output=$("$SYNC_SCRIPT" 2>&1) || exit_code=$?
  
  # Verify file was updated
  local new_content
  new_content=$(cat "$TEST_DIR/handoff/20250928/40_App/frontend-dashboard/package.json")
  
  assert_contains "$new_content" "19.1.0" "File should be updated to 19.1.0"
  assert_contains "$output" "Updated" "Output should mention Updated"
}

# ============================================================================
# TEST: Version extraction
# ============================================================================

test_version_extraction_from_overrides() {
  local output
  local exit_code=0
  
  cd "$TEST_DIR"
  
  # Create aligned workspace
  cat > "$TEST_DIR/handoff/20250928/40_App/frontend-dashboard/package.json" << 'EOF'
{
  "dependencies": {
    "react": "^19.1.0",
    "react-dom": "^19.1.0"
  }
}
EOF
  
  cat > "$TEST_DIR/handoff/20250928/40_App/owner-console/package.json" << 'EOF'
{
  "dependencies": {
    "react": "^19.1.0",
    "react-dom": "^19.1.0"
  }
}
EOF
  
  output=$("$SYNC_SCRIPT" --check --verbose 2>&1) || exit_code=$?
  
  assert_contains "$output" "19.1.0" "Should extract version from overrides"
}

# ============================================================================
# TEST: Missing workspace handling
# ============================================================================

test_missing_workspace_warning() {
  local output
  local exit_code=0
  
  cd "$TEST_DIR"
  
  # Remove one workspace
  rm -rf "$TEST_DIR/handoff/20250928/40_App/frontend-dashboard"
  
  # Create remaining workspace
  cat > "$TEST_DIR/handoff/20250928/40_App/owner-console/package.json" << 'EOF'
{
  "dependencies": {
    "react": "^19.1.0",
    "react-dom": "^19.1.0"
  }
}
EOF
  
  output=$("$SYNC_SCRIPT" --check 2>&1) || exit_code=$?
  
  assert_contains "$output" "not found" "Should warn about missing workspace"
}

# ============================================================================
# MAIN
# ============================================================================

main() {
  echo "=============================================================================="
  echo "React Version Sync Script Unit Tests"
  echo "=============================================================================="
  echo ""
  
  # Check if script exists
  if [[ ! -f "$SYNC_SCRIPT" ]]; then
    echo -e "${RED}ERROR${NC}: Script not found at $SYNC_SCRIPT"
    exit 1
  fi
  
  echo "Testing: $SYNC_SCRIPT"
  echo ""
  
  # Help and usage tests
  echo "Help and Usage Tests:"
  run_test "Help flag shows usage" test_help_flag
  run_test "Unknown option exits with error" test_unknown_option
  echo ""
  
  # Version validation tests
  echo "Version Validation Tests:"
  run_test "Valid version format accepted" test_valid_version_format
  run_test "Invalid version format rejected" test_invalid_version_format
  echo ""
  
  # Check mode tests
  echo "Check Mode Tests:"
  run_test "Check mode passes for aligned versions" test_check_mode_aligned
  run_test "Check mode fails for misaligned versions" test_check_mode_misaligned
  echo ""
  
  # Dry-run mode tests
  echo "Dry-run Mode Tests:"
  run_test "Dry-run does not modify files" test_dry_run_no_changes
  echo ""
  
  # Sync mode tests
  echo "Sync Mode Tests:"
  run_test "Sync updates misaligned versions" test_sync_updates_versions
  echo ""
  
  # Version extraction tests
  echo "Version Extraction Tests:"
  run_test "Extracts version from pnpm overrides" test_version_extraction_from_overrides
  echo ""
  
  # Missing workspace tests
  echo "Missing Workspace Tests:"
  run_test "Warns about missing workspaces" test_missing_workspace_warning
  echo ""
  
  # Summary
  echo "=============================================================================="
  echo "Test Summary"
  echo "=============================================================================="
  echo "Total:  $TESTS_RUN"
  echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
  echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
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
