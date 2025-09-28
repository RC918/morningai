# Morning AI - 企業級智能決策系統

**版本**: 3.0 (企業增強版)

**核心理念**: 智能決策，自主學習，持續優化

## 項目概述

Morning AI 是一個先進的、自主學習的智能決策系統，旨在幫助企業自動化運維、優化資源配置、預測系統行為並做出最佳決策。此版本在原有基礎上進行了全面的企業級強化，包括自動化測試、可視化管理和金融級安全。

## 核心功能

- **智能決策引擎**: 基於 Meta-Agent 架構，能夠綜合分析系統狀態，生成並評估多種解決方案。
- **自主學習系統**: 能夠從歷史決策和用戶反饋中學習，持續優化策略庫，讓系統越用越聰明。
- **AI服務抽象層**: 解耦對外部AI服務的依賴，支持多模型智能路由和成本優化。
- **前端管理儀表板**: 提供可視化的系統監控、策略管理、決策審批和成本分析界面。
- **企業級安全性**: 包括密鑰管理、API安全、通信加密、安全掃描和審計日誌。
- **自動化測試體系**: 完整的單元、集成和端到端測試，確保系統的健壯性和可靠性。

## 技術棧

- **後端**: Python, Flask, SQLAlchemy
- **前端**: React, Vite, Tailwind CSS, shadcn/ui
- **數據庫**: PostgreSQL (推薦), SQLite (開發)
- **緩存**: Redis
- **AI**: OpenAI (可擴展), pgvector
- **測試**: pytest, Playwright (推薦)
- **安全**: JWT, OAuth2, Fernet, mTLS (推薦)

## 快速啟動

1. **安裝依賴**:
   ```bash
   # 安裝後端依賴
   cd api-backend
   pip install -r requirements.txt

   # 安裝前端依賴
   cd ../frontend-dashboard
   npm install
   ```

2. **配置環境**:
   - 複製 `config_template.yaml` 為 `config.yaml`
   - 填寫必要的配置，特別是 `openai_api_key` 和數據庫連接信息。

3. **啟動後端**:
   ```bash
   cd api-backend
   python src/main.py
   ```

4. **啟動前端**:
   ```bash
   cd frontend-dashboard
   npm run dev
   ```

5. **訪問儀表板**:
   - 打開瀏覽器，訪問 `http://localhost:3000`
   - 使用默認帳號 `admin` / `admin123` 登錄。

## 測試

- **運行所有測試**:
  ```bash
  pytest
  ```

- **查看測試覆蓋率報告**:
  - 打開 `htmlcov/index.html`

## 安全

- **依賴項安全掃描**:
  ```bash
  python dependency_scanner.py .
  ```

- **安全配置**:
  - 所有敏感信息都應通過 `secure_config.py` 進行加密管理。

## 部署

1. **構建前端**:
   ```bash
   cd frontend-dashboard
   npm run build
   ```

2. **複製前端文件到後端**:
   - 將 `frontend-dashboard/dist` 目錄下的所有文件複製到 `api-backend/src/static`。

3. **部署後端**:
   - 使用 Gunicorn 或 uWSGI 等生產級服務器部署 Flask 應用。

## 未來展望

- **多租戶支持**: 為SaaS服務提供多租戶隔離。
- **更複雜的AI模型**: 集成更多領域專用的AI模型。
- **數字孿生**: 建立更精確的系統數字孿生模型，用於模擬和預測。
- **無代碼策略編輯器**: 允許非技術人員通過可視化界面創建和編輯決策策略。


