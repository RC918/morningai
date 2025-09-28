> **服務異常處置手冊 (Incident Response Runbook)**

本手冊旨在提供一套標準化的異常處置流程，確保在服務發生問題時，能快速、有效地進行應對，並將影響降到最低。

---

### **第一步：告警觸發與初步評估**

當監控系統（Sentry, UptimeRobot, 或內部腳本）發出「警告」或「嚴重」級別的告警時，值班人員應立即啟動此流程。

1.  **確認告警**：在 Slack `#morningai-alerts` 頻道確認告警信息。
2.  **建立溝通頻道**：建立臨時的 Slack 頻道（如 `#incident-YYYYMMDD-description`）用於集中溝通。
3.  **初步評估**：在 5 分鐘內完成初步評估，判斷告警的緊急性和可能影響範圍。

---

### **第二步：界定問題範圍 (Scoping)**

此步驟的目標是快速判斷問題的影響範圍，是全域性問題還是局部問題。

| 檢查項目 | 操作指令 / 方法 | 預期結果 | 分析 | 
|---|---|---|---|
| **1. 影響範圍** | 檢查告警是來自單一端點 (e.g., `/referral/stats`) 還是多個端點。 | 確認問題是單點故障還是系統性問題。 | 如果是單點問題，優先檢查相關服務的日誌。如果是系統性問題，則可能是基礎設施層面的問題。 |
| **2. Cloudflare vs. Render** | `curl --resolve api.morningai.me:443:<RENDER_IP> https://api.morningai.me/health` | 將直連 Render 的結果與通過 Cloudflare 的結果 (`curl https://api.morningai.me/health`) 進行比對。 | - **兩者都失敗**：問題很可能在 Render 服務本身。
- **直連成功，CF 失敗**：問題可能出在 Cloudflare 的配置上（如 WAF 規則、路由）。 |
| **3. 檢查日誌** | 登入 Render 查看服務的實時日誌。 | 尋找 `ERROR` 或 `CRITICAL` 級別的日誌，特別是堆疊追蹤 (Stack Trace)。 | 日誌是定位問題根源的最直接證據。 |

---

### **第三步：快速修復 (Quick Fix)**

根據第二步的判斷，採取以下最合適的快速修復措施。**目標是在 15 分鐘內恢復服務**。

#### **場景 A：問題在 Render 服務**

1.  **重啟服務 (Restart Service)**
    *   **操作**：在 Render Dashboard 找到對應服務，點擊 "Manual Deploy" -> "Restart service"。
    *   **注意事項**：此操作不會改變程式碼或配置，僅是重啟進程。適用於解決內存洩漏、連線池耗盡等臨時性問題。

2.  **回滾部署 (Rollback Deployment)**
    *   **操作**：在 Render Dashboard 的 "Events" 標籤頁，找到上一個成功的 "Live" commit，點擊 "Rollback to this commit"。
    *   **注意事項**：這是處理因新程式碼引入 Bug 的最快方法。**回滾前務必確認該版本是穩定的**。

#### **場景 B：問題在 Cloudflare**

1.  **暫停 Worker / WAF 規則 (Pause Rules)**
    *   **操作**：登入 Cloudflare Dashboard，找到可能誤攔流量的 Worker 路由或 WAF 規則（特別是針對 `/auth/*` 或 `/referral/*` 的）。
    *   **動作**：暫時禁用 (Disable) 該規則，並在操作日誌中**詳細備註原因和時間**。
    *   **風險**：暫停安全規則可能會暴露服務於潛在威脅之下，恢復後應立即重新評估並啟用。

---

### **第四步：恢復後驗證 (Post-Recovery Validation)**

在執行快速修復後，必須進行驗證以確保服務已完全恢復正常。

1.  **執行健康檢查腳本**：運行以下五條 `curl` 命令，必須一次性全部通過。

    ```bash
    # 1. 輕量健康檢查
    curl -I https://api.morningai.me/health

    # 2. 全面健康檢查
    curl -I https://api.morningai.me/healthz

    # 3. API 規格檢查
    curl -I https://api.morningai.me/openapi.json

    # 4. 核心功能 (註冊 Dry-run)
    curl -X POST -H "Content-Type: application/json" -d '{}' https://api.morningai.me/auth/register

    # 5. 需認證的核心功能 (替換為有效 Token)
    curl -H "Authorization: Bearer <VALID_TOKEN>" https://api.morningai.me/referral/stats
    ```

2.  **持續監控**：在接下來的 30 分鐘內，密切關注監控儀表板，確保錯誤率和延遲恢復到正常水平。

---

### **第五步：事故報告 (Incident Report)**

服務恢復後，必須在 **1 小時內** 補交一份簡要的「事故 5W1H 報告」。

*   **目標**：不是為了追究責任，而是為了記錄、學習和改進。
*   **模板**：參考 `incident_report_template.md`。
*   **提交**：將報告發送到 Slack `#morningai-alerts` 頻道，並存檔到知識庫。


