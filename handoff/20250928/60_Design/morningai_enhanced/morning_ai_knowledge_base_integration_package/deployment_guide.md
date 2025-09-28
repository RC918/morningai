# Morning AI - 部署指南與基礎設施即代碼 (IaC)

**版本**: 1.0
**日期**: 2025-09-12
**作者**: Manus AI

---

## 1. **概述**

本指南詳細闡述了部署 Morning AI 平台的完整流程，涵蓋了從基礎設施的自動化創建到應用程序的持續集成與持續部署 (CI/CD)。我們採用**基礎設施即代碼 (Infrastructure as Code - IaC)** 的最佳實踐，使用 **Terraform** 來定義和管理所有雲資源，確保部署過程的**自動化、可重複性和版本化**。

本指南旨在為 DevOps 工程師提供一個清晰、可執行的操作手冊，以快速、可靠地搭建和維護 Staging 和 Production 環境。

## 2. **核心理念：GitOps 與不可變基礎設施**

*   **GitOps**: 我們將 Git 倉庫作為管理基礎設施和應用程序配置的唯一真實來源 (Single Source of Truth)。所有的變更都通過 Git 提交和 Pull Request 進行，經審查後自動應用到目標環境。
*   **不可變基礎設施 (Immutable Infrastructure)**: 我們不對現有的基礎設施進行原地修改。任何變更都會創建新的資源（如新的 Fargate 任務定義、新的容器鏡像），然後將流量切換到新資源上。這大大降低了配置漂移和部署失敗的風險。

## 3. **環境策略**

我們定義了兩個核心的長期環境：

*   **Staging 環境**: 用於部署開發分支的最新代碼，進行功能測試、集成測試和 E2E 測試。此環境的數據可以隨時被清除和重置。
*   **Production 環境**: 面向最終用戶的生產環境，具有最高的穩定性和可用性要求。只有經過 Staging 環境充分驗證的代碼才能部署到此環境。

## 4. **部署流程概覽**

部署流程分為兩大階段：

1.  **基礎設施引導 (Infrastructure Bootstrap)**: 一次性或低頻率操作，使用 Terraform 創建所有底層雲資源。
2.  **應用程序 CI/CD**: 高頻率操作，開發人員提交代碼後，由 GitHub Actions 自動觸發，完成應用的構建、測試和部署。

![Deployment Flow](https://i.imgur.com/example.png)  *<-- 佔位符：此處應插入部署流程圖* 

--- 

## 5. **階段一：基礎設施引導 (Terraform)**

我們使用 Terraform 來管理所有 AWS 資源。Terraform 代碼應存放在一個獨立的 Git 倉庫中（例如 `morningai-infrastructure`）。

### **5.1 目錄結構**

```
/morningai-infrastructure
├── environments
│   ├── staging
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── terraform.tfvars
│   └── production
│       ├── main.tf
│       ├── variables.tf
│       └── terraform.tfvars
└── modules
    ├── vpc
    ├── fargate
    ├── rds
    ├── s3
    └── ...
```

*   `modules/`: 存放可重用的基礎設施模塊（如網絡、數據庫、計算等）。
*   `environments/`: 為每個環境（Staging, Production）定義具體的資源實例和配置。

### **5.2 執行步驟**

**前提**: 已安裝 Terraform CLI，並配置好 AWS 訪問憑證。

1.  **初始化 Terraform**:
    ```bash
    cd environments/staging
    terraform init
    ```

2.  **規劃變更**:
    ```bash
    terraform plan -out=staging.plan
    ```
    此步驟會顯示 Terraform 將要創建、修改或刪除的資源，供部署前審查。

3.  **應用變更**:
    ```bash
    terraform apply "staging.plan"
    ```
    此步驟將實際創建 AWS 上的所有資源。這個過程可能需要 10-30 分鐘。

4.  **輸出關鍵信息**: Terraform 執行完畢後，會輸出關鍵的資源信息，如數據庫地址、負載均衡器 DNS 等。這些信息需要被配置到 GitHub Actions 的 Secrets 中，供 CI/CD 流程使用。

### **5.3 Terraform 管理的核心資源**

*   **網絡 (VPC)**: 虛擬私有云、子網、路由表、安全組。
*   **計算 (Fargate)**: ECS 集群、任務定義、服務、負載均衡器。
*   **數據庫 (RDS)**: PostgreSQL 實例、參數組、只讀副本。
*   **緩存 (ElastiCache)**: Redis 實例。
*   **存儲 (S3)**: 用於不同目的的存儲桶（日誌、用戶上傳、靜態網站）。
*   **IAM**: 服務所需的角色和權限策略。
*   **監控與日誌**: CloudWatch Log Groups, OpenSearch 域。
*   **消息隊列**: SQS 隊列和 EventBridge 總線。

--- 

## 6. **階段二：應用程序 CI/CD (GitHub Actions)**

CI/CD 流程在 `.github/workflows/` 目錄下定義。

### **6.1 核心工作流 (Workflow)**

*   `ci.yml`: 在每次提交和 Pull Request 時觸發。執行單元測試、代碼風格檢查和靜態分析。
*   `cd-staging.yml`: 當代碼合併到 `develop` 分支時觸發。執行構建、推送到 ECR、運行集成測試，並最終部署到 Staging 環境。
*   `cd-production.yml`: 當在 `main` 分支上創建一個新的 Git Tag 時觸發。執行與 Staging 類似的流程，但包含手動審批步驟，並最終部署到 Production 環境。

### **6.2 `cd-staging.yml` 流程詳解**

1.  **Checkout Code**: 簽出 `develop` 分支的最新代碼。
2.  **Configure AWS Credentials**: 使用 GitHub Secrets 配置 AWS 訪問憑證。
3.  **Login to Amazon ECR**: 登錄到 AWS 容器鏡像倉庫。
4.  **Build, Tag, and Push Image**: 構建 Docker 鏡像，並使用 Git Commit SHA 作為標籤，推送到 ECR。
5.  **Run Database Migrations**: 運行數據庫遷移腳本（通常是通過一個一次性的 Fargate 任務）。
6.  **Run Integration Tests**: 針對 Staging 環境運行集成測試套件。
7.  **Deploy to Amazon ECS**: 更新 Fargate 服務的任務定義，使其指向新的容器鏡像，觸發滾動更新。
8.  **Post-Deployment Health Check**: 檢查部署後應用的健康檢查端點，確保部署成功。
9.  **Send Notification**: 發送部署狀態通知到 Slack 頻道。

### **6.3 Production 部署的特殊考慮**

*   **手動審批 (Manual Approval)**: 在部署到生產環境前，工作流會暫停，等待指定人員（如 Tech Lead 或 DevOps 負責人）在 GitHub Actions 界面上手動批准，增加一道安全防線。
*   **藍綠部署/金絲雀部署 (Blue/Green or Canary)**: 為了實現零停機和低風險部署，可以引入更高級的部署策略。例如，使用 AWS CodeDeploy 來管理 Fargate 的藍綠部署，先將新版本部署到一個獨立的環境，測試通過後再將流量完全切換過去。

## 7. **成本估算**

請參考獨立的 `cost_estimation.md` 文檔，其中包含了對 Staging 和 Production 環境的詳細月度成本估算和優化建議。

## 8. **結論**

本部署指南為 Morning AI 提供了一個現代化、自動化且高度可靠的部署框架。通過結合 Terraform 的 IaC 能力和 GitHub Actions 的 CI/CD 流程，我們能夠實現快速迭代，同時保證生產環境的穩定性和安全性。這套體係是支撐 Morning AI 成為一個頂級自治 SaaS 平台的堅實工程基礎。

