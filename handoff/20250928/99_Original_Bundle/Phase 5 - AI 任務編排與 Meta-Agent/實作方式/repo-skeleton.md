# Phase 5: AI Orchestrator & Meta-Agent - Repo Skeleton

## 📂 目錄結構

```
morningai-core/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── orchestrator.py
│   │   │   │   └── governance.py
│   │   │   └── routes.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   ├── models/
│   │   │   ├── workflow.py
│   │   │   └── agent.py
│   │   └── session.py
│   ├── schemas/
│   │   ├── workflow.py
│   │   └── agent.py
│   ├── services/
│   │   ├── orchestrator_service.py
│   │   └── agent_service.py
│   └── main.py
├── agents/
│   ├── base_agent.py
│   ├── product_master/
│   │   ├── main.py
│   │   └── tools.py
│   ├── code_writer/
│   │   ├── main.py
│   │   └── tools.py
│   └── qa_auditor/
│       ├── main.py
│       └── tools.py
├── workflows/
│   ├── new_feature_development.py
│   └── bug_fix.py
├── tests/
│   ├── test_orchestrator.py
│   └── test_agents.py
├── .env.sample
├── Dockerfile
└── requirements.txt
```

## 📝 文件說明

### `app/` - 主應用程式 (FastAPI)

- **`api/`**: API 端點定義。
  - `orchestrator.py`: 處理工作流的創建、啟動、監控。
  - `governance.py`: 處理 HITL 審批、Agent 狀態查詢。
- **`db/`**: 資料庫模型 (SQLAlchemy) 和會話管理。
  - `workflow.py`: `WorkflowRun` 和 `TaskRun` 模型。
  - `agent.py`: `Agent` 模型，用於註冊 Agent。
- **`schemas/`**: Pydantic 模型，用於 API 的請求和響應。
- **`services/`**: 核心業務邏輯。
  - `orchestrator_service.py`: 封裝 LangGraph 的調用、狀態管理。
  - `agent_service.py`: Agent 的註冊、發現和調度邏輯。

### `agents/` - AI Agent Hub

- **`base_agent.py`**: 所有 Agent 的抽象基類，定義標準接口。
- **`product_master/`**, **`code_writer/`**, **`qa_auditor/`**: 各個具體 Agent 的實現。
  - `main.py`: Agent 的主邏輯。
  - `tools.py`: Agent 使用的工具 (e.g., file I/O, API calls)。

### `workflows/` - 工作流定義

- **`new_feature_development.py`**: 「新功能開發」工作流的 LangGraph 定義。
- **`bug_fix.py`**: 「Bug 修復」工作流的 LangGraph 定義。

### `tests/` - 自動化測試

- **`test_orchestrator.py`**: 對 Orchestrator 服務的單元測試和整合測試。
- **`test_agents.py`**: 對各個 Agent 的功能測試。

## 🚀 快速啟動

1.  **安裝依賴**
    ```bash
    pip install -r requirements.txt
    ```

2.  **設置環境變數**
    ```bash
    cp .env.sample .env
    # 編輯 .env 文件，填寫資料庫連接等信息
    ```

3.  **運行資料庫遷移**
    ```bash
    alembic upgrade head
    ```

4.  **啟動應用**
    ```bash
    uvicorn app.main:app --reload
    ```

## 📦 Docker 部署

```bash
# 構建 Docker 映像
docker build -t morningai-core .

# 運行 Docker 容器
docker run -d -p 8000:8000 --env-file .env morningai-core
```

## 🤖 Agent 註冊流程

1.  每個 Agent 在啟動時，向 Orchestrator 的 `/api/v1/agents/register` 端點發送 POST 請求。
2.  請求 Body 包含 Agent 的名稱、能力描述、API 端點和健康檢查端點。
3.  Orchestrator 將 Agent 信息存儲在資料庫中，並定期進行健康檢查。

## ⚙️ 工作流觸發

- **API 觸發**: 向 `/api/v1/orchestrator/workflows/{workflow_name}/run` 發送 POST 請求。
- **對話式觸發**: 在治理主控台輸入自然語言指令，由後端解析並觸發對應的工作流。

