# Phase 1: AI Planner Integration - Implementation Plan

**Date**: 2025-11-17  
**Duration**: 2-3 weeks  
**Status**: Completed (2026-01-16)

---

## Executive Summary

Phase 1 focuses on integrating the agent_eval framework with the orchestrator to enable continuous monitoring of AI agent performance, with emphasis on planner accuracy metrics.

**Key Objectives**:
1. Integrate agent_eval with orchestrator workflow
2. Implement Planner Accuracy metric (Target: 70%)
3. Implement Self-Healing Rate metric (Target: 50%)
4. Expand dataset from 10 to 50+ evaluation cases
5. Deploy agent_eval CI in non-blocking mode
6. Create monitoring dashboard for metrics visualization

---

## Current State Analysis

### Agent_eval Framework (from AUDIT_REPORT_2025_11_17.md)
- ✅ **Structure**: Complete (runner.py, metrics.py, dataset.jsonl)
- ❌ **Integration**: Placeholder only (not connected to orchestrator)
- ⚠️ **Metrics**: 40% aligned with roadmap (missing planner accuracy, self-healing, coordination, cost)
- ✅ **Dataset**: 10 tasks, well-balanced, all paths validated
- ❌ **CI**: Template ready but not deployed

### Orchestrator Architecture
- **Entry Point**: `redis_queue/worker.py::run_orchestrator_task()`
- **Modes**: LangGraph (stateful) vs Simple (direct execution)
- **Canary**: USE_LANGGRAPH_PERCENT for gradual rollout
- **Persistence**: Redis + PostgreSQL (via db_writer)
- **Result Format**: `{"pr_url": str, "trace_id": str, "state": str}`

### Integration Points
1. **Task Submission**: `run_orchestrator_task()` in worker.py
2. **Status Monitoring**: Redis keys `agent:task:{task_id}`
3. **Result Collection**: PR URL, CI state, trace_id
4. **Database**: `agent_tasks` table via db_writer

---

## Task Breakdown

### Task 1: Orchestrator Integration (2-3 days)
**Goal**: Connect agent_eval runner to orchestrator for real task execution

**Subtasks**:
1.1. Create orchestrator client wrapper (`tools/agent_eval/orchestrator_client.py`)
   - Submit task via `run_orchestrator_task()`
   - Poll Redis for status updates
   - Extract results (PR URL, CI state, duration)
   - Handle timeouts and errors

1.2. Update `runner.py::run_task()` to use orchestrator client
   - Replace placeholder logic with real orchestrator calls
   - Add timeout configuration (default: 600s)
   - Implement status polling (interval: 10s)
   - Collect execution metrics

1.3. Add GitHub API integration for CI status
   - Check PR CI checks via GitHub API
   - Determine ci_passed boolean
   - Extract CI failure reasons

1.4. Update result schema
   - Add `actual_duration_seconds`
   - Add `ci_failure_reasons`
   - Add `orchestrator_mode` (langgraph vs simple)

**Acceptance Criteria**:
- ✅ agent_eval can submit tasks to orchestrator
- ✅ Status polling works correctly
- ✅ Results include real PR URLs and CI status
- ✅ Timeouts handled gracefully
- ✅ Tests pass for orchestrator client

**Files to Modify**:
- `tools/agent_eval/runner.py` (lines 56-94)
- `tools/agent_eval/orchestrator_client.py` (NEW)
- `tools/agent_eval/requirements.txt` (add PyGithub)

---

### Task 2: Planner Accuracy Metric (1-2 days)
**Goal**: Implement metric to measure planner step accuracy (Target: 70%)

**Subtasks**:
2.1. Extend dataset schema with `expected_plan_steps`
   - Add to 10 existing tasks
   - Define clear, measurable plan steps
   - Example: ["Analyze auth.py", "Update timeout", "Add tests", "Create PR"]

2.2. Capture actual plan steps from orchestrator
   - Extract from LangGraph state (if available)
   - Parse from execution logs
   - Store in result schema as `actual_plan_steps`

2.3. Implement planner accuracy calculation
   - Add `calculate_planner_accuracy()` to metrics.py
   - Use sequence similarity (e.g., Levenshtein distance)
   - Formula: `matching_steps / expected_steps * 100`

2.4. Add planner metrics to output
   - Update `print_metrics()` to show planner accuracy
   - Add breakdown by task type and difficulty

**Acceptance Criteria**:
- ✅ Dataset includes expected_plan_steps for all tasks
- ✅ Actual plan steps captured from orchestrator
- ✅ Planner accuracy metric calculated correctly
- ✅ Metric displayed in evaluation output
- ✅ Tests pass for planner accuracy calculation

**Files to Modify**:
- `tools/agent_eval/dataset.jsonl` (all 10 tasks)
- `tools/agent_eval/metrics.py` (add calculate_planner_accuracy)
- `tools/agent_eval/runner.py` (capture actual_plan_steps)

---

### Task 3: Self-Healing Rate Metric (1 day)
**Goal**: Implement metric to measure self-healing success (Target: 50%)

**Subtasks**:
3.1. Extend dataset schema with self-healing fields
   - Add `expected_retries` (number of expected retry attempts)
   - Add `self_healing_opportunities` (list of expected fix scenarios)

3.2. Capture retry/fix attempts from orchestrator
   - Track retry_attempts from RQ job retries
   - Detect self-healing from execution logs
   - Store in result schema

3.3. Implement self-healing rate calculation
   - Add `calculate_self_healing_rate()` to metrics.py
   - Formula: `successful_heals / total_retry_attempts * 100`

3.4. Add self-healing metrics to output
   - Update `print_metrics()` to show self-healing rate
   - Add breakdown by error type

**Acceptance Criteria**:
- ✅ Dataset includes self-healing fields
- ✅ Retry attempts tracked correctly
- ✅ Self-healing rate metric calculated
- ✅ Metric displayed in evaluation output
- ✅ Tests pass for self-healing calculation

**Files to Modify**:
- `tools/agent_eval/dataset.jsonl` (add self-healing fields)
- `tools/agent_eval/metrics.py` (add calculate_self_healing_rate)
- `tools/agent_eval/runner.py` (capture retry data)

---

### Task 4: Dataset Expansion (2-3 days)
**Goal**: Expand dataset from 10 to 50+ evaluation cases

**Subtasks**:
4.1. Analyze existing codebase for task candidates
   - Review recent PRs for real-world tasks
   - Identify common bug patterns
   - Find feature requests from issues

4.2. Create 40+ new evaluation tasks
   - Maintain balanced distribution (bug_fix, feature, refactor, test)
   - Cover difficulty range (easy: 30%, medium: 40%, hard: 30%)
   - Include edge cases and failure scenarios

4.3. Validate new tasks
   - Verify all file paths exist
   - Ensure expected outcomes are measurable
   - Add expected_plan_steps for planner accuracy

4.4. Document task creation guidelines
   - Create TASK_CREATION_GUIDE.md
   - Define quality standards
   - Provide examples

**Acceptance Criteria**:
- ✅ Dataset contains 50+ tasks
- ✅ Balanced distribution maintained
- ✅ All file paths validated
- ✅ Expected outcomes well-defined
- ✅ Task creation guide documented

**Files to Modify**:
- `tools/agent_eval/dataset.jsonl` (expand to 50+ tasks)
- `tools/agent_eval/TASK_CREATION_GUIDE.md` (NEW)

---

### Task 5: Agent_eval CI Integration (1-2 days)
**Goal**: Deploy agent_eval to CI in non-blocking mode

**Subtasks**:
5.1. Create GitHub Actions workflow
   - File: `.github/workflows/agent-evaluation.yml`
   - Trigger: Weekly schedule (Sunday) + manual dispatch
   - Run subset of tasks (--max-tasks 5) for speed

5.2. Configure non-blocking mode
   - Set `continue-on-error: true`
   - Don't fail PR on evaluation failures
   - Upload results as artifacts

5.3. Add result archiving
   - Store results in GitHub artifacts
   - Retain last 10 evaluations
   - Enable trend analysis

5.4. Configure notifications
   - Alert on >10% success rate drop
   - Post summary to PR comments (optional)

**Acceptance Criteria**:
- ✅ CI workflow created and tested
- ✅ Non-blocking mode verified
- ✅ Results archived correctly
- ✅ Notifications working
- ✅ Documentation updated

**Files to Create**:
- `.github/workflows/agent-evaluation.yml` (NEW)
- `tools/agent_eval/CI_INTEGRATION.md` (NEW)

---

### Task 6: Monitoring Dashboard (2-3 days)
**Goal**: Create dashboard for metrics visualization

**Subtasks**:
6.1. Design dashboard layout
   - Overall metrics (completion, correctness, CI pass)
   - Planner accuracy trend
   - Self-healing rate trend
   - Breakdown by task type and difficulty

6.2. Implement dashboard backend
   - API endpoint: `GET /api/agent-eval/metrics`
   - Fetch historical results from artifacts
   - Calculate trends and aggregates

6.3. Implement dashboard frontend
   - Create page in Owner Console
   - Use Chart.js or similar for visualizations
   - Add filters (date range, task type, difficulty)

6.4. Add real-time updates
   - WebSocket or polling for live metrics
   - Show currently running evaluations

**Acceptance Criteria**:
- ✅ Dashboard displays all key metrics
- ✅ Trends visualized correctly
- ✅ Filters work as expected
- ✅ Real-time updates functional
- ✅ Tests pass for dashboard components

**Files to Create**:
- `handoff/20250928/40_App/owner-console/src/pages/AgentEvalDashboard.tsx` (NEW)
- `handoff/20250928/40_App/api-backend/src/routes/agent_eval.py` (NEW)

---

### Task 7: Testing & Validation (1-2 days)
**Goal**: Comprehensive testing of all Phase 1 components

**Subtasks**:
7.1. Unit tests for new metrics
   - Test planner accuracy calculation
   - Test self-healing rate calculation
   - Test orchestrator client

7.2. Integration tests
   - Test end-to-end evaluation flow
   - Test CI workflow locally
   - Test dashboard API

7.3. Manual validation
   - Run full evaluation on staging
   - Verify metrics accuracy
   - Test dashboard usability

7.4. Performance testing
   - Measure evaluation runtime
   - Optimize slow operations
   - Ensure CI timeout compliance

**Acceptance Criteria**:
- ✅ All unit tests pass
- ✅ Integration tests pass
- ✅ Manual validation successful
- ✅ Performance acceptable (<10 min for 50 tasks)

**Files to Create**:
- `tools/agent_eval/tests/test_orchestrator_client.py` (NEW)
- `tools/agent_eval/tests/test_planner_metrics.py` (NEW)

---

### Task 8: Documentation & PR (1 day)
**Goal**: Document Phase 1 work and create PR

**Subtasks**:
8.1. Update README
   - Document orchestrator integration
   - Add usage examples
   - Update metrics documentation

8.2. Create Phase 1 completion report
   - Summarize achievements
   - Document metrics baselines
   - Identify future improvements

8.3. Create PR
   - Comprehensive description
   - Link to Phase 1 plan
   - Include screenshots of dashboard

8.4. Wait for CI and address feedback
   - Fix any CI failures
   - Address code review comments
   - Update PR description

**Acceptance Criteria**:
- ✅ Documentation complete and accurate
- ✅ PR created with detailed description
- ✅ CI passes
- ✅ Code review feedback addressed

**Files to Modify**:
- `tools/agent_eval/README.md`
- `PHASE_1_COMPLETION_REPORT.md` (NEW)

---

## Timeline

### Week 1 (Nov 17-23)
- **Days 1-3**: Task 1 (Orchestrator Integration)
- **Days 4-5**: Task 2 (Planner Accuracy Metric)

### Week 2 (Nov 24-30)
- **Day 1**: Task 3 (Self-Healing Rate Metric)
- **Days 2-4**: Task 4 (Dataset Expansion)
- **Day 5**: Task 5 (CI Integration)

### Week 3 (Dec 1-7)
- **Days 1-3**: Task 6 (Monitoring Dashboard)
- **Days 4-5**: Task 7 (Testing & Validation)
- **Day 6**: Task 8 (Documentation & PR)

---

## Success Metrics

### Quantitative
- ✅ Agent_eval integrated with orchestrator (100% functional)
- ✅ Planner accuracy metric implemented and tracking (baseline established)
- ✅ Self-healing rate metric implemented and tracking (baseline established)
- ✅ Dataset expanded to 50+ tasks (5x growth)
- ✅ CI integration deployed and running weekly
- ✅ Dashboard created and accessible

### Qualitative
- ✅ Metrics provide actionable insights for agent improvement
- ✅ CI integration is non-blocking and reliable
- ✅ Dashboard is intuitive and useful for monitoring
- ✅ Documentation is comprehensive and clear

---

## Risk Mitigation

### Technical Risks
1. **Orchestrator integration complexity**
   - Mitigation: Start with minimal integration, iterate
   - Fallback: Use mock orchestrator for testing

2. **Planner step extraction difficulty**
   - Mitigation: Parse from logs if LangGraph state unavailable
   - Fallback: Manual annotation for baseline

3. **CI timeout on full dataset**
   - Mitigation: Use `--max-tasks 5` for CI runs
   - Fallback: Run full evaluation weekly via cron

### Timeline Risks
1. **Dataset expansion takes longer than expected**
   - Mitigation: Prioritize quality over quantity (aim for 30+ if needed)
   - Fallback: Phase 1.5 for remaining tasks

2. **Dashboard implementation delayed**
   - Mitigation: Start with simple CLI output, iterate
   - Fallback: Defer dashboard to Phase 2

---

## Next Steps

**Immediate (Today)**:
1. ✅ Create Phase 1 implementation plan (DONE)
2. 🔄 Start Task 1.1: Create orchestrator client wrapper
3. ⏳ Implement task submission logic
4. ⏳ Add status polling

**This Week**:
- Complete orchestrator integration
- Implement planner accuracy metric
- Begin dataset expansion

---

## References

- [Agent Eval Audit Report](./tools/agent_eval/AUDIT_REPORT_2025_11_17.md)
- [Strategic Roadmap](./MorningAI_Planning_Report_2025-11-17.md)
- [Orchestrator Worker](./handoff/20250928/40_App/orchestrator/redis_queue/worker.py)
- [Phase 0.1 Completion](./PHASE_0_COMPLETION_REPORT.md)

---

**Plan Status**: ✅ APPROVED  
**Start Date**: 2025-11-17  
**Expected Completion**: 2025-12-07
