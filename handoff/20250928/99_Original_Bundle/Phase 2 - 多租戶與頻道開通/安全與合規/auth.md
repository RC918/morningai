
# 驗證與授權 - Phase 2: 多租戶與頻道開通

## 1. 驗證機制

- **Token 驗證**：在連接通訊平台時，系統會驗證使用者提供的 Token 或 Access Token 的有效性。
- **OAuth 2.0**：在整合 Messenger Bot 時，系統會使用 OAuth 2.0 流程來取得使用者的授權。

## 2. 授權機制

- **Webhook 授權**：系統會為每個租戶的每個通訊平台產生一個獨一無二的 Webhook URL，以確保只有合法的請求才能被處理。
- **權限範圍**：在整合 Messenger Bot 時，系統只會請求必要的權限（例如 `pages_messaging`），以保護使用者的隱私。

