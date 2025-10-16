# Dev Agent - Devin-Level Development Agent

## 概述

Dev Agent 是 Morning AI 生態系統中的開發代理，具備類似 Devin AI 的通用軟體工程能力。它在安全的沙箱環境中運行，配備完整的 IDE、Shell、LSP 伺服器和開發工具。

## 核心功能

### 1. 沙箱環境
- Docker 容器隔離
- 資源限制（CPU、記憶體、磁碟）
- 安全配置（seccomp、AppArmor）
- 網路隔離選項

### 2. 開發工具
- **VSCode Server**: Web-based IDE 介面
- **Language Server Protocol (LSP)**: 
  - Python LSP (pylsp)
  - TypeScript/JavaScript LSP
  - YAML、Dockerfile 支援
- **Git 工具**: 完整的版本控制操作
- **檔案系統工具**: 檔案讀寫、搜尋、管理

### 3. 整合能力
- MCP (Model Context Protocol) 整合
- GitHub API 整合（PR 創建）
- Playwright 瀏覽器自動化
- Shell 命令執行

## 架構設計

```
agents/dev_agent/
├── sandbox/
│   ├── Dockerfile              # Dev Agent 容器定義
│   ├── requirements.txt        # Python 依賴
│   ├── docker-compose.yml      # 容器編排配置
│   ├── dev_agent_sandbox.py    # 沙箱核心邏輯
│   ├── mcp_client.py          # MCP 伺服器
│   ├── seccomp-profile.json   # Seccomp 安全配置
│   └── apparmor-profile       # AppArmor 安全配置
├── tools/
│   ├── git_tool.py            # Git 操作工具
│   ├── ide_tool.py            # IDE 功能工具
│   └── filesystem_tool.py     # 檔案系統工具
└── tests/
    └── test_e2e.py            # E2E 測試
```

## 快速開始

### 1. 構建沙箱容器

```bash
cd agents/dev_agent/sandbox
docker-compose build
```

### 2. 啟動沙箱

```bash
docker-compose up -d
```

### 3. 驗證健康狀態

```bash
curl http://localhost:8080/health
```

### 4. 運行測試

```bash
cd agents/dev_agent
pytest tests/test_e2e.py -v
```

## API 端點

### 健康檢查
```
GET /health
```

### Shell 執行
```
POST /api/shell
Body: {"command": "ls -la"}
```

### Git 操作
```
POST /api/git/clone
Body: {"repo_url": "https://github.com/...", "destination": "/workspace/repo"}

POST /api/git/commit
Body: {"message": "commit message", "files": ["file1.py"]}
```

### 檔案操作
```
POST /api/file/read
Body: {"file_path": "README.md"}

POST /api/file/write
Body: {"file_path": "test.py", "content": "print('hello')"}
```

### LSP 伺服器
```
POST /api/lsp/start
Body: {"language": "python"}
```

## 使用範例

### 在 Python 中使用 Dev Agent 工具

```python
from agents.dev_agent.tools import get_git_tool, get_ide_tool, get_filesystem_tool

# 初始化工具
sandbox_endpoint = "http://localhost:8080"
git_tool = get_git_tool(sandbox_endpoint)
ide_tool = get_ide_tool(sandbox_endpoint)
fs_tool = get_filesystem_tool(sandbox_endpoint)

# 克隆倉庫
await git_tool.clone("https://github.com/example/repo.git")

# 讀取檔案
result = await fs_tool.read_file("README.md")
print(result['content'])

# 編輯檔案
await ide_tool.edit_file("src/main.py", "def main():\n    print('Hello')")

# 提交變更
await git_tool.commit("Update main.py")
```

## 安全性

Dev Agent 實施多層安全措施：

1. **容器隔離**: 使用 Docker 容器隔離執行環境
2. **資源限制**: CPU、記憶體、磁碟空間限制
3. **權限控制**: 以非 root 使用者運行
4. **Seccomp Profile**: 限制系統呼叫
5. **AppArmor**: 強制訪問控制
6. **唯讀檔案系統**: 除 /workspace 和 /tmp 外都是唯讀
7. **網路隔離**: 可選的網路隔離模式

## 資源配置

預設資源限制：
- CPU: 1.0 核心
- 記憶體: 2048 MB
- 磁碟: 10 GB
- 進程數: 100
- 閒置超時: 30 分鐘
- 最大運行時間: 2 小時

可在 `docker-compose.yml` 中調整。

## OODA Loop 整合 (Phase 1 Week 3-4)

Dev Agent 包含增強的 OODA（Observe, Orient, Decide, Act）循環，支援會話持久化和決策追蹤：

### 使用方法

**基本使用（Week 3）**:
```python
import asyncio
from agents.dev_agent.dev_agent_ooda import create_dev_agent_ooda

async def execute_dev_task():
    ooda = create_dev_agent_ooda('http://localhost:8080')
    
    result = await ooda.execute_task(
        "修復身份驗證模組中的錯誤",
        priority="high",
        max_iterations=3
    )
    
    print(f"任務完成: {result['result']}")
    print(f"決策追蹤: {len(result['decision_trace'])} 條記錄")

asyncio.run(execute_dev_task())
```

**會話持久化（Week 4）**:
```python
# 啟用 Redis 會話持久化 (important-comment)
ooda = create_dev_agent_ooda(
    'http://localhost:8080',
    enable_persistence=True
)

result = await ooda.execute_task("任務描述", priority="high")

# 獲取會話歷史 (important-comment)
if result.get('session_id'):
    session = ooda.session_manager.get_session(result['session_id'])
    context_window = ooda.session_manager.get_context_window(result['session_id'])
    decision_trace = ooda.session_manager.get_decision_trace(result['session_id'])
```

### OODA 階段

1. **Observe（觀察）**: 探索代碼庫，收集相關上下文
2. **Orient（定位）**: 分析任務，評估複雜度，生成策略
3. **Decide（決策）**: 選擇最佳策略，創建行動計劃
4. **Act（行動）**: 使用 Git、IDE 和 FileSystem 工具執行操作

### Week 4 新功能

1. **決策追蹤（Decision Trace）**: 記錄每個 OODA 階段的決策過程
2. **會話持久化**: 使用 Redis 緩存會話狀態，支援跨重啟恢復
3. **上下文窗口**: 滑動窗口保留最近 50 個操作
4. **路徑白名單**: 文件操作安全驗證（限制 /workspace 和 /tmp）
5. **統一錯誤處理**: 標準化錯誤碼、訊息和提示
6. **最大步數限制**: 防止無限循環（最多 100 步）

### 安全功能

**路徑白名單驗證**:
```python
from agents.dev_agent.tools.filesystem_tool import FileSystemTool

fs_tool = FileSystemTool('http://localhost:8080')

# ✓ 允許的路徑 (important-comment)
result = await fs_tool.read_file('/workspace/src/main.py')

# ✗ 禁止的路徑 (important-comment)
result = await fs_tool.read_file('/etc/passwd')  # 返回 PATH_NOT_WHITELISTED 錯誤
```

### 錯誤處理

所有錯誤採用統一格式：
```python
{
    'success': False,
    'error': {
        'error_code': 'DEV_003',
        'error_name': 'PATH_NOT_WHITELISTED',
        'message': '路徑不在白名單中',
        'hint': '使用 /workspace 目錄',
        'context': {'path': '/forbidden/path'}
    }
}
```

### 範例

查看 `agents/dev_agent/examples/ooda_example.py` 以獲取完整範例。

### 測試

運行 E2E 測試：

```bash
# 現有沙箱測試 (important-comment)
pytest agents/dev_agent/tests/test_e2e.py -v

# OODA 循環測試（Week 3-4）(important-comment)
pytest agents/dev_agent/tests/test_ooda_e2e.py -v
```

### 配置

**環境變數**:
- `DEV_AGENT_ENDPOINT`: 沙箱端點 URL（預設：http://localhost:8080）
- `GITHUB_TOKEN`: GitHub API token（用於 PR 操作）
- `UPSTASH_REDIS_REST_URL`: Upstash Redis REST API URL（可選，用於持久化）
- `UPSTASH_REDIS_REST_TOKEN`: Upstash Redis REST API Token（可選，用於持久化）

**OODA 參數**:
- `max_iterations`: 最大 OODA 循環次數（預設：3）
- `enable_persistence`: 啟用 Redis 持久化（預設：False）
- `MAX_STEPS`: 最大工作流程步數限制（100 步，防止無限循環）

## 後續開發

根據 Phase 1 實作計畫，接下來將：

1. **Week 3**: 整合 Meta-Agent OODA 循環
2. **Week 4**: 實現 Session State 管理
3. 後續階段: 擴展到更多語言和工具

## 相關文檔

- [Devin-Level Agents Roadmap](../../docs/devin-level-agents-roadmap.md)
- [MCP Protocol Documentation](../../handoff/20250928/40_App/orchestrator/mcp/README.md)

## 授權

本專案遵循 Morning AI 專案授權條款。
