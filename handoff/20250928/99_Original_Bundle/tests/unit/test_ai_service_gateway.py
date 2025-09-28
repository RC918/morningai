"""
AI服務網關單元測試
測試AIServiceGateway的核心功能
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# 添加專案根目錄到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ai_service_gateway import AIServiceGateway, ModelConfig, RoutingStrategy

@pytest.mark.unit
class TestAIServiceGateway:
    
    @pytest.fixture
    def gateway_config(self):
        """測試用的網關配置"""
        return {
            "openai_api_key": "test-key",
            "default_model": "gpt-3.5-turbo",
            "max_retries": 3,
            "timeout": 30,
            "cost_tracking": True
        }
    
    @pytest.fixture
    def gateway(self, gateway_config):
        """創建測試用的網關實例"""
        return AIServiceGateway(gateway_config)
    
    def test_gateway_initialization(self, gateway):
        """測試網關初始化"""
        assert gateway.config["default_model"] == "gpt-3.5-turbo"
        assert gateway.config["max_retries"] == 3
        assert gateway.total_cost == 0.0
        assert len(gateway.model_configs) > 0
    
    def test_model_config_creation(self):
        """測試模型配置創建"""
        config = ModelConfig(
            name="gpt-4",
            provider="openai",
            cost_per_token=0.00003,
            max_tokens=8192,
            capabilities=["chat", "reasoning"]
        )
        
        assert config.name == "gpt-4"
        assert config.provider == "openai"
        assert config.cost_per_token == 0.00003
        assert "reasoning" in config.capabilities
    
    @pytest.mark.asyncio
    async def test_route_request_by_cost(self, gateway):
        """測試基於成本的路由"""
        # 模擬不同成本的模型
        with patch.object(gateway, '_get_model_cost') as mock_cost:
            mock_cost.side_effect = lambda model: {
                "gpt-3.5-turbo": 0.001,
                "gpt-4": 0.03,
                "claude-3": 0.015
            }.get(model, 0.01)
            
            selected_model = gateway._route_by_cost(["gpt-3.5-turbo", "gpt-4", "claude-3"])
            assert selected_model == "gpt-3.5-turbo"  # 最便宜的模型
    
    @pytest.mark.asyncio
    async def test_route_request_by_capability(self, gateway):
        """測試基於能力的路由"""
        # 模擬需要推理能力的請求
        request_requirements = ["reasoning", "long_context"]
        
        with patch.object(gateway, '_get_model_capabilities') as mock_capabilities:
            mock_capabilities.side_effect = lambda model: {
                "gpt-3.5-turbo": ["chat"],
                "gpt-4": ["chat", "reasoning", "long_context"],
                "claude-3": ["chat", "reasoning"]
            }.get(model, [])
            
            selected_model = gateway._route_by_capability(
                ["gpt-3.5-turbo", "gpt-4", "claude-3"], 
                request_requirements
            )
            assert selected_model == "gpt-4"  # 唯一滿足所有要求的模型
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, gateway):
        """測試成功生成回應"""
        with patch.object(gateway, '_call_openai_api') as mock_api:
            mock_api.return_value = {
                "choices": [{"message": {"content": "測試回應"}}],
                "usage": {"total_tokens": 100}
            }
            
            response = await gateway.generate_response(
                prompt="測試提示",
                model="gpt-3.5-turbo"
            )
            
            assert response["content"] == "測試回應"
            assert response["model"] == "gpt-3.5-turbo"
            assert response["tokens_used"] == 100
    
    @pytest.mark.asyncio
    async def test_generate_response_with_retry(self, gateway):
        """測試重試機制"""
        with patch.object(gateway, '_call_openai_api') as mock_api:
            # 前兩次調用失敗，第三次成功
            mock_api.side_effect = [
                Exception("API錯誤"),
                Exception("網絡錯誤"),
                {
                    "choices": [{"message": {"content": "重試成功"}}],
                    "usage": {"total_tokens": 50}
                }
            ]
            
            response = await gateway.generate_response(
                prompt="測試提示",
                model="gpt-3.5-turbo"
            )
            
            assert response["content"] == "重試成功"
            assert mock_api.call_count == 3
    
    @pytest.mark.asyncio
    async def test_cost_tracking(self, gateway):
        """測試成本追蹤"""
        initial_cost = gateway.total_cost
        
        with patch.object(gateway, '_call_openai_api') as mock_api:
            mock_api.return_value = {
                "choices": [{"message": {"content": "測試"}}],
                "usage": {"total_tokens": 1000}
            }
            
            await gateway.generate_response(
                prompt="測試提示",
                model="gpt-3.5-turbo"
            )
            
            # 驗證成本有增加
            assert gateway.total_cost > initial_cost
    
    def test_get_cost_statistics(self, gateway):
        """測試成本統計"""
        # 模擬一些成本數據
        gateway.total_cost = 15.75
        gateway.request_count = 100
        
        stats = gateway.get_cost_statistics()
        
        assert stats["total_cost"] == 15.75
        assert stats["request_count"] == 100
        assert stats["average_cost_per_request"] == 0.1575
    
    @pytest.mark.asyncio
    async def test_intelligent_routing(self, gateway):
        """測試智能路由"""
        request_context = {
            "complexity": "high",
            "budget_limit": 0.05,
            "required_capabilities": ["reasoning"]
        }
        
        with patch.object(gateway, '_analyze_request_complexity') as mock_analyze:
            mock_analyze.return_value = "high"
            
            with patch.object(gateway, '_select_optimal_model') as mock_select:
                mock_select.return_value = "gpt-4"
                
                selected_model = await gateway.intelligent_route(
                    prompt="複雜的推理問題",
                    context=request_context
                )
                
                assert selected_model == "gpt-4"
                mock_analyze.assert_called_once()
                mock_select.assert_called_once()
    
    def test_fallback_mechanism(self, gateway):
        """測試降級機制"""
        failed_models = ["gpt-4", "claude-3"]
        
        fallback_model = gateway._get_fallback_model(failed_models)
        
        # 應該返回一個不在失敗列表中的模型
        assert fallback_model not in failed_models
        assert fallback_model in gateway.available_models
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, gateway):
        """測試並發請求處理"""
        with patch.object(gateway, '_call_openai_api') as mock_api:
            mock_api.return_value = {
                "choices": [{"message": {"content": "並發測試"}}],
                "usage": {"total_tokens": 50}
            }
            
            # 創建多個並發請求
            tasks = [
                gateway.generate_response(f"請求 {i}", "gpt-3.5-turbo")
                for i in range(5)
            ]
            
            responses = await asyncio.gather(*tasks)
            
            assert len(responses) == 5
            assert all(r["content"] == "並發測試" for r in responses)
            assert mock_api.call_count == 5

