#!/usr/bin/env python3
"""
監控系統配置文件
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class MonitoringConfig:
    """監控配置類"""
    
    # 服務配置
    base_url: str = "http://localhost:8000"
    auth_token: Optional[str] = None
    
    # 告警閾值配置
    error_rate_warning_threshold: float = 0.01  # 1%
    error_rate_critical_threshold: float = 0.05  # 5%
    latency_warning_threshold: float = 500.0  # 500ms
    consecutive_5xx_critical: int = 3
    consecutive_health_fail_critical: int = 2
    window_minutes: int = 10
    
    # Slack 配置
    slack_webhook_url: Optional[str] = None
    slack_channel: str = "#morningai-alerts"
    
    # 檢查間隔（秒）
    check_interval: int = 3600  # 1 小時
    
    # 日誌配置
    log_level: str = "INFO"
    log_file: str = "monitoring.log"
    
    # 數據儲存配置
    data_retention_days: int = 30
    
    @classmethod
    def from_env(cls) -> 'MonitoringConfig':
        """從環境變數創建配置"""
        return cls(
            base_url=os.getenv('MONITOR_BASE_URL', cls.base_url),
            auth_token=os.getenv('MONITOR_AUTH_TOKEN'),
            error_rate_warning_threshold=float(os.getenv('ERROR_RATE_WARNING', cls.error_rate_warning_threshold)),
            error_rate_critical_threshold=float(os.getenv('ERROR_RATE_CRITICAL', cls.error_rate_critical_threshold)),
            latency_warning_threshold=float(os.getenv('LATENCY_WARNING', cls.latency_warning_threshold)),
            consecutive_5xx_critical=int(os.getenv('CONSECUTIVE_5XX_CRITICAL', cls.consecutive_5xx_critical)),
            consecutive_health_fail_critical=int(os.getenv('HEALTH_FAIL_CRITICAL', cls.consecutive_health_fail_critical)),
            window_minutes=int(os.getenv('WINDOW_MINUTES', cls.window_minutes)),
            slack_webhook_url=os.getenv('SLACK_WEBHOOK_URL'),
            slack_channel=os.getenv('SLACK_CHANNEL', cls.slack_channel),
            check_interval=int(os.getenv('CHECK_INTERVAL', cls.check_interval)),
            log_level=os.getenv('LOG_LEVEL', cls.log_level),
            log_file=os.getenv('LOG_FILE', cls.log_file),
            data_retention_days=int(os.getenv('DATA_RETENTION_DAYS', cls.data_retention_days))
        )
    
    def to_env_file(self, filename: str = '.env'):
        """將配置寫入環境變數文件"""
        with open(filename, 'w') as f:
            f.write(f"MONITOR_BASE_URL={self.base_url}\n")
            if self.auth_token:
                f.write(f"MONITOR_AUTH_TOKEN={self.auth_token}\n")
            f.write(f"ERROR_RATE_WARNING={self.error_rate_warning_threshold}\n")
            f.write(f"ERROR_RATE_CRITICAL={self.error_rate_critical_threshold}\n")
            f.write(f"LATENCY_WARNING={self.latency_warning_threshold}\n")
            f.write(f"CONSECUTIVE_5XX_CRITICAL={self.consecutive_5xx_critical}\n")
            f.write(f"HEALTH_FAIL_CRITICAL={self.consecutive_health_fail_critical}\n")
            f.write(f"WINDOW_MINUTES={self.window_minutes}\n")
            if self.slack_webhook_url:
                f.write(f"SLACK_WEBHOOK_URL={self.slack_webhook_url}\n")
            f.write(f"SLACK_CHANNEL={self.slack_channel}\n")
            f.write(f"CHECK_INTERVAL={self.check_interval}\n")
            f.write(f"LOG_LEVEL={self.log_level}\n")
            f.write(f"LOG_FILE={self.log_file}\n")
            f.write(f"DATA_RETENTION_DAYS={self.data_retention_days}\n")

# 預設配置實例
DEFAULT_CONFIG = MonitoringConfig()

if __name__ == "__main__":
    # 生成範例配置文件
    config = MonitoringConfig.from_env()
    config.to_env_file('.env.example')
    print("Generated .env.example file with default configuration")

