# MorningAI 術語對照表 (Terminology Guide)

**版本**: 1.0  
**發布日期**: 2025-10-21  
**用途**: 統一中英文技術術語翻譯，確保文檔、UI、API 的一致性

---

## 使用指南 (Usage Guide)

### 優先級規則
1. **代碼變數/函數**: 一律使用英文
2. **代碼註釋**: 使用中文（團隊溝通效率）
3. **技術文檔**: 英文為主，關鍵概念附中文註解
4. **用戶界面 (UI)**: 繁體中文
5. **API 響應**: 動態語言（支持 i18n）

### 術語選擇原則
- **專有名詞**: 保留英文（如 LangGraph, PostgreSQL, Redis）
- **技術概念**: 使用官方譯名或業界通用譯名
- **產品功能**: 優先使用中文，易於理解
- **避免混用**: 同一文檔中保持術語一致性

---

## 核心技術術語 (Core Technical Terms)

### AI & 機器學習 (AI & Machine Learning)

| 英文 | 繁體中文 | 使用場景 | 範例 |
|------|---------|---------|------|
| Agent | 智能代理 / AI 代理 | UI, 用戶文檔 | "創建新的智能代理" |
| Workflow | 工作流 | 所有文檔 | "工作流執行成功" |
| Task | 任務 | 所有文檔 | "分配 3 個任務給代理" |
| Embedding | 向量嵌入 / 嵌入向量 | 技術文檔 | "生成文本的向量嵌入" |
| Vector | 向量 | 所有文檔 | "向量相似度搜尋" |
| Model | 模型 / 語言模型 | 所有文檔 | "使用 GPT-4 模型" |
| Prompt | 提示詞 / 提示 | 技術文檔, UI | "編輯提示詞模板" |
| Token | 標記 (計費), 令牌 (認證) | 根據上下文 | "消耗 1,500 tokens" / "JWT 令牌" |
| Fine-tuning | 微調 | 技術文檔 | "模型微調訓練" |
| Inference | 推理 / 推論 | 技術文檔 | "模型推理延遲" |
| Training | 訓練 | 技術文檔 | "模型訓練過程" |
| LLM (Large Language Model) | 大型語言模型 / LLM | 技術文檔 | "LLM 成本優化" |
| RAG (Retrieval-Augmented Generation) | 檢索增強生成 / RAG | 技術文檔 | "RAG 管道配置" |

### 資料庫與存儲 (Database & Storage)

| 英文 | 繁體中文 | 使用場景 | 範例 |
|------|---------|---------|------|
| Tenant | 租戶 | 技術文檔 | "多租戶隔離策略" |
| Row-Level Security (RLS) | 行級安全策略 / RLS | 技術文檔 | "啟用 RLS 策略" |
| Migration | 資料庫遷移 / 遷移 | 技術文檔 | "執行資料庫遷移腳本" |
| Index | 索引 | 技術文檔 | "創建資料庫索引" |
| Query | 查詢 | 所有文檔 | "執行資料查詢" |
| Schema | 資料庫模式 / Schema | 技術文檔 | "定義資料庫 schema" |
| Table | 資料表 / 表 | 技術文檔 | "users 資料表" |
| Column | 欄位 / 列 | 技術文檔 | "tenant_id 欄位" |
| Record | 記錄 / 資料列 | 技術文檔 | "插入新記錄" |
| Primary Key | 主鍵 | 技術文檔 | "設定主鍵約束" |
| Foreign Key | 外鍵 | 技術文檔 | "建立外鍵關聯" |
| Materialized View | 物化視圖 | 技術文檔 | "刷新物化視圖" |
| Connection Pool | 連接池 | 技術文檔 | "配置資料庫連接池" |

### 後端架構 (Backend Architecture)

| 英文 | 繁體中文 | 使用場景 | 範例 |
|------|---------|---------|------|
| API | API / 應用程式介面 | 所有文檔 | "調用 API 端點" |
| Endpoint | 端點 / API 端點 | 技術文檔 | "GET /api/vectors 端點" |
| Request | 請求 | 所有文檔 | "發送 HTTP 請求" |
| Response | 響應 / 回應 | 所有文檔 | "API 響應格式" |
| Middleware | 中介軟體 / 中間件 | 技術文檔 | "認證中介軟體" |
| Authentication | 認證 / 身份驗證 | 所有文檔 | "JWT 認證機制" |
| Authorization | 授權 | 所有文檔 | "角色權限授權" |
| Rate Limiting | 限流 / 速率限制 | 技術文檔 | "API 限流策略" |
| Caching | 快取 / 緩存 | 技術文檔 | "Redis 快取層" |
| Load Balancer | 負載平衡器 | 技術文檔 | "配置負載平衡" |
| Microservice | 微服務 | 技術文檔 | "微服務架構設計" |
| Webhook | Webhook / 網絡鉤子 | 技術文檔 | "配置 Webhook 通知" |

### 前端技術 (Frontend)

| 英文 | 繁體中文 | 使用場景 | 範例 |
|------|---------|---------|------|
| Component | 組件 / 元件 | 技術文檔 | "React 組件設計" |
| State | 狀態 | 技術文檔 | "組件狀態管理" |
| Props | 屬性 / Props | 技術文檔 | "傳遞 props 給子組件" |
| Hook | 鉤子 / Hook | 技術文檔 | "使用 useState hook" |
| Routing | 路由 | 技術文檔 | "配置路由規則" |
| Layout | 布局 / 版面 | UI, 技術文檔 | "調整頁面布局" |
| Theme | 主題 / 佈景 | UI | "切換深色主題" |
| Responsive | 響應式 | 技術文檔 | "響應式設計" |
| Widget | 小工具 / Widget | UI | "拖曳儀表板小工具" |
| Dashboard | 儀表板 / 控制台 | UI, 用戶文檔 | "查看監控儀表板" |

### DevOps & 部署 (DevOps & Deployment)

| 英文 | 繁體中文 | 使用場景 | 範例 |
|------|---------|---------|------|
| Deployment | 部署 | 所有文檔 | "生產環境部署" |
| CI/CD | 持續整合/持續部署 / CI/CD | 技術文檔 | "配置 CI/CD 管道" |
| Pipeline | 管道 / 流水線 | 技術文檔 | "建構管道配置" |
| Container | 容器 | 技術文檔 | "Docker 容器化" |
| Orchestration | 編排 | 技術文檔 | "Kubernetes 編排" |
| Environment | 環境 | 技術文檔 | "Staging 環境" |
| Build | 建構 / 構建 | 技術文檔 | "執行專案建構" |
| Release | 發布 / 版本 | 所有文檔 | "v1.0.0 版本發布" |
| Rollback | 回滾 / 還原 | 技術文檔 | "回滾到上一版本" |
| Health Check | 健康檢查 | 技術文檔 | "配置健康檢查端點" |
| Monitoring | 監控 | 所有文檔 | "系統性能監控" |
| Logging | 日誌 / 紀錄 | 技術文檔 | "查看應用日誌" |
| Alert | 告警 / 警報 | 技術文檔, UI | "設定成本告警" |

### 安全性 (Security)

| 英文 | 繁體中文 | 使用場景 | 範例 |
|------|---------|---------|------|
| Encryption | 加密 | 所有文檔 | "資料傳輸加密" |
| Decryption | 解密 | 技術文檔 | "解密敏感資料" |
| Hash | 雜湊 / 哈希 | 技術文檔 | "密碼雜湊算法" |
| Salt | 鹽值 | 技術文檔 | "密碼加鹽處理" |
| SSL/TLS | SSL/TLS | 技術文檔 | "啟用 SSL 加密" |
| Certificate | 憑證 / 證書 | 技術文檔 | "更新 SSL 憑證" |
| Firewall | 防火牆 | 技術文檔 | "配置防火牆規則" |
| Vulnerability | 漏洞 | 技術文檔 | "修復安全漏洞" |
| Audit Log | 審計日誌 | 技術文檔 | "查看審計日誌" |
| Access Control | 存取控制 / 訪問控制 | 技術文檔 | "設定存取控制策略" |

### 性能與優化 (Performance & Optimization)

| 英文 | 繁體中文 | 使用場景 | 範例 |
|------|---------|---------|------|
| Latency | 延遲 | 技術文檔 | "降低 API 延遲" |
| Throughput | 吞吐量 | 技術文檔 | "提升系統吞吐量" |
| Bottleneck | 瓶頸 | 技術文檔 | "識別性能瓶頸" |
| Optimization | 優化 | 所有文檔 | "查詢性能優化" |
| Scalability | 可擴展性 / 擴充性 | 技術文檔 | "水平擴展策略" |
| Performance | 性能 / 效能 | 所有文檔 | "系統性能分析" |
| Benchmark | 基準測試 | 技術文檔 | "執行性能基準測試" |
| Profiling | 效能分析 / 剖析 | 技術文檔 | "CPU 效能分析" |
| Trace | 追蹤 / 軌跡 | 技術文檔 | "分散式追蹤系統" |

---

## 產品功能術語 (Product Features)

### MorningAI 特定功能

| 英文 | 繁體中文 | 使用場景 | 說明 |
|------|---------|---------|------|
| Vector Visualization | 向量視覺化 | UI, 用戶文檔 | pgvector 空間視覺化功能 |
| Memory Drift Detection | 記憶遷移偵測 | UI, 技術文檔 | 檢測向量分佈變化 |
| Trace Drains | 追蹤引流 / Trace Drains | 技術文檔 | Vercel 追蹤數據導出 |
| Cost Analysis | 成本分析 | UI, 用戶文檔 | LLM 成本監控與分析 |
| Hybrid Search | 混合搜尋 | 技術文檔 | 文本 + 向量混合搜尋 |
| Auto-merge | 自動合併 | UI, 技術文檔 | CI 通過後自動合併 PR |
| HITL (Human-in-the-Loop) | 人機協作 / HITL | 技術文檔 | 需要人工審核的流程 |
| Orchestrator | 編排器 / 調度器 | 技術文檔 | LangGraph 工作流編排 |
| Observability | 可觀測性 | 技術文檔 | 系統監控與追蹤能力 |

---

## 狀態與動作 (States & Actions)

### 狀態描述

| 英文 | 繁體中文 | 使用場景 | 範例 |
|------|---------|---------|------|
| Pending | 待處理 / 進行中 | UI, API | "狀態: 待處理" |
| In Progress | 進行中 / 處理中 | UI, API | "任務進行中..." |
| Completed | 已完成 | UI, API | "工作流已完成" |
| Failed | 失敗 | UI, API | "執行失敗" |
| Cancelled | 已取消 | UI, API | "已取消任務" |
| Success | 成功 | UI, API | "操作成功" |
| Error | 錯誤 | UI, API | "發生錯誤" |
| Warning | 警告 | UI, API | "系統警告" |
| Unknown | 未知 | UI, API | "狀態未知" |

### 動作指令

| 英文 | 繁體中文 | 使用場景 | 範例 (UI 按鈕) |
|------|---------|---------|---------------|
| Create | 創建 / 新增 | UI | "創建工作流" |
| Read | 讀取 / 查看 | UI | "查看詳情" |
| Update | 更新 / 編輯 | UI | "編輯設定" |
| Delete | 刪除 | UI | "刪除任務" |
| Submit | 提交 / 送出 | UI | "提交表單" |
| Save | 儲存 / 保存 | UI | "儲存變更" |
| Cancel | 取消 | UI | "取消操作" |
| Refresh | 刷新 / 重新整理 | UI | "刷新頁面" |
| Download | 下載 | UI | "下載報告" |
| Upload | 上傳 | UI | "上傳檔案" |
| Export | 匯出 | UI | "匯出資料" |
| Import | 匯入 | UI | "匯入設定" |
| Deploy | 部署 | UI, 技術文檔 | "部署到生產環境" |
| Execute | 執行 | UI, 技術文檔 | "執行工作流" |
| Retry | 重試 | UI | "重試操作" |

---

## 時間與日期 (Time & Date)

| 英文 | 繁體中文 | 格式範例 |
|------|---------|---------|
| Today | 今天 | "今天" |
| Yesterday | 昨天 | "昨天" |
| Last 7 days | 最近 7 天 | "最近 7 天" |
| Last 30 days | 最近 30 天 | "最近 30 天" |
| This month | 本月 | "本月" |
| Last month | 上個月 | "上個月" |
| Timestamp | 時間戳記 | "2025-10-21T10:30:00Z" |
| Created at | 創建時間 | "創建時間: 2025-10-21 10:30" |
| Updated at | 更新時間 | "更新時間: 2025-10-21 15:45" |
| Expires at | 過期時間 | "過期時間: 2025-11-21" |

---

## 數量與單位 (Quantity & Units)

| 英文 | 繁體中文 | 使用場景 |
|------|---------|---------|
| Count | 數量 / 計數 | "結果數量: 1,247" |
| Total | 總計 / 總數 | "總計: 5,000 tokens" |
| Average | 平均 | "平均延遲: 120ms" |
| Maximum | 最大值 | "最大值: 500ms" |
| Minimum | 最小值 | "最小值: 50ms" |
| Percentage | 百分比 | "完成度: 75%" |
| Duration | 持續時間 / 時長 | "執行時長: 2.5 秒" |
| Size | 大小 / 容量 | "檔案大小: 1.5 MB" |
| Rate | 速率 / 比率 | "錯誤率: 0.1%" |

---

## 常見縮寫 (Common Abbreviations)

| 縮寫 | 完整英文 | 繁體中文 | 使用建議 |
|------|---------|---------|---------|
| API | Application Programming Interface | 應用程式介面 / API | 保留縮寫 |
| CI/CD | Continuous Integration/Continuous Deployment | 持續整合/持續部署 | 保留縮寫 |
| CRUD | Create, Read, Update, Delete | 增查改刪 | 技術文檔可用 |
| DB | Database | 資料庫 | 技術文檔可用 |
| FAQ | Frequently Asked Questions | 常見問題 / FAQ | 保留縮寫 |
| HTTP | Hypertext Transfer Protocol | 超文本傳輸協定 / HTTP | 保留縮寫 |
| JWT | JSON Web Token | JSON Web Token / JWT | 保留縮寫 |
| LLM | Large Language Model | 大型語言模型 / LLM | 保留縮寫 |
| ORM | Object-Relational Mapping | 物件關聯對映 | 技術文檔可用 |
| REST | Representational State Transfer | REST / RESTful API | 保留縮寫 |
| RLS | Row-Level Security | 行級安全策略 / RLS | 保留縮寫 |
| SQL | Structured Query Language | 結構化查詢語言 / SQL | 保留縮寫 |
| UI | User Interface | 用戶界面 / UI | 保留縮寫 |
| UX | User Experience | 用戶體驗 / UX | 保留縮寫 |

---

## 錯誤類型 (Error Types)

| 錯誤代碼 | 英文描述 | 繁體中文 |
|---------|---------|---------|
| 400 | Bad Request | 請求錯誤 |
| 401 | Unauthorized | 未授權 / 認證失敗 |
| 403 | Forbidden | 禁止存取 |
| 404 | Not Found | 找不到資源 |
| 409 | Conflict | 衝突 / 資源已存在 |
| 422 | Unprocessable Entity | 無法處理的實體 |
| 429 | Too Many Requests | 請求過多 / 超過限流 |
| 500 | Internal Server Error | 伺服器內部錯誤 |
| 503 | Service Unavailable | 服務暫時無法使用 |

---

## 使用範例 (Usage Examples)

### 技術文檔範例
```markdown
## Vector Visualization API

向量視覺化 API 提供 pgvector 空間的 2D/3D 視覺化功能。

**Endpoint**: `GET /api/vectors/visualize`

**Parameters**:
- `method` (string): 降維方法 - "tsne" 或 "pca"
- `limit` (integer): 向量數量限制，預設 1000，最大 5000

**Response**:
\`\`\`json
{
  "data": {
    "figure": "plotly_json_string",
    "vector_count": 1247,
    "method": "tsne",
    "dimensions": 2
  },
  "cached": false
}
\`\`\`
```

### UI 文案範例
```tsx
// 按鈕
<Button>創建智能代理</Button>
<Button>開始向量視覺化</Button>
<Button>刷新監控數據</Button>

// 狀態訊息
<Alert type="success">工作流執行成功，共處理 10 個任務</Alert>
<Alert type="error">資料庫連接失敗。請檢查設定後重試。</Alert>
<Alert type="warning">API 成本超過每日限額 ($10)，請確認使用量</Alert>

// 表單標籤
<Label>租戶 ID (Tenant ID)</Label>
<Label>向量相似度閾值</Label>
<Label>最大結果數量</Label>
```

---

## 更新與維護 (Maintenance)

### 新增術語流程
1. 確認術語在官方文檔或業界的標準譯法
2. 檢查是否與現有術語衝突
3. 在本文檔中添加新術語
4. 更新相關技術文檔和 UI 文案
5. 通知開發團隊

### 術語衝突解決
- 優先使用官方譯名
- 參考台灣 Microsoft、Google 等大廠的譯法
- 團隊投票決定（如有爭議）
- 記錄決策理由

---

## 參考資源 (References)

- [Microsoft 語言入口網站](https://www.microsoft.com/zh-tw/language)
- [Google Developers 中文文檔](https://developers.google.com/terms?hl=zh-tw)
- [品牌語調指南](./BRAND_VOICE_GUIDELINES.md)
- [貢獻指南](./CONTRIBUTING.md)

---

## 版本歷史 (Version History)

| 版本 | 日期 | 變更內容 | 作者 |
|------|------|----------|------|
| 1.0 | 2025-10-21 | 初版發布，涵蓋 200+ 核心術語 | MorningAI Team |
