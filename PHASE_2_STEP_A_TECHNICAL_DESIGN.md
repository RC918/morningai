# Phase 2 Step A：基礎架構技術設計文檔

**版本**: 1.0  
**日期**: 2025-11-27  
**作者**: Devin AI  
**狀態**: Draft → Review → Approved

---

## 一、概述

### 1.1 目標

Phase 2 Step A 的目標是為後續的代碼生成整合（Phase 2 Step B/C）和多代理協調（Phase 3）打下基礎架構，具體包括：

1. **ProjectEngineerAgent**：提供對人類友好的任務執行入口
2. **Safe Tasks 白名單**：定義哪些任務類型允許自動代碼生成
3. **PR Review CLI**：將 ReviewerAgent 包裝成可重複使用的命令行工具
4. **LLM Provider 抽象**：統一 LLM 調用接口，為未來的 Gemini 整合做準備

### 1.2 設計原則

- **不改變現有行為**：所有新增組件都是包裝和抽象，不影響現有功能
- **漸進式啟用**：新功能通過 feature flags 控制，預設關閉
- **向後兼容**：保持與現有 LLMPlannerAdapter、TaskClassifier、ReviewerAgent 的兼容性
- **安全第一**：Safe Tasks 白名單採用保守策略，初期只允許低風險任務

### 1.3 範圍

**包含**：
- ProjectEngineerAgent 骨架實現
- Safe Tasks 白名單定義
- PR Review CLI 工具
- LLM Provider 抽象層（OpenAI 實現）

**不包含**（留待後續）：
- Gemini Provider 實現（Phase 2 Extra）
- CodeGenerationWorkflow 啟用（Phase 2 Step B）
- 多代理協調邏輯（Phase 3）

---

## 二、架構設計

### 2.1 系統架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                        User / External System                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │   ProjectEngineerAgent        │  ◄── 新增（Phase 2 Step A）
         │   - run_task(description)     │
         │   - 任務規劃與分解            │
         └───────────┬───────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌────────────────┐      ┌────────────────┐
│ LLMPlanner     │      │ TaskClassifier │  ◄── 現有組件（重用）
│ Adapter        │      │                │
└────────┬───────┘      └────────┬───────┘
         │                       │
         │                       ▼
         │              ┌────────────────┐
         │              │ Safe Tasks     │  ◄── 新增（Phase 2 Step A）
         │              │ Whitelist      │
         │              └────────────────┘
         │
         ▼
┌────────────────────────────────┐
│      LLMClient (抽象層)        │  ◄── 新增（Phase 2 Step A）
│  - generate(prompt, **kwargs)  │
│  - Provider: openai / gemini   │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│      OpenAI API                │  ◄── 現有（預設 Provider）
│      (GPT-4)                   │
└────────────────────────────────┘


┌─────────────────────────────────────────────────────────────┐
│                    PR Review 流程                            │
└─────────────────────────────────────────────────────────────┘

User / CI Pipeline
         │
         ▼
┌────────────────────────────────┐
│  run_pr_review.py (CLI)        │  ◄── 新增（Phase 2 Step A）
│  --pr 1234 --files a.py b.py   │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│    ReviewerAgent               │  ◄── 現有組件（重用）
│    - review_files()            │
│    - Lint / Security / A11y    │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  Structured Review Result      │
│  - passed: bool                │
│  - comments: List[Comment]     │
│  - summary: Dict[str, int]     │
└────────────────────────────────┘
```

### 2.2 組件關係圖

```
ProjectEngineerAgent
    ├─ 依賴 LLMPlannerAdapter (現有)
    ├─ 依賴 TaskClassifier (現有)
    ├─ 依賴 SafeTasks (新增)
    └─ 依賴 Orchestrator (現有)

LLMClient (新增)
    ├─ 被 LLMPlannerAdapter 使用
    ├─ 被 FAQGenerator 使用
    └─ 未來被 CodeGenerationWorkflow 使用

run_pr_review.py (新增)
    └─ 依賴 ReviewerAgent (現有)

SafeTasks (新增)
    └─ 被 ProjectEngineerAgent 使用
    └─ 未來被 CodeGenerationWorkflow 使用
```

---

## 三、API 設計

### 3.1 ProjectEngineerAgent API

#### 類定義

```python
class ProjectEngineerAgent:
    """
    Devin-like Meta-Agent that accepts natural language commands
    and orchestrates task execution.
    
    Features:
    - Task decomposition using LLM Planner
    - Safe task classification
    - Structured result reporting
    """
    
    def __init__(self):
        """Initialize ProjectEngineerAgent with dependencies"""
        
    def run_task(self, description: str) -> List[TaskResult]:
        """
        Execute a task based on natural language description
        
        Args:
            description: Natural language task description
            
        Returns:
            List of TaskResult objects with execution details
            
        Raises:
            ValueError: If description is empty or invalid
        """
```

#### TaskResult 數據結構

```python
@dataclass
class TaskResult:
    """Result of a single task execution"""
    task_id: str
    task_type: str
    status: str  # "success", "failed", "skipped"
    is_safe: bool
    details: str
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    error: Optional[str] = None
```

#### 使用範例

```python
# 範例 1：分析任務（不執行代碼生成）
agent = ProjectEngineerAgent()
results = agent.run_task("分析 user_service.py 的性能瓶頸")

for result in results:
    print(f"Task: {result.task_type}")
    print(f"Status: {result.status}")
    print(f"Details: {result.details}")

# 範例 2：安全任務（可能執行代碼生成）
results = agent.run_task("更新 README.md 添加安裝說明")

# 範例 3：非安全任務（只分析不執行）
results = agent.run_task("重構 payment_service.py 的錯誤處理")
```

---

### 3.2 Safe Tasks API

#### 模組定義

```python
# safe_tasks.py

SAFE_TASK_TYPES = {
    "documentation_update",
    "test_generation",
    "update_readme",
    "fix_lint",
    "fix_typo",
    "comment_enhancement",
    "env_sync",
    "i18n_update",
    "config_update",
}

def is_safe_task(task_type: str) -> bool:
    """
    Check if a task type is safe for automatic code generation
    
    Args:
        task_type: Task type from TaskClassifier
        
    Returns:
        True if task is in safe whitelist, False otherwise
    """
    
def get_safe_task_metadata(task_type: str) -> Dict[str, Any]:
    """
    Get metadata for a safe task type
    
    Args:
        task_type: Task type from TaskClassifier
        
    Returns:
        Dict with risk_level, max_files, requires_review, etc.
    """
```

#### 使用範例

```python
from project_engineer.safe_tasks import is_safe_task, SAFE_TASK_TYPES

# 檢查任務是否安全
if is_safe_task("documentation_update"):
    # 允許自動代碼生成
    execute_codegen()
else:
    # 只分析不執行
    analyze_only()

# 獲取所有安全任務類型
print(f"Safe tasks: {SAFE_TASK_TYPES}")
```

---

### 3.3 PR Review CLI API

#### 命令行接口

```bash
# 基本用法
python tools/code_agents/run_pr_review.py --pr 1234

# 指定檔案
python tools/code_agents/run_pr_review.py --pr 1234 --files src/app.py src/utils.py

# 輸出格式
python tools/code_agents/run_pr_review.py --pr 1234 --format json

# 設定嚴格度
python tools/code_agents/run_pr_review.py --pr 1234 --strict
```

#### 輸出格式

```json
{
  "pr_number": 1234,
  "passed": false,
  "summary": {
    "total": 15,
    "error": 3,
    "warning": 8,
    "info": 4,
    "lint": 5,
    "security": 2,
    "accessibility": 3,
    "style": 5
  },
  "comments": [
    {
      "file_path": "src/app.py",
      "line_number": 42,
      "severity": "error",
      "category": "security",
      "message": "Avoid using eval() - security risk",
      "suggestion": "Use safer alternatives like json.loads()",
      "code_snippet": "result = eval(user_input)"
    }
  ]
}
```

---

### 3.4 LLMClient API

#### 類定義

```python
class LLMClient:
    """
    Unified LLM client supporting multiple providers
    
    Providers:
    - openai: OpenAI GPT-4 (default)
    - gemini: Google Gemini (future)
    - auto: Automatic provider selection
    """
    
    def __init__(self, provider: str = "openai"):
        """
        Initialize LLM client with specified provider
        
        Args:
            provider: LLM provider name ("openai", "gemini", "auto")
            
        Raises:
            ValueError: If provider is not supported
        """
        
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """
        Generate text using LLM
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters
            
        Returns:
            Generated text
            
        Raises:
            LLMError: If generation fails
        """
```

#### 使用範例

```python
# 範例 1：使用預設 Provider (OpenAI)
client = LLMClient()
response = client.generate("解釋什麼是依賴注入")

# 範例 2：指定 Provider
client = LLMClient(provider="openai")
response = client.generate(
    prompt="生成單元測試",
    system_prompt="你是一個測試工程師",
    temperature=0.3
)

# 範例 3：未來支援 Gemini
client = LLMClient(provider="gemini")
response = client.generate("審查這段代碼")
```

---

## 四、資料流圖

### 4.1 ProjectEngineerAgent 執行流程

```
User Input: "更新 README.md 添加安裝說明"
         │
         ▼
┌────────────────────────────────┐
│ ProjectEngineerAgent           │
│ .run_task(description)         │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Step 1: LLM Planner            │
│ - 拆解任務為多個步驟           │
│ - 生成執行計劃                 │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Step 2: Task Classification    │
│ - 使用 TaskClassifier          │
│ - 判斷任務類型                 │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Step 3: Safe Task Check        │
│ - 檢查 is_safe_task()          │
│ - 決定是否允許 codegen         │
└────────┬───────────────────────┘
         │
         ├─ is_safe = True ──────────┐
         │                           │
         │                           ▼
         │                  ┌────────────────────┐
         │                  │ Execute with       │
         │                  │ CodeGen (Phase 2B) │
         │                  └────────────────────┘
         │
         └─ is_safe = False ─────────┐
                                     │
                                     ▼
                            ┌────────────────────┐
                            │ Analyze Only       │
                            │ (不執行 codegen)   │
                            └────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Step 4: Return Results         │
│ - List[TaskResult]             │
│ - 包含狀態、詳情、PR 連結      │
└────────────────────────────────┘
```

### 4.2 PR Review CLI 執行流程

```
CLI Command: python run_pr_review.py --pr 1234
         │
         ▼
┌────────────────────────────────┐
│ Step 1: Parse Arguments        │
│ - pr_number: 1234              │
│ - files: Optional[List[str]]   │
│ - format: text / json          │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Step 2: Fetch PR Files         │
│ - 從 GitHub API 獲取檔案列表   │
│ - 或使用 --files 指定          │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Step 3: ReviewerAgent          │
│ - review_files(file_paths)     │
│ - Lint / Security / A11y       │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Step 4: Format Output          │
│ - Text: format_review_comments │
│ - JSON: structured dict        │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Step 5: Exit Code              │
│ - 0: Review passed             │
│ - 1: Review failed             │
└────────────────────────────────┘
```

### 4.3 LLMClient 調用流程

```
Caller: LLMPlannerAdapter / FAQGenerator / etc.
         │
         ▼
┌────────────────────────────────┐
│ LLMClient.generate()           │
│ - prompt: str                  │
│ - provider: "openai"           │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Provider Router                │
│ - if provider == "openai"      │
│   → _call_openai()             │
│ - elif provider == "gemini"    │
│   → _call_gemini() (future)    │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ OpenAI API Call                │
│ - model: gpt-4-turbo-preview   │
│ - messages: [...]              │
│ - temperature: 0.7             │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Response Processing            │
│ - Extract text                 │
│ - Handle errors                │
│ - Return string                │
└────────────────────────────────┘
```

---

## 五、測試計劃

### 5.1 單元測試

#### ProjectEngineerAgent 測試

```python
# test_project_engineer_agent.py

def test_init():
    """測試 ProjectEngineerAgent 初始化"""
    agent = ProjectEngineerAgent()
    assert agent.planner is not None
    assert agent.classifier is not None

def test_run_task_with_safe_task():
    """測試執行安全任務"""
    agent = ProjectEngineerAgent()
    results = agent.run_task("更新 README.md")
    
    assert len(results) > 0
    assert results[0].is_safe == True
    assert results[0].task_type == "documentation_update"

def test_run_task_with_unsafe_task():
    """測試執行非安全任務（只分析）"""
    agent = ProjectEngineerAgent()
    results = agent.run_task("重構 payment_service.py")
    
    assert len(results) > 0
    assert results[0].is_safe == False
    assert results[0].status == "skipped"

def test_run_task_empty_description():
    """測試空描述"""
    agent = ProjectEngineerAgent()
    with pytest.raises(ValueError):
        agent.run_task("")
```

#### Safe Tasks 測試

```python
# test_safe_tasks.py

def test_is_safe_task_documentation():
    """測試文檔更新是安全任務"""
    assert is_safe_task("documentation_update") == True

def test_is_safe_task_refactor():
    """測試重構不是安全任務"""
    assert is_safe_task("refactor") == False

def test_safe_task_types_immutable():
    """測試 SAFE_TASK_TYPES 不可變"""
    original_size = len(SAFE_TASK_TYPES)
    # 嘗試修改應該失敗或不影響原集合
    SAFE_TASK_TYPES.add("dangerous_task")
    assert len(SAFE_TASK_TYPES) == original_size

def test_get_safe_task_metadata():
    """測試獲取安全任務元數據"""
    metadata = get_safe_task_metadata("documentation_update")
    assert metadata["risk_level"] == "low"
    assert metadata["requires_review"] == False
```

#### PR Review CLI 測試

```python
# test_run_pr_review.py

def test_cli_basic_usage(tmp_path):
    """測試基本 CLI 使用"""
    # 創建測試檔案
    test_file = tmp_path / "test.py"
    test_file.write_text("print('hello')")
    
    # 執行 CLI
    result = subprocess.run(
        ["python", "tools/code_agents/run_pr_review.py", "--files", str(test_file)],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "REVIEW RESULTS" in result.stdout

def test_cli_json_output(tmp_path):
    """測試 JSON 輸出格式"""
    test_file = tmp_path / "test.py"
    test_file.write_text("eval('1+1')")  # 安全問題
    
    result = subprocess.run(
        ["python", "tools/code_agents/run_pr_review.py", 
         "--files", str(test_file), "--format", "json"],
        capture_output=True,
        text=True
    )
    
    output = json.loads(result.stdout)
    assert output["passed"] == False
    assert output["summary"]["security"] > 0
```

#### LLMClient 測試

```python
# test_llm_client.py

def test_llm_client_init_openai():
    """測試 OpenAI Provider 初始化"""
    client = LLMClient(provider="openai")
    assert client.provider == "openai"

def test_llm_client_generate():
    """測試生成文本"""
    client = LLMClient()
    response = client.generate("Say hello")
    assert isinstance(response, str)
    assert len(response) > 0

def test_llm_client_invalid_provider():
    """測試無效 Provider"""
    with pytest.raises(ValueError):
        LLMClient(provider="invalid")

@pytest.mark.skip(reason="Gemini not implemented yet")
def test_llm_client_gemini():
    """測試 Gemini Provider（未來）"""
    client = LLMClient(provider="gemini")
    response = client.generate("Say hello")
    assert isinstance(response, str)
```

---

### 5.2 整合測試

#### End-to-End 測試

```python
# test_phase2_step_a_integration.py

def test_project_engineer_agent_e2e():
    """測試 ProjectEngineerAgent 端到端流程"""
    agent = ProjectEngineerAgent()
    
    # 執行安全任務
    results = agent.run_task("更新 README.md 添加安裝說明")
    
    # 驗證結果
    assert len(results) > 0
    assert results[0].status in ["success", "skipped"]
    assert results[0].is_safe == True

def test_pr_review_cli_e2e(tmp_path):
    """測試 PR Review CLI 端到端流程"""
    # 創建測試檔案
    test_file = tmp_path / "app.py"
    test_file.write_text("""
def process_data(data):
    result = eval(data)  # Security issue
    return result
""")
    
    # 執行 CLI
    result = subprocess.run(
        ["python", "tools/code_agents/run_pr_review.py", "--files", str(test_file)],
        capture_output=True,
        text=True
    )
    
    # 驗證輸出
    assert result.returncode == 1  # Failed due to security issue
    assert "security" in result.stdout.lower()
    assert "eval" in result.stdout.lower()

def test_llm_client_integration():
    """測試 LLMClient 與現有組件整合"""
    # 測試與 LLMPlannerAdapter 整合
    from llm_planner_adapter import LLMPlannerAdapter
    
    adapter = LLMPlannerAdapter()
    plan = adapter.generate_plan(
        goal="更新文檔",
        repo="test/repo",
        trace_id="test-123"
    )
    
    assert plan["planner_type"] in ["llm", "static"]
    assert len(plan["plan"]) >= 3
```

---

### 5.3 測試覆蓋率目標

| 組件 | 目標覆蓋率 | 優先級 |
|------|-----------|--------|
| ProjectEngineerAgent | ≥ 80% | P0 |
| Safe Tasks | ≥ 90% | P0 |
| PR Review CLI | ≥ 70% | P1 |
| LLMClient | ≥ 85% | P0 |

---

### 5.4 測試執行計劃

#### Phase 1：單元測試（Day 4 上午）
```bash
# 執行所有單元測試
pytest handoff/20250928/40_App/orchestrator/project_engineer/tests/ -v

# 執行覆蓋率報告
pytest --cov=project_engineer --cov-report=html
```

#### Phase 2：整合測試（Day 4 下午）
```bash
# 執行整合測試
pytest handoff/20250928/40_App/orchestrator/tests/test_phase2_step_a_integration.py -v

# 執行 CLI 測試
pytest tools/code_agents/tests/ -v
```

#### Phase 3：Staging 驗證（Day 4 晚上）
- 在 Staging 環境手動測試 ProjectEngineerAgent
- 驗證 Safe Tasks 白名單正確運作
- 測試 PR Review CLI 與 GitHub 整合

---

## 六、部署計劃

### 6.1 環境配置

#### 新增環境變數

```yaml
# config/env.schema.yaml

LLM_PROVIDER:
  type: string
  default: "openai"
  enum: ["openai", "gemini", "auto"]
  description: "LLM provider for code generation"

ENABLE_PROJECT_ENGINEER_AGENT:
  type: boolean
  default: false
  description: "Enable ProjectEngineerAgent (Phase 2 Step A)"

SAFE_TASKS_MODE:
  type: string
  default: "strict"
  enum: ["strict", "permissive"]
  description: "Safe tasks whitelist mode"
```

#### 配置範例

```bash
# .env.staging
LLM_PROVIDER=openai
ENABLE_PROJECT_ENGINEER_AGENT=false  # 預設關閉
SAFE_TASKS_MODE=strict
```

---

### 6.2 部署步驟

#### Step 1：代碼部署（Day 4 上午）
```bash
# 1. 創建 PR
git checkout -b phase-2-step-a-infrastructure
git add handoff/20250928/40_App/orchestrator/project_engineer/
git add tools/code_agents/
git commit -m "feat: Add Phase 2 Step A infrastructure"
git push origin phase-2-step-a-infrastructure

# 2. 等待 CI 通過
# 3. Code Review
# 4. 合併到 main
```

#### Step 2：Staging 部署（Day 4 下午）
```bash
# 1. 部署到 Staging
kubectl set image deployment/morningai-backend-v2-stg-worker \
  worker=gcr.io/morningai/backend:phase-2-step-a

# 2. 驗證部署
kubectl rollout status deployment/morningai-backend-v2-stg-worker

# 3. 檢查日誌
kubectl logs -f deployment/morningai-backend-v2-stg-worker
```

#### Step 3：功能驗證（Day 4 晚上）
```bash
# 1. 測試 ProjectEngineerAgent（手動）
python -c "
from project_engineer.agent import ProjectEngineerAgent
agent = ProjectEngineerAgent()
results = agent.run_task('分析 README.md')
print(results)
"

# 2. 測試 PR Review CLI
python tools/code_agents/run_pr_review.py --pr 1234

# 3. 測試 LLMClient
python -c "
from llm.llm_client import LLMClient
client = LLMClient()
response = client.generate('Say hello')
print(response)
"
```

---

### 6.3 回滾計劃

如果部署後發現問題：

```bash
# 1. 立即回滾到上一個版本
kubectl rollout undo deployment/morningai-backend-v2-stg-worker

# 2. 驗證回滾成功
kubectl rollout status deployment/morningai-backend-v2-stg-worker

# 3. 檢查日誌確認問題
kubectl logs deployment/morningai-backend-v2-stg-worker --previous
```

---

## 七、監控與指標

### 7.1 關鍵指標

| 指標名稱 | 描述 | 目標值 | 監控方式 |
|---------|------|--------|---------|
| `project_engineer_agent_calls` | ProjectEngineerAgent 調用次數 | - | Counter |
| `safe_task_check_rate` | Safe task 檢查通過率 | ≥ 95% | Gauge |
| `pr_review_cli_success_rate` | PR Review CLI 成功率 | ≥ 90% | Gauge |
| `llm_client_latency_ms` | LLM Client 延遲 | P95 < 3000ms | Histogram |
| `llm_client_error_rate` | LLM Client 錯誤率 | < 5% | Gauge |

### 7.2 日誌記錄

```python
# 範例日誌格式
logger.info(
    "[ProjectEngineerAgent] Task executed",
    extra={
        "operation": "project_engineer_agent",
        "task_type": "documentation_update",
        "is_safe": True,
        "status": "success",
        "execution_time_ms": 1234
    }
)
```

---

## 八、風險與緩解

### 8.1 技術風險

| 風險 | 影響 | 可能性 | 緩解措施 |
|------|------|--------|---------|
| LLMClient 抽象層性能開銷 | 中 | 低 | 保持薄層設計，避免過度抽象 |
| Safe Tasks 白名單過於保守 | 低 | 中 | 漸進式擴展白名單，收集實際使用數據 |
| ProjectEngineerAgent 與現有組件衝突 | 高 | 低 | 充分測試，使用 feature flag 控制 |
| PR Review CLI 與 GitHub API 限制 | 中 | 中 | 實現 rate limiting 和 retry 邏輯 |

### 8.2 操作風險

| 風險 | 影響 | 可能性 | 緩解措施 |
|------|------|--------|---------|
| 部署後發現 bug | 高 | 中 | 完整的測試覆蓋，Staging 驗證，快速回滾計劃 |
| 配置錯誤導致功能異常 | 中 | 低 | 配置驗證，預設值保守，文檔清晰 |
| 團隊不熟悉新 API | 低 | 高 | 提供詳細文檔和使用範例 |

---

## 九、後續步驟

### 9.1 Phase 2 Step B 準備

完成 Phase 2 Step A 後，需要為 Phase 2 Step B 做準備：

1. **Salvage CodeGenerationWorkflow**
   - 重用 TaskClassifier / ReviewerAgent / Generation Primitives
   - 整合 Safe Tasks 白名單
   - 添加 Sub-canary 邏輯

2. **Executor Node 整合**
   - 實現 `execute_with_codegen()`
   - 使用 ProjectEngineerAgent 作為入口
   - 添加 CodeGen 事件監控

### 9.2 Phase 3 準備

為多代理協調做準備：

1. **Code-Audit Pipeline**
   - 使用 PR Review CLI 作為第一個 agent
   - 添加 Repo Audit / DevOps / UX/i18n / Memory agents
   - 實現代理間通訊協議

2. **ProjectEngineerAgent 增強**
   - 添加多代理協調邏輯
   - 實現任務分配和結果聚合
   - 添加失敗重試機制

---

## 十、附錄

### 10.1 參考文檔

- [Phase 1 Canary 完成報告](./PHASE_1_COMPLETE_VALIDATION_REPORT.md)
- [原始路線圖](./Nov+27+2025+09-50-18+PM+Markdown+Content.md)
- [TaskClassifier 實現](./agents/dev_agent/workflows/task_classifier.py)
- [ReviewerAgent 實現](./agents/reviewer_agent/reviewer_agent.py)
- [LLMPlannerAdapter 實現](./handoff/20250928/40_App/orchestrator/llm_planner_adapter.py)

### 10.2 詞彙表

| 術語 | 定義 |
|------|------|
| ProjectEngineerAgent | Devin-like Meta-Agent，接受自然語言指令並協調任務執行 |
| Safe Tasks | 允許自動代碼生成的低風險任務類型白名單 |
| Sub-Canary | 在金絲雀部署內部的更小規模測試（如 1% 流量） |
| Code-Audit Pipeline | 5 個專門的審查 agents 組成的驗證流程 |
| LLM Provider | 提供 LLM 服務的後端（OpenAI, Gemini 等） |

### 10.3 變更歷史

| 版本 | 日期 | 作者 | 變更內容 |
|------|------|------|---------|
| 1.0 | 2025-11-27 | Devin AI | 初始版本 |

---

**審查者簽名**：_________________  
**批准日期**：_________________
