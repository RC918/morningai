# Morning AI 系統架構設計

## 1. 總體架構

Morning AI 採用前後端分離的微服務架構，以實現高度的可擴展性、靈活性和可維護性。

- **前端**: 採用 Next.js 框架，基於 React 進行開發，提供豐富的用戶交互體驗。
- **後端**: 採用 FastAPI 框架，基於 Python 進行開發，提供高性能的 API 服務。
- **資料庫**: 採用 PostgreSQL 作為主要數據庫，提供穩定的數據存儲。
- **緩存**: 採用 Redis 作為緩存服務，提升系統性能。
- **部署**: 採用 Docker 進行容器化部署，並使用 Kubernetes 進行容器編排。

## 2. 前端架構

### 2.1. 技術棧

- **框架**: Next.js 14 (App Router)
- **語言**: TypeScript
- **樣式**: Tailwind CSS
- **狀態管理**: Zustand
- **數據請求**: SWR
- **表單處理**: React Hook Form
- **國際化**: next-intl

### 2.2. 介面規劃

#### 用戶儀表板 (app.morningai.me)

- **登入/註冊**: 提供多種登入方式，包括郵箱、Google、GitHub。
- **儀表板首頁**: 展示核心數據指標和快速入口。
- **租戶管理**: 創建和管理多個租戶。
- **頻道開通**: 連接 LINE、Telegram、Messenger 等平台。
- **AI Bot 管理**: 創建、配置和管理 AI Bot。
- **任務編排**: 設計和管理 AI 任務流程。
- **數據報表**: 查看和分析運營數據。
- **設置中心**: 帳號設置、安全設置、通知設置。

#### 管理後台 (admin.morningai.me)

- **用戶管理**: 管理所有用戶和租戶。
- **系統監控**: 監控系統運行狀態和性能指標。
- **日誌管理**: 查看和分析系統日誌。
- **配置管理**: 管理系統級別的配置。

## 3. 後端架構

### 3.1. 技術棧

- **框架**: FastAPI
- **語言**: Python 3.11
- **異步處理**: Celery
- **資料庫 ORM**: SQLAlchemy
- **數據驗證**: Pydantic

### 3.2. 微服務劃分

- **認證服務**: 處理用戶認證和授權。
- **租戶服務**: 管理租戶和頻道。
- **AI Agent 服務**: 執行 AI 任務和對話。
- **數據服務**: 提供數據存儲和查詢。
- **通知服務**: 發送郵件、短信和推送通知。

## 4. API 介面設計

採用 RESTful API 風格，並使用 OpenAPI 規範進行文檔化。

### 核心 API 端點

- `/auth/register`: 用戶註冊
- `/auth/login`: 用戶登入
- `/tenants`: 租戶管理
- `/bindings`: 平台綁定
- `/bots`: AI Bot 管理
- `/tasks`: 任務編排
- `/reports`: 數據報表

## 5. 系統架構圖

```mermaid
graph TD
    subgraph 用戶端
        A[用戶儀表板 (Next.js)]
        B[管理後台 (Next.js)]
    end

    subgraph API 閘道
        C[API Gateway (e.g., Nginx)]
    end

    subgraph 後端微服務 (FastAPI)
        D[認證服務]
        E[租戶服務]
        F[AI Agent 服務]
        G[數據服務]
        H[通知服務]
    end

    subgraph 數據存儲
        I[PostgreSQL]
        J[Redis]
    end

    subgraph 基礎設施
        K[Docker]
        L[Kubernetes]
    end

    A --> C
    B --> C
    C --> D
    C --> E
    C --> F
    C --> G
    C --> H
    D --> I
    E --> I
    F --> I
    F --> J
    G --> I
    H --> J

    D -- "異步任務" --> M[Celery Worker]
    E -- "異步任務" --> M
    F -- "異步任務" --> M
    H -- "異步任務" --> M

    M --> J
```


