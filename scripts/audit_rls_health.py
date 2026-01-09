#!/usr/bin/env python3
"""
RLS Health Audit Script

Performs comprehensive Row-Level Security (RLS) auditing:
1. Coverage Audit: Scan all tables for RLS status and policy count
2. Semantic Consistency Audit: Check for anti-patterns and policy correctness
3. Environment Alignment: Compare policies across environments (optional)

This script is designed for CI integration with blocking gate support.

Usage:
    python scripts/audit_rls_health.py                    # Full audit, report only
    python scripts/audit_rls_health.py --fail-on-critical # Exit 1 if critical issues
    python scripts/audit_rls_health.py --json             # Output JSON for CI parsing
    python scripts/audit_rls_health.py --table agent_tasks # Audit specific table

    # Environment comparison (Issue #3326):
    python scripts/audit_rls_health.py --compare-env \\
      --staging-url $STAGING_DATABASE_URL \\
      --production-url $PRODUCTION_DATABASE_URL

Exit Codes:
    0 - All checks passed (or no critical issues in report-only mode)
    1 - Critical issues found (when --fail-on-critical is set)
    2 - Configuration or connection error

Environment Variables:
    DATABASE_URL: PostgreSQL connection string (required for single-env audit)
    STAGING_DATABASE_URL: Staging PostgreSQL connection string (for --compare-env)
    PRODUCTION_DATABASE_URL: Production PostgreSQL connection string (for --compare-env)
"""

import os
import re
import sys
import json
import argparse
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(2)


class Severity(Enum):
    """Issue severity levels"""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class AuditIssue:
    """Represents an audit finding"""
    severity: Severity
    table: str
    issue_type: str
    message: str
    policy_name: Optional[str] = None
    recommendation: Optional[str] = None


@dataclass
class TableAuditResult:
    """Audit result for a single table"""
    table_name: str
    rls_enabled: bool
    policy_count: int
    has_tenant_id: bool
    policies: list = field(default_factory=list)
    issues: list = field(default_factory=list)


@dataclass
class AuditReport:
    """Complete audit report"""
    version: str = "1.0"
    database: str = ""
    total_tables: int = 0
    tables_with_rls: int = 0
    tables_without_rls: int = 0
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    table_results: list = field(default_factory=list)
    all_issues: list = field(default_factory=list)


@dataclass
class PolicyDiff:
    """Represents a difference in a policy between environments"""
    table_name: str
    policy_name: str
    diff_type: str  # "staging_only", "production_only", "semantic_diff"
    staging_value: Optional[str] = None
    production_value: Optional[str] = None
    details: Optional[str] = None


@dataclass
class EnvironmentComparisonReport:
    """Report comparing RLS policies between two environments"""
    version: str = "1.0"
    staging_database: str = ""
    production_database: str = ""
    staging_only_policies: list = field(default_factory=list)
    production_only_policies: list = field(default_factory=list)
    semantic_differences: list = field(default_factory=list)
    staging_only_tables: list = field(default_factory=list)
    production_only_tables: list = field(default_factory=list)
    total_differences: int = 0
    is_aligned: bool = True


class RLSAuditor:
    """RLS Health Auditor"""

    TENANT_SCOPED_TABLES = [
        "agent_tasks",
        "planner_events",
        "users",
        "user_profiles",
        "tenants",
        "platform_bindings",
        "external_integrations",
        "action_requests",
        "tenant_quotas",
    ]

    PLATFORM_ADMIN_ONLY_TABLES = [
        "memory",
        "error_fix_pairs",
        "failure_memory",
        "agent_reputation",
        "ai_policies",
    ]

    SYSTEM_TABLES_IGNORE = [
        "schema_migrations",
        "spatial_ref_sys",
        "geography_columns",
        "geometry_columns",
    ]

    def __init__(self, database_url: str, verbose: bool = False):
        self.database_url = database_url
        self.verbose = verbose
        self.conn = None
        self.current_database = None
        self.issues: list[AuditIssue] = []
        self.table_results: list[TableAuditResult] = []

    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                self.database_url,
                cursor_factory=RealDictCursor
            )
            self.conn.autocommit = True

            with self.conn.cursor() as cur:
                cur.execute("SELECT current_database()")
                self.current_database = cur.fetchone()['current_database']

            if self.verbose:
                print(f"Connected to database: {self.current_database}")
            return True
        except Exception:
            print("ERROR: Failed to connect to database. Check DATABASE_URL and connectivity.")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get_all_tables(self) -> list[dict]:
        """Get all tables in public schema with RLS status"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT
                    t.tablename,
                    t.rowsecurity as rls_enabled,
                    (SELECT COUNT(*) FROM pg_policies p
                     WHERE p.schemaname = 'public' AND p.tablename = t.tablename) as policy_count
                FROM pg_tables t
                WHERE t.schemaname = 'public'
                ORDER BY t.tablename
            """)
            return cur.fetchall()

    def get_table_columns(self, table_name: str) -> list[str]:
        """Get column names for a table"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
            """, (table_name,))
            return [row['column_name'] for row in cur.fetchall()]

    def get_table_policies(self, table_name: str) -> list[dict]:
        """Get RLS policies for a table"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT
                    policyname,
                    cmd as operation,
                    roles,
                    qual::text as using_clause,
                    with_check::text as with_check_clause
                FROM pg_policies
                WHERE schemaname = 'public' AND tablename = %s
                ORDER BY policyname
            """, (table_name,))
            return cur.fetchall()

    def audit_table(self, table_info: dict) -> TableAuditResult:
        """Audit a single table"""
        table_name = table_info['tablename']
        rls_enabled = table_info['rls_enabled']
        policy_count = table_info['policy_count']

        columns = self.get_table_columns(table_name)
        has_tenant_id = 'tenant_id' in columns
        policies = self.get_table_policies(table_name)

        result = TableAuditResult(
            table_name=table_name,
            rls_enabled=rls_enabled,
            policy_count=policy_count,
            has_tenant_id=has_tenant_id,
            policies=[dict(p) for p in policies],
            issues=[]
        )

        if table_name in self.SYSTEM_TABLES_IGNORE:
            return result

        if not rls_enabled:
            issue = AuditIssue(
                severity=Severity.CRITICAL,
                table=table_name,
                issue_type="RLS_DISABLED",
                message=f"RLS is DISABLED on table '{table_name}'",
                recommendation="Enable RLS with: ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;"
            )
            result.issues.append(issue)
            self.issues.append(issue)

        if rls_enabled and policy_count == 0:
            issue = AuditIssue(
                severity=Severity.CRITICAL,
                table=table_name,
                issue_type="NO_POLICIES",
                message=f"RLS is enabled but NO POLICIES exist on '{table_name}'",
                recommendation="Add at least one RLS policy to control access"
            )
            result.issues.append(issue)
            self.issues.append(issue)

        self._audit_semantic_patterns(result, policies)

        return result

    def _has_tenant_isolation_pattern(self, policy: dict) -> bool:
        """
        Check if a policy contains tenant isolation logic using robust pattern matching.

        This method uses regex patterns to detect tenant isolation in SQL clauses,
        handling various SQL formatting styles (whitespace, newlines, aliases, etc.)
        """
        using_clause = (policy.get('using_clause') or '').lower()
        policy_name = (policy.get('policyname') or '').lower()

        if 'true_tenant_isolation' in policy_name:
            return True

        tenant_id_patterns = [
            r'\btenant_id\s*=',
            r'=\s*tenant_id\b',
            r'\btenant_id\s+in\b',
            r'\bcurrent_user_tenant_id\s*\(\s*\)',
            r'\btenant_id\b.*\bcurrent_user_tenant_id\b',
            r'\bcurrent_user_tenant_id\b.*\btenant_id\b',
        ]

        for pattern in tenant_id_patterns:
            if re.search(pattern, using_clause, re.IGNORECASE | re.DOTALL):
                return True

        return False

    def _audit_semantic_patterns(self, result: TableAuditResult, policies: list[dict]):
        """Check for semantic anti-patterns in policies"""
        table_name = result.table_name

        is_tenant_scoped = table_name in self.TENANT_SCOPED_TABLES or result.has_tenant_id
        is_platform_admin_only = table_name in self.PLATFORM_ADMIN_ONLY_TABLES

        for policy in policies:
            policy_name = policy['policyname']
            using_clause = policy.get('using_clause') or ''
            roles = policy.get('roles') or []

            if is_tenant_scoped and not is_platform_admin_only:
                if 'authenticated' in str(roles) and using_clause.strip().lower() == 'true':
                    if 'platform_admin' not in policy_name.lower():
                        issue = AuditIssue(
                            severity=Severity.WARNING,
                            table=table_name,
                            issue_type="OVERLY_PERMISSIVE",
                            message=f"Policy '{policy_name}' uses USING(true) on tenant-scoped table (heuristic check)",
                            policy_name=policy_name,
                            recommendation="Replace with tenant isolation: USING(tenant_id = current_user_tenant_id())"
                        )
                        result.issues.append(issue)
                        self.issues.append(issue)

            if is_platform_admin_only:
                if 'authenticated' in str(roles) and 'platform_admin' not in policy_name.lower():
                    if 'is_platform_admin' not in using_clause.lower():
                        issue = AuditIssue(
                            severity=Severity.WARNING,
                            table=table_name,
                            issue_type="MISSING_ADMIN_CHECK",
                            message=f"Policy '{policy_name}' on platform-admin table may lack admin check",
                            policy_name=policy_name,
                            recommendation="Ensure policy checks is_platform_admin = TRUE"
                        )
                        result.issues.append(issue)
                        self.issues.append(issue)

        if is_tenant_scoped and result.has_tenant_id and result.policy_count > 0:
            has_tenant_isolation = any(
                self._has_tenant_isolation_pattern(p)
                for p in policies
            )

            if not has_tenant_isolation:
                issue = AuditIssue(
                    severity=Severity.WARNING,
                    table=table_name,
                    issue_type="NO_TENANT_ISOLATION",
                    message=f"Table '{table_name}' has tenant_id but no tenant isolation policy detected",
                    recommendation="Add policy with USING(tenant_id = current_user_tenant_id())"
                )
                result.issues.append(issue)
                self.issues.append(issue)

    def run_audit(self, specific_table: Optional[str] = None) -> AuditReport:
        """Run full RLS audit"""
        tables = self.get_all_tables()

        if specific_table:
            tables = [t for t in tables if t['tablename'] == specific_table]
            if not tables:
                print(f"ERROR: Table '{specific_table}' not found")
                sys.exit(2)

        for table_info in tables:
            if table_info['tablename'] in self.SYSTEM_TABLES_IGNORE:
                continue
            result = self.audit_table(table_info)
            self.table_results.append(result)

        tables_with_rls = sum(1 for r in self.table_results if r.rls_enabled)
        tables_without_rls = sum(1 for r in self.table_results if not r.rls_enabled)

        critical_count = sum(1 for i in self.issues if i.severity == Severity.CRITICAL)
        warning_count = sum(1 for i in self.issues if i.severity == Severity.WARNING)
        info_count = sum(1 for i in self.issues if i.severity == Severity.INFO)

        return AuditReport(
            database=self.current_database,
            total_tables=len(self.table_results),
            tables_with_rls=tables_with_rls,
            tables_without_rls=tables_without_rls,
            critical_count=critical_count,
            warning_count=warning_count,
            info_count=info_count,
            table_results=[asdict(r) for r in self.table_results],
            all_issues=[asdict(i) for i in self.issues]
        )

    def print_report(self, report: AuditReport):
        """Print human-readable report"""
        print("\n" + "=" * 70)
        print("RLS HEALTH AUDIT REPORT")
        print("=" * 70)
        print(f"Database: {report.database}")
        print(f"Total Tables: {report.total_tables}")
        print(f"Tables with RLS: {report.tables_with_rls}")
        print(f"Tables without RLS: {report.tables_without_rls}")
        print("-" * 70)
        print(f"CRITICAL Issues: {report.critical_count}")
        print(f"WARNING Issues: {report.warning_count}")
        print(f"INFO Issues: {report.info_count}")
        print("=" * 70)

        if report.critical_count > 0:
            print("\nCRITICAL ISSUES:")
            print("-" * 70)
            for issue in report.all_issues:
                if issue['severity'] == 'CRITICAL':
                    print(f"  [{issue['table']}] {issue['issue_type']}")
                    print(f"    {issue['message']}")
                    if issue.get('recommendation'):
                        print(f"    Recommendation: {issue['recommendation']}")
                    print()

        if report.warning_count > 0 and self.verbose:
            print("\nWARNINGS:")
            print("-" * 70)
            for issue in report.all_issues:
                if issue['severity'] == 'WARNING':
                    print(f"  [{issue['table']}] {issue['issue_type']}")
                    print(f"    {issue['message']}")
                    print()

        if self.verbose:
            print("\nTABLE DETAILS:")
            print("-" * 70)
            for result in report.table_results:
                status = "RLS ON" if result['rls_enabled'] else "RLS OFF"
                tenant = "tenant_id" if result['has_tenant_id'] else "no tenant_id"
                print(f"  {result['table_name']}: {status}, {result['policy_count']} policies, {tenant}")

        print("\n" + "=" * 70)
        if report.critical_count == 0:
            print("RESULT: PASS - No critical RLS issues found")
        else:
            print(f"RESULT: FAIL - {report.critical_count} critical issue(s) found")
        print("=" * 70 + "\n")


class RLSEnvironmentComparator:
    """
    Compare RLS policies between two environments (e.g., staging and production).

    Issue #3326: Environment Alignment - Fourth layer of RLS Gate 分層 plan.

    This class performs:
    1. Policy Diff Report: Compare pg_policies views between environments
    2. Drift Detection: Identify policies that exist in one environment but not the other
    3. Semantic Comparison: Detect policies with same name but different USING/WITH CHECK clauses
    """

    def __init__(self, staging_url: str, production_url: str, verbose: bool = False):
        self.staging_url = staging_url
        self.production_url = production_url
        self.verbose = verbose
        self.staging_conn = None
        self.production_conn = None
        self.staging_database = None
        self.production_database = None

    def _mask_url(self, url: str) -> str:
        """Mask credentials in database URL for safe logging"""
        if '@' in url:
            parts = url.split('@')
            return f"***@{parts[-1]}"
        return "***"

    def connect(self) -> bool:
        """Establish connections to both environments"""
        try:
            self.staging_conn = psycopg2.connect(
                self.staging_url,
                cursor_factory=RealDictCursor
            )
            self.staging_conn.autocommit = True

            with self.staging_conn.cursor() as cur:
                cur.execute("SELECT current_database()")
                self.staging_database = cur.fetchone()['current_database']

            if self.verbose:
                print(f"Connected to staging: {self.staging_database}")

        except Exception as e:
            print(f"ERROR: Failed to connect to staging database: {e}")
            return False

        try:
            self.production_conn = psycopg2.connect(
                self.production_url,
                cursor_factory=RealDictCursor
            )
            self.production_conn.autocommit = True

            with self.production_conn.cursor() as cur:
                cur.execute("SELECT current_database()")
                self.production_database = cur.fetchone()['current_database']

            if self.verbose:
                print(f"Connected to production: {self.production_database}")

        except Exception as e:
            print(f"ERROR: Failed to connect to production database: {e}")
            if self.staging_conn:
                self.staging_conn.close()
            return False

        return True

    def disconnect(self):
        """Close database connections"""
        if self.staging_conn:
            self.staging_conn.close()
        if self.production_conn:
            self.production_conn.close()

    def _get_tables(self, conn) -> set:
        """Get all tables in public schema"""
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
            """)
            return {row['tablename'] for row in cur.fetchall()}

    def _get_all_policies(self, conn) -> dict:
        """
        Get all RLS policies from a database.

        Returns a dict keyed by (table_name, policy_name) with policy details.
        """
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    tablename,
                    policyname,
                    cmd as operation,
                    roles,
                    qual::text as using_clause,
                    with_check::text as with_check_clause
                FROM pg_policies
                WHERE schemaname = 'public'
                ORDER BY tablename, policyname
            """)
            policies = {}
            for row in cur.fetchall():
                key = (row['tablename'], row['policyname'])
                policies[key] = {
                    'table_name': row['tablename'],
                    'policy_name': row['policyname'],
                    'operation': row['operation'],
                    'roles': row['roles'],
                    'using_clause': row['using_clause'],
                    'with_check_clause': row['with_check_clause'],
                }
            return policies

    def _normalize_clause(self, clause: Optional[str]) -> str:
        """Normalize SQL clause for comparison (remove whitespace variations)"""
        if clause is None:
            return ""
        normalized = ' '.join(clause.split())
        return normalized.lower().strip()

    def compare(self) -> EnvironmentComparisonReport:
        """
        Compare RLS policies between staging and production.

        Returns an EnvironmentComparisonReport with all differences found.
        """
        staging_tables = self._get_tables(self.staging_conn)
        production_tables = self._get_tables(self.production_conn)

        staging_policies = self._get_all_policies(self.staging_conn)
        production_policies = self._get_all_policies(self.production_conn)

        staging_only_tables = staging_tables - production_tables
        production_only_tables = production_tables - staging_tables

        staging_only_policies = []
        production_only_policies = []
        semantic_differences = []

        staging_keys = set(staging_policies.keys())
        production_keys = set(production_policies.keys())

        for key in staging_keys - production_keys:
            table_name, policy_name = key
            reason = ""
            if table_name in staging_only_tables:
                reason = f"(table '{table_name}' only exists in staging)"
            staging_only_policies.append(PolicyDiff(
                table_name=table_name,
                policy_name=policy_name,
                diff_type="staging_only",
                staging_value=staging_policies[key].get('using_clause'),
                details=reason
            ))

        for key in production_keys - staging_keys:
            table_name, policy_name = key
            reason = ""
            if table_name in production_only_tables:
                reason = f"(table '{table_name}' only exists in production)"
            production_only_policies.append(PolicyDiff(
                table_name=table_name,
                policy_name=policy_name,
                diff_type="production_only",
                production_value=production_policies[key].get('using_clause'),
                details=reason
            ))

        for key in staging_keys & production_keys:
            staging_policy = staging_policies[key]
            production_policy = production_policies[key]

            staging_using = self._normalize_clause(staging_policy.get('using_clause'))
            production_using = self._normalize_clause(production_policy.get('using_clause'))

            staging_with_check = self._normalize_clause(staging_policy.get('with_check_clause'))
            production_with_check = self._normalize_clause(production_policy.get('with_check_clause'))

            differences = []
            if staging_using != production_using:
                differences.append("USING clause differs")
            if staging_with_check != production_with_check:
                differences.append("WITH CHECK clause differs")

            if differences:
                table_name, policy_name = key
                semantic_differences.append(PolicyDiff(
                    table_name=table_name,
                    policy_name=policy_name,
                    diff_type="semantic_diff",
                    staging_value=staging_policy.get('using_clause'),
                    production_value=production_policy.get('using_clause'),
                    details="; ".join(differences)
                ))

        total_differences = (
            len(staging_only_policies) +
            len(production_only_policies) +
            len(semantic_differences)
        )

        return EnvironmentComparisonReport(
            staging_database=self.staging_database,
            production_database=self.production_database,
            staging_only_policies=[asdict(p) for p in staging_only_policies],
            production_only_policies=[asdict(p) for p in production_only_policies],
            semantic_differences=[asdict(p) for p in semantic_differences],
            staging_only_tables=list(staging_only_tables),
            production_only_tables=list(production_only_tables),
            total_differences=total_differences,
            is_aligned=(total_differences == 0)
        )

    def print_report(self, report: EnvironmentComparisonReport):
        """Print human-readable environment comparison report"""
        print("\n" + "=" * 70)
        print("ENVIRONMENT ALIGNMENT REPORT")
        print("=" * 70)
        print(f"Staging Database: {report.staging_database}")
        print(f"Production Database: {report.production_database}")
        print("-" * 70)

        if report.staging_only_tables:
            print(f"\nTables only in Staging ({len(report.staging_only_tables)}):")
            for table in sorted(report.staging_only_tables):
                print(f"  - {table}")

        if report.production_only_tables:
            print(f"\nTables only in Production ({len(report.production_only_tables)}):")
            for table in sorted(report.production_only_tables):
                print(f"  - {table}")

        print("\n" + "-" * 70)
        print("POLICY DIFFERENCES")
        print("-" * 70)

        if report.staging_only_policies:
            print(f"\nPolicies only in Staging ({len(report.staging_only_policies)}):")
            for diff in report.staging_only_policies:
                details = f" {diff['details']}" if diff.get('details') else ""
                print(f"  - {diff['table_name']}.{diff['policy_name']}{details}")

        if report.production_only_policies:
            print(f"\nPolicies only in Production ({len(report.production_only_policies)}):")
            for diff in report.production_only_policies:
                details = f" {diff['details']}" if diff.get('details') else ""
                print(f"  - {diff['table_name']}.{diff['policy_name']}{details}")

        if report.semantic_differences:
            print(f"\nPolicies with semantic differences ({len(report.semantic_differences)}):")
            for diff in report.semantic_differences:
                print(f"  - {diff['table_name']}.{diff['policy_name']}: {diff['details']}")
                if self.verbose:
                    print(f"    Staging:    {diff.get('staging_value', 'N/A')}")
                    print(f"    Production: {diff.get('production_value', 'N/A')}")

        print("\n" + "=" * 70)
        if report.is_aligned:
            print("RESULT: ALIGNED - No policy differences between environments")
        else:
            print(f"RESULT: DRIFT DETECTED - {report.total_differences} difference(s) found")
        print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="RLS Health Audit Script")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument(
        "--fail-on-critical", action="store_true",
        help="Exit with code 1 if critical issues found"
    )
    parser.add_argument("--table", type=str, help="Audit specific table only")

    # Issue #3326: Environment comparison arguments
    parser.add_argument(
        "--compare-env", action="store_true",
        help="Compare RLS policies between staging and production environments"
    )
    parser.add_argument(
        "--staging-url", type=str,
        help="Staging database URL (or use STAGING_DATABASE_URL env var)"
    )
    parser.add_argument(
        "--production-url", type=str,
        help="Production database URL (or use PRODUCTION_DATABASE_URL env var)"
    )
    parser.add_argument(
        "--fail-on-drift", action="store_true",
        help="Exit with code 1 if environment drift is detected (for CI)"
    )

    args = parser.parse_args()

    # Issue #3326: Handle environment comparison mode
    if args.compare_env:
        staging_url = args.staging_url or os.environ.get("STAGING_DATABASE_URL")
        production_url = args.production_url or os.environ.get("PRODUCTION_DATABASE_URL")

        if not staging_url:
            print("ERROR: Staging database URL not provided.")
            print("Use --staging-url or set STAGING_DATABASE_URL environment variable.")
            sys.exit(2)

        if not production_url:
            print("ERROR: Production database URL not provided.")
            print("Use --production-url or set PRODUCTION_DATABASE_URL environment variable.")
            sys.exit(2)

        comparator = RLSEnvironmentComparator(
            staging_url=staging_url,
            production_url=production_url,
            verbose=args.verbose
        )

        if not comparator.connect():
            sys.exit(2)

        try:
            report = comparator.compare()

            if args.json:
                print(json.dumps(asdict(report), indent=2, default=str))
            else:
                comparator.print_report(report)

            if args.fail_on_drift and not report.is_aligned:
                sys.exit(1)

            sys.exit(0)

        finally:
            comparator.disconnect()

    # Standard single-environment audit mode
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(2)

    auditor = RLSAuditor(database_url, verbose=args.verbose)

    if not auditor.connect():
        sys.exit(2)

    try:
        report = auditor.run_audit(specific_table=args.table)

        if args.json:
            report_dict = asdict(report)
            for issue in report_dict['all_issues']:
                if isinstance(issue['severity'], Severity):
                    issue['severity'] = issue['severity'].value
            for table_result in report_dict['table_results']:
                for issue in table_result.get('issues', []):
                    if isinstance(issue.get('severity'), Severity):
                        issue['severity'] = issue['severity'].value
            print(json.dumps(report_dict, indent=2, default=str))
        else:
            auditor.print_report(report)

        if args.fail_on_critical and report.critical_count > 0:
            sys.exit(1)

        sys.exit(0)

    finally:
        auditor.disconnect()


if __name__ == "__main__":
    main()
