# Bug Fix Workflow Guide

## Overview

The Bug Fix Workflow automates the complete process of fixing bugs from GitHub Issues to Pull Requests. It combines Knowledge Graph-based pattern learning, LLM-powered code generation, and Human-in-the-Loop (HITL) approval to deliver high-quality automated bug fixes.

**Phase**: Phase 1 Week 6  
**Status**: ✅ Implemented  
**Architecture**: LangGraph workflow with 8 stages

---

## Architecture

### Workflow Stages

```
┌─────────────────┐
│  Parse Issue    │  Extract bug info from GitHub Issue
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Reproduce Bug   │  Run tests to confirm bug exists
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Analyze Root    │  Use LSP + Knowledge Graph + LLM
│    Cause        │  to identify root cause
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate Fixes  │  Use learned patterns + LLM
│                 │  to generate fix strategies
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Apply Fix     │  Apply code changes to files
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Run Tests     │  Verify fix resolves the bug
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Create PR     │  Create Pull Request on GitHub
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Request HITL    │  Request human approval
│   Approval      │  via Telegram or Console
└─────────────────┘
```

### Component Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    BugFixWorkflow                         │
│                   (LangGraph Workflow)                    │
└──────────┬────────────────────────────────────┬──────────┘
           │                                    │
           ▼                                    ▼
┌──────────────────────┐          ┌──────────────────────┐
│    DevAgent          │          │  Pattern Learner     │
│  - Git Tool          │          │  - Bug Patterns      │
│  - Filesystem Tool   │          │  - Fix Patterns      │
│  - IDE Tool          │          │  - History Tracking  │
│  - Test Tool         │          └──────────┬───────────┘
│  - LLM               │                     │
└──────────┬───────────┘                     │
           │                                 │
           ▼                                 ▼
┌──────────────────────┐          ┌──────────────────────┐
│ Knowledge Graph      │◄─────────│    PostgreSQL        │
│  Manager             │          │  + pgvector          │
│  - Embeddings        │          │  - code_patterns     │
│  - Search            │          │  - bug_fix_history   │
└──────────────────────┘          └──────────────────────┘
           │
           ▼
┌──────────────────────┐
│  HITL Approval       │
│  System              │
│  - Telegram Bot      │
│  - Console UI        │
└──────────────────────┘
```

---

## Setup

### Prerequisites

1. **Database**: PostgreSQL with pgvector extension
2. **Python**: Python 3.12+ with required packages
3. **Credentials**: OpenAI API key, Supabase credentials

### Installation

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

Required packages are already in `requirements.txt`:
- `langgraph` - Workflow orchestration
- `langchain-core` - Core LangChain functionality
- `openai` - LLM API
- `pgvector` - Vector operations
- `psycopg2-binary` - PostgreSQL driver

2. **Run Migrations**:
```bash
cd agents/dev_agent/migrations
python run_migration.py
```

This creates:
- Knowledge Graph tables (`code_embeddings`, `code_patterns`, etc.)
- Bug Fix History table (`bug_fix_history`)
- Indexes and RLS policies

3. **Configure Environment**:
```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_DB_PASSWORD="your-password"
export OPENAI_API_KEY="sk-..."
export TELEGRAM_BOT_TOKEN="123456:ABC..."  # Optional
export TELEGRAM_ADMIN_CHAT_ID="987654321"  # Optional
```

---

## Usage

### Basic Usage

```python
from agents.dev_agent.workflows.bug_fix_workflow import BugFixWorkflow
from agents.dev_agent.dev_agent_wrapper import DevAgent

agent = DevAgent()
workflow = BugFixWorkflow(agent)

github_issue = {
    "number": 123,
    "title": "Fix: TypeError in user_service.py",
    "body": """
When calling get_user(None), a TypeError is raised.

Error: 'NoneType' object has no attribute 'id'

File: agents/user_service.py
Line: 45
"""
}

result = await workflow.execute(github_issue)

print(f"Issue ID: {result['issue_id']}")
print(f"Bug Type: {result['bug_type']}")
print(f"Root Cause: {result['root_cause']}")
print(f"Fix Strategy: {result['fix_strategy']}")
print(f"PR URL: {result['pr_url']}")
print(f"Success: {result['test_results']['success']}")
```

### Advanced Usage

#### Custom Configuration

```python
agent = DevAgent(
    supabase_url="https://custom.supabase.co",
    supabase_password="custom-password",
    openai_api_key="sk-custom...",
    telegram_bot_token="custom-bot-token",
    admin_chat_id="custom-chat-id"
)
```

#### Pattern Learning

```python
agent.pattern_learner.learn_bug_pattern(
    bug_description="Index out of range when accessing list",
    root_cause="List bounds not checked before access",
    bug_type="index_error",
    affected_code="items[index]"
)

agent.pattern_learner.learn_fix_pattern(
    bug_description="Index out of range",
    fix_strategy="Add bounds check before accessing list",
    fix_code="if 0 <= index < len(items): return items[index]",
    success=True
)
```

#### Querying History

```python
history = agent.pattern_learner.get_bug_fix_history(
    bug_type="type_error",
    success_only=True,
    limit=10
)

for record in history['data']['records']:
    print(f"Issue #{record['issue_number']}: {record['issue_title']}")
    print(f"Success: {record['success']}")
    print(f"Execution Time: {record['execution_time_seconds']}s")
```

---

## Pattern Learning

### How It Works

The workflow learns from every bug fix attempt:

1. **Bug Patterns**: Extracted from issue descriptions and error messages
   - Stored in `code_patterns` table with `pattern_type='bug_pattern'`
   - Includes bug type, description, root cause
   - Frequency and confidence tracked

2. **Fix Patterns**: Learned from successful fixes
   - Stored in `code_patterns` table with `pattern_type='fix_pattern'`
   - Includes fix strategy, code changes
   - Success rate calculated and updated

3. **History Tracking**: All attempts recorded
   - Stored in `bug_fix_history` table
   - Includes execution time, test results, patterns used
   - Used for analytics and improvement

### Pattern Matching

When processing a new bug:

1. **Similar Bugs**: Query `code_patterns` for similar bug patterns
   - Match by bug type, description similarity
   - Rank by frequency and confidence

2. **Successful Fixes**: Query `code_patterns` for fix patterns
   - Filter by success rate (>70%)
   - Rank by confidence and frequency

3. **Context Integration**: Combine with LLM analysis
   - LLM generates fix based on similar patterns
   - Patterns guide LLM towards proven solutions

---

## HITL Integration

### Telegram Bot

If `TELEGRAM_BOT_TOKEN` configured:

1. **Approval Request**: Sent when PR is created
2. **Message Format**:
   ```
   🐛 Bug Fix PR Ready

   Issue: #123
   Title: Fix TypeError in user_service
   Bug Type: type_error
   Test Status: ✅ Passed

   PR: https://github.com/owner/repo/pull/456

   Approve? Reply: /approve <request_id>
   ```

3. **Commands**:
   - `/approve <request_id>` - Approve fix
   - `/reject <request_id>` - Reject fix
   - `/status` - Check pending approvals

### Console UI

Fallback if Telegram not configured:

1. **Console Notification**: Logged to stdout
2. **API Endpoint**: `/api/approvals/pending`
3. **Manual Approval**: Via API or direct database update

---

## Testing

### Unit Tests

```bash
pytest agents/dev_agent/tests/test_bug_fix_pattern_learner.py -v
```

Tests:
- Pattern learning (bug and fix)
- Pattern querying
- History recording
- Error handling

### E2E Tests

```bash
pytest agents/dev_agent/tests/test_bug_fix_workflow_e2e.py -v
```

Tests:
- Full workflow execution
- Mocked workflow (no external services)
- Individual stage testing

### Integration Tests

Requires real credentials:

```bash
export OPENAI_API_KEY="sk-..."
export SUPABASE_URL="https://..."
export SUPABASE_DB_PASSWORD="..."

pytest agents/dev_agent/tests/test_bug_fix_workflow_e2e.py::test_bug_fix_workflow_full_e2e -v
```

---

## Troubleshooting

### Common Issues

**1. Migration Fails**

```
Error: relation "code_patterns" already exists
```

Solution: Tables already exist. Skip migration or drop tables first.

**2. LLM Not Generating Fixes**

```
Warning: OpenAI API key not configured
```

Solution: Set `OPENAI_API_KEY` environment variable.

**3. Tests Not Running**

```
Error: pytest not found
```

Solution: Install test dependencies: `pip install pytest pytest-asyncio`

**4. Pattern Storage Failing**

```
Error: Database not configured
```

Solution: Set `SUPABASE_URL` and `SUPABASE_DB_PASSWORD`.

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This shows:
- Stage transitions
- Database queries
- LLM prompts/responses
- Pattern matches

---

## Performance

### Expected Metrics

| Metric | Target | Notes |
|--------|--------|-------|
| Parse Issue | <1s | Regex-based extraction |
| Reproduce Bug | 30-60s | Depends on test suite |
| Analyze Root Cause | 5-10s | LLM + pattern query |
| Generate Fixes | 10-15s | LLM generation |
| Apply Fix | <5s | File operations |
| Run Tests | 30-60s | Depends on test suite |
| Create PR | 5-10s | Git operations |
| Total | 2-3 min | For typical bug |

### Optimization Tips

1. **Cache LLM Responses**: Reuse for similar bugs
2. **Parallel Pattern Query**: Query bug and fix patterns concurrently
3. **Incremental Testing**: Run only affected tests
4. **Pattern Pruning**: Remove low-confidence patterns

---

## Best Practices

### Issue Format

Provide clear issue descriptions:

```markdown
## Bug Description
TypeError when calling get_user(None)

## Error Message
'NoneType' object has no attribute 'id'

## Location
File: agents/user_service.py
Line: 45

## Steps to Reproduce
1. Call get_user(None)
2. Observe error
```

### Pattern Curation

Regularly review patterns:

```sql
-- Low success rate patterns
SELECT * FROM code_patterns 
WHERE pattern_type = 'fix_pattern' 
AND confidence_score < 0.5;

-- Unused patterns
SELECT * FROM code_patterns
WHERE frequency < 3
AND created_at < NOW() - INTERVAL '30 days';
```

### Monitoring

Track workflow metrics:

```sql
-- Success rate by bug type
SELECT bug_type, 
       COUNT(*) as total,
       SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
       AVG(execution_time_seconds) as avg_time
FROM bug_fix_history
GROUP BY bug_type;

-- Recent failures
SELECT issue_number, issue_title, bug_type, error
FROM bug_fix_history
WHERE success = false
ORDER BY created_at DESC
LIMIT 10;
```

---

## Future Enhancements

### Planned Features

1. **Multi-language Support**: JavaScript, TypeScript, Go
2. **Advanced Root Cause Analysis**: AST-based analysis
3. **Automated Test Generation**: Generate tests for fixes
4. **Fix Validation**: Static analysis before applying
5. **Rollback Mechanism**: Auto-rollback failed fixes

### Experimental Features

1. **Reinforcement Learning**: Learn from approval feedback
2. **Ensemble Fixes**: Generate multiple fix candidates
3. **Interactive Debugging**: Step-through debugging
4. **Visual Diff UI**: Rich PR preview

---

## Contributing

See main [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

Bug Fix Workflow specific:
- Add new pattern extractors in `BugFixPatternLearner`
- Extend workflow stages in `BugFixWorkflow`
- Add tests for new features
- Update this guide with examples

---

## References

- [Knowledge Graph Migration Guide](knowledge_graph_migration_guide.md)
- [Dev Agent README](../agents/dev_agent/README.md)
- [HITL Approval System](../hitl_approval_system.py)
- [LangGraph Documentation](https://github.com/langchain-ai/langgraph)

---

**Last Updated**: October 17, 2025  
**Version**: 1.0.0  
**Status**: Production Ready
