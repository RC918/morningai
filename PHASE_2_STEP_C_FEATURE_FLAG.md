# Phase 2 Step C: Feature Flag Implementation

**Status**: ✅ Complete  
**PR**: TBD  
**Date**: 2025-11-27

## Overview

Phase 2 Step C implements the `ENABLE_PROJECT_ENGINEER_CODEGEN` feature flag to control ProjectEngineerAgent execution mode via environment variables, eliminating the need for code changes to toggle between analysis-only and execution modes.

## Changes

### 1. Feature Flag Definition

**File**: `config/env.schema.yaml`

```yaml
ENABLE_PROJECT_ENGINEER_CODEGEN:
  type: boolean
  required: false
  default: false
  description: Enable ProjectEngineerAgent code generation execution mode (Phase 2 Step C)
  category: Feature Flags
  security_level: public
  notes: |
    Controls whether ProjectEngineerAgent can execute code generation:
    - false (default): Analysis-only mode, tasks are classified but not executed
    - true: Execution mode, safe tasks trigger CodeGenerationWorkflow
    
    Requires dev_agent to be provided to ProjectEngineerAgent constructor.
    Only affects safe tasks (documentation_update, test_generation).
    Unsafe tasks are always skipped regardless of this setting.
```

### 2. Settings Integration

**File**: `common/config/settings.py`

```python
enable_project_engineer_codegen: bool = Field(
    default=False,
    alias="ENABLE_PROJECT_ENGINEER_CODEGEN",
    description="Enable ProjectEngineerAgent code generation execution mode (Phase 2 Step C)"
)
```

### 3. Agent Integration

**File**: `handoff/20250928/40_App/orchestrator/project_engineer/agent.py`

```python
def __init__(self, enable_code_generation: bool = None, dev_agent=None):
    """
    Initialize ProjectEngineerAgent with dependencies

    Args:
        enable_code_generation: Enable code generation execution
                               If None, reads from ENABLE_PROJECT_ENGINEER_CODEGEN env var
                               If False, forces analysis-only mode
                               If True, enables execution mode (requires dev_agent)
        dev_agent: DevAgent instance for CodeGenerationWorkflow
    """
    # Phase 2 Step C: Read from feature flag if not explicitly set
    if enable_code_generation is None:
        try:
            from common.config.settings import settings
            enable_code_generation = settings.enable_project_engineer_codegen
            logger.info(f"[ProjectEngineerAgent] Using ENABLE_PROJECT_ENGINEER_CODEGEN={enable_code_generation}")
        except Exception as e:
            logger.warning(f"[ProjectEngineerAgent] Failed to read feature flag: {e}, defaulting to False")
            enable_code_generation = False
```

## Usage

### Environment Variable Control (Recommended)

```bash
# Enable execution mode via environment variable
export ENABLE_PROJECT_ENGINEER_CODEGEN=true

# Create agent (reads from env var)
agent = ProjectEngineerAgent(dev_agent=dev_agent)
```

### Explicit Override

```python
# Force execution mode (overrides env var)
agent = ProjectEngineerAgent(enable_code_generation=True, dev_agent=dev_agent)

# Force analysis-only mode (overrides env var)
agent = ProjectEngineerAgent(enable_code_generation=False)
```

### Backward Compatibility

Phase 2 Step B code continues to work without changes:

```python
# Phase 2 Step B style (still supported)
agent = ProjectEngineerAgent(enable_code_generation=False)  # Analysis mode
agent = ProjectEngineerAgent(enable_code_generation=True, dev_agent=dev_agent)  # Execution mode
```

## Test Coverage

**Total Tests**: 84 (all passing)  
**New Tests**: 12 feature flag tests

### Feature Flag Integration Tests (9 tests)

1. `test_feature_flag_disabled_by_default` - Verifies default False behavior
2. `test_feature_flag_enabled_via_env` - Tests env var enabling
3. `test_explicit_true_overrides_env` - Tests explicit True override
4. `test_explicit_false_overrides_env` - Tests explicit False override
5. `test_none_reads_from_env` - Tests None reads from env
6. `test_feature_flag_requires_dev_agent_when_enabled` - Tests dev_agent requirement
7. `test_feature_flag_fallback_on_settings_error` - Tests error fallback
8. `test_backward_compatibility_explicit_false` - Tests Phase 2 Step B compat
9. `test_backward_compatibility_explicit_true` - Tests Phase 2 Step B compat

### Settings Integration Tests (3 tests)

1. `test_settings_has_feature_flag` - Verifies field exists in settings
2. `test_settings_reads_from_env` - Tests env var reading
3. `test_settings_type_validation` - Tests boolean type validation

## Benefits

1. **Centralized Configuration**: Control execution mode via environment variables
2. **No Code Changes**: Toggle execution mode without modifying code
3. **Canary Rollout Support**: Enable for subset of instances via env vars
4. **A/B Testing**: Test execution mode vs analysis mode in production
5. **Backward Compatible**: Existing Phase 2 Step B code works unchanged
6. **Type Safe**: Pydantic validation ensures boolean type
7. **Error Handling**: Falls back to False on settings errors

## Migration Path

### From Phase 2 Step B to Step C

**Before (Phase 2 Step B)**:
```python
# Hardcoded in code
agent = ProjectEngineerAgent(enable_code_generation=True, dev_agent=dev_agent)
```

**After (Phase 2 Step C)**:
```bash
# Set environment variable
export ENABLE_PROJECT_ENGINEER_CODEGEN=true
```

```python
# Read from env var
agent = ProjectEngineerAgent(dev_agent=dev_agent)
```

### Deployment Strategy

1. **Phase 1**: Deploy with `ENABLE_PROJECT_ENGINEER_CODEGEN=false` (default)
2. **Phase 2**: Enable for 10% of instances via env var
3. **Phase 3**: Monitor metrics and gradually increase to 50%
4. **Phase 4**: Enable for 100% if metrics are good
5. **Phase 5**: Update code to remove explicit `enable_code_generation` parameters

## Future Improvements (Deferred)

The following improvements were identified but deferred to future PRs:

### 1. Per-Task Whitelist (Medium Priority)

Currently only global deny list exists. Future enhancement:

```python
# In safe_tasks.py
SAFE_TASK_METADATA = {
    "documentation_update": {
        "allowed_directories": ["docs/", "README.md"],
        "max_files": 5,
        ...
    }
}
```

### 2. Rollback Semantics (Low Priority)

Currently:
- New files created during execution are not deleted on rollback
- PRs created are not automatically closed on failure

Future enhancement: Full rollback support with state tracking

### 3. E2E Integration Tests (Medium Priority)

Current tests use mocks. Future enhancement: Real CodeGenerationWorkflow integration tests

### 4. Sync Wrapper (Low Priority)

Add `run_task_sync()` for CLI usage (currently only async `run_task()` exists)

## Related Documents

- [Phase 2 Step A Technical Design](PHASE_2_STEP_A_TECHNICAL_DESIGN.md)
- [Phase 2 Step B Technical Design](PHASE_2_STEP_B_TECHNICAL_DESIGN.md)
- [Environment Schema](config/env.schema.yaml)
- [Settings Module](common/config/settings.py)

## Commits

1. `add71892` - feat(phase2): Add ENABLE_PROJECT_ENGINEER_CODEGEN feature flag
2. `28ce4a30` - test(phase2): Add comprehensive tests for feature flag integration
