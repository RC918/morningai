# Database Migrations Guide

本文檔是 MorningAI 資料庫遷移的權威指南，涵蓋 Alembic 工作流程、最佳實踐和故障排除。

## 📋 目錄

- [概述](#概述)
- [工具與配置](#工具與配置)
- [工作流程](#工作流程)
- [Enum 值政策](#enum-值政策)
- [DATABASE_URL 配置](#database_url-配置)
- [CI/CD 整合](#cicd-整合)
- [故障排除](#故障排除)
- [最佳實踐](#最佳實踐)

---

## 概述

MorningAI 使用 **Alembic 1.13.1** 作為資料庫遷移框架，支援版本化的 schema 管理。

### 關鍵資訊

- **工具**: Alembic 1.13.1
- **ORM**: SQLAlchemy (Flask-SQLAlchemy)
- **Baseline Migration**: `91b9a61fcafa` (Initial baseline migration)
- **Metadata 來源**: `src/models/user.py` 中的 `db.metadata`
- **開發環境**: SQLite (絕對路徑)
- **生產環境**: PostgreSQL (Supabase)

### 目錄結構

```
handoff/20250928/40_App/api-backend/
├── alembic/
│   ├── versions/
│   │   └── 91b9a61fcafa_initial_baseline_migration.py
│   ├── env.py          # Alembic 環境配置
│   ├── script.py.mako  # Migration 模板
│   └── README
├── alembic.ini         # Alembic 配置文件
├── scripts/
│   ├── run_alembic_migrations.sh           # Migration 輔助腳本
│   └── test_migration_data_insertion.py    # 整合測試
└── src/
    └── models/
        ├── user.py                 # db.metadata 定義
        └── agent_registry_db.py    # Enum 模型定義
```

---

## 工具與配置

### Alembic 配置 (`alembic.ini`)

```ini
[alembic]
script_location = alembic
sqlalchemy.url = ${DATABASE_URL}  # 從環境變數讀取
```

### 環境配置 (`alembic/env.py`)

```python
# 匯入所有模型以確保 metadata 完整
from src.models.user import db
from src.models.agent_registry_db import AgentDB, TaskDB

# 設置 target_metadata
target_metadata = db.metadata
```

**重要**: 所有新模型必須在 `env.py` 中匯入，否則 autogenerate 會忽略它們。

---

## 工作流程

### 1. 創建新 Migration

```bash
cd handoff/20250928/40_App/api-backend

# 設置 DATABASE_URL (SQLite 開發環境)
export DATABASE_URL="sqlite:////absolute/path/to/dev.db"

# 自動生成 migration
alembic revision --autogenerate -m "Add new table or column"
```

### 2. 檢查生成的 Migration

```bash
# 查看最新 migration 文件
ls -lt alembic/versions/ | head -5

# 編輯 migration 文件
vim alembic/versions/<revision_id>_<message>.py
```

**必須手動檢查**:
- ✅ `upgrade()` 邏輯正確
- ✅ `downgrade()` 邏輯正確（可回滾）
- ✅ Enum 值使用**小寫**（見下方 Enum 政策）
- ✅ 外鍵約束正確
- ✅ 索引定義合理

### 3. 本地測試 Migration

```bash
# Upgrade
alembic upgrade head

# 測試 downgrade
alembic downgrade -1

# 重新 upgrade
alembic upgrade head
```

### 4. 測試資料插入

```bash
# 執行整合測試
python scripts/test_migration_data_insertion.py
```

此測試驗證:
- ✅ 資料可以使用模型 enum 成功插入
- ✅ Enum 值在資料庫中正確儲存為小寫
- ✅ 外鍵約束正常工作

### 5. 提交 PR

```bash
git add alembic/versions/<new_migration>.py
git commit -m "feat: add migration for <feature>"
git push origin <branch>
```

CI 會自動執行:
- ✅ PostgreSQL migration 測試
- ✅ SQLite migration 測試
- ✅ 資料插入整合測試

---

## Enum 值政策

### 🔴 關鍵規則：Enum 值必須小寫

**問題**: SQLAlchemy 預設會將 enum **名稱**（大寫）而非 enum **值**（小寫）寫入資料庫，導致 PostgreSQL 拒絕資料插入。

**解決方案**: 遵循以下政策

### Python 模型定義

```python
# src/models/agent_registry_db.py

from enum import Enum
from src.models.user import db

class AgentTypeDB(str, Enum):
    """Database enum for agent types"""
    DEV_AGENT = "dev_agent"        # ✅ 值為小寫
    OPS_AGENT = "ops_agent"
    PM_AGENT = "pm_agent"
    GROWTH_STRATEGIST = "growth_strategist"
    META_AGENT = "meta_agent"

class AgentDB(db.Model):
    __tablename__ = 'agents'
    
    # ✅ 使用 values_callable 確保寫入 enum 值而非名稱
    agent_type = db.Column(
        db.Enum(
            AgentTypeDB,
            values_callable=lambda e: [i.value for i in e],  # ✅ 關鍵參數
            name='agenttypedb'  # ✅ 指定 PostgreSQL enum 類型名稱
        ),
        nullable=False
    )
```

### Migration 定義

```python
# alembic/versions/<revision>_*.py

def upgrade():
    op.create_table(
        'agents',
        sa.Column(
            'agent_type',
            # ✅ 使用小寫 enum 值
            sa.Enum('dev_agent', 'ops_agent', 'pm_agent', 'growth_strategist', 'meta_agent',
                    name='agenttypedb'),  # ✅ 類型名稱與模型一致
            nullable=False
        ),
        # ...
    )
```

### Enum 類型名稱對照表

| Python Enum 類別 | PostgreSQL 類型名稱 | 值範例 |
|-----------------|-------------------|-------|
| `AgentTypeDB` | `agenttypedb` | `'dev_agent'`, `'ops_agent'` |
| `AgentStatusDB` | `agentstatusdb` | `'active'`, `'idle'`, `'busy'` |
| `PermissionLevelDB` | `permissionleveldb` | `'sandbox_only'`, `'staging_access'` |
| `TaskStatusDB` | `taskstatusdb` | `'queued'`, `'assigned'`, `'running'` |

### 驗證 Enum 值

```python
# 在 Python 中驗證
from src.models.agent_registry_db import AgentTypeDB

print(AgentTypeDB.DEV_AGENT.value)  # 應輸出: 'dev_agent'
```

```sql
-- 在 PostgreSQL 中驗證
SELECT enumlabel FROM pg_enum 
WHERE enumtypid = 'agenttypedb'::regtype;

-- 應返回: dev_agent, ops_agent, pm_agent, growth_strategist, meta_agent
```

---

## DATABASE_URL 配置

### 開發環境 (SQLite)

**⚠️ 重要**: 使用**絕對路徑**避免 "no such table" 錯誤

```bash
# ❌ 錯誤 - 相對路徑會導致不同進程使用不同資料庫文件
export DATABASE_URL="sqlite:///dev.db"

# ✅ 正確 - 絕對路徑確保所有進程使用同一資料庫
export DATABASE_URL="sqlite:////home/ubuntu/repos/morningai/handoff/20250928/40_App/api-backend/dev.db"
```

### 生產環境 (PostgreSQL)

```bash
# Supabase PostgreSQL
export DATABASE_URL="postgresql://user:password@host:5432/database"
```

### 在 alembic.ini 中使用環境變數

```ini
[alembic]
sqlalchemy.url = ${DATABASE_URL}
```

Alembic 會自動從環境變數讀取 `DATABASE_URL`。

---

## CI/CD 整合

### GitHub Actions Workflow

`.github/workflows/alembic-check.yml` 在每次 PR 時執行:

```yaml
jobs:
  validate-migrations:
    steps:
      # 1. PostgreSQL 測試
      - name: Run migrations (PostgreSQL)
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_db
        run: alembic upgrade head
      
      # 2. 資料插入測試
      - name: Test data insertion
        run: python scripts/test_migration_data_insertion.py
      
      # 3. Downgrade 測試
      - name: Test downgrade
        run: alembic downgrade -1
      
      # 4. SQLite 測試
      - name: Run migrations (SQLite)
        env:
          DATABASE_URL: sqlite:////tmp/test.db
        run: alembic upgrade head
```

### CI 檢查項目

- ✅ Migration 可以在 PostgreSQL 上執行
- ✅ Migration 可以在 SQLite 上執行
- ✅ 資料可以使用模型 enum 成功插入
- ✅ Downgrade 可以正常回滾
- ✅ Enum 值在資料庫中正確儲存為小寫

---

## 故障排除

### 問題 1: "no such table" 錯誤

**症狀**:
```
sqlite3.OperationalError: no such table: agents
```

**原因**: SQLite 使用相對路徑時，不同進程可能使用不同的資料庫文件。

**解決方案**:
```bash
# 使用絕對路徑
export DATABASE_URL="sqlite:////absolute/path/to/dev.db"
```

### 問題 2: Enum 值不匹配錯誤

**症狀**:
```
psycopg2.errors.InvalidTextRepresentation: invalid input value for enum agenttypedb: "DEV_AGENT"
```

**原因**: SQLAlchemy 寫入 enum 名稱（大寫）而非 enum 值（小寫）。

**解決方案**:
1. 在模型中添加 `values_callable` 參數:
   ```python
   agent_type = db.Column(
       db.Enum(AgentTypeDB, values_callable=lambda e: [i.value for i in e], name='agenttypedb'),
       nullable=False
   )
   ```

2. 確保 migration 使用小寫 enum 值:
   ```python
   sa.Enum('dev_agent', 'ops_agent', ..., name='agenttypedb')
   ```

### 問題 3: Migration 未檢測到模型變更

**原因**: 模型未在 `alembic/env.py` 中匯入。

**解決方案**:
```python
# alembic/env.py
from src.models.user import db
from src.models.agent_registry_db import AgentDB, TaskDB
from src.models.new_model import NewModel  # ✅ 添加新模型匯入
```

### 問題 4: PostgreSQL enum 類型衝突

**症狀**:
```
psycopg2.errors.DuplicateObject: type "agenttypedb" already exists
```

**原因**: PostgreSQL enum 類型已存在但定義不同。

**解決方案**:
```sql
-- 手動刪除舊 enum 類型（謹慎操作）
DROP TYPE IF EXISTS agenttypedb CASCADE;
```

或在 migration 中處理:
```python
def upgrade():
    # 檢查 enum 類型是否存在
    conn = op.get_bind()
    result = conn.execute(text("SELECT 1 FROM pg_type WHERE typname = 'agenttypedb'"))
    if not result.fetchone():
        # 創建 enum 類型
        op.execute("CREATE TYPE agenttypedb AS ENUM ('dev_agent', 'ops_agent', ...)")
```

---

## 最佳實踐

### 1. Migration 命名

```bash
# ✅ 好的命名
alembic revision --autogenerate -m "add user email verification"
alembic revision --autogenerate -m "add agent reputation score index"

# ❌ 不好的命名
alembic revision --autogenerate -m "update"
alembic revision --autogenerate -m "fix"
```

### 2. 總是測試 Downgrade

```bash
# 測試 downgrade 是否正常工作
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

### 3. 避免編輯已部署的 Migration

**規則**: 一旦 migration 已部署到生產環境，**不要編輯**它。

**原因**: Alembic 使用 revision ID 追蹤已執行的 migration。編輯已部署的 migration 會導致不一致。

**正確做法**: 創建新的 migration 來修正問題。

### 4. 使用 Batch Operations (SQLite)

SQLite 不支援某些 ALTER TABLE 操作。使用 batch mode:

```python
def upgrade():
    with op.batch_alter_table('agents') as batch_op:
        batch_op.add_column(sa.Column('new_field', sa.String(50)))
```

### 5. 添加索引以提升性能

```python
def upgrade():
    op.create_index('idx_tasks_agent_id', 'tasks', ['agent_id'])
    op.create_index('idx_tasks_status', 'tasks', ['status'])
    op.create_index('idx_tasks_created_at', 'tasks', ['created_at'])
```

### 6. 明確指定外鍵行為

```python
def upgrade():
    op.create_foreign_key(
        'fk_tasks_agent_id',
        'tasks', 'agents',
        ['agent_id'], ['agent_id'],
        ondelete='CASCADE'  # ✅ 明確指定刪除行為
    )
```

### 7. 使用 Transaction 確保原子性

```python
def upgrade():
    # Alembic 預設使用 transaction，但可以明確控制
    with op.get_context().autocommit_block():
        # 不使用 transaction 的操作（如 CREATE INDEX CONCURRENTLY）
        pass
```

---

## 相關資源

- **Alembic 官方文檔**: https://alembic.sqlalchemy.org/
- **SQLAlchemy Enum 文檔**: https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.Enum
- **PR #1107**: https://github.com/RC918/morningai/pull/1107 (Alembic 實作)
- **Onboarding Guide**: [docs/ONBOARDING_GUIDE.md](../ONBOARDING_GUIDE.md)
- **輔助腳本**: `scripts/run_alembic_migrations.sh`
- **整合測試**: `scripts/test_migration_data_insertion.py`

---

## 支援

如有問題或需要協助，請:
1. 查看本文檔的故障排除章節
2. 檢查 CI 日誌 (`.github/workflows/alembic-check.yml`)
3. 查看 PR #1107 的討論和 CTO 審查意見
4. 在 GitHub Issues 中提問並標記 `database` 標籤

---

**文檔版本**: 1.0  
**最後更新**: 2025-11-04  
**維護者**: Backend Team
