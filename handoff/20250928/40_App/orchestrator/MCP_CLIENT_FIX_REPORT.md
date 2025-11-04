# MCP Client Session Leak Fix - 2025-10-19

**Issue**: Sentry 報告多個嚴重錯誤  
**Reported by**: Ryan Chen (@RC918)  
**Fixed by**: Devin AI

---

## 🚨 Sentry 錯誤報告

From Sentry dashboard (`morningai-backend-v2`):

1. **Unclosed client session** (asyncio) - 6 events
   - Tag: `asyncio`
   - 原因：aiohttp ClientSession 未正確關閉

2. **Failed to call tool shell/browser** - MCP client 連接失敗
   - Tag: `mcp.client`
   - 原因：連接錯誤、缺少錯誤處理

3. **[Executor] Step failed** - 3 events
   - Tag: `langgraph_orchestrator`
   - 原因：Orchestrator 執行失敗

4. **LangGraph orchestrator failed: Workflow failed** - 3 events
   - Tag: `langgraph_orchestrator`
   - 原因：Workflow 失敗導致連鎖錯誤

5. **[CI Monitor] Failed to check CI: API Error** - 3 events
   - Tag: `langgraph_orchestrator`
   - 原因：GitHub API 調用失敗

---

## 🔍 根本原因分析

### 問題 1: Asyncio Session 洩漏

**原因**:
```python
# 舊代碼
async def connect(self):
    self.session = aiohttp.ClientSession()  # ❌ 創建但可能未關閉
```

**後果**:
- aiohttp ClientSession 物件未正確關閉
- 觸發 Python asyncio 警告
- 資源洩漏（連接、記憶體）
- Sentry 報告 "Unclosed client session"

### 問題 2: 缺少 Context Manager

**原因**:
- 沒有實現 `__aenter__` 和 `__aexit__`
- 使用者必須手動調用 `connect()` 和 `disconnect()`
- 容易忘記調用 `disconnect()`

**後果**:
- 測試中可能遺漏 `disconnect()` 調用
- 異常情況下 session 不會被關閉
- 資源洩漏

### 問題 3: 連接錯誤處理不足

**原因**:
```python
# 舊代碼
if not self.session:
    raise Exception("MCP client not connected")  # ❌ 錯誤訊息不清楚
```

**後果**:
- 錯誤訊息不友善
- 沒有檢查 session 是否已關閉
- 連接失敗時沒有具體錯誤類型

---

## ✅ 修復方案

### 修復 1: 實現 Async Context Manager

**文件**: `orchestrator/mcp/client.py`

**變更**:
```python
class MCPClient:
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures session is closed"""
        await self.disconnect()
        return False
```

**優點**:
- ✅ 自動管理 session 生命週期
- ✅ 異常情況下確保 session 關閉
- ✅ 符合 Python 最佳實踐
- ✅ 代碼更簡潔

**使用方式**:
```python
# ✅ 新方式（推薦）
async with MCPClient(server_url, agent_id) as client:
    result = await client.execute_shell('echo "Hello"')
    # session 自動關閉

# ⚠️  舊方式（仍支援但不推薦）
client = MCPClient(server_url, agent_id)
await client.connect()
try:
    result = await client.execute_shell('echo "Hello"')
finally:
    await client.disconnect()
```

---

### 修復 2: 加強 Session 關閉邏輯

**文件**: `orchestrator/mcp/client.py`

**變更**:
```python
async def disconnect(self):
    """Disconnect from MCP server and ensure session is closed"""
    if self.session and not self.session.closed:
        try:
            await self.session.close()
            self.logger.info("MCP client session closed")
        except Exception as e:
            self.logger.error(f"Error closing MCP client session: {e}")
        finally:
            self.session = None
            self._connected = False
```

**改進**:
- ✅ 檢查 `session.closed` 狀態
- ✅ 使用 try/finally 確保清理
- ✅ 記錄關閉錯誤
- ✅ 設置 `_connected` 標記

---

### 修復 3: 改進連接狀態追蹤

**文件**: `orchestrator/mcp/client.py`

**變更**:
```python
def __init__(self, server_url: str, agent_id: str, timeout: int = 30):
    self.server_url = server_url
    self.agent_id = agent_id
    self.timeout = timeout  # ← 新增超時配置
    self.logger = logging.getLogger(__name__)
    self.session: Optional[aiohttp.ClientSession] = None
    self._connected = False  # ← 新增連接狀態追蹤

async def connect(self):
    """Connect to MCP server"""
    if self._connected:
        self.logger.warning("MCP client already connected")
        return
    
    try:
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        self._connected = True
        self.logger.info(f"MCP client connected to {self.server_url}")
    except Exception as e:
        self.logger.error(f"Failed to create MCP client session: {e}")
        raise
```

**改進**:
- ✅ 新增 `_connected` 狀態標記
- ✅ 防止重複連接
- ✅ 配置超時參數
- ✅ 改進錯誤處理

---

### 修復 4: 增強錯誤處理

**文件**: `orchestrator/mcp/client.py`

**變更**:
```python
async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Call a tool via MCP protocol"""
    if not self.session or not self._connected:
        error_msg = "MCP client not connected. Call connect() first or use async context manager."
        self.logger.error(error_msg)
        raise ConnectionError(error_msg)  # ← 使用特定異常類型
    
    if self.session.closed:
        error_msg = "MCP client session is closed"
        self.logger.error(error_msg)
        raise ConnectionError(error_msg)  # ← 檢查 session 狀態
    
    try:
        async with self.session.post(...) as response:
            if response.status >= 400:
                error_text = await response.text()
                raise Exception(f"HTTP {response.status}: {error_text}")
            
            result = await response.json()
            
            if "error" in result:
                error_msg = result['error'].get('message', 'Unknown error')
                self.logger.error(f"MCP tool call failed: {error_msg}")
                raise Exception(f"MCP tool error: {error_msg}")
            
            return result.get("result", {})
            
    except aiohttp.ClientError as e:
        error_msg = f"Cannot connect to host localhost: {e}"
        self.logger.error(f"Failed to call tool {tool_name}: {error_msg}")
        raise ConnectionError(error_msg) from e  # ← 保留原始異常
    except Exception as e:
        self.logger.error(f"Failed to call tool {tool_name}: {e}")
        raise
```

**改進**:
- ✅ 使用 `ConnectionError` 而非通用 `Exception`
- ✅ 檢查 HTTP 狀態碼
- ✅ 檢查 JSON-RPC 錯誤
- ✅ 區分 `aiohttp.ClientError` 和其他異常
- ✅ 更清晰的錯誤訊息

---

### 修復 5: 更新測試使用 Context Manager

**文件**: `orchestrator/tests/test_ops_agent_sandbox.py`

**變更**:
```python
# ❌ 舊代碼
@pytest.mark.asyncio
async def test_ops_agent_shell_execution():
    sandbox = await sandbox_manager.create_sandbox(config)
    try:
        client = MCPClient(sandbox.mcp_endpoint, sandbox.agent_id)
        await client.connect()
        result = await client.execute_shell('echo "Hello"')
        await client.disconnect()  # ← 可能被遺忘
    finally:
        await sandbox_manager.destroy_sandbox(sandbox.sandbox_id)

# ✅ 新代碼
@pytest.mark.asyncio
async def test_ops_agent_shell_execution():
    sandbox = await sandbox_manager.create_sandbox(config)
    try:
        async with MCPClient(sandbox.mcp_endpoint, sandbox.agent_id) as client:
            result = await client.execute_shell('echo "Hello"')
            # session 自動關閉 ✅
    finally:
        await sandbox_manager.destroy_sandbox(sandbox.sandbox_id)
```

**優點**:
- ✅ 更簡潔
- ✅ 自動資源管理
- ✅ 異常安全

---

## 📊 影響分析

### Before（修復前）

**問題**:
- ❌ Sentry 報告 6+ 個 session 洩漏
- ❌ MCP 連接失敗錯誤
- ❌ Orchestrator workflow 失敗
- ❌ 資源洩漏（連接、記憶體）

**統計**:
- Unclosed sessions: 6 events
- MCP failures: 2 events
- Orchestrator failures: 9 events
- 總計: 17+ 錯誤事件

### After（修復後）

**改進**:
- ✅ Context manager 自動管理 session
- ✅ 加強錯誤處理和日誌
- ✅ 狀態追蹤和驗證
- ✅ 更清晰的錯誤訊息

**預期效果**:
- Session 洩漏: 0 events
- 更友善的錯誤訊息
- 更容易調試和維護
- 符合 Python 最佳實踐

---

## 🧪 測試建議

### 手動測試

```python
import asyncio
from mcp.client import MCPClient

async def test_context_manager():
    # 測試 context manager
    async with MCPClient("http://localhost:8000", "test-agent") as client:
        try:
            result = await client.execute_shell('echo "Test"')
            print("Success:", result)
        except ConnectionError as e:
            print("Connection error (expected if server not running):", e)

asyncio.run(test_context_manager())
```

### 自動化測試

```bash
cd handoff/20250928/40_App/orchestrator
pytest tests/test_ops_agent_sandbox.py -v
```

---

## 📝 遷移指南

### 對現有代碼的影響

**向後兼容**: ✅  
舊的 `connect()` / `disconnect()` 方式仍然可用。

**建議更新**: ✅  
所有新代碼應使用 async context manager。

**遷移步驟**:

1. **識別舊模式**:
   ```python
   client = MCPClient(...)
   await client.connect()
   try:
       # use client
   finally:
       await client.disconnect()
   ```

2. **轉換為新模式**:
   ```python
   async with MCPClient(...) as client:
       # use client
   ```

3. **測試驗證**:
   - 執行測試確保功能正常
   - 檢查 Sentry 確認錯誤消失

---

## 🚀 部署指示

1. **合併 PR** - 將修復合併到 main
2. **重新部署** - 部署新版本到 production
3. **監控 Sentry** - 確認錯誤消失
4. **更新文檔** - 通知團隊新的使用方式

---

## 📚 相關文件

- `orchestrator/mcp/client.py` - MCP Client 實現
- `orchestrator/tests/test_ops_agent_sandbox.py` - 更新的測試
- [Python Context Managers](https://docs.python.org/3/reference/datamodel.html#context-managers)
- [aiohttp Client Session](https://docs.aiohttp.org/en/stable/client_reference.html#client-session)

---

**Status**: ✅ 修復完成  
**Tested**: ⏳ 待測試  
**Deployed**: ⏳ 待部署
