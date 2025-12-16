# 斷言修復計劃

## 策略：更智能的斷言

不是簡單地將 `in [200, 500]` 改為 `== 200`，而是：
1. 保留對可選服務的寬鬆斷言
2. 在寬鬆斷言後添加**更嚴格的內容驗證**

## 修復示例

### 修改前（問題）
```python
assert response.status_code in [200, 500]
```
**問題**：測試對成功和失敗都滿意

### 修改後（正確）
```python
assert response.status_code in [200, 500]

if response.status_code == 200:
    data = response.get_json()
    assert 'expected_field' in data
    assert data['expected_field'] is not None
elif response.status_code == 500:
    data = response.get_json()
    assert 'error' in data
    assert len(data['error']) > 0
```
**優點**：
- 允許服務不可用（500）
- 但嚴格驗證響應結構
- 確保錯誤消息有意義

## 需要修復的測試

### 優先級 1：核心功能（必須修復）
1. `test_health_check_complete_flow` - 健康檢查必須返回正確結構
2. `test_new_user_dashboard_setup` - 用戶工作流核心
3. `test_concurrent_health_checks` - 並發健康檢查

### 優先級 2：保留但增強（可選）
1. Dashboard 相關測試 - 添加內容驗證
2. Report 相關測試 - 添加錯誤處理驗證

### 優先級 3：保持現狀（Phase 7）
1. 所有 Phase 7 監控測試
2. 所有環境驗證測試
