# Local Development Setup Guide

## 快速啟動指南 (Quick Start)

本指南將協助您在本地環境快速啟動 Morning AI 專案進行開發。

### 系統需求

- **Python**: 3.12+ (使用 pyenv 管理版本)
- **Node.js**: 18+ (使用 nvm 管理版本)
- **Redis**: 7.0+ (本地或 Docker)
- **PostgreSQL**: 16+ (可選，測試使用 SQLite)
- **Git**: 2.30+

### 最短啟動路徑 (Minimal Setup)

#### 1. 克隆專案

```bash
git clone https://github.com/RC918/morningai.git
cd morningai
```

#### 2. 設定環境變數

複製環境變數範本並設定最少 5 個必需變數：

```bash
cp .env.example .env
```

編輯 `.env` 並設定以下**最低限度**變數：

```bash
# 必需 (5 個變數)
JWT_SECRET_KEY=your-secret-key-minimum-32-characters-long-please
ADMIN_PASSWORD=your-secure-admin-password
SECRET_KEY=your-flask-secret-key-also-32-chars-min
DATABASE_URL=sqlite:///database/app.db
REDIS_URL=redis://localhost:6379/0
```

💡 **提示**: 完整的環境變數清單和說明請參閱 [環境變數 Schema 文件](/docs/config/env_schema.md)

#### 3. 啟動 Redis (Docker)

如果本機沒有 Redis，使用 Docker 快速啟動：

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

驗證 Redis 運作：

```bash
redis-cli ping
# 應該返回: PONG
```

#### 4. 後端設定與啟動

```bash
cd handoff/20250928/40_App/api-backend

# 安裝依賴
pip install -r requirements.txt

# 啟動開發伺服器
cd src
python main.py
```

後端將在 `http://localhost:5001` 運作。

#### 5. Worker 設定與啟動 (可選)

在新的終端視窗：

```bash
cd handoff/20250928/40_App/orchestrator

# 安裝依賴
pip install -r requirements.txt
pip install -e .

# 啟動 Worker
python redis_queue/worker.py
```

#### 6. 前端設定與啟動 (可選)

在新的終端視窗：

```bash
cd handoff/20250928/40_App/frontend-dashboard

# 安裝依賴
npm install
# 或使用 pnpm: pnpm install

# 設定前端環境變數
cp .env.example .env.local
# 編輯 .env.local 設定 VITE_API_BASE_URL=http://localhost:5001

# 啟動開發伺服器
npm run dev
```

前端將在 `http://localhost:5173` 運作。

### 驗證設定

#### 健康檢查

```bash
# 後端健康檢查
curl http://localhost:5001/health

# 預期回應:
# {"status":"healthy","version":"9.0.0","timestamp":"..."}
```

#### 環境變數驗證

```bash
# 驗證環境變數設定
curl http://localhost:5001/api/validate-env

# 檢查缺失的必需變數
```

---

## 完整開發環境 (Full Development Setup)

### 外部服務整合

如需完整功能（AI、部署、監控），需要設定以下 19 個必需環境變數：

#### Cloud Services - Supabase (3 變數)

```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

註冊 [Supabase](https://supabase.com) 並建立專案以取得這些金鑰。

#### Cloud Services - Cloudflare (2 變數)

```bash
CLOUDFLARE_API_TOKEN=your-cloudflare-token
CLOUDFLARE_ZONE_ID=your-zone-id
```

從 [Cloudflare Dashboard](https://dash.cloudflare.com) 取得 API Token 和 Zone ID。

#### Cloud Services - Vercel (3 變數)

```bash
VERCEL_TOKEN=your-vercel-token
VERCEL_ORG_ID=your-org-id
VERCEL_PROJECT_ID=your-project-id
```

從 [Vercel Settings](https://vercel.com/account/tokens) 取得 Token 和專案 ID。

#### Cloud Services - Render (1 變數)

```bash
RENDER_API_KEY=your-render-key
```

從 [Render Dashboard](https://dashboard.render.com/account) 取得 API Key。

#### Cloud Services - Upstash Redis (2 變數)

```bash
UPSTASH_REDIS_REST_URL=https://xxxxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-upstash-token
```

註冊 [Upstash](https://upstash.com) 並建立 Redis 資料庫。

#### Monitoring - Sentry (1 變數)

```bash
SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
```

從 [Sentry](https://sentry.io) 建立專案以取得 DSN。

#### Integration - GitHub (2 變數)

```bash
GITHUB_TOKEN=ghp_xxxxx
GITHUB_REPO=RC918/morningai
```

從 [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens) 建立 Token（需要 `repo` 和 `workflow` 權限）。

#### Integration - OpenAI (1 變數)

```bash
OPENAI_API_KEY=sk-xxxxx
```

從 [OpenAI API Keys](https://platform.openai.com/api-keys) 取得 API Key。

---

## 開發工作流程

### 執行測試

```bash
# 後端測試
cd handoff/20250928/40_App/api-backend
pytest

# 產生覆蓋率報告
pytest --cov=src --cov-report=term --cov-report=xml

# Orchestrator 測試
cd ../orchestrator
pytest
```

### Lint 與格式化

```bash
# 後端 Lint
cd handoff/20250928/40_App/api-backend
ruff check .

# 前端 Lint
cd ../frontend-dashboard
npm run lint
```

### 本地 CI 驗證

在提交 PR 前，可以本地執行關鍵檢查：

```bash
# 環境變數 Schema 驗證
python - <<'EOF'
import yaml
with open('config/env.schema.yaml', 'r') as f:
    schema = yaml.safe_load(f)
print(f"✅ Schema valid: {len(schema['fields'])} variables defined")
EOF

# 產生 .env.example 並檢查差異
python scripts/generate_env_example.py
git diff .env.example
```

---

## 常見問題排除

### 1. Redis 連線失敗

**錯誤訊息**:
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**解決方案**:

```bash
# 檢查 Redis 是否運作
redis-cli ping

# 如果沒有回應，啟動 Redis
docker run -d -p 6379:6379 redis:7-alpine

# 檢查 .env 中的 REDIS_URL 設定
echo $REDIS_URL
# 應該是: redis://localhost:6379/0
```

### 2. 缺失環境變數

**錯誤訊息**:
```
Missing required environment variable: JWT_SECRET_KEY
```

**解決方案**:

```bash
# 檢查 .env 檔案是否存在
ls -la .env

# 如果不存在，從範本複製
cp .env.example .env

# 編輯並設定必需變數
nano .env

# 驗證設定
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('JWT_SECRET_KEY:', 'SET' if os.getenv('JWT_SECRET_KEY') else 'MISSING')"
```

### 3. 資料庫遷移錯誤

**錯誤訊息**:
```
sqlalchemy.exc.OperationalError: no such table
```

**解決方案**:

```bash
# 使用 SQLite 本地開發時，確保資料庫目錄存在
mkdir -p handoff/20250928/40_App/api-backend/database

# 如果使用 PostgreSQL，確認 DATABASE_URL 正確
echo $DATABASE_URL
```

### 4. 模組導入錯誤

**錯誤訊息**:
```
ModuleNotFoundError: No module named 'morningai_orchestrator'
```

**解決方案**:

```bash
# 確保 orchestrator 已安裝
cd handoff/20250928/40_App/orchestrator
pip install -e .

# 驗證安裝
pip list | grep morningai
```

### 5. 前端 API 連線失敗

**錯誤訊息** (瀏覽器控制台):
```
Failed to fetch: CORS error
```

**解決方案**:

```bash
# 檢查後端 CORS 設定
# .env 中應該包含:
CORS_ORIGINS=http://localhost:5173,http://localhost:5174

# 確認後端正在運作
curl http://localhost:5001/health

# 檢查前端 API base URL
# frontend-dashboard/.env.local 應該有:
VITE_API_BASE_URL=http://localhost:5001
```

### 6. Worker 無法連線到 Backend

**症狀**: Task 狀態始終為 "Task not found"

**解決方案**:

```bash
# 確認 Backend 和 Worker 使用相同的 REDIS_URL
# 在兩個終端分別執行:

# Terminal 1 (Backend)
cd handoff/20250928/40_App/api-backend/src
echo $REDIS_URL
python main.py

# Terminal 2 (Worker)
cd handoff/20250928/40_App/orchestrator
echo $REDIS_URL
python redis_queue/worker.py

# 兩個 REDIS_URL 必須完全相同

# 檢查 Queue
redis-cli
> KEYS *
> LLEN rq:queue:orchestrator
```

### 7. JWT Token 驗證失敗

**錯誤訊息**:
```
401 Unauthorized: Invalid token
```

**解決方案**:

```bash
# 確認 JWT_SECRET_KEY 在 Backend 和測試中一致
# 最少 32 字元

# 產生安全的 Secret Key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 更新 .env
JWT_SECRET_KEY=<generated-key>

# 重新啟動 Backend
```

### 8. Pytest 收集測試失敗

**錯誤訊息**:
```
ImportError while importing test module
```

**解決方案**:

```bash
# 確保所有測試目錄有 __init__.py
touch handoff/20250928/40_App/api-backend/tests/__init__.py
touch handoff/20250928/40_App/orchestrator/tests/__init__.py

# 確認 PYTHONPATH 包含專案根目錄
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

---

## 效能優化建議

### 本地開發

1. **使用 SQLite 而非 PostgreSQL** - 本地開發更快，生產環境才用 PostgreSQL
2. **Redis 使用 Docker** - 輕量且隔離，容易清理
3. **前端使用 HMR** - Vite 熱模組替換，修改即時生效
4. **跳過非必要整合** - 本地開發可以不設定 Cloudflare、Vercel 等

### 測試加速

```bash
# 只執行特定測試檔案
pytest tests/test_auth_endpoints.py

# 平行執行測試 (需要 pytest-xdist)
pip install pytest-xdist
pytest -n auto

# 跳過慢速測試
pytest -m "not slow"
```

---

## 進階設定

### 使用 Docker Compose 一鍵啟動

```bash
# 啟動所有服務（後端、Worker、Redis）
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down
```

### 使用 VSCode 除錯

在 `.vscode/launch.json` 中新增配置：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Backend",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/handoff/20250928/40_App/api-backend/src/main.py",
      "console": "integratedTerminal",
      "envFile": "${workspaceFolder}/.env"
    },
    {
      "name": "Python: Worker",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/handoff/20250928/40_App/orchestrator/redis_queue/worker.py",
      "console": "integratedTerminal",
      "envFile": "${workspaceFolder}/.env"
    }
  ]
}
```

---

## 相關文件

- [環境變數完整說明](/docs/config/env_schema.md) - 所有 53 個環境變數的詳細文件
- [CI/CD 工作流矩陣](/docs/ci_matrix.md) - GitHub Actions 工作流說明
- [貢獻規則](/docs/CONTRIBUTING.md) - 分工規則與 PR 流程
- [管理腳本指南](/docs/scripts_overview.md) - 標準化腳本使用方式
- [架構文件](/docs/ARCHITECTURE.md) - 系統架構總覽

---

## 需要協助？

- **GitHub Issues**: https://github.com/RC918/morningai/issues
- **文件首頁**: `/docs/README.md`
- **FAQ**: `/docs/FAQ.md`

---

**Last Updated**: Phase 11 Task 5 (2025-10-13)  
**Maintainer**: Morning AI Engineering Team
