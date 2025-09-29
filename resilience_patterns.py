#!/usr/bin/env python3
"""
Resilience Patterns - Circuit Breaker, Bulkhead, and Retry Logic
Implements anti-fragile patterns for Morning AI system components
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import json

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    success_threshold: int = 3  # for half-open state
    timeout: float = 30.0  # request timeout

@dataclass
class CircuitBreakerMetrics:
    """Circuit breaker metrics"""
    total_requests: int = 0
    failed_requests: int = 0
    success_requests: int = 0
    last_failure_time: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0

class CircuitBreaker:
    """Circuit breaker implementation for external service calls"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self.logger = logging.getLogger(f"circuit_breaker.{name}")
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.logger.info(f"Circuit breaker {self.name} transitioning to HALF_OPEN")
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is OPEN")
                
        try:
            self.metrics.total_requests += 1
            
            result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.config.timeout)
            
            self._on_success()
            return result
            
        except asyncio.TimeoutError:
            self._on_failure()
            raise CircuitBreakerTimeoutError(f"Request to {self.name} timed out")
        except Exception as e:
            self._on_failure()
            raise
            
    def _on_success(self):
        """Handle successful request"""
        self.metrics.success_requests += 1
        self.metrics.consecutive_failures = 0
        self.metrics.consecutive_successes += 1
        
        if self.state == CircuitState.HALF_OPEN:
            if self.metrics.consecutive_successes >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.logger.info(f"Circuit breaker {self.name} reset to CLOSED")
                
    def _on_failure(self):
        """Handle failed request"""
        self.metrics.failed_requests += 1
        self.metrics.consecutive_failures += 1
        self.metrics.consecutive_successes = 0
        self.metrics.last_failure_time = datetime.now()
        
        if (self.state == CircuitState.CLOSED and 
            self.metrics.consecutive_failures >= self.config.failure_threshold):
            self.state = CircuitState.OPEN
            self.logger.warning(f"Circuit breaker {self.name} opened due to failures")
            
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if not self.metrics.last_failure_time:
            return True
            
        time_since_failure = datetime.now() - self.metrics.last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout
        
    def get_metrics(self) -> Dict:
        """Get circuit breaker metrics"""
        return {
            'name': self.name,
            'state': self.state.value,
            'total_requests': self.metrics.total_requests,
            'failed_requests': self.metrics.failed_requests,
            'success_requests': self.metrics.success_requests,
            'failure_rate': self.metrics.failed_requests / max(self.metrics.total_requests, 1),
            'consecutive_failures': self.metrics.consecutive_failures,
            'last_failure_time': self.metrics.last_failure_time.isoformat() if self.metrics.last_failure_time else None
        }

class BulkheadPool:
    """Bulkhead pattern implementation for resource isolation"""
    
    def __init__(self, name: str, max_concurrent: int = 10):
        self.name = name
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_requests = 0
        self.total_requests = 0
        self.rejected_requests = 0
        self.logger = logging.getLogger(f"bulkhead.{name}")
        
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with bulkhead protection"""
        self.total_requests += 1
        
        try:
            if self.semaphore.locked() and self.semaphore._value == 0:
                self.rejected_requests += 1
                raise BulkheadRejectionError(f"Bulkhead {self.name} at capacity")
            
            await self.semaphore.acquire()
                
            self.active_requests += 1
            try:
                return await func(*args, **kwargs)
            finally:
                self.active_requests -= 1
                self.semaphore.release()
                
        except Exception as e:
            self.logger.error(f"Bulkhead {self.name} execution failed: {e}")
            raise
            
    def get_metrics(self) -> Dict:
        """Get bulkhead metrics"""
        return {
            'name': self.name,
            'active_requests': self.active_requests,
            'total_requests': self.total_requests,
            'rejected_requests': self.rejected_requests,
            'rejection_rate': self.rejected_requests / max(self.total_requests, 1),
            'available_capacity': self.semaphore._value
        }

class RetryPolicy:
    """Retry policy with exponential backoff"""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry policy"""
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_attempts - 1:
                    break
                    
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                await asyncio.sleep(delay)
                
        raise last_exception

class ResilienceManager:
    """Central manager for all resilience patterns"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.bulkheads: Dict[str, BulkheadPool] = {}
        self.logger = logging.getLogger(__name__)
        
    def get_circuit_breaker(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Get or create circuit breaker"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, config)
        return self.circuit_breakers[name]
        
    def get_bulkhead(self, name: str, max_concurrent: int = 10) -> BulkheadPool:
        """Get or create bulkhead pool"""
        if name not in self.bulkheads:
            self.bulkheads[name] = BulkheadPool(name, max_concurrent)
        return self.bulkheads[name]
        
    async def protected_call(self, service_name: str, func: Callable, *args, **kwargs) -> Any:
        """Make a protected call with circuit breaker and bulkhead"""
        circuit_breaker = self.get_circuit_breaker(service_name)
        bulkhead = self.get_bulkhead(service_name)
        retry_policy = RetryPolicy()
        
        async def protected_func():
            return await bulkhead.execute(
                lambda: circuit_breaker.call(func, *args, **kwargs)
            )
            
        return await retry_policy.execute(protected_func)
        
    def get_all_metrics(self) -> Dict:
        """Get metrics from all resilience components"""
        return {
            'circuit_breakers': {name: cb.get_metrics() for name, cb in self.circuit_breakers.items()},
            'bulkheads': {name: bh.get_metrics() for name, bh in self.bulkheads.items()},
            'timestamp': datetime.now().isoformat()
        }

class CircuitBreakerOpenError(Exception):
    pass

class CircuitBreakerTimeoutError(Exception):
    pass

class BulkheadRejectionError(Exception):
    pass

resilience_manager = ResilienceManager()
