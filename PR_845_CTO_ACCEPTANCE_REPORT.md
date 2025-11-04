# PR #845 CTO驗收報告

**日期：** 2025-10-27  
**審查者：** CTO (Ryan Chen)  
**PR：** https://github.com/RC918/morningai/pull/845  
**分支：** `devin/1761570563-phase3-batch9-type-annotations`  
**狀態：** ⚠️ **要求修正 - 不可合併**

---

## 執行摘要

PR #845 (Batch 9) 為3個大型元件添加TypeScript類型註解，但**引入了33個新的TypeScript錯誤**，違反了"不增加錯誤數量"的原則。此PR需要修正後才能合併。

**❌ 要求修正後重新提交**

---

## 關鍵發現

### ❌ 阻塞問題：引入33個新TypeScript錯誤

**TypeScript錯誤統計：**
- **Main分支：** 306個錯誤
- **PR分支：** 339個錯誤
- **新增錯誤：** 33個 ❌

**錯誤分布：**
- UsabilityTestDashboard.tsx: 16個新錯誤
- Dashboard.tsx: 3個新錯誤（`unsaved` status + DnD ref類型）
- 其他文件：14個錯誤（與此PR無關）

**結論：** 此PR引入的類型錯誤是**阻塞性問題**，必須修正後才能合併。過去的Batch 7和Batch 8都維持了"不增加錯誤數量"的標準，此PR不應例外。

---

## 詳細問題分析

### 阻塞問題 #1：UsabilityTestDashboard.tsx - 過度泛化的介面定義

**問題根源：**
```typescript
interface Session {
  id: string
  participantId: string
  startTime: number
  endTime?: number
  [key: string]: unknown  // ❌ 過度泛化！導致所有屬性都是unknown類型
}

interface SurveyResult {
  [key: string]: unknown  // ❌ 過度泛化！導致所有屬性都是unknown類型
}
```

**導致的16個TypeScript錯誤：**

1. **Lines 242-282：** `summary.*` 屬性全部為 `unknown` 類型，無法賦值給React children
   ```typescript
   // ❌ 錯誤：Type 'unknown' is not assignable to type 'ReactI18NextChildren'
   <div className="text-2xl font-bold">{summary.total_sessions}</div>
   <p className="text-xs text-muted-foreground">{summary.total_participants} participants</p>
   <div className="text-2xl font-bold">{summary.success_rate}</div>
   <p className="text-xs text-muted-foreground">{summary.successful_tasks}/{summary.completed_tasks} tasks</p>
   <div className="text-2xl font-bold">{summary.avg_sus_score}</div>
   <div className="text-2xl font-bold">{summary.nps_score}</div>
   <p className="text-xs text-muted-foreground">{summary.nps_rating}</p>
   ```

2. **Lines 443-450：** `result.*` 屬性為 `unknown` 類型
   ```typescript
   // ❌ 錯誤：Property 'toFixed' does not exist on type 'unknown'
   <div className="font-medium">{result.participant_id}</div>
   <div className="text-xs text-muted-foreground">
     {new Date(result.timestamp).toLocaleString()}  // ❌ unknown不能傳給Date構造函數
   </div>
   <div className="text-lg font-bold">{result.sus_score.toFixed(1)}</div>  // ❌ unknown沒有toFixed方法
   <div className="text-xs text-muted-foreground">Grade {result.sus_grade}</div>
   ```

3. **Lines 471-478：** NPS結果同樣問題
   ```typescript
   <div className="font-medium">{result.participant_id}</div>
   <div className="text-lg font-bold">{result.nps_score}/10</div>
   <div className="text-xs text-muted-foreground">{result.nps_category}</div>
   ```

**根本原因：**
- `calculateOverallSummary()` 返回 `Record<string, unknown>`
- `susResults` 和 `npsResults` 使用過度泛化的 `SurveyResult[]` 介面
- 索引簽名 `[key: string]: unknown` 使所有屬性訪問都返回 `unknown` 類型

---

### 阻塞問題 #2：Session介面與實際實現不匹配

**實際Session對象結構**（來自 `src/lib/usability-testing.js`）：
```javascript
class UsabilityTestingSession {
  constructor(participantId, sessionId) {
    this.participantId = participantId
    this.sessionId = sessionId  // ⚠️ 注意：是sessionId，不是id
    this.startTime = Date.now()
    this.tasks = []
    this.interactions = []
    this.currentTask = null
    this.isRecording = false
  }
  
  getSessionSummary() { ... }
  exportData() { ... }
}
```

**當前介面定義的問題：**
```typescript
interface Session {
  id: string           // ❌ 錯誤：實際是sessionId
  participantId: string
  startTime: number
  endTime?: number
  [key: string]: unknown  // ❌ 導致isRecording, tasks, sessionId等都是unknown
}
```

**導致的11個 `as any` 使用：**
```typescript
// Line 133: ❌ 缺少exportData()方法
const data: unknown = (session as any).exportData()

// Line 145: ❌ 缺少exportData()方法
sessions: sessions.map((s: Session) => (s as any).exportData()),

// Line 162: ❌ 缺少isRecording屬性
const completedSessions: Session[] = sessions.filter((s: Session) => !(s as any).isRecording)

// Lines 164, 166, 170: ❌ 缺少tasks屬性
const totalTasks: number = completedSessions.reduce((sum: number, s: Session) => sum + (s as any).tasks.length, 0)
const completedTasks: number = completedSessions.reduce(
  (sum: number, s: Session) => sum + (s as any).tasks.filter((t: any) => t.endTime !== null).length, 
  0
)
const successfulTasks: number = completedSessions.reduce(
  (sum: number, s: Session) => sum + (s as any).tasks.filter((t: any) => t.success === true).length, 
  0
)

// Lines 175, 178: ❌ SurveyResult缺少sus_score和nps_score
const avgSUS: number | null = susResults.length > 0
  ? susResults.reduce((sum: number, r: SurveyResult) => sum + (r as any).sus_score, 0) / susResults.length
  : null
const npsScores: number[] = npsResults.map((r: SurveyResult) => (r as any).nps_score)

// Line 364: ❌ 缺少getSessionSummary()方法
const summary: any = (session as any).getSessionSummary()

// Lines 366, 395: ❌ 使用sessionId但介面定義為id
<Card key={(session as any).sessionId}>
onClick={(): void => handleDeleteSession((session as any).sessionId)}
```

---

### 阻塞問題 #3：Dashboard.tsx - SaveStatus類型不完整

**問題：**
```typescript
interface SaveStatus {
  status: 'saved' | 'saving' | 'error'  // ❌ 缺少'unsaved'狀態
  lastSaved: Date | null
  error: string | null
}

// Lines 305, 310, 320: ❌ 錯誤：Type '"unsaved"' is not assignable to type '"error" | "saved" | "saving"'
setSaveStatus((prev: SaveStatus): SaveStatus => ({ ...prev, status: 'unsaved' as const }))
```

**修正：**
```typescript
interface SaveStatus {
  status: 'saved' | 'saving' | 'error' | 'unsaved'  // ✅ 添加'unsaved'
  lastSaved: Date | null
  error: string | null
}
```

---

### 非阻塞問題：Dashboard.tsx - Widget介面缺少屬性

**問題：**
```typescript
interface Widget {
  id: string
  type: string
  component: React.ReactNode | null
  // ❌ 缺少name和position屬性
}

// Line 272: ❌ 使用as any訪問position
layout: { widgets: dashboardLayout.map((w: Widget) => ({ id: w.id, position: (w as any).position })) }

// Line 437: ❌ 使用as any訪問name
<span className="text-xs">{(widget as any).name}</span>
```

**調查結果：**
根據 `WidgetLibrary.tsx` 的實現，widget組件本身不包含 `name` 或 `position` 元數據。這些屬性可能來自：
1. API響應 `/dashboard/layouts` 或 `getDashboardWidgets()`
2. 前端本地添加的元數據

**建議修正：**
```typescript
interface Widget {
  id: string
  type: string
  component: React.ReactNode | null
  name?: string  // ✅ 可選屬性
  position?: { x: number; y: number; w?: number; h?: number }  // ✅ 可選屬性
}
```

---

## 必須修正項目（阻塞合併）

### 1. 定義正確的Session介面 ✅ 必須

**基於實際實現**（`src/lib/usability-testing.js`）：

```typescript
interface Task {
  taskId: string
  taskName: string
  description: string
  startTime: number
  endTime: number | null
  duration: number | null
  success: boolean | null
  errors: Array<{ timestamp: number; type: string; description: string }>
  interactions: Array<unknown>
  notes: Array<{ timestamp: number; text: string } | string>
}

interface SessionSummary {
  session_id: string
  participant_id: string
  total_duration_ms: number
  total_duration_minutes: number
  tasks_total: number
  tasks_completed: number
  tasks_successful: number
  tasks_failed: number
  success_rate: string
  total_errors: number
  total_interactions: number
  avg_task_duration_ms: number
  avg_task_duration_seconds: number
  tasks: Array<{
    task_id: string
    task_name: string
    duration_seconds: number | null
    success: boolean | null
    errors: number
    interactions: number
  }>
}

interface Session {
  participantId: string
  sessionId: string  // ✅ 不是id，是sessionId
  startTime: number
  endTime?: number
  tasks: Task[]
  interactions: Array<unknown>
  currentTask: Task | null
  isRecording: boolean
  
  // 方法
  exportData(): {
    session_id: string
    participant_id: string
    start_time: string
    end_time: string | null
    tasks: Task[]
    interactions: Array<unknown>
    summary: SessionSummary
  }
  
  getSessionSummary(): SessionSummary
}
```

**移除所有 `as any` 使用：**
- Line 133: `session.exportData()` ✅
- Line 145: `s.exportData()` ✅
- Line 162: `!s.isRecording` ✅
- Lines 164, 166, 170: `s.tasks` ✅
- Line 364: `session.getSessionSummary()` ✅
- Lines 366, 395: `session.sessionId` ✅

---

### 2. 定義正確的SurveyResult介面 ✅ 必須

**基於實際使用**（SUSQuestionnaire.tsx 和 NPSQuestionnaire.tsx）：

```typescript
interface SUSResult {
  participant_id: string
  session_id?: string
  timestamp: string | number
  sus_score: number
  sus_grade: string
  sus_adjective?: string
  responses: number[]
}

interface NPSResult {
  participant_id: string
  session_id?: string
  timestamp: string | number
  nps_score: number
  nps_category: string  // 'Promoter', 'Passive', 'Detractor'
  comment?: string
}
```

**更新狀態類型：**
```typescript
const [susResults, setSusResults] = useState<SUSResult[]>([])
const [npsResults, setNpsResults] = useState<NPSResult[]>([])
```

**移除所有 `as any` 使用：**
- Line 175: `r.sus_score` ✅
- Line 178: `r.nps_score` ✅

---

### 3. 定義OverallSummary介面 ✅ 必須

**當前問題：**
```typescript
const calculateOverallSummary = (): Record<string, unknown> => { ... }
const summary: Record<string, unknown> = calculateOverallSummary()
```

**修正：**
```typescript
interface OverallSummary {
  total_sessions: number
  total_participants: number
  total_tasks: number
  completed_tasks: number
  successful_tasks: number
  success_rate: string
  avg_sus_score: string | number
  nps_score: number | string
  nps_rating: string
}

const calculateOverallSummary = (): OverallSummary => {
  // ... 實現保持不變
  return {
    total_sessions: completedSessions.length,
    total_participants: new Set(completedSessions.map((s: Session) => s.participantId)).size,
    total_tasks: totalTasks,
    completed_tasks: completedTasks,
    successful_tasks: successfulTasks,
    success_rate: completedTasks > 0 ? ((successfulTasks / completedTasks) * 100).toFixed(1) + '%' : 'N/A',
    avg_sus_score: avgSUS ? avgSUS.toFixed(1) : 'N/A',
    nps_score: npsResult ? npsResult.nps : 'N/A',
    nps_rating: npsResult ? npsResult.rating : 'N/A'
  }
}

const summary: OverallSummary = calculateOverallSummary()
```

**這將消除16個TypeScript錯誤！**

---

### 4. 修正Dashboard.tsx SaveStatus類型 ✅ 必須

```typescript
interface SaveStatus {
  status: 'saved' | 'saving' | 'error' | 'unsaved'  // ✅ 添加'unsaved'
  lastSaved: Date | null
  error: string | null
}
```

---

### 5. 修正sessionId vs id不一致 ✅ 必須

**選項A：** 更新介面使用 `sessionId`（推薦）
```typescript
interface Session {
  sessionId: string  // ✅ 與實際實現一致
  // ... 其他屬性
}

// 更新所有使用
<Card key={session.sessionId}>
onClick={(): void => handleDeleteSession(session.sessionId)}
```

**選項B：** 在loadSession時將sessionId映射為id
```typescript
const loadSessions = (): void => {
  const sessionIds: string[] = usabilityTest.listSessions()
  const loadedSessions: Session[] = sessionIds
    .map((id: string) => {
      const session = usabilityTest.loadSession(id)
      return session ? { ...session, id: session.sessionId } : null
    })
    .filter(Boolean)
    .sort((a: Session, b: Session) => b.startTime - a.startTime)
  setSessions(loadedSessions)
}
```

**推薦：** 選項A，與實際實現保持一致。

---

## 建議改進項目（非阻塞）

### 6. 擴展Widget介面（可選）

```typescript
interface Widget {
  id: string
  type: string
  component: React.ReactNode | null
  name?: string  // ✅ 可選
  position?: {   // ✅ 可選
    x: number
    y: number
    w?: number
    h?: number
  }
}
```

**注意：** 需要驗證API響應是否實際包含這些欄位。如果不包含，保持 `as any` 可能是暫時的合理選擇。

---

### 7. MetricsAnalysisDashboard.tsx類型改進（可選）

**當前狀態：** ✅ 未引入新錯誤，但可以改進

```typescript
// 當前使用Record<string, unknown>
web_vitals?: Record<string, unknown>
ux_metrics?: Record<string, unknown>
trends?: Record<string, unknown>
regression?: Record<string, unknown>

// 建議改進（後續PR）
interface WebVitalStats {
  status: MetricStatus
  current: number
  average: number
  p90: number
  count: number
}

interface MetricsReport {
  // ...
  web_vitals?: Record<string, WebVitalStats>
  ux_metrics?: {
    ttv?: {
      status: MetricStatus
      average: number
      median: number
      p90: number
      count: number
    }
  }
  // ...
}
```

**決定：** 不在此PR中要求，因為未引入新錯誤。可創建後續任務票據。

---

## 技術驗證

### TypeScript類型檢查 ❌

```
Main分支：     306個錯誤
PR分支：       339個錯誤
新增錯誤：     33個 ❌
```

**結論：** 引入33個新錯誤，違反驗收標準。

### CI/CD狀態 ✅

```
✅ 所有20/20 CI檢查通過
✅ 構建成功
✅ Lint檢查通過
```

### `as any` 使用統計

**Dashboard.tsx：** 2個實例
- Line 272: `(w as any).position`
- Line 437: `(widget as any).name`

**UsabilityTestDashboard.tsx：** 11個實例
- Lines 133, 145: `exportData()`
- Line 162: `isRecording`
- Lines 164, 166, 170: `tasks`
- Lines 175, 178: `sus_score`, `nps_score`
- Line 364: `getSessionSummary()`
- Lines 366, 395: `sessionId`

**MetricsAnalysisDashboard.tsx：** 0個實例 ✅

**總計：** 13個 `as any` 使用

---

## 修正檢查清單

工程團隊需要完成以下修正：

### 阻塞性修正（必須完成）

- [ ] **1. 定義完整的Session介面**
  - [ ] 添加 `sessionId: string`（不是id）
  - [ ] 添加 `tasks: Task[]`
  - [ ] 添加 `isRecording: boolean`
  - [ ] 添加 `exportData()` 方法簽名
  - [ ] 添加 `getSessionSummary()` 方法簽名
  - [ ] 移除 `[key: string]: unknown` 索引簽名

- [ ] **2. 定義Task介面**
  - [ ] 包含所有必需屬性（taskId, taskName, startTime, endTime, success, errors等）

- [ ] **3. 定義SessionSummary介面**
  - [ ] 包含所有getSessionSummary()返回的屬性

- [ ] **4. 定義SUSResult和NPSResult介面**
  - [ ] SUSResult: participant_id, timestamp, sus_score, sus_grade
  - [ ] NPSResult: participant_id, timestamp, nps_score, nps_category
  - [ ] 移除泛化的SurveyResult介面

- [ ] **5. 定義OverallSummary介面**
  - [ ] 包含所有calculateOverallSummary()返回的屬性
  - [ ] 更新函數簽名為 `(): OverallSummary`
  - [ ] 更新summary變量類型

- [ ] **6. 修正SaveStatus類型**
  - [ ] 添加 `'unsaved'` 到status聯合類型

- [ ] **7. 統一sessionId vs id**
  - [ ] 決定使用sessionId（推薦）或id
  - [ ] 更新所有相關代碼保持一致

- [ ] **8. 移除所有as any使用**
  - [ ] UsabilityTestDashboard.tsx: 11個實例
  - [ ] 驗證所有屬性訪問都有正確類型

- [ ] **9. 重新運行typecheck**
  - [ ] 確認錯誤數量回到306
  - [ ] 確認無新增錯誤

### 可選改進（非阻塞）

- [ ] **10. 擴展Widget介面**（如果API支持）
  - [ ] 添加 `name?: string`
  - [ ] 添加 `position?: { x, y, w?, h? }`

- [ ] **11. 創建後續任務票據**
  - [ ] MetricsAnalysisDashboard類型細化
  - [ ] API Client類型生成
  - [ ] 集中化類型定義

---

## 預期結果

完成所有阻塞性修正後：

1. **TypeScript錯誤：** 306個（與main相同）✅
2. **`as any` 使用：** 0-2個（僅Dashboard的name/position如果API不支持）
3. **類型安全：** 所有Session、SurveyResult、Summary屬性都有正確類型
4. **代碼質量：** 無運行時行為變更，純類型註解

---

## 風險評估

### 當前風險等級：高 ❌

**阻塞風險：**
- ❌ 引入33個新TypeScript錯誤
- ❌ 過度使用 `as any`（13個實例）
- ❌ 介面定義與實際實現不匹配
- ❌ 類型安全性降低（unknown類型傳播）

**修正後風險：** 極低 ✅

---

## 團隊表現評估

**評分：** ⭐⭐⭐ (3/5)

**優點：**
- 工作量大（1,650+行代碼）
- MetricsAnalysisDashboard.tsx執行良好（無新錯誤）
- PR描述清楚標識了已知問題
- CI/CD全部通過

**需改進：**
- 引入33個新TypeScript錯誤（違反標準）
- 過度使用索引簽名導致類型安全性降低
- 未驗證實際實現就定義介面
- sessionId vs id不一致

**建議：**
- 在添加類型前先檢查實際實現
- 避免使用 `[key: string]: unknown` 索引簽名
- 運行typecheck並確保不增加錯誤數量
- 參考Batch 7和Batch 8的標準

---

## 最終決定

### ❌ 要求修正 - 不可合併

**拒絕理由：**
1. ❌ 引入33個新TypeScript錯誤（違反驗收標準）
2. ❌ 過度使用 `as any`（13個實例）
3. ❌ 介面定義與實際實現嚴重不匹配
4. ❌ 類型安全性降低（unknown類型傳播到React children）

**批准條件：**
1. ✅ 完成所有9項阻塞性修正
2. ✅ TypeScript錯誤數量回到306
3. ✅ 移除所有不必要的 `as any` 使用
4. ✅ 重新運行CI/CD確認通過

**預計修正時間：** 4-6小時

---

## 後續行動

### 立即行動（工程團隊）

1. 閱讀 `src/lib/usability-testing.js` 了解實際Session結構
2. 按照檢查清單完成所有9項阻塞性修正
3. 運行 `pnpm run typecheck` 確認錯誤數量回到306
4. 提交修正並更新PR

### 驗證行動（CTO）

1. 重新審查修正後的代碼
2. 驗證TypeScript錯誤數量
3. 確認所有 `as any` 已移除或有合理解釋
4. 最終批准或提供進一步反饋

### 後續任務票據

1. **MetricsAnalysisDashboard類型細化**（優先級：MEDIUM）
   - 定義WebVitalStats、UXMetrics等詳細介面
   - 替換Record<string, unknown>

2. **類型集中化**（優先級：MEDIUM）
   - 創建 `src/types/usability.ts`
   - 創建 `src/types/dashboard.ts`
   - 集中管理共享類型

3. **API類型生成**（優先級：LOW）
   - 調研Orval/openapi-typescript
   - 自動生成API客戶端類型

---

## 總結

PR #845展示了大規模類型註解工作的複雜性。雖然工作量大且MetricsAnalysisDashboard執行良好，但UsabilityTestDashboard的介面定義問題導致引入33個新TypeScript錯誤，這是不可接受的。

**關鍵教訓：**
1. 在定義介面前必須檢查實際實現
2. 避免過度使用索引簽名 `[key: string]: unknown`
3. 每次提交前運行typecheck確保不增加錯誤
4. 參考成功的先例（Batch 7, Batch 8）

**修正後此PR將是高質量的類型註解工作，值得合併。**

---

**報告生成：** 2025-10-27  
**CTO簽名：** Ryan Chen  
**Devin運行連結：** https://app.devin.ai/sessions/f416a94c87d14b39bb4cb59d00667a84

---

## 附錄：錯誤示例

### UsabilityTestDashboard.tsx 新增錯誤（16個）

```typescript
// Lines 242-282: summary屬性為unknown
src/components/usability/UsabilityTestDashboard.tsx(242,49): error TS2322: Type 'unknown' is not assignable to type 'ReactI18NextChildren | Iterable<ReactI18NextChildren>'.
src/components/usability/UsabilityTestDashboard.tsx(243,58): error TS2322: Type 'unknown' is not assignable to type 'string | number | bigint | boolean | ReactElement<unknown, string | JSXElementConstructor<any>> | Iterable<ReactNode> | ReactPortal | Promise<...>'.
src/components/usability/UsabilityTestDashboard.tsx(255,49): error TS2322: Type 'unknown' is not assignable to type 'ReactI18NextChildren | Iterable<ReactI18NextChildren>'.
src/components/usability/UsabilityTestDashboard.tsx(256,58): error TS2322: Type 'unknown' is not assignable to type 'string | number | bigint | boolean | ReactElement<unknown, string | JSXElementConstructor<any>> | Iterable<ReactNode> | ReactPortal | Promise<...>'.
src/components/usability/UsabilityTestDashboard.tsx(256,85): error TS2322: Type 'unknown' is not assignable to type 'string | number | bigint | boolean | ReactElement<unknown, string | JSXElementConstructor<any>> | Iterable<ReactNode> | ReactPortal | Promise<...>'.
src/components/usability/UsabilityTestDashboard.tsx(268,49): error TS2322: Type 'unknown' is not assignable to type 'ReactI18NextChildren | Iterable<ReactI18NextChildren>'.
src/components/usability/UsabilityTestDashboard.tsx(281,49): error TS2322: Type 'unknown' is not assignable to type 'ReactI18NextChildren | Iterable<ReactI18NextChildren>'.
src/components/usability/UsabilityTestDashboard.tsx(282,58): error TS2322: Type 'unknown' is not assignable to type 'ReactI18NextChildren | Iterable<ReactI18NextChildren>'.

// Lines 443-450: result屬性為unknown
src/components/usability/UsabilityTestDashboard.tsx(443,56): error TS2322: Type 'unknown' is not assignable to type 'ReactI18NextChildren | Iterable<ReactI18NextChildren>'.
src/components/usability/UsabilityTestDashboard.tsx(445,39): error TS2769: No overload matches this call.
src/components/usability/UsabilityTestDashboard.tsx(449,80): error TS2339: Property 'toFixed' does not exist on type 'unknown'.
src/components/usability/UsabilityTestDashboard.tsx(450,80): error TS2322: Type 'unknown' is not assignable to type 'string | number | bigint | boolean | ReactElement<unknown, string | JSXElementConstructor<any>> | Iterable<ReactNode> | ReactPortal | Promise<...>'.

// Lines 471-478: NPS result屬性為unknown
src/components/usability/UsabilityTestDashboard.tsx(471,56): error TS2322: Type 'unknown' is not assignable to type 'ReactI18NextChildren | Iterable<ReactI18NextChildren>'.
src/components/usability/UsabilityTestDashboard.tsx(473,39): error TS2769: No overload matches this call.
src/components/usability/UsabilityTestDashboard.tsx(477,62): error TS2322: Type 'unknown' is not assignable to type 'string | number | bigint | boolean | ReactElement<unknown, string | JSXElementConstructor<any>> | Iterable<ReactNode> | ReactPortal | Promise<...>'.
src/components/usability/UsabilityTestDashboard.tsx(478,74): error TS2322: Type 'unknown' is not assignable to type 'ReactI18NextChildren | Iterable<ReactI18NextChildren>'.
```

### Dashboard.tsx 新增錯誤（3個）

```typescript
// Lines 305, 310, 320: 'unsaved' status不在類型定義中
src/components/Dashboard.tsx(305,65): error TS2820: Type '"unsaved"' is not assignable to type '"error" | "saved" | "saving"'. Did you mean '"saved"'?
src/components/Dashboard.tsx(310,65): error TS2820: Type '"unsaved"' is not assignable to type '"error" | "saved" | "saving"'. Did you mean '"saved"'?
src/components/Dashboard.tsx(320,65): error TS2820: Type '"unsaved"' is not assignable to type '"error" | "saved" | "saving"'. Did you mean '"saved"'?
```
