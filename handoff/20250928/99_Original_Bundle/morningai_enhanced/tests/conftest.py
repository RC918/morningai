"""
pytest 配置文件
提供測試夾具和共用配置
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import redis

@pytest.fixture
def mock_database():
    """模擬資料庫連接"""
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def mock_redis():
    """模擬Redis連接"""
    return Mock(spec=redis.Redis)

@pytest.fixture
def mock_openai_client():
    """模擬OpenAI客戶端"""
    client = Mock()
    client.chat.completions.create = AsyncMock()
    return client

@pytest.fixture
def temp_config_file():
    """創建臨時配置文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
database_url: "sqlite:///:memory:"
redis_url: "redis://localhost:6379/0"
openai_api_key: "test-key"
log_level: "INFO"
""")
        temp_path = f.name
    
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def event_loop():
    """為異步測試提供事件循環"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def sample_metrics():
    """提供樣本指標數據"""
    return {
        "cpu_usage": 75.5,
        "memory_usage": 60.2,
        "response_time": 120.0,
        "error_rate": 0.05,
        "timestamp": "2024-01-01T12:00:00Z"
    }

@pytest.fixture
def sample_strategy():
    """提供樣本策略數據"""
    return {
        "id": "test_strategy_001",
        "name": "CPU優化策略",
        "description": "當CPU使用率超過80%時的優化策略",
        "conditions": {"cpu_usage": {"operator": ">", "value": 80}},
        "actions": [
            {"type": "scale_up", "parameters": {"instances": 2}},
            {"type": "optimize_cache", "parameters": {"ttl": 300}}
        ],
        "confidence_score": 0.85,
        "estimated_impact": {"cpu_reduction": 15, "cost_increase": 20}
    }

# 測試標記
pytest_plugins = []

def pytest_configure(config):
    """pytest配置"""
    config.addinivalue_line(
        "markers", "unit: 標記為單元測試"
    )
    config.addinivalue_line(
        "markers", "integration: 標記為集成測試"
    )
    config.addinivalue_line(
        "markers", "e2e: 標記為端到端測試"
    )
    config.addinivalue_line(
        "markers", "performance: 標記為性能測試"
    )
    config.addinivalue_line(
        "markers", "slow: 標記為慢速測試"
    )

