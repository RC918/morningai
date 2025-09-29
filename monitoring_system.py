#!/usr/bin/env python3
"""
服務監控系統
實現每小時健檢、告警門檻檢測和數據收集功能
"""

import requests
import json
import time
import datetime
import logging
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque
import statistics

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class HealthCheckResult:
    """健康檢查結果"""
    endpoint: str
    status_code: int
    latency_ms: float
    timestamp: datetime.datetime
    error_message: Optional[str] = None
    success: bool = True

@dataclass
class AlertConfig:
    """告警配置"""
    error_rate_warning_threshold: float = 0.01  # 1%
    error_rate_critical_threshold: float = 0.05  # 5%
    latency_warning_threshold: float = 500.0  # 500ms
    consecutive_5xx_critical: int = 3
    consecutive_health_fail_critical: int = 2
    window_minutes: int = 10

class MonitoringSystem:
    """監控系統主類"""
    
    def __init__(self, base_url: str, auth_token: str = None):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.alert_config = AlertConfig()
        
        # 使用 deque 來維護滑動窗口數據
        self.health_results = deque(maxlen=1000)
        self.error_counts = deque(maxlen=100)
        self.latency_measurements = deque(maxlen=100)
        
        # 連續失敗計數器
        self.consecutive_5xx_count = 0
        self.consecutive_health_fail_count = 0
        
    def check_endpoint(self, endpoint: str, method: str = 'GET', 
                      headers: Dict = None, json_data: Dict = None, 
                      dry_run: bool = False) -> HealthCheckResult:
        """檢查單個端點"""
        url = f"{self.base_url}{endpoint}"
        
        if dry_run:
            logger.info(f"[DRY RUN] Would send {method} request to {url}")
            return HealthCheckResult(
                endpoint=endpoint,
                status_code=200,
                latency_ms=0,
                timestamp=datetime.datetime.now(),
                success=True
            )
        
        try:
            start_time = time.time()
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=json_data, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            result = HealthCheckResult(
                endpoint=endpoint,
                status_code=response.status_code,
                latency_ms=latency_ms,
                timestamp=datetime.datetime.now(),
                success=200 <= response.status_code < 400
            )
            
            logger.info(f"{endpoint}: {response.status_code} ({latency_ms:.2f}ms)")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking {endpoint}: {str(e)}")
            return HealthCheckResult(
                endpoint=endpoint,
                status_code=-1,
                latency_ms=-1,
                timestamp=datetime.datetime.now(),
                error_message=str(e),
                success=False
            )
    
    def run_health_checks(self) -> List[HealthCheckResult]:
        """執行所有健康檢查"""
        results = []
        
        # 檢查 /health
        results.append(self.check_endpoint('/health'))
        
        # 檢查 /healthz
        results.append(self.check_endpoint('/healthz'))
        
        # 儲存結果
        for result in results:
            self.health_results.append(result)
        
        return results
    
    def calculate_error_rate(self, window_minutes: int = 10) -> float:
        """計算指定時間窗口內的錯誤率"""
        cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes=window_minutes)
        
        recent_results = [r for r in self.health_results if r.timestamp >= cutoff_time]
        
        if not recent_results:
            return 0.0
        
        error_count = sum(1 for r in recent_results if not r.success or r.status_code >= 400)
        total_count = len(recent_results)
        
        return error_count / total_count if total_count > 0 else 0.0
    
    def calculate_p95_latency(self, window_minutes: int = 10) -> float:
        """計算指定時間窗口內的 P95 延遲"""
        cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes=window_minutes)
        
        recent_results = [r for r in self.health_results 
                         if r.timestamp >= cutoff_time and r.latency_ms > 0]
        
        if not recent_results:
            return 0.0
        
        latencies = [r.latency_ms for r in recent_results]
        return statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
    
    def check_alerts(self) -> List[Dict]:
        """檢查告警條件"""
        alerts = []
        
        # 檢查錯誤率
        error_rate = self.calculate_error_rate(self.alert_config.window_minutes)
        
        if error_rate >= self.alert_config.error_rate_critical_threshold:
            alerts.append({
                'level': 'CRITICAL',
                'type': 'ERROR_RATE',
                'message': f'錯誤率達到 {error_rate:.2%}，超過臨界值 {self.alert_config.error_rate_critical_threshold:.2%}',
                'value': error_rate,
                'threshold': self.alert_config.error_rate_critical_threshold
            })
        elif error_rate >= self.alert_config.error_rate_warning_threshold:
            alerts.append({
                'level': 'WARNING',
                'type': 'ERROR_RATE',
                'message': f'錯誤率達到 {error_rate:.2%}，超過警告值 {self.alert_config.error_rate_warning_threshold:.2%}',
                'value': error_rate,
                'threshold': self.alert_config.error_rate_warning_threshold
            })
        
        # 檢查 P95 延遲
        p95_latency = self.calculate_p95_latency(self.alert_config.window_minutes)
        
        if p95_latency > self.alert_config.latency_warning_threshold:
            alerts.append({
                'level': 'WARNING',
                'type': 'LATENCY',
                'message': f'P95 延遲達到 {p95_latency:.2f}ms，超過警告值 {self.alert_config.latency_warning_threshold}ms',
                'value': p95_latency,
                'threshold': self.alert_config.latency_warning_threshold
            })
        
        return alerts
    
    def send_slack_alert(self, alerts: List[Dict], webhook_url: str):
        """發送 Slack 告警"""
        if not alerts:
            return
        
        color_map = {
            'CRITICAL': '#FF0000',
            'WARNING': '#FFA500'
        }
        
        attachments = []
        for alert in alerts:
            attachments.append({
                'color': color_map.get(alert['level'], '#808080'),
                'title': f"{alert['level']}: {alert['type']}",
                'text': alert['message'],
                'timestamp': int(time.time())
            })
        
        payload = {
            'text': f'🚨 Morning AI 服務監控告警 ({len(alerts)} 個)',
            'attachments': attachments
        }
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"Successfully sent {len(alerts)} alerts to Slack")
            else:
                logger.error(f"Failed to send Slack alert: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending Slack alert: {str(e)}")
    
    def generate_daily_report(self) -> Dict:
        """生成每日報告數據"""
        now = datetime.datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 獲取今日數據
        today_results = [r for r in self.health_results if r.timestamp >= start_of_day]
        
        if not today_results:
            return {}
        
        # 計算統計數據
        total_requests = len(today_results)
        error_count = sum(1 for r in today_results if not r.success or r.status_code >= 400)
        error_rate = error_count / total_requests if total_requests > 0 else 0
        
        successful_results = [r for r in today_results if r.success and r.latency_ms > 0]
        if successful_results:
            latencies = [r.latency_ms for r in successful_results]
            p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
            avg_latency = statistics.mean(latencies)
        else:
            p95_latency = 0
            avg_latency = 0
        
        return {
            'date': now.strftime('%Y-%m-%d'),
            'total_requests': total_requests,
            'error_count': error_count,
            'error_rate': error_rate,
            'p95_latency': p95_latency,
            'avg_latency': avg_latency,
            'alerts_triggered': len(self.check_alerts())
        }
    
    def save_monitoring_data(self, filename: str = None):
        """儲存監控數據到文件"""
        if filename is None:
            filename = f"monitoring_data_{datetime.datetime.now().strftime('%Y%m%d')}.json"
        
        data = {
            'timestamp': datetime.datetime.now().isoformat(),
            'health_results': [
                {
                    'endpoint': r.endpoint,
                    'status_code': r.status_code,
                    'latency_ms': r.latency_ms,
                    'timestamp': r.timestamp.isoformat(),
                    'success': r.success,
                    'error_message': r.error_message
                }
                for r in self.health_results
            ],
            'daily_report': self.generate_daily_report()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Monitoring data saved to {filename}")

def main():
    """主函數"""
    # 從環境變數讀取配置
    base_url = os.getenv('MONITOR_BASE_URL', 'https://morningai-backend-v2.onrender.com')
    auth_token = os.getenv('MONITOR_AUTH_TOKEN')
    slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
    
    # 初始化監控系統
    monitor = MonitoringSystem(base_url, auth_token)
    
    logger.info("Starting Morning AI monitoring system...")
    
    try:
        while True:
            # 執行健康檢查
            results = monitor.run_health_checks()
            
            # 檢查告警
            alerts = monitor.check_alerts()
            
            if alerts:
                logger.warning(f"Detected {len(alerts)} alerts")
                for alert in alerts:
                    logger.warning(f"{alert['level']}: {alert['message']}")
                
                # 發送 Slack 告警
                if slack_webhook:
                    monitor.send_slack_alert(alerts, slack_webhook)
            
            # 儲存監控數據
            monitor.save_monitoring_data()
            
            # 等待一小時
            logger.info("Waiting for next check cycle (1 hour)...")
            time.sleep(3600)  # 3600 秒 = 1 小時
            
    except KeyboardInterrupt:
        logger.info("Monitoring system stopped by user")
    except Exception as e:
        logger.error(f"Monitoring system error: {str(e)}")

if __name__ == "__main__":
    main()
