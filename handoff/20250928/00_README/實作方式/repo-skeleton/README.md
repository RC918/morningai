# Phase 2 Repo Skeleton - AI Agent 輔助綁定

這個腳手架包含了實現 AI Agent 輔助綁定功能的最小化程式碼結構。

## 目錄結構

```
/morningai-core
├── /app
│   ├── /api
│   │   └── /v1
│   │       └── /endpoints
│   │           └── binding_agent.py  # 新增: AI 綁定助手的 API 端點
│   ├── /services
│   │   └── binding_service.py      # 新增: 處理平台綁定邏輯的服務
│   └── /agents
│       └── binding_flow_agent.py   # 新增: 定義對話流程的 Agent
├── /models
│   └── platform_binding.py       # 新增: 平台綁定相關的數據模型
└── /core
    └── config.py                 # 修改: 新增平台 API 的相關配置

/morningai-web
└── /src
    ├── /components
    │   └── /binding
    │       └── AIAgentDialog.tsx   # 新增: 對話式 UI 組件
    └── /app
        └── /(dashboard)
            └── /settings
                └── /integrations
                    └── page.tsx      # 修改: 替換舊表單為新按鈕和對話框
```

## 關鍵檔案說明

### 後端 (`morningai-core`)

- **`binding_agent.py`**: 
  - `/start`: 啟動一個新的綁定對話流程。
  - `/next`: 處理用戶的下一步輸入（例如，提供 Token）。
  - `/status`: 查詢當前綁定狀態。

- **`binding_service.py`**: 
  - `validate_token(platform, token)`: 驗證 Token 的有效性。
  - `setup_webhook(platform, tenant_id, token)`: 自動設置 Webhook。
  - `send_test_message(platform, tenant_id)`: 發送測試消息。

- **`binding_flow_agent.py`**: 
  - 使用狀態機或決策樹來管理對話流程。
  - 根據用戶的回答提供不同的引導文本和視覺輔助材料。

- **`platform_binding.py`**: 
  - Pydantic 模型，用於 API 的請求和響應。
  - SQLAlchemy 模型，用於存儲綁定信息到資料庫。

### 前端 (`morningai-web`)

- **`AIAgentDialog.tsx`**: 
  - 一個 React 組件，用於呈現對話式 UI。
  - 管理與後端 `binding_agent` 的 API 通信。
  - 顯示 AI Agent 的消息、用戶的輸入選項以及指南圖片/動畫。

- **`page.tsx`**: 
  - 包含「AI 助手一鍵綁定」按鈕。
  - 處理點擊事件，打開 `AIAgentDialog` 模態框。

## 快速啟動

1.  **後端**: 在 `morningai-core` 中，應用資料庫遷移，然後運行 FastAPI 服務。
2.  **前端**: 在 `morningai-web` 中，運行 `npm run dev`。
3.  訪問 `http://localhost:3000/settings/integrations` 即可看到新的綁定按鈕。


