> **每日監控報告**
> **日期**: {{date}}

### 總體評價: {{overall_status_emoji}} {{overall_status_text}}

{{summary_text}}

---

### 1. 服務健康檢查 (Service Health)

| 端點 (Endpoint) | 狀態 (Status) | 平均延遲 (Avg. Latency) | 成功率 (Success Rate) | 備註 (Notes) |
|---|---|---|---|---|
| `GET /health` | {{health_status_emoji}} {{health_status}} | {{health_latency}}ms | {{health_success_rate}}% | 輕量級檢查 |
| `GET /healthz` | {{healthz_status_emoji}} {{healthz_status}} | {{healthz_latency}}ms | {{healthz_success_rate}}% | 全面健康檢查 |
| `GET /openapi.json` | {{openapi_status_emoji}} {{openapi_status}} | {{openapi_latency}}ms | {{openapi_success_rate}}% | API 規格，需包含 /auth/ & /referral/ |

### 2. 效能與錯誤 (Performance & Errors)

| 指標 (Metric) | 數值 (Value) | 狀態 (Status) | 說明 (Description) |
|---|---|---|---|
| **P95 延遲** | `{{p95_latency}}ms` | {{p95_latency_emoji}} | 95% 的請求應在 500ms 內完成 |
| **錯誤率** | `{{error_rate}}%` | {{error_rate_emoji}} | 4xx/5xx 錯誤比例應低於 1% |
| **5xx 峰值時段** | `{{peak_5xx_time}}` | | 過去 24 小時內 5xx 錯誤最頻繁的時段 |

### 3. 資源與依賴 (Resources & Dependencies)

*   **Render 服務狀態**: {{render_status_emoji}} {{render_status_text}}
    *   *附件: [Render Events 截圖]*
*   **資料庫健康度 (Database Health)**:
    *   連線數 (Connections): `{{db_connections}}`
    *   錯誤數 (Errors): `{{db_errors}}`

### 4. 監控與告警 (Monitoring & Alerts)

{{#if alerts}}
**今日告警摘要 (Today's Alert Summary):**
{{#each alerts}}
*   `[{{level}}]` {{message}} ({{timestamp}})
{{/each}}
{{else}}
✅ **今日無觸發任何告警。**
{{/if}}

*   *附件: [Sentry/UptimeRobot 告警截圖 (若有)]*

---

*報告由 Manus AI 自動生成。*

