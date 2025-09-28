# Morning AI - 雲資源成本估算

**版本**: 1.0
**日期**: 2025-09-12
**作者**: Manus AI

---

## 1. **概述**

本文件旨在為 Morning AI 項目在 AWS 上的部署提供一個初步的月度成本估算。此估算基於我們在《完整技術資源清單》中推薦的技術棧，並分別對 **Staging** 和 **Production** 環境進行了測算。

**重要提示**: 這是一個**估算值**，實際成本會根據真實的使用量、數據傳輸量和具體配置而波動。我們建議在部署後密切監控 AWS Cost Explorer，並根據實際情況進行持續優化。

## 2. **估算假設**

*   **區域**: 所有資源均部署在 `us-east-1` (N. Virginia) 區域。
*   **運行時間**: 所有服務均按 24/7 運行（約 730 小時/月）。
*   **工作負載**: 估算基於項目初期到中期的中等負載水平。
*   **數據量**: 假設每月數據庫增長 50GB，S3 存儲增長 100GB，數據傳輸流出 1TB。
*   **定價模型**: 優先使用按需定價模型進行估算。對於可預測的穩定負載，未來可考慮購買 Savings Plans 或預留實例以節省成本。

--- 

## 3. **Staging 環境成本估算 (月度)**

Staging 環境旨在用於測試和開發，因此我們選擇較低的配置以控制成本。

| 服務 | 配置 | 數量 | 估算月度成本 (USD) | 備註 |
|---|---|---|---|---|
| **AWS Fargate** | 1 vCPU, 2 GB RAM | 2 (後端+AI Agent) | ~$30 | 按需定價 |
| **AWS RDS for PostgreSQL** | `db.t3.micro` (2 vCPU, 1 GB RAM), 20 GB GP2 | 1 | ~$15 | |
| **AWS ElastiCache for Redis** | `cache.t3.micro` | 1 | ~$13 | |
| **AWS S3** | Standard, 50 GB | 1 | ~$1.15 | |
| **AWS OpenSearch Service** | `t3.small.search` | 1 | ~$25 | 用於日誌聚合 |
| **AWS SQS** | 1M 請求 | 1 | ~$0.40 | 免費套餐額度內 |
| **AWS EventBridge** | 1M 事件 | 1 | ~$1.00 | |
| **AWS SageMaker Endpoint** | `ml.t2.medium` | 1 | ~$55 | 用於模型測試 |
| **數據傳輸** | 100 GB 流出 | - | ~$9 | |
| **其他 (Secrets Manager, etc.)** | - | - | ~$5 | |
| **總計 (Staging)** | | | **~$154.55** | **約 155 美元/月** |

--- 

## 4. **Production 環境成本估算 (月度)**

Production 環境需要更高的可用性和性能，因此配置更高，並包含多可用區 (Multi-AZ) 部署。

| 服務 | 配置 | 數量 | 估算月度成本 (USD) | 備註 |
|---|---|---|---|---|
| **AWS Fargate** | 2 vCPU, 4 GB RAM | 4 (負載均衡+自動擴縮) | ~$240 | 假設平均 2 個實例運行 |
| **AWS RDS for PostgreSQL** | `db.t3.medium` (2 vCPU, 4 GB RAM), 100 GB GP2, Multi-AZ | 1 | ~$130 | 高可用性部署 |
| **AWS ElastiCache for Redis** | `cache.t3.small`, Multi-AZ | 1 | ~$50 | 高可用性部署 |
| **AWS S3** | Standard, 500 GB | 1 | ~$11.50 | |
| **AWS OpenSearch Service** | `m6g.large.search`, Multi-AZ | 2 | ~$250 | 高可用性部署 |
| **AWS Redshift** | `dc2.large` | 2 | ~$365 | 數據倉庫 |
| **AWS Glue** | - | - | ~$50 | 按 ETL 任務運行時間計費 |
| **AWS SQS** | 10M 請求 | 1 | ~$4.00 | |
| **AWS EventBridge** | 10M 事件 | 1 | ~$10.00 | |
| **AWS SageMaker Endpoint** | `ml.m5.large`, Auto Scaling | 2 | ~$200 | 高性能推理 |
| **AWS SES** | 100,000 封郵件 | 1 | ~$10.00 | |
| **Cloudflare** | Pro Plan | 1 | $20 | WAF 和高級功能 |
| **數據傳輸** | 1 TB 流出 | - | ~$90 | |
| **其他 (Secrets Manager, etc.)** | - | - | ~$10 | |
| **總計 (Production)** | | | **~$1450.50** | **約 1,450 美元/月** |

## 5. **總成本預估**

| 環境 | 估算月度成本 (USD) |
|---|---|
| Staging | ~$155 |
| Production | ~$1,450 |
| **總計** | **~$1,605** |

**初步總月度成本約為 1,600 美元。**

--- 

## 6. **成本優化策略**

在系統穩定運行後，我們可以採取以下措施來進一步降低成本：

1.  **購買 Savings Plans**: 對於 Fargate 和 SageMaker 等計算資源，購買 1 年或 3 年的 Savings Plans 可以節省高達 50-70% 的成本。
2.  **預留實例 (Reserved Instances)**: 對於 RDS 和 ElastiCache 等穩定的數據庫負載，購買預留實例可以顯著降低成本。
3.  **S3 智能分層 (Intelligent-Tiering)**: 對於不經常訪問的數據，啟用 S3 智能分層可以自動將其移動到成本更低的存儲層。
4.  **Spot 實例**: 對於可中斷的批處理任務（如部分 ETL 或模型訓練），可以考慮使用 Spot 實例，成本可降低高達 90%。
5.  **精細化自動擴縮 (Fine-grained Auto Scaling)**: 根據負載情況，精細調整 Fargate 和 SageMaker 的自動擴縮策略，避免資源浪費。
6.  **成本異常檢測 (Cost Anomaly Detection)**: 啟用 AWS Cost Anomaly Detection，在成本出現異常增長時及時收到通知。

## 7. **結論**

本估算為 Morning AI 的雲資源預算規劃提供了一個堅實的基礎。我們建議在項目初期預算約為 **每月 2,000 美元**，以應對可能出現的未預期使用量。隨著業務的增長和對系統負載模式的深入了解，我們將能夠更精確地預測成本，並通過實施上述優化策略來持續控制和降低運營開銷。

