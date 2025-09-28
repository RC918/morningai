# 7天觀察期彙整表

## 總覽

本文檔旨在記錄和分析服務在為期七天的觀察期內的各項監控指標，以評估服務的穩定性和性能。

## 每日監控記錄





### Day {{day_number}} - {{date}}

**總結**:
{{summary}}

**詳細指標**:

| 分類 | 指標 | 數值 |
|---|---|---|
| **服務健康** | `/health` 狀態 | {{health_status}} |
| | `/healthz` 狀態 | {{healthz_status}} |
| | `/openapi.json` 狀態 | {{openapi_status}} |
| **效能** | P95 延遲 | {{p95_latency}} ms |
| | 錯誤率 | {{error_rate}}% |
| | 5xx 峰值時段 | {{peak_5xx_time}} |
| **資源** | 資料庫連線數 | {{db_connections}} |
| | 資料庫錯誤數 | {{db_errors}} |
| **告警** | 觸發告警數 | {{alerts_triggered}} |

**截圖證據**:

- Render Events: [截圖連結]
- Grafana/Sentry 儀表板: [截圖連結]
- 其他: [截圖連結]

---


