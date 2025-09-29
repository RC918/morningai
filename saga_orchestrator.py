#!/usr/bin/env python3
"""
Saga Orchestrator - Implements Saga pattern for distributed transactions
Provides idempotency and compensation mechanisms for complex workflows
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import hashlib

class SagaStepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"

class SagaStatus(Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"

@dataclass
class SagaStep:
    """Individual step in a Saga transaction"""
    step_id: str
    name: str
    action: Callable
    compensate: Optional[Callable] = None
    status: SagaStepStatus = SagaStepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    idempotency_key: Optional[str] = None

@dataclass
class SagaTransaction:
    """Saga transaction containing multiple steps"""
    saga_id: str
    name: str
    steps: List[SagaStep] = field(default_factory=list)
    status: SagaStatus = SagaStatus.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    context: Dict = field(default_factory=dict)
    current_step_index: int = 0

class IdempotencyManager:
    """Manages idempotency keys to prevent duplicate operations"""
    
    def __init__(self):
        self.processed_keys: Dict[str, Any] = {}
        self.logger = logging.getLogger(f"{__name__}.idempotency")
        
    def generate_key(self, operation: str, params: Dict) -> str:
        """Generate idempotency key from operation and parameters"""
        content = f"{operation}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
        
    def is_processed(self, key: str) -> bool:
        """Check if operation was already processed"""
        return key in self.processed_keys
        
    def get_result(self, key: str) -> Any:
        """Get result of previously processed operation"""
        return self.processed_keys.get(key)
        
    def mark_processed(self, key: str, result: Any):
        """Mark operation as processed with result"""
        self.processed_keys[key] = result
        self.logger.debug(f"Marked operation {key} as processed")
        
    def cleanup_old_keys(self, max_age_hours: int = 24):
        """Clean up old idempotency keys"""
        if len(self.processed_keys) > 10000:
            keys_to_remove = list(self.processed_keys.keys())[:-5000]
            for key in keys_to_remove:
                del self.processed_keys[key]

class SagaOrchestrator:
    """Orchestrates Saga transactions with compensation and idempotency"""
    
    def __init__(self, persistent_state_manager=None):
        self.active_sagas: Dict[str, SagaTransaction] = {}
        self.completed_sagas: List[SagaTransaction] = []
        self.idempotency_manager = IdempotencyManager()
        self.persistent_state_manager = persistent_state_manager
        self.logger = logging.getLogger(__name__)
        
    def create_saga(self, name: str, context: Dict = None) -> SagaTransaction:
        """Create new Saga transaction"""
        saga_id = str(uuid.uuid4())
        saga = SagaTransaction(
            saga_id=saga_id,
            name=name,
            context=context or {}
        )
        
        self.active_sagas[saga_id] = saga
        self.logger.info(f"Created Saga {saga_id}: {name}")
        
        return saga
        
    def add_step(self, saga: SagaTransaction, name: str, action: Callable, 
                 compensate: Callable = None, max_retries: int = 3) -> SagaStep:
        """Add step to Saga transaction"""
        step_id = f"{saga.saga_id}_{len(saga.steps)}"
        
        step = SagaStep(
            step_id=step_id,
            name=name,
            action=action,
            compensate=compensate,
            max_retries=max_retries
        )
        
        saga.steps.append(step)
        self.logger.debug(f"Added step {name} to Saga {saga.saga_id}")
        
        return step
        
    async def execute_saga(self, saga: SagaTransaction) -> bool:
        """Execute Saga transaction with compensation on failure"""
        saga.status = SagaStatus.RUNNING
        saga.started_at = datetime.now()
        
        try:
            for i, step in enumerate(saga.steps):
                saga.current_step_index = i
                
                if not await self._execute_step(step, saga.context):
                    await self._compensate_saga(saga, i)
                    return False
                    
            saga.status = SagaStatus.COMPLETED
            saga.completed_at = datetime.now()
            
            self._move_to_completed(saga)
            self.logger.info(f"Saga {saga.saga_id} completed successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Saga {saga.saga_id} failed with exception: {e}")
            saga.status = SagaStatus.FAILED
            await self._compensate_saga(saga, saga.current_step_index)
            return False
            
    async def _execute_step(self, step: SagaStep, context: Dict) -> bool:
        """Execute individual Saga step with idempotency"""
        step.status = SagaStepStatus.RUNNING
        step.started_at = datetime.now()
        
        if not step.idempotency_key:
            step.idempotency_key = self.idempotency_manager.generate_key(
                step.name, context
            )
            
        if self.idempotency_manager.is_processed(step.idempotency_key):
            step.result = self.idempotency_manager.get_result(step.idempotency_key)
            step.status = SagaStepStatus.COMPLETED
            step.completed_at = datetime.now()
            self.logger.info(f"Step {step.name} already processed (idempotent)")
            return True
            
        for attempt in range(step.max_retries + 1):
            try:
                step.retry_count = attempt
                result = await step.action(context)
                
                step.result = result
                step.status = SagaStepStatus.COMPLETED
                step.completed_at = datetime.now()
                
                self.idempotency_manager.mark_processed(step.idempotency_key, result)
                
                self.logger.info(f"Step {step.name} completed successfully")
                return True
                
            except Exception as e:
                step.error = str(e)
                self.logger.warning(f"Step {step.name} attempt {attempt + 1} failed: {e}")
                
                if attempt < step.max_retries:
                    delay = 2 ** attempt
                    await asyncio.sleep(delay)
                else:
                    step.status = SagaStepStatus.FAILED
                    return False
                    
        return False
        
    async def _compensate_saga(self, saga: SagaTransaction, failed_step_index: int):
        """Compensate Saga by running compensation actions in reverse order"""
        saga.status = SagaStatus.COMPENSATING
        self.logger.info(f"Starting compensation for Saga {saga.saga_id}")
        
        for i in range(failed_step_index - 1, -1, -1):
            step = saga.steps[i]
            
            if step.status == SagaStepStatus.COMPLETED and step.compensate:
                await self._compensate_step(step, saga.context)
                
        saga.status = SagaStatus.COMPENSATED
        self._move_to_completed(saga)
        
    async def _compensate_step(self, step: SagaStep, context: Dict):
        """Compensate individual step"""
        step.status = SagaStepStatus.COMPENSATING
        
        try:
            await step.compensate(context, step.result)
            step.status = SagaStepStatus.COMPENSATED
            self.logger.info(f"Step {step.name} compensated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to compensate step {step.name}: {e}")
            
    def _move_to_completed(self, saga: SagaTransaction):
        """Move Saga from active to completed"""
        if saga.saga_id in self.active_sagas:
            del self.active_sagas[saga.saga_id]
            
        self.completed_sagas.append(saga)
        
        if len(self.completed_sagas) > 1000:
            self.completed_sagas = self.completed_sagas[-500:]
            
        if self.persistent_state_manager:
            self.persistent_state_manager.create_checkpoint(
                'saga_orchestrator',
                {
                    'saga_id': saga.saga_id,
                    'status': saga.status.value,
                    'completed_at': saga.completed_at.isoformat() if saga.completed_at else None
                }
            )
            
    def get_saga_status(self, saga_id: str) -> Optional[Dict]:
        """Get status of Saga transaction"""
        if saga_id in self.active_sagas:
            saga = self.active_sagas[saga_id]
        else:
            saga = next((s for s in self.completed_sagas if s.saga_id == saga_id), None)
            
        if not saga:
            return None
            
        return {
            'saga_id': saga.saga_id,
            'name': saga.name,
            'status': saga.status.value,
            'current_step_index': saga.current_step_index,
            'total_steps': len(saga.steps),
            'created_at': saga.created_at.isoformat(),
            'started_at': saga.started_at.isoformat() if saga.started_at else None,
            'completed_at': saga.completed_at.isoformat() if saga.completed_at else None,
            'steps': [
                {
                    'step_id': step.step_id,
                    'name': step.name,
                    'status': step.status.value,
                    'retry_count': step.retry_count,
                    'error': step.error
                } for step in saga.steps
            ]
        }
        
    def get_orchestrator_metrics(self) -> Dict:
        """Get Saga orchestrator metrics"""
        return {
            'active_sagas': len(self.active_sagas),
            'completed_sagas': len(self.completed_sagas),
            'processed_idempotency_keys': len(self.idempotency_manager.processed_keys),
            'saga_statuses': {
                status.value: len([s for s in self.active_sagas.values() if s.status == status])
                for status in SagaStatus
            }
        }

saga_orchestrator = SagaOrchestrator()
