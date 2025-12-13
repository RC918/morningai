# Testing Best Practices

本文檔提供 MorningAI 專案的測試最佳實踐和指南。

## 目錄

- [測試策略概覽](#測試策略概覽)
- [測試類型](#測試類型)
- [測試目錄結構](#測試目錄結構)
- [編寫測試](#編寫測試)
- [JWT 認證測試](#jwt-認證測試)
- [Mock 和 Fixtures](#mock-和-fixtures)
- [測試覆蓋率](#測試覆蓋率)
- [CI/CD 整合](#cicd-整合)
- [常見問題](#常見問題)

## 測試策略概覽

MorningAI 採用三層測試策略，平衡測試速度、覆蓋率和可靠性：

```
┌─────────────────────────────────────────────────┐
│                  E2E Tests                      │
│         (關鍵路徑 100% 覆蓋)                     │
│              5-30 秒/測試                        │
└─────────────────────────────────────────────────┘
                      ▲
                      │
┌─────────────────────────────────────────────────┐
│            Integration Tests                    │
│              (60%+ 覆蓋)                        │
│              1-5 秒/測試                         │
└─────────────────────────────────────────────────┘
                      ▲
                      │
┌─────────────────────────────────────────────────┐
│              Unit Tests                         │
│              (80%+ 覆蓋)                        │
│              < 1 秒/測試                         │
└─────────────────────────────────────────────────┘
```

### 測試金字塔原則

- **單元測試 (70%)**: 快速、隔離、大量
- **整合測試 (20%)**: 中等速度、測試協作
- **E2E 測試 (10%)**: 慢速、測試關鍵流程

## 測試類型

### 1. 單元測試 (Unit Tests)

**目的**: 測試單一函式、類別或模組的邏輯

**特性**:
- ✅ 使用 mock 隔離所有外部依賴
- ✅ 快速執行（< 1 秒）
- ✅ 測試邊界條件和錯誤處理
- ✅ 覆蓋率目標: 80%+

**目錄**: `tests/unit/`

**範例**:

```python
# tests/unit/services/test_monitoring_unit.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.monitoring_dashboard import MonitoringDashboard

@pytest.fixture
def mock_state_manager():
    """Mock PersistentStateManager"""
    mock = MagicMock()
    mock.get_state.return_value = {'status': 'healthy'}
    return mock

@pytest.fixture
def mock_resilience_manager():
    """Mock resilience_manager"""
    mock = MagicMock()
    mock.get_stats.return_value = {
        'success_count': 100,
        'failure_count': 5
    }
    return mock

def test_collect_metrics_success(mock_state_manager, mock_resilience_manager):
    """測試 metrics 收集成功情境"""
    with patch('src.services.monitoring_dashboard.resilience_manager', mock_resilience_manager):
        with patch('src.services.monitoring_dashboard.PersistentStateManager', return_value=mock_state_manager):
            dashboard = MonitoringDashboard()
            metrics = dashboard.collect_metrics()
            
            assert metrics.success_count == 100
            assert metrics.failure_count == 5
            assert metrics.success_rate == 0.95

def test_collect_metrics_handles_error(mock_state_manager):
    """測試 metrics 收集錯誤處理"""
    mock_state_manager.get_state.side_effect = Exception("Database error")
    
    with patch('src.services.monitoring_dashboard.PersistentStateManager', return_value=mock_state_manager):
        dashboard = MonitoringDashboard()
        
        with pytest.raises(Exception) as exc_info:
            dashboard.collect_metrics()
        
        assert "Database error" in str(exc_info.value)

def test_calculate_success_rate_edge_cases():
    """測試成功率計算邊界條件"""
    dashboard = MonitoringDashboard()
    
    # 零除錯誤
    assert dashboard.calculate_success_rate(0, 0) == 0.0
    
    # 100% 成功
    assert dashboard.calculate_success_rate(100, 0) == 1.0
    
    # 0% 成功
    assert dashboard.calculate_success_rate(0, 100) == 0.0
```

**何時使用單元測試**:
- ✅ 測試業務邏輯
- ✅ 測試資料轉換和計算
- ✅ 測試錯誤處理
- ✅ 測試邊界條件
- ✅ 測試工具函式

**何時不使用單元測試**:
- ❌ 測試 API endpoints（使用整合測試）
- ❌ 測試資料庫操作（使用整合測試）
- ❌ 測試完整使用者流程（使用 E2E 測試）

---

### 2. 整合測試 (Integration Tests)

**目的**: 測試多個模組的協作和整合

**特性**:
- ✅ 使用真實 Flask app
- ✅ 使用真實 JWT token
- ✅ 測試 API endpoints
- ✅ 中等執行速度（1-5 秒）
- ✅ 覆蓋率目標: 60%+

**目錄**: `tests/integration/`

**範例**:

```python
# tests/integration/routes/test_vectors_integration.py
import pytest
from src.main import app
from src.middleware.auth_middleware import create_admin_token

@pytest.fixture
def client():
    """建立測試 client"""
    app.config['TESTING'] = True
    app.config['JWT_SECRET'] = 'test-secret-do-not-use-in-production'
    return app.test_client()

@pytest.fixture
def auth_headers():
    """建立認證 headers"""
    token = create_admin_token()
    return {'Authorization': f'Bearer {token}'}

def test_vector_search_requires_authentication(client):
    """測試 vector 搜尋需要認證"""
    response = client.post('/api/vectors/search', 
                          json={'query': 'test'})
    assert response.status_code == 401
    assert 'Missing Authorization Header' in response.json['error']

def test_vector_search_with_valid_token(client, auth_headers):
    """測試使用有效 token 進行 vector 搜尋"""
    response = client.post('/api/vectors/search', 
                          json={'query': 'test query'},
                          headers=auth_headers)
    assert response.status_code == 200
    assert 'results' in response.json

def test_vector_search_with_invalid_token(client):
    """測試使用無效 token 進行 vector 搜尋"""
    response = client.post('/api/vectors/search', 
                          json={'query': 'test'},
                          headers={'Authorization': 'Bearer invalid-token'})
    assert response.status_code == 401

def test_vector_search_validates_input(client, auth_headers):
    """測試 vector 搜尋驗證輸入"""
    # 缺少 query 參數
    response = client.post('/api/vectors/search', 
                          json={},
                          headers=auth_headers)
    assert response.status_code == 400
    
    # query 為空字串
    response = client.post('/api/vectors/search', 
                          json={'query': ''},
                          headers=auth_headers)
    assert response.status_code == 400

def test_vector_search_returns_correct_format(client, auth_headers):
    """測試 vector 搜尋返回正確格式"""
    response = client.post('/api/vectors/search', 
                          json={'query': 'test'},
                          headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json
    assert 'results' in data
    assert isinstance(data['results'], list)
    
    if len(data['results']) > 0:
        result = data['results'][0]
        assert 'id' in result
        assert 'score' in result
        assert 'content' in result
```

**何時使用整合測試**:
- ✅ 測試 API endpoints
- ✅ 測試認證和授權
- ✅ 測試多個服務的協作
- ✅ 測試資料庫操作
- ✅ 測試中介軟體

**何時不使用整合測試**:
- ❌ 測試純業務邏輯（使用單元測試）
- ❌ 測試完整使用者流程（使用 E2E 測試）

---

### 3. E2E 測試 (End-to-End Tests)

**目的**: 測試完整使用者流程和系統整合

**特性**:
- ✅ 測試完整使用者旅程
- ✅ 使用真實資料庫和服務
- ✅ 較慢執行速度（5-30 秒）
- ✅ 覆蓋率目標: 關鍵路徑 100%

**目錄**: `tests/integration/e2e/`

**範例**:

```python
# tests/integration/e2e/test_full_workflow.py
import pytest
from src.main import app
from src.models import User, Vector

@pytest.fixture
def client():
    """建立測試 client"""
    app.config['TESTING'] = True
    return app.test_client()

@pytest.fixture
def db_session():
    """建立測試資料庫 session"""
    # 設置測試資料庫
    from src.database import db
    db.create_all()
    yield db.session
    db.session.remove()
    db.drop_all()

def test_complete_user_journey(client, db_session):
    """測試完整使用者流程：註冊 -> 登入 -> 搜尋 -> 查看結果"""
    
    # 1. 註冊新使用者
    response = client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'SecurePassword123!',
        'name': 'Test User'
    })
    assert response.status_code == 201
    assert 'user_id' in response.json
    user_id = response.json['user_id']
    
    # 2. 登入
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'SecurePassword123!'
    })
    assert response.status_code == 200
    assert 'token' in response.json
    token = response.json['token']
    
    # 3. 使用 token 進行 vector 搜尋
    auth_headers = {'Authorization': f'Bearer {token}'}
    response = client.post('/api/vectors/search', 
                          json={'query': 'machine learning'},
                          headers=auth_headers)
    assert response.status_code == 200
    assert 'results' in response.json
    
    # 4. 查看搜尋結果詳情
    if len(response.json['results']) > 0:
        vector_id = response.json['results'][0]['id']
        response = client.get(f'/api/vectors/{vector_id}',
                             headers=auth_headers)
        assert response.status_code == 200
        assert response.json['id'] == vector_id
    
    # 5. 登出
    response = client.post('/api/auth/logout',
                          headers=auth_headers)
    assert response.status_code == 200
    
    # 6. 驗證 token 已失效
    response = client.post('/api/vectors/search', 
                          json={'query': 'test'},
                          headers=auth_headers)
    assert response.status_code == 401

def test_error_recovery_workflow(client):
    """測試錯誤恢復流程"""
    
    # 1. 嘗試使用無效 token
    response = client.post('/api/vectors/search', 
                          json={'query': 'test'},
                          headers={'Authorization': 'Bearer invalid'})
    assert response.status_code == 401
    
    # 2. 正確登入
    response = client.post('/api/auth/login', json={
        'email': 'admin@example.com',
        'password': 'admin'
    })
    assert response.status_code == 200
    token = response.json['token']
    
    # 3. 使用有效 token 重試
    auth_headers = {'Authorization': f'Bearer {token}'}
    response = client.post('/api/vectors/search', 
                          json={'query': 'test'},
                          headers=auth_headers)
    assert response.status_code == 200
```

**何時使用 E2E 測試**:
- ✅ 測試關鍵使用者流程
- ✅ 測試跨模組整合
- ✅ 部署前驗證
- ✅ 測試錯誤恢復流程

**何時不使用 E2E 測試**:
- ❌ 測試單一功能（使用單元測試）
- ❌ 測試 API endpoints（使用整合測試）
- ❌ 快速反饋循環（太慢）

## 測試目錄結構

```
tests/
├── unit/                           # 單元測試
│   ├── routes/
│   │   ├── test_vectors_unit.py
│   │   ├── test_faq_unit.py
│   │   └── test_monitoring_unit.py
│   ├── services/
│   │   ├── test_monitoring_service_unit.py
│   │   └── test_vector_service_unit.py
│   └── utils/
│       ├── test_validators_unit.py
│       └── test_helpers_unit.py
│
├── integration/                    # 整合測試
│   ├── routes/
│   │   ├── test_vectors_integration.py
│   │   ├── test_faq_integration.py
│   │   └── test_monitoring_integration.py
│   └── e2e/
│       ├── test_full_workflow.py
│       └── test_error_recovery.py
│
├── fixtures/                       # 共用 fixtures
│   ├── __init__.py
│   ├── auth.py                    # 認證相關 fixtures
│   ├── database.py                # 資料庫相關 fixtures
│   └── mock_data.py               # 測試資料
│
├── conftest.py                    # pytest 配置
└── pytest.ini                     # pytest 設定
```

## 編寫測試

### 測試命名規範

**格式**: `test_<function_name>_<scenario>_<expected_result>`

```python
# ✅ 好的測試名稱
def test_collect_metrics_with_valid_data_returns_dashboard_metrics():
    """測試使用有效資料收集 metrics 返回 DashboardMetrics 物件"""
    pass

def test_vector_search_without_auth_returns_401():
    """測試未認證的 vector 搜尋返回 401"""
    pass

def test_calculate_success_rate_with_zero_total_returns_zero():
    """測試總數為零時計算成功率返回 0"""
    pass

# ❌ 不好的測試名稱
def test_1():
    pass

def test_monitoring():
    pass

def test_it_works():
    pass
```

### 測試結構 (AAA Pattern)

使用 **Arrange-Act-Assert** 模式：

```python
def test_vector_search_with_valid_query():
    # Arrange (準備)
    client = app.test_client()
    auth_headers = {'Authorization': f'Bearer {create_admin_token()}'}
    query = {'query': 'machine learning'}
    
    # Act (執行)
    response = client.post('/api/vectors/search', 
                          json=query,
                          headers=auth_headers)
    
    # Assert (驗證)
    assert response.status_code == 200
    assert 'results' in response.json
    assert isinstance(response.json['results'], list)
```

### 測試獨立性

每個測試應該獨立運行，不依賴其他測試：

```python
# ✅ 好的做法 - 每個測試獨立
def test_create_user():
    user = create_user('test@example.com')
    assert user.email == 'test@example.com'

def test_delete_user():
    user = create_user('test2@example.com')  # 建立自己的測試資料
    delete_user(user.id)
    assert get_user(user.id) is None

# ❌ 不好的做法 - 測試相互依賴
user_id = None

def test_create_user():
    global user_id
    user = create_user('test@example.com')
    user_id = user.id
    assert user.email == 'test@example.com'

def test_delete_user():
    global user_id
    delete_user(user_id)  # 依賴前一個測試
    assert get_user(user_id) is None
```

### 測試邊界條件

確保測試覆蓋邊界條件和錯誤情況：

```python
def test_calculate_success_rate_edge_cases():
    """測試成功率計算的邊界條件"""
    dashboard = MonitoringDashboard()
    
    # 正常情況
    assert dashboard.calculate_success_rate(80, 20) == 0.8
    
    # 邊界條件
    assert dashboard.calculate_success_rate(0, 0) == 0.0      # 零除錯誤
    assert dashboard.calculate_success_rate(100, 0) == 1.0    # 100% 成功
    assert dashboard.calculate_success_rate(0, 100) == 0.0    # 0% 成功
    
    # 錯誤情況
    with pytest.raises(ValueError):
        dashboard.calculate_success_rate(-1, 10)  # 負數
    
    with pytest.raises(ValueError):
        dashboard.calculate_success_rate(10, -1)  # 負數
```

## JWT 認證測試

### 測試環境 JWT Secret

**重要**: 測試環境必須使用獨立的 JWT secret，不得使用生產環境 secret。

```python
# tests/fixtures/auth.py
import os
import pytest

@pytest.fixture(autouse=True)
def test_jwt_secret():
    """確保測試環境使用獨立的 JWT secret"""
    original_secret = os.environ.get('JWT_SECRET')
    os.environ['JWT_SECRET'] = 'test-secret-do-not-use-in-production'
    
    yield
    
    # 清理
    if original_secret:
        os.environ['JWT_SECRET'] = original_secret
    elif 'JWT_SECRET' in os.environ:
        del os.environ['JWT_SECRET']
```

### 單元測試中的 JWT

**使用 mock** 避免依賴真實 JWT 實作：

```python
# tests/unit/routes/test_vectors_unit.py
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_jwt_required():
    """Mock JWT 認證裝飾器"""
    with patch('src.middleware.auth_middleware.jwt_required') as mock:
        # 讓裝飾器直接返回原函式（跳過認證）
        mock.side_effect = lambda f: f
        yield mock

def test_vector_search_logic(mock_jwt_required):
    """測試 vector 搜尋邏輯（不測試認證）"""
    # 測試業務邏輯，不關心認證
    result = vector_search('test query')
    assert len(result) > 0
```

### 整合測試中的 JWT

**使用真實 JWT token** 測試完整認證流程：

```python
# tests/integration/routes/test_vectors_integration.py
from src.middleware.auth_middleware import create_admin_token, create_user_token

@pytest.fixture
def admin_headers():
    """建立管理員認證 headers"""
    token = create_admin_token()
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def user_headers():
    """建立一般使用者認證 headers"""
    token = create_user_token(user_id='test-user-123')
    return {'Authorization': f'Bearer {token}'}

def test_vector_search_requires_authentication(client):
    """測試 vector 搜尋需要認證"""
    response = client.post('/api/vectors/search', json={'query': 'test'})
    assert response.status_code == 401

def test_vector_search_with_admin_token(client, admin_headers):
    """測試管理員可以進行 vector 搜尋"""
    response = client.post('/api/vectors/search', 
                          json={'query': 'test'},
                          headers=admin_headers)
    assert response.status_code == 200

def test_vector_search_with_user_token(client, user_headers):
    """測試一般使用者可以進行 vector 搜尋"""
    response = client.post('/api/vectors/search', 
                          json={'query': 'test'},
                          headers=user_headers)
    assert response.status_code == 200

def test_admin_endpoint_requires_admin_role(client, user_headers):
    """測試管理員 endpoint 需要管理員權限"""
    response = client.post('/api/admin/users', 
                          json={'email': 'new@example.com'},
                          headers=user_headers)
    assert response.status_code == 403  # Forbidden
```

### JWT Token 過期測試

```python
import time
from datetime import datetime, timedelta

def test_expired_token_returns_401(client):
    """測試過期 token 返回 401"""
    # 建立已過期的 token（過期時間設為 1 秒前）
    token = create_token(
        user_id='test-user',
        expires_delta=timedelta(seconds=-1)
    )
    
    headers = {'Authorization': f'Bearer {token}'}
    response = client.post('/api/vectors/search', 
                          json={'query': 'test'},
                          headers=headers)
    
    assert response.status_code == 401
    assert 'expired' in response.json['error'].lower()
```

## Mock 和 Fixtures

### 使用 Mock

**何時使用 Mock**:
- 隔離外部依賴（資料庫、API、檔案系統）
- 測試錯誤處理
- 控制測試環境

**Mock 範例**:

```python
from unittest.mock import Mock, patch, MagicMock

# Mock 函式
@patch('src.services.monitoring.get_database_stats')
def test_collect_metrics_with_mock(mock_get_stats):
    mock_get_stats.return_value = {'connections': 10}
    
    dashboard = MonitoringDashboard()
    metrics = dashboard.collect_metrics()
    
    assert metrics.database_connections == 10
    mock_get_stats.assert_called_once()

# Mock 類別
@patch('src.services.monitoring.PersistentStateManager')
def test_collect_metrics_with_mock_class(MockStateManager):
    mock_instance = MockStateManager.return_value
    mock_instance.get_state.return_value = {'status': 'healthy'}
    
    dashboard = MonitoringDashboard()
    metrics = dashboard.collect_metrics()
    
    assert metrics.status == 'healthy'

# Mock 多個依賴
@patch('src.services.monitoring.resilience_manager')
@patch('src.services.monitoring.saga_orchestrator')
def test_collect_metrics_with_multiple_mocks(mock_saga, mock_resilience):
    mock_resilience.get_stats.return_value = {'success': 100}
    mock_saga.get_stats.return_value = {'pending': 5}
    
    dashboard = MonitoringDashboard()
    metrics = dashboard.collect_metrics()
    
    assert metrics.success_count == 100
    assert metrics.pending_sagas == 5
```

### 使用 Fixtures

**共用 Fixtures** 放在 `tests/fixtures/`:

```python
# tests/fixtures/auth.py
import pytest
from src.middleware.auth_middleware import create_admin_token, create_user_token

@pytest.fixture
def admin_token():
    """建立管理員 token"""
    return create_admin_token()

@pytest.fixture
def user_token():
    """建立一般使用者 token"""
    return create_user_token(user_id='test-user-123')

@pytest.fixture
def admin_headers(admin_token):
    """建立管理員認證 headers"""
    return {'Authorization': f'Bearer {admin_token}'}

@pytest.fixture
def user_headers(user_token):
    """建立一般使用者認證 headers"""
    return {'Authorization': f'Bearer {user_token}'}
```

```python
# tests/fixtures/database.py
import pytest
from src.database import db

@pytest.fixture
def db_session():
    """建立測試資料庫 session"""
    db.create_all()
    yield db.session
    db.session.remove()
    db.drop_all()

@pytest.fixture
def sample_user(db_session):
    """建立測試使用者"""
    user = User(email='test@example.com', name='Test User')
    db_session.add(user)
    db_session.commit()
    return user
```

**使用 Fixtures**:

```python
# tests/integration/routes/test_vectors_integration.py
from tests.fixtures.auth import admin_headers, user_headers
from tests.fixtures.database import db_session, sample_user

def test_vector_search_with_fixtures(client, admin_headers, db_session):
    """使用 fixtures 測試 vector 搜尋"""
    response = client.post('/api/vectors/search', 
                          json={'query': 'test'},
                          headers=admin_headers)
    assert response.status_code == 200
```

### Fixture Scope

控制 fixture 的生命週期：

```python
# Function scope (預設) - 每個測試函式執行一次
@pytest.fixture
def temp_data():
    return {'key': 'value'}

# Class scope - 每個測試類別執行一次
@pytest.fixture(scope='class')
def database_connection():
    conn = create_connection()
    yield conn
    conn.close()

# Module scope - 每個測試模組執行一次
@pytest.fixture(scope='module')
def app_config():
    return load_config()

# Session scope - 整個測試 session 執行一次
@pytest.fixture(scope='session')
def docker_services():
    start_docker_services()
    yield
    stop_docker_services()
```

## 測試覆蓋率

### 覆蓋率目標

| 測試類型 | 覆蓋率目標 | 執行頻率 |
|---------|-----------|---------|
| 單元測試 | 80%+ | 每次 commit |
| 整合測試 | 60%+ | 每次 PR |
| E2E 測試 | 關鍵路徑 100% | 每日/部署前 |

### 執行覆蓋率報告

```bash
# 執行所有測試並生成覆蓋率報告
pytest --cov=src --cov-report=term-missing --cov-report=html

# 只執行單元測試
pytest tests/unit/ --cov=src --cov-report=term-missing

# 只執行整合測試
pytest tests/integration/ --cov=src --cov-report=term-missing

# 設置覆蓋率門檻（低於門檻會失敗）
pytest --cov=src --cov-fail-under=60
```

### 查看覆蓋率報告

```bash
# 終端機報告
pytest --cov=src --cov-report=term-missing

# HTML 報告（在瀏覽器中查看）
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### 排除檔案

在 `.coveragerc` 或 `pyproject.toml` 中配置：

```ini
# .coveragerc
[run]
omit =
    */tests/*
    */migrations/*
    */venv/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

## CI/CD 整合

### GitHub Actions 配置

```yaml
# .github/workflows/backend.yml
name: Backend Tests

on:
  workflow_dispatch:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12.x'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run unit tests
        run: |
          pytest tests/unit/ \
            --cov=src \
            --cov-report=term-missing \
            --cov-fail-under=80 \
            --maxfail=1 \
            -v
  
  integration-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:alpine
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12.x'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run integration tests
        env:
          REDIS_URL: redis://localhost:6379/0
          JWT_SECRET: test-secret-do-not-use-in-production
        run: |
          pytest tests/integration/ \
            --cov=src \
            --cov-report=term-missing \
            --cov-fail-under=60 \
            -v
      
      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

### 本地測試腳本

```bash
#!/bin/bash
# scripts/run_tests.sh

set -e

echo "🧪 Running unit tests..."
pytest tests/unit/ \
  --cov=src \
  --cov-report=term-missing \
  --cov-fail-under=80 \
  -v

echo "🔗 Running integration tests..."
pytest tests/integration/ \
  --cov=src \
  --cov-report=term-missing \
  --cov-fail-under=60 \
  -v

echo "✅ All tests passed!"
```

## 常見問題

### Q1: 單元測試 vs 整合測試，如何選擇？

**A**: 使用決策樹：

```
是否需要測試多個模組的協作？
├─ 是 → 整合測試
└─ 否 → 是否需要測試外部依賴（資料庫、API）？
    ├─ 是 → 整合測試
    └─ 否 → 單元測試
```

### Q2: 如何測試非同步函式？

**A**: 使用 `pytest-asyncio`:

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected_value
```

### Q3: 如何測試私有方法？

**A**: 不要直接測試私有方法，測試公開 API：

```python
# ❌ 不好的做法
def test_private_method():
    obj = MyClass()
    result = obj._private_method()  # 測試私有方法
    assert result == expected

# ✅ 好的做法
def test_public_method_that_uses_private():
    obj = MyClass()
    result = obj.public_method()  # 測試公開方法
    assert result == expected  # 間接測試私有方法
```

### Q4: 測試執行太慢怎麼辦？

**A**: 優化策略：

1. **並行執行測試**:
   ```bash
   pytest -n auto  # 使用 pytest-xdist
   ```

2. **只執行失敗的測試**:
   ```bash
   pytest --lf  # last failed
   pytest --ff  # failed first
   ```

3. **使用 markers 分組測試**:
   ```python
   @pytest.mark.slow
   def test_slow_operation():
       pass
   
   # 跳過慢速測試
   pytest -m "not slow"
   ```

### Q5: 如何處理測試資料？

**A**: 使用 fixtures 和 factories:

```python
# tests/fixtures/mock_data.py
import pytest

@pytest.fixture
def sample_vector_data():
    return {
        'id': 'vec-123',
        'content': 'test content',
        'embedding': [0.1, 0.2, 0.3]
    }

@pytest.fixture
def sample_user_data():
    return {
        'email': 'test@example.com',
        'name': 'Test User',
        'role': 'user'
    }
```

### Q6: 如何測試錯誤處理？

**A**: 使用 `pytest.raises`:

```python
def test_function_raises_error():
    with pytest.raises(ValueError) as exc_info:
        function_that_raises_error()
    
    assert "expected error message" in str(exc_info.value)
```

### Q7: 如何 mock 環境變數？

**A**: 使用 `monkeypatch`:

```python
def test_with_env_var(monkeypatch):
    monkeypatch.setenv('API_KEY', 'test-key')
    
    result = function_that_uses_env_var()
    assert result == expected
```

## 相關資源

### 內部文檔

- [Testing Architecture](./TESTING_ARCHITECTURE.md) - 雙層測試架構和 CI 配置
- [VSCode IDE Test Strategy](./VSCODE_IDE_TEST_STRATEGY.md) - IDE 服務的測試架構和 mock 策略

### 外部文檔

- [pytest 官方文檔](https://docs.pytest.org/)
- [unittest.mock 文檔](https://docs.python.org/3/library/unittest.mock.html)
- [pytest-cov 文檔](https://pytest-cov.readthedocs.io/)
- [Flask Testing 文檔](https://flask.palletsprojects.com/en/latest/testing/)

## 貢獻

如有測試相關問題或建議，請：
1. 查看 [CONTRIBUTING.md](../CONTRIBUTING.md)
2. 建立 Issue 討論
3. 提交 PR 改進文檔

---

**最後更新**: 2025-10-23  
**維護者**: MorningAI Engineering Team
