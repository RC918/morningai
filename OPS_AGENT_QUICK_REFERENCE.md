# Ops Agent 快速參考指南

**最後更新**: 2025-10-19  
**狀態**: ✅ 生產就緒

---

## 🚀 快速開始

### 1. 運行交互式演示

```bash
cd /home/ubuntu/repos/morningai
python /home/ubuntu/ops_agent_demo.py
```

選項:
- `1` - 檢查 Vercel 部署狀態
- `2` - 系統健康檢查
- `3` - 日誌分析
- `4` - 告警管理
- `5` - 完整健康檢查
- `0` - 運行所有演示

### 2. 運行測試

```bash
# 運行所有測試
python -m pytest agents/ops_agent/tests/ -v

# 運行特定測試
python -m pytest agents/ops_agent/tests/test_deployment_tool.py -v

# 查看覆蓋率
python -m pytest agents/ops_agent/tests/ --cov=agents/ops_agent
```

---

## 📊 常用命令

### 部署監控

```python
from agents.ops_agent.tools.deployment_tool import DeploymentTool

# 初始化
tool = DeploymentTool(
    token=os.getenv('VERCEL_TOKEN_NEW'),
    team_id=None
)

# 列出最近部署
result = await tool.list_deployments(limit=10)

# 獲取特定部署詳情
result = await tool.get_deployment_details(deployment_id)

# 取消部署
result = await tool.cancel_deployment(deployment_id)
```

### 系統監控

```python
from agents.ops_agent.tools.monitoring_tool import MonitoringTool

tool = MonitoringTool()

# 獲取系統指標
result = await tool.get_system_metrics()

# CPU: result['metrics']['cpu']['percent']
# 記憶體: result['metrics']['memory']['percent']
# 磁碟: result['metrics']['disk']['percent']

# 執行健康檢查
result = await tool.health_check([
    {'name': 'api', 'url': 'https://api.example.com/health'},
    {'name': 'db', 'url': 'https://db.example.com/health'}
])
```

### 日誌分析

```python
from agents.ops_agent.tools.log_analysis_tool import LogAnalysisTool

tool = LogAnalysisTool()

# 搜索日誌
result = await tool.search_logs(
    query="error",
    time_range="1h",
    severity="error"
)

# 分析錯誤模式
result = await tool.analyze_error_patterns(time_range="24h")

# 檢測異常
result = await tool.detect_anomalies(
    metric="cpu_percent",
    time_range="1h"
)
```

### 告警管理

```python
from agents.ops_agent.tools.alert_management_tool import AlertManagementTool

tool = AlertManagementTool()

# 創建告警規則
result = await tool.create_alert_rule(
    name="high_cpu_alert",
    condition="cpu_percent > 80",
    severity="medium",
    channels=["email", "slack"]
)

# 觸發告警
result = await tool.trigger_alert(
    rule_id="rule_123",
    details={"cpu": 85, "threshold": 80}
)

# 列出所有告警
result = await tool.list_alerts(status="active")

# 確認告警
result = await tool.acknowledge_alert(alert_id)

# 解決告警
result = await tool.resolve_alert(alert_id)
```

---

## 🔧 日常運維任務

### 每日檢查

```bash
# 1. 檢查系統健康
python /home/ubuntu/ops_agent_demo.py
# 選擇 "2" 或 "5"

# 2. 查看最新部署
python /home/ubuntu/ops_agent_demo.py
# 選擇 "1"

# 3. 檢查錯誤日誌
python /home/ubuntu/ops_agent_demo.py
# 選擇 "3"
```

### 故障排除

#### CPU 使用率過高

```python
# 1. 檢查系統指標
tool = MonitoringTool()
metrics = await tool.get_system_metrics()
cpu_percent = metrics['metrics']['cpu']['percent']

# 2. 分析日誌找原因
log_tool = LogAnalysisTool()
errors = await log_tool.analyze_error_patterns(time_range="1h")

# 3. 創建告警
alert_tool = AlertManagementTool()
await alert_tool.create_alert_rule(
    name="high_cpu",
    condition="cpu_percent > 80",
    severity="high",
    channels=["email"]
)
```

#### 部署失敗

```python
# 1. 獲取部署詳情
tool = DeploymentTool(token=os.getenv('VERCEL_TOKEN_NEW'))
deployments = await tool.list_deployments(limit=5)

# 2. 查看失敗的部署
for dep in deployments['deployments']:
    if dep['state'] == 'ERROR':
        details = await tool.get_deployment_details(dep['id'])
        # 檢查錯誤信息

# 3. 回滾到上一個成功部署
# (手動在 Vercel dashboard 操作)
```

#### 記憶體洩漏

```python
# 1. 監控記憶體趨勢
tool = MonitoringTool()
for i in range(10):
    metrics = await tool.get_system_metrics()
    print(f"Memory: {metrics['metrics']['memory']['percent']}%")
    await asyncio.sleep(60)  # 每分鐘檢查

# 2. 檢測異常
log_tool = LogAnalysisTool()
anomalies = await log_tool.detect_anomalies(
    metric="memory_percent",
    time_range="1h"
)
```

---

## 📋 運維清單

### 每日任務（5 分鐘）

- [ ] 檢查系統健康狀態
- [ ] 查看最新部署
- [ ] 確認所有服務正常運行
- [ ] 檢查是否有新告警

### 每週任務（15 分鐘）

- [ ] 審查錯誤日誌
- [ ] 檢查資源使用趨勢
- [ ] 更新告警規則
- [ ] 測試告警通道

### 每月任務（1 小時）

- [ ] 全面健康檢查
- [ ] 性能基準測試
- [ ] 清理舊日誌
- [ ] 更新文檔
- [ ] 審查安全設置

---

## 🚨 緊急事件處理

### P0 - 服務完全中斷

```bash
# 1. 檢查所有端點
curl https://morningai-morning-ai.vercel.app/health
curl https://morningai-sandbox-dev-agent.fly.dev/health
curl https://morningai-sandbox-ops-agent.fly.dev/health

# 2. 查看 Vercel 狀態
python /home/ubuntu/ops_agent_demo.py  # 選擇 1

# 3. 檢查系統資源
python /home/ubuntu/ops_agent_demo.py  # 選擇 5

# 4. 查看錯誤日誌
python /home/ubuntu/ops_agent_demo.py  # 選擇 3

# 5. 必要時回滾部署（Vercel dashboard）
```

### P1 - 性能下降

```python
# 執行完整診斷
from agents.ops_agent.tools.monitoring_tool import MonitoringTool
from agents.ops_agent.tools.log_analysis_tool import LogAnalysisTool

# 1. 系統指標
monitor = MonitoringTool()
metrics = await monitor.get_system_metrics()

# 2. 錯誤分析
logs = LogAnalysisTool()
errors = await logs.analyze_error_patterns(time_range="1h")

# 3. 異常檢測
anomalies = await logs.detect_anomalies(time_range="1h")
```

### P2 - 告警觸發

```python
# 查看和處理告警
from agents.ops_agent.tools.alert_management_tool import AlertManagementTool

tool = AlertManagementTool()

# 列出活動告警
alerts = await tool.list_alerts(status="active")

# 確認告警
for alert in alerts['alerts']:
    await tool.acknowledge_alert(alert['id'])
    
# 分析後解決
await tool.resolve_alert(alert_id)
```

---

## 📚 文檔資源

### 核心文檔

| 文檔 | 路徑 | 用途 |
|------|------|------|
| 運維手冊 | `agents/ops_agent/OPERATIONS_RUNBOOK.md` | 完整運維程序 |
| 驗證報告 | `agents/ops_agent/PRODUCTION_VALIDATION_REPORT.md` | 生產驗證結果 |
| 通知設置 | `agents/ops_agent/NOTIFICATION_SETUP_GUIDE.md` | Email/Slack 配置 |
| API 文檔 | `agents/ops_agent/README.md` | API 參考 |

### 查看文檔

```bash
# 運維手冊
cat agents/ops_agent/OPERATIONS_RUNBOOK.md

# 驗證報告
cat agents/ops_agent/PRODUCTION_VALIDATION_REPORT.md

# 通知配置
cat agents/ops_agent/NOTIFICATION_SETUP_GUIDE.md
```

---

## 🔑 環境變數

### 必需

```bash
# Vercel
export VERCEL_TOKEN_NEW="your-vercel-token"

# Database (如需)
export DATABASE_URL_2="your-supabase-url"
export SUPABASE_URL="your-supabase-url"
export SUPABASE_SERVICE_ROLE_KEY="your-key"
```

### 可選（通知）

```bash
# Email (Mailtrap)
export MAILTRAP_SENDING_TOKEN="your-token"

# Slack
export SLACK_WEBHOOK_URL="your-webhook-url"

# SMTP
export SMTP_HOST="smtp.example.com"
export SMTP_PORT="587"
export SMTP_USER="your-user"
export SMTP_PASSWORD="your-password"
```

---

## 💡 最佳實踐

### 1. 定期監控

```python
# 設置定期健康檢查（cron job）
# 每 5 分鐘檢查一次

*/5 * * * * cd /home/ubuntu/repos/morningai && python -c "
import asyncio
from agents.ops_agent.tools.monitoring_tool import MonitoringTool
async def check():
    tool = MonitoringTool()
    result = await tool.get_system_metrics()
    metrics = result['metrics']
    if metrics['cpu']['percent'] > 80:
        print('WARNING: High CPU')
    if metrics['memory']['percent'] > 85:
        print('WARNING: High Memory')
asyncio.run(check())
"
```

### 2. 告警分級

- **Critical (P0)**: 服務中斷，立即通知
- **High (P1)**: 性能嚴重下降，1 小時內響應
- **Medium (P2)**: 異常但可用，當日處理
- **Low (P3)**: 優化建議，定期審查

### 3. 日誌保留

- **即時日誌**: 7 天
- **壓縮日誌**: 30 天
- **歸檔日誌**: 90 天
- **審計日誌**: 1 年

### 4. 備份策略

- **數據庫**: 每日自動備份（Supabase）
- **配置文件**: Git 版本控制
- **關鍵日誌**: 異地備份

---

## 🎯 快速命令參考

```bash
# 運行演示
python /home/ubuntu/ops_agent_demo.py

# 運行測試
python -m pytest agents/ops_agent/tests/ -v

# 查看健康
curl https://morningai-sandbox-ops-agent.fly.dev/health

# 查看文檔
cat agents/ops_agent/OPERATIONS_RUNBOOK.md

# 檢查環境變數
echo $VERCEL_TOKEN_NEW

# 清理日誌
find /var/log -name "*.log" -mtime +7 -delete
```

---

## 📞 支持

### 遇到問題？

1. **查看文檔**: 先查閱 `OPERATIONS_RUNBOOK.md`
2. **檢查日誌**: 使用日誌分析工具
3. **運行測試**: 確認工具正常運行
4. **創建 Issue**: GitHub Issues

### 緊急聯絡

- **GitHub**: @RC918
- **Email**: ryan2939z@gmail.com
- **Devin Session**: https://app.devin.ai/sessions/a6c88268b1df401ea9edd10c29bacd41

---

## ✅ 檢查清單

### 準備使用？

- [x] PR #460 已合併
- [x] 所有測試通過 (110/110)
- [x] 環境變數已配置
- [x] 文檔已閱讀
- [ ] Email 通知已配置（可選）
- [ ] Slack webhook 已配置（可選）
- [x] 演示已運行成功

### 開始使用！

```bash
# 運行第一次健康檢查
python /home/ubuntu/ops_agent_demo.py
# 選擇 "5" - 完整健康檢查
```

---

**🎉 Ops Agent 已準備就緒！**

立即開始使用，讓運維更輕鬆！
