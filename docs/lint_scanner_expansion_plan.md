# Lint Scanner Expansion Plan: Orchestrator & Agents

**Task 9: 規劃將掃描器擴展到 orchestrator/agents**

**Date**: 2025-11-09  
**Status**: Planning Phase  
**Owner**: Engineering Team

---

## 📋 Executive Summary

This document outlines the plan to expand the deprecated import scanner (implemented in Task 7 for api-backend) to cover orchestrator and all agents (dev_agent, faq_agent, ops_agent). The scanner will enforce deprecation policies across the entire codebase by detecting deprecated module imports in production code during CI.

**Key Goals**:
- Extend lint checks to orchestrator and all agents
- Maintain consistency with existing api-backend scanner
- Integrate seamlessly with existing CI workflows
- Minimize code duplication through shared helpers

---

## 🎯 Goals and Scope

### In Scope
1. **Orchestrator**: Scan all production Python files in `orchestrator/` (excluding tests)
2. **Agents**: Scan all production Python files in:
   - `agents/dev_agent/`
   - `agents/faq_agent/`
   - `agents/ops_agent/`
3. **CI Integration**: Ensure lint tests run automatically on PRs affecting these components
4. **Shared Infrastructure**: Extract common scanner logic to avoid duplication

### Out of Scope
- Traditional linters (flake8, ruff, mypy) - these are separate from pytest-based lint checks
- Scanning test files - tests are excluded to allow backward compatibility testing
- Relative import detection - consistent with Task 7 policy
- Performance optimization (scanning only changed files) - defer to future task

---

## 🏗️ Architecture

### Current State (Task 7)

**api-backend Scanner**:
- Location: `handoff/20250928/40_App/api-backend/tests/lint/test_no_deprecated_imports.py`
- Scans: `src/**/*.py` in api-backend
- Detects: Direct and aliased imports of deprecated modules
- Runs in: `backend.yml` CI workflow (test job)
- Status: ✅ Implemented and verified

**Deprecated Modules**:
```python
DEPRECATED_MODULES = [
    "utils.preauth_token",
    "src.utils.preauth_token",
]
```

### Target State (Task 9)

**Shared Scanner Infrastructure**:
- Extract AST scanning logic to `common/tests/lint_helpers.py`
- Centralize deprecated module lists in `common/tests/test_config.py`
- Allow per-domain overrides and extensions

**Domain-Specific Lint Tests**:
1. **Orchestrator**: `handoff/20250928/40_App/orchestrator/tests/lint/test_no_deprecated_imports.py`
2. **Dev Agent**: `agents/dev_agent/tests/lint/test_no_deprecated_imports.py`
3. **FAQ Agent**: `agents/faq_agent/tests/lint/test_no_deprecated_imports.py`
4. **Ops Agent**: `agents/ops_agent/tests/lint/test_no_deprecated_imports.py`

---

## 📂 Test Placement Strategy

### Orchestrator
**Location**: `handoff/20250928/40_App/orchestrator/tests/lint/`

**Rationale**:
- Aligns with existing test structure (`orchestrator/tests/`)
- CI workflow `test-apps.yml` already runs `pytest tests/` from orchestrator directory
- No workflow changes required

**Scan Pattern**: `orchestrator/**/*.py` (excluding `tests/**`)

### Agents

**Location**: `agents/<agent_name>/tests/lint/`

**Rationale**:
- Each agent has its own test directory structure
- CI workflow `test-agents.yml` runs `pytest tests/` per agent
- Allows agent-specific deprecated module lists if needed
- No workflow changes required

**Scan Patterns**:
- Dev Agent: `agents/dev_agent/**/*.py` (excluding `tests/**`)
- FAQ Agent: `agents/faq_agent/**/*.py` (excluding `tests/**`)
- Ops Agent: `agents/ops_agent/**/*.py` (excluding `tests/**`)

---

## 🔄 CI Integration

### Existing CI Workflows

#### 1. test-apps.yml (Orchestrator)
```yaml
- name: Run Orchestrator tests
  working-directory: handoff/20250928/40_App/orchestrator
  run: pytest tests/ -v --tb=short --disable-warnings
```
✅ **No changes required** - pytest will automatically discover `tests/lint/` tests

#### 2. test-agents.yml (All Agents)
```yaml
# FAQ Agent
- name: Run FAQ Agent tests
  working-directory: agents/faq_agent
  run: pytest tests/ -v --tb=short --disable-warnings

# Ops Agent
- name: Run Ops Agent tests
  working-directory: agents/ops_agent
  run: pytest tests/ -v --tb=short --disable-warnings

# Dev Agent
- name: Run Dev Agent tests
  working-directory: agents/dev_agent
  run: pytest tests/ -v --tb=short --disable-warnings
```
✅ **No changes required** - pytest will automatically discover `tests/lint/` tests

### Verification Strategy
After implementation, verify that:
1. Lint tests are collected by pytest (check "collected N items" in CI logs)
2. Lint tests execute and pass/fail appropriately
3. CI fails when deprecated imports are detected

---

## 🛠️ Shared Infrastructure Design

### 1. Common Scanner Helper (`common/tests/lint_helpers.py`)

**Purpose**: Centralize AST scanning logic to avoid duplication

**Exported Functions**:
```python
def check_file_for_deprecated_imports(
    file_path: Path,
    deprecated_modules: List[str]
) -> List[Tuple[int, str, str]]:
    """
    Check a Python file for deprecated module imports.
    
    Detects both direct and aliased imports:
    - import utils.preauth_token
    - import utils.preauth_token as preauth  (aliased)
    - from utils.preauth_token import generate_preauth_token
    - from utils.preauth_token import generate_preauth_token as gen_token
    
    Args:
        file_path: Path to Python file to scan
        deprecated_modules: List of deprecated module FQNs
    
    Returns:
        List of (line_number, import_statement, deprecated_module) tuples
    """

def find_python_files(
    root: Path,
    include_pattern: str = "**/*.py",
    exclude_patterns: List[str] = None
) -> List[Path]:
    """
    Find all Python files matching the pattern.
    
    Args:
        root: Root directory to search from
        include_pattern: Glob pattern for files to include
        exclude_patterns: List of glob patterns to exclude (e.g., ["tests/**"])
    
    Returns:
        List of matching Python file paths
    """
```

**Key Features**:
- Reuses existing AST parsing logic from Task 7
- Detects aliased imports, star imports, multi-line imports
- Skips relative imports (node.level > 0)
- Handles syntax errors gracefully

### 2. Common Test Configuration (`common/tests/test_config.py`)

**Purpose**: Centralize deprecated module lists with domain-specific overrides

**Structure**:
```python
# Base deprecated modules (shared across all domains)
BASE_DEPRECATED_MODULES = [
    "utils.preauth_token",
    "src.utils.preauth_token",
]

# Domain-specific deprecated modules
API_BACKEND_DEPRECATED_MODULES = BASE_DEPRECATED_MODULES + [
    # Add api-backend specific deprecated modules here
]

ORCHESTRATOR_DEPRECATED_MODULES = BASE_DEPRECATED_MODULES + [
    # Add orchestrator-specific deprecated modules here
]

AGENTS_DEPRECATED_MODULES = BASE_DEPRECATED_MODULES + [
    # Add agent-specific deprecated modules here
]

# Per-agent overrides (if needed)
DEV_AGENT_DEPRECATED_MODULES = AGENTS_DEPRECATED_MODULES + []
FAQ_AGENT_DEPRECATED_MODULES = AGENTS_DEPRECATED_MODULES + []
OPS_AGENT_DEPRECATED_MODULES = AGENTS_DEPRECATED_MODULES + []
```

### 3. Domain-Specific Test Files

Each domain will have a thin test file that:
1. Imports shared scanner helper
2. Specifies domain-specific configuration (root path, scan pattern, deprecated modules)
3. Implements test function that calls shared scanner

**Example** (`orchestrator/tests/lint/test_no_deprecated_imports.py`):
```python
"""Test to ensure deprecated modules are not imported in orchestrator code."""

from pathlib import Path
from common.tests.lint_helpers import check_file_for_deprecated_imports, find_python_files
from common.tests.test_config import ORCHESTRATOR_DEPRECATED_MODULES

def get_orchestrator_root() -> Path:
    """Get the orchestrator root directory."""
    return Path(__file__).parent.parent.parent

def test_no_deprecated_imports_in_orchestrator():
    """Test that deprecated modules are not imported in orchestrator code."""
    root = get_orchestrator_root()
    python_files = find_python_files(
        root,
        include_pattern="**/*.py",
        exclude_patterns=["tests/**"]
    )
    
    all_violations = []
    for file_path in python_files:
        violations = check_file_for_deprecated_imports(
            file_path,
            ORCHESTRATOR_DEPRECATED_MODULES
        )
        if violations:
            all_violations.append((file_path, violations))
    
    if all_violations:
        # Format error message (reuse from Task 7)
        raise AssertionError(format_violations_message(all_violations))
```

---

## 📋 Deprecated Modules Inventory

### Current Status

**Scan Results** (2025-11-09):
```bash
# Check for deprecated module usage in orchestrator/agents
grep -r "utils.preauth_token\|src.utils.preauth_token" orchestrator/ agents/ --include="*.py"
```

**Result**: ✅ No deprecated module imports found in orchestrator or agents

**Conclusion**: No immediate remediation required. Scanner will prevent future violations.

### Future Deprecated Modules

As new modules are deprecated, add them to `BASE_DEPRECATED_MODULES` or domain-specific lists in `common/tests/test_config.py`.

---

## 🚀 Rollout Plan (Phased Implementation)

### Phase 1: Shared Infrastructure
**Goal**: Create reusable scanner components

**Tasks**:
1. Create `common/tests/` directory structure
2. Extract AST scanner logic to `common/tests/lint_helpers.py`
3. Create `common/tests/test_config.py` with deprecated module lists
4. Add unit tests for shared helpers
5. Update api-backend scanner to use shared helpers (refactor)

**Deliverable**: PR with shared infrastructure and refactored api-backend scanner

**Estimated Effort**: 2-3 hours

---

### Phase 2: Orchestrator Scanner
**Goal**: Add lint checks to orchestrator

**Tasks**:
1. Create `handoff/20250928/40_App/orchestrator/tests/lint/` directory
2. Implement `test_no_deprecated_imports.py` using shared helpers
3. Test locally: `cd handoff/20250928/40_App/orchestrator && pytest tests/lint/ -v`
4. Verify CI integration in test-apps.yml
5. Document orchestrator-specific scan patterns

**Deliverable**: PR with orchestrator lint scanner

**Estimated Effort**: 1-2 hours

---

### Phase 3: Dev Agent Scanner
**Goal**: Add lint checks to dev_agent

**Tasks**:
1. Create `agents/dev_agent/tests/lint/` directory
2. Implement `test_no_deprecated_imports.py` using shared helpers
3. Test locally: `cd agents/dev_agent && pytest tests/lint/ -v`
4. Verify CI integration in test-agents.yml
5. Document dev_agent-specific scan patterns

**Deliverable**: PR with dev_agent lint scanner

**Estimated Effort**: 1-2 hours

---

### Phase 4: FAQ & Ops Agent Scanners
**Goal**: Add lint checks to faq_agent and ops_agent

**Tasks**:
1. Create `agents/faq_agent/tests/lint/` directory
2. Implement `test_no_deprecated_imports.py` for faq_agent
3. Create `agents/ops_agent/tests/lint/` directory
4. Implement `test_no_deprecated_imports.py` for ops_agent
5. Test locally for both agents
6. Verify CI integration in test-agents.yml
7. Document agent-specific scan patterns

**Deliverable**: PR with faq_agent and ops_agent lint scanners

**Estimated Effort**: 2-3 hours

---

### Phase 5: Consolidation & Documentation
**Goal**: Clean up and document the complete system

**Tasks**:
1. Remove any remaining code duplication
2. Add comprehensive documentation to shared helpers
3. Update main README with lint scanner overview
4. Create troubleshooting guide for common issues
5. Document how to add new deprecated modules
6. Document how to add new domains (future agents)

**Deliverable**: PR with documentation and final cleanup

**Estimated Effort**: 1-2 hours

---

## 🔍 Edge Cases and Policies

### 1. Relative Imports
**Policy**: Skip relative imports (node.level > 0)

**Rationale**: Relative imports within a package are acceptable; we only care about absolute imports of deprecated modules.

**Implementation**: Already handled in Task 7 scanner logic

### 2. Star Imports
**Policy**: Detect and flag star imports from deprecated modules

**Example**: `from utils.preauth_token import *`

**Implementation**: Already handled in Task 7 scanner logic

### 3. Aliased Imports
**Policy**: Detect all forms of aliased imports

**Examples**:
- `import utils.preauth_token as preauth`
- `from utils.preauth_token import generate_preauth_token as gen_token`

**Implementation**: Already handled in Task 7 scanner logic (verified with 15 test cases)

### 4. Multi-line Imports
**Policy**: Detect imports spanning multiple lines

**Example**:
```python
from utils.preauth_token import (
    generate_preauth_token as gen
)
```

**Implementation**: Already handled in Task 7 scanner logic

### 5. False Positives
**Policy**: Strict FQN matching to avoid false positives

**Example**: `utils.preauth_token_tools` should NOT trigger (similar name but not deprecated)

**Implementation**: Use exact equality or endswith checks with proper delimiters

### 6. Allowlists
**Policy**: Avoid allowlists unless absolutely necessary

**Rationale**: Allowlists create technical debt and bypass deprecation enforcement

**Alternative**: If a file legitimately needs to import deprecated modules (e.g., migration scripts), move it outside production code paths or add a clear exception with justification

### 7. Test Files
**Policy**: Exclude all test files from scanning

**Rationale**: Tests need to verify backward compatibility and migration paths

**Implementation**: Use exclude_patterns=["tests/**"] in find_python_files()

---

## ⚠️ Risks and Mitigations

### Risk 1: Root Path Discovery Differences
**Description**: Different domains have different directory structures and root paths

**Impact**: Scanner might fail to find files or scan wrong directories

**Mitigation**:
- Define explicit root path discovery per domain
- Test glob patterns locally before committing
- Add assertions to verify expected file counts

**Example**:
```python
# Orchestrator root: handoff/20250928/40_App/orchestrator/
# Agent root: agents/dev_agent/
```

### Risk 2: CI Job Discovery Failures
**Description**: pytest might not discover new tests/lint/ directories

**Impact**: Lint tests won't run in CI, defeating the purpose

**Mitigation**:
- Verify CI logs show "collected N items" includes lint tests
- Add explicit test to CI that checks lint tests are discovered
- Monitor first PR for each domain to confirm CI integration

### Risk 3: False Positives
**Description**: Scanner might flag legitimate imports as deprecated

**Impact**: Blocks valid PRs, creates frustration

**Mitigation**:
- Use strict FQN matching (exact equality or proper endswith checks)
- Add comprehensive test cases for edge cases
- Document how to report false positives
- Keep allowlist as escape hatch (use sparingly)

### Risk 4: Performance Impact
**Description**: Scanning many files might slow down CI

**Impact**: Longer CI times, slower feedback loop

**Mitigation**:
- Current api-backend scanner is fast (< 1 second for 1131 tests)
- Orchestrator + agents have ~133 Python files (manageable)
- Defer optimization (scanning only changed files) to future task
- Monitor CI times and optimize if needed

### Risk 5: Maintenance Burden
**Description**: Multiple lint test files to maintain across domains

**Impact**: Changes to scanner logic require updates in multiple places

**Mitigation**:
- Centralize logic in shared helpers (single source of truth)
- Domain-specific tests are thin wrappers (minimal duplication)
- Document update process clearly
- Consider future consolidation if maintenance becomes burdensome

---

## 📚 Documentation Requirements

### 1. Shared Helper Documentation
- Add docstrings to all functions in `common/tests/lint_helpers.py`
- Document AST node types and detection logic
- Provide examples of detected patterns

### 2. Configuration Documentation
- Document deprecated module list structure in `common/tests/test_config.py`
- Explain how to add new deprecated modules
- Explain domain-specific overrides

### 3. Domain-Specific Documentation
- Add docstrings to each domain's test file
- Document scan patterns and exclusions
- Provide local testing instructions

### 4. CI Integration Documentation
- Document which workflows run which lint tests
- Explain how pytest discovers tests/lint/ directories
- Provide troubleshooting guide for CI failures

### 5. Migration Guide
- Document how to fix deprecated import violations
- Provide examples of correct replacements
- Link to replacement module documentation

---

## ✅ Success Criteria

### Phase 1 (Shared Infrastructure)
- [ ] `common/tests/lint_helpers.py` created with AST scanner logic
- [ ] `common/tests/test_config.py` created with deprecated module lists
- [ ] api-backend scanner refactored to use shared helpers
- [ ] All existing api-backend lint tests pass
- [ ] Unit tests for shared helpers pass

### Phase 2 (Orchestrator)
- [ ] `orchestrator/tests/lint/test_no_deprecated_imports.py` created
- [ ] Orchestrator lint tests run locally and pass
- [ ] test-apps.yml CI collects and runs orchestrator lint tests
- [ ] CI logs show lint tests in "collected N items"

### Phase 3 (Dev Agent)
- [ ] `agents/dev_agent/tests/lint/test_no_deprecated_imports.py` created
- [ ] Dev agent lint tests run locally and pass
- [ ] test-agents.yml CI collects and runs dev agent lint tests
- [ ] CI logs show lint tests in "collected N items"

### Phase 4 (FAQ & Ops Agents)
- [ ] `agents/faq_agent/tests/lint/test_no_deprecated_imports.py` created
- [ ] `agents/ops_agent/tests/lint/test_no_deprecated_imports.py` created
- [ ] FAQ and ops agent lint tests run locally and pass
- [ ] test-agents.yml CI collects and runs both agent lint tests
- [ ] CI logs show lint tests in "collected N items"

### Phase 5 (Consolidation)
- [ ] No code duplication across domain-specific tests
- [ ] Comprehensive documentation completed
- [ ] Troubleshooting guide created
- [ ] All lint tests passing in CI

---

## 🔗 References

- **Task 7 Implementation**: PR #1234 - https://github.com/RC918/morningai/pull/1234
- **Task 8 Verification**: backend.yml runs lint on all backend PRs (verified 2025-11-09)
- **api-backend Scanner**: `handoff/20250928/40_App/api-backend/tests/lint/test_no_deprecated_imports.py`
- **backend.yml Workflow**: `.github/workflows/backend.yml`
- **test-apps.yml Workflow**: `.github/workflows/test-apps.yml`
- **test-agents.yml Workflow**: `.github/workflows/test-agents.yml`

---

## 📝 Notes

### Design Decisions

1. **Separate test files per domain** (vs. single centralized test)
   - Rationale: Aligns with existing CI structure, no workflow changes required
   - Trade-off: More files to maintain, but shared helpers minimize duplication

2. **Shared helper approach** (vs. copy-paste)
   - Rationale: Single source of truth, easier maintenance, consistency
   - Trade-off: Adds dependency on common/ module

3. **Phased rollout** (vs. big bang)
   - Rationale: Easier to review, test, and debug; reduces risk
   - Trade-off: Takes longer to complete full rollout

4. **pytest-based lint checks** (vs. traditional linters)
   - Rationale: Consistent with existing approach, flexible, easy to customize
   - Trade-off: Not as fast as compiled linters, but acceptable for current scale

### Future Enhancements

1. **Optimization**: Scan only changed files in PR context
2. **Additional Lint Checks**: Environment variable validation, import ordering, etc.
3. **Centralized Lint Test**: Single test that scans all domains (if maintenance burden grows)
4. **Pre-commit Hook**: Run lint checks locally before commit
5. **IDE Integration**: Real-time lint feedback in editor

---

**End of Plan**
