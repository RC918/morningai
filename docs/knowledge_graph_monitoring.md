# Knowledge Graph Monitoring Operations Guide

This guide covers monitoring, alerting, and troubleshooting for the Knowledge Graph system in production.

---

## Monitoring Overview

### Key Metrics to Monitor

| Metric | Target | Alert Threshold | Critical Threshold |
|--------|--------|----------------|-------------------|
| Query P95 Latency | <50ms | >100ms | >200ms |
| Embedding Generation P95 | <200ms | >500ms | >1000ms |
| Cache Hit Rate | >80% | <60% | <40% |
| Daily API Cost | Variable | >80% of limit | 100% of limit |
| Index Size Growth | - | >50% month | >100% month |
| Error Rate | <1% | >5% | >10% |

---

## 1. Query Performance Monitoring

### Setup: Enable Query Logging

```sql
-- Enable slow query logging (queries >50ms)
ALTER DATABASE your_db SET log_min_duration_statement = 50;

-- Enable execution plan logging
ALTER DATABASE your_db SET auto_explain.log_min_duration = 100;
ALTER DATABASE your_db SET auto_explain.log_analyze = true;
```

### Query 1: Identify Slow Queries

```sql
SELECT 
    query,
    calls,
    total_exec_time / 1000 as total_time_sec,
    mean_exec_time / 1000 as mean_time_ms,
    max_exec_time / 1000 as max_time_ms,
    stddev_exec_time / 1000 as stddev_ms
FROM pg_stat_statements
WHERE query LIKE '%code_embeddings%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

**Interpretation**:
- `mean_time_ms > 50`: Query may benefit from optimization
- `max_time_ms > 200`: Investigate outliers
- `stddev_ms > 100`: Inconsistent performance

### Query 2: Monitor HNSW Index Performance

```sql
-- Check if index is being used
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as times_used,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE indexname LIKE '%embedding%'
ORDER BY idx_scan DESC;
```

**Red Flags**:
- `idx_scan = 0`: Index not being used
- `idx_tup_read / idx_tup_fetch > 100`: Index inefficient

### Automation: Set Up Monitoring Script

Save as `scripts/monitor_query_performance.sh`:

```bash
#!/bin/bash

# Monitor Knowledge Graph query performance
DB_URL=$SUPABASE_URL

while true; do
    echo "=== Query Performance Check $(date) ===" 
    
    # Get P95 latency
    psql $DB_URL -c "
        SELECT 
            'P95 Latency' as metric,
            percentile_cont(0.95) WITHIN GROUP (ORDER BY mean_exec_time) / 1000 as value_ms
        FROM pg_stat_statements
        WHERE query LIKE '%code_embeddings%' AND query LIKE '%ORDER BY%distance%';
    "
    
    # Get index usage
    psql $DB_URL -c "
        SELECT 
            indexname,
            idx_scan as scans_last_period
        FROM pg_stat_user_indexes
        WHERE indexname LIKE '%embedding%';
    "
    
    echo ""
    sleep 300  # Run every 5 minutes
done
```

Run with:
```bash
nohup bash scripts/monitor_query_performance.sh > logs/kg_monitoring.log 2>&1 &
```

---

## 2. Memory Usage Monitoring

### Query 1: Check Table and Index Sizes

```sql
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - 
                   pg_relation_size(schemaname||'.'||tablename)) AS indexes_size
FROM pg_tables
WHERE tablename LIKE 'code_%'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Alert Thresholds**:
- Total size >10GB: Review data retention policy
- Indexes > 3x table size: Check for bloat

### Query 2: Monitor Connection Pool Usage

```python
# Add to application monitoring
def monitor_db_pool():
    """Monitor database connection pool"""
    if hasattr(kg_manager, 'db_pool') and kg_manager.db_pool:
        pool = kg_manager.db_pool
        print(f"DB Pool Status:")
        print(f"  Min connections: {pool.minconn}")
        print(f"  Max connections: {pool.maxconn}")
        print(f"  Closed connections: {pool.closed}")
        
        # Alert if pool exhausted
        # Note: psycopg2 doesn't expose current usage directly
        # Use database query instead
```

```sql
-- Check active connections
SELECT 
    count(*) as active_connections,
    state,
    wait_event_type
FROM pg_stat_activity
WHERE datname = 'your_database'
GROUP BY state, wait_event_type;
```

### Query 3: Application Memory Usage

```python
# Add to application code
import psutil
import logging

logger = logging.getLogger(__name__)

def monitor_memory_usage():
    """Monitor application memory usage"""
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    memory_percent = process.memory_percent()
    
    logger.info(f"Memory usage: {memory_mb:.1f}MB ({memory_percent:.1f}%)")
    
    # Alert if > 1GB
    if memory_mb > 1024:
        logger.warning(f"High memory usage: {memory_mb:.1f}MB")
    
    # Critical if > 2GB
    if memory_mb > 2048:
        logger.error(f"Critical memory usage: {memory_mb:.1f}MB")
    
    return memory_mb

# Call periodically
```

---

## 3. API Cost Monitoring

### Check Daily Costs

```bash
# Manual check
python scripts/kg_cost_report.py --check-limit

# Output example:
# 💰 Daily Cost Limit Check:
#    Current Usage: $0.0234 USD
#    Daily Limit: $5.0000 USD
#    Remaining: $4.9766 USD
#    Usage: 0.5%
```

### Automation: Cost Alert Script

Save as `scripts/alert_high_cost.sh`:

```bash
#!/bin/bash

# Alert if daily cost exceeds threshold
MAX_COST=${OPENAI_MAX_DAILY_COST:-5.0}
WARNING_THRESHOLD=0.8  # 80%

# Get current cost
COST=$(python scripts/kg_cost_report.py --check-limit 2>&1 | grep "Current Usage" | awk '{print $3}')

if [ ! -z "$COST" ]; then
    COST_NUM=$(echo $COST | sed 's/\$//g')
    WARNING_LEVEL=$(echo "$MAX_COST * $WARNING_THRESHOLD" | bc)
    
    # Compare (using bc for floating point)
    if (( $(echo "$COST_NUM >= $MAX_COST" | bc -l) )); then
        echo "🚨 CRITICAL: Daily cost limit exceeded! ($COST_NUM >= $MAX_COST)"
        # Send alert (Slack, email, etc.)
    elif (( $(echo "$COST_NUM >= $WARNING_LEVEL" | bc -l) )); then
        echo "⚠️  WARNING: Approaching daily cost limit ($COST_NUM >= $WARNING_LEVEL)"
        # Send warning
    else
        echo "✓ Cost within normal range ($COST_NUM < $WARNING_LEVEL)"
    fi
fi
```

### Cron Job Setup

```bash
# Add to crontab
crontab -e

# Check cost every hour
0 * * * * /path/to/scripts/alert_high_cost.sh >> /var/log/kg_cost_alerts.log 2>&1

# Daily cost report at 9 AM
0 9 * * * python /path/to/scripts/kg_cost_report.py --daily | mail -s "KG Daily Cost Report" admin@example.com
```

---

## 4. Cache Performance Monitoring

### Query 1: Cache Statistics

```python
# Add to monitoring dashboard
from agents.dev_agent.knowledge_graph import get_embeddings_cache

def monitor_cache():
    cache = get_embeddings_cache()
    
    if not cache.enabled:
        print("⚠️  Cache not enabled")
        return
    
    stats = cache.get_stats(days=1)
    
    if stats.get('summary'):
        summary = stats['summary']
        hit_rate = summary.get('cache_hit_rate', 0)
        
        print(f"Cache Performance (Today):")
        print(f"  Hit Rate: {hit_rate:.1f}%")
        print(f"  Total Calls: {summary.get('total_calls', 0):,}")
        print(f"  Cache Hits: {summary.get('cache_hits', 0):,}")
        print(f"  Cache Misses: {summary.get('cache_misses', 0):,}")
        
        # Alert if hit rate low
        if hit_rate < 60:
            print(f"⚠️  WARNING: Low cache hit rate ({hit_rate:.1f}%)")
        elif hit_rate < 40:
            print(f"🚨 CRITICAL: Very low cache hit rate ({hit_rate:.1f}%)")

# Run periodically
```

### Query 2: Redis Connection Health

```python
# Add health check
def check_redis_health():
    cache = get_embeddings_cache()
    health = cache.health_check()
    
    if health.get('success'):
        print("✓ Redis cache healthy")
    else:
        print(f"❌ Redis cache unhealthy: {health.get('error')}")
    
    return health.get('success', False)
```

---

## 5. Error Rate Monitoring

### Application Logging

```python
# Enhanced error logging
import logging
from datetime import datetime

logger = logging.getLogger('knowledge_graph')

class ErrorRateMonitor:
    def __init__(self, window_minutes=60):
        self.window_minutes = window_minutes
        self.errors = []
    
    def log_error(self, error_type, message):
        """Log error with timestamp"""
        self.errors.append({
            'timestamp': datetime.now(),
            'type': error_type,
            'message': message
        })
        
        # Clean old errors
        cutoff = datetime.now() - timedelta(minutes=self.window_minutes)
        self.errors = [e for e in self.errors if e['timestamp'] > cutoff]
        
        logger.error(f"[{error_type}] {message}")
    
    def get_error_rate(self):
        """Calculate error rate (errors per hour)"""
        return len(self.errors) * (60 / self.window_minutes)
    
    def check_threshold(self, threshold=10):
        """Check if error rate exceeds threshold"""
        rate = self.get_error_rate()
        if rate > threshold:
            logger.critical(f"High error rate: {rate:.1f} errors/hour")
            return True
        return False

# Usage
error_monitor = ErrorRateMonitor()

try:
    result = kg_manager.generate_embedding(code)
    if not result.get('success'):
        error_monitor.log_error('EMBEDDING_FAILED', result.get('error'))
except Exception as e:
    error_monitor.log_error('EXCEPTION', str(e))
```

### Database Error Tracking

```sql
-- Check PostgreSQL error log
SELECT 
    message,
    count(*) as occurrences,
    max(log_time) as last_seen
FROM pg_log
WHERE message LIKE '%code_embeddings%'
    AND log_time > now() - interval '1 hour'
GROUP BY message
ORDER BY occurrences DESC;
```

---

## 6. Alerting Setup

### Slack Webhook Integration

```python
# scripts/alert_to_slack.py
import requests
import os

SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')

def send_slack_alert(title, message, severity='warning'):
    """Send alert to Slack"""
    if not SLACK_WEBHOOK_URL:
        print("⚠️  SLACK_WEBHOOK_URL not configured")
        return
    
    emoji = {
        'info': ':information_source:',
        'warning': ':warning:',
        'critical': ':rotating_light:'
    }.get(severity, ':question:')
    
    payload = {
        'text': f"{emoji} *{title}*\n{message}"
    }
    
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send Slack alert: {e}")

# Usage examples
send_slack_alert(
    "High Query Latency",
    "P95 latency exceeded 100ms (current: 156ms)",
    severity='warning'
)

send_slack_alert(
    "Cost Limit Exceeded",
    f"Daily API cost reached ${daily_cost:.2f} (limit: ${limit:.2f})",
    severity='critical'
)
```

### Email Alerts

```python
# scripts/alert_to_email.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_alert(subject, body, to_email):
    """Send alert via email"""
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')
    
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")
```

---

## 7. Health Check Endpoint

### Add to Application

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health/knowledge-graph', methods=['GET'])
def kg_health_check():
    """Knowledge Graph system health check"""
    kg_manager = get_knowledge_graph_manager()
    cache = get_embeddings_cache()
    
    health = {
        'timestamp': datetime.now().isoformat(),
        'status': 'healthy',
        'checks': {}
    }
    
    # Check 1: Database connectivity
    try:
        db_health = kg_manager.health_check()
        health['checks']['database'] = {
            'status': 'pass' if db_health.get('success') else 'fail',
            'details': db_health.get('data', {})
        }
    except Exception as e:
        health['checks']['database'] = {
            'status': 'fail',
            'error': str(e)
        }
        health['status'] = 'unhealthy'
    
    # Check 2: Cache connectivity
    if cache and cache.enabled:
        cache_health = cache.health_check()
        health['checks']['cache'] = {
            'status': 'pass' if cache_health.get('success') else 'fail'
        }
    else:
        health['checks']['cache'] = {
            'status': 'warn',
            'message': 'Cache not enabled'
        }
    
    # Check 3: Recent query performance
    stats = cache.get_stats(days=1) if cache else {}
    if stats.get('summary'):
        hit_rate = stats['summary'].get('cache_hit_rate', 0)
        health['checks']['performance'] = {
            'status': 'pass' if hit_rate > 60 else 'warn',
            'cache_hit_rate': hit_rate,
            'total_calls': stats['summary'].get('total_calls', 0)
        }
    
    # Check 4: Cost limit status
    if kg_manager.max_daily_cost:
        daily_cost = stats.get('summary', {}).get('total_cost', 0)
        usage_pct = (daily_cost / kg_manager.max_daily_cost) * 100
        
        health['checks']['cost_limit'] = {
            'status': 'pass' if usage_pct < 100 else 'fail',
            'daily_cost': daily_cost,
            'limit': kg_manager.max_daily_cost,
            'usage_percent': usage_pct
        }
    
    # Set overall status
    if any(check['status'] == 'fail' for check in health['checks'].values()):
        health['status'] = 'unhealthy'
        return jsonify(health), 503
    elif any(check['status'] == 'warn' for check in health['checks'].values()):
        health['status'] = 'degraded'
        return jsonify(health), 200
    
    return jsonify(health), 200

# Monitor with:
# curl http://localhost:5000/health/knowledge-graph
```

---

## 8. Troubleshooting Runbook

### Issue: Slow Queries

**Symptoms**: P95 latency > 100ms

**Diagnosis**:
```sql
-- Check if index is being used
EXPLAIN (ANALYZE, BUFFERS) 
SELECT file_path, embedding <=> '[...]'::vector AS distance
FROM code_embeddings
ORDER BY distance
LIMIT 10;

-- Should see "Index Scan using hnsw"
```

**Solutions**:
1. Increase `ef_search`: `SET hnsw.ef_search = 100;`
2. Re-index with higher parameters
3. Check for database load: `SELECT * FROM pg_stat_activity;`

### Issue: High Memory Usage

**Symptoms**: Application using >2GB RAM

**Diagnosis**:
```python
import psutil
process = psutil.Process()
memory_mb = process.memory_info().rss / 1024 / 1024
print(f"Memory: {memory_mb:.1f}MB")
```

**Solutions**:
1. Reduce `max_workers` in code indexer
2. Process files in smaller batches
3. Clear caches: `cache.client.flushdb()` (if safe)

### Issue: Cost Limit Exceeded

**Symptoms**: Embedding generation returns cost limit error

**Diagnosis**:
```bash
python scripts/kg_cost_report.py --check-limit
```

**Solutions**:
1. Wait until tomorrow (limit resets)
2. Increase `OPENAI_MAX_DAILY_COST`
3. Investigate why usage is high:
   ```bash
   python scripts/kg_cost_report.py --daily
   # Check cache hit rate
   ```

---

## 9. Dashboard Setup (Optional)

### Grafana Dashboard JSON

```json
{
  "dashboard": {
    "title": "Knowledge Graph Monitoring",
    "panels": [
      {
        "title": "Query P95 Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(kg_query_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "targets": [
          {
            "expr": "rate(kg_cache_hits_total[5m]) / rate(kg_cache_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Daily API Cost",
        "targets": [
          {
            "expr": "kg_api_cost_usd_total"
          }
        ]
      }
    ]
  }
}
```

---

## Best Practices

### 1. Monitor Continuously

Set up automated monitoring - don't wait for issues to surface.

### 2. Set Up Alerts

Configure alerts for:
- Query P95 > 100ms
- Cache hit rate < 60%
- Daily cost > 80% of limit
- Error rate > 5%

### 3. Review Weekly

Weekly review of:
- Cost trends
- Performance trends
- Error patterns
- Index growth

### 4. Capacity Planning

Monthly review for:
- Projected data growth
- Cost projections
- Performance trends

### 5. Document Incidents

Keep runbook updated with:
- Issue descriptions
- Root causes
- Solutions applied
- Prevention measures

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-17  
**For**: Knowledge Graph System (Phase 1 Week 5)
