#!/usr/bin/env python3
"""Tests for task router"""
import pytest
from unittest.mock import Mock, AsyncMock

from orchestrator.api.router import OrchestratorRouter
from orchestrator.schemas.task_schema import UnifiedTask, TaskType, TaskPriority


class TestOrchestratorRouter:
    """Test OrchestratorRouter"""
    
    @pytest.fixture
    def router(self):
        """Create router instance"""
        redis_queue = Mock()
        return OrchestratorRouter(redis_queue)
    
    def test_route_faq_task(self, router):
        """Test routing FAQ task"""
        task = UnifiedTask(type=TaskType.FAQ, payload={"question": "How?"})
        agent = router.route_task(task)
        assert agent == "faq_agent"
    
    def test_route_kb_update_task(self, router):
        """Test routing KB update task"""
        task = UnifiedTask(type=TaskType.KB_UPDATE, payload={})
        agent = router.route_task(task)
        assert agent == "faq_agent"
    
    def test_route_bugfix_task(self, router):
        """Test routing bugfix task"""
        task = UnifiedTask(type=TaskType.BUGFIX, payload={"issue": "123"})
        agent = router.route_task(task)
        assert agent == "dev_agent"
    
    def test_route_refactor_task(self, router):
        """Test routing refactor task"""
        task = UnifiedTask(type=TaskType.REFACTOR, payload={})
        agent = router.route_task(task)
        assert agent == "dev_agent"
    
    def test_route_feature_task(self, router):
        """Test routing feature task"""
        task = UnifiedTask(type=TaskType.FEATURE, payload={})
        agent = router.route_task(task)
        assert agent == "dev_agent"
    
    def test_route_deploy_task(self, router):
        """Test routing deploy task"""
        task = UnifiedTask(type=TaskType.DEPLOY, payload={"env": "prod"})
        agent = router.route_task(task)
        assert agent == "ops_agent"
    
    def test_route_monitor_task(self, router):
        """Test routing monitor task"""
        task = UnifiedTask(type=TaskType.MONITOR, payload={})
        agent = router.route_task(task)
        assert agent == "ops_agent"
    
    def test_route_alert_task(self, router):
        """Test routing alert task"""
        task = UnifiedTask(type=TaskType.ALERT, payload={})
        agent = router.route_task(task)
        assert agent == "ops_agent"
    
    def test_register_custom_rule(self, router):
        """Test registering custom routing rule"""
        router.register_custom_rule(TaskType.INVESTIGATE, "custom_agent")
        
        task = UnifiedTask(type=TaskType.INVESTIGATE, payload={})
        agent = router.route_task(task)
        
        assert agent == "custom_agent"
    
    def test_get_routing_rules(self, router):
        """Test getting routing rules"""
        rules = router.get_routing_rules()
        
        assert "faq" in rules
        assert "bugfix" in rules
        assert "deploy" in rules
        assert rules["faq"] == "faq_agent"
        assert rules["bugfix"] == "dev_agent"
        assert rules["deploy"] == "ops_agent"
