# Dev Agent 整合指南

## 與 Orchestrator 整合

Dev Agent 設計為可與現有的 Orchestrator 系統無縫整合。

### 1. 沙箱管理器整合

Dev Agent 使用與 Ops Agent 相同的 `AgentSandboxManager`：

```python
from handoff.20250928.40_App.orchestrator.sandbox.manager import sandbox_manager, SandboxConfig

# 創建 Dev Agent 沙箱
config = SandboxConfig(
    agent_id="dev-agent-001",
    agent_type="dev",
    cpu_limit=1.0,
    memory_limit_mb=2048,
    network_enabled=True
)

sandbox = await sandbox_manager.create_sandbox(config)
print(f"Sandbox created: {sandbox.mcp_endpoint}")
```

### 2. 工具註冊

在 LangGraph 中註冊 Dev Agent 工具：

```python
from agents.dev_agent.tools import get_git_tool, get_ide_tool, get_filesystem_tool
from langchain.tools import Tool

def register_dev_agent_tools(sandbox_endpoint: str):
    """註冊 Dev Agent 工具到 LangGraph"""
    
    git_tool = get_git_tool(sandbox_endpoint)
    ide_tool = get_ide_tool(sandbox_endpoint)
    fs_tool = get_filesystem_tool(sandbox_endpoint)
    
    tools = [
        Tool(
            name="git_clone",
            func=git_tool.clone,
            description="Clone a git repository"
        ),
        Tool(
            name="git_commit",
            func=git_tool.commit,
            description="Commit changes to repository"
        ),
        Tool(
            name="git_create_pr",
            func=git_tool.create_pr,
            description="Create a pull request on GitHub"
        ),
        Tool(
            name="read_file",
            func=fs_tool.read_file,
            description="Read file contents"
        ),
        Tool(
            name="write_file",
            func=fs_tool.write_file,
            description="Write content to file"
        ),
        Tool(
            name="search_code",
            func=ide_tool.search_code,
            description="Search for code in workspace"
        ),
        Tool(
            name="format_code",
            func=ide_tool.format_code,
            description="Format code using language-specific formatter"
        ),
        Tool(
            name="run_linter",
            func=ide_tool.run_linter,
            description="Run linter on code"
        )
    ]
    
    return tools
```

### 3. Meta-Agent OODA 整合

Dev Agent 可以作為 Meta-Agent OODA 循環的執行節點：

```python
from langgraph.graph import StateGraph, END

class DevAgentState(TypedDict):
    task: str
    context: Dict[str, Any]
    observations: List[str]
    actions: List[str]
    result: Optional[Dict[str, Any]]

def create_dev_agent_graph(sandbox_endpoint: str):
    """創建 Dev Agent 的 OODA 循環圖"""
    
    tools = register_dev_agent_tools(sandbox_endpoint)
    
    workflow = StateGraph(DevAgentState)
    
    # Observe 階段
    def observe_node(state: DevAgentState):
        """觀察當前代碼庫狀態"""
        # 使用 IDE Tool 探索代碼庫
        pass
    
    # Orient 階段
    def orient_node(state: DevAgentState):
        """分析任務並制定策略"""
        # 使用 LLM 分析觀察結果
        pass
    
    # Decide 階段
    def decide_node(state: DevAgentState):
        """決定下一步操作"""
        # 選擇合適的工具和參數
        pass
    
    # Act 階段
    def act_node(state: DevAgentState):
        """執行操作"""
        # 調用相應的工具
        pass
    
    workflow.add_node("observe", observe_node)
    workflow.add_node("orient", orient_node)
    workflow.add_node("decide", decide_node)
    workflow.add_node("act", act_node)
    
    workflow.set_entry_point("observe")
    workflow.add_edge("observe", "orient")
    workflow.add_edge("orient", "decide")
    workflow.add_edge("decide", "act")
    workflow.add_conditional_edges(
        "act",
        lambda state: "observe" if not state.get("result") else END
    )
    
    return workflow.compile()
```

### 4. 環境配置

在 `.env` 文件中添加 Dev Agent 配置：

```bash
# Dev Agent Configuration
SANDBOX_ENABLED=true
DEV_AGENT_ENDPOINT=http://localhost:8080
DEV_AGENT_VSCODE_ENDPOINT=http://localhost:8443

# GitHub Integration
GITHUB_TOKEN=your_github_token_here

# Resource Limits
DEV_AGENT_CPU_LIMIT=1.0
DEV_AGENT_MEMORY_LIMIT_MB=2048
DEV_AGENT_DISK_LIMIT_MB=10240
```

### 5. 使用範例：完整開發任務

```python
async def example_dev_task():
    """範例：使用 Dev Agent 完成開發任務"""
    
    # 1. 創建沙箱
    config = SandboxConfig(
        agent_id="dev-task-001",
        agent_type="dev",
        network_enabled=True
    )
    sandbox = await sandbox_manager.create_sandbox(config)
    
    # 2. 初始化工具
    endpoint = sandbox.mcp_endpoint
    git_tool = get_git_tool(endpoint)
    ide_tool = get_ide_tool(endpoint)
    fs_tool = get_filesystem_tool(endpoint)
    
    # 3. 克隆倉庫
    await git_tool.clone("https://github.com/RC918/morningai.git")
    
    # 4. 創建新分支
    await git_tool.create_branch("feature/new-api")
    
    # 5. 讀取現有代碼
    result = await fs_tool.read_file("src/api/routes.py")
    current_code = result['content']
    
    # 6. 修改代碼（這裡可以用 LLM 生成）
    new_code = current_code + "\n\n@app.get('/new-endpoint')\ndef new_endpoint():\n    return {'status': 'ok'}"
    
    # 7. 寫入修改
    await fs_tool.write_file("src/api/routes.py", new_code)
    
    # 8. 格式化代碼
    await ide_tool.format_code("src/api/routes.py", "python")
    
    # 9. 運行 linter
    lint_result = await ide_tool.run_linter("src/api/routes.py", "python")
    
    # 10. 提交變更
    await git_tool.commit("feat: Add new API endpoint", ["src/api/routes.py"])
    
    # 11. 推送到遠端
    await git_tool.push("origin", "feature/new-api")
    
    # 12. 創建 PR
    pr_result = await git_tool.create_pr(
        repo="RC918/morningai",
        title="Add new API endpoint",
        body="This PR adds a new API endpoint for...",
        head="feature/new-api",
        base="main"
    )
    
    print(f"PR created: {pr_result['pr_url']}")
    
    # 13. 清理沙箱
    await sandbox_manager.destroy_sandbox(sandbox.sandbox_id)
```

## 性能優化建議

1. **沙箱重用**: 對於連續任務，重用現有沙箱而非每次創建新的
2. **並行執行**: 多個獨立任務可以使用多個沙箱並行執行
3. **快取策略**: 快取常用的倉庫和依賴
4. **資源監控**: 監控沙箱資源使用，動態調整限制

## 故障處理

```python
async def safe_dev_task():
    """帶有故障處理的開發任務"""
    sandbox = None
    try:
        # 創建沙箱
        config = SandboxConfig(agent_id="safe-task", agent_type="dev")
        sandbox = await sandbox_manager.create_sandbox(config)
        
        # 執行任務...
        
    except Exception as e:
        logger.error(f"Task failed: {e}")
        # 處理錯誤
        
    finally:
        # 確保清理沙箱
        if sandbox:
            await sandbox_manager.destroy_sandbox(sandbox.sandbox_id)
```

## 下一步

完成 Phase 1 後，將實現：

1. **Session State 管理**: 跨沙箱的狀態持久化
2. **知識圖譜**: 代碼庫結構的持久化知識
3. **學習機制**: 從過去的操作中學習最佳實踐
4. **多語言支援**: 擴展到 Go、Rust、Java 等

## 相關資源

- [Orchestrator 文檔](../../handoff/20250928/40_App/orchestrator/README.md)
- [MCP 協議文檔](../../handoff/20250928/40_App/orchestrator/mcp/README.md)
- [Devin-Level Agents Roadmap](../../docs/devin-level-agents-roadmap.md)
