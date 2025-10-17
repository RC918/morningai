#!/usr/bin/env python3
"""
Security Fix Migration Runner
Fixes issues detected by Supabase Security Advisor
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import psycopg2
    from dotenv import load_dotenv
except ImportError as e:
    print(f"ERROR: Missing required package: {e}")
    print("\nPlease install: pip install psycopg2-binary python-dotenv")
    sys.exit(1)

def get_db_connection():
    """Create database connection from environment variables"""
    load_dotenv()
    
    supabase_url = os.getenv('SUPABASE_URL', '')
    supabase_password = os.getenv('SUPABASE_DB_PASSWORD', '')
    
    if not supabase_url or not supabase_password:
        print("ERROR: Missing SUPABASE_URL or SUPABASE_DB_PASSWORD")
        print("\nPlease set these in your .env file:")
        print("  SUPABASE_URL=https://your-project.supabase.co")
        print("  SUPABASE_DB_PASSWORD=your_password")
        sys.exit(1)
    
    # Convert HTTPS URL to PostgreSQL connection string
    try:
        db_url = supabase_url.replace('https://', 'postgresql://postgres:')
        db_url = db_url.replace('.supabase.co', '.supabase.co:5432/postgres')
        
        if supabase_password:
            db_url = db_url.replace('postgres:', f'postgres:{supabase_password}@')
        
        return psycopg2.connect(db_url)
    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}")
        print(f"URL format: {supabase_url[:50]}...")
        sys.exit(1)

def run_migration():
    """Execute the security fix migration"""
    migration_file = Path(__file__).parent / '003_fix_security_issues.sql'
    
    if not migration_file.exists():
        print(f"ERROR: Migration file not found: {migration_file}")
        sys.exit(1)
    
    print("=" * 70)
    print("Security Fix Migration")
    print("Fixing issues detected by Supabase Security Advisor")
    print("=" * 70)
    print()
    
    # Read migration SQL
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    print(f"Migration file: {migration_file}")
    print()
    
    # Connect to database
    print("--- Connecting to Database ---")
    try:
        conn = get_db_connection()
        conn.autocommit = False
        cursor = conn.cursor()
        print("✓ Connected successfully")
        print()
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        sys.exit(1)
    
    # Execute migration
    print("--- Executing Security Fixes ---")
    try:
        cursor.execute(migration_sql)
        
        # Fetch result
        if cursor.description:
            result = cursor.fetchone()
            if result:
                print(f"✓ {result[0]}")
        
        conn.commit()
        print()
        print("✓ Migration completed successfully!")
        print()
        
        # Verify RLS is enabled
        print("--- Verifying RLS Status ---")
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                rowsecurity as rls_enabled
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename IN (
                'code_embeddings', 
                'code_patterns', 
                'code_relationships', 
                'embedding_cache_stats',
                'agent_tasks'
            )
            ORDER BY tablename;
        """)
        
        tables = cursor.fetchall()
        if tables:
            for schema, table, rls_enabled in tables:
                status = "✓ ENABLED" if rls_enabled else "✗ DISABLED"
                print(f"  {table}: {status}")
        else:
            print("  No tables found (may not exist yet)")
        
        print()
        
        # Count policies
        print("--- Verifying RLS Policies ---")
        cursor.execute("""
            SELECT 
                tablename,
                COUNT(*) as policy_count
            FROM pg_policies 
            WHERE schemaname = 'public'
            GROUP BY tablename
            ORDER BY tablename;
        """)
        
        policies = cursor.fetchall()
        if policies:
            for table, count in policies:
                print(f"  {table}: {count} policies")
        
        print()
        print("=" * 70)
        print("✓ All security fixes applied successfully!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Go to Supabase Dashboard > Advisors > Security Advisor")
        print("2. Click 'Refresh' to re-run the security scan")
        print("3. Verify all errors are resolved")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        print()
        print("Rolling back changes...")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    run_migration()
