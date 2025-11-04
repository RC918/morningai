# PR #318 Breaking Changes 詳細分析

## 🚨 Breaking Change: `/api/agent/faq` 端點需要認證

### 變更詳情

**檔案**: `handoff/20250928/40_App/api-backend/src/routes/agent.py`  
**行號**: 72  
**Commit**: 968bf3e08057c23a1c4b2b2e08e4f4177ca2f17d

**變更前**:
```python
@bp.route("/faq", methods=["POST"])
def create_faq_task():
    """Create FAQ generation task"""
```

**變更後**:
```python
@bp.route("/faq", methods=["POST"])
@jwt_required  # ⚠️ NEW - Breaking Change
def create_faq_task():
    """Create FAQ generation task (Phase 3: tenant-aware)"""
```

---

## 📊 影響範圍評估

### 1. 受影響的客戶端

#### Frontend Dashboard
- **位置**: `handoff/20250928/40_App/frontend-dashboard/`
- **影響**: 所有調用 `/api/agent/faq` 的 React 組件
- **狀態**: ✅ 已修復 (PR 中已包含 TenantContext 和 JWT 處理)

#### 自動化測試
- **位置**: `handoff/20250928/40_App/api-backend/tests/`
- **影響**: 3 個測試檔案
  - `test_faq_methods.py`: 5 個測試
  - `test_agent_task_flow.py`: 2 個測試
  - `test_redis_retry.py`: 3 個測試
- **狀態**: ✅ 已修復 (在本次 commit 63fb14fb 中修復)

#### E2E 測試腳本
- **位置**: 各種測試腳本
- **影響**: 所有直接調用 API 的腳本
- **狀態**: ⚠️ **需要手動檢查和更新**

#### 第三方整合
- **Postman Collections**
- **Curl 範例**
- **CI/CD 健康檢查**
- **狀態**: ⚠️ **需要手動更新**

---

## 🔧 修復指南

### Frontend 修復範例

**Before** (舊代碼 - 會失敗):
```javascript
fetch('/api/agent/faq', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ question: 'What is...?' })
})
```

**After** (新代碼 - 正確):
```javascript
const token = localStorage.getItem('jwt_token');

fetch('/api/agent/faq', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`  // ✅ 新增
  },
  body: JSON.stringify({ question: 'What is...?' })
})
```

### Python 測試修復範例

**Before**:
```python
def test_faq():
    response = client.post('/api/agent/faq', json={
        'question': 'Test question'
    })
    assert response.status_code == 202
```

**After**:
```python
def test_faq():
    token = create_user_token()  # ✅ 創建測試 token
    response = client.post('/api/agent/faq', json={
        'question': 'Test question'
    }, headers={
        'Authorization': f'Bearer {token}'  # ✅ 添加 header
    })
    assert response.status_code == 202
```

### Curl 修復範例

**Before**:
```bash
curl -X POST http://api.morningai.com/api/agent/faq \
  -H "Content-Type: application/json" \
  -d '{"question": "Test"}'
```

**After**:
```bash
# 首先取得 JWT token (透過登入)
TOKEN=$(curl -X POST http://api.morningai.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "***"}' \
  | jq -r '.token')

# 使用 token 調用 API
curl -X POST http://api.morningai.com/api/agent/faq \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \  # ✅ 新增
  -d '{"question": "Test"}'
```

---

## ⚠️ 預期錯誤

### 錯誤 1: 401 Unauthorized

**症狀**:
```json
{
  "error": "Authorization header missing"
}
```

**原因**: 請求未包含 `Authorization` header

**修復**: 添加 `Authorization: Bearer <JWT_TOKEN>` header

### 錯誤 2: 401 Token Expired

**症狀**:
```json
{
  "error": "Token expired"
}
```

**原因**: JWT token 已過期

**修復**: 刷新 token 或重新登入

### 錯誤 3: 401 Invalid Token

**症狀**:
```json
{
  "error": "Invalid token"
}
```

**原因**: Token 格式錯誤或簽名無效

**修復**: 確保使用正確的 JWT_SECRET_KEY 簽發的 token

---

## 📈 監控建議

### 部署後 24 小時監控指標

1. **401 錯誤數量**
   - **預期**: 會增加，因為未更新的客戶端會收到 401
   - **行動**: 識別並更新受影響的客戶端
   - **警報閾值**: 如果 401 錯誤 > 100/小時，需要立即調查

2. **API 成功率**
   - **預期**: 可能會短暫下降
   - **目標**: 在 48 小時內恢復到 > 99.5%
   - **警報閾值**: 如果成功率 < 95%，考慮回滾

3. **用戶登入率**
   - **預期**: 可能會增加（用戶需要重新登入）
   - **行動**: 確保登入流程順暢
   - **警報閾值**: 登入失敗率 > 5%

---

## 🎯 行動計劃

### 部署前 (Pre-Deployment)

- [x] 更新所有後端測試添加 JWT (已完成)
- [ ] 檢查並更新所有 E2E 測試腳本
- [ ] 更新 Postman Collections
- [ ] 更新 API 文檔
- [ ] 準備用戶通知郵件

### 部署中 (During Deployment)

- [ ] 執行資料庫遷移
- [ ] 部署後端
- [ ] 部署前端
- [ ] 執行煙霧測試

### 部署後 (Post-Deployment)

- [ ] 監控錯誤率 (前 24 小時)
- [ ] 收集用戶反饋
- [ ] 識別並修復未更新的客戶端
- [ ] 更新知識庫/FAQ

---

## 💡 遷移策略

### 選項 1: 立即切換 (目前實施)

**優點**:
- 清晰、一次性變更
- 強制所有客戶端更新
- 更好的安全性

**缺點**:
- 可能造成短期中斷
- 需要同步更新所有客戶端

### 選項 2: 漸進式遷移 (未實施)

如果需要更平滑的過渡，可以考慮：

```python
@bp.route("/faq", methods=["POST"])
def create_faq_task():
    """Create FAQ generation task"""
    
    # 嘗試取得 JWT，但不強制
    auth_header = request.headers.get('Authorization')
    if auth_header:
        # 有 token - Phase 3 路徑
        user_id = verify_jwt(auth_header)
        tenant_id = fetch_user_tenant_id(user_id)
    else:
        # 無 token - Phase 2 後向兼容
        logger.warning("FAQ request without JWT - using default tenant")
        tenant_id = "00000000-0000-0000-0000-000000000001"
    
    # ... 繼續處理
```

**注意**: 此選項未在當前 PR 中實施，但可作為緊急回滾方案。

---

## 📞 聯絡資訊

如遇問題，請聯繫：

- **技術問題**: [建立 GitHub Issue](https://github.com/RC918/morningai/issues)
- **緊急問題**: Slack #engineering-alerts

---

## 📚 相關文檔

- PR #318: https://github.com/RC918/morningai/pull/318
- Migration 005: `migrations/005_create_user_profiles_table.sql`
- Migration 006: `migrations/006_update_rls_policies_true_tenant_isolation.sql`
- 測試修復 Commit: 63fb14fbdab558ac8d062690389336f41beb839d

---

Generated: 2025-10-18  
Author: Devin AI  
Status: ✅ Ready for Review
