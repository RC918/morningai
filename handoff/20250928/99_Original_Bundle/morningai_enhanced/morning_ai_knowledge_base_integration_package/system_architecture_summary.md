# Morning AI 系統架構摘要

## 核心應用棧

*   **容器運行環境**: AWS Fargate
*   **對象存儲**: AWS S3
*   **緩存服務**: AWS ElastiCache for Redis 7
*   **CDN 與網絡安全**: Cloudflare
*   **主數據庫**: AWS RDS for PostgreSQL 16 + pgvector
*   **版本控制與 CI/CD**: GitHub & GitHub Actions

## 可觀測性棧

*   **日誌聚合與管理**: AWS OpenSearch Service 或 Datadog Logs
*   **應用性能監控 (APM)**: Sentry 或 Datadog APM
*   **分佈式追踪**: AWS X-Ray 或 OpenTelemetry + Jaeger
*   **指標與儀表板**: Amazon Managed Service for Prometheus + Grafana

## AI/ML 基礎設施棧

*   **模型服務與推理**: AWS SageMaker Endpoints
*   **AI 工作流編排**: AWS Step Functions
*   **特徵存儲**: AWS SageMaker Feature Store

## 異步通信棧

*   **消息隊列**: AWS SQS (Simple Queue Service)
*   **事件總線**: AWS EventBridge

## 數據智能棧

*   **數據倉庫**: AWS Redshift
*   **ETL/ELT 服務**: AWS Glue
*   **全文搜索引擎**: AWS OpenSearch Service
*   **商業智能 (BI)**: Amazon QuickSight 或 Tableau

## 基礎設施與 DevOps 棧

*   **基礎設施即代碼 (IaC)**: Terraform 或 AWS CDK
*   **密鑰管理**: AWS Secrets Manager
*   **容器鏡像倉庫**: Amazon ECR (Elastic Container Registry)

## 通信棧

*   **郵件服務**: AWS SES (Simple Email Service)
*   **多渠道通知**: AWS SNS (Simple Notification Service)


