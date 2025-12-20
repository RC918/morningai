#!/bin/bash
# =============================================================================
# Unit Tests for simple-mode-guard.sh
# =============================================================================
#
# Tests the Simple Mode Guard CI script, specifically:
#   - Detection of forbidden symbols in orchestrator directory
#   - Detection of forbidden symbols in api-backend directory
#   - Detection of forbidden symbols in common directory
#   - Exclusion of comments and documentation
#   - Multiple file handling
#   - Resource limits (MAX_FILES, MAX_LINES_PER_FILE)
#
# USAGE:
#   ./scripts/tests/simple-mode-guard.test.sh
#
# REQUIREMENTS:
#   - Bash 4.0+
#   - Git
#
# =============================================================================

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
GUARD_SCRIPT="$SCRIPT_DIR/ci/simple-mode-guard.sh"

# =============================================================================
# TEST FRAMEWORK
# =============================================================================

setup() {
    TEST_DIR=$(mktemp -d)
    echo "Test directory: $TEST_DIR"
    
    # Initialize git repo
    cd "$TEST_DIR"
    git init --quiet
    git config user.email "test@example.com"
    git config user.name "Test User"
    
    # Create directory structure matching the real repo
    mkdir -p "handoff/20250928/40_App/orchestrator"
    mkdir -p "handoff/20250928/40_App/api-backend/src"
    mkdir -p "common/config"
    
    # Create initial commit with clean files
    cat > "handoff/20250928/40_App/orchestrator/worker.py" << 'EOF'
#!/usr/bin/env python3
"""Worker module for orchestrator"""

def process_task(task_id: str) -> bool:
    """Process a task using LangGraph"""
    return True
EOF
    
    cat > "handoff/20250928/40_App/api-backend/src/routes.py" << 'EOF'
#!/usr/bin/env python3
"""API routes"""

def get_status():
    return {"status": "ok"}
EOF
    
    cat > "common/config/settings.py" << 'EOF'
#!/usr/bin/env python3
"""Settings module"""

DEBUG = False
EOF
    
    git add .
    git commit -m "Initial commit" --quiet
}

teardown() {
    if [[ -n "$TEST_DIR" ]] && [[ -d "$TEST_DIR" ]]; then
        rm -rf "$TEST_DIR"
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

assert_contains() {
    local haystack="$1"
    local needle="$2"
    local message="${3:-}"
    
    if [[ "$haystack" == *"$needle"* ]]; then
        return 0
    else
        echo -e "${RED}FAIL${NC}: Output does not contain '$needle' ${message:+- $message}"
        return 1
    fi
}

assert_not_contains() {
    local haystack="$1"
    local needle="$2"
    local message="${3:-}"
    
    if [[ "$haystack" != *"$needle"* ]]; then
        return 0
    else
        echo -e "${RED}FAIL${NC}: Output should not contain '$needle' ${message:+- $message}"
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

# =============================================================================
# TEST: Basic functionality
# =============================================================================

test_no_changes() {
    local output
    local exit_code=0
    
    cd "$TEST_DIR"
    local base_sha head_sha
    base_sha=$(git rev-parse HEAD)
    head_sha=$(git rev-parse HEAD)
    
    output=$("$GUARD_SCRIPT" "$base_sha" "$head_sha" 2>&1) || exit_code=$?
    
    assert_exit_code "0" "$exit_code" "No changes should pass"
    assert_contains "$output" "No Python files changed" "Should report no files changed"
}

test_clean_changes() {
    local output
    local exit_code=0
    
    cd "$TEST_DIR"
    local base_sha
    base_sha=$(git rev-parse HEAD)
    
    # Add clean code
    cat >> "handoff/20250928/40_App/orchestrator/worker.py" << 'EOF'

def new_function():
    """A new clean function"""
    return "langgraph"
EOF
    
    git add .
    git commit -m "Add clean function" --quiet
    
    local head_sha
    head_sha=$(git rev-parse HEAD)
    
    output=$("$GUARD_SCRIPT" "$base_sha" "$head_sha" 2>&1) || exit_code=$?
    
    assert_exit_code "0" "$exit_code" "Clean changes should pass"
    assert_contains "$output" "No violations found" "Should report no violations"
}

# =============================================================================
# TEST: Forbidden symbol detection
# =============================================================================

test_detect_record_simple_task_in_orchestrator() {
    local output
    local exit_code=0
    
    cd "$TEST_DIR"
    local base_sha
    base_sha=$(git rev-parse HEAD)
    
    # Add forbidden symbol
    cat >> "handoff/20250928/40_App/orchestrator/worker.py" << 'EOF'

def bad_function():
    record_simple_task("test")
EOF
    
    git add .
    git commit -m "Add forbidden symbol" --quiet
    
    local head_sha
    head_sha=$(git rev-parse HEAD)
    
    output=$("$GUARD_SCRIPT" "$base_sha" "$head_sha" 2>&1) || exit_code=$?
    
    assert_exit_code "1" "$exit_code" "Should detect violation"
    assert_contains "$output" "record_simple_task" "Should report the forbidden symbol"
    assert_contains "$output" "worker.py" "Should report the file"
}

test_detect_record_simple_task_in_api_backend() {
    local output
    local exit_code=0
    
    cd "$TEST_DIR"
    local base_sha
    base_sha=$(git rev-parse HEAD)
    
    # Add forbidden symbol in api-backend
    cat >> "handoff/20250928/40_App/api-backend/src/routes.py" << 'EOF'

def bad_route():
    return record_simple_task()
EOF
    
    git add .
    git commit -m "Add forbidden symbol in api-backend" --quiet
    
    local head_sha
    head_sha=$(git rev-parse HEAD)
    
    output=$("$GUARD_SCRIPT" "$base_sha" "$head_sha" 2>&1) || exit_code=$?
    
    assert_exit_code "1" "$exit_code" "Should detect violation in api-backend"
    assert_contains "$output" "record_simple_task" "Should report the forbidden symbol"
    assert_contains "$output" "routes.py" "Should report the file"
}

test_detect_record_simple_task_in_common() {
    local output
    local exit_code=0
    
    cd "$TEST_DIR"
    local base_sha
    base_sha=$(git rev-parse HEAD)
    
    # Add forbidden symbol in common
    cat >> "common/config/settings.py" << 'EOF'

SIMPLE_TASK_HANDLER = record_simple_task
EOF
    
    git add .
    git commit -m "Add forbidden symbol in common" --quiet
    
    local head_sha
    head_sha=$(git rev-parse HEAD)
    
    output=$("$GUARD_SCRIPT" "$base_sha" "$head_sha" 2>&1) || exit_code=$?
    
    assert_exit_code "1" "$exit_code" "Should detect violation in common"
    assert_contains "$output" "record_simple_task" "Should report the forbidden symbol"
    assert_contains "$output" "settings.py" "Should report the file"
}

test_detect_use_langgraph_percent() {
    local output
    local exit_code=0
    
    cd "$TEST_DIR"
    local base_sha
    base_sha=$(git rev-parse HEAD)
    
    # Add forbidden symbol
    cat >> "handoff/20250928/40_App/orchestrator/worker.py" << 'EOF'

USE_LANGGRAPH_PERCENT = 50
EOF
    
    git add .
    git commit -m "Add USE_LANGGRAPH_PERCENT" --quiet
    
    local head_sha
    head_sha=$(git rev-parse HEAD)
    
    output=$("$GUARD_SCRIPT" "$base_sha" "$head_sha" 2>&1) || exit_code=$?
    
    assert_exit_code "1" "$exit_code" "Should detect USE_LANGGRAPH_PERCENT"
    assert_contains "$output" "USE_LANGGRAPH_PERCENT" "Should report the forbidden symbol"
}

test_detect_simple_mode_string() {
    local output
    local exit_code=0
    
    cd "$TEST_DIR"
    local base_sha
    base_sha=$(git rev-parse HEAD)
    
    # Add forbidden string
    cat >> "handoff/20250928/40_App/orchestrator/worker.py" << 'EOF'

MODE = "Simple Mode"
EOF
    
    git add .
    git commit -m "Add Simple Mode string" --quiet
    
    local head_sha
    head_sha=$(git rev-parse HEAD)
    
    output=$("$GUARD_SCRIPT" "$base_sha" "$head_sha" 2>&1) || exit_code=$?
    
    assert_exit_code "1" "$exit_code" "Should detect Simple Mode string"
    assert_contains "$output" "Simple Mode" "Should report the forbidden string"
}

# =============================================================================
# TEST: Exclusions
# =============================================================================

test_exclude_note_comments() {
    local output
    local exit_code=0
    
    cd "$TEST_DIR"
    local base_sha
    base_sha=$(git rev-parse HEAD)
    
    # Add comment with NOTE (should be excluded)
    cat >> "handoff/20250928/40_App/orchestrator/worker.py" << 'EOF'

# NOTE: record_simple_task was removed in Issue #2651
EOF
    
    git add .
    git commit -m "Add NOTE comment" --quiet
    
    local head_sha
    head_sha=$(git rev-parse HEAD)
    
    output=$("$GUARD_SCRIPT" "$base_sha" "$head_sha" 2>&1) || exit_code=$?
    
    assert_exit_code "0" "$exit_code" "NOTE comments should be excluded"
    assert_contains "$output" "No violations found" "Should not flag NOTE comments"
}

test_exclude_removed_comments() {
    local output
    local exit_code=0
    
    cd "$TEST_DIR"
    local base_sha
    base_sha=$(git rev-parse HEAD)
    
    # Add comment mentioning removal
    cat >> "handoff/20250928/40_App/orchestrator/worker.py" << 'EOF'

# record_simple_task was removed after LangGraph rollout
EOF
    
    git add .
    git commit -m "Add removal comment" --quiet
    
    local head_sha
    head_sha=$(git rev-parse HEAD)
    
    output=$("$GUARD_SCRIPT" "$base_sha" "$head_sha" 2>&1) || exit_code=$?
    
    assert_exit_code "0" "$exit_code" "Removal comments should be excluded"
}

test_exclude_deprecated_comments() {
    local output
    local exit_code=0
    
    cd "$TEST_DIR"
    local base_sha
    base_sha=$(git rev-parse HEAD)
    
    # Add comment mentioning deprecation
    cat >> "handoff/20250928/40_App/orchestrator/worker.py" << 'EOF'

# record_simple_task is deprecated, use LangGraph instead
EOF
    
    git add .
    git commit -m "Add deprecation comment" --quiet
    
    local head_sha
    head_sha=$(git rev-parse HEAD)
    
    output=$("$GUARD_SCRIPT" "$base_sha" "$head_sha" 2>&1) || exit_code=$?
    
    assert_exit_code "0" "$exit_code" "Deprecation comments should be excluded"
}

# =============================================================================
# TEST: Multiple files
# =============================================================================

test_multiple_files_with_violations() {
    local output
    local exit_code=0
    
    cd "$TEST_DIR"
    local base_sha
    base_sha=$(git rev-parse HEAD)
    
    # Add violations in multiple files
    cat >> "handoff/20250928/40_App/orchestrator/worker.py" << 'EOF'

def bad1():
    record_simple_task("1")
EOF
    
    cat >> "handoff/20250928/40_App/api-backend/src/routes.py" << 'EOF'

def bad2():
    record_simple_task("2")
EOF
    
    git add .
    git commit -m "Add violations in multiple files" --quiet
    
    local head_sha
    head_sha=$(git rev-parse HEAD)
    
    output=$("$GUARD_SCRIPT" "$base_sha" "$head_sha" 2>&1) || exit_code=$?
    
    assert_exit_code "1" "$exit_code" "Should detect violations in multiple files"
    assert_contains "$output" "worker.py" "Should report first file"
    assert_contains "$output" "routes.py" "Should report second file"
}

# =============================================================================
# TEST: Edge cases
# =============================================================================

test_invalid_base_sha() {
    local output
    local exit_code=0
    
    cd "$TEST_DIR"
    
    output=$("$GUARD_SCRIPT" "invalid_sha" "HEAD" 2>&1) || exit_code=$?
    
    assert_exit_code "3" "$exit_code" "Invalid SHA should exit with code 3"
    assert_contains "$output" "Invalid base SHA" "Should report invalid SHA"
}

test_missing_arguments() {
    local output
    local exit_code=0
    
    cd "$TEST_DIR"
    
    output=$("$GUARD_SCRIPT" 2>&1) || exit_code=$?
    
    assert_exit_code "2" "$exit_code" "Missing args should exit with code 2"
    assert_contains "$output" "Missing required arguments" "Should report missing args"
}

test_files_outside_scan_dirs_ignored() {
    local output
    local exit_code=0
    
    cd "$TEST_DIR"
    local base_sha
    base_sha=$(git rev-parse HEAD)
    
    # Add forbidden symbol in a file outside scan directories
    mkdir -p "other"
    cat > "other/script.py" << 'EOF'
record_simple_task("should be ignored")
EOF
    
    git add .
    git commit -m "Add file outside scan dirs" --quiet
    
    local head_sha
    head_sha=$(git rev-parse HEAD)
    
    output=$("$GUARD_SCRIPT" "$base_sha" "$head_sha" 2>&1) || exit_code=$?
    
    assert_exit_code "0" "$exit_code" "Files outside scan dirs should be ignored"
    assert_not_contains "$output" "script.py" "Should not scan files outside scan dirs"
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    echo "=============================================="
    echo "Simple Mode Guard Tests"
    echo "=============================================="
    echo ""
    
    # Check script exists
    if [[ ! -x "$GUARD_SCRIPT" ]]; then
        echo -e "${RED}ERROR${NC}: Guard script not found or not executable: $GUARD_SCRIPT"
        exit 1
    fi
    
    echo "Testing: $GUARD_SCRIPT"
    echo ""
    
    echo "Basic functionality:"
    run_test "No changes" test_no_changes
    run_test "Clean changes" test_clean_changes
    echo ""
    
    echo "Forbidden symbol detection:"
    run_test "Detect record_simple_task in orchestrator" test_detect_record_simple_task_in_orchestrator
    run_test "Detect record_simple_task in api-backend" test_detect_record_simple_task_in_api_backend
    run_test "Detect record_simple_task in common" test_detect_record_simple_task_in_common
    run_test "Detect USE_LANGGRAPH_PERCENT" test_detect_use_langgraph_percent
    run_test "Detect Simple Mode string" test_detect_simple_mode_string
    echo ""
    
    echo "Exclusions:"
    run_test "Exclude NOTE comments" test_exclude_note_comments
    run_test "Exclude removed comments" test_exclude_removed_comments
    run_test "Exclude deprecated comments" test_exclude_deprecated_comments
    echo ""
    
    echo "Multiple files:"
    run_test "Multiple files with violations" test_multiple_files_with_violations
    echo ""
    
    echo "Edge cases:"
    run_test "Invalid base SHA" test_invalid_base_sha
    run_test "Missing arguments" test_missing_arguments
    run_test "Files outside scan dirs ignored" test_files_outside_scan_dirs_ignored
    echo ""
    
    echo "=============================================="
    echo "Results: $TESTS_PASSED/$TESTS_RUN passed"
    echo "=============================================="
    
    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo -e "${RED}$TESTS_FAILED test(s) failed${NC}"
        exit 1
    else
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    fi
}

main "$@"
