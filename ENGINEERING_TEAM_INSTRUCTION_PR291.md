# 🔧 工程團隊指令 - PR #291 更新

**日期**: 2025-10-17  
**CTO**: Ryan Chen  
**任務**: 解決 PR #291 與 main 分支的衝突

---

## 📊 當前狀態

### ✅ 已完成
- PR #295 已合併到 main：修復了 `psycopg2.pool` import 和 OpenAI API 客戶端初始化
- PR #294 已合併到 main：修復了 Supabase Security Advisor 的 RLS 建議
- PR #292 已合併到 main：Week 5 Knowledge Graph 基礎功能

### ⚠️ 待處理
- **PR #291** 需要更新以解決與 main 的衝突

---

## 🎯 工程團隊任務

### 任務：更新 PR #291 以合併最新的 main 分支

PR #291 (`devin/1760637285-phase1-week5-6-bug-fix-pilot`) 目前基於舊版 main，需要合併最新的修復。

---

## 📝 詳細步驟

### Step 1: Checkout PR #291 分支
```bash
cd ~/repos/morningai
git fetch origin devin/1760637285-phase1-week5-6-bug-fix-pilot
git checkout devin/1760637285-phase1-week5-6-bug-fix-pilot
```

### Step 2: 合併最新的 main
```bash
git fetch origin main
git merge origin/main
```

### Step 3: 解決衝突（如果有）

**預期衝突檔案**:
- `agents/dev_agent/knowledge_graph/knowledge_graph_manager.py`

**解決方式**:
1. 打開衝突檔案
2. **保留 main 分支的修復**（來自 PR #295）：
   - ✅ `from psycopg2 import pool` (正確的 import)
   - ✅ `from openai import OpenAI` (新版 API)
   - ✅ `self.openai_client = OpenAI(api_key=...)` (客戶端初始化)

3. 解決衝突後：
```bash
git add agents/dev_agent/knowledge_graph/knowledge_graph_manager.py
git commit -m "Merge main: adopt psycopg2 and OpenAI API fixes from PR #295"
```

### Step 4: 推送更新
```bash
git push origin devin/1760637285-phase1-week5-6-bug-fix-pilot
```

### Step 5: 驗證 CI
等待 GitHub Actions CI 完成（應該會自動觸發）

---

## ⚠️ 重要注意事項

### 關於 Supabase Security Advisor 的警告

Ryan 提到的 Supabase 截圖顯示的 **RLS (Row Level Security)** 建議：
- ✅ **已由 PR #294 修復**
- 這些只是建議，不影響功能運作
- 合併 main 後會自動包含修復

### 關於連接超時問題

```
Failed to initialize connection pool: connection to server at "qevmlbsunnwgrsdibdoi.supabase.co" port 5432 failed: Operation timed out
```

- ⚠️ 這是**網路環境問題**，不是程式碼錯誤
- 在本地環境（macOS）無法連接 Supabase port 5432
- **不需要修復程式碼**
- 建議：在伺服器環境或配置防火牆後測試

---

## ✅ 驗收標準

PR #291 更新後應滿足：

1. ✅ 成功合併 main 分支
2. ✅ 所有 CI 檢查通過 (12/12)
3. ✅ 包含 PR #295 的修復
4. ✅ 包含 PR #294 的安全修復
5. ✅ 沒有 merge conflict

---

## 📌 下一步（CTO 審查後）

PR #291 更新並通過 CI 後：
1. CTO (Ryan) 進行最終驗收
2. 合併 PR #291 到 main
3. Week 5-6 完成 🎉

---

## 🔗 參考連結

- **PR #291**: https://github.com/RC918/morningai/pull/291
- **PR #295** (已合併): https://github.com/RC918/morningai/pull/295
- **PR #294** (已合併): https://github.com/RC918/morningai/pull/294
- **PR #292** (已合併): https://github.com/RC918/morningai/pull/292

---

**指令來源**: Ryan Chen (CTO)  
**執行團隊**: 工程團隊  
**截止時間**: 盡快（Week 5 收尾）
