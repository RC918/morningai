#!/usr/bin/env python3
"""
Apply Phase 3 Database Migrations
Executes SQL migrations directly via psycopg2
"""
import os
import sys
import psycopg2

def read_sql_file(filepath):
    """Read SQL file content"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def execute_sql_file(conn, filepath, description):
    """Execute SQL file"""
    print(f"\n{'='*60}")
    print(f"Executing: {description}")
    print(f"File: {filepath}")
    print(f"{'='*60}\n")
    
    try:
        sql_content = read_sql_file(filepath)
        
        with conn.cursor() as cur:
            cur.execute(sql_content)
            conn.commit()
            
            if cur.statusmessage:
                print(f"Status: {cur.statusmessage}")
            
            try:
                for notice in conn.notices:
                    print(notice.strip())
            except:
                pass
        
        print(f"\n✅ {description} - SUCCESS\n")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ {description} - FAILED")
        print(f"Error: {str(e)}\n")
        return False

def main():
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ Error: DATABASE_URL must be set")
        sys.exit(1)
    
    print(f"Connecting to database...")
    
    try:
        conn = psycopg2.connect(database_url)
        conn.set_session(autocommit=False)
        print(f"✅ Connected successfully\n")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)
    
    migrations = [
        ('migrations/005_create_user_profiles_table.sql', 'Migration 005: Create user_profiles table'),
        ('migrations/006_update_rls_policies_true_tenant_isolation.sql', 'Migration 006: RLS Policies for Tenant Isolation'),
        ('migrations/backfill_user_profiles.sql', 'Backfill: Assign existing users to default tenant'),
    ]
    
    success_count = 0
    failed_count = 0
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for filepath, description in migrations:
        full_path = os.path.join(base_dir, filepath)
        
        if not os.path.exists(full_path):
            print(f"⚠️  Skipping {filepath} (file not found)")
            continue
        
        if execute_sql_file(conn, full_path, description):
            success_count += 1
        else:
            failed_count += 1
    
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"Migration Summary")
    print(f"{'='*60}")
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed:  {failed_count}")
    print(f"Total:     {len(migrations)}")
    print(f"{'='*60}\n")
    
    if failed_count > 0:
        print("⚠️  Some migrations failed. Please review errors above.")
        sys.exit(1)
    else:
        print("🎉 All migrations completed successfully!")

if __name__ == '__main__':
    main()
