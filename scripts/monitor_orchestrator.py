#!/usr/bin/env python3
"""
Orchestrator API Monitoring Script

This script monitors the MorningAI Orchestrator API and sends alerts to Slack
when issues are detected.

Features:
- Health check monitoring
- Queue depth monitoring
- Response time tracking
- Automatic Slack notifications

Environment Variables:
- SLACK_WEBHOOK_URL: Slack webhook URL for sending alerts
- ORCHESTRATOR_API_URL: Base URL of the Orchestrator API
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from typing import Dict, Optional, Tuple


class OrchestratorMonitor:
    def __init__(self, api_url: str, slack_webhook_url: str):
        self.api_url = api_url.rstrip('/')
        self.slack_webhook_url = slack_webhook_url
        self.health_endpoint = f"{self.api_url}/health"
        self.stats_endpoint = f"{self.api_url}/stats"
        
        self.max_response_time = 5.0  # seconds
        self.max_queue_depth = 100
        self.critical_queue_depth = 500
    
    def send_slack_alert(self, message: str, severity: str = "warning") -> bool:
        """Send alert to Slack"""
        emoji_map = {
            "info": ":information_source:",
            "warning": ":warning:",
            "error": ":x:",
            "critical": ":rotating_light:",
            "success": ":white_check_mark:"
        }
        
        emoji = emoji_map.get(severity, ":bell:")
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        payload = {
            "text": f"{emoji} *Orchestrator Alert*",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{emoji} *Orchestrator Alert*\n\n{message}"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Time: {timestamp} | Severity: {severity.upper()}"
                        }
                    ]
                }
            ]
        }
        
        try:
            response = requests.post(
                self.slack_webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")
            return False
    
    def check_health(self) -> Tuple[bool, Optional[Dict], Optional[float]]:
        """Check API health endpoint"""
        try:
            start_time = time.time()
            response = requests.get(self.health_endpoint, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code != 200:
                return False, None, response_time
            
            data = response.json()
            return True, data, response_time
        except requests.exceptions.Timeout:
            return False, {"error": "timeout"}, None
        except requests.exceptions.ConnectionError:
            return False, {"error": "connection_error"}, None
        except Exception as e:
            return False, {"error": str(e)}, None
    
    def check_stats(self) -> Tuple[bool, Optional[Dict]]:
        """Check API stats endpoint"""
        try:
            response = requests.get(self.stats_endpoint, timeout=10)
            
            if response.status_code != 200:
                return False, None
            
            data = response.json()
            return True, data
        except Exception as e:
            print(f"Failed to check stats: {e}")
            return False, None
    
    def run_health_check(self) -> bool:
        """Run health check and send alerts if needed"""
        print(f"Checking health: {self.health_endpoint}")
        
        success, data, response_time = self.check_health()
        
        if not success:
            error_type = data.get("error", "unknown") if data else "unknown"
            
            if error_type == "timeout":
                message = (
                    f"*Health Check Timeout*\n"
                    f"The API did not respond within 10 seconds.\n"
                    f"URL: {self.health_endpoint}"
                )
                self.send_slack_alert(message, severity="critical")
                return False
            
            elif error_type == "connection_error":
                message = (
                    f"*Health Check Failed - Connection Error*\n"
                    f"Unable to connect to the API.\n"
                    f"URL: {self.health_endpoint}\n"
                    f"Possible causes: Service is down, network issue, or DNS problem"
                )
                self.send_slack_alert(message, severity="critical")
                return False
            
            else:
                message = (
                    f"*Health Check Failed*\n"
                    f"Error: {error_type}\n"
                    f"URL: {self.health_endpoint}"
                )
                self.send_slack_alert(message, severity="error")
                return False
        
        if response_time and response_time > self.max_response_time:
            message = (
                f"*Slow Response Time*\n"
                f"Response time: {response_time:.2f}s (threshold: {self.max_response_time}s)\n"
                f"URL: {self.health_endpoint}"
            )
            self.send_slack_alert(message, severity="warning")
        
        if data and data.get("redis") != "connected":
            message = (
                f"*Redis Connection Issue*\n"
                f"Redis status: {data.get('redis', 'unknown')}\n"
                f"This may affect task queue functionality."
            )
            self.send_slack_alert(message, severity="error")
            return False
        
        print(f"✓ Health check passed (response time: {response_time:.2f}s)")
        return True
    
    def run_queue_check(self) -> bool:
        """Run queue depth check and send alerts if needed"""
        print(f"Checking queue stats: {self.stats_endpoint}")
        
        success, data = self.check_stats()
        
        if not success:
            print("✗ Failed to check queue stats")
            return False
        
        queue_data = data.get("queue", {})
        pending_tasks = queue_data.get("pending_tasks", 0)
        processing_tasks = queue_data.get("processing_tasks", 0)
        total_tasks = queue_data.get("total_tasks", 0)
        
        print(f"✓ Queue stats: pending={pending_tasks}, processing={processing_tasks}, total={total_tasks}")
        
        if pending_tasks >= self.critical_queue_depth:
            message = (
                f"*CRITICAL: High Queue Depth*\n"
                f"Pending tasks: {pending_tasks} (critical threshold: {self.critical_queue_depth})\n"
                f"Processing tasks: {processing_tasks}\n"
                f"Total tasks: {total_tasks}\n\n"
                f"*Action Required:* Check agent health and capacity immediately."
            )
            self.send_slack_alert(message, severity="critical")
            return False
        
        elif pending_tasks >= self.max_queue_depth:
            message = (
                f"*WARNING: Elevated Queue Depth*\n"
                f"Pending tasks: {pending_tasks} (threshold: {self.max_queue_depth})\n"
                f"Processing tasks: {processing_tasks}\n"
                f"Total tasks: {total_tasks}\n\n"
                f"*Recommendation:* Monitor agent capacity."
            )
            self.send_slack_alert(message, severity="warning")
        
        return True
    
    def run(self) -> int:
        """Run all monitoring checks"""
        print(f"\n{'='*60}")
        print(f"Orchestrator Monitoring - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"{'='*60}\n")
        
        health_ok = self.run_health_check()
        queue_ok = self.run_queue_check()
        
        print(f"\n{'='*60}")
        
        if health_ok and queue_ok:
            print("✓ All checks passed")
            return 0
        else:
            print("✗ Some checks failed")
            return 1


def main():
    slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    api_url = os.environ.get("ORCHESTRATOR_API_URL", "https://morningai-orchestrator-api.onrender.com")
    
    if not slack_webhook_url:
        print("Error: SLACK_WEBHOOK_URL environment variable is not set")
        sys.exit(1)
    
    monitor = OrchestratorMonitor(api_url, slack_webhook_url)
    exit_code = monitor.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
