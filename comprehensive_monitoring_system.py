#!/usr/bin/env python3
"""
Comprehensive Monitoring and Alerting System
Implements monitoring for Phase 1-3 functionality with automated alerts
"""

import time
import json
import requests
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class ComprehensiveMonitoringSystem:
    def __init__(self, config_file='monitoring_config.json'):
        self.config = self.load_config(config_file)
        self.db_path = 'monitoring_data.db'
        self.init_database()
        self.running = False
        self.alert_thresholds = {
            'response_time_ms': 5000,
            'error_rate_threshold': 0.05,
            'consecutive_failures': 3,
            'uptime_threshold': 0.95
        }
        
    def load_config(self, config_file):
        """Load monitoring configuration"""
        default_config = {
            'base_url': 'http://127.0.0.1:10000',
            'check_interval_seconds': 60,
            'alert_email': 'admin@morningai.com',
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'endpoints_to_monitor': [
                '/health',
                '/healthz',
                '/api/agents/bind',
                '/api/bots/create',
                '/api/subscriptions/create',
                '/api/tenants/isolate'
            ]
        }
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                return {**default_config, **config}
        except FileNotFoundError:
            return default_config
    
    def init_database(self):
        """Initialize monitoring database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitoring_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT,
                status_code INTEGER,
                response_time_ms REAL,
                success BOOLEAN,
                error_message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT,
                severity TEXT,
                message TEXT,
                endpoint TEXT,
                resolved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT,
                metric_value REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def check_endpoint_health(self, endpoint):
        """Check health of a single endpoint"""
        url = f"{self.config['base_url']}{endpoint}"
        
        try:
            start_time = time.time()
            
            if endpoint in ['/api/agents/bind', '/api/bots/create', '/api/subscriptions/create', '/api/tenants/isolate']:
                test_data = self.get_test_data_for_endpoint(endpoint)
                response = requests.post(url, json=test_data, timeout=10)
            else:
                response = requests.get(url, timeout=10)
            
            response_time = (time.time() - start_time) * 1000
            
            result = {
                'endpoint': endpoint,
                'status_code': response.status_code,
                'response_time_ms': response_time,
                'success': response.status_code < 400,
                'error_message': None,
                'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
            }
            
        except Exception as e:
            result = {
                'endpoint': endpoint,
                'status_code': None,
                'response_time_ms': None,
                'success': False,
                'error_message': str(e),
                'response_data': None
            }
        
        self.save_monitoring_check(result)
        return result
    
    def get_test_data_for_endpoint(self, endpoint):
        """Get appropriate test data for POST endpoints"""
        test_data = {
            '/api/agents/bind': {
                'tenant_id': 'monitor_test',
                'platform_type': 'test_platform'
            },
            '/api/bots/create': {
                'bot_name': 'Monitor Test Bot',
                'tenant_id': 'monitor_test'
            },
            '/api/subscriptions/create': {
                'tenant_id': 'monitor_test',
                'plan_type': 'basic'
            },
            '/api/tenants/isolate': {
                'tenant_id': 'monitor_test',
                'isolation_level': 'schema'
            }
        }
        return test_data.get(endpoint, {})
    
    def save_monitoring_check(self, result):
        """Save monitoring check result to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO monitoring_checks 
            (endpoint, status_code, response_time_ms, success, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            result['endpoint'],
            result['status_code'],
            result['response_time_ms'],
            result['success'],
            result['error_message']
        ))
        
        conn.commit()
        conn.close()
    
    def check_alert_conditions(self, results):
        """Check if any alert conditions are met"""
        alerts = []
        
        for result in results:
            endpoint = result['endpoint']
            
            if result['response_time_ms'] and result['response_time_ms'] > self.alert_thresholds['response_time_ms']:
                alerts.append({
                    'type': 'high_response_time',
                    'severity': 'warning',
                    'message': f"High response time: {result['response_time_ms']:.2f}ms",
                    'endpoint': endpoint
                })
            
            if not result['success']:
                consecutive_failures = self.get_consecutive_failures(endpoint)
                if consecutive_failures >= self.alert_thresholds['consecutive_failures']:
                    alerts.append({
                        'type': 'consecutive_failures',
                        'severity': 'critical',
                        'message': f"Consecutive failures: {consecutive_failures}",
                        'endpoint': endpoint
                    })
        
        error_rate = self.calculate_error_rate()
        if error_rate > self.alert_thresholds['error_rate_threshold']:
            alerts.append({
                'type': 'high_error_rate',
                'severity': 'critical',
                'message': f"High error rate: {error_rate:.2%}",
                'endpoint': 'system'
            })
        
        return alerts
    
    def get_consecutive_failures(self, endpoint):
        """Get number of consecutive failures for an endpoint"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT success FROM monitoring_checks 
            WHERE endpoint = ? 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''', (endpoint,))
        
        results = cursor.fetchall()
        conn.close()
        
        consecutive_failures = 0
        for (success,) in results:
            if not success:
                consecutive_failures += 1
            else:
                break
        
        return consecutive_failures
    
    def calculate_error_rate(self, hours=1):
        """Calculate error rate over the last N hours"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_time = datetime.now() - timedelta(hours=hours)
        
        cursor.execute('''
            SELECT COUNT(*) as total, SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as errors
            FROM monitoring_checks 
            WHERE timestamp > ?
        ''', (since_time.isoformat(),))
        
        result = cursor.fetchone()
        conn.close()
        
        total, errors = result
        return (errors / total) if total > 0 else 0
    
    def save_alert(self, alert):
        """Save alert to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (alert_type, severity, message, endpoint)
            VALUES (?, ?, ?, ?)
        ''', (
            alert['type'],
            alert['severity'],
            alert['message'],
            alert['endpoint']
        ))
        
        conn.commit()
        conn.close()
    
    def send_alert_notification(self, alert):
        """Send alert notification (console for now, email in production)"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        severity_emoji = '🔴' if alert['severity'] == 'critical' else '🟡'
        
        message = f"{severity_emoji} ALERT [{alert['severity'].upper()}] {timestamp}"
        message += f"\nEndpoint: {alert['endpoint']}"
        message += f"\nType: {alert['type']}"
        message += f"\nMessage: {alert['message']}"
        
        print(message)
        print("-" * 50)
    
    def run_monitoring_cycle(self):
        """Run a single monitoring cycle"""
        print(f"🔍 Running monitoring cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = []
        for endpoint in self.config['endpoints_to_monitor']:
            result = self.check_endpoint_health(endpoint)
            results.append(result)
            
            status = "✅" if result['success'] else "❌"
            response_time = f" ({result['response_time_ms']:.2f}ms)" if result['response_time_ms'] else ""
            print(f"  {status} {endpoint}{response_time}")
        
        alerts = self.check_alert_conditions(results)
        for alert in alerts:
            self.save_alert(alert)
            self.send_alert_notification(alert)
        
        self.save_system_metrics(results)
        
        return results
    
    def save_system_metrics(self, results):
        """Save system-wide metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        successful_checks = sum(1 for r in results if r['success'])
        total_checks = len(results)
        uptime_percentage = (successful_checks / total_checks) if total_checks > 0 else 0
        
        avg_response_time = sum(r['response_time_ms'] for r in results if r['response_time_ms']) / len([r for r in results if r['response_time_ms']])
        
        metrics = [
            ('uptime_percentage', uptime_percentage),
            ('avg_response_time_ms', avg_response_time),
            ('total_endpoints', total_checks),
            ('successful_endpoints', successful_checks)
        ]
        
        for metric_name, metric_value in metrics:
            cursor.execute('''
                INSERT INTO system_metrics (metric_name, metric_value)
                VALUES (?, ?)
            ''', (metric_name, metric_value))
        
        conn.commit()
        conn.close()
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        self.running = True
        print("🚀 Starting comprehensive monitoring system...")
        print(f"📊 Monitoring {len(self.config['endpoints_to_monitor'])} endpoints")
        print(f"⏱️  Check interval: {self.config['check_interval_seconds']} seconds")
        print()
        
        while self.running:
            try:
                self.run_monitoring_cycle()
                time.sleep(self.config['check_interval_seconds'])
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                time.sleep(self.config['check_interval_seconds'])
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
    
    def get_monitoring_report(self, hours=24):
        """Generate monitoring report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_time = datetime.now() - timedelta(hours=hours)
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_checks,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_checks,
                AVG(response_time_ms) as avg_response_time,
                MAX(response_time_ms) as max_response_time
            FROM monitoring_checks 
            WHERE timestamp > ?
        ''', (since_time.isoformat(),))
        
        stats = cursor.fetchone()
        
        cursor.execute('''
            SELECT 
                endpoint,
                COUNT(*) as checks,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                AVG(response_time_ms) as avg_response_time
            FROM monitoring_checks 
            WHERE timestamp > ?
            GROUP BY endpoint
        ''', (since_time.isoformat(),))
        
        endpoint_stats = cursor.fetchall()
        
        cursor.execute('''
            SELECT alert_type, severity, message, endpoint, created_at
            FROM alerts 
            WHERE created_at > ?
            ORDER BY created_at DESC
            LIMIT 10
        ''', (since_time.isoformat(),))
        
        recent_alerts = cursor.fetchall()
        
        conn.close()
        
        report = {
            'period_hours': hours,
            'overall_stats': {
                'total_checks': stats[0],
                'successful_checks': stats[1],
                'success_rate': (stats[1] / stats[0]) if stats[0] > 0 else 0,
                'avg_response_time_ms': stats[2],
                'max_response_time_ms': stats[3]
            },
            'endpoint_stats': [
                {
                    'endpoint': row[0],
                    'checks': row[1],
                    'successes': row[2],
                    'success_rate': (row[2] / row[1]) if row[1] > 0 else 0,
                    'avg_response_time_ms': row[3]
                }
                for row in endpoint_stats
            ],
            'recent_alerts': [
                {
                    'type': row[0],
                    'severity': row[1],
                    'message': row[2],
                    'endpoint': row[3],
                    'created_at': row[4]
                }
                for row in recent_alerts
            ]
        }
        
        return report

def main():
    """Main function to run monitoring system"""
    monitoring = ComprehensiveMonitoringSystem()
    
    try:
        monitoring.start_monitoring()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down monitoring system...")
    finally:
        monitoring.stop_monitoring()

if __name__ == "__main__":
    main()
