#!/usr/bin/env python3
"""
每日監控報告生成器
根據監控數據生成每日簡報，符合規範要求的格式
"""

import json
import datetime
import os
import statistics
from typing import Dict, List, Optional
import requests
from dataclasses import dataclass

@dataclass
class DailyReportData:
    """每日報告數據結構"""
    date: str
    health_status: Dict[str, Dict]
    performance_metrics: Dict
    resource_status: Dict
    alerts_summary: List[Dict]
    summary_text: str

class DailyReportGenerator:
    """每日報告生成器"""
    
    def __init__(self, data_dir: str = "data", reports_dir: str = "reports"):
        self.data_dir = data_dir
        self.reports_dir = reports_dir
        
        # 確保目錄存在
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)
    
    def load_monitoring_data(self, date: str = None) -> Dict:
        """載入指定日期的監控數據"""
        if date is None:
            date = datetime.datetime.now().strftime('%Y%m%d')
        
        filename = f"{self.data_dir}/monitoring_data_{date}.json"
        
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Monitoring data file not found: {filename}")
        
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def analyze_health_status(self, health_results: List[Dict]) -> Dict[str, Dict]:
        """分析健康狀態"""
        endpoints = ['/health', '/healthz', '/openapi.json']
        status_summary = {}
        
        for endpoint in endpoints:
            endpoint_results = [r for r in health_results if r['endpoint'] == endpoint]
            
            if not endpoint_results:
                status_summary[endpoint] = {
                    'status_code': 'N/A',
                    'avg_latency': 0,
                    'success_rate': 0,
                    'note': '無數據'
                }
                continue
            
            # 計算統計數據
            successful_results = [r for r in endpoint_results if r['success']]
            success_rate = len(successful_results) / len(endpoint_results) if endpoint_results else 0
            
            if successful_results:
                avg_latency = statistics.mean([r['latency_ms'] for r in successful_results if r['latency_ms'] > 0])
                most_common_status = statistics.mode([r['status_code'] for r in successful_results])
            else:
                avg_latency = 0
                most_common_status = 'ERROR'
            
            # 特殊處理 openapi.json
            note = ""
            if endpoint == '/openapi.json' and successful_results:
                # 這裡可以添加檢查 /auth/ 和 /referral/ 路由的邏輯
                note = "需檢查 /auth/ 和 /referral/ 路由"
            
            status_summary[endpoint] = {
                'status_code': most_common_status,
                'avg_latency': round(avg_latency, 2),
                'success_rate': round(success_rate * 100, 2),
                'note': note
            }
        
        return status_summary
    
    def analyze_performance_metrics(self, health_results: List[Dict]) -> Dict:
        """分析效能指標"""
        if not health_results:
            return {
                'p95_latency': 0,
                'error_rate': 0,
                'peak_5xx_time': '無'
            }
        
        # 計算 P95 延遲
        successful_results = [r for r in health_results if r['success'] and r['latency_ms'] > 0]
        if successful_results:
            latencies = [r['latency_ms'] for r in successful_results]
            p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
        else:
            p95_latency = 0
        
        # 計算錯誤率
        error_count = sum(1 for r in health_results if not r['success'] or r['status_code'] >= 400)
        error_rate = (error_count / len(health_results)) * 100 if health_results else 0
        
        # 找出 5xx 峰值時段
        hour_5xx_counts = {}
        for result in health_results:
            if result['status_code'] >= 500:
                timestamp = datetime.datetime.fromisoformat(result['timestamp'])
                hour = timestamp.hour
                hour_5xx_counts[hour] = hour_5xx_counts.get(hour, 0) + 1
        
        if hour_5xx_counts:
            peak_hour = max(hour_5xx_counts.items(), key=lambda x: x[1])[0]
            peak_5xx_time = f"{peak_hour:02d}:00-{peak_hour+1:02d}:00"
        else:
            peak_5xx_time = "無"
        
        return {
            'p95_latency': round(p95_latency, 2),
            'error_rate': round(error_rate, 2),
            'peak_5xx_time': peak_5xx_time
        }
    
    def get_resource_status(self) -> Dict:
        """獲取資源狀態（模擬數據，實際需要連接真實服務）"""
        return {
            'render_status': '需手動檢查 Render Events',
            'db_connections': '需連接資料庫獲取',
            'db_errors': '需連接資料庫獲取'
        }
    
    def generate_summary_text(self, report_data: DailyReportData) -> str:
        """生成摘要文字（≦10行）"""
        lines = []
        
        # 服務健康狀態
        health_ok = all(status['success_rate'] > 95 for status in report_data.health_status.values())
        if health_ok:
            lines.append("✅ 所有健康檢查端點運行正常")
        else:
            lines.append("⚠️ 部分健康檢查端點存在問題")
        
        # 效能指標
        perf = report_data.performance_metrics
        if perf['error_rate'] < 1:
            lines.append(f"✅ 錯誤率 {perf['error_rate']:.2f}% (< 1%)")
        else:
            lines.append(f"⚠️ 錯誤率 {perf['error_rate']:.2f}% (≥ 1%)")
        
        if perf['p95_latency'] < 500:
            lines.append(f"✅ P95 延遲 {perf['p95_latency']:.2f}ms (< 500ms)")
        else:
            lines.append(f"⚠️ P95 延遲 {perf['p95_latency']:.2f}ms (≥ 500ms)")
        
        # 告警情況
        if report_data.alerts_summary:
            lines.append(f"🚨 今日觸發 {len(report_data.alerts_summary)} 個告警")
        else:
            lines.append("✅ 今日無告警觸發")
        
        # 5xx 峰值
        if perf['peak_5xx_time'] != "無":
            lines.append(f"📊 5xx 錯誤峰值時段: {perf['peak_5xx_time']}")
        
        # 資源狀態提醒
        lines.append("📋 請檢查 Render Events 截圖和資料庫連線狀態")
        
        return "\n".join(lines[:10])  # 限制在 10 行內
    
    def generate_markdown_report(self, report_data: DailyReportData) -> str:
        """生成 Markdown 格式的報告"""
        md_content = f"""# 每日監控報告 - {report_data.date}

## 總結 (≦10 行)

{report_data.summary_text}

## 服務健康

| 端點 | 狀態碼 | 平均回應時間 (ms) | 成功率 (%) | 備註 |
|---|---|---|---|---|
"""
        
        for endpoint, status in report_data.health_status.items():
            md_content += f"| `{endpoint}` | {status['status_code']} | {status['avg_latency']} | {status['success_rate']} | {status['note']} |\n"
        
        md_content += f"""
## 效能與錯誤

| 指標 | 數值 |
|---|---|
| P95 延遲 | {report_data.performance_metrics['p95_latency']} ms |
| 錯誤率 (4xx/5xx) | {report_data.performance_metrics['error_rate']}% |
| 5xx 峰值時段 (過去 24h) | {report_data.performance_metrics['peak_5xx_time']} |

## 資源與依賴

*   **Render 服務狀態**: {report_data.resource_status['render_status']}
*   **資料庫連線健康度**:
    *   連線數: {report_data.resource_status['db_connections']}
    *   錯誤數: {report_data.resource_status['db_errors']}

## 監控與告警

"""
        
        if report_data.alerts_summary:
            md_content += f"今日共觸發 {len(report_data.alerts_summary)} 個告警:\n\n"
            for i, alert in enumerate(report_data.alerts_summary, 1):
                md_content += f"{i}. **{alert.get('level', 'UNKNOWN')}**: {alert.get('message', 'No message')}\n"
        else:
            md_content += "今日無告警事件。\n"
        
        md_content += f"""
---

**報告生成時間**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**數據來源**: 7天觀察期監控系統
"""
        
        return md_content
    
    def generate_slack_message(self, report_data: DailyReportData) -> Dict:
        """生成 Slack 訊息格式"""
        # 判斷整體狀態
        health_ok = all(status['success_rate'] > 95 for status in report_data.health_status.values())
        perf_ok = (report_data.performance_metrics['error_rate'] < 1 and 
                  report_data.performance_metrics['p95_latency'] < 500)
        no_alerts = len(report_data.alerts_summary) == 0
        
        if health_ok and perf_ok and no_alerts:
            color = "#36a64f"  # 綠色
            status_emoji = "✅"
        elif not no_alerts:
            color = "#ff0000"  # 紅色
            status_emoji = "🚨"
        else:
            color = "#ffaa00"  # 橙色
            status_emoji = "⚠️"
        
        return {
            "text": f"{status_emoji} 每日監控報告 - {report_data.date}",
            "attachments": [
                {
                    "color": color,
                    "fields": [
                        {
                            "title": "服務健康",
                            "value": f"健康檢查: {'✅ 正常' if health_ok else '⚠️ 異常'}",
                            "short": True
                        },
                        {
                            "title": "效能指標",
                            "value": f"P95: {report_data.performance_metrics['p95_latency']}ms | 錯誤率: {report_data.performance_metrics['error_rate']}%",
                            "short": True
                        },
                        {
                            "title": "告警狀況",
                            "value": f"今日告警: {len(report_data.alerts_summary)} 個",
                            "short": True
                        },
                        {
                            "title": "摘要",
                            "value": report_data.summary_text.replace('\n', ' | '),
                            "short": False
                        }
                    ],
                    "footer": "7天觀察期監控系統",
                    "ts": int(datetime.datetime.now().timestamp())
                }
            ]
        }
    
    def generate_report(self, date: str = None) -> DailyReportData:
        """生成每日報告"""
        if date is None:
            date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # 載入監控數據
        data_date = date.replace('-', '')
        try:
            monitoring_data = self.load_monitoring_data(data_date)
        except FileNotFoundError:
            # 如果沒有數據，創建空報告
            monitoring_data = {'health_results': [], 'daily_report': {}}
        
        health_results = monitoring_data.get('health_results', [])
        
        # 分析數據
        health_status = self.analyze_health_status(health_results)
        performance_metrics = self.analyze_performance_metrics(health_results)
        resource_status = self.get_resource_status()
        alerts_summary = []  # 這裡可以從監控數據中提取告警信息
        
        # 創建報告數據
        report_data = DailyReportData(
            date=date,
            health_status=health_status,
            performance_metrics=performance_metrics,
            resource_status=resource_status,
            alerts_summary=alerts_summary,
            summary_text=""
        )
        
        # 生成摘要文字
        report_data.summary_text = self.generate_summary_text(report_data)
        
        return report_data
    
    def save_report(self, report_data: DailyReportData, formats: List[str] = ['markdown', 'json']):
        """儲存報告到文件"""
        day_num = (datetime.datetime.strptime(report_data.date, '%Y-%m-%d') - 
                  datetime.datetime(2024, 1, 1)).days + 1
        
        base_filename = f"7天觀察期監控日誌_Day{day_num}_{report_data.date}"
        
        if 'markdown' in formats:
            md_content = self.generate_markdown_report(report_data)
            md_filename = f"{self.reports_dir}/{base_filename}.md"
            with open(md_filename, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f"Markdown report saved: {md_filename}")
        
        if 'json' in formats:
            json_filename = f"{self.reports_dir}/{base_filename}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'date': report_data.date,
                    'health_status': report_data.health_status,
                    'performance_metrics': report_data.performance_metrics,
                    'resource_status': report_data.resource_status,
                    'alerts_summary': report_data.alerts_summary,
                    'summary_text': report_data.summary_text
                }, f, ensure_ascii=False, indent=2)
            print(f"JSON report saved: {json_filename}")
    
    def send_to_slack(self, report_data: DailyReportData, webhook_url: str):
        """發送報告到 Slack"""
        message = self.generate_slack_message(report_data)
        
        try:
            response = requests.post(webhook_url, json=message, timeout=10)
            if response.status_code == 200:
                print("Report sent to Slack successfully")
            else:
                print(f"Failed to send report to Slack: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending report to Slack: {str(e)}")

def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='生成每日監控報告')
    parser.add_argument('--date', help='報告日期 (YYYY-MM-DD)', default=None)
    parser.add_argument('--slack-webhook', help='Slack Webhook URL', default=None)
    parser.add_argument('--format', choices=['markdown', 'json', 'both'], default='both', help='報告格式')
    
    args = parser.parse_args()
    
    # 從環境變數獲取 Slack Webhook
    slack_webhook = args.slack_webhook or os.getenv('SLACK_WEBHOOK_URL')
    
    # 創建報告生成器
    generator = DailyReportGenerator()
    
    try:
        # 生成報告
        report_data = generator.generate_report(args.date)
        
        # 儲存報告
        formats = ['markdown', 'json'] if args.format == 'both' else [args.format]
        generator.save_report(report_data, formats)
        
        # 發送到 Slack
        if slack_webhook:
            generator.send_to_slack(report_data, slack_webhook)
        else:
            print("No Slack webhook URL provided, skipping Slack notification")
        
        print(f"Daily report generated successfully for {report_data.date}")
        
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

