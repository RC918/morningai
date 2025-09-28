# 服務監控與運維實施方案

歡迎使用由 Manus AI 構建的服務監控與運維實施方案。本方案旨在根據您提供的規範，提供一套完整的工具和流程，以確保服務的穩定、高效運行。

---

## 總覽與目錄結構

本方案包含自動化腳本、標準化文檔模板和清晰的操作流程，所有相關文件都組織在當前目錄下。

```
.
├── 7_day_observation_summary.md      # 7 天觀察期彙整表記錄
├── README.md                         # 本指南
├── change_management_process.md      # D. 變更管理流程文檔
├── change_request_template.md        # D. 變更請求模板
├── daily_report_generator.py         # A. 每日報告生成腳本
├── daily_report_template.md          # A. 每日報告基礎模板
├── detailed_daily_report_template.md # A. 每日報告詳細模板
├── health_check.py                   # B. 基礎健康檢查腳本
├── incident_report_template.md       # C. 事故報告模板
├── monitoring_config.py              # B. 監控系統配置文件
├── monitoring_system.py              # B. 自動化監控核心系統
├── runbook_incident_response.md      # C. 異常處置手冊 (Runbook)
├── start_monitoring.sh               # B. 監控系統啟動腳本
└── stop_monitoring.sh                # B. 監控系統停止/狀態檢查腳本
```

---

## A. 每日固定產出 (Daily Operations)

每日的監控報告和日誌記錄是評估服務健康度的核心。

1.  **生成每日報告**:
    *   系統會通過 `monitoring_system.py` 自動收集數據並存儲在 `data/` 目錄下。
    *   您可以手動運行 `daily_report_generator.py` 來生成特定日期的報告。
        ```bash
        python3 daily_report_generator.py --date YYYY-MM-DD
        ```
    *   報告會以 Markdown 和 JSON 格式保存在 `reports/` 目錄下。

2.  **發送到 Slack**:
    *   在 `.env` 文件中配置 `SLACK_WEBHOOK_URL` 後，報告生成器可以自動將簡報發送到指定的 Slack 頻道。
        ```bash
        python3 daily_report_generator.py --slack-webhook "YOUR_WEBHOOK_URL"
        ```

3.  **彙整與存檔**:
    *   將生成的報告（`7天觀察期監控日誌_DayN_....md`）和相關截圖（Render Events 等）整理歸檔。
    *   定期更新 `7_day_observation_summary.md`，以提供一個高級別的概覽。

---

## B. 自動監控 (Automated Monitoring)

核心的自動化監控系統會持續在後台運行，執行每小時的健康檢查並根據預設規則觸發告警。

1.  **配置**:
    *   首次運行前，請複製 `.env.example` 為 `.env`，並填寫您的服務 `MONITOR_BASE_URL` 和 `SLACK_WEBHOOK_URL`。
        ```bash
        cp .env.example .env
        # ...編輯 .env 文件...
        ```

2.  **啟動監控系統**:
    *   執行 `start_monitoring.sh` 腳本，它會在後台啟動監控進程。
        ```bash
        ./start_monitoring.sh
        ```
    *   日誌會輸出到 `logs/monitoring_output.log`。

3.  **檢查狀態與停止**:
    *   使用 `stop_monitoring.sh` 腳本來檢查狀態、停止或重啟監控系統。
        ```bash
        ./stop_monitoring.sh status    # 檢查運行狀態
        ./stop_monitoring.sh stop      # 停止監控
        ./stop_monitoring.sh restart   # 重啟監控
        ```

---

## C. 異常處置 (Incident Response)

當收到「警告」或「嚴重」告警時，請嚴格遵循 **`runbook_incident_response.md`** 中的步驟進行操作。

1.  **界定範圍**: 快速判斷問題影響面。
2.  **快速修復**: 根據場景選擇重啟、回滾或調整 Cloudflare 規則。
3.  **恢復驗證**: 使用 Runbook 中提供的 `curl` 命令集進行驗證。
4.  **事故報告**: 服務恢復後，使用 **`incident_report_template.md`** 模板填寫 5W1H 報告。

---

## D. 變更凍結 (Change Management)

在 7 天觀察期內，所有變更都應被凍結。任何必要的試驗性調整都必須遵循 **`change_management_process.md`** 中定義的流程。

1.  **提交變更單**: 使用 **`change_request_template.md`** 模板創建變更請求。
2.  **審批**: 變更單需要經過審批才能執行。
3.  **執行與驗收**: 在指定的時窗內執行變更，並完成驗收。

---

## 依賴與環境

*   **Python 3.7+**
*   **`requests` 庫**: `pip3 install requests`
*   **Shell 環境**: `bash`

本方案旨在提供一個起點，您可以根據團隊的具體需求和技術棧對其進行擴展和定製。


