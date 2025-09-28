-- Phase 3 Seed Data: 為平台綁定和外部整合提供範例數據

-- 假設 tenant_id = 1 和 user_id = 1, 2, 3 已在之前的種子數據中創建

-- 1. 為 tenant_id = 1 更新行業和地區信息
UPDATE tenants SET industry = 'E-commerce', region = 'APAC' WHERE id = 1;

-- 2. 為 tenant_id = 1 插入一個已成功綁定的 Telegram 平台
INSERT INTO platform_bindings (tenant_id, platform, platform_user_id, access_token, webhook_url, status)
VALUES (1, 'telegram', '1234567890:BOT_TOKEN_EXAMPLE', 'encrypted:tg_token_here', 'https://api.morningai.me/webhook/telegram/1', 'active')
ON CONFLICT (tenant_id, platform) DO NOTHING;

-- 3. 為 tenant_id = 1 插入一個綁定失敗的 LINE 平台，並記錄錯誤信息
INSERT INTO platform_bindings (tenant_id, platform, access_token, status, last_error)
VALUES (1, 'line', 'encrypted:line_token_here', 'failed', 'Invalid Channel Access Token')
ON CONFLICT (tenant_id, platform) DO NOTHING;

-- 4. 為 tenant_id = 1 插入一個待處理的 Messenger 平台綁定
INSERT INTO platform_bindings (tenant_id, platform, status)
VALUES (1, 'messenger', 'pending')
ON CONFLICT (tenant_id, platform) DO NOTHING;

-- 5. 為 tenant_id = 1 插入一個已激活的 Zapier 整合
INSERT INTO external_integrations (tenant_id, service_name, api_key, config, is_active)
VALUES (1, 'zapier', 'encrypted:zapier_api_key', '{"triggers": ["new_lead", "new_sale"], "actions": ["send_slack_message"]}', TRUE)
ON CONFLICT DO NOTHING;

-- 6. 為 tenant_id = 1 插入一個未激活的 Slack 整合
INSERT INTO external_integrations (tenant_id, service_name, config, is_active)
VALUES (1, 'slack', '{"channel": "#sales-alerts"}', FALSE)
ON CONFLICT DO NOTHING;

-- 7. 更新用戶的最後活躍時間
UPDATE users SET last_active_at = NOW() - INTERVAL '1 day' WHERE id = 1;
UPDATE users SET last_active_at = NOW() - INTERVAL '3 day' WHERE id = 2;

-- End of Phase 3 Seed Data


