"""
VM Provisioner - Task-Isolated Virtual Machine Management

This module implements VM provisioning for task isolation, ensuring each task
executes in its own isolated environment with proper resource limits and security.

Issue: #1822 - 整合開發工具 (Integrate Development Tools)
Issue: #2104 - Redis-backed distributed VM locking
Milestone: M5 - Meta Agent 優化

Architecture:
    TaskPlan → VMProvisioner → TaskVM → Task Execution → Cleanup

Supported Providers:
    - docker: Local Docker containers (default, fast)
    - fly: Fly.io cloud VMs (production, scalable)
    - local: Local process isolation (development only)

Distributed Locking (when USE_DISTRIBUTED_VM_LOCKING=true):
    - Task locks prevent duplicate VM creation across processes
    - Concurrency semaphore enforces global MAX_CONCURRENT_VMS
    - Shared VM registry enables cross-process visibility
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .distributed_vm_lock import VMRegistryEntry

logger = logging.getLogger(__name__)


class VMProvider(Enum):
    """Supported VM providers"""
    DOCKER = "docker"  # Local Docker containers
    FLY = "fly"  # Fly.io cloud VMs
    LOCAL = "local"  # Local process (dev only)


class VMStatus(Enum):
    """VM lifecycle status"""
    PENDING = "pending"  # VM requested but not created
    CREATING = "creating"  # VM being provisioned
    READY = "ready"  # VM ready for task execution
    RUNNING = "running"  # Task executing in VM
    STOPPING = "stopping"  # VM being stopped
    STOPPED = "stopped"  # VM stopped
    FAILED = "failed"  # VM creation/execution failed
    TERMINATED = "terminated"  # VM destroyed


@dataclass
class VMConfig:
    """Configuration for task VM"""
    task_id: str
    plan_id: str
    provider: VMProvider = VMProvider.DOCKER
    cpu_cores: float = 1.0
    memory_mb: int = 2048
    disk_mb: int = 10240
    timeout_minutes: int = 60
    network_enabled: bool = True
    gpu_enabled: bool = False
    environment: Dict[str, str] = field(default_factory=dict)
    volumes: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "task_id": self.task_id,
            "plan_id": self.plan_id,
            "provider": self.provider.value,
            "cpu_cores": self.cpu_cores,
            "memory_mb": self.memory_mb,
            "disk_mb": self.disk_mb,
            "timeout_minutes": self.timeout_minutes,
            "network_enabled": self.network_enabled,
            "gpu_enabled": self.gpu_enabled,
            "environment": self.environment,
            "volumes": self.volumes,
            "labels": self.labels,
        }


@dataclass
class TaskVM:
    """Represents a task-isolated VM instance"""
    vm_id: str
    task_id: str
    plan_id: str
    provider: VMProvider
    status: VMStatus
    config: VMConfig
    created_at: datetime
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    ssh_port: Optional[int] = None
    mcp_endpoint: Optional[str] = None
    container_id: Optional[str] = None
    fly_app_id: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "vm_id": self.vm_id,
            "task_id": self.task_id,
            "plan_id": self.plan_id,
            "provider": self.provider.value,
            "status": self.status.value,
            "config": self.config.to_dict(),
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "ip_address": self.ip_address,
            "ssh_port": self.ssh_port,
            "mcp_endpoint": self.mcp_endpoint,
            "container_id": self.container_id,
            "fly_app_id": self.fly_app_id,
            "error": self.error,
            "metadata": self.metadata,
        }

    @property
    def is_active(self) -> bool:
        """Check if VM is in an active state"""
        return self.status in [VMStatus.CREATING, VMStatus.READY, VMStatus.RUNNING]

    @property
    def runtime_seconds(self) -> float:
        """Get VM runtime in seconds"""
        if not self.started_at:
            return 0.0
        end_time = self.stopped_at or datetime.now()
        return (end_time - self.started_at).total_seconds()


class VMProviderBase(ABC):
    """Abstract base class for VM providers"""

    @abstractmethod
    async def create(self, config: VMConfig) -> TaskVM:
        """Create a new VM"""
        pass

    @abstractmethod
    async def start(self, vm: TaskVM) -> TaskVM:
        """Start the VM"""
        pass

    @abstractmethod
    async def stop(self, vm: TaskVM) -> TaskVM:
        """Stop the VM"""
        pass

    @abstractmethod
    async def destroy(self, vm: TaskVM) -> bool:
        """Destroy the VM"""
        pass

    @abstractmethod
    async def get_status(self, vm: TaskVM) -> VMStatus:
        """Get current VM status"""
        pass

    @abstractmethod
    async def execute_command(self, vm: TaskVM, command: str) -> Dict[str, Any]:
        """Execute a command in the VM"""
        pass


class DockerVMProvider(VMProviderBase):
    """Docker-based VM provider for local development"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._client = None

    def _get_client(self):
        """Lazy load Docker client"""
        if self._client is None:
            try:
                import docker
                self._client = docker.from_env()
            except Exception as e:
                self.logger.error("Failed to connect to Docker: %s", e)
                raise
        return self._client

    async def create(self, config: VMConfig) -> TaskVM:
        """Create a Docker container for task isolation"""
        vm_id = f"vm-{config.task_id[:8]}-{uuid.uuid4().hex[:8]}"

        vm = TaskVM(
            vm_id=vm_id,
            task_id=config.task_id,
            plan_id=config.plan_id,
            provider=VMProvider.DOCKER,
            status=VMStatus.CREATING,
            config=config,
            created_at=datetime.now(),
        )

        try:
            # Issue #2002: Use asyncio.to_thread to avoid blocking event loop
            client = await asyncio.to_thread(self._get_client)

            container_config = {
                "image": "morningai-task-vm:latest",
                # Issue #2003: Use vm_id instead of task_id[:8] to avoid name collision
                "name": f"task-vm-{vm_id}",
                "detach": True,
                "remove": False,
                "mem_limit": f"{config.memory_mb}m",
                "cpu_period": 100000,
                "cpu_quota": int(100000 * config.cpu_cores),
                "environment": {
                    "TASK_ID": config.task_id,
                    "PLAN_ID": config.plan_id,
                    "VM_ID": vm_id,
                    **config.environment,
                },
                "labels": {
                    "morningai.task_id": config.task_id,
                    "morningai.plan_id": config.plan_id,
                    "morningai.vm_id": vm_id,
                    **config.labels,
                },
                "network_mode": "bridge" if config.network_enabled else "none",
            }

            # Issue #2002: Use asyncio.to_thread for sync Docker calls
            container = await asyncio.to_thread(
                client.containers.run, **container_config
            )
            await asyncio.to_thread(container.reload)

            vm.container_id = container.id
            vm.status = VMStatus.READY
            vm.started_at = datetime.now()

            network_settings = container.attrs.get("NetworkSettings", {})
            vm.ip_address = network_settings.get("IPAddress")
            if vm.ip_address:
                vm.mcp_endpoint = f"http://{vm.ip_address}:8080"

            self.logger.info(
                "[DockerVMProvider] Created VM %s for task %s",
                vm_id, config.task_id[:8]
            )

            return vm

        except Exception as e:
            self.logger.error(
                "[DockerVMProvider] Failed to create VM for task %s: %s",
                config.task_id[:8], e
            )
            vm.status = VMStatus.FAILED
            vm.error = str(e)
            return vm

    async def start(self, vm: TaskVM) -> TaskVM:
        """Start a stopped Docker container"""
        if not vm.container_id:
            vm.error = "No container ID"
            return vm

        try:
            # Issue #2002: Use asyncio.to_thread for sync Docker calls
            client = await asyncio.to_thread(self._get_client)
            container = await asyncio.to_thread(client.containers.get, vm.container_id)
            await asyncio.to_thread(container.start)
            vm.status = VMStatus.RUNNING
            vm.started_at = datetime.now()
            self.logger.info("[DockerVMProvider] Started VM %s", vm.vm_id)
        except Exception as e:
            self.logger.error("[DockerVMProvider] Failed to start VM %s: %s", vm.vm_id, e)
            vm.error = str(e)

        return vm

    async def stop(self, vm: TaskVM) -> TaskVM:
        """Stop a running Docker container"""
        if not vm.container_id:
            vm.error = "No container ID"
            return vm

        try:
            # Issue #2002: Use asyncio.to_thread for sync Docker calls
            client = await asyncio.to_thread(self._get_client)
            container = await asyncio.to_thread(client.containers.get, vm.container_id)
            await asyncio.to_thread(container.stop, timeout=30)
            vm.status = VMStatus.STOPPED
            vm.stopped_at = datetime.now()
            self.logger.info("[DockerVMProvider] Stopped VM %s", vm.vm_id)
        except Exception as e:
            self.logger.error("[DockerVMProvider] Failed to stop VM %s: %s", vm.vm_id, e)
            vm.error = str(e)

        return vm

    async def destroy(self, vm: TaskVM) -> bool:
        """Destroy a Docker container"""
        if not vm.container_id:
            return True

        try:
            # Issue #2002: Use asyncio.to_thread for sync Docker calls
            client = await asyncio.to_thread(self._get_client)
            container = await asyncio.to_thread(client.containers.get, vm.container_id)
            await asyncio.to_thread(container.remove, force=True)
            vm.status = VMStatus.TERMINATED
            self.logger.info("[DockerVMProvider] Destroyed VM %s", vm.vm_id)
            return True
        except Exception as e:
            self.logger.error("[DockerVMProvider] Failed to destroy VM %s: %s", vm.vm_id, e)
            vm.error = str(e)
            return False

    async def get_status(self, vm: TaskVM) -> VMStatus:
        """Get Docker container status"""
        if not vm.container_id:
            return VMStatus.FAILED

        try:
            # Issue #2002: Use asyncio.to_thread for sync Docker calls
            client = await asyncio.to_thread(self._get_client)
            container = await asyncio.to_thread(client.containers.get, vm.container_id)
            container_status = container.status

            status_map = {
                "created": VMStatus.READY,
                "running": VMStatus.RUNNING,
                "paused": VMStatus.STOPPED,
                "restarting": VMStatus.CREATING,
                "removing": VMStatus.STOPPING,
                "exited": VMStatus.STOPPED,
                "dead": VMStatus.FAILED,
            }

            return status_map.get(container_status, VMStatus.FAILED)
        except Exception:
            return VMStatus.FAILED

    async def execute_command(self, vm: TaskVM, command: str) -> Dict[str, Any]:
        """Execute a command in the Docker container"""
        if not vm.container_id:
            return {"success": False, "error": "No container ID"}

        try:
            # Issue #2002: Use asyncio.to_thread for sync Docker calls
            client = await asyncio.to_thread(self._get_client)
            container = await asyncio.to_thread(client.containers.get, vm.container_id)
            exit_code, output = await asyncio.to_thread(
                container.exec_run, command, demux=True
            )

            stdout = output[0].decode() if output[0] else ""
            stderr = output[1].decode() if output[1] else ""

            return {
                "success": exit_code == 0,
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class LocalVMProvider(VMProviderBase):
    """Local process-based provider for development/testing"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._processes: Dict[str, Any] = {}

    async def create(self, config: VMConfig) -> TaskVM:
        """Create a local 'VM' (just tracking, no real isolation)"""
        vm_id = f"local-{config.task_id[:8]}-{uuid.uuid4().hex[:8]}"

        vm = TaskVM(
            vm_id=vm_id,
            task_id=config.task_id,
            plan_id=config.plan_id,
            provider=VMProvider.LOCAL,
            status=VMStatus.READY,
            config=config,
            created_at=datetime.now(),
            started_at=datetime.now(),
            ip_address="127.0.0.1",
            mcp_endpoint="http://localhost:8080",
        )

        self.logger.info(
            "[LocalVMProvider] Created local VM %s for task %s (no isolation)",
            vm_id, config.task_id[:8]
        )

        return vm

    async def start(self, vm: TaskVM) -> TaskVM:
        """Start local VM (no-op)"""
        vm.status = VMStatus.RUNNING
        vm.started_at = datetime.now()
        return vm

    async def stop(self, vm: TaskVM) -> TaskVM:
        """Stop local VM (no-op)"""
        vm.status = VMStatus.STOPPED
        vm.stopped_at = datetime.now()
        return vm

    async def destroy(self, vm: TaskVM) -> bool:
        """Destroy local VM (no-op)"""
        vm.status = VMStatus.TERMINATED
        return True

    async def get_status(self, vm: TaskVM) -> VMStatus:
        """Get local VM status"""
        return vm.status

    async def execute_command(self, vm: TaskVM, command: str) -> Dict[str, Any]:
        """Execute command locally"""
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**vm.config.environment},
            )
            stdout, stderr = await proc.communicate()

            return {
                "success": proc.returncode == 0,
                "exit_code": proc.returncode,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class VMProvisioner:
    """
    Manages VM lifecycle for task isolation.

    This provisioner creates isolated VMs for each task, ensuring:
    - Resource isolation (CPU, memory, disk)
    - Security isolation (network, filesystem)
    - Automatic cleanup after task completion

    When USE_DISTRIBUTED_VM_LOCKING is enabled (#2104):
    - Cross-process coordination via Redis
    - Global concurrency limits across all workers
    - Duplicate VM prevention across processes
    """

    # Default resource limits
    DEFAULT_CPU_CORES = 1.0
    DEFAULT_MEMORY_MB = 2048
    DEFAULT_DISK_MB = 10240
    DEFAULT_TIMEOUT_MINUTES = 60

    # Maximum concurrent VMs
    MAX_CONCURRENT_VMS = 10

    def __init__(
        self,
        default_provider: VMProvider = VMProvider.LOCAL,
        max_concurrent_vms: int = MAX_CONCURRENT_VMS,
        redis_client: Optional[Any] = None,
    ):
        """
        Initialize the VMProvisioner.

        Args:
            default_provider: Default VM provider to use
            max_concurrent_vms: Maximum number of concurrent VMs
            redis_client: Optional Redis client for distributed locking (#2104)
        """
        self.default_provider = default_provider
        self.max_concurrent_vms = max_concurrent_vms
        self._vms: Dict[str, TaskVM] = {}
        self._lock = asyncio.Lock()

        # Initialize providers
        self._providers: Dict[VMProvider, VMProviderBase] = {
            VMProvider.DOCKER: DockerVMProvider(),
            VMProvider.LOCAL: LocalVMProvider(),
        }

        # Issue #2104: Initialize distributed locking if enabled
        self._distributed_lock: Optional["DistributedVMLockManager"] = None
        self._use_distributed_locking = False

        try:
            from common.config.settings import settings
            if settings.use_distributed_vm_locking and redis_client is not None:
                from .distributed_vm_lock import DistributedVMLockManager
                self._distributed_lock = DistributedVMLockManager(
                    redis_client=redis_client,
                    max_concurrent_vms=max_concurrent_vms,
                    lock_ttl_seconds=settings.vm_lock_ttl_seconds,
                    registry_ttl_buffer=settings.vm_registry_ttl_buffer,
                )
                self._use_distributed_locking = True
                logger.info(
                    "[VMProvisioner] Distributed locking enabled via Redis"
                )
        except ImportError:
            logger.debug(
                "[VMProvisioner] Distributed locking not available (settings not found)"
            )
        except Exception as e:
            logger.warning(
                "[VMProvisioner] Failed to initialize distributed locking: %s", e
            )

        logger.info(
            "[VMProvisioner] Initialized with provider=%s, max_vms=%d, distributed=%s",
            default_provider.value, max_concurrent_vms, self._use_distributed_locking
        )

    async def provision_vm(
        self,
        task_id: str,
        plan_id: str,
        provider: Optional[VMProvider] = None,
        cpu_cores: Optional[float] = None,
        memory_mb: Optional[int] = None,
        disk_mb: Optional[int] = None,
        timeout_minutes: Optional[int] = None,
        environment: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> TaskVM:
        """
        Provision a new VM for a task.

        When USE_DISTRIBUTED_VM_LOCKING is enabled (#2104):
            - Cross-process uniqueness is guaranteed via Redis locks
            - Global concurrency limits are enforced across all workers
            - Existing VMs from other processes are visible

        When disabled (default):
            - At most one active VM per task is enforced within a single process
            - Cross-process uniqueness is NOT guaranteed

        Args:
            task_id: ID of the task
            plan_id: ID of the execution plan
            provider: VM provider to use (default: self.default_provider)
            cpu_cores: CPU cores limit
            memory_mb: Memory limit in MB
            disk_mb: Disk limit in MB
            timeout_minutes: VM timeout in minutes
            environment: Environment variables
            labels: Labels for the VM

        Returns:
            TaskVM instance

        Raises:
            RuntimeError: If max concurrent VMs reached or duplicate VM for task
        """
        # Issue #2104: Use distributed locking if enabled
        if self._use_distributed_locking and self._distributed_lock:
            return await self._provision_vm_distributed(
                task_id=task_id,
                plan_id=plan_id,
                provider=provider,
                cpu_cores=cpu_cores,
                memory_mb=memory_mb,
                disk_mb=disk_mb,
                timeout_minutes=timeout_minutes,
                environment=environment,
                labels=labels,
            )

        # Fallback to in-memory locking
        return await self._provision_vm_local(
            task_id=task_id,
            plan_id=plan_id,
            provider=provider,
            cpu_cores=cpu_cores,
            memory_mb=memory_mb,
            disk_mb=disk_mb,
            timeout_minutes=timeout_minutes,
            environment=environment,
            labels=labels,
        )

    async def _provision_vm_local(
        self,
        task_id: str,
        plan_id: str,
        provider: Optional[VMProvider] = None,
        cpu_cores: Optional[float] = None,
        memory_mb: Optional[int] = None,
        disk_mb: Optional[int] = None,
        timeout_minutes: Optional[int] = None,
        environment: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> TaskVM:
        """
        Provision VM using in-memory locking (single-process mode).

        This is the original implementation for backward compatibility.
        """
        async with self._lock:
            # Issue #2004: Prevent duplicate VM creation for the same task
            if any(vm.task_id == task_id and vm.is_active for vm in self._vms.values()):
                raise RuntimeError(
                    f"An active VM for task {task_id[:8]} already exists. "
                    "Use get_vm_for_task() to retrieve the existing VM."
                )

            # Check concurrent VM limit
            active_vms = sum(1 for vm in self._vms.values() if vm.is_active)
            if active_vms >= self.max_concurrent_vms:
                raise RuntimeError(
                    f"Max concurrent VMs ({self.max_concurrent_vms}) reached. "
                    f"Active VMs: {active_vms}"
                )

            # Create VM config
            config = VMConfig(
                task_id=task_id,
                plan_id=plan_id,
                provider=provider or self.default_provider,
                cpu_cores=cpu_cores or self.DEFAULT_CPU_CORES,
                memory_mb=memory_mb or self.DEFAULT_MEMORY_MB,
                disk_mb=disk_mb or self.DEFAULT_DISK_MB,
                timeout_minutes=timeout_minutes or self.DEFAULT_TIMEOUT_MINUTES,
                environment=environment or {},
                labels=labels or {},
            )

            # Get provider
            vm_provider = self._providers.get(config.provider)
            if not vm_provider:
                raise ValueError(f"Unsupported provider: {config.provider}")

            # Create VM
            logger.info(
                "[VMProvisioner] Provisioning VM for task %s with provider %s",
                task_id[:8], config.provider.value
            )

            vm = await vm_provider.create(config)
            self._vms[vm.vm_id] = vm

            logger.info(
                "[VMProvisioner] VM %s provisioned for task %s (status: %s)",
                vm.vm_id, task_id[:8], vm.status.value
            )

            return vm

    async def _provision_vm_distributed(
        self,
        task_id: str,
        plan_id: str,
        provider: Optional[VMProvider] = None,
        cpu_cores: Optional[float] = None,
        memory_mb: Optional[int] = None,
        disk_mb: Optional[int] = None,
        timeout_minutes: Optional[int] = None,
        environment: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> TaskVM:
        """
        Provision VM using distributed Redis locking (#2104).

        This implementation provides cross-process coordination:
        1. Acquire task lock (prevent duplicates across processes)
        2. Acquire VM slot (enforce global concurrency limit)
        3. Create VM via provider
        4. Register in shared Redis registry
        5. Release task lock
        """
        from .distributed_vm_lock import VMRegistryEntry

        # Step 1: Try to acquire task lock or wait for existing VM
        try:
            existing_entry = await self._distributed_lock.wait_for_vm_or_lock(task_id)
            if existing_entry:
                # Another process created a VM for this task
                logger.info(
                    "[VMProvisioner] Found existing VM %s for task %s from another process",
                    existing_entry.vm_id, task_id[:8]
                )
                # Return a TaskVM from the registry entry
                return self._registry_entry_to_task_vm(existing_entry)
        except RuntimeError as e:
            raise RuntimeError(
                f"Failed to acquire lock for task {task_id[:8]}: {e}"
            )

        try:
            # Step 2: Acquire concurrency slot
            if not await self._distributed_lock.acquire_vm_slot():
                raise RuntimeError(
                    f"Max concurrent VMs ({self.max_concurrent_vms}) reached globally"
                )

            try:
                # Step 3: Create VM config
                config = VMConfig(
                    task_id=task_id,
                    plan_id=plan_id,
                    provider=provider or self.default_provider,
                    cpu_cores=cpu_cores or self.DEFAULT_CPU_CORES,
                    memory_mb=memory_mb or self.DEFAULT_MEMORY_MB,
                    disk_mb=disk_mb or self.DEFAULT_DISK_MB,
                    timeout_minutes=timeout_minutes or self.DEFAULT_TIMEOUT_MINUTES,
                    environment=environment or {},
                    labels=labels or {},
                )

                # Get provider
                vm_provider = self._providers.get(config.provider)
                if not vm_provider:
                    raise ValueError(f"Unsupported provider: {config.provider}")

                # Create VM
                logger.info(
                    "[VMProvisioner] Provisioning VM for task %s with provider %s (distributed)",
                    task_id[:8], config.provider.value
                )

                vm = await vm_provider.create(config)

                # Step 4: Register in shared registry
                registry_entry = VMRegistryEntry(
                    vm_id=vm.vm_id,
                    task_id=vm.task_id,
                    plan_id=vm.plan_id,
                    status=vm.status.value,
                    provider=vm.provider.value,
                    created_at=vm.created_at.isoformat(),
                    process_id=self._distributed_lock.process_id,
                    ip_address=vm.ip_address,
                    mcp_endpoint=vm.mcp_endpoint,
                    container_id=vm.container_id,
                    timeout_minutes=config.timeout_minutes,
                )
                await self._distributed_lock.register_vm(registry_entry)

                # Also store locally for fast access
                self._vms[vm.vm_id] = vm

                logger.info(
                    "[VMProvisioner] VM %s provisioned for task %s (status: %s, distributed)",
                    vm.vm_id, task_id[:8], vm.status.value
                )

                return vm

            except Exception:
                # Release slot on failure
                await self._distributed_lock.release_vm_slot()
                raise

        finally:
            # Step 5: Always release task lock
            await self._distributed_lock.release_task_lock(task_id)

    def _registry_entry_to_task_vm(self, entry: "VMRegistryEntry") -> TaskVM:
        """Convert a VMRegistryEntry to a TaskVM object."""
        from datetime import datetime

        provider_map = {
            "docker": VMProvider.DOCKER,
            "fly": VMProvider.FLY,
            "local": VMProvider.LOCAL,
        }
        status_map = {
            "pending": VMStatus.PENDING,
            "creating": VMStatus.CREATING,
            "ready": VMStatus.READY,
            "running": VMStatus.RUNNING,
            "stopping": VMStatus.STOPPING,
            "stopped": VMStatus.STOPPED,
            "failed": VMStatus.FAILED,
            "terminated": VMStatus.TERMINATED,
        }

        provider = provider_map.get(entry.provider, VMProvider.LOCAL)
        status = status_map.get(entry.status, VMStatus.READY)

        try:
            created_at = datetime.fromisoformat(entry.created_at)
        except (ValueError, TypeError):
            created_at = datetime.now()

        config = VMConfig(
            task_id=entry.task_id,
            plan_id=entry.plan_id,
            provider=provider,
            timeout_minutes=entry.timeout_minutes,
        )

        return TaskVM(
            vm_id=entry.vm_id,
            task_id=entry.task_id,
            plan_id=entry.plan_id,
            provider=provider,
            status=status,
            config=config,
            created_at=created_at,
            ip_address=entry.ip_address,
            mcp_endpoint=entry.mcp_endpoint,
            container_id=entry.container_id,
        )

    async def get_vm(self, vm_id: str) -> Optional[TaskVM]:
        """Get VM by ID"""
        return self._vms.get(vm_id)

    async def get_vm_for_task(self, task_id: str) -> Optional[TaskVM]:
        """
        Get VM for a specific task.

        When distributed locking is enabled (#2104), also checks Redis registry
        for VMs created by other processes.
        """
        # First check local cache
        for vm in self._vms.values():
            if vm.task_id == task_id and vm.is_active:
                return vm

        # Issue #2104: Check Redis registry for VMs from other processes
        if self._use_distributed_locking and self._distributed_lock:
            entry = await self._distributed_lock.get_vm_for_task(task_id)
            if entry:
                return self._registry_entry_to_task_vm(entry)

        return None

    async def execute_in_vm(
        self,
        vm_id: str,
        command: str,
    ) -> Dict[str, Any]:
        """
        Execute a command in a VM.

        Args:
            vm_id: ID of the VM
            command: Command to execute

        Returns:
            Execution result with stdout, stderr, exit_code
        """
        vm = self._vms.get(vm_id)
        if not vm:
            return {"success": False, "error": f"VM {vm_id} not found"}

        if not vm.is_active:
            return {"success": False, "error": f"VM {vm_id} is not active"}

        provider = self._providers.get(vm.provider)
        if not provider:
            return {"success": False, "error": f"Provider {vm.provider} not available"}

        # Update VM status
        vm.status = VMStatus.RUNNING

        result = await provider.execute_command(vm, command)

        logger.info(
            "[VMProvisioner] Executed command in VM %s: success=%s",
            vm_id, result.get("success")
        )

        return result

    async def stop_vm(self, vm_id: str) -> bool:
        """Stop a VM"""
        vm = self._vms.get(vm_id)
        if not vm:
            return False

        provider = self._providers.get(vm.provider)
        if not provider:
            return False

        await provider.stop(vm)
        logger.info("[VMProvisioner] Stopped VM %s", vm_id)
        return True

    async def destroy_vm(self, vm_id: str) -> bool:
        """
        Destroy a VM and clean up resources.

        When distributed locking is enabled (#2104), also releases the VM slot
        and unregisters from the shared Redis registry.
        """
        async with self._lock:
            vm = self._vms.get(vm_id)
            if not vm:
                return False

            provider = self._providers.get(vm.provider)
            if not provider:
                return False

            success = await provider.destroy(vm)
            if success:
                del self._vms[vm_id]

                # Issue #2104: Release slot and unregister from Redis
                if self._use_distributed_locking and self._distributed_lock:
                    try:
                        await self._distributed_lock.unregister_vm(vm_id)
                        await self._distributed_lock.release_vm_slot()
                        logger.info(
                            "[VMProvisioner] Destroyed VM %s and released distributed slot",
                            vm_id
                        )
                    except Exception as e:
                        logger.warning(
                            "[VMProvisioner] Failed to release distributed resources for VM %s: %s",
                            vm_id, e
                        )
                else:
                    logger.info("[VMProvisioner] Destroyed VM %s", vm_id)

            return success

    async def cleanup_task_vms(self, task_id: str) -> int:
        """Clean up all VMs for a task"""
        vms_to_cleanup = [
            vm_id for vm_id, vm in self._vms.items()
            if vm.task_id == task_id
        ]

        cleaned = 0
        for vm_id in vms_to_cleanup:
            if await self.destroy_vm(vm_id):
                cleaned += 1

        logger.info(
            "[VMProvisioner] Cleaned up %d VMs for task %s",
            cleaned, task_id[:8]
        )

        return cleaned

    async def cleanup_expired_vms(self) -> int:
        """Clean up VMs that have exceeded their timeout"""
        now = datetime.now()
        vms_to_cleanup = []

        for vm_id, vm in self._vms.items():
            if vm.started_at:
                runtime = now - vm.started_at
                timeout = timedelta(minutes=vm.config.timeout_minutes)
                if runtime > timeout:
                    vms_to_cleanup.append(vm_id)
                    logger.warning(
                        "[VMProvisioner] VM %s exceeded timeout (%s > %s)",
                        vm_id, runtime, timeout
                    )

        cleaned = 0
        for vm_id in vms_to_cleanup:
            if await self.destroy_vm(vm_id):
                cleaned += 1

        if cleaned > 0:
            logger.info("[VMProvisioner] Cleaned up %d expired VMs", cleaned)

        return cleaned

    async def get_active_vms(self) -> List[TaskVM]:
        """Get all active VMs"""
        return [vm for vm in self._vms.values() if vm.is_active]

    async def get_vm_stats(self) -> Dict[str, Any]:
        """Get VM statistics"""
        vms = list(self._vms.values())
        active = sum(1 for vm in vms if vm.is_active)

        status_counts = {}
        for vm in vms:
            status = vm.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        provider_counts = {}
        for vm in vms:
            provider = vm.provider.value
            provider_counts[provider] = provider_counts.get(provider, 0) + 1

        return {
            "total_vms": len(vms),
            "active_vms": active,
            "max_concurrent_vms": self.max_concurrent_vms,
            "status_counts": status_counts,
            "provider_counts": provider_counts,
        }


# Global provisioner instance
vm_provisioner = VMProvisioner()
