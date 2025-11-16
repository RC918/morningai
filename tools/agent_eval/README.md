# Agent Evaluation Harness

This directory contains the evaluation harness for measuring AI agent performance metrics.

## Purpose

The evaluation harness provides:
- **Measurable success rates** for LLM Planner, Code Generator, and overall Agent performance
- **Standardized test dataset** with known expected outcomes
- **Automated evaluation** that can run in CI
- **Metrics dashboard** integration with Owner Console

## Structure

```
tools/agent_eval/
├── README.md              # This file
├── dataset.jsonl          # Test cases with expected outcomes
├── runner.py              # Evaluation runner
├── metrics.py             # Success rate calculation
├── __init__.py            # Package initialization
└── results/               # Evaluation results (gitignored)
```

## Quick Start

### 1. Run Evaluation

```bash
cd tools/agent_eval
python runner.py --dataset dataset.jsonl --output results/latest.json
```

### 2. View Metrics

```bash
python metrics.py --results results/latest.json
```

### 3. Add to CI

```yaml
# .github/workflows/agent-evaluation.yml
name: Agent Evaluation
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run evaluation
        run: |
          cd tools/agent_eval
          python runner.py --dataset dataset.jsonl --output results/weekly.json
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: evaluation-results
          path: tools/agent_eval/results/weekly.json
```

## Dataset Format

Each line in `dataset.jsonl` is a JSON object with:

```json
{
  "id": "task-001",
  "type": "bug_fix",
  "description": "Fix authentication timeout issue",
  "input": {
    "issue_url": "https://github.com/RC918/morningai/issues/123",
    "repo": "RC918/morningai"
  },
  "expected_outcome": {
    "pr_created": true,
    "ci_passed": true,
    "issue_closed": true,
    "correctness_criteria": [
      "Session timeout increased to 30 minutes",
      "Tests added for timeout behavior",
      "No breaking changes"
    ]
  },
  "difficulty": "medium",
  "estimated_time_minutes": 30
}
```

## Metrics

### 1. Task Completion Rate

Percentage of tasks where the agent:
- Created a PR
- PR was not empty
- No critical errors occurred

**Formula:** `completed_tasks / total_tasks * 100`

### 2. Correctness Rate

Percentage of completed tasks where:
- CI checks passed
- All correctness criteria met
- Human review approved (if available)

**Formula:** `correct_tasks / completed_tasks * 100`

### 3. CI Pass Rate

Percentage of PRs where CI checks passed on first attempt.

**Formula:** `ci_passed_first_attempt / prs_created * 100`

### 4. Time Efficiency

Average time to completion vs estimated time.

**Formula:** `avg(actual_time / estimated_time) * 100`

### 5. Overall Success Rate

Combined metric weighing all factors.

**Formula:** `(completion_rate * 0.3) + (correctness_rate * 0.4) + (ci_pass_rate * 0.2) + (time_efficiency * 0.1)`

## Integration with Owner Console

Evaluation results are automatically synced to the Owner Console dashboard:

1. **Metrics Dashboard**: Real-time success rates
2. **Trend Charts**: Historical performance over time
3. **Task Breakdown**: Success rates by task type
4. **Failure Analysis**: Common failure patterns

## Adding New Test Cases

1. Create a new task in `dataset.jsonl`:
   ```json
   {
     "id": "task-XXX",
     "type": "feature|bug_fix|refactor|test",
     "description": "Clear description",
     "input": {...},
     "expected_outcome": {...},
     "difficulty": "easy|medium|hard",
     "estimated_time_minutes": 15-120
   }
   ```

2. Run evaluation to validate:
   ```bash
   python runner.py --dataset dataset.jsonl --task-id task-XXX
   ```

3. Review results and adjust criteria if needed

## Troubleshooting

### Evaluation Fails to Start

- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify GitHub token is set: `echo $GITHUB_TOKEN`
- Check Redis connection: `redis-cli ping`

### Low Success Rates

- Review failure logs in `results/latest.json`
- Check common failure patterns
- Adjust agent prompts or tools
- Add more training examples

### CI Timeout

- Reduce dataset size for CI runs
- Use `--max-tasks 10` flag
- Increase timeout in workflow file

## Future Enhancements

- [ ] Add support for multi-agent evaluation
- [ ] Implement A/B testing for prompt variations
- [ ] Add cost tracking per task
- [ ] Generate automated improvement suggestions
- [ ] Add human-in-the-loop validation UI

## References

- [Strategic Roadmap Reality Comparison](../../docs/STRATEGIC_ROADMAP_REALITY_COMPARE_2025_11_16.md)
- [CTO Strategic Plan](../../CTO_STRATEGIC_PLAN_MVP_TO_WORLD_CLASS.md)
- [Owner Console Phase Plan](../../docs/OWNER_CONSOLE_PHASE_PLAN.md)
