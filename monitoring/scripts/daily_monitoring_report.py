#!/usr/bin/env python3
"""
Daily RLS Monitoring Report Generator
Runs SQL monitoring queries and generates alert report

Schedule:
- 9 AM: Run checks, alert on CRITICAL issues
- 6 PM: Run checks, send full report to CTO

Usage:
    python daily_monitoring_report.py --time morning|evening
    python daily_monitoring_report.py --time morning  # 9 AM run
    python daily_monitoring_report.py --time evening  # 6 PM run with full report
"""

import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple
import logging

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s"}'
)
logger = logging.getLogger(__name__)

try:
    from supabase import create_client, Client
except ImportError:
    logger.error("supabase-py not installed. Run: pip install supabase")
    sys.exit(1)

SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(dsn=SENTRY_DSN)
    except ImportError:
        logger.warning("sentry-sdk not installed. Sentry alerts disabled")
        sentry_sdk = None
else:
    sentry_sdk = None


class RLSMonitor:
    """RLS Monitoring System"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        self.sql_queries_dir = Path(__file__).parent.parent / "sql_queries"
        self.results: Dict[str, any] = {}
        self.alerts: List[Dict] = []
    
    def run_sql_query(self, query_file: Path) -> Tuple[bool, any]:
        """Execute SQL query from file"""
        try:
            with open(query_file, 'r') as f:
                sql = f.read()
            
            queries = [q.strip() for q in sql.split(';') if q.strip() and not q.strip().startswith('--')]
            
            results = []
            for query in queries:
                if query:
                    result = self.client.rpc('exec_sql', {'sql': query}).execute()
                    results.append(result.data if result.data else [])
            
            return True, results
        except Exception as e:
            logger.error(f"Failed to execute {query_file.name}: {e}")
            return False, str(e)
    
    def check_rls_health(self) -> Dict:
        """Run Query #1: RLS Health Check"""
        query_file = self.sql_queries_dir / "01_rls_health_check.sql"
        success, result = self.run_sql_query(query_file)
        
        status = {
            "query": "RLS Health Check",
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": result if success else None,
            "error": None if success else result,
            "alert_level": "OK"
        }
        
        if success and result:
            for table in result[0] if isinstance(result, list) else []:
                if isinstance(table, dict):
                    if not table.get('rls_enabled') or table.get('policy_count', 0) == 0:
                        status["alert_level"] = "CRITICAL"
                        self.alerts.append({
                            "level": "CRITICAL",
                            "query": "RLS Health Check",
                            "message": f"RLS disabled or no policies on {table.get('tablename')}"
                        })
        
        return status
    
    def check_tenant_isolation(self) -> Dict:
        """Run Query #2: Tenant Isolation Verification"""
        query_file = self.sql_queries_dir / "02_tenant_isolation_verification.sql"
        success, result = self.run_sql_query(query_file)
        
        status = {
            "query": "Tenant Isolation Verification",
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": result if success else None,
            "error": None if success else result,
            "alert_level": "OK"
        }
        
        if success and result and isinstance(result, list) and len(result) > 0:
            summary = result[0][0] if isinstance(result[0], list) and len(result[0]) > 0 else {}
            if isinstance(summary, dict):
                null_count = summary.get('null_tenant_count', 0)
                if null_count > 0:
                    status["alert_level"] = "CRITICAL"
                    self.alerts.append({
                        "level": "CRITICAL",
                        "query": "Tenant Isolation",
                        "message": f"{null_count} tasks have NULL tenant_id - will fail RLS checks"
                    })
        
        return status
    
    def check_policy_effectiveness(self) -> Dict:
        """Run Query #3: RLS Policy Effectiveness"""
        query_file = self.sql_queries_dir / "03_rls_policy_effectiveness.sql"
        success, result = self.run_sql_query(query_file)
        
        status = {
            "query": "RLS Policy Effectiveness",
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": result if success else None,
            "error": None if success else result,
            "alert_level": "OK"
        }
        
        if success and result:
            for policy in (result[0] if isinstance(result, list) else []):
                if isinstance(policy, dict):
                    if 'USING(true)' in policy.get('policy_logic_preview', ''):
                        status["alert_level"] = "CRITICAL"
                        self.alerts.append({
                            "level": "CRITICAL",
                            "query": "Policy Effectiveness",
                            "message": f"Policy {policy.get('policyname')} using USING(true) - NO tenant isolation!"
                        })
        
        return status
    
    def check_user_tenant_coverage(self) -> Dict:
        """Run Query #4: User Tenant Coverage"""
        query_file = self.sql_queries_dir / "04_user_tenant_coverage.sql"
        success, result = self.run_sql_query(query_file)
        
        status = {
            "query": "User Tenant Coverage",
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": result if success else None,
            "error": None if success else result,
            "alert_level": "OK"
        }
        
        if success and result and isinstance(result, list) and len(result) > 0:
            summary = result[0][0] if isinstance(result[0], list) and len(result[0]) > 0 else {}
            if isinstance(summary, dict):
                null_users = summary.get('null_tenant_users', 0)
                if null_users > 0:
                    status["alert_level"] = "CRITICAL"
                    self.alerts.append({
                        "level": "CRITICAL",
                        "query": "User Tenant Coverage",
                        "message": f"{null_users} users have NULL tenant_id - LOCKED OUT by RLS!"
                    })
        
        return status
    
    def check_performance_metrics(self) -> Dict:
        """Run Query #5: Performance Metrics"""
        query_file = self.sql_queries_dir / "05_rls_performance_metrics.sql"
        success, result = self.run_sql_query(query_file)
        
        status = {
            "query": "Performance Metrics",
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": result if success else None,
            "error": None if success else result,
            "alert_level": "OK"
        }
        
        if success and result:
            if len(result) > 1 and isinstance(result[1], list):
                for status_row in result[1]:
                    if isinstance(status_row, dict):
                        if status_row.get('status') == 'error':
                            error_pct = float(status_row.get('percentage', 0))
                            if error_pct > 20:
                                status["alert_level"] = "WARNING"
                                self.alerts.append({
                                    "level": "WARNING",
                                    "query": "Performance",
                                    "message": f"Error rate {error_pct}% exceeds threshold (20%)"
                                })
        
        return status
    
    def run_all_checks(self) -> Dict:
        """Run all monitoring checks"""
        logger.info("Starting RLS monitoring checks...")
        
        self.results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                "rls_health": self.check_rls_health(),
                "tenant_isolation": self.check_tenant_isolation(),
                "policy_effectiveness": self.check_policy_effectiveness(),
                "user_tenant_coverage": self.check_user_tenant_coverage(),
                "performance_metrics": self.check_performance_metrics()
            },
            "alerts": self.alerts,
            "summary": {
                "total_checks": 5,
                "passed": 0,
                "failed": 0,
                "critical_alerts": 0,
                "warning_alerts": 0
            }
        }
        
        for check in self.results["checks"].values():
            if check["success"]:
                self.results["summary"]["passed"] += 1
            else:
                self.results["summary"]["failed"] += 1
        
        self.results["summary"]["critical_alerts"] = len([a for a in self.alerts if a["level"] == "CRITICAL"])
        self.results["summary"]["warning_alerts"] = len([a for a in self.alerts if a["level"] == "WARNING"])
        
        logger.info(f"Monitoring complete. Passed: {self.results['summary']['passed']}/5, "
                   f"Critical: {self.results['summary']['critical_alerts']}, "
                   f"Warnings: {self.results['summary']['warning_alerts']}")
        
        return self.results
    
    def send_alerts(self):
        """Send alerts to Sentry for CRITICAL issues"""
        if not sentry_sdk:
            logger.warning("Sentry not configured. Skipping alert notifications")
            return
        
        for alert in self.alerts:
            if alert["level"] == "CRITICAL":
                sentry_sdk.capture_message(
                    f"RLS Monitor Alert: {alert['message']}",
                    level="error",
                    extras={
                        "query": alert["query"],
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
                logger.error(f"CRITICAL ALERT: {alert['message']}")
    
    def generate_report(self, report_type: str = "summary") -> str:
        """Generate monitoring report"""
        if report_type == "summary":
            report = f"""
=== RLS Monitoring Report (Morning Check) ===
Timestamp: {self.results['timestamp']}

Summary:
- Checks Passed: {self.results['summary']['passed']}/5
- Checks Failed: {self.results['summary']['failed']}/5
- Critical Alerts: {self.results['summary']['critical_alerts']}
- Warning Alerts: {self.results['summary']['warning_alerts']}

"""
            if self.alerts:
                report += "ALERTS:\n"
                for alert in self.alerts:
                    report += f"  {alert['level']}: {alert['message']} (Query: {alert['query']})\n"
            else:
                report += "✅ No alerts - All systems operational\n"
        
        else:  # full report for evening
            report = f"""
=== RLS Monitoring Report (Evening Full Report) ===
Timestamp: {self.results['timestamp']}

SUMMARY:
- Checks Passed: {self.results['summary']['passed']}/5
- Checks Failed: {self.results['summary']['failed']}/5
- Critical Alerts: {self.results['summary']['critical_alerts']}
- Warning Alerts: {self.results['summary']['warning_alerts']}

DETAILED RESULTS:
"""
            for check_name, check_data in self.results['checks'].items():
                report += f"\n{check_name.upper()}:\n"
                report += f"  Status: {'✅ PASS' if check_data['success'] else '❌ FAIL'}\n"
                report += f"  Alert Level: {check_data['alert_level']}\n"
                if check_data.get('error'):
                    report += f"  Error: {check_data['error']}\n"
            
            if self.alerts:
                report += "\nALERTS:\n"
                for alert in self.alerts:
                    report += f"  {alert['level']}: {alert['message']} (Query: {alert['query']})\n"
            else:
                report += "\n✅ No alerts - All systems operational\n"
        
        return report


def main():
    parser = argparse.ArgumentParser(description="RLS Daily Monitoring Report")
    parser.add_argument('--time', choices=['morning', 'evening'], required=True,
                       help="Report time: morning (9 AM) or evening (6 PM)")
    args = parser.parse_args()
    
    try:
        monitor = RLSMonitor()
        results = monitor.run_all_checks()
        
        if results['summary']['critical_alerts'] > 0:
            monitor.send_alerts()
        
        report_type = "summary" if args.time == "morning" else "full"
        report = monitor.generate_report(report_type)
        print(report)
        
        if args.time == "evening":
            report_file = Path(__file__).parent.parent / "reports" / f"rls_report_{datetime.now().strftime('%Y%m%d')}.txt"
            report_file.parent.mkdir(parents=True, exist_ok=True)
            with open(report_file, 'w') as f:
                f.write(report)
            logger.info(f"Report saved to {report_file}")
        
        sys.exit(1 if results['summary']['critical_alerts'] > 0 else 0)
    
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
