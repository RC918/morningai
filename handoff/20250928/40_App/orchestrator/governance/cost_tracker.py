"""Cost Tracking System - Token and USD budget monitoring"""
import os
import redis
import yaml
from datetime import date, datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


class CostBudgetExceeded(Exception):
    """Raised when cost budget is exceeded"""
    pass


@dataclass
class CostMetrics:
    """Cost metrics for a time period"""
    tokens: int
    usd: float
    requests: int


class CostTracker:
    """Track and enforce cost budgets"""
    
    def __init__(self, redis_url: Optional[str] = None, policies_path: Optional[str] = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            self.redis.ping()
        except Exception as e:
            print(f"[CostTracker] Redis unavailable: {e}")
            self.redis = None
        
        if policies_path is None:
            policies_path = os.path.join(
                os.path.dirname(__file__),
                '../../../../config/policies.yaml'
            )
        
        self.policies = self._load_policies(policies_path)
        self.budgets = self.policies.get('cost_budget', {})
    
    def _load_policies(self, path: str) -> Dict:
        """Load policies from YAML"""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"[CostTracker] Error loading policies: {e}")
            return {}
    
    def track_usage(
        self,
        trace_id: str,
        tokens: int,
        cost_usd: float,
        model: str = "gpt-4",
        operation: str = "completion"
    ) -> None:
        """Track token and cost usage"""
        if not self.redis:
            print(f"[CostTracker] Redis unavailable, skipping tracking")
            return
        
        timestamp = datetime.now().isoformat()
        
        daily_key = f"cost:daily:{date.today()}"
        self.redis.hincrby(daily_key, "tokens", tokens)
        self.redis.hincrbyfloat(daily_key, "usd", cost_usd)
        self.redis.hincrby(daily_key, "requests", 1)
        self.redis.expire(daily_key, 86400 * 7)  # Keep for 7 days
        
        current_hour = datetime.now().strftime("%Y-%m-%d-%H")
        hourly_key = f"cost:hourly:{current_hour}"
        self.redis.hincrby(hourly_key, "tokens", tokens)
        self.redis.hincrbyfloat(hourly_key, "usd", cost_usd)
        self.redis.hincrby(hourly_key, "requests", 1)
        self.redis.expire(hourly_key, 3600 * 24)  # Keep for 24 hours
        
        task_key = f"cost:task:{trace_id}"
        self.redis.hincrby(task_key, "tokens", tokens)
        self.redis.hincrbyfloat(task_key, "usd", cost_usd)
        self.redis.hincrby(task_key, "requests", 1)
        self.redis.hset(task_key, "model", model)
        self.redis.hset(task_key, "operation", operation)
        self.redis.hset(task_key, "timestamp", timestamp)
        self.redis.expire(task_key, 86400 * 30)  # Keep for 30 days
        
        print(f"[CostTracker] Tracked: {tokens} tokens, ${cost_usd:.4f} for {trace_id}")
    
    def check_budget(self, trace_id: str, period: str = "daily") -> Tuple[bool, CostMetrics, Dict]:
        """
        Check if budget is exceeded
        
        Args:
            trace_id: Task trace ID
            period: 'daily', 'hourly', or 'task'
        
        Returns:
            Tuple of (within_budget, current_metrics, budget_limits)
        """
        if not self.redis:
            return True, CostMetrics(0, 0.0, 0), {}
        
        if period == "daily":
            key = f"cost:daily:{date.today()}"
            budget = self.budgets.get('daily', {})
        elif period == "hourly":
            current_hour = datetime.now().strftime("%Y-%m-%d-%H")
            key = f"cost:hourly:{current_hour}"
            budget = self.budgets.get('hourly', {})
        elif period == "task":
            key = f"cost:task:{trace_id}"
            budget = self.budgets.get('per_task', {})
        else:
            raise ValueError(f"Invalid period: {period}")
        
        tokens = int(self.redis.hget(key, "tokens") or 0)
        usd = float(self.redis.hget(key, "usd") or 0.0)
        requests = int(self.redis.hget(key, "requests") or 0)
        
        metrics = CostMetrics(tokens=tokens, usd=usd, requests=requests)
        
        max_tokens = budget.get('max_tokens', float('inf'))
        max_usd = budget.get('max_usd', float('inf'))
        
        within_budget = tokens <= max_tokens and usd <= max_usd
        
        return within_budget, metrics, budget
    
    def enforce_budget(self, trace_id: str, period: str = "daily") -> None:
        """Enforce budget limits, raise exception if exceeded"""
        within_budget, metrics, budget = self.check_budget(trace_id, period)
        
        if not within_budget:
            max_tokens = budget.get('max_tokens', 0)
            max_usd = budget.get('max_usd', 0.0)
            
            raise CostBudgetExceeded(
                f"{period.capitalize()} budget exceeded: "
                f"tokens={metrics.tokens}/{max_tokens}, "
                f"usd=${metrics.usd:.2f}/${max_usd:.2f}"
            )
    
    def get_budget_status(self, trace_id: str, period: str = "daily") -> Dict:
        """Get detailed budget status"""
        within_budget, metrics, budget = self.check_budget(trace_id, period)
        
        max_tokens = budget.get('max_tokens', 0)
        max_usd = budget.get('max_usd', 0.0)
        
        token_percent = (metrics.tokens / max_tokens * 100) if max_tokens > 0 else 0
        usd_percent = (metrics.usd / max_usd * 100) if max_usd > 0 else 0
        
        alert_thresholds = self.budgets.get('alert_thresholds', {})
        warning_percent = alert_thresholds.get('warning_percent', 80)
        critical_percent = alert_thresholds.get('critical_percent', 95)
        
        max_percent = max(token_percent, usd_percent)
        if max_percent >= critical_percent:
            alert_level = "critical"
        elif max_percent >= warning_percent:
            alert_level = "warning"
        else:
            alert_level = "ok"
        
        return {
            'period': period,
            'within_budget': within_budget,
            'alert_level': alert_level,
            'usage': {
                'tokens': metrics.tokens,
                'usd': metrics.usd,
                'requests': metrics.requests
            },
            'limits': {
                'tokens': max_tokens,
                'usd': max_usd
            },
            'percentages': {
                'tokens': round(token_percent, 2),
                'usd': round(usd_percent, 2)
            }
        }
    
    def get_cost_summary(self, trace_id: str) -> Dict:
        """Get comprehensive cost summary for all periods"""
        return {
            'task': self.get_budget_status(trace_id, 'task'),
            'hourly': self.get_budget_status(trace_id, 'hourly'),
            'daily': self.get_budget_status(trace_id, 'daily')
        }
    
    def estimate_cost(self, tokens: int, model: str = "gpt-4") -> float:
        """Estimate cost in USD for given tokens"""
        pricing = {
            'gpt-4': 0.03,  # Input
            'gpt-4-output': 0.06,  # Output
            'gpt-3.5-turbo': 0.0015,  # Input
            'gpt-3.5-turbo-output': 0.002,  # Output
        }
        
        rate = pricing.get(model, 0.03)
        return (tokens / 1000) * rate
    
    def reset_budget(self, period: str = "daily") -> None:
        """Reset budget for testing purposes"""
        if not self.redis:
            return
        
        if period == "daily":
            key = f"cost:daily:{date.today()}"
        elif period == "hourly":
            current_hour = datetime.now().strftime("%Y-%m-%d-%H")
            key = f"cost:hourly:{current_hour}"
        else:
            return
        
        self.redis.delete(key)
        print(f"[CostTracker] Reset {period} budget")


_cost_tracker = None


def get_cost_tracker() -> CostTracker:
    """Get or create global CostTracker instance"""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker
