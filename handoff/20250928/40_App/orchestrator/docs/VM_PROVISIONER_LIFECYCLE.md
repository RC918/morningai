# VMProvisioner Lifecycle and Cross-Process Limitations

This document describes the VMProvisioner architecture, its current limitations regarding cross-process coordination, and the planned improvements.

## Architecture Overview

The VMProvisioner manages task-isolated virtual machines for the Meta Agent orchestrator. Each task can have its own VM for secure, isolated code execution.

```
TaskPlan → VMProvisioner → VMProvider (Docker/Local/Fly.io) → TaskVM
                ↓
         - VM lifecycle management
         - Concurrent VM limits
         - Duplicate prevention
```

## Current Implementation

### Core Components

The VMProvisioner (`meta_agent/vm_provisioner.py`) consists of:

1. **VMProvisioner**: Main orchestrator class managing VM lifecycle
2. **VMProviderBase**: Abstract base class for VM providers
3. **DockerVMProvider**: Docker-based VM implementation
4. **LocalVMProvider**: Local process-based VM (for development)
5. **TaskVM**: Dataclass representing a provisioned VM
6. **VMConfig**: Configuration for VM provisioning

### State Management

The VMProvisioner maintains state using in-memory data structures:

```python
class VMProvisioner:
    def __init__(self, ...):
        self._vms: Dict[str, TaskVM] = {}  # VM registry
        self._lock = asyncio.Lock()         # Concurrency control
        self.max_concurrent_vms = 10        # Global limit
```

### Concurrency Controls

Two mechanisms prevent resource exhaustion:

1. **Duplicate VM Prevention** (Issue #2004):
   ```python
   if any(vm.task_id == task_id and vm.is_active for vm in self._vms.values()):
       raise RuntimeError(f"An active VM for task {task_id[:8]} already exists.")
   ```

2. **Concurrent VM Limit**:
   ```python
   active_vms = sum(1 for vm in self._vms.values() if vm.is_active)
   if active_vms >= self.max_concurrent_vms:
       raise RuntimeError(f"Max concurrent VMs ({self.max_concurrent_vms}) reached.")
   ```

## Cross-Process Limitations

### The Problem

The current implementation uses `asyncio.Lock()` for concurrency control. This lock only coordinates coroutines within a single Python process. In a multi-process deployment (e.g., multiple RQ workers, Kubernetes pods), each process has its own:

1. **Separate `_vms` dictionary**: Each process tracks only VMs it created
2. **Separate `asyncio.Lock`**: Locks don't coordinate across processes

### Failure Scenarios

#### Scenario 1: Exceeding MAX_CONCURRENT_VMS

```
Process A: active_vms = 5, creates VM → total = 6
Process B: active_vms = 5, creates VM → total = 6
                                        ↓
                            Actual total = 12 (exceeds limit of 10)
```

#### Scenario 2: Duplicate VMs for Same Task

```
Process A: No VM for task-123, creates VM-A
Process B: No VM for task-123 (doesn't see VM-A), creates VM-B
                                        ↓
                            Two VMs for same task (violates uniqueness)
```

### Current Assumptions

The current implementation assumes:

1. **Single orchestrator process**: Only one process runs VMProvisioner
2. **No horizontal scaling**: No multiple workers processing VM requests
3. **No process crashes**: State is not persisted, lost on restart

## Impact Assessment

### When This Matters

Cross-process coordination is critical when:

1. Running multiple RQ workers for the orchestrator queue
2. Deploying to Kubernetes with multiple replicas
3. Using auto-scaling that spawns additional processes
4. Recovering from process crashes (state is lost)

### When This Doesn't Matter

Single-process deployments are safe:

1. Development environments with single worker
2. Small-scale deployments with one orchestrator instance
3. Testing scenarios

## Planned Improvements

See [VM_LOCKING_DESIGN.md](./VM_LOCKING_DESIGN.md) for the detailed design of Redis/DB-backed distributed locking to address these limitations.

### Summary of Planned Changes

1. **Distributed Lock for VM Creation**: Use Redis SETNX or database row locking
2. **Shared VM Registry**: Store VM state in Redis/database instead of in-memory
3. **Lease-based Locking**: TTL-based locks to handle process crashes
4. **Graceful Degradation**: Fallback behavior when Redis is unavailable

## Related Issues

- Issue #2004: Prevent duplicate VM creation for the same task
- Issue #1995: VM provisioning for task isolation

## Related Files

- `meta_agent/vm_provisioner.py`: VMProvisioner implementation
- `meta_agent/tests/test_vm_provisioner.py`: Unit tests
