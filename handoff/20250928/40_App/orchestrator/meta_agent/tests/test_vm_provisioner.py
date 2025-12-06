"""
Tests for VMProvisioner

Issue: #1822 - 整合開發工具 (Integrate Development Tools)
Milestone: M5 - Meta Agent 優化
"""

import pytest
from unittest.mock import patch
from datetime import datetime, timedelta

from ..vm_provisioner import (
    DockerVMProvider,
    LocalVMProvider,
    TaskVM,
    VMConfig,
    VMProvider,
    VMProvisioner,
    VMStatus,
)


@pytest.fixture
def vm_config():
    """Create a basic VM config for testing"""
    return VMConfig(
        task_id="task-12345678",
        plan_id="plan-87654321",
        provider=VMProvider.LOCAL,
        cpu_cores=1.0,
        memory_mb=2048,
        disk_mb=10240,
        timeout_minutes=60,
        network_enabled=True,
        environment={"TEST_VAR": "test_value"},
        labels={"test": "true"},
    )


@pytest.fixture
def vm_provisioner():
    """Create a VMProvisioner instance for testing"""
    return VMProvisioner(default_provider=VMProvider.LOCAL, max_concurrent_vms=5)


@pytest.fixture
def local_provider():
    """Create a LocalVMProvider instance for testing"""
    return LocalVMProvider()


class TestVMConfig:
    """Tests for VMConfig dataclass"""

    def test_init(self, vm_config):
        """Test VMConfig initialization"""
        assert vm_config.task_id == "task-12345678"
        assert vm_config.plan_id == "plan-87654321"
        assert vm_config.provider == VMProvider.LOCAL
        assert vm_config.cpu_cores == 1.0
        assert vm_config.memory_mb == 2048

    def test_to_dict(self, vm_config):
        """Test VMConfig to_dict method"""
        d = vm_config.to_dict()

        assert d["task_id"] == "task-12345678"
        assert d["plan_id"] == "plan-87654321"
        assert d["provider"] == "local"
        assert d["cpu_cores"] == 1.0
        assert d["memory_mb"] == 2048
        assert d["environment"] == {"TEST_VAR": "test_value"}
        assert d["labels"] == {"test": "true"}


class TestTaskVM:
    """Tests for TaskVM dataclass"""

    def test_init(self, vm_config):
        """Test TaskVM initialization"""
        vm = TaskVM(
            vm_id="vm-test-123",
            task_id="task-12345678",
            plan_id="plan-87654321",
            provider=VMProvider.LOCAL,
            status=VMStatus.READY,
            config=vm_config,
            created_at=datetime.now(),
        )

        assert vm.vm_id == "vm-test-123"
        assert vm.status == VMStatus.READY
        assert vm.is_active is True

    def test_to_dict(self, vm_config):
        """Test TaskVM to_dict method"""
        vm = TaskVM(
            vm_id="vm-test-123",
            task_id="task-12345678",
            plan_id="plan-87654321",
            provider=VMProvider.LOCAL,
            status=VMStatus.READY,
            config=vm_config,
            created_at=datetime.now(),
            ip_address="127.0.0.1",
            mcp_endpoint="http://localhost:8080",
        )

        d = vm.to_dict()

        assert d["vm_id"] == "vm-test-123"
        assert d["status"] == "ready"
        assert d["provider"] == "local"
        assert d["ip_address"] == "127.0.0.1"
        assert "config" in d

    def test_is_active(self, vm_config):
        """Test TaskVM is_active property"""
        vm = TaskVM(
            vm_id="vm-test-123",
            task_id="task-12345678",
            plan_id="plan-87654321",
            provider=VMProvider.LOCAL,
            status=VMStatus.READY,
            config=vm_config,
            created_at=datetime.now(),
        )

        assert vm.is_active is True

        vm.status = VMStatus.RUNNING
        assert vm.is_active is True

        vm.status = VMStatus.STOPPED
        assert vm.is_active is False

        vm.status = VMStatus.TERMINATED
        assert vm.is_active is False

    def test_runtime_seconds(self, vm_config):
        """Test TaskVM runtime_seconds property"""
        now = datetime.now()
        vm = TaskVM(
            vm_id="vm-test-123",
            task_id="task-12345678",
            plan_id="plan-87654321",
            provider=VMProvider.LOCAL,
            status=VMStatus.RUNNING,
            config=vm_config,
            created_at=now,
            started_at=now - timedelta(seconds=100),
        )

        assert vm.runtime_seconds >= 100

    def test_runtime_seconds_not_started(self, vm_config):
        """Test TaskVM runtime_seconds when not started"""
        vm = TaskVM(
            vm_id="vm-test-123",
            task_id="task-12345678",
            plan_id="plan-87654321",
            provider=VMProvider.LOCAL,
            status=VMStatus.PENDING,
            config=vm_config,
            created_at=datetime.now(),
        )

        assert vm.runtime_seconds == 0.0


class TestVMProviderEnum:
    """Tests for VMProvider enum"""

    def test_providers(self):
        """Test all VM providers exist"""
        assert VMProvider.DOCKER.value == "docker"
        assert VMProvider.FLY.value == "fly"
        assert VMProvider.LOCAL.value == "local"


class TestVMStatusEnum:
    """Tests for VMStatus enum"""

    def test_statuses(self):
        """Test all VM statuses exist"""
        assert VMStatus.PENDING.value == "pending"
        assert VMStatus.CREATING.value == "creating"
        assert VMStatus.READY.value == "ready"
        assert VMStatus.RUNNING.value == "running"
        assert VMStatus.STOPPING.value == "stopping"
        assert VMStatus.STOPPED.value == "stopped"
        assert VMStatus.FAILED.value == "failed"
        assert VMStatus.TERMINATED.value == "terminated"


class TestLocalVMProvider:
    """Tests for LocalVMProvider"""

    @pytest.mark.asyncio
    async def test_create(self, local_provider, vm_config):
        """Test creating a local VM"""
        vm = await local_provider.create(vm_config)

        assert vm is not None
        assert vm.task_id == vm_config.task_id
        assert vm.plan_id == vm_config.plan_id
        assert vm.provider == VMProvider.LOCAL
        assert vm.status == VMStatus.READY
        assert vm.ip_address == "127.0.0.1"
        assert vm.mcp_endpoint == "http://localhost:8080"

    @pytest.mark.asyncio
    async def test_start(self, local_provider, vm_config):
        """Test starting a local VM"""
        vm = await local_provider.create(vm_config)
        vm = await local_provider.start(vm)

        assert vm.status == VMStatus.RUNNING
        assert vm.started_at is not None

    @pytest.mark.asyncio
    async def test_stop(self, local_provider, vm_config):
        """Test stopping a local VM"""
        vm = await local_provider.create(vm_config)
        vm = await local_provider.start(vm)
        vm = await local_provider.stop(vm)

        assert vm.status == VMStatus.STOPPED
        assert vm.stopped_at is not None

    @pytest.mark.asyncio
    async def test_destroy(self, local_provider, vm_config):
        """Test destroying a local VM"""
        vm = await local_provider.create(vm_config)
        success = await local_provider.destroy(vm)

        assert success is True
        assert vm.status == VMStatus.TERMINATED

    @pytest.mark.asyncio
    async def test_get_status(self, local_provider, vm_config):
        """Test getting local VM status"""
        vm = await local_provider.create(vm_config)
        status = await local_provider.get_status(vm)

        assert status == VMStatus.READY

    @pytest.mark.asyncio
    async def test_execute_command(self, local_provider, vm_config):
        """Test executing command in local VM"""
        vm = await local_provider.create(vm_config)
        result = await local_provider.execute_command(vm, "echo hello")

        assert result["success"] is True
        assert "hello" in result["stdout"]


class TestVMProvisioner:
    """Tests for VMProvisioner"""

    def test_init(self, vm_provisioner):
        """Test VMProvisioner initialization"""
        assert vm_provisioner is not None
        assert vm_provisioner.default_provider == VMProvider.LOCAL
        assert vm_provisioner.max_concurrent_vms == 5

    @pytest.mark.asyncio
    async def test_provision_vm(self, vm_provisioner):
        """Test provisioning a VM"""
        vm = await vm_provisioner.provision_vm(
            task_id="task-12345678",
            plan_id="plan-87654321",
        )

        assert vm is not None
        assert vm.task_id == "task-12345678"
        assert vm.plan_id == "plan-87654321"
        assert vm.status == VMStatus.READY

    @pytest.mark.asyncio
    async def test_provision_vm_with_custom_config(self, vm_provisioner):
        """Test provisioning a VM with custom configuration"""
        vm = await vm_provisioner.provision_vm(
            task_id="task-12345678",
            plan_id="plan-87654321",
            cpu_cores=2.0,
            memory_mb=4096,
            timeout_minutes=120,
            environment={"CUSTOM_VAR": "custom_value"},
        )

        assert vm is not None
        assert vm.config.cpu_cores == 2.0
        assert vm.config.memory_mb == 4096
        assert vm.config.timeout_minutes == 120
        assert vm.config.environment["CUSTOM_VAR"] == "custom_value"

    @pytest.mark.asyncio
    async def test_get_vm(self, vm_provisioner):
        """Test getting a VM by ID"""
        vm = await vm_provisioner.provision_vm(
            task_id="task-12345678",
            plan_id="plan-87654321",
        )

        retrieved = await vm_provisioner.get_vm(vm.vm_id)
        assert retrieved is not None
        assert retrieved.vm_id == vm.vm_id

    @pytest.mark.asyncio
    async def test_get_vm_not_found(self, vm_provisioner):
        """Test getting a non-existent VM"""
        retrieved = await vm_provisioner.get_vm("non-existent-vm")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_vm_for_task(self, vm_provisioner):
        """Test getting a VM for a specific task"""
        await vm_provisioner.provision_vm(
            task_id="task-12345678",
            plan_id="plan-87654321",
        )

        retrieved = await vm_provisioner.get_vm_for_task("task-12345678")
        assert retrieved is not None
        assert retrieved.task_id == "task-12345678"

    @pytest.mark.asyncio
    async def test_execute_in_vm(self, vm_provisioner):
        """Test executing a command in a VM"""
        vm = await vm_provisioner.provision_vm(
            task_id="task-12345678",
            plan_id="plan-87654321",
        )

        result = await vm_provisioner.execute_in_vm(vm.vm_id, "echo test")
        assert result["success"] is True
        assert "test" in result["stdout"]

    @pytest.mark.asyncio
    async def test_execute_in_vm_not_found(self, vm_provisioner):
        """Test executing in a non-existent VM"""
        result = await vm_provisioner.execute_in_vm("non-existent", "echo test")
        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_stop_vm(self, vm_provisioner):
        """Test stopping a VM"""
        vm = await vm_provisioner.provision_vm(
            task_id="task-12345678",
            plan_id="plan-87654321",
        )

        success = await vm_provisioner.stop_vm(vm.vm_id)
        assert success is True

        retrieved = await vm_provisioner.get_vm(vm.vm_id)
        assert retrieved.status == VMStatus.STOPPED

    @pytest.mark.asyncio
    async def test_destroy_vm(self, vm_provisioner):
        """Test destroying a VM"""
        vm = await vm_provisioner.provision_vm(
            task_id="task-12345678",
            plan_id="plan-87654321",
        )

        success = await vm_provisioner.destroy_vm(vm.vm_id)
        assert success is True

        retrieved = await vm_provisioner.get_vm(vm.vm_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_cleanup_task_vms(self, vm_provisioner):
        """Test cleaning up VM for a task"""
        await vm_provisioner.provision_vm(
            task_id="task-12345678",
            plan_id="plan-87654321",
        )

        cleaned = await vm_provisioner.cleanup_task_vms("task-12345678")
        assert cleaned == 1

    @pytest.mark.asyncio
    async def test_duplicate_vm_prevention(self, vm_provisioner):
        """Test that duplicate VMs for the same task are prevented (Issue #2004)"""
        await vm_provisioner.provision_vm(
            task_id="task-12345678",
            plan_id="plan-87654321",
        )

        with pytest.raises(RuntimeError) as exc_info:
            await vm_provisioner.provision_vm(
                task_id="task-12345678",
                plan_id="plan-87654321",
            )

        assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cleanup_expired_vms(self, vm_provisioner):
        """Test cleaning up expired VMs"""
        vm = await vm_provisioner.provision_vm(
            task_id="task-12345678",
            plan_id="plan-87654321",
            timeout_minutes=1,  # 1 minute timeout
        )

        # Manually set started_at to past (more than 1 minute ago)
        vm.started_at = datetime.now() - timedelta(minutes=5)

        cleaned = await vm_provisioner.cleanup_expired_vms()
        assert cleaned >= 1

    @pytest.mark.asyncio
    async def test_get_active_vms(self, vm_provisioner):
        """Test getting all active VMs"""
        await vm_provisioner.provision_vm(
            task_id="task-1",
            plan_id="plan-1",
        )
        await vm_provisioner.provision_vm(
            task_id="task-2",
            plan_id="plan-2",
        )

        active = await vm_provisioner.get_active_vms()
        assert len(active) == 2

    @pytest.mark.asyncio
    async def test_get_vm_stats(self, vm_provisioner):
        """Test getting VM statistics"""
        await vm_provisioner.provision_vm(
            task_id="task-1",
            plan_id="plan-1",
        )

        stats = await vm_provisioner.get_vm_stats()

        assert stats["total_vms"] >= 1
        assert stats["active_vms"] >= 1
        assert stats["max_concurrent_vms"] == 5
        assert "status_counts" in stats
        assert "provider_counts" in stats

    @pytest.mark.asyncio
    async def test_max_concurrent_vms_limit(self, vm_provisioner):
        """Test that max concurrent VMs limit is enforced"""
        # Create max VMs
        for i in range(5):
            await vm_provisioner.provision_vm(
                task_id=f"task-{i}",
                plan_id=f"plan-{i}",
            )

        # Try to create one more
        with pytest.raises(RuntimeError) as exc_info:
            await vm_provisioner.provision_vm(
                task_id="task-overflow",
                plan_id="plan-overflow",
            )

        assert "Max concurrent VMs" in str(exc_info.value)


class TestDockerVMProvider:
    """Tests for DockerVMProvider (mocked)"""

    @pytest.mark.asyncio
    async def test_create_no_docker(self):
        """Test DockerVMProvider when Docker is not available"""
        provider = DockerVMProvider()

        config = VMConfig(
            task_id="task-12345678",
            plan_id="plan-87654321",
            provider=VMProvider.DOCKER,
        )

        # Mock Docker client to raise exception
        with patch.object(provider, "_get_client", side_effect=Exception("Docker not available")):
            vm = await provider.create(config)
            assert vm.status == VMStatus.FAILED
            assert "Docker not available" in vm.error

    @pytest.mark.asyncio
    async def test_destroy_no_container_id(self):
        """Test destroying VM with no container ID"""
        provider = DockerVMProvider()

        config = VMConfig(
            task_id="task-12345678",
            plan_id="plan-87654321",
            provider=VMProvider.DOCKER,
        )

        vm = TaskVM(
            vm_id="vm-test",
            task_id="task-12345678",
            plan_id="plan-87654321",
            provider=VMProvider.DOCKER,
            status=VMStatus.READY,
            config=config,
            created_at=datetime.now(),
            container_id=None,
        )

        success = await provider.destroy(vm)
        assert success is True

    @pytest.mark.asyncio
    async def test_get_status_no_container_id(self):
        """Test getting status with no container ID"""
        provider = DockerVMProvider()

        config = VMConfig(
            task_id="task-12345678",
            plan_id="plan-87654321",
            provider=VMProvider.DOCKER,
        )

        vm = TaskVM(
            vm_id="vm-test",
            task_id="task-12345678",
            plan_id="plan-87654321",
            provider=VMProvider.DOCKER,
            status=VMStatus.READY,
            config=config,
            created_at=datetime.now(),
            container_id=None,
        )

        status = await provider.get_status(vm)
        assert status == VMStatus.FAILED

    @pytest.mark.asyncio
    async def test_execute_command_no_container_id(self):
        """Test executing command with no container ID"""
        provider = DockerVMProvider()

        config = VMConfig(
            task_id="task-12345678",
            plan_id="plan-87654321",
            provider=VMProvider.DOCKER,
        )

        vm = TaskVM(
            vm_id="vm-test",
            task_id="task-12345678",
            plan_id="plan-87654321",
            provider=VMProvider.DOCKER,
            status=VMStatus.READY,
            config=config,
            created_at=datetime.now(),
            container_id=None,
        )

        result = await provider.execute_command(vm, "echo test")
        assert result["success"] is False
        assert "No container ID" in result["error"]
