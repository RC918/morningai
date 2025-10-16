# Dev Agent Implementation - Work Ticket

## 工單資訊

**工單編號**: DEV-AGENT-001  
**優先級**: High  
**類型**: Feature Implementation  
**預計時間**: 2 週 (Phase 1)  
**負責人**: Development Team  
**狀態**: In Progress

## 目標

實現具備 Devin-level 能力的 Dev Agent，為 Morning AI 生態系統提供通用軟體工程能力。

## 背景

Morning AI 目前的 Agent 生態系統專注於特定領域任務。為了提供更全面的開發自動化能力，需要實現類似 Devin AI 的通用開發 Agent，配備：
- 完整 IDE 環境
- Shell 執行能力
- Language Server Protocol (LSP) 整合
- Git 版本控制
- 安全沙箱隔離

## 實作範圍

### Phase 1: 基礎沙箱與工具 (Week 1-2) ✅ **已完成**

#### Week 1: 沙箱環境搭建 ✅
- [x] 設計 Dev_Agent Dockerfile（基於現有 ops_agent）
- [x] 整合 VSCode Server (code-server)
- [x] 配置 LSP Servers
  - [x] Python LSP (pylsp + plugins)
  - [x] TypeScript/JavaScript LSP
  - [x] YAML、Dockerfile LSP
- [x] 安全配置
  - [x] Seccomp profile
  - [x] AppArmor profile
  - [x] 資源限制
- [x] Docker Compose 配置

#### Week 2: 開發工具實現 ✅
- [x] Git_Tool 增強版
  - [x] Clone、Commit、Push
  - [x] Branch 管理
  - [x] PR 創建（GitHub API）
  - [x] Diff、Status
- [x] IDE_Tool
  - [x] 檔案開啟/編輯
  - [x] 代碼搜尋
  - [x] 代碼格式化
  - [x] Linter 整合
  - [x] LSP 啟動
- [x] FileSystem_Tool
  - [x] 檔案讀寫
  - [x] 目錄操作
  - [x] 檔案搜尋
  - [x] 檔案資訊查詢
- [x] E2E 測試
  - [x] 沙箱啟動測試
  - [x] 工具調用測試
  - [x] 整合測試

### Phase 2: Meta-Agent 整合 (Week 3-4) 🔜 **下一步**

#### Week 3: OODA 循環整合
- [ ] 設計 Dev_Agent State Schema
- [ ] 實現 Observe 節點（代碼探索）
- [ ] 實現 Orient 節點（任務分析）
- [ ] 實現 Decide 節點（策略選擇）
- [ ] 實現 Act 節點（工具執行）
- [ ] 整合到現有 Orchestrator

#### Week 4: Session State 管理
- [ ] 設計 Session State 結構
- [ ] 實現 Context Window 管理
- [ ] 實現知識圖譜（代碼庫結構）
- [ ] 實現學習機制（編碼模式）
- [ ] 持久化層設計

## 已交付成果

### 1. 沙箱基礎設施
```
agents/dev_agent/sandbox/
├── Dockerfile              # ✅ Dev Agent 容器定義
├── requirements.txt        # ✅ Python 依賴
├── docker-compose.yml      # ✅ 容器編排
├── dev_agent_sandbox.py    # ✅ 沙箱核心邏輯
├── mcp_client.py          # ✅ MCP 伺服器
├── seccomp-profile.json   # ✅ 安全配置
└── apparmor-profile       # ✅ 安全配置
```

### 2. 開發工具
```
agents/dev_agent/tools/
├── __init__.py            # ✅ 工具模組
├── git_tool.py           # ✅ Git 操作工具
├── ide_tool.py           # ✅ IDE 功能工具
└── filesystem_tool.py    # ✅ 檔案系統工具
```

### 3. 測試與文檔
```
agents/dev_agent/
├── tests/
│   └── test_e2e.py       # ✅ E2E 測試套件
├── README.md             # ✅ 使用文檔
└── INTEGRATION.md        # ✅ 整合指南
```

### 4. 核心功能

#### Git 工具
- ✅ 倉庫克隆
- ✅ 提交變更
- ✅ 分支管理
- ✅ 推送到遠端
- ✅ PR 創建
- ✅ 狀態查詢
- ✅ Diff 查看

#### IDE 工具
- ✅ 檔案開啟/編輯
- ✅ 代碼搜尋
- ✅ 代碼格式化（Black、Prettier）
- ✅ Linter 執行（Ruff、ESLint）
- ✅ LSP 伺服器啟動
- ✅ 檔案樹瀏覽

#### 檔案系統工具
- ✅ 檔案讀寫
- ✅ 目錄創建
- ✅ 檔案刪除/複製/移動
- ✅ 檔案搜尋
- ✅ 檔案資訊查詢

#### 安全特性
- ✅ Docker 容器隔離
- ✅ 資源限制（CPU: 1.0, RAM: 2GB）
- ✅ 非 root 使用者執行
- ✅ Seccomp 系統呼叫限制
- ✅ AppArmor 訪問控制
- ✅ 唯讀檔案系統（除工作區）

## 測試計畫

### Phase 1 測試 ✅
- [x] 單元測試：各工具獨立測試
- [x] 整合測試：沙箱與工具整合
- [x] E2E 測試：完整開發流程
- [x] 安全測試：沙箱隔離驗證

### Phase 2 測試 🔜
- [ ] OODA 循環測試
- [ ] State 管理測試
- [ ] 性能測試
- [ ] 壓力測試

## 部署計畫

### 開發環境部署
```bash
cd agents/dev_agent/sandbox
docker-compose up -d
```

### 生產環境部署
- 使用 Fly.io 部署（利用免費額度）
- 配置環境變數
- 設置監控和日誌

## 風險與緩解

### 已緩解的風險 ✅
1. **容器構建複雜度** 
   - 緩解：基於現有 ops_agent，漸進式添加功能
   
2. **安全配置錯誤**
   - 緩解：複用經過驗證的 seccomp 和 AppArmor 配置

### 待處理的風險 🔜
1. **資源消耗過高**
   - 計畫：實施嚴格的資源限制和監控
   
2. **沙箱逃逸風險**
   - 計畫：多層安全防護，定期安全審計

## 成功標準

### Phase 1 ✅
- [x] Dev Agent 沙箱可以成功啟動
- [x] 所有工具可以正常調用
- [x] E2E 測試通過
- [x] 文檔完整

### Phase 2 🔜
- [ ] 可以完成完整的開發任務（clone → edit → commit → PR）
- [ ] OODA 循環正常運行
- [ ] Session state 正確持久化
- [ ] 性能符合預期（< 5s 響應時間）

## 後續計畫

### Phase 3: 高級功能 (Week 5-8)
- [ ] 多語言支援（Go、Rust、Java）
- [ ] 瀏覽器整合（Playwright）
- [ ] Terminal 整合
- [ ] 調試器支援

### Phase 4: 優化與擴展 (Week 9-13)
- [ ] 性能優化
- [ ] 智能緩存
- [ ] 並行任務執行
- [ ] 錯誤恢復機制

## 相關資源

- [Devin-Level Agents Roadmap](./devin-level-agents-roadmap.md)
- [Dev Agent README](../agents/dev_agent/README.md)
- [Integration Guide](../agents/dev_agent/INTEGRATION.md)
- [Orchestrator Documentation](../handoff/20250928/40_App/orchestrator/README.md)

## 需要使用者操作的部分

### 立即需要 ⚠️
1. **GitHub Token 配置**
   - 請在 `.env` 中配置 `GITHUB_TOKEN`
   - 用於 PR 創建功能

2. **Fly.io 帳號確認**
   - 確認 Fly.io 帳號和免費額度
   - 用於生產環境部署

### 可選配置
1. **資源限制調整**
   - 根據實際需求調整 `docker-compose.yml` 中的資源限制
   
2. **安全配置審查**
   - 審查 `seccomp-profile.json` 和 `apparmor-profile`
   - 根據安全要求調整

## 更新記錄

- **2025-10-16**: Phase 1 完成，創建工單
  - 完成沙箱基礎設施
  - 完成所有核心工具
  - 完成 E2E 測試
  - 完成文檔撰寫

---

**下一步行動**: 提交 PR 並開始 Phase 2 實作
