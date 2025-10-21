# MorningAI 品牌語調指南 (Brand Voice Guidelines)

**版本**: 1.0  
**發布日期**: 2025-10-21  
**適用範圍**: 產品文案、技術文檔、用戶界面、行銷內容

---

## 核心品牌調性 (Core Brand Voice)

MorningAI 的品牌語調體現以下三個核心原則：

### 1. 專業但親切 (Professional yet Approachable)
- **技術準確**: 使用精確的技術術語，展現專業度
- **平易近人**: 避免過度艱澀的表達，讓非技術用戶也能理解
- **範例**:
  - ✅ 推薦: "工作流執行成功，已生成 5 個智能任務"
  - ❌ 避免: "Workflow invocation succeeded, 5 agentic tasks instantiated"
  - ❌ 避免: "你的工作流跑完啦～產生了 5 個小任務喔！😊"

### 2. 高效簡潔 (Efficient and Concise)
- **直接明確**: 一句話說清楚，避免冗詞贅字
- **動作導向**: 告訴用戶該做什麼，而非長篇解釋
- **範例**:
  - ✅ 推薦: "請輸入 API 金鑰以啟用功能"
  - ❌ 避免: "為了確保您能夠順利使用這個功能，我們需要您提供一個有效的 API 金鑰，這個金鑰將會被安全地存儲"

### 3. 創新前瞻 (Innovative and Forward-thinking)
- **展現技術領先性**: 突出 AI、自動化、智能決策等特色
- **解決問題**: 強調如何幫助用戶達成目標
- **範例**:
  - ✅ 推薦: "AI 代理自動識別並修復了 3 個潛在問題"
  - ❌ 避免: "系統已處理完成"

---

## 語感節奏表 (Voice Rhythm Guide)

### 技術文檔 (Developer Documentation)

**目標受眾**: 開發者、工程師、技術決策者

**語言策略**:
- **主要語言**: 英文
- **補充說明**: 中文註解（關鍵概念）
- **語氣**: 正式、精確、技術導向
- **句式**: 簡短陳述句、列表、代碼示例

**範例**:
```markdown
## Authentication

All API requests require a valid JWT token in the `Authorization` header.

使用 Bearer token 進行認證：

\`\`\`http
GET /api/vectors/visualize
Authorization: Bearer YOUR_JWT_TOKEN
\`\`\`

**Response**: Returns a Plotly JSON figure with vector embeddings.
```

**關鍵原則**:
- ✅ 使用主動語態: "The API returns..." 而非 "The response is returned by..."
- ✅ 提供具體示例: 代碼片段、請求/響應格式
- ✅ 避免模糊詞彙: "可能"、"大概"、"也許"
- ✅ 使用標準術語: 參考 `TERMINOLOGY.md`

---

### 用戶界面 (User Interface)

**目標受眾**: 終端用戶、產品經理、業務人員

**語言策略**:
- **主要語言**: 繁體中文
- **補充說明**: 英文專有名詞（保持一致性）
- **語氣**: 友好、清晰、指導性
- **句式**: 完整句子、動詞開頭的指令

**範例**:
```tsx
// 按鈕文案
<Button>創建新工作流</Button>
<Button>開始分析</Button>

// 狀態訊息
<Alert>向量視覺化已生成，共 1,247 個向量</Alert>
<Error>無法連接資料庫，請稍後再試</Error>

// 輸入提示
<Input placeholder="輸入查詢關鍵字..." />
<Select>
  <Option>最近 7 天</Option>
  <Option>最近 30 天</Option>
</Select>
```

**關鍵原則**:
- ✅ 使用動詞開頭: "創建"、"編輯"、"刪除" 而非 "新增項目"
- ✅ 提供明確狀態: "處理中..."、"已完成"、"失敗"
- ✅ 避免技術術語: 用 "智能代理" 而非 "LangGraph Agent"
- ✅ 使用完整句子: "查詢成功" 而非 "Success"

---

### API 響應訊息 (API Response Messages)

**目標受眾**: 開發者（通過 API）、前端應用

**語言策略**:
- **主要語言**: 動態切換（根據 `Accept-Language` header）
- **預設語言**: 繁體中文（zh-TW）
- **備選語言**: 英文（en-US）
- **語氣**: 清晰、簡潔、可操作

**範例**:
```json
// 成功響應 (zh-TW)
{
  "data": {
    "vectors": [...],
    "count": 1247
  },
  "message": "查詢成功",
  "cached": false
}

// 錯誤響應 (zh-TW)
{
  "error": {
    "code": "invalid_parameters",
    "message": "參數 'limit' 必須在 1-5000 之間",
    "field": "limit"
  }
}

// 成功響應 (en-US)
{
  "data": {
    "vectors": [...],
    "count": 1247
  },
  "message": "Query successful",
  "cached": false
}

// 錯誤響應 (en-US)
{
  "error": {
    "code": "invalid_parameters",
    "message": "Parameter 'limit' must be between 1-5000",
    "field": "limit"
  }
}
```

**關鍵原則**:
- ✅ 提供錯誤代碼: 標準化的 `error.code`
- ✅ 清晰的錯誤訊息: 說明問題 + 解決方向
- ✅ 包含上下文: 指出具體的欄位或參數
- ✅ 一致的結構: 所有響應使用相同格式

---

### 錯誤訊息 (Error Messages)

**目標受眾**: 所有用戶

**語言策略**:
- **語氣**: 同理、解決導向、非責備性
- **結構**: 問題描述 + 建議操作
- **範例**:

| 情境 | ❌ 不好的錯誤訊息 | ✅ 好的錯誤訊息 |
|------|-----------------|---------------|
| 認證失敗 | "401 Unauthorized" | "認證失敗。請檢查您的 API 金鑰是否正確。" |
| 資源不存在 | "404 Not Found" | "找不到該資源。請確認 ID 是否正確。" |
| 參數錯誤 | "Invalid input" | "參數 'page_size' 必須是正整數，當前值：-1" |
| 伺服器錯誤 | "500 Internal Server Error" | "伺服器發生錯誤，我們正在處理。請稍後再試。" |
| 限流 | "429 Too Many Requests" | "請求過於頻繁。請等待 60 秒後再試。" |

**關鍵原則**:
- ✅ 解釋問題: 用戶能理解發生了什麼
- ✅ 提供解決方案: 告訴用戶該怎麼做
- ✅ 避免責備: 不要用 "您的輸入有誤"，改用 "請檢查..."
- ✅ 包含技術細節: 開發者需要的錯誤代碼和堆疊

---

### 行銷內容 (Marketing Content)

**目標受眾**: 潛在客戶、市場推廣

**語言策略**:
- **主要語言**: 繁體中文
- **補充說明**: 英文品牌名稱
- **語氣**: 熱情、有說服力、價值導向
- **句式**: 簡短有力、強調利益

**範例**:
```markdown
## 為何選擇 MorningAI？

**自動化決策，釋放團隊潛力**  
讓 AI 代理處理重複性任務，您的團隊專注於創新與策略。

**10 倍效率提升**  
從手動流程到全自動工作流，平均節省 80% 時間成本。

**企業級安全與隔離**  
內建 Row-Level Security (RLS)，確保多租戶數據完全隔離。
```

**關鍵原則**:
- ✅ 以用戶利益為中心: "您將獲得..." 而非 "我們提供..."
- ✅ 使用具體數字: "10 倍效率" 而非 "顯著提升"
- ✅ 突出差異化: 說明為何選擇 MorningAI
- ✅ 呼籲行動: "立即開始"、"免費試用"

---

## 禁止使用清單 (Don'ts)

### 語言風格
- ❌ 過度口語化: "超讚的"、"酷斃了"
- ❌ 過度正式: "茲通知閣下..."、"敬啟者"
- ❌ 表情符號（除非行銷內容明確需要）: "😊"、"🎉"
- ❌ 網路用語: "gg"、"wwww"、"666"
- ❌ 模糊表達: "可能"、"也許"、"大概"

### 技術術語誤用
- ❌ 中英混雜（應統一）: "請 create 一個新的 workflow"
- ❌ 錯誤翻譯: "Agent" → "中介" (應為 "智能代理")
- ❌ 不一致術語: 同一概念使用多個譯名

### 用戶體驗
- ❌ 責備用戶: "您的操作有誤"
- ❌ 空洞承諾: "即將推出" (應給明確時間)
- ❌ 過度行銷: "史上最強"、"絕對"、"保證"

---

## 實施檢查清單 (Implementation Checklist)

### 開發者
- [ ] 所有 API 錯誤訊息提供 `error.code` 和 `error.message`
- [ ] 響應訊息支持 i18n（至少 zh-TW 和 en-US）
- [ ] 技術文檔使用英文，關鍵概念有中文註解
- [ ] 代碼註釋使用中文（團隊溝通效率）

### 設計師
- [ ] UI 文案使用繁體中文
- [ ] 按鈕使用動詞開頭（創建、編輯、刪除）
- [ ] 錯誤訊息包含問題說明 + 解決建議
- [ ] 專有名詞參考 `TERMINOLOGY.md`

### 產品經理
- [ ] 功能命名與術語對照表一致
- [ ] 用戶文檔語氣友好、清晰
- [ ] 行銷內容突出用戶價值
- [ ] Release notes 使用繁體中文 + 英文摘要

### QA
- [ ] 測試多語言切換功能
- [ ] 驗證錯誤訊息清晰度
- [ ] 檢查術語一致性
- [ ] 確保無硬編碼文本

---

## 版本歷史 (Version History)

| 版本 | 日期 | 變更內容 | 作者 |
|------|------|----------|------|
| 1.0 | 2025-10-21 | 初版發布 | MorningAI Team |

---

## 參考文檔 (References)

- [術語對照表](./TERMINOLOGY.md)
- [API 文檔](../api/README.md)
- [貢獻指南](./CONTRIBUTING.md)
