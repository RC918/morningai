# Morning AI - 核心技術知識庫

## 1. 系統架構

- **名稱**: Morning AI 系統架構
- **內容**: 採用前後端分離的微服務架構。前端使用 Next.js 14 + TypeScript，部署於 Vercel；後端使用 FastAPI + Python 3.11，部署於 AWS Fargate。資料庫採用 PostgreSQL 16 + pgvector，部署於 AWS RDS；快取使用 Redis 7，部署於 AWS ElastiCache。CDN 使用 Cloudflare 進行全球加速。
- **使用時機**: 進行系統開發、部署或維護時。

## 2. 部署流程

- **名稱**: Morning AI 部署流程
- **內容**: 採用三環境部署策略：開發 (Dev)、預備 (Staging)、生產 (Production)。CI/CD 流程基於 GitHub Actions，實現自動化測試和部署。基礎設施採用 Terraform 進行程式碼管理 (IaC)。
- **使用時機**: 進行新功能部署或環境變更時。

## 3. 監控與告警

- **名稱**: Morning AI 監控與告警系統
- **內容**: 使用 Prometheus 進行指標收集，Grafana 進行視覺化展示，Sentry 進行錯誤追蹤。告警通過 Slack 通知，實現即時響應。
- **使用時機**: 進行系統監控、故障排查或性能優化時。

## 4. AI Agent 生態系統

- **名稱**: Morning AI Agent 團隊架構
- **內容**: 由 15 個精銳 AI Agent 組成，涵蓋決策、產品、開發、測試、設計、運維、安全、客服、行銷、分析、合規等多個領域。Meta-Agent 作為決策中樞，協調所有 Agent 的工作。
- **使用時機**: 進行系統自主管理、決策制定或任務編排時。

## 5. Meta-Agent 決策中樞

- **名稱**: Meta-Agent 運作機制
- **內容**: 基於 OODA 循環 (Observe, Orient, Decide, Act) 進行決策。通過多源數據融合、態勢分析、策略生成、模擬驗證和任務編排，實現系統的自主管理和主動優化。
- **使用時機**: 進行系統自治、性能優化、安全響應或業務增長決策時。


