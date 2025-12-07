# Redis/DB-Backed VM Locking Design

This document describes the design for distributed VM locking to address the cross-process limitations documented in [VM_PROVISIONER_LIFECYCLE.md](./VM_PROVISIONER_LIFECYCLE.md).

## Goals

1. **Prevent duplicate VMs**: Ensure only one VM exists per task across all processes
2. **Enforce global concurrency limit**: Respect MAX_CONCURRENT_VMS across all processes
3. **Handle process crashes**: Automatically release locks from crashed processes
4. **Maintain backward compatibility**: Support single-process deployments without Redis

## Design Overview

### Lock Types

Two types of distributed locks are needed:

1. **Task Lock**: Prevents duplicate VM creation for the same task
2. **Concurrency Semaphore**: Enforces global MAX_CONCURRENT_VMS limit

### Redis Key Schema

```
vm:lock:task:{task_id}     → Task-level lock (prevents duplicates)
vm:registry:{vm_id}        → VM state (replaces in-memory _vms dict)
vm:active_count            → Counter for active VMs (for concurrency limit)
```

## Detailed Design

### 1. Task Lock (Duplicate Prevention)

#### Acquisition

```python
async def acquire_task_lock(self, task_id: str, ttl_seconds: int = 300) -> bool:
    """
    Acquire exclusive lock for creating a VM for this task.
    
    Uses Redis SETNX with TTL to prevent duplicate VM creation.
    TTL ensures lock is released if process crashes.
    """
    lock_key = f"vm:lock:task:{task_id}"
    lock_value = f"{self.process_id}:{time.time()}"
    
    # SETNX with TTL - atomic operation
    acquired = await self.redis.set(
        lock_key,
        lock_value,
        nx=True,  # Only set if not exists
        ex=ttl_seconds  # Expire after TTL
    )
    
    return acquired is not None
```

#### Release

```python
async def release_task_lock(self, task_id: str) -> bool:
    """
    Release task lock after VM creation completes or fails.
    
    Uses Lua script for atomic check-and-delete to prevent
    releasing a lock acquired by another process.
    """
    lock_key = f"vm:lock:task:{task_id}"
    expected_value = f"{self.process_id}:{self.lock_acquired_time}"
    
    # Lua script for atomic check-and-delete
    script = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """
    
    return await self.redis.eval(script, 1, lock_key, expected_value)
```

### 2. Concurrency Semaphore (Global Limit)

#### Check and Increment

```python
async def acquire_vm_slot(self) -> bool:
    """
    Acquire a slot in the global VM concurrency limit.
    
    Uses Redis INCR with conditional check to atomically
    verify and increment the active VM count.
    """
    # Lua script for atomic check-and-increment
    script = """
    local current = tonumber(redis.call("get", KEYS[1]) or "0")
    local max_vms = tonumber(ARGV[1])
    
    if current < max_vms then
        redis.call("incr", KEYS[1])
        return 1
    else
        return 0
    end
    """
    
    result = await self.redis.eval(
        script, 1, 
        "vm:active_count", 
        self.max_concurrent_vms
    )
    
    return result == 1
```

#### Decrement on VM Destruction

```python
async def release_vm_slot(self) -> None:
    """
    Release a slot when VM is destroyed.
    
    Decrements the active count, with floor at 0.
    """
    script = """
    local current = tonumber(redis.call("get", KEYS[1]) or "0")
    if current > 0 then
        redis.call("decr", KEYS[1])
    end
    return current - 1
    """
    
    await self.redis.eval(script, 1, "vm:active_count")
```

### 3. VM Registry (Shared State)

#### Store VM State

```python
async def register_vm(self, vm: TaskVM) -> None:
    """
    Register VM in shared Redis registry.
    
    Replaces in-memory _vms dict for cross-process visibility.
    """
    vm_key = f"vm:registry:{vm.vm_id}"
    vm_data = {
        "vm_id": vm.vm_id,
        "task_id": vm.task_id,
        "status": vm.status.value,
        "provider": vm.provider.value,
        "created_at": vm.created_at.isoformat(),
        "process_id": self.process_id,
    }
    
    # Store with TTL slightly longer than max VM lifetime
    ttl = vm.config.timeout_minutes * 60 + 300  # +5 min buffer
    await self.redis.hset(vm_key, mapping=vm_data)
    await self.redis.expire(vm_key, ttl)
```

#### Query VMs

```python
async def get_vm_for_task(self, task_id: str) -> Optional[TaskVM]:
    """
    Find active VM for a task across all processes.
    """
    # Scan for VMs with matching task_id
    async for key in self.redis.scan_iter("vm:registry:*"):
        vm_data = await self.redis.hgetall(key)
        if vm_data.get("task_id") == task_id:
            if vm_data.get("status") in ["ready", "running"]:
                return self._deserialize_vm(vm_data)
    return None
```

## Integration with VMProvisioner

### Modified provision_vm Flow

```python
async def provision_vm(self, task_id: str, ...) -> TaskVM:
    """
    Provision a VM with distributed locking.
    """
    # Step 1: Acquire task lock (prevent duplicates)
    if not await self.acquire_task_lock(task_id):
        # Check if VM already exists
        existing = await self.get_vm_for_task(task_id)
        if existing:
            raise RuntimeError(f"VM for task {task_id[:8]} already exists")
        raise RuntimeError(f"Could not acquire lock for task {task_id[:8]}")
    
    try:
        # Step 2: Acquire concurrency slot
        if not await self.acquire_vm_slot():
            raise RuntimeError(f"Max concurrent VMs reached")
        
        try:
            # Step 3: Create VM (existing logic)
            vm = await self._create_vm(task_id, ...)
            
            # Step 4: Register in shared registry
            await self.register_vm(vm)
            
            return vm
            
        except Exception:
            # Release slot on failure
            await self.release_vm_slot()
            raise
            
    finally:
        # Always release task lock
        await self.release_task_lock(task_id)
```

## Failure Handling

### Process Crash Recovery

1. **Task locks**: TTL ensures automatic release (default: 5 minutes)
2. **VM slots**: Periodic cleanup job reconciles count with actual VMs
3. **VM registry**: TTL ensures stale entries are cleaned up

### Cleanup Job

```python
async def cleanup_stale_vms(self) -> int:
    """
    Periodic job to clean up stale VM entries and reconcile counts.
    
    Should run every few minutes via scheduler.
    """
    cleaned = 0
    actual_active = 0
    
    async for key in self.redis.scan_iter("vm:registry:*"):
        vm_data = await self.redis.hgetall(key)
        
        # Check if VM is actually running
        is_alive = await self._check_vm_alive(vm_data)
        
        if not is_alive:
            await self.redis.delete(key)
            cleaned += 1
        elif vm_data.get("status") in ["ready", "running"]:
            actual_active += 1
    
    # Reconcile active count
    await self.redis.set("vm:active_count", actual_active)
    
    return cleaned
```

## Configuration

### Environment Variables

```python
# Redis connection
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

# Lock configuration
VM_LOCK_TTL_SECONDS = int(os.environ.get("VM_LOCK_TTL_SECONDS", "300"))
VM_REGISTRY_TTL_BUFFER = int(os.environ.get("VM_REGISTRY_TTL_BUFFER", "300"))

# Feature flag for gradual rollout
USE_DISTRIBUTED_VM_LOCKING = os.environ.get("USE_DISTRIBUTED_VM_LOCKING", "false").lower() == "true"
```

### Graceful Degradation

```python
class VMProvisioner:
    def __init__(self, redis_client: Optional[Redis] = None, ...):
        self.redis = redis_client
        self.use_distributed_locking = (
            redis_client is not None and 
            os.environ.get("USE_DISTRIBUTED_VM_LOCKING", "false").lower() == "true"
        )
        
        # Fallback to in-memory for single-process deployments
        if not self.use_distributed_locking:
            self._vms: Dict[str, TaskVM] = {}
            self._lock = asyncio.Lock()
```

## Migration Plan

### Phase 1: Add Redis Support (Non-Breaking)

1. Add Redis client dependency
2. Implement distributed locking behind feature flag
3. Keep existing in-memory logic as fallback
4. Deploy with `USE_DISTRIBUTED_VM_LOCKING=false`

### Phase 2: Testing and Validation

1. Enable feature flag in staging
2. Run load tests with multiple workers
3. Verify no duplicate VMs or limit violations
4. Monitor Redis performance and lock contention

### Phase 3: Production Rollout

1. Enable feature flag in production
2. Monitor for issues
3. Remove in-memory fallback code (optional)

## Future Considerations

### Database-Backed Alternative

If Redis is not available, a database-backed implementation could use:

1. **PostgreSQL advisory locks**: `pg_advisory_lock(task_id_hash)`
2. **Row-level locking**: `SELECT ... FOR UPDATE SKIP LOCKED`
3. **Unique constraints**: Prevent duplicate VM records

### Kubernetes-Native Alternative

For Kubernetes deployments, consider:

1. **Leader election**: Only one pod handles VM provisioning
2. **Custom Resource Definitions**: Store VM state in Kubernetes API
3. **Operator pattern**: Dedicated controller for VM lifecycle

## Related Issues

- Issue #2004: Prevent duplicate VM creation
- Issue #1995: VM provisioning for task isolation

## Related Files

- `meta_agent/vm_provisioner.py`: VMProvisioner implementation
- `redis_queue/worker.py`: RQ worker configuration
