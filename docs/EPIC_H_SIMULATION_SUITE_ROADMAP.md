# EPIC H: Multi-Agent Simulation Suite v1 Roadmap

## Overview

EPIC H implements the Multi-Agent Simulation Suite v1 and Regression Pipeline v1 as defined in Blueprint Sections 5.3 and 5.4.

**Blueprint Reference**: MorningAI_Ecosystem_Blueprint_2025_Final.md
- Section 5.3: Multi-Agent Simulation Suite v1
- Section 5.4: Regression Pipeline v1

**GitHub Issue**: [#3492](https://github.com/RC918/morningai/issues/3492)

## Architecture

### Simulation Suite v1 (Blueprint 5.3)

The Simulation Suite is MorningAI's QA system for multi-agent testing:

```
┌─────────────────────────────────────────────────────────────┐
│                    Simulation Suite v1                       │
├─────────────────────────────────────────────────────────────┤
│  SimulationScenario (Base Class)                            │
│  ├── FlowBranchScenario      - Flow v3 branch testing       │
│  ├── RoutingScenario         - Routing testing              │
│  ├── SafetyComplianceScenario - Safety/compliance testing   │
│  ├── DriftScenario           - Drift testing                │
│  ├── ProviderFallbackScenario - Provider fallback testing   │
│  └── MultiAgentScenario      - Multi-agent E2E testing      │
├─────────────────────────────────────────────────────────────┤
│  ScenarioRunner                                              │
│  ├── Sequential execution                                    │
│  ├── Parallel execution                                      │
│  ├── Tag-based filtering                                     │
│  ├── Result aggregation                                      │
│  └── Replay capability (Blueprint: 可回放)                   │
└─────────────────────────────────────────────────────────────┘
```

### Regression Pipeline v1 (Blueprint 5.4)

Automated regression test generation from errors:

```
┌─────────────────────────────────────────────────────────────┐
│                  Regression Pipeline v1                      │
├─────────────────────────────────────────────────────────────┤
│  Error Sources:                                              │
│  ├── Runtime Errors (Node/Python logs)                       │
│  ├── BrowserNode Failures (selector/DOM issues)              │
│  ├── Sentry/Datadog Alerts (stack trace + breadcrumbs)       │
│  └── Diagnostic Agent Reports (root cause + repro steps)     │
├─────────────────────────────────────────────────────────────┤
│  RegressionCandidateCollector                                │
│  ├── Error signature generation (deduplication)              │
│  ├── Frequency tracking                                      │
│  └── Priority calculation:                                   │
│      priority = severity*0.5 + frequency*0.3 + blast_radius*0.2│
├─────────────────────────────────────────────────────────────┤
│  Priority Levels:                                            │
│  ├── P0: 立即建立 regression (score >= 0.7)                  │
│  ├── P1: 排入 nightly cycle (score >= 0.4)                   │
│  └── P2: 觀察是否重複 (score < 0.4)                          │
├─────────────────────────────────────────────────────────────┤
│  RegressionTestGenerator                                     │
│  ├── Generate test from candidate                            │
│  ├── Include reproduction steps                              │
│  └── Add CI enforcement metadata                             │
└─────────────────────────────────────────────────────────────┘
```

### CI Enforcement (Blueprint 5.4)

```
┌─────────────────────────────────────────────────────────────┐
│                    CI Enforcement Rules                      │
├─────────────────────────────────────────────────────────────┤
│  1. Regression test fails → PR blocked                       │
│  2. Regression test modified → Requires reviewer approval    │
│  3. Regression test deleted → Safety Governor blocks         │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Status

### Phase H-1: Simulation Suite Core (Completed)

| Component | Status | Description |
|-----------|--------|-------------|
| `SimulationScenario` | Completed | Base class for all scenarios |
| `ScenarioResult` | Completed | Result data structure |
| `ScenarioRunner` | Completed | Executes scenarios, aggregates results |
| `FlowBranchScenario` | Completed | Flow v3 branch testing base |
| `RoutingScenario` | Completed | Routing testing base |
| `SafetyComplianceScenario` | Completed | Safety/compliance testing base |
| `DriftScenario` | Completed | Drift testing base |
| `ProviderFallbackScenario` | Completed | Provider fallback testing base |
| `MultiAgentScenario` | Completed | Multi-agent E2E testing base |

### Phase H-2: Regression Pipeline Core (Completed)

| Component | Status | Description |
|-----------|--------|-------------|
| `RegressionCandidate` | Completed | Candidate data structure with priority calculation |
| `RegressionPriority` | Completed | P0/P1/P2 priority levels |
| `ErrorSource` | Completed | Error source enumeration |
| `RegressionCandidateCollector` | Completed | Collects and deduplicates errors |
| `RegressionTestGenerator` | Completed | Generates test code from candidates |

### Phase H-3: Built-in Scenarios (Completed)

| Scenario | Status | Description |
|----------|--------|-------------|
| `FlowExecutionScenario` | Completed | Test complete flow execution |
| `FlowBranchCoverageScenario` | Completed | Test all flow branches |
| `TaskRoutingScenario` | Completed | Test task-based routing |
| `FallbackRoutingScenario` | Completed | Test provider fallback |
| `ContentSafetyScenario` | Completed | Test content safety scanning |
| `PIIScannerScenario` | Completed | Test PII detection |
| `DriftDetectionScenario` | Completed | Test drift detection |
| `HealthCheckScenario` | Completed | Test health monitoring |

### Phase H-4: Integration (Future)

| Component | Status | Description |
|-----------|--------|-------------|
| Error source integration | Planned | Hook into runtime error logging |
| CI enforcement | Planned | GitHub Actions integration |
| Visualization | Planned | Risk Heatmap, test coverage dashboard |
| Weekly cycle automation | Planned | Automated regression generation |

## Usage Examples

### Running Simulation Scenarios

```python
from simulation import ScenarioRunner
from simulation.scenarios import (
    FlowExecutionScenario,
    TaskRoutingScenario,
    ContentSafetyScenario,
)

# Create runner
runner = ScenarioRunner()

# Register scenarios
runner.register(FlowExecutionScenario(flow_type="review"))
runner.register(TaskRoutingScenario(task_type="code_gen", expected_provider="alicloud"))
runner.register(ContentSafetyScenario(
    test_input="Normal safe content",
    expected_blocked=False,
))

# Run all scenarios
result = runner.run_all(parallel=True)

# Check results
print(result.summary())
if not result.all_passed:
    for failed in result.get_failed_scenarios():
        print(f"Failed: {failed.scenario_name} - {failed.error_message}")
```

### Collecting Regression Candidates

```python
from simulation.regression import (
    RegressionCandidateCollector,
    RegressionTestGenerator,
    ErrorSource,
    RegressionPriority,
)

# Create collector
collector = RegressionCandidateCollector()

# Collect an error
candidate = collector.collect(
    source=ErrorSource.RUNTIME_ERROR,
    error_type="ValueError",
    error_message="Invalid model response format",
    stack_trace="...",
    severity=0.8,
    blast_radius=0.5,
)

# Check priority
print(f"Priority: {candidate.priority.value}")  # p0

# Generate regression test
generator = RegressionTestGenerator()
test_code = generator.generate_test(candidate)
print(test_code)
```

### Filtering by Tags

```python
# Run only routing scenarios
result = runner.run_by_tags(["routing"])

# Run only safety scenarios
result = runner.run_by_tags(["safety", "compliance"])

# Run only drift scenarios
result = runner.run_by_tags(["drift"])
```

## Feature Flags

| Flag | Default | Description |
|------|---------|-------------|
| `ENABLE_SIMULATION_SUITE` | `false` | Enable simulation suite execution |
| `SIMULATION_PARALLEL_WORKERS` | `4` | Number of parallel workers |
| `ENABLE_REGRESSION_PIPELINE` | `false` | Enable regression candidate collection |
| `REGRESSION_AUTO_GENERATE` | `false` | Auto-generate regression tests for P0 |

## Cross-EPIC Integration

### EPIC G (Memory v2) Integration
- Simulation results stored in Knowledge Base memory
- Regression patterns stored for learning

### EPIC I (Runtime Governance) Integration
- Drift scenarios use DriftDetector from EPIC I
- Health scenarios use HeartbeatHandler from EPIC I

### EPIC D (Coder Agent) Integration
- Diagnostic Agent provides reproduction steps for regression candidates
- Test Agent v2 generates regression tests

## Weekly Regression Cycle (Blueprint 5.4)

```
Weekly Cycle:
1. 搜集新錯誤 (Collect new errors)
   - Runtime errors from logs
   - BrowserNode failures
   - Sentry/Datadog alerts
   - Diagnostic Agent reports

2. 自動生成 regression (Auto-generate regression tests)
   - P0 candidates → Immediate generation
   - P1 candidates → Nightly generation
   - P2 candidates → Observe for repetition

3. 重新計算 regression coverage (Recalculate coverage)
   - Track which error patterns are covered
   - Identify gaps in coverage

4. 更新 Risk Heatmap (Update Risk Heatmap)
   - Visualize high-risk areas
   - Track regression over time
```

## ChangeLog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-15 | Devin AI | Initial implementation: H-1 Simulation Suite Core, H-2 Regression Pipeline Core, H-3 Built-in Scenarios |
