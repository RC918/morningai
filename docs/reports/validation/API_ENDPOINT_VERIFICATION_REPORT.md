# Dashboard API 端點驗證報告

**日期**: 2025-10-21  
**目的**: 確認 Dashboard 所需的 API 端點可用性  
**相關 Issue**: #474-#477 (Week 5-6 Dashboard 能力增強)

---

## 📋 執行摘要

### 驗證結果

**總體狀態**: ✅ **大部分可用** (6/8 端點已實作)

- ✅ **已實作**: 6 個端點
- ⚠️ **需要新增**: 2 個端點
- 🔴 **需要 RFC**: 0 個端點 (現有端點足夠)

---

## ✅ 已實作的 API 端點

### 1. GET /api/dashboard/metrics

**狀態**: ✅ **已實作**

**檔案**: `handoff/20250928/40_App/api-backend/src/routes/dashboard.py:8-28`

**回傳資料**:
```json
{
  "cpu_usage": 72.5,
  "memory_usage": 68.3,
  "response_time": 145,
  "error_rate": 0.02,
  "active_strategies": 12,
  "pending_approvals": 3,
  "cost_today": 45.67,
  "cost_saved": 123.45,
  "timestamp": "2025-10-21T10:30:00"
}
```

**對應 Dashboard 需求**:
- ✅ CPU 使用率 (`cpu_usage`)
- ✅ 內存使用率 (`memory_usage`)
- ✅ 響應時間 (`response_time`)
- ✅ 錯誤率 (`error_rate`)
- ✅ 活躍策略數 (`active_strategies`)
- ✅ 待審批任務 (`pending_approvals`)
- ✅ 今日成本 (`cost_today`)
- ✅ 成本節省 (`cost_saved`)

---

### 2. GET /api/dashboard/performance-history

**狀態**: ✅ **已實作**

**檔案**: `handoff/20250928/40_App/api-backend/src/routes/dashboard.py:30-55`

**參數**:
- `hours` (可選): 歷史數據小時數，預設 6

**回傳資料**:
```json
[
  {
    "time": "14:30",
    "cpu": 72.5,
    "memory": 68.3,
    "response_time": 145,
    "timestamp": "2025-10-21T14:30:00"
  },
  ...
]
```

**對應 Dashboard 需求**:
- ✅ 性能趨勢圖數據
- ✅ CPU/內存歷史
- ✅ 響應時間歷史

---

### 3. GET /api/dashboard/recent-decisions

**狀態**: ✅ **已實作**

**檔案**: `handoff/20250928/40_App/api-backend/src/routes/dashboard.py:57-91`

**參數**:
- `limit` (可選): 返回決策數量，預設 10

**回傳資料**:
```json
[
  {
    "id": "decision_001",
    "timestamp": "2025-10-21T14:25:00",
    "strategy": "CPU優化策略",
    "status": "executed",
    "impact": "+15% 性能提升",
    "confidence": 0.87,
    "execution_time": 45.3
  },
  ...
]
```

**對應 Dashboard 需求**:
- ✅ 最近決策列表
- ✅ 決策狀態 (executed/pending/failed)
- ✅ 影響評估
- ✅ 信心度

---

### 4. GET /api/dashboard/system-health

**狀態**: ✅ **已實作**

**檔案**: `handoff/20250928/40_App/api-backend/src/routes/dashboard.py:93-131`

**回傳資料**:
```json
{
  "overall_status": "healthy",
  "components": {
    "ai_gateway": {
      "status": "healthy",
      "response_time": 120,
      "last_check": "2025-10-21T14:30:00"
    },
    "learning_system": {
      "status": "healthy",
      "active_strategies": 15,
      "last_check": "2025-10-21T14:30:00"
    },
    ...
  },
  "last_check_time": "2025-10-21T14:30:00"
}
```

**對應 Dashboard 需求**:
- ✅ 系統健康狀態
- ✅ 組件狀態監控

---

### 5. GET /api/dashboard/alerts

**狀態**: ✅ **已實作**

**檔案**: `handoff/20250928/40_App/api-backend/src/routes/dashboard.py:133-163`

**回傳資料**:
```json
[
  {
    "id": "alert_1",
    "type": "high_cpu",
    "message": "CPU使用率持續偏高",
    "severity": "warning",
    "timestamp": "2025-10-21T14:15:00",
    "acknowledged": false
  },
  ...
]
```

**對應 Dashboard 需求**:
- ✅ 活躍告警列表
- ✅ 告警嚴重程度
- ✅ 告警確認狀態

---

### 6. GET /api/dashboard/cost-analysis

**狀態**: ✅ **已實作**

**檔案**: `handoff/20250928/40_App/api-backend/src/routes/dashboard.py:165-200`

**參數**:
- `period` (可選): today/week/month，預設 today

**回傳資料**:
```json
{
  "total_cost": 65.50,
  "ai_service_cost": 32.75,
  "infrastructure_cost": 22.50,
  "storage_cost": 5.25,
  "savings": 125.80,
  "breakdown": [
    {"service": "OpenAI API", "cost": 20.50},
    {"service": "AWS EC2", "cost": 15.30},
    ...
  ]
}
```

**對應 Dashboard 需求**:
- ✅ 成本分析
- ✅ 成本分解
- ✅ 成本節省

---

## ⚠️ 需要新增的 API 端點

### 7. GET /api/dashboard/layouts (需要新增)

**狀態**: ⚠️ **需要實作**

**目的**: 儲存/載入用戶自訂的 Dashboard 佈局

**當前狀態**:
- Dashboard.jsx 已經呼叫此端點 (line 118)
- 但後端尚未實作

**建議實作**:

```python
# dashboard.py

@dashboard_bp.route('/layouts', methods=['GET'])
def get_dashboard_layout():
    """獲取用戶的 Dashboard 佈局"""
    try:
        user_id = request.args.get('user_id', 'default')
        
        # TODO: 從資料庫載入用戶佈局
        # 目前返回預設佈局
        default_layout = {
            'user_id': user_id,
            'widgets': [
                {'id': 'cpu_usage', 'position': {'x': 0, 'y': 0, 'w': 6, 'h': 4}},
                {'id': 'memory_usage', 'position': {'x': 6, 'y': 0, 'w': 6, 'h': 4}},
                {'id': 'response_time', 'position': {'x': 0, 'y': 4, 'w': 6, 'h': 4}},
                {'id': 'error_rate', 'position': {'x': 6, 'y': 4, 'w': 6, 'h': 4}},
                {'id': 'active_strategies', 'position': {'x': 0, 'y': 8, 'w': 4, 'h': 3}},
                {'id': 'pending_approvals', 'position': {'x': 4, 'y': 8, 'w': 4, 'h': 3}},
                {'id': 'task_execution', 'position': {'x': 8, 'y': 8, 'w': 4, 'h': 6}}
            ],
            'updated_at': datetime.datetime.now().isoformat()
        }
        
        return jsonify(default_layout)
        
    except Exception as e:
        return jsonify({'error': '獲取佈局失敗'}), 500

@dashboard_bp.route('/layouts', methods=['POST'])
def save_dashboard_layout():
    """儲存用戶的 Dashboard 佈局"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default')
        layout = data.get('layout', {})
        
        # TODO: 儲存到資料庫
        # 目前只返回成功
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'updated_at': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': '儲存佈局失敗'}), 500
```

**優先級**: 🟡 **P1** (Week 5-6 需要)

**預估工時**: 2-3 小時 (含資料庫 schema)

---

### 8. GET /api/dashboard/widgets (需要新增)

**狀態**: ⚠️ **需要實作**

**目的**: 獲取可用的 Dashboard 小工具列表

**當前狀態**:
- Dashboard.jsx 已經呼叫此端點 (line 135)
- 但後端尚未實作

**建議實作**:

```python
# dashboard.py

@dashboard_bp.route('/widgets', methods=['GET'])
def get_available_widgets():
    """獲取可用的 Dashboard 小工具列表"""
    try:
        widgets = [
            {
                'id': 'cpu_usage',
                'name': 'CPU 使用率',
                'description': '實時 CPU 使用率監控',
                'category': 'system',
                'icon': 'cpu',
                'size': {'w': 6, 'h': 4}
            },
            {
                'id': 'memory_usage',
                'name': '內存使用率',
                'description': '實時內存使用率監控',
                'category': 'system',
                'icon': 'memory',
                'size': {'w': 6, 'h': 4}
            },
            {
                'id': 'response_time',
                'name': '響應時間',
                'description': '系統響應時間監控',
                'category': 'performance',
                'icon': 'clock',
                'size': {'w': 6, 'h': 4}
            },
            {
                'id': 'error_rate',
                'name': '錯誤率',
                'description': '系統錯誤率監控',
                'category': 'performance',
                'icon': 'alert',
                'size': {'w': 6, 'h': 4}
            },
            {
                'id': 'active_strategies',
                'name': '活躍策略',
                'description': '當前活躍的 AI 策略數量',
                'category': 'ai',
                'icon': 'zap',
                'size': {'w': 4, 'h': 3}
            },
            {
                'id': 'pending_approvals',
                'name': '待審批任務',
                'description': '需要人工審批的決策數量',
                'category': 'workflow',
                'icon': 'check-circle',
                'size': {'w': 4, 'h': 3}
            },
            {
                'id': 'cost_today',
                'name': '今日成本',
                'description': '今日累計成本',
                'category': 'cost',
                'icon': 'dollar-sign',
                'size': {'w': 4, 'h': 3}
            },
            {
                'id': 'cost_saved',
                'name': '成本節省',
                'description': '通過 AI 優化節省的成本',
                'category': 'cost',
                'icon': 'trending-down',
                'size': {'w': 4, 'h': 3}
            },
            {
                'id': 'task_execution',
                'name': '任務執行',
                'description': '任務執行狀態與統計',
                'category': 'workflow',
                'icon': 'activity',
                'size': {'w': 4, 'h': 6}
            }
        ]
        
        return jsonify({'widgets': widgets})
        
    except Exception as e:
        return jsonify({'error': '獲取小工具列表失敗'}), 500
```

**優先級**: 🟡 **P1** (Week 5-6 需要)

**預估工時**: 1-2 小時

---

## 📊 API 端點對應表

| Dashboard 需求 | API 端點 | 狀態 | 優先級 |
|---------------|---------|------|--------|
| CPU 使用率 | GET /api/dashboard/metrics | ✅ 已實作 | - |
| 內存使用率 | GET /api/dashboard/metrics | ✅ 已實作 | - |
| 響應時間 | GET /api/dashboard/metrics | ✅ 已實作 | - |
| 錯誤率 | GET /api/dashboard/metrics | ✅ 已實作 | - |
| 活躍策略數 | GET /api/dashboard/metrics | ✅ 已實作 | - |
| 待審批任務 | GET /api/dashboard/metrics | ✅ 已實作 | - |
| 今日成本 | GET /api/dashboard/metrics | ✅ 已實作 | - |
| 成本節省 | GET /api/dashboard/metrics | ✅ 已實作 | - |
| 性能趨勢 | GET /api/dashboard/performance-history | ✅ 已實作 | - |
| 最近決策 | GET /api/dashboard/recent-decisions | ✅ 已實作 | - |
| 系統健康 | GET /api/dashboard/system-health | ✅ 已實作 | - |
| 活躍告警 | GET /api/dashboard/alerts | ✅ 已實作 | - |
| 成本分析 | GET /api/dashboard/cost-analysis | ✅ 已實作 | - |
| 佈局儲存/載入 | GET/POST /api/dashboard/layouts | ⚠️ 需要實作 | 🟡 P1 |
| 小工具列表 | GET /api/dashboard/widgets | ⚠️ 需要實作 | 🟡 P1 |

---

## 🚀 建議行動

### 立即執行 (本週)

1. **實作 GET/POST /api/dashboard/layouts** (2-3 小時)
   - 建立資料庫 schema (如需要)
   - 實作 GET 端點 (載入佈局)
   - 實作 POST 端點 (儲存佈局)
   - 測試與驗證

2. **實作 GET /api/dashboard/widgets** (1-2 小時)
   - 定義小工具清單
   - 實作 GET 端點
   - 測試與驗證

### Week 5-6 前完成

3. **整合測試** (1 小時)
   - 測試所有 Dashboard API 端點
   - 確認前後端整合正常
   - 修復任何發現的問題

---

## 📝 RFC 評估

### 是否需要 RFC？

**結論**: ❌ **不需要**

**理由**:
1. 新增的端點不影響現有 API
2. 不涉及資料庫 schema 變更 (或僅新增表)
3. 不影響其他系統組件
4. 向後相容

### 建議流程

1. 直接建立工程 PR
2. PR 描述中說明新增端點的目的與用途
3. 確保通過所有 CI 檢查
4. Code review 後合併

---

## ✅ 結論

### 當前狀態

- **6/8 端點已實作** (75%)
- **2/8 端點需要新增** (25%)
- **0 端點需要 RFC**

### 風險評估

- 🟢 **低風險**: 新增端點不影響現有功能
- 🟢 **低複雜度**: 實作簡單，預估 3-5 小時完成
- 🟢 **低依賴**: 不依賴其他系統變更

### 推薦策略

1. **本週完成**: 實作 layouts 與 widgets 端點
2. **Week 5-6 前**: 完成整合測試
3. **無需 RFC**: 直接建立工程 PR

---

**報告完成日期**: 2025-10-21  
**下次更新**: 實作完成後
