"""
Distributed VM Locking - Redis-backed cross-process coordination for VM provisioning

This module implements distributed locking for VM provisioning to address
cross-process limitations documented in VM_PROVISIONER_LIFECYCLE.md.

Issue: #2104 - Redis-backed distributed VM locking
Design: docs/VM_LOCKING_DESIGN.md

Key Features:
    - Task Lock: Prevents duplicate VM creation for the same task
    - Concurrency Semaphore: Enforces global MAX_CONCURRENT_VMS limit
    - VM Registry: Shared state across processes with secondary index
    - Graceful Degradation: Falls back to in-memory when Redis unavailable
"""

import asyncio
import logging
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

MAX_LOCK_WAIT_SECONDS = 5
LOCK_RETRY_INTERVAL = 0.1


@dataclass
class VMRegistryEntry:
    """Represents a VM entry in the distributed registry."""
    vm_id: str
    task_id: str
    plan_id: str
    status: str
    provider: str
    created_at: str
    process_id: str
    ip_address: Optional[str] = None
    mcp_endpoint: Optional[str] = None
    container_id: Optional[str] = None
    timeout_minutes: int = 60

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vm_id": self.vm_id,
            "task_id": self.task_id,
            "plan_id": self.plan_id,
            "status": self.status,
            "provider": self.provider,
            "created_at": self.created_at,
            "process_id": self.process_id,
            "ip_address": self.ip_address,
            "mcp_endpoint": self.mcp_endpoint,
            "container_id": self.container_id,
            "timeout_minutes": self.timeout_minutes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VMRegistryEntry":
        return cls(
            vm_id=data.get("vm_id", ""),
            task_id=data.get("task_id", ""),
            plan_id=data.get("plan_id", ""),
            status=data.get("status", ""),
            provider=data.get("provider", ""),
            created_at=data.get("created_at", ""),
            process_id=data.get("process_id", ""),
            ip_address=data.get("ip_address"),
            mcp_endpoint=data.get("mcp_endpoint"),
            container_id=data.get("container_id"),
            timeout_minutes=int(data.get("timeout_minutes", 60)),
        )


class DistributedVMLockManager:
    """
    Manages distributed locking for VM provisioning using Redis.

    This class provides:
    1. Task locks to prevent duplicate VM creation
    2. Concurrency semaphore to enforce global VM limits
    3. Shared VM registry for cross-process visibility
    4. Secondary index for O(1) task-to-VM lookups

    Redis Key Schema:
        vm:lock:task:{task_id}     → Task-level lock (prevents duplicates)
        vm:registry:{vm_id}        → VM state (replaces in-memory _vms dict)
        vm:task_to_vm:{task_id}    → Secondary index: task_id → vm_id
        vm:active_count            → Counter for active VMs
    """

    def __init__(
        self,
        redis_client: Optional[Any] = None,
        max_concurrent_vms: int = 10,
        lock_ttl_seconds: int = 300,
        registry_ttl_buffer: int = 300,
    ):
        """
        Initialize the distributed lock manager.

        Args:
            redis_client: Redis client instance (async redis)
            max_concurrent_vms: Maximum concurrent VMs allowed
            lock_ttl_seconds: TTL for task locks (default: 5 minutes)
            registry_ttl_buffer: Additional TTL buffer for registry entries
        """
        self.redis = redis_client
        self.max_concurrent_vms = max_concurrent_vms
        self.lock_ttl_seconds = lock_ttl_seconds
        self.registry_ttl_buffer = registry_ttl_buffer
        self.process_id = f"{os.getpid()}-{uuid.uuid4().hex[:8]}"
        self._task_lock_tokens: Dict[str, str] = {}

        logger.info(
            "[DistributedVMLockManager] Initialized with process_id=%s, max_vms=%d",
            self.process_id, max_concurrent_vms
        )

    @property
    def is_available(self) -> bool:
        """Check if Redis is available for distributed locking."""
        return self.redis is not None

    async def acquire_task_lock(self, task_id: str) -> bool:
        """
        Acquire exclusive lock for creating a VM for this task.

        Uses Redis SET NX with TTL to prevent duplicate VM creation.
        TTL ensures the lock is eventually released if the owning process crashes.

        Args:
            task_id: The task ID to lock

        Returns:
            True if lock acquired, False otherwise
        """
        if not self.redis:
            return True

        lock_key = f"vm:lock:task:{task_id}"
        lock_token = uuid.uuid4().hex

        try:
            acquired = await self.redis.set(
                lock_key,
                lock_token,
                nx=True,
                ex=self.lock_ttl_seconds,
            )

            if acquired:
                self._task_lock_tokens[task_id] = lock_token
                logger.debug(
                    "[DistributedVMLockManager] Acquired task lock for %s",
                    task_id[:8]
                )

            return bool(acquired)

        except Exception as e:
            logger.error(
                "[DistributedVMLockManager] Failed to acquire task lock: %s", e
            )
            return False

    async def release_task_lock(self, task_id: str) -> bool:
        """
        Release the task lock after VM creation completes or fails.

        Uses a Lua script for atomic check-and-delete to ensure we only
        delete the lock if we still own it (token matches).

        Args:
            task_id: The task ID to unlock

        Returns:
            True if lock released, False otherwise
        """
        if not self.redis:
            return True

        lock_key = f"vm:lock:task:{task_id}"
        lock_token = self._task_lock_tokens.get(task_id)
        if not lock_token:
            return False

        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """

        try:
            deleted = await self.redis.eval(script, 1, lock_key, lock_token)
            if deleted:
                self._task_lock_tokens.pop(task_id, None)
                logger.debug(
                    "[DistributedVMLockManager] Released task lock for %s",
                    task_id[:8]
                )
            return bool(deleted)

        except Exception as e:
            logger.error(
                "[DistributedVMLockManager] Failed to release task lock: %s", e
            )
            return False

    async def acquire_vm_slot(self) -> bool:
        """
        Acquire a slot in the global VM concurrency limit.

        Uses Redis INCR with conditional check to atomically
        verify and increment the active VM count.

        Returns:
            True if slot acquired, False if limit reached
        """
        if not self.redis:
            return True

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

        try:
            result = await self.redis.eval(
                script, 1,
                "vm:active_count",
                self.max_concurrent_vms
            )
            acquired = result == 1

            if acquired:
                logger.debug("[DistributedVMLockManager] Acquired VM slot")
            else:
                logger.warning(
                    "[DistributedVMLockManager] VM slot limit reached (%d)",
                    self.max_concurrent_vms
                )

            return acquired

        except Exception as e:
            logger.error(
                "[DistributedVMLockManager] Failed to acquire VM slot: %s", e
            )
            return False

    async def release_vm_slot(self) -> None:
        """
        Release a slot when VM is destroyed.

        Decrements the active count, with floor at 0.
        """
        if not self.redis:
            return

        script = """
        local current = tonumber(redis.call("get", KEYS[1]) or "0")
        if current > 0 then
            redis.call("decr", KEYS[1])
        end
        return current - 1
        """

        try:
            await self.redis.eval(script, 1, "vm:active_count")
            logger.debug("[DistributedVMLockManager] Released VM slot")

        except Exception as e:
            logger.error(
                "[DistributedVMLockManager] Failed to release VM slot: %s", e
            )

    async def register_vm(self, entry: VMRegistryEntry) -> None:
        """
        Register VM in shared Redis registry and secondary index.

        Replaces in-memory _vms dict for cross-process visibility.
        The secondary index enables O(1) lookups by task_id.

        Args:
            entry: VM registry entry to store
        """
        if not self.redis:
            return

        vm_key = f"vm:registry:{entry.vm_id}"
        index_key = f"vm:task_to_vm:{entry.task_id}"

        ttl = entry.timeout_minutes * 60 + self.registry_ttl_buffer

        try:
            vm_data = entry.to_dict()
            await self.redis.hset(vm_key, mapping=vm_data)
            await self.redis.expire(vm_key, ttl)

            await self.redis.set(index_key, entry.vm_id, ex=ttl)

            logger.debug(
                "[DistributedVMLockManager] Registered VM %s for task %s",
                entry.vm_id, entry.task_id[:8]
            )

        except Exception as e:
            logger.error(
                "[DistributedVMLockManager] Failed to register VM: %s", e
            )

    async def unregister_vm(self, vm_id: str, task_id: str) -> None:
        """
        Remove VM from registry and secondary index.

        Only removes the secondary index if it still points to this VM
        (to avoid race conditions with a newer VM for the same task).

        Args:
            vm_id: VM ID to unregister
            task_id: Task ID associated with the VM
        """
        if not self.redis:
            return

        vm_key = f"vm:registry:{vm_id}"
        index_key = f"vm:task_to_vm:{task_id}"

        try:
            await self.redis.delete(vm_key)

            script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            await self.redis.eval(script, 1, index_key, vm_id)

            logger.debug(
                "[DistributedVMLockManager] Unregistered VM %s", vm_id
            )

        except Exception as e:
            logger.error(
                "[DistributedVMLockManager] Failed to unregister VM: %s", e
            )

    async def get_vm_for_task(self, task_id: str) -> Optional[VMRegistryEntry]:
        """
        Find active VM for a task across all processes using the secondary index.

        Uses vm:task_to_vm:{task_id} for O(1) lookup instead of scanning.

        Args:
            task_id: Task ID to look up

        Returns:
            VMRegistryEntry if found and active, None otherwise
        """
        if not self.redis:
            return None

        index_key = f"vm:task_to_vm:{task_id}"

        try:
            vm_id = await self.redis.get(index_key)
            if not vm_id:
                return None

            if isinstance(vm_id, bytes):
                vm_id = vm_id.decode()

            vm_key = f"vm:registry:{vm_id}"
            vm_data = await self.redis.hgetall(vm_key)
            if not vm_data:
                return None

            decoded_data = {}
            for k, v in vm_data.items():
                key = k.decode() if isinstance(k, bytes) else k
                value = v.decode() if isinstance(v, bytes) else v
                decoded_data[key] = value

            if decoded_data.get("status") not in {"ready", "running", "creating"}:
                return None

            return VMRegistryEntry.from_dict(decoded_data)

        except Exception as e:
            logger.error(
                "[DistributedVMLockManager] Failed to get VM for task: %s", e
            )
            return None

    async def wait_for_vm_or_lock(
        self,
        task_id: str,
        timeout_seconds: float = MAX_LOCK_WAIT_SECONDS,
    ) -> Optional[VMRegistryEntry]:
        """
        Wait for either an existing VM to appear or acquire the lock ourselves.

        This handles race conditions where another process might be creating
        a VM for the same task.

        Args:
            task_id: Task ID to wait for
            timeout_seconds: Maximum time to wait

        Returns:
            VMRegistryEntry if another worker created one, None if we acquired the lock

        Raises:
            RuntimeError: If timed out waiting for lock or VM
        """
        if not self.redis:
            return None

        deadline = time.monotonic() + timeout_seconds

        while time.monotonic() < deadline:
            vm = await self.get_vm_for_task(task_id)
            if vm:
                logger.debug(
                    "[DistributedVMLockManager] Found existing VM %s for task %s",
                    vm.vm_id, task_id[:8]
                )
                return vm

            if await self.acquire_task_lock(task_id):
                return None

            await asyncio.sleep(LOCK_RETRY_INTERVAL)

        raise RuntimeError(
            f"Timed out waiting for VM lock for task {task_id[:8]}"
        )

    async def get_active_vm_count(self) -> int:
        """
        Get the current active VM count from Redis.

        Returns:
            Current active VM count, or 0 if unavailable
        """
        if not self.redis:
            return 0

        try:
            count = await self.redis.get("vm:active_count")
            if count is None:
                return 0
            if isinstance(count, bytes):
                count = count.decode()
            return int(count)

        except Exception as e:
            logger.error(
                "[DistributedVMLockManager] Failed to get active VM count: %s", e
            )
            return 0

    async def cleanup_stale_vms(self) -> int:
        """
        Periodic job to clean up stale VM entries and reconcile counts.

        Should run every few minutes via scheduler.

        Returns:
            Number of stale entries cleaned up
        """
        if not self.redis:
            return 0

        cleaned = 0
        actual_active = 0

        try:
            async for key in self.redis.scan_iter("vm:registry:*"):
                if isinstance(key, bytes):
                    key = key.decode()

                vm_data = await self.redis.hgetall(key)
                if not vm_data:
                    continue

                decoded_data = {}
                for k, v in vm_data.items():
                    dk = k.decode() if isinstance(k, bytes) else k
                    dv = v.decode() if isinstance(v, bytes) else v
                    decoded_data[dk] = dv

                status = decoded_data.get("status", "")

                if status in {"ready", "running", "creating"}:
                    actual_active += 1
                elif status in {"stopped", "failed", "terminated"}:
                    await self.redis.delete(key)
                    cleaned += 1

            await self.redis.set("vm:active_count", actual_active)

            if cleaned > 0:
                logger.info(
                    "[DistributedVMLockManager] Cleaned up %d stale VMs, "
                    "reconciled count to %d",
                    cleaned, actual_active
                )

            return cleaned

        except Exception as e:
            logger.error(
                "[DistributedVMLockManager] Failed to cleanup stale VMs: %s", e
            )
            return 0

    async def update_vm_status(self, vm_id: str, status: str) -> bool:
        """
        Update the status of a VM in the registry.

        Args:
            vm_id: VM ID to update
            status: New status value

        Returns:
            True if updated successfully, False otherwise
        """
        if not self.redis:
            return True

        vm_key = f"vm:registry:{vm_id}"

        try:
            exists = await self.redis.exists(vm_key)
            if not exists:
                return False

            await self.redis.hset(vm_key, "status", status)
            logger.debug(
                "[DistributedVMLockManager] Updated VM %s status to %s",
                vm_id, status
            )
            return True

        except Exception as e:
            logger.error(
                "[DistributedVMLockManager] Failed to update VM status: %s", e
            )
            return False
