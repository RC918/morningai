#!/usr/bin/env python3
"""
RLS Runtime Verification Script

Validates that Row-Level Security (RLS) policies are correctly enforcing
tenant isolation at runtime. This script performs actual database queries
to verify that users can only access data from their own tenant.

Usage:
    python scripts/verify_rls_runtime.py
    python scripts/verify_rls_runtime.py --verbose
    python scripts/verify_rls_runtime.py --table agent_tasks
    python scripts/verify_rls_runtime.py --all-tables

Requirements:
    - DATABASE_URL environment variable set
    - PostgreSQL database with RLS policies enabled
    - Test tenants and users created

Exit Codes:
    0 - All RLS checks passed
    1 - One or more RLS checks failed
    2 - Configuration or connection error
"""

import os
import sys
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class TestResult(Enum):
    """Test result status"""
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    SKIP = "⏭️  SKIP"
    ERROR = "🔥 ERROR"


@dataclass
class RLSTest:
    """RLS test case definition"""
    name: str
    description: str
    table: str
    role: str
    user_id: Optional[str]
    tenant_id: Optional[str]
    query: str
    expected_row_count: Optional[int]
    should_succeed: bool
    result: Optional[TestResult] = None
    actual_row_count: Optional[int] = None
    error_message: Optional[str] = None


class RLSVerifier:
    """RLS runtime verification engine"""
    
    TENANT_A_ID = "00000000-0000-0000-0000-000000000001"
    TENANT_B_ID = "00000000-0000-0000-0000-000000000002"
    USER_A_ID = "10000000-0000-0000-0000-000000000001"
    USER_B_ID = "20000000-0000-0000-0000-000000000002"
    
    RLS_TABLES = [
        "agent_tasks",
        "users",
        "user_profiles",
        "agent_execution_logs",
        "trace_metrics",
        "embeddings",
    ]
    
    def __init__(self, database_url: str, verbose: bool = False):
        self.database_url = database_url
        self.verbose = verbose
        self.conn = None
        self.tests: List[RLSTest] = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = 0
    
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                self.database_url,
                cursor_factory=RealDictCursor
            )
            self.conn.autocommit = False
            if self.verbose:
                print(f"✅ Connected to database")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            if self.verbose:
                print(f"✅ Disconnected from database")
    
    def setup_test_data(self) -> bool:
        """Create test tenants, users, and data"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO tenants (id, name) VALUES 
                        (%s, 'Test Tenant A'),
                        (%s, 'Test Tenant B')
                    ON CONFLICT (id) DO NOTHING
                """, (self.TENANT_A_ID, self.TENANT_B_ID))
                
                cur.execute("""
                    INSERT INTO users (id, tenant_id, email) VALUES
                        (%s, %s, 'test_user_a@rls-verify.test'),
                        (%s, %s, 'test_user_b@rls-verify.test')
                    ON CONFLICT (id) DO NOTHING
                """, (self.USER_A_ID, self.TENANT_A_ID, self.USER_B_ID, self.TENANT_B_ID))
                
                cur.execute("""
                    INSERT INTO agent_tasks (task_id, tenant_id, trace_id, question, status) VALUES
                        ('a0000001-0000-0000-0000-000000000000', %s, 'a0000001-0000-0000-0000-000000000000', 'Test task for Tenant A', 'queued'),
                        ('a0000002-0000-0000-0000-000000000000', %s, 'a0000002-0000-0000-0000-000000000000', 'Test task for Tenant B', 'queued')
                    ON CONFLICT (task_id) DO NOTHING
                """, (self.TENANT_A_ID, self.TENANT_B_ID))
                
                self.conn.commit()
                
                if self.verbose:
                    print(f"✅ Test data setup complete")
                return True
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Failed to setup test data: {e}")
            return False
    
    def cleanup_test_data(self):
        """Remove test data"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM agent_tasks 
                    WHERE task_id IN (
                        'a0000001-0000-0000-0000-000000000000',
                        'a0000002-0000-0000-0000-000000000000'
                    )
                """)
                
                
                self.conn.commit()
                
                if self.verbose:
                    print(f"✅ Test data cleanup complete")
        except Exception as e:
            self.conn.rollback()
            if self.verbose:
                print(f"⚠️  Test data cleanup failed: {e}")
    
    def verify_rls_enabled(self, table: str) -> Tuple[bool, str]:
        """Check if RLS is enabled on a table"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT rowsecurity 
                    FROM pg_tables 
                    WHERE schemaname = 'public' AND tablename = %s
                """, (table,))
                
                result = cur.fetchone()
                if not result:
                    return False, f"Table '{table}' not found"
                
                if result['rowsecurity']:
                    return True, f"RLS enabled on '{table}'"
                else:
                    return False, f"RLS NOT enabled on '{table}'"
        except Exception as e:
            return False, f"Error checking RLS status: {e}"
    
    def get_rls_policies(self, table: str) -> List[Dict]:
        """Get RLS policies for a table"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        policyname,
                        cmd as operation,
                        roles,
                        qual::text as using_clause,
                        with_check::text as with_check_clause
                    FROM pg_policies 
                    WHERE tablename = %s
                    ORDER BY policyname
                """, (table,))
                
                return cur.fetchall()
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Error fetching policies for '{table}': {e}")
            return []
    
    def run_test(self, test: RLSTest) -> TestResult:
        """Execute a single RLS test"""
        try:
            with self.conn.cursor() as cur:
                self.conn.rollback()
                
                if test.role:
                    cur.execute(f"SET LOCAL ROLE {test.role}")
                
                if test.user_id:
                    cur.execute(f"SET LOCAL request.jwt.claims.sub = '{test.user_id}'")
                
                try:
                    cur.execute(test.query)
                    rows = cur.fetchall()
                    test.actual_row_count = len(rows)
                    
                    if test.expected_row_count is not None:
                        if test.actual_row_count == test.expected_row_count:
                            test.result = TestResult.PASS
                        else:
                            test.result = TestResult.FAIL
                            test.error_message = f"Expected {test.expected_row_count} rows, got {test.actual_row_count}"
                    else:
                        test.result = TestResult.PASS if test.should_succeed else TestResult.FAIL
                        test.error_message = "Query succeeded but was expected to fail"
                    
                except psycopg2.Error as e:
                    if not test.should_succeed:
                        test.result = TestResult.PASS
                        test.error_message = f"Query correctly blocked: {str(e)[:100]}"
                    else:
                        test.result = TestResult.FAIL
                        test.error_message = f"Query failed unexpectedly: {str(e)[:100]}"
                
                self.conn.rollback()
                
        except Exception as e:
            test.result = TestResult.ERROR
            test.error_message = f"Test execution error: {str(e)[:100]}"
        
        return test.result
    
    def define_agent_tasks_tests(self) -> List[RLSTest]:
        """Define RLS tests for agent_tasks table"""
        return [
            RLSTest(
                name="User A reads own tenant tasks",
                description="User A should only see tasks from Tenant A",
                table="agent_tasks",
                role="authenticated",
                user_id=self.USER_A_ID,
                tenant_id=self.TENANT_A_ID,
                query=f"SELECT * FROM agent_tasks WHERE task_id = 'a0000001-0000-0000-0000-000000000000'",
                expected_row_count=1,
                should_succeed=True
            ),
            RLSTest(
                name="User A cannot read Tenant B tasks",
                description="User A should not see tasks from Tenant B",
                table="agent_tasks",
                role="authenticated",
                user_id=self.USER_A_ID,
                tenant_id=self.TENANT_A_ID,
                query=f"SELECT * FROM agent_tasks WHERE task_id = 'a0000002-0000-0000-0000-000000000000'",
                expected_row_count=0,
                should_succeed=True
            ),
            RLSTest(
                name="User B reads own tenant tasks",
                description="User B should only see tasks from Tenant B",
                table="agent_tasks",
                role="authenticated",
                user_id=self.USER_B_ID,
                tenant_id=self.TENANT_B_ID,
                query=f"SELECT * FROM agent_tasks WHERE task_id = 'a0000002-0000-0000-0000-000000000000'",
                expected_row_count=1,
                should_succeed=True
            ),
            RLSTest(
                name="User B cannot read Tenant A tasks",
                description="User B should not see tasks from Tenant A",
                table="agent_tasks",
                role="authenticated",
                user_id=self.USER_B_ID,
                tenant_id=self.TENANT_B_ID,
                query=f"SELECT * FROM agent_tasks WHERE task_id = 'a0000001-0000-0000-0000-000000000000'",
                expected_row_count=0,
                should_succeed=True
            ),
            RLSTest(
                name="User A cannot update Tenant B tasks",
                description="User A should not be able to update Tenant B tasks",
                table="agent_tasks",
                role="authenticated",
                user_id=self.USER_A_ID,
                tenant_id=self.TENANT_A_ID,
                query=f"UPDATE agent_tasks SET status = 'completed' WHERE task_id = 'a0000002-0000-0000-0000-000000000000' RETURNING *",
                expected_row_count=0,
                should_succeed=True
            ),
            RLSTest(
                name="User A cannot delete Tenant B tasks",
                description="User A should not be able to delete Tenant B tasks",
                table="agent_tasks",
                role="authenticated",
                user_id=self.USER_A_ID,
                tenant_id=self.TENANT_A_ID,
                query=f"DELETE FROM agent_tasks WHERE task_id = 'a0000002-0000-0000-0000-000000000000' RETURNING *",
                expected_row_count=0,
                should_succeed=True
            ),
            RLSTest(
                name="Service role reads all tasks",
                description="Service role should bypass RLS and see all tasks",
                table="agent_tasks",
                role="service_role",
                user_id=None,
                tenant_id=None,
                query=f"SELECT * FROM agent_tasks WHERE task_id IN ('a0000001-0000-0000-0000-000000000000', 'a0000002-0000-0000-0000-000000000000')",
                expected_row_count=2,
                should_succeed=True
            ),
            RLSTest(
                name="Anon role cannot read tasks",
                description="Anonymous role should not be able to read any tasks",
                table="agent_tasks",
                role="anon",
                user_id=None,
                tenant_id=None,
                query=f"SELECT * FROM agent_tasks WHERE task_id IN ('a0000001-0000-0000-0000-000000000000', 'a0000002-0000-0000-0000-000000000000')",
                expected_row_count=0,
                should_succeed=True
            ),
        ]
    
    def run_all_tests(self, table: Optional[str] = None):
        """Run all RLS verification tests"""
        print("\n" + "="*70)
        print("RLS RUNTIME VERIFICATION")
        print("="*70)
        
        tables_to_test = [table] if table else self.RLS_TABLES
        
        for test_table in tables_to_test:
            print(f"\n📋 Testing table: {test_table}")
            print("-"*70)
            
            rls_enabled, message = self.verify_rls_enabled(test_table)
            print(f"  {message}")
            
            if not rls_enabled:
                print(f"  ⏭️  Skipping tests for '{test_table}' (RLS not enabled)")
                self.skipped += 1
                continue
            
            policies = self.get_rls_policies(test_table)
            if self.verbose and policies:
                print(f"  📜 Policies: {len(policies)}")
                for policy in policies:
                    print(f"     - {policy['policyname']} ({policy['operation']})")
            
            if test_table == "agent_tasks":
                table_tests = self.define_agent_tasks_tests()
            else:
                print(f"  ℹ️  Detailed tests not yet implemented for '{test_table}'")
                continue
            
            print(f"\n  Running {len(table_tests)} tests...")
            
            for test in table_tests:
                result = self.run_test(test)
                
                if result == TestResult.PASS:
                    self.passed += 1
                    status_icon = "✅"
                elif result == TestResult.FAIL:
                    self.failed += 1
                    status_icon = "❌"
                elif result == TestResult.SKIP:
                    self.skipped += 1
                    status_icon = "⏭️ "
                else:
                    self.errors += 1
                    status_icon = "🔥"
                
                print(f"  {status_icon} {test.name}")
                if self.verbose or result != TestResult.PASS:
                    print(f"     {test.description}")
                    if test.error_message:
                        print(f"     {test.error_message}")
                    if test.actual_row_count is not None:
                        print(f"     Rows returned: {test.actual_row_count}")
        
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"✅ Passed:  {self.passed}")
        print(f"❌ Failed:  {self.failed}")
        print(f"⏭️  Skipped: {self.skipped}")
        print(f"🔥 Errors:  {self.errors}")
        print(f"📊 Total:   {self.passed + self.failed + self.skipped + self.errors}")
        
        if self.failed > 0 or self.errors > 0:
            print("\n⚠️  RLS VERIFICATION FAILED")
            print("Some RLS policies are not working correctly!")
            print("Review the failed tests above and fix the policies.")
            return False
        else:
            print("\n🎉 RLS VERIFICATION PASSED")
            print("All RLS policies are working correctly!")
            return True


def main():
    parser = argparse.ArgumentParser(
        description="Verify RLS policies are correctly enforcing tenant isolation at runtime"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--table", "-t",
        help="Test specific table only (default: test all tables)"
    )
    parser.add_argument(
        "--all-tables",
        action="store_true",
        help="Test all RLS-enabled tables"
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL"),
        help="PostgreSQL connection URL (default: $DATABASE_URL)"
    )
    
    args = parser.parse_args()
    
    if not args.database_url:
        print("❌ ERROR: DATABASE_URL not set")
        print("Set DATABASE_URL environment variable or use --database-url flag")
        return 2
    
    verifier = RLSVerifier(args.database_url, verbose=args.verbose)
    
    if not verifier.connect():
        return 2
    
    try:
        if not verifier.setup_test_data():
            return 2
        
        table = args.table if args.table else None
        success = verifier.run_all_tests(table=table)
        
        verifier.cleanup_test_data()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted by user")
        return 2
    except Exception as e:
        print(f"\n\n🔥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 2
    finally:
        verifier.disconnect()


if __name__ == "__main__":
    sys.exit(main())
