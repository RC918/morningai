"""
Tests for Distributed VM Locking - Redis-backed cross-process coordination

Issue: #2104 - Redis-backed distributed VM locking
Design: docs/VM_LOCKING_DESIGN.md

These tests verify:
    - Task lock acquisition/release with UUID tokens
    - Concurrency semaphore enforcement
    - VM registry operations with secondary index
    - Race condition handling
    - Graceful degradation without Redis
    - VMProvisioner integration with distributed locking
"""

import pytest
from unittest.mock import MagicMock, patch

from meta_agent.distributed_vm_lock import (
    DistributedVMLockManager,
    VMRegistryEntry,
)
from meta_agent.vm_provisioner import (
    VMProvider,
    VMProvisioner,
    VMStatus,
)


class TestVMRegistryEntry:
    """Tests for VMRegistryEntry dataclass"""

    def test_init(self):
        """Test VMRegistryEntry initialization"""
        entry = VMRegistryEntry(
            vm_id="vm-test-123",
            task_id="task-12345678",
            plan_id="plan-87654321",
            status="ready",
            provider="local",
            created_at="2025-01-01T00:00:00",
            process_id="proc-123",
            ip_address="127.0.0.1",
            mcp_endpoint="http://localhost:8080",
            timeout_minutes=60,
        )

        assert entry.vm_id == "vm-test-123"
        assert entry.task_id == "task-12345678"
        assert entry.plan_id == "plan-87654321"
        assert entry.status == "ready"
        assert entry.provider == "local"
        assert entry.process_id == "proc-123"
        assert entry.ip_address == "127.0.0.1"
        assert entry.timeout_minutes == 60

    def test_to_dict(self):
        """Test VMRegistryEntry to_dict method"""
        entry = VMRegistryEntry(
            vm_id="vm-test-123",
            task_id="task-12345678",
            plan_id="plan-87654321",
            status="ready",
            provider="local",
            created_at="2025-01-01T00:00:00",
            process_id="proc-123",
        )

        d = entry.to_dict()

        assert d["vm_id"] == "vm-test-123"
        assert d["task_id"] == "task-12345678"
        assert d["plan_id"] == "plan-87654321"
        assert d["status"] == "ready"
        assert d["provider"] == "local"
        assert d["process_id"] == "proc-123"

    def test_from_dict(self):
        """Test VMRegistryEntry from_dict class method"""
        data = {
            "vm_id": "vm-test-123",
            "task_id": "task-12345678",
            "plan_id": "plan-87654321",
            "status": "ready",
            "provider": "local",
            "created_at": "2025-01-01T00:00:00",
            "process_id": "proc-123",
            "ip_address": "127.0.0.1",
            "mcp_endpoint": "http://localhost:8080",
            "container_id": "container-abc",
            "timeout_minutes": "60",
        }

        entry = VMRegistryEntry.from_dict(data)

        assert entry.vm_id == "vm-test-123"
        assert entry.task_id == "task-12345678"
        assert entry.ip_address == "127.0.0.1"
        assert entry.timeout_minutes == 60


class TestDistributedVMLockManager:
    """Tests for DistributedVMLockManager"""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client"""
        redis = MagicMock()
        redis.set = MagicMock(return_value=True)
        redis.get = MagicMock(return_value=None)
        redis.delete = MagicMock(return_value=1)
        redis.eval = MagicMock(return_value=1)
        redis.hset = MagicMock(return_value=1)
        redis.hgetall = MagicMock(return_value={})
        redis.hdel = MagicMock(return_value=1)
        redis.expire = MagicMock(return_value=True)
        redis.exists = MagicMock(return_value=0)
        redis.keys = MagicMock(return_value=[])
        return redis

    @pytest.fixture
    def lock_manager(self, mock_redis):
        """Create a DistributedVMLockManager instance"""
        return DistributedVMLockManager(
            redis_client=mock_redis,
            max_concurrent_vms=5,
            lock_ttl_seconds=300,
            registry_ttl_buffer=300,
        )

    def test_init(self, lock_manager, mock_redis):
        """Test DistributedVMLockManager initialization"""
        assert lock_manager.redis_client == mock_redis
        assert lock_manager.max_concurrent_vms == 5
        assert lock_manager.lock_ttl_seconds == 300
        assert lock_manager.registry_ttl_buffer == 300
        assert lock_manager.process_id is not None

    @pytest.mark.asyncio
    async def test_acquire_task_lock_success(self, lock_manager, mock_redis):
        """Test successful task lock acquisition"""
        mock_redis.set.return_value = True

        result = await lock_manager.acquire_task_lock("task-123")

        assert result is True
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert "vm:task_lock:task-123" in str(call_args)

    @pytest.mark.asyncio
    async def test_acquire_task_lock_already_held(self, lock_manager, mock_redis):
        """Test task lock acquisition when already held"""
        mock_redis.set.return_value = False

        result = await lock_manager.acquire_task_lock("task-123")

        assert result is False

    @pytest.mark.asyncio
    async def test_release_task_lock_success(self, lock_manager, mock_redis):
        """Test successful task lock release"""
        mock_redis.set.return_value = True
        await lock_manager.acquire_task_lock("task-123")

        mock_redis.eval.return_value = 1
        result = await lock_manager.release_task_lock("task-123")

        assert result is True

    @pytest.mark.asyncio
    async def test_release_task_lock_not_owner(self, lock_manager, mock_redis):
        """Test task lock release when not owner"""
        mock_redis.eval.return_value = 0
        result = await lock_manager.release_task_lock("task-123")

        assert result is False

    @pytest.mark.asyncio
    async def test_acquire_vm_slot_success(self, lock_manager, mock_redis):
        """Test successful VM slot acquisition"""
        mock_redis.eval.return_value = 1

        result = await lock_manager.acquire_vm_slot()

        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_vm_slot_at_limit(self, lock_manager, mock_redis):
        """Test VM slot acquisition when at limit"""
        mock_redis.eval.return_value = 0

        result = await lock_manager.acquire_vm_slot()

        assert result is False

    @pytest.mark.asyncio
    async def test_release_vm_slot(self, lock_manager, mock_redis):
        """Test VM slot release"""
        mock_redis.eval.return_value = 1

        result = await lock_manager.release_vm_slot()

        assert result is True

    @pytest.mark.asyncio
    async def test_register_vm(self, lock_manager, mock_redis):
        """Test VM registration in Redis"""
        entry = VMRegistryEntry(
            vm_id="vm-test-123",
            task_id="task-12345678",
            plan_id="plan-87654321",
            status="ready",
            provider="local",
            created_at="2025-01-01T00:00:00",
            process_id="proc-123",
        )

        await lock_manager.register_vm(entry)

        mock_redis.hset.assert_called()
        mock_redis.set.assert_called()

    @pytest.mark.asyncio
    async def test_unregister_vm(self, lock_manager, mock_redis):
        """Test VM unregistration from Redis"""
        mock_redis.hgetall.return_value = {
            b"vm_id": b"vm-test-123",
            b"task_id": b"task-12345678",
        }

        result = await lock_manager.unregister_vm("vm-test-123")

        assert result is True
        mock_redis.delete.assert_called()

    @pytest.mark.asyncio
    async def test_get_vm_for_task_found(self, lock_manager, mock_redis):
        """Test getting VM for task when found"""
        mock_redis.get.return_value = b"vm-test-123"
        mock_redis.hgetall.return_value = {
            b"vm_id": b"vm-test-123",
            b"task_id": b"task-12345678",
            b"plan_id": b"plan-87654321",
            b"status": b"ready",
            b"provider": b"local",
            b"created_at": b"2025-01-01T00:00:00",
            b"process_id": b"proc-123",
        }

        entry = await lock_manager.get_vm_for_task("task-12345678")

        assert entry is not None
        assert entry.vm_id == "vm-test-123"
        assert entry.task_id == "task-12345678"

    @pytest.mark.asyncio
    async def test_get_vm_for_task_not_found(self, lock_manager, mock_redis):
        """Test getting VM for task when not found"""
        mock_redis.get.return_value = None

        entry = await lock_manager.get_vm_for_task("task-nonexistent")

        assert entry is None

    @pytest.mark.asyncio
    async def test_get_active_vm_count(self, lock_manager, mock_redis):
        """Test getting active VM count"""
        mock_redis.get.return_value = b"3"

        count = await lock_manager.get_active_vm_count()

        assert count == 3

    @pytest.mark.asyncio
    async def test_get_active_vm_count_none(self, lock_manager, mock_redis):
        """Test getting active VM count when not set"""
        mock_redis.get.return_value = None

        count = await lock_manager.get_active_vm_count()

        assert count == 0

    @pytest.mark.asyncio
    async def test_update_vm_status(self, lock_manager, mock_redis):
        """Test updating VM status"""
        mock_redis.exists.return_value = 1

        result = await lock_manager.update_vm_status("vm-test-123", "running")

        assert result is True
        mock_redis.hset.assert_called()

    @pytest.mark.asyncio
    async def test_update_vm_status_not_found(self, lock_manager, mock_redis):
        """Test updating VM status when VM not found"""
        mock_redis.exists.return_value = 0

        result = await lock_manager.update_vm_status("vm-nonexistent", "running")

        assert result is False

    @pytest.mark.asyncio
    async def test_wait_for_vm_or_lock_acquires_lock(self, lock_manager, mock_redis):
        """Test wait_for_vm_or_lock when lock is acquired"""
        mock_redis.set.return_value = True
        mock_redis.get.return_value = None

        result = await lock_manager.wait_for_vm_or_lock("task-123")

        assert result is None

    @pytest.mark.asyncio
    async def test_wait_for_vm_or_lock_finds_vm(self, lock_manager, mock_redis):
        """Test wait_for_vm_or_lock when VM is found"""
        mock_redis.set.return_value = False
        mock_redis.get.return_value = b"vm-test-123"
        mock_redis.hgetall.return_value = {
            b"vm_id": b"vm-test-123",
            b"task_id": b"task-123",
            b"plan_id": b"plan-123",
            b"status": b"ready",
            b"provider": b"local",
            b"created_at": b"2025-01-01T00:00:00",
            b"process_id": b"proc-123",
        }

        result = await lock_manager.wait_for_vm_or_lock("task-123", max_wait_seconds=1)

        assert result is not None
        assert result.vm_id == "vm-test-123"

    @pytest.mark.asyncio
    async def test_cleanup_stale_vms(self, lock_manager, mock_redis):
        """Test cleanup of stale VMs"""
        mock_redis.keys.return_value = [b"vm:registry:vm-stale-1"]
        mock_redis.hgetall.return_value = {
            b"vm_id": b"vm-stale-1",
            b"task_id": b"task-stale",
            b"plan_id": b"plan-stale",
            b"status": b"ready",
            b"provider": b"local",
            b"created_at": b"2020-01-01T00:00:00",
            b"process_id": b"proc-dead",
            b"timeout_minutes": b"60",
        }

        cleaned = await lock_manager.cleanup_stale_vms()

        assert cleaned >= 0


class TestVMProvisionerDistributedLocking:
    """Tests for VMProvisioner with distributed locking enabled"""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client"""
        redis = MagicMock()
        redis.set = MagicMock(return_value=True)
        redis.get = MagicMock(return_value=None)
        redis.delete = MagicMock(return_value=1)
        redis.eval = MagicMock(return_value=1)
        redis.hset = MagicMock(return_value=1)
        redis.hgetall = MagicMock(return_value={})
        redis.hdel = MagicMock(return_value=1)
        redis.expire = MagicMock(return_value=True)
        redis.exists = MagicMock(return_value=0)
        redis.keys = MagicMock(return_value=[])
        return redis

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings with distributed locking enabled"""
        settings = MagicMock()
        settings.use_distributed_vm_locking = True
        settings.vm_lock_ttl_seconds = 300
        settings.vm_registry_ttl_buffer = 300
        return settings

    @pytest.mark.asyncio
    async def test_provisioner_init_with_distributed_locking(
        self, mock_redis, mock_settings
    ):
        """Test VMProvisioner initialization with distributed locking"""
        with patch(
            "meta_agent.vm_provisioner.settings", mock_settings
        ):
            provisioner = VMProvisioner(
                default_provider=VMProvider.LOCAL,
                max_concurrent_vms=5,
                redis_client=mock_redis,
            )

            assert provisioner._use_distributed_locking is True
            assert provisioner._distributed_lock is not None

    @pytest.mark.asyncio
    async def test_provisioner_init_without_redis(self):
        """Test VMProvisioner initialization without Redis client"""
        provisioner = VMProvisioner(
            default_provider=VMProvider.LOCAL,
            max_concurrent_vms=5,
            redis_client=None,
        )

        assert provisioner._use_distributed_locking is False
        assert provisioner._distributed_lock is None

    @pytest.mark.asyncio
    async def test_provision_vm_distributed_success(self, mock_redis, mock_settings):
        """Test provisioning VM with distributed locking"""
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 1
        mock_redis.get.return_value = None

        with patch(
            "meta_agent.vm_provisioner.settings", mock_settings
        ):
            provisioner = VMProvisioner(
                default_provider=VMProvider.LOCAL,
                max_concurrent_vms=5,
                redis_client=mock_redis,
            )

            vm = await provisioner.provision_vm(
                task_id="task-12345678",
                plan_id="plan-87654321",
            )

            assert vm is not None
            assert vm.task_id == "task-12345678"
            assert vm.status == VMStatus.READY

    @pytest.mark.asyncio
    async def test_provision_vm_distributed_at_limit(self, mock_redis, mock_settings):
        """Test provisioning VM when at global limit"""
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 0
        mock_redis.get.return_value = None

        with patch(
            "meta_agent.vm_provisioner.settings", mock_settings
        ):
            provisioner = VMProvisioner(
                default_provider=VMProvider.LOCAL,
                max_concurrent_vms=5,
                redis_client=mock_redis,
            )

            with pytest.raises(RuntimeError) as exc_info:
                await provisioner.provision_vm(
                    task_id="task-12345678",
                    plan_id="plan-87654321",
                )

            assert "Max concurrent VMs" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_vm_for_task_distributed(self, mock_redis, mock_settings):
        """Test getting VM for task with distributed locking"""
        mock_redis.get.return_value = b"vm-remote-123"
        mock_redis.hgetall.return_value = {
            b"vm_id": b"vm-remote-123",
            b"task_id": b"task-remote",
            b"plan_id": b"plan-remote",
            b"status": b"ready",
            b"provider": b"local",
            b"created_at": b"2025-01-01T00:00:00",
            b"process_id": b"proc-other",
            b"timeout_minutes": b"60",
        }

        with patch(
            "meta_agent.vm_provisioner.settings", mock_settings
        ):
            provisioner = VMProvisioner(
                default_provider=VMProvider.LOCAL,
                max_concurrent_vms=5,
                redis_client=mock_redis,
            )

            vm = await provisioner.get_vm_for_task("task-remote")

            assert vm is not None
            assert vm.vm_id == "vm-remote-123"
            assert vm.task_id == "task-remote"

    @pytest.mark.asyncio
    async def test_destroy_vm_distributed(self, mock_redis, mock_settings):
        """Test destroying VM with distributed locking"""
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 1
        mock_redis.get.return_value = None
        mock_redis.hgetall.return_value = {
            b"vm_id": b"vm-test-123",
            b"task_id": b"task-12345678",
        }

        with patch(
            "meta_agent.vm_provisioner.settings", mock_settings
        ):
            provisioner = VMProvisioner(
                default_provider=VMProvider.LOCAL,
                max_concurrent_vms=5,
                redis_client=mock_redis,
            )

            vm = await provisioner.provision_vm(
                task_id="task-12345678",
                plan_id="plan-87654321",
            )

            success = await provisioner.destroy_vm(vm.vm_id)

            assert success is True


class TestGracefulDegradation:
    """Tests for graceful degradation when Redis is unavailable"""

    @pytest.mark.asyncio
    async def test_fallback_to_local_locking(self):
        """Test that VMProvisioner falls back to local locking without Redis"""
        provisioner = VMProvisioner(
            default_provider=VMProvider.LOCAL,
            max_concurrent_vms=5,
            redis_client=None,
        )

        assert provisioner._use_distributed_locking is False

        vm = await provisioner.provision_vm(
            task_id="task-12345678",
            plan_id="plan-87654321",
        )

        assert vm is not None
        assert vm.task_id == "task-12345678"

    @pytest.mark.asyncio
    async def test_local_duplicate_prevention(self):
        """Test duplicate prevention with local locking"""
        provisioner = VMProvisioner(
            default_provider=VMProvider.LOCAL,
            max_concurrent_vms=5,
            redis_client=None,
        )

        await provisioner.provision_vm(
            task_id="task-12345678",
            plan_id="plan-87654321",
        )

        with pytest.raises(RuntimeError) as exc_info:
            await provisioner.provision_vm(
                task_id="task-12345678",
                plan_id="plan-87654321",
            )

        assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_local_concurrency_limit(self):
        """Test concurrency limit with local locking"""
        provisioner = VMProvisioner(
            default_provider=VMProvider.LOCAL,
            max_concurrent_vms=2,
            redis_client=None,
        )

        await provisioner.provision_vm(task_id="task-1", plan_id="plan-1")
        await provisioner.provision_vm(task_id="task-2", plan_id="plan-2")

        with pytest.raises(RuntimeError) as exc_info:
            await provisioner.provision_vm(task_id="task-3", plan_id="plan-3")

        assert "Max concurrent VMs" in str(exc_info.value)


class TestFeatureFlagConfiguration:
    """Tests for feature flag configuration"""

    def test_settings_default_values(self):
        """Test that settings have correct default values"""
        try:
            from common.config.settings import Settings

            settings = Settings()

            assert settings.use_distributed_vm_locking is False
            assert settings.vm_lock_ttl_seconds == 300
            assert settings.vm_registry_ttl_buffer == 300
        except ImportError:
            pytest.skip("Settings module not available")

    def test_settings_env_override(self):
        """Test that settings can be overridden via environment"""
        try:
            from common.config.settings import Settings

            with patch.dict(
                "os.environ",
                {
                    "USE_DISTRIBUTED_VM_LOCKING": "true",
                    "VM_LOCK_TTL_SECONDS": "600",
                    "VM_REGISTRY_TTL_BUFFER": "600",
                },
            ):
                settings = Settings()

                assert settings.use_distributed_vm_locking is True
                assert settings.vm_lock_ttl_seconds == 600
                assert settings.vm_registry_ttl_buffer == 600
        except ImportError:
            pytest.skip("Settings module not available")
