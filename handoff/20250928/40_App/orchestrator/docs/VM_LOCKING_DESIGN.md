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
vm:task_to_vm:{task_id}    → Secondary index: task_id → vm_id (O(1) lookup)
vm:active_count            → Counter for active VMs (for concurrency limit)
```

#### Secondary Index: `vm:task_to_vm:{task_id}`

Looking up a VM for a task by scanning all `vm:registry:*` keys is O(N) in the number of VMs and does not scale well. To support O(1) lookups and clearer race handling, we introduce a secondary index:

- **Key**: `vm:task_to_vm:{task_id}`
- **Value**: `vm_id` of the current active VM for that task
- **TTL**: Same as `vm:registry:{vm_id}` to ensure consistency

This index is maintained alongside the VM registry:
- On VM creation/registration: Set `vm:task_to_vm:{task_id} = vm_id`
- On VM destruction/cleanup: Delete `vm:task_to_vm:{task_id}` if it still points to this `vm_id`

## Detailed Design

### 1. Task Lock (Duplicate Prevention)

Each task gets a dedicated Redis lock key to prevent duplicate VM creation.

We use a **random UUID lock token** rather than a timestamp. The reasons:

- A UUID is globally unique across processes and machines, even if they start at the same instant
- The lock token is opaque and hard to guess, which makes it safer to use in a check-and-delete release script
- A `time.time()` based token can, in theory, collide if two workers on the same host acquire within the same timestamp granularity

#### Acquisition

```python
import uuid

async def acquire_task_lock(self, task_id: str, ttl_seconds: int = 300) -> bool:
    """
    Acquire exclusive lock for creating a VM for this task.
    
    Uses Redis SET NX with TTL to prevent duplicate VM creation.
    TTL ensures the lock is eventually released if the owning process crashes.
    """
    lock_key = f"vm:lock:task:{task_id}"
    lock_token = uuid.uuid4().hex  # Opaque, globally-unique token
    
    # SET NX with TTL - atomic operation
    acquired = await self.redis.set(
        lock_key,
        lock_token,
        nx=True,          # Only set if key does not exist
        ex=ttl_seconds,   # Expire after TTL
    )
    
    if acquired:
        # Store token in memory so we can release the lock safely later
        self._task_lock_tokens[task_id] = lock_token
    
    return bool(acquired)
```

#### Release

```python
async def release_task_lock(self, task_id: str) -> bool:
    """
    Release the task lock after VM creation completes or fails.
    
    Uses a Lua script for atomic check-and-delete to ensure we only
    delete the lock if we still own it (token matches).
    """
    lock_key = f"vm:lock:task:{task_id}"
    lock_token = self._task_lock_tokens.get(task_id)
    if not lock_token:
        return False
    
    # Lua script for atomic check-and-delete
    script = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """
    
    deleted = await self.redis.eval(script, 1, lock_key, lock_token)
    if deleted:
        self._task_lock_tokens.pop(task_id, None)
    return bool(deleted)
```

> **Note**: The `_task_lock_tokens` dictionary is an in-memory structure that maps `task_id` to the UUID token used when acquiring the lock. This is necessary for safe lock release.

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

#### Store VM State with Secondary Index

```python
async def register_vm(self, vm: TaskVM) -> None:
    """
    Register VM in shared Redis registry and secondary index.
    
    Replaces in-memory _vms dict for cross-process visibility.
    The secondary index enables O(1) lookups by task_id.
    """
    vm_key = f"vm:registry:{vm.vm_id}"
    index_key = f"vm:task_to_vm:{vm.task_id}"
    
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
    
    # Secondary index for O(1) lookups by task
    await self.redis.set(index_key, vm.vm_id, ex=ttl)
```

#### Query VMs Using Secondary Index

```python
async def get_vm_for_task(self, task_id: str) -> Optional[TaskVM]:
    """
    Find active VM for a task across all processes using the secondary index.
    
    Uses vm:task_to_vm:{task_id} for O(1) lookup instead of scanning.
    """
    index_key = f"vm:task_to_vm:{task_id}"
    vm_id = await self.redis.get(index_key)
    if not vm_id:
        return None
    
    vm_key = f"vm:registry:{vm_id}"
    vm_data = await self.redis.hgetall(vm_key)
    if not vm_data:
        return None
    
    # Filter by active statuses
    if vm_data.get("status") not in {"ready", "running"}:
        return None
    
    return self._deserialize_vm(vm_data)
```

#### Cleanup Secondary Index on VM Destruction

```python
async def unregister_vm(self, vm: TaskVM) -> None:
    """
    Remove VM from registry and secondary index.
    
    Only removes the secondary index if it still points to this VM
    (to avoid race conditions with a newer VM for the same task).
    """
    vm_key = f"vm:registry:{vm.vm_id}"
    index_key = f"vm:task_to_vm:{vm.task_id}"
    
    # Delete VM registry entry
    await self.redis.delete(vm_key)
    
    # Only delete secondary index if it points to this VM
    script = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """
    await self.redis.eval(script, 1, index_key, vm.vm_id)
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

### Race Conditions and `acquire_task_lock` Failures

When `acquire_task_lock(task_id)` returns `False`, there are two main possibilities:

1. **Another process is legitimately creating a VM** for this task and currently holds the lock
2. **The lock is stale**, left over from a crashed process (will eventually expire via TTL)

We handle this as follows:

#### Step 1: Immediate Check for Existing VM via Secondary Index

First, call `get_vm_for_task(task_id)` using the `vm:task_to_vm:{task_id}` index. If it returns a VM, we treat that as the "winner" of the race:
- We do **not** try to create a second VM
- The caller reuses the existing VM instead of raising an error

#### Step 2: Short, Bounded Wait if No VM Exists Yet

If `get_vm_for_task(task_id)` returns `None`, we cannot distinguish between:
- A legitimate concurrent creator that has the lock but has not registered the VM yet
- A stale lock from a crashed process that will expire soon

To avoid "stealing" locks and causing split-brain, we do **not** forcefully overwrite the lock. Instead, we retry in a small loop:

```python
MAX_LOCK_WAIT_SECONDS = 5

async def wait_for_vm_or_lock(self, task_id: str) -> Optional[TaskVM]:
    """
    Wait for either an existing VM to appear or acquire the lock ourselves.
    
    Returns:
        TaskVM if another worker created one, None if we acquired the lock
    Raises:
        RuntimeError if timed out waiting
    """
    deadline = time.monotonic() + MAX_LOCK_WAIT_SECONDS
    
    while time.monotonic() < deadline:
        # Check if VM was created by another worker
        vm = await self.get_vm_for_task(task_id)
        if vm:
            return vm
        
        # Try to become the owner
        if await self.acquire_task_lock(task_id):
            # We now hold the lock; caller can proceed with creation path
            return None
        
        await asyncio.sleep(0.1)  # Simple backoff
    
    raise RuntimeError(f"Timed out waiting for VM lock for task {task_id[:8]}")
```

#### Step 3: Creation Path Remains Single-Owner

Only the worker that successfully acquires the task lock proceeds to:
1. Check again for an existing VM (in case the VM was created between queueing and locking)
2. Acquire a global VM slot (`acquire_vm_slot`)
3. Call the actual VM provider to create the VM
4. Register the VM in `vm:registry:{vm_id}` and `vm:task_to_vm:{task_id}`
5. Release the task lock in a `finally` block

This strategy ensures:
- At most one VM per task (enforced by task lock + `vm:task_to_vm` index)
- Other workers either reuse the existing VM or fail fast with a clear "timed out acquiring lock" error
- We never "steal" a lock from another process; stale locks are resolved by TTL expiration rather than guessing

> **Note**: The `MAX_LOCK_WAIT_SECONDS` value should be tuned based on typical VM provisioning time. If VM creation typically takes longer than 5 seconds, increase this value accordingly.

### Process Crash Recovery

1. **Task locks**: TTL ensures automatic release (default: 5 minutes)
2. **VM slots**: Periodic cleanup job reconciles count with actual VMs
3. **VM registry**: TTL ensures stale entries are cleaned up
4. **Secondary index**: TTL ensures stale `vm:task_to_vm` entries are cleaned up

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
