# Sentry Alert Rules（初版）
## Error Alert（必備）
- Scope: env=prod
- Condition: Any error
- Threshold: ≥ 1 event in 5 minutes
- Actions: Slack #oncall / Email on-call

## Performance Alert（可選）
- Scope: env=prod
- Condition: p95(latency) > 1000ms for 5m
- Actions: Slack #oncall

> 工程在 Sentry 後台建立規則後，請回填：
- Error Rule URL: <填入>
- Performance Rule URL: <填入>
- 通知管道: <填入>
