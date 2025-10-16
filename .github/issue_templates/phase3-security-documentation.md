## 目標

完成 OWASP 安全審計、Secrets 管理、災難恢復計畫，並完善技術文檔和團隊培訓材料。

## 背景

Fly.io 部署已完成（PR #278, #279），基礎安全措施（Docker 隔離、Seccomp、AppArmor）已實施。需要：
- 全面安全審計
- Secrets 管理加固
- 災難恢復演練
- 完整技術文檔

## 工作範圍

### Week 12: 安全加固

#### OWASP 安全審計
- [ ] **A01:2021 – Broken Access Control**
  - 審查 API 端點權限控制
  - 驗證 HITL 審批機制
  - 測試 Agent sandbox 隔離

- [ ] **A02:2021 – Cryptographic Failures**
  - 審查 SECRET_KEY 強度（env_schema.yaml 要求 >32 字元）
  - 驗證 HTTPS 加密（Render + Fly.io 強制 TLS）
  - 檢查敏感資料儲存（Supabase encryption at rest）

- [ ] **A03:2021 – Injection**
  - 審查 Shell_Tool 命令注入風險
  - SQL injection 測試（Supabase RLS）
  - 測試 Git_Tool 參數驗證

- [ ] **A04:2021 – Insecure Design**
  - 審查 Agent OODA 決策邏輯
  - 驗證 Circuit Breaker 設計
  - 測試失敗恢復機制

- [ ] **A05:2021 – Security Misconfiguration**
  - 審查 Dockerfile 安全配置
  - 驗證 seccomp/AppArmor profiles
  - 檢查環境變數管理

- [ ] **A06:2021 – Vulnerable Components**
  - 掃描 Python 依賴漏洞（pip-audit）
  - 掃描 npm 依賴漏洞（npm audit）
  - 更新過時套件

- [ ] **A07:2021 – Authentication Failures**
  - 審查 GitHub Token 管理
  - 驗證 Render/Fly.io API keys 權限
  - 測試 Telegram Bot Token 安全性

- [ ] **A08:2021 – Software and Data Integrity Failures**
  - 驗證 CI/CD pipeline 安全性
  - 審查 PR auto-merge 邏輯
  - 測試 Agent 代碼變更審計

- [ ] **A09:2021 – Security Logging Failures**
  - 審查 Sentry 日誌覆蓋率
  - 驗證 audit_log 完整性
  - 測試安全事件告警

- [ ] **A10:2021 – Server-Side Request Forgery (SSRF)**
  - 測試 Browser_Tool SSRF 風險
  - 審查 Render_Tool API 調用
  - 驗證網路隔離

#### Secrets 管理（Vault 整合）
- [ ] 安裝 HashiCorp Vault（或使用 Render Secrets + Fly.io Secrets）
- [ ] 遷移敏感環境變數到 Vault
- [ ] 實現動態 secrets rotation
- [ ] 設定 secrets 審計日誌
- [ ] 測試 secrets 洩漏檢測（gitleaks）

```bash
# 方案 1: HashiCorp Vault（推薦用於 >50 secrets）
vault kv put secret/morningai/prod \
  OPENAI_API_KEY=${OPENAI_API_KEY} \
  SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}

# 方案 2: Render Secrets + Fly.io Secrets（目前使用，適合 <20 secrets）
# 保持現狀，加強 secrets 審計
```

### Week 13: 文檔與培訓

#### 災難恢復 Runbook
- [ ] **Scenario 1: Fly.io 服務中斷**
  - 檢測方式：Health check 失敗 >5 分鐘
  - 回應步驟：切換到備用 region / 降級到 subprocess 模式
  - 預計恢復時間：<30 分鐘

- [ ] **Scenario 2: Render 後端故障**
  - 檢測方式：API 健康檢查失敗
  - 回應步驟：Redeploy previous stable version
  - 預計恢復時間：<15 分鐘

- [ ] **Scenario 3: Supabase 資料庫故障**
  - 檢測方式：Database connection errors
  - 回應步驟：切換到備份 instance / 聯繫 Supabase 支援
  - 預計恢復時間：<1 小時

- [ ] **Scenario 4: Redis (Upstash) 故障**
  - 檢測方式：Cache miss rate >50%
  - 回應步驟：降級運行（無快取）
  - 預計恢復時間：<5 分鐘

- [ ] **Scenario 5: Agent 決策錯誤導致系統損壞**
  - 檢測方式：CI 失敗 + Production errors spike
  - 回應步驟：Git revert + Redeploy
  - 預計恢復時間：<10 分鐘

#### 技術文檔完善
- [ ] **架構文檔**
  - 更新 Agent Sandbox Architecture（已部分完成）
  - 補充 Session State 架構圖
  - 補充 OODA 整合流程圖

- [ ] **API 文檔**
  - MCP 工具 API 參考
  - Agent Orchestrator API
  - Webhook 整合文檔

- [ ] **運維 Runbook**
  - Fly.io 部署指南
  - 監控告警配置
  - 日常維護檢查清單
  - 常見問題排除

- [ ] **開發者指南**
  - 本地開發環境設定
  - 新增 MCP 工具指南
  - Agent 擴展開發
  - 測試編寫指南

#### 團隊培訓材料
- [ ] **培訓簡報**
  - Agent 架構概覽（30 分鐘）
  - MCP 協議介紹（20 分鐘）
  - OODA 決策流程（20 分鐘）
  - 安全最佳實踐（30 分鐘）

- [ ] **實作演練**
  - 創建新 MCP 工具（1 小時）
  - 設計 Agent workflow（1 小時）
  - 處理 Agent 錯誤（30 分鐘）
  - 執行災難恢復（1 小時）

- [ ] **認證測試**
  - Agent 運維認證（15 題）
  - 安全審計認證（10 題）

## 驗收標準

- [ ] OWASP Top 10 全部審計完成
- [ ] 0 個 Critical security vulnerabilities
- [ ] Secrets 審計日誌啟用
- [ ] 災難恢復演練成功（所有 5 個 scenarios）
- [ ] 技術文檔覆蓋率 100%（所有關鍵系統）
- [ ] 團隊培訓完成率 100%（所有工程師）

## 工具與資源

### 安全掃描工具
```bash
# Python 依賴掃描
pip install pip-audit
pip-audit

# npm 依賴掃描
npm audit

# Secrets 洩漏檢測
pip install gitleaks
gitleaks detect --source . --verbose

# Docker 映像掃描
docker scan morningai-sandbox-dev-agent:latest

# OWASP ZAP（動態掃描）
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t https://morningai-backend-v2.onrender.com
```

## 相關資源

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [Security Hardening Runbook](../docs/sandbox-security-hardening-runbook.md)
- [Disaster Recovery Best Practices](https://fly.io/docs/reference/disaster-recovery/)
- [HashiCorp Vault](https://www.vaultproject.io/)

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|---------|
| 安全漏洞修復引入 Bug | 高 | 每個修復都經過 CI 驗證 |
| Vault 複雜度過高 | 中 | 先用 Render/Fly.io Secrets，未來遷移 |
| 災難恢復演練影響生產 | 高 | 在 staging 環境演練 |
| 培訓時間不足 | 中 | 錄製培訓影片，非同步學習 |

## 估計工時

- Week 12: 40 小時（安全加固）
- Week 13: 40 小時（文檔 + 培訓）
- **總計**: 80 小時

## 負責人

- CTO（安全審計）
- Backend Engineer（Secrets 管理）
- DevOps Engineer（災難恢復）
- Tech Writer（文檔）
- PM（培訓）
