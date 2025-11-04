# API Backend Tests

本目錄包含 Flask API 後端的測試套件。

## 運行測試

```bash
# 運行所有測試
cd handoff/20250928/40_App/api-backend
python -m pytest tests/ -v

# 運行特定測試文件
python -m pytest tests/test_tenant_routes.py -v

# 運行帶 coverage 的測試
python -m pytest tests/ --cov=src --cov-report=html
```

## 測試環境配置

### Sentry 配置

測試環境中自動禁用 Sentry 以防止測試錯誤污染 Production 環境。

**自動禁用機制**（在 `conftest.py` 中配置）:
- `SENTRY_DSN` 環境變數被移除
- `SENTRY_ENABLED` 設為 `"false"`
- `TESTING` 設為 `"true"`

**為什麼需要這樣做？**

許多測試會故意觸發錯誤來驗證錯誤處理邏輯（例如 `test_get_current_tenant_server_error`）。如果測試時 Sentry 仍在運行，這些預期的測試錯誤會被發送到 Production Sentry，導致：

❌ 誤導性警報  
❌ Sentry quota 浪費  
❌ 混淆真實的 Production 錯誤  

**驗證配置**:

```bash
# 運行專門的 Sentry 配置測試
python -m pytest tests/test_sentry_disabled.py -v
```

應該看到所有測試通過：
```
✓ test_sentry_dsn_is_removed
✓ test_sentry_enabled_is_false  
✓ test_testing_flag_is_true
```

## 測試結構

```
tests/
├── conftest.py              # Pytest 配置和共用 fixtures
├── test_sentry_disabled.py  # Sentry 配置驗證
├── test_tenant_routes.py    # Tenant API 測試
├── test_auth_endpoints.py   # 認證端點測試
└── ...
```

## 常見問題

### Q: 為什麼測試會發送錯誤到 Sentry？

A: 這是舊的問題。現在 `conftest.py` 中的 `disable_sentry_in_tests` fixture 會自動禁用 Sentry（`autouse=True`）。

### Q: 如何在測試中使用真實的 Sentry？

A: 通常不建議。但如果需要測試 Sentry 整合，可以在特定測試中覆蓋 fixture：

```python
@pytest.mark.usefixtures("enable_sentry")  # 需要自定義 fixture
def test_sentry_integration():
    # 測試代碼
    pass
```

### Q: 測試失敗時如何調試？

A: 使用 `-v` 和 `-s` 參數：

```bash
python -m pytest tests/test_tenant_routes.py -v -s
```

- `-v`: verbose 模式，顯示詳細測試名稱
- `-s`: 顯示 print 輸出（不捕獲 stdout）

## 相關文檔

- [Sentry 測試錯誤分析報告](/home/ubuntu/SENTRY_TEST_ERROR_ANALYSIS.md)
- [pytest 文檔](https://docs.pytest.org/)
- [Flask 測試文檔](https://flask.palletsprojects.com/en/latest/testing/)
