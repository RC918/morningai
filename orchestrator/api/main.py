#!/usr/bin/env python3
"""
Orchestrator REST API
Provides HTTP endpoints for task submission and status monitoring
"""
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from orchestrator.queue.redis_queue import RedisQueue, create_redis_queue
from orchestrator.schemas.task_schema import (
    UnifiedTask, TaskType, TaskPriority, TaskSource, TaskStatus, create_task
)
from orchestrator.api.router import OrchestratorRouter
from orchestrator.api.hitl_gate import HITLGate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_queue: Optional[RedisQueue] = None
orchestrator_router: Optional[OrchestratorRouter] = None
hitl_gate: Optional[HITLGate] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app"""
    global redis_queue, orchestrator_router, hitl_gate
    
    logger.info("Starting Orchestrator API")
    
    redis_queue = await create_redis_queue()
    
    orchestrator_router = OrchestratorRouter(redis_queue)
    
    hitl_gate = HITLGate()
    
    logger.info("Orchestrator API started successfully")
    
    yield
    
    logger.info("Shutting down Orchestrator API")
    if redis_queue:
        await redis_queue.disconnect()


app = FastAPI(
    title="MorningAI Orchestrator",
    description="Multi-Agent Task Orchestration and Event Bus",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TaskRequest(BaseModel):
    """Request model for creating a task"""
    type: str = Field(..., description="Task type (faq, bugfix, deploy, investigate, etc.)")
    payload: Dict[str, Any] = Field(..., description="Task-specific payload")
    priority: str = Field(default="P2", description="Task priority (P0, P1, P2, P3)")
    source: str = Field(default="user", description="Task source")
    sla_target: Optional[str] = Field(None, description="SLA target description")
    sla_deadline: Optional[str] = Field(None, description="SLA deadline (ISO8601)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class TaskResponse(BaseModel):
    """Response model for task operations"""
    success: bool
    task_id: Optional[str] = None
    message: Optional[str] = None
    task: Optional[Dict[str, Any]] = None


class EventPublishRequest(BaseModel):
    """Request model for publishing events"""
    event_type: str = Field(..., description="Event type")
    source_agent: str = Field(..., description="Source agent name")
    payload: Dict[str, Any] = Field(..., description="Event payload")
    task_id: Optional[str] = Field(None, description="Related task ID")
    trace_id: Optional[str] = Field(None, description="Trace ID")
    priority: str = Field(default="medium", description="Event priority")


async def get_redis_queue() -> RedisQueue:
    """Dependency to get Redis queue instance"""
    if not redis_queue:
        raise HTTPException(status_code=503, detail="Redis queue not initialized")
    return redis_queue


async def get_orchestrator_router() -> OrchestratorRouter:
    """Dependency to get orchestrator router instance"""
    if not orchestrator_router:
        raise HTTPException(status_code=503, detail="Orchestrator router not initialized")
    return orchestrator_router


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "MorningAI Orchestrator",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check(queue: RedisQueue = Depends(get_redis_queue)):
    """Health check endpoint"""
    try:
        stats = await queue.get_queue_stats()
        return {
            "status": "healthy",
            "redis": "connected",
            "queue_stats": stats
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/tasks", response_model=TaskResponse)
async def create_task_endpoint(
    request: TaskRequest,
    background_tasks: BackgroundTasks,
    queue: RedisQueue = Depends(get_redis_queue),
    router: OrchestratorRouter = Depends(get_orchestrator_router)
):
    """
    Create a new task
    
    This is the unified entry point for all agents (FAQ, Dev, Ops) to submit tasks.
    The orchestrator routes tasks to the appropriate agent based on task type.
    """
    try:
        task = create_task(
            task_type=request.type,
            payload=request.payload,
            priority=request.priority,
            source=request.source,
            sla_target=request.sla_target,
            sla_deadline=request.sla_deadline,
            metadata=request.metadata
        )
        
        assigned_agent = router.route_task(task)
        task.mark_assigned(assigned_agent)
        
        success = await queue.enqueue_task(task)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to enqueue task")
        
        logger.info(f"Created task {task.task_id} assigned to {assigned_agent}")
        
        return TaskResponse(
            success=True,
            task_id=task.task_id,
            message=f"Task created and assigned to {assigned_agent}",
            task=task.to_dict()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_endpoint(
    task_id: str,
    queue: RedisQueue = Depends(get_redis_queue)
):
    """Get task status by ID"""
    try:
        task = await queue.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return TaskResponse(
            success=True,
            task_id=task_id,
            task=task.to_dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/tasks/{task_id}/status")
async def update_task_status(
    task_id: str,
    status: str,
    error: Optional[str] = None,
    queue: RedisQueue = Depends(get_redis_queue)
):
    """Update task status"""
    try:
        task = await queue.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        if status == "in_progress":
            task.mark_in_progress()
        elif status == "completed":
            task.mark_completed()
        elif status == "failed":
            task.mark_failed(error or "Unknown error")
        else:
            task.status = TaskStatus(status)
        
        success = await queue.update_task(task)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update task")
        
        await queue.publish_event(
            event_type=f"task.{status}",
            source_agent="orchestrator",
            task_id=task_id,
            payload={
                "status": status,
                "error": error
            },
            trace_id=task.trace_id
        )
        
        return {"success": True, "task_id": task_id, "status": status}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/events/publish")
async def publish_event_endpoint(
    request: EventPublishRequest,
    queue: RedisQueue = Depends(get_redis_queue)
):
    """
    Publish an event to the event bus
    
    Agents use this endpoint to publish events that other agents can subscribe to.
    """
    try:
        success = await queue.publish_event(
            event_type=request.event_type,
            source_agent=request.source_agent,
            payload=request.payload,
            task_id=request.task_id,
            trace_id=request.trace_id,
            priority=request.priority
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to publish event")
        
        return {
            "success": True,
            "event_type": request.event_type,
            "message": "Event published successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to publish event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats(queue: RedisQueue = Depends(get_redis_queue)):
    """Get orchestrator statistics"""
    try:
        stats = await queue.get_queue_stats()
        
        return {
            "queue": stats,
            "timestamp": "2025-10-21T10:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
