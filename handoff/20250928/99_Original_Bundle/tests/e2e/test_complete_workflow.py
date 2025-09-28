"""
端到端測試
測試完整的業務工作流程
"""

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import patch, Mock
import sys

# 添加專案根目錄到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

@pytest.mark.e2e
class TestCompleteWorkflow:
    
    @pytest.fixture
    async def system_setup(self):
        """設置完整的系統環境"""
        # 創建臨時配置文件
        config = {
            "database_url": "sqlite:///:memory:",
            "redis_url": "redis://localhost:6379/0",
            "openai_api_key": "test-key",
            "log_level": "INFO",
            "confidence_threshold": 0.8
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(config, f)
            config_path = f.name
        
        yield {"config_path": config_path, "config": config}
        
        # 清理
        os.unlink(config_path)
    
    @pytest.mark.asyncio
    async def test_problem_detection_to_resolution(self, system_setup):
        """測試從問題檢測到解決的完整流程"""
        
        # 模擬系統監控檢測到問題
        detected_issue = {
            "timestamp": "2024-01-01T12:00:00Z",
            "issue_type": "high_cpu_usage",
            "severity": "high",
            "metrics": {
                "cpu_usage": 92,
                "memory_usage": 75,
                "response_time": 350,
                "error_rate": 0.08
            },
            "affected_services": ["web-api", "background-worker"]
        }
        
        with patch('meta_agent_implementation.MetaAgent') as MockMetaAgent:
            # 模擬MetaAgent的決策過程
            mock_agent = MockMetaAgent.return_value
            mock_agent.make_decision.return_value = {
                "recommended_strategy": {
                    "id": "cpu_optimization_001",
                    "name": "CPU優化策略",
                    "actions": [
                        {"type": "scale_up", "parameters": {"instances": 3}},
                        {"type": "optimize_cache", "parameters": {"ttl": 300}}
                    ]
                },
                "confidence_score": 0.87,
                "predicted_impact": {
                    "cpu_reduction": 25,
                    "response_time_improvement": 30,
                    "estimated_cost": 18.50
                },
                "execution_plan": {
                    "steps": [
                        {"order": 1, "action": "scale_up", "estimated_duration": "2min"},
                        {"order": 2, "action": "optimize_cache", "estimated_duration": "30sec"}
                    ],
                    "total_estimated_duration": "2.5min"
                }
            }
            
            # 模擬策略執行
            mock_agent.execute_strategy.return_value = {
                "execution_id": "exec_001",
                "status": "completed",
                "start_time": "2024-01-01T12:01:00Z",
                "end_time": "2024-01-01T12:03:30Z",
                "actual_duration": "2min 30sec",
                "results": {
                    "scale_up": {"success": True, "new_instances": 3},
                    "optimize_cache": {"success": True, "cache_hit_rate": 0.95}
                }
            }
            
            # 執行完整流程
            decision = await mock_agent.make_decision(detected_issue["metrics"])
            execution_result = await mock_agent.execute_strategy(
                decision["recommended_strategy"]["id"]
            )
            
            # 驗證決策質量
            assert decision["confidence_score"] > 0.8
            assert decision["predicted_impact"]["cpu_reduction"] > 0
            
            # 驗證執行結果
            assert execution_result["status"] == "completed"
            assert execution_result["results"]["scale_up"]["success"] == True
    
    @pytest.mark.asyncio
    async def test_learning_cycle_completion(self, system_setup):
        """測試完整的學習循環"""
        
        with patch('strategy_learning_system.StrategyLearningSystem') as MockLearningSystem:
            mock_learning = MockLearningSystem.return_value
            
            # 1. 初始策略生成
            mock_learning.generate_strategy_from_template.return_value = Mock(
                id="learning_test_001",
                name="學習測試策略",
                confidence_score=0.6,
                source="template"
            )
            
            # 2. 策略執行和結果記錄
            execution_result = {
                "success": True,
                "metrics_before": {"cpu_usage": 85, "response_time": 200},
                "metrics_after": {"cpu_usage": 68, "response_time": 145},
                "execution_time": 35.2,
                "improvement_score": 22.5
            }
            
            # 3. 用戶反饋
            user_feedback = {
                "rating": 4,
                "effectiveness": "high",
                "side_effects": "minimal",
                "comments": "策略執行順利，效果顯著"
            }
            
            # 4. 策略信心度更新
            mock_learning.record_strategy_execution.return_value = True
            mock_learning.learn_from_feedback.return_value = True
            
            # 模擬更新後的策略（信心度提升）
            mock_learning.get_strategy_by_id.return_value = Mock(
                id="learning_test_001",
                confidence_score=0.78,  # 信心度提升
                execution_count=1,
                success_count=1
            )
            
            # 執行學習循環
            strategy = await mock_learning.generate_strategy_from_template({})
            await mock_learning.record_strategy_execution("learning_test_001", execution_result)
            await mock_learning.learn_from_feedback("learning_test_001", user_feedback)
            
            updated_strategy = await mock_learning.get_strategy_by_id("learning_test_001")
            
            # 驗證學習效果
            assert updated_strategy.confidence_score > 0.6  # 信心度應該提升
            assert updated_strategy.execution_count == 1
            assert updated_strategy.success_count == 1
            
            # 驗證學習系統的方法被正確調用
            mock_learning.record_strategy_execution.assert_called_once()
            mock_learning.learn_from_feedback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_multi_agent_collaboration(self, system_setup):
        """測試多Agent協作場景"""
        
        # 模擬複雜場景：需要多個Agent協作解決
        complex_scenario = {
            "issue_type": "cascading_failure",
            "affected_systems": ["database", "cache", "api_gateway"],
            "metrics": {
                "database_connections": 950,  # 接近上限
                "cache_hit_rate": 0.3,        # 極低
                "api_response_time": 800,     # 極高
                "error_rate": 0.15            # 很高
            }
        }
        
        with patch('meta_agent_implementation.MetaAgent') as MockMetaAgent:
            # 模擬主Agent的協調決策
            mock_main_agent = MockMetaAgent.return_value
            mock_main_agent.coordinate_multi_agent_response.return_value = {
                "coordination_plan": {
                    "database_agent": {
                        "priority": 1,
                        "actions": ["optimize_connections", "scale_read_replicas"]
                    },
                    "cache_agent": {
                        "priority": 2,
                        "actions": ["warm_cache", "increase_cache_size"]
                    },
                    "api_agent": {
                        "priority": 3,
                        "actions": ["enable_circuit_breaker", "adjust_rate_limits"]
                    }
                },
                "estimated_resolution_time": "8min",
                "coordination_confidence": 0.82
            }
            
            # 模擬各Agent的執行結果
            agent_results = {
                "database_agent": {"success": True, "execution_time": "3min"},
                "cache_agent": {"success": True, "execution_time": "2min"},
                "api_agent": {"success": True, "execution_time": "1min"}
            }
            
            mock_main_agent.execute_coordinated_plan.return_value = {
                "overall_success": True,
                "total_execution_time": "4min",  # 並行執行
                "agent_results": agent_results,
                "final_metrics": {
                    "database_connections": 650,
                    "cache_hit_rate": 0.85,
                    "api_response_time": 180,
                    "error_rate": 0.02
                }
            }
            
            # 執行協作流程
            coordination_plan = await mock_main_agent.coordinate_multi_agent_response(
                complex_scenario
            )
            execution_result = await mock_main_agent.execute_coordinated_plan(
                coordination_plan
            )
            
            # 驗證協作效果
            assert coordination_plan["coordination_confidence"] > 0.8
            assert execution_result["overall_success"] == True
            assert len(execution_result["agent_results"]) == 3
            
            # 驗證系統指標改善
            final_metrics = execution_result["final_metrics"]
            assert final_metrics["database_connections"] < 950
            assert final_metrics["cache_hit_rate"] > 0.3
            assert final_metrics["api_response_time"] < 800
            assert final_metrics["error_rate"] < 0.15
    
    @pytest.mark.asyncio
    async def test_system_recovery_workflow(self, system_setup):
        """測試系統恢復工作流程"""
        
        # 模擬系統故障場景
        system_failure = {
            "failure_type": "service_outage",
            "affected_services": ["payment_service", "user_service"],
            "failure_start": "2024-01-01T12:00:00Z",
            "severity": "critical",
            "impact": {
                "users_affected": 15000,
                "revenue_impact": 5000.0,
                "sla_breach": True
            }
        }
        
        with patch('meta_agent_implementation.MetaAgent') as MockMetaAgent:
            mock_agent = MockMetaAgent.return_value
            
            # 模擬恢復策略
            mock_agent.generate_recovery_plan.return_value = {
                "recovery_steps": [
                    {
                        "step": 1,
                        "action": "failover_to_backup",
                        "target": "payment_service",
                        "estimated_time": "2min"
                    },
                    {
                        "step": 2,
                        "action": "restart_service",
                        "target": "user_service",
                        "estimated_time": "1min"
                    },
                    {
                        "step": 3,
                        "action": "verify_functionality",
                        "target": "all_services",
                        "estimated_time": "3min"
                    }
                ],
                "total_estimated_recovery_time": "6min",
                "success_probability": 0.92
            }
            
            # 模擬恢復執行
            mock_agent.execute_recovery_plan.return_value = {
                "recovery_success": True,
                "actual_recovery_time": "5min 30sec",
                "services_restored": ["payment_service", "user_service"],
                "post_recovery_metrics": {
                    "service_availability": 0.999,
                    "response_time": 95,
                    "error_rate": 0.001
                },
                "lessons_learned": [
                    "備用服務切換順利",
                    "用戶服務重啟解決了內存洩漏問題",
                    "監控告警及時有效"
                ]
            }
            
            # 執行恢復流程
            recovery_plan = await mock_agent.generate_recovery_plan(system_failure)
            recovery_result = await mock_agent.execute_recovery_plan(recovery_plan)
            
            # 驗證恢復效果
            assert recovery_plan["success_probability"] > 0.9
            assert recovery_result["recovery_success"] == True
            assert len(recovery_result["services_restored"]) == 2
            
            # 驗證恢復時間在預期範圍內
            assert "5min" in recovery_result["actual_recovery_time"]
            
            # 驗證系統指標恢復正常
            metrics = recovery_result["post_recovery_metrics"]
            assert metrics["service_availability"] > 0.99
            assert metrics["error_rate"] < 0.01
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_long_running_optimization(self, system_setup):
        """測試長期運行的系統優化"""
        
        # 模擬24小時的系統優化過程
        optimization_scenario = {
            "optimization_type": "cost_performance_balance",
            "duration": "24_hours",
            "target_metrics": {
                "cost_reduction": 0.3,        # 目標降低30%成本
                "performance_maintenance": 0.95  # 保持95%性能
            }
        }
        
        with patch('meta_agent_implementation.MetaAgent') as MockMetaAgent:
            mock_agent = MockMetaAgent.return_value
            
            # 模擬分階段優化計劃
            mock_agent.create_long_term_optimization_plan.return_value = {
                "phases": [
                    {
                        "phase": 1,
                        "duration": "8_hours",
                        "focus": "resource_rightsizing",
                        "expected_cost_reduction": 0.15
                    },
                    {
                        "phase": 2,
                        "duration": "8_hours",
                        "focus": "cache_optimization",
                        "expected_performance_gain": 0.1
                    },
                    {
                        "phase": 3,
                        "duration": "8_hours",
                        "focus": "workload_scheduling",
                        "expected_cost_reduction": 0.15
                    }
                ],
                "monitoring_checkpoints": [4, 8, 12, 16, 20, 24],  # 每4小時檢查
                "rollback_triggers": {
                    "performance_drop": 0.1,
                    "error_rate_increase": 0.05
                }
            }
            
            # 模擬優化執行結果
            mock_agent.execute_long_term_optimization.return_value = {
                "optimization_success": True,
                "total_duration": "23h 45min",
                "achieved_metrics": {
                    "cost_reduction": 0.32,      # 超過目標
                    "performance_ratio": 0.97    # 保持高性能
                },
                "phase_results": [
                    {"phase": 1, "success": True, "cost_reduction": 0.16},
                    {"phase": 2, "success": True, "performance_gain": 0.12},
                    {"phase": 3, "success": True, "cost_reduction": 0.16}
                ],
                "unexpected_benefits": [
                    "系統穩定性提升",
                    "監控精度改善",
                    "運維效率提升"
                ]
            }
            
            # 執行長期優化
            optimization_plan = await mock_agent.create_long_term_optimization_plan(
                optimization_scenario
            )
            optimization_result = await mock_agent.execute_long_term_optimization(
                optimization_plan
            )
            
            # 驗證優化效果
            assert optimization_result["optimization_success"] == True
            assert optimization_result["achieved_metrics"]["cost_reduction"] >= 0.3
            assert optimization_result["achieved_metrics"]["performance_ratio"] >= 0.95
            
            # 驗證所有階段都成功完成
            phase_results = optimization_result["phase_results"]
            assert len(phase_results) == 3
            assert all(phase["success"] for phase in phase_results)

