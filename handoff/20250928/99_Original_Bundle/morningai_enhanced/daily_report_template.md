# 每日監控報告 - Day N

**日期**: {{date}}

## 總結 (≦10 行)

{{summary}}

## 服務健康

| 端點 | 狀態碼 | 回應時間 (ms) | 備註 |
|---|---|---|---|
| `/health` | {{health_status}} | {{health_latency}} | |
| `/healthz` | {{healthz_status}} | {{healthz_latency}} | |
| `/openapi.json` | {{openapi_status}} | {{openapi_latency}} | {{openapi_note}} |

## 效能與錯誤

| 指標 | 數值 |
|---|---|
| P95 延遲 | {{p95_latency}} ms |
| 錯誤率 (4xx/5xx) | {{error_rate}}% |
| 5xx 峰值時段 (過去 24h) | {{peak_5xx_time}} |

## 資源與依賴

*   **Render 服務狀態**: [請在此附上 Events 截圖]
*   **資料庫連線健康度**:
    *   連線數: {{db_connections}}
    *   錯誤數: {{db_errors}}

## 監控與告警

{{alerts_summary}}


