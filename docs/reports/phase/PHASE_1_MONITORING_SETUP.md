# Phase 1 Monitoring Setup Guide

**Date**: 2025-11-24  
**Status**: In Progress  
**Purpose**: Establish comprehensive monitoring for Phase 1 (5% Canary)

---

## Overview

This document provides the complete monitoring setup for Phase 1 canary deployment, including:
1. OpenAI usage monitoring and alerts
2. Canary metrics dashboard
3. Data collection and analysis procedures

---

## 1. OpenAI Usage Monitoring

### Current Status

**OpenAI Account**: `morningai (sk-...PJ0A)` (Staging)
- **Credit Balance**: Recently recharged (was -$0.11, now positive)
- **Auto-recharge**: ✅ Enabled
- **Usage Tier**: Tier 1
- **Model**: GPT-4 Turbo (`gpt-4-turbo-preview`)

### Monitoring Requirements

**Critical Metrics**:
1. **Daily Usage**: Track API calls and costs
2. **Credit Balance**: Monitor remaining credits
3. **Quota Errors**: Detect 429 errors early
4. **Cost per Task**: Calculate average cost per LLM Planner call

**Alert Thresholds**:
- ⚠️ Warning: Credit balance < $10
- 🚨 Critical: Credit balance < $5
- 🚨 Critical: 429 errors > 3 in 5 minutes
- ⚠️ Warning: Daily cost > $5 (Staging) / $30 (Production)

### Implementation Options

#### Option A: OpenAI Dashboard Manual Monitoring (Current)

**Pros**:
- No implementation needed
- Official OpenAI metrics
- Accurate billing data

**Cons**:
- Manual checking required
- No automated alerts
- Reactive, not proactive

**Access**: https://platform.openai.com/usage

#### Option B: API-based Monitoring (Recommended)

**Implementation**:
```python
# tools/monitoring/openai_usage_monitor.py
import os
import requests
from datetime import datetime, timedelta

def check_openai_usage():
    """Check OpenAI usage and send alerts if needed"""
    api_key = os.getenv('OPENAI_API_KEY')
    
    # Get usage data from OpenAI API
    # Note: OpenAI doesn't have a public usage API yet
    # Alternative: Parse from dashboard or use billing API
    
    # For now, we track via our own metrics
    pass

def track_llm_planner_cost():
    """Track cost per LLM Planner call"""
    # GPT-4 Turbo pricing (as of 2024):
    # Input: $0.01 / 1K tokens
    # Output: $0.03 / 1K tokens
    
    # Estimated tokens per call:
    # Input: ~2000 tokens (task description + context)
    # Output: ~500 tokens (plan with 3-7 steps)
    
    estimated_cost_per_call = (2000 * 0.01 / 1000) + (500 * 0.03 / 1000)
    # = $0.02 + $0.015 = $0.035 per call
    
    return estimated_cost_per_call
```

**Cost Estimates**:
- **Per LLM Planner Call**: ~$0.035 (3.5 cents)
- **Staging (5% of 100 tasks/day)**: 5 calls/day × $0.035 = **$0.175/day** = **$5.25/month**
- **Production (5% of 1000 tasks/day)**: 50 calls/day × $0.035 = **$1.75/day** = **$52.50/month**

#### Option C: Sentry-based Cost Tracking (Implemented)

**Current Implementation**:
- LLM Planner already logs to Sentry
- Can add custom tags for cost tracking
- Integrate with existing alerting

**Enhancement**:
```python
# In llm_planner_adapter.py
import sentry_sdk

def generate_plan(task_description):
    start_time = time.time()
    
    try:
        response = openai.ChatCompletion.create(...)
        
        # Track usage
        usage = response.get('usage', {})
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        
        # Calculate cost
        cost = (prompt_tokens * 0.01 / 1000) + (completion_tokens * 0.03 / 1000)
        
        # Log to Sentry
        sentry_sdk.set_context("llm_usage", {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost_usd": cost,
            "model": "gpt-4-turbo-preview"
        })
        
        # Also log to JSONL for analysis
        log_to_jsonl({
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": task_id,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost_usd": cost
        })
        
    except openai.error.RateLimitError as e:
        # 429 error - quota exceeded
        sentry_sdk.capture_exception(e)
        sentry_sdk.set_tag("alert_type", "openai_quota_exceeded")
        raise
```

### Recommended Approach

**Week 1-2 (Immediate)**:
1. ✅ Manual monitoring via OpenAI Dashboard (daily checks)
2. ⚠️ Enhance LLM Planner to log token usage and cost to JSONL
3. ⚠️ Set up Sentry alerts for 429 errors
4. ⚠️ Create daily cost summary script

**Week 3+ (Before Phase 2)**:
1. Implement automated cost tracking
2. Set up budget alerts
3. Create cost projection dashboard

---

## 2. Canary Metrics Dashboard

### Existing Infrastructure

**Canary Metrics** (`metrics.py`):
- ✅ Redis-based minute-bucket counters
- ✅ Tracks routing decisions (simple vs langgraph)
- ✅ Tracks planner success/failure/error rates
- ✅ Calculates latency percentiles (P50/P90/P95/P99)
- ✅ 15-minute rolling window analysis

**Canary Alerting** (`canary_alerting.py`):
- ✅ SLO breach detection
- ✅ Sentry and webhook alerts
- ✅ 5-minute cooldown to prevent alert storms

### Dashboard Requirements

**Key Metrics to Display**:

1. **Routing Decisions**:
   - Total decisions (simple + langgraph)
   - LangGraph percentage (should be ~5%)
   - Trend over time

2. **LLM Planner Performance**:
   - Success rate (target: > 95%)
   - Failure rate (target: < 5%)
   - 5xx error rate (target: < 1%)

3. **Latency**:
   - P50, P90, P95, P99 (ms)
   - Target: P95 < 30 seconds

4. **Cost**:
   - Daily cost (USD)
   - Cost per task (USD)
   - Projected monthly cost

5. **Data Collection Progress**:
   - Total LLM Planner calls
   - Target: 50+ calls for Phase 2 decision

### Implementation Options

#### Option A: Grafana Dashboard (Ideal, but requires setup)

**Pros**:
- Professional, real-time dashboard
- Rich visualization options
- Alerting built-in

**Cons**:
- Requires Grafana instance
- Requires Redis data source setup
- Time-consuming to set up

**Estimated Setup Time**: 4-6 hours

#### Option B: Simple Python Script (Recommended for Week 1-2)

**Pros**:
- Quick to implement (30 minutes)
- Uses existing Canary Metrics
- Can run on-demand or scheduled

**Cons**:
- Not real-time
- Basic visualization
- Manual execution

**Implementation**:
```python
# tools/monitoring/canary_dashboard.py
#!/usr/bin/env python3
"""
Simple Canary Dashboard - Display current metrics
"""
import os
import redis
from datetime import datetime
import sys
sys.path.insert(0, '/home/ubuntu/repos/morningai/handoff/20250928/40_App/orchestrator')
from metrics import create_canary_metrics

def display_dashboard():
    """Display current canary metrics"""
    redis_url = os.getenv('REDIS_URL')
    if not redis_url:
        print("Error: REDIS_URL not set")
        return
    
    r = redis.from_url(redis_url)
    metrics = create_canary_metrics(r, enabled=True)
    
    # Get 15-minute summary
    summary = metrics.get_canary_summary(window_minutes=15)
    
    print("=" * 60)
    print(f"Phase 1 Canary Dashboard - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 60)
    print()
    
    if not summary.get('enabled'):
        print("❌ Canary metrics disabled")
        return
    
    counts = summary.get('counts', {})
    rates = summary.get('rates', {})
    latency = summary.get('latency', {})
    
    # Routing Decisions
    print("📊 Routing Decisions (Last 15 min)")
    print(f"  Simple Mode:    {counts.get('decisions_simple', 0)}")
    print(f"  LangGraph Mode: {counts.get('decisions_langgraph', 0)}")
    total_decisions = counts.get('total_decisions', 0)
    if total_decisions > 0:
        langgraph_pct = (counts.get('decisions_langgraph', 0) / total_decisions) * 100
        print(f"  LangGraph %:    {langgraph_pct:.1f}% (target: ~5%)")
    print()
    
    # LLM Planner Performance
    print("🎯 LLM Planner Performance (Last 15 min)")
    print(f"  Success:  {counts.get('planner_success', 0)}")
    print(f"  Failure:  {counts.get('planner_failure', 0)}")
    print(f"  5xx Error: {counts.get('planner_error_5xx', 0)}")
    print(f"  Total:    {counts.get('total_planner', 0)}")
    print()
    print(f"  Failure Rate: {rates.get('failure_rate', 0):.2f}% (target: < 5%)")
    print(f"  5xx Rate:     {rates.get('error_5xx_rate', 0):.2f}% (target: < 1%)")
    
    total_planner = counts.get('total_planner', 0)
    if total_planner > 0:
        success_rate = (counts.get('planner_success', 0) / total_planner) * 100
        print(f"  Success Rate: {success_rate:.2f}% (target: > 95%)")
    print()
    
    # Latency
    print("⏱️  Latency (Last 15 min)")
    print(f"  P50: {latency.get('p50_ms', 'N/A')} ms")
    print(f"  P90: {latency.get('p90_ms', 'N/A')} ms")
    print(f"  P95: {latency.get('p95_ms', 'N/A')} ms (target: < 30000 ms)")
    print(f"  P99: {latency.get('p99_ms', 'N/A')} ms")
    print()
    
    # Data Collection Progress
    print("📈 Data Collection Progress")
    print(f"  Total LLM Planner Calls: {total_planner}")
    print(f"  Target for Phase 2: 50+")
    if total_planner >= 50:
        print(f"  Status: ✅ Ready for Phase 2 evaluation")
    else:
        remaining = 50 - total_planner
        print(f"  Status: ⚠️ Need {remaining} more calls")
    print()
    
    # SLO Status
    print("✅ SLO Status")
    slo_pass = True
    
    if rates.get('failure_rate', 0) > 5.0:
        print(f"  ❌ Failure rate too high: {rates.get('failure_rate', 0):.2f}%")
        slo_pass = False
    else:
        print(f"  ✅ Failure rate OK: {rates.get('failure_rate', 0):.2f}%")
    
    if rates.get('error_5xx_rate', 0) > 1.0:
        print(f"  ❌ 5xx rate too high: {rates.get('error_5xx_rate', 0):.2f}%")
        slo_pass = False
    else:
        print(f"  ✅ 5xx rate OK: {rates.get('error_5xx_rate', 0):.2f}%")
    
    p95 = latency.get('p95_ms')
    if p95 and p95 > 30000:
        print(f"  ❌ P95 latency too high: {p95} ms")
        slo_pass = False
    elif p95:
        print(f"  ✅ P95 latency OK: {p95} ms")
    else:
        print(f"  ⚠️ P95 latency: No data")
    
    print()
    if slo_pass and total_planner >= 5:
        print("🎉 All SLOs passing!")
    elif total_planner < 5:
        print("⚠️ Insufficient data for SLO evaluation")
    else:
        print("⚠️ Some SLOs failing - investigate!")
    
    print("=" * 60)

if __name__ == '__main__':
    display_dashboard()
```

**Usage**:
```bash
cd /home/ubuntu/repos/morningai
source .venv/bin/activate
export REDIS_URL="your-redis-url"
python tools/monitoring/canary_dashboard.py
```

#### Option C: Web Dashboard (Future)

**For Phase 2+**:
- Build simple Flask/FastAPI web dashboard
- Real-time updates via WebSocket
- Embeddable in admin console

---

## 3. Data Collection and Analysis

### Data Storage: Database + JSONL (Dual-Write)

**Current Status**:
- ✅ Database persistence implemented in `planner_events_store.py`
- ✅ Dual-write strategy: JSONL (backward compatibility) + Database (persistent storage)
- ✅ CLI tool supports both data sources
- ✅ Migration: `migrations/024_create_planner_events_table.sql`

**Storage Backends**:

1. **Database (Supabase PostgreSQL)** - Recommended for Production
   - **Pros**: Persistent across pod restarts, queryable, scalable
   - **Cons**: Requires Supabase credentials
   - **Table**: `planner_events`
   - **Indexes**: `timestamp DESC`, `trace_id`, `planner_type + timestamp`

2. **JSONL File** - Backward Compatibility / Local Dev
   - **Pros**: Simple, no external dependencies
   - **Cons**: Ephemeral (lost on pod restart in multi-pod deployments)
   - **Path**: `tools/agent_eval/data/planner_runs.jsonl`

**Configuration**:
```bash
# Environment variable (default: db)
export PLANNER_EVENTS_STORAGE=db    # Use database (production)
export PLANNER_EVENTS_STORAGE=jsonl # Use JSONL file (local dev)
```

**Data Fields** (stored in both backends):
```json
{
  "trace_id": "dd85a361-a6d1-46c1-aebe-9705423a75f4",
  "goal": "Fix bug in authentication flow",
  "planner_type": "llm",
  "task_type": "bugfix",
  "actual_plan_steps": ["step1", "step2", "step3"],
  "num_steps": 3,
  "planning_time_ms": 1500.0,
  "timestamp": "2025-11-27T01:00:00.000Z"
}
```

**Database Schema**:
```sql
CREATE TABLE planner_events (
    id BIGSERIAL PRIMARY KEY,
    trace_id UUID NOT NULL,
    goal TEXT NOT NULL,
    planner_type VARCHAR(50) NOT NULL,
    task_type VARCHAR(100),
    actual_plan_steps JSONB NOT NULL,
    num_steps INTEGER NOT NULL,
    planning_time_ms DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for query performance
CREATE INDEX idx_planner_events_timestamp ON planner_events(timestamp DESC);
CREATE INDEX idx_planner_events_trace_id ON planner_events(trace_id);
CREATE INDEX idx_planner_events_planner_type_timestamp ON planner_events(planner_type, timestamp DESC);
```

### Data Collection Goals

**Week 1-2 Target**: 50+ LLM Planner calls

**Current Progress**: 1 call (from final validation test)

**Estimated Timeline**:
- Staging traffic: ~5 calls/day (5% of 100 tasks/day)
- Days needed: 50 / 5 = **10 days**
- Target date: **December 4, 2025**

**Options to Accelerate**:
1. **Increase Staging traffic**: Run more test tasks
2. **Deploy to Production**: Enable 5% canary in Production
3. **Manual testing**: Run controlled tests with various task types

### Viewing Planner Statistics

**CLI Tool**: `tools/monitoring/view_planner_stats.py`

**Usage**:
```bash
# View statistics from database (default)
python -m tools.monitoring.view_planner_stats

# Show last 10 entries
python -m tools.monitoring.view_planner_stats --last 10

# Filter by goal substring
python -m tools.monitoring.view_planner_stats --filter "[Phase1-Test]"

# Use JSONL file instead of database
python -m tools.monitoring.view_planner_stats --source jsonl

# Use custom JSONL file path
python -m tools.monitoring.view_planner_stats --source jsonl --file /path/to/planner_runs.jsonl
```

**Output**:
```
======================================================================
Planner Statistics
======================================================================

Source: Database (Supabase)

📊 Total Planner Runs: 15

📅 Timeline
  First: 2025-11-24 14:02:15 UTC
  Last:  2025-11-27 01:00:00 UTC
  Duration: 58.9 hours
  Rate: 0.25 runs/hour

⏱️  Planning Time
  Min:    1.20s
  Median: 1.50s
  Mean:   1.65s
  P95:    2.80s
  Max:    3.50s
  Status: ✅ Acceptable (< 30s target)

📋 Plan Steps Distribution
  3 steps:   5 (33.3%) ████████
  4 steps:   4 (26.7%) ██████
  5 steps:   3 (20.0%) █████
  7 steps:   3 (20.0%) █████

🤖 Planner Type Distribution
  llm:    15 (100.0%)

📝 Task Type Distribution (Top 10)
  codegen:  5 (33.3%)
  bugfix:   4 (26.7%)
  refactor: 3 (20.0%)
  unknown:  3 (20.0%)

======================================================================
```

### Data Analysis Script

```python
# tools/monitoring/analyze_planner_data.py
#!/usr/bin/env python3
"""
Analyze JSONL planner data for Phase 2 readiness
"""
import json
from datetime import datetime
from collections import defaultdict

def analyze_planner_data(jsonl_path):
    """Analyze planner runs from JSONL file"""
    
    data = []
    with open(jsonl_path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    
    if not data:
        print("No data found")
        return
    
    print(f"Total LLM Planner Calls: {len(data)}")
    print()
    
    # Success rate
    successes = sum(1 for d in data if d.get('success'))
    success_rate = (successes / len(data)) * 100
    print(f"Success Rate: {success_rate:.2f}% ({successes}/{len(data)})")
    print()
    
    # Planning time statistics
    times = [d.get('planning_time_seconds', 0) for d in data]
    if times:
        print(f"Planning Time:")
        print(f"  Min:    {min(times):.2f}s")
        print(f"  Max:    {max(times):.2f}s")
        print(f"  Avg:    {sum(times)/len(times):.2f}s")
        print(f"  Median: {sorted(times)[len(times)//2]:.2f}s")
    print()
    
    # Cost analysis
    costs = [d.get('cost_usd', 0) for d in data]
    if costs:
        total_cost = sum(costs)
        avg_cost = total_cost / len(costs)
        print(f"Cost Analysis:")
        print(f"  Total:   ${total_cost:.4f}")
        print(f"  Average: ${avg_cost:.4f} per call")
        print(f"  Daily (5%):   ${avg_cost * 5:.4f} (Staging)")
        print(f"  Daily (5%):   ${avg_cost * 50:.4f} (Production)")
        print(f"  Monthly (5%): ${avg_cost * 5 * 30:.2f} (Staging)")
        print(f"  Monthly (5%): ${avg_cost * 50 * 30:.2f} (Production)")
    print()
    
    # Plan steps distribution
    steps = [d.get('plan_steps', 0) for d in data]
    if steps:
        print(f"Plan Steps:")
        print(f"  Min: {min(steps)}")
        print(f"  Max: {max(steps)}")
        print(f"  Avg: {sum(steps)/len(steps):.1f}")
    print()
    
    # Phase 2 readiness
    print("Phase 2 Readiness:")
    if len(data) >= 50:
        print(f"  ✅ Data collection: {len(data)}/50 calls")
    else:
        print(f"  ⚠️ Data collection: {len(data)}/50 calls (need {50-len(data)} more)")
    
    if success_rate >= 95:
        print(f"  ✅ Success rate: {success_rate:.2f}% (target: > 95%)")
    else:
        print(f"  ❌ Success rate: {success_rate:.2f}% (target: > 95%)")
    
    if avg_cost <= 0.05:
        print(f"  ✅ Cost per call: ${avg_cost:.4f} (target: < $0.05)")
    else:
        print(f"  ⚠️ Cost per call: ${avg_cost:.4f} (target: < $0.05)")

if __name__ == '__main__':
    jsonl_path = '/home/ubuntu/repos/morningai/tools/agent_eval/data/planner_runs.jsonl'
    analyze_planner_data(jsonl_path)
```

---

## 4. Monitoring Schedule

### Daily Tasks (Week 1-2)

**Every Morning** (10 minutes):
1. Check OpenAI Dashboard for credit balance and usage
2. Run canary dashboard script
3. Check Sentry for any alerts
4. Review JSONL data collection progress

**Every Evening** (5 minutes):
1. Run data analysis script
2. Update progress tracking
3. Note any anomalies

### Weekly Tasks

**Every Monday**:
1. Generate weekly summary report
2. Calculate weekly cost
3. Project Phase 2 readiness date
4. Update stakeholders

---

## 5. Alert Configuration

### Sentry Alerts

**Already Configured**:
- ✅ LLM Planner errors logged to Sentry
- ✅ Canary SLO breaches sent to Sentry

**To Add**:
- ⚠️ OpenAI 429 errors (quota exceeded)
- ⚠️ High cost alerts (> $5/day Staging)
- ⚠️ Low success rate (< 95%)

### Webhook Alerts (Optional)

**Slack Integration** (if available):
```python
# In canary_alerting.py
webhook_url = os.getenv('SLACK_WEBHOOK_URL')
alerting = create_canary_alerting(
    redis_client=redis,
    enabled=True,
    sentry_dsn=os.getenv('SENTRY_DSN'),
    webhook_url=webhook_url
)
```

**Slack Message Format**:
```
🚨 Canary Alert: P95 Latency Breach

P95 latency exceeded: 35000ms > 30000ms
Window: Last 15 minutes
Total tasks: 12

View dashboard: [link]
```

---

## 6. Implementation Checklist

### Week 1-2 (Immediate Actions)

- [ ] Create monitoring tools directory
- [ ] Implement canary dashboard script
- [ ] Implement data analysis script
- [ ] Enhance LLM Planner to log token usage and cost
- [ ] Set up daily monitoring routine
- [ ] Document monitoring procedures
- [ ] Test all monitoring scripts

### Week 3 (Before Phase 2)

- [ ] Review 7-14 days of data
- [ ] Generate Phase 2 readiness report
- [ ] Implement Circuit Breaker (if Phase 2 approved)
- [ ] Set up automated alerting
- [ ] Create monitoring dashboard (Grafana or web)

---

## 7. Success Criteria

**Phase 1 Monitoring is successful if**:

1. ✅ **Data Collection**: 50+ LLM Planner calls recorded
2. ✅ **Success Rate**: > 95% success rate
3. ✅ **Cost**: Average cost < $0.05 per call
4. ✅ **Latency**: P95 < 30 seconds
5. ✅ **No Incidents**: No quota errors or service disruptions
6. ✅ **Documentation**: All monitoring procedures documented

**If all criteria met**: ✅ Ready for Phase 2

**If any criteria not met**: ⚠️ Extend monitoring period or investigate issues

---

## 8. Next Steps

1. **Implement monitoring scripts** (30 minutes)
2. **Test monitoring scripts** (15 minutes)
3. **Set up daily monitoring routine** (5 minutes/day)
4. **Collect data for 7-14 days**
5. **Evaluate Phase 2 readiness** (Week 3)

---

**Document Status**: Draft  
**Last Updated**: 2025-11-24  
**Next Review**: 2025-12-01 (after 7 days of monitoring)

---

## 9. Planner Statistics CLI Tool

**Tool**: `tools/monitoring/view_planner_stats.py`

**Purpose**: View statistics from `planner_runs.jsonl` file for Phase 1 data collection monitoring.

**Features**:
- Display total planner runs, timeline, and planning time statistics
- Show plan step distribution and planner type distribution
- View recent entries with details
- Filter by goal substring (e.g., "[Phase1-Test]")
- Works on local, staging, and production environments

**Usage**:

**Local Environment**:
```bash
cd /home/ubuntu/repos/morningai
source .venv/bin/activate
python tools/monitoring/view_planner_stats.py
python tools/monitoring/view_planner_stats.py --last 10
python tools/monitoring/view_planner_stats.py --filter "[Phase1-Test]"
```

**Staging Environment (Render Shell)**:
```bash
cd /opt/render/project/src
python tools/monitoring/view_planner_stats.py
python tools/monitoring/view_planner_stats.py --last 20
```

**Custom File Path**:
```bash
python tools/monitoring/view_planner_stats.py --file /path/to/planner_runs.jsonl
```

**Environment Variable Override**:
```bash
PLANNER_EVENTS_FILE=/custom/path/planner_runs.jsonl python tools/monitoring/view_planner_stats.py
```

**Output Example**:
```
======================================================================
Planner Statistics
======================================================================

File: /opt/render/project/src/tools/agent_eval/data/planner_runs.jsonl

📊 Total Planner Runs: 30

📅 Timeline
  First: 2025-11-26 10:00:00 UTC
  Last:  2025-11-26 11:20:00 UTC
  Duration: 1.3 hours
  Rate: 23.08 runs/hour

⏱️  Planning Time
  Min:        8.39s
  Median:    11.50s
  Mean:      11.23s
  P95:       14.94s
  Max:       15.00s
  Status: ✅ Acceptable (< 30s target)

📋 Plan Steps Distribution
  5 steps:   3 ( 42.9%) ████████
  6 steps:   3 ( 42.9%) ████████
  7 steps:   1 ( 14.3%) ██

🤖 Planner Type Distribution
  llm:  30 (100.0%)

📝 Task Type Distribution (Top 10)
  code_generation:   10 ( 33.3%)
  bug_fix:            8 ( 26.7%)
  refactoring:        7 ( 23.3%)
  test_generation:    5 ( 16.7%)

======================================================================
```

**Testing**:
```bash
cd /home/ubuntu/repos/morningai
source .venv/bin/activate
python -m pytest tools/monitoring/tests/test_view_planner_stats.py -v
```
