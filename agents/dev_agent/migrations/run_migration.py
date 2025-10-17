#!/usr/bin/env python3
"""
Migration Helper Script
Phase 1 Week 5: Knowledge Graph System

Hybrid approach: Manual execution + Automatic checks
- Provides safety through human verification
- Supports different environments (dev/staging/prod)
- Allows rollback and troubleshooting
"""
import os
import sys
import psycopg2
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def get_db_connection():
    """Get database connection from environment variables"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_password = os.getenv('SUPABASE_DB_PASSWORD')

    if not supabase_url or not supabase_password:
        logger.error("Missing required environment variables:")
        logger.error("  - SUPABASE_URL")
        logger.error("  - SUPABASE_DB_PASSWORD")
        sys.exit(1)

    db_url = supabase_url.replace('https://', 'postgresql://postgres:')
    db_url = db_url.replace('.supabase.co', '.supabase.co:5432/postgres')

    if supabase_password:
        db_url = db_url.replace('postgres:', f'postgres:{supabase_password}@')

    try:
        conn = psycopg2.connect(db_url)
        logger.info("✓ Database connection successful")
        return conn
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        sys.exit(1)


def check_migration_status(conn):
    """Check if migration has already been applied"""
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'code_embeddings'
            );
        """)

        exists = cursor.fetchone()[0]

        if exists:
            logger.warning("⚠ Migration appears to have been applied already")
            logger.warning("  Table 'code_embeddings' exists")

            response = input(
                "\nContinue anyway? This may cause errors. (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Migration cancelled by user")
                sys.exit(0)
        else:
            logger.info("✓ Migration not yet applied (tables do not exist)")

    except Exception as e:
        logger.error(f"✗ Failed to check migration status: {e}")
        sys.exit(1)
    finally:
        cursor.close()


def check_pgvector_extension(conn):
    """Check if pgvector extension is available"""
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_available_extensions
                WHERE name = 'vector'
            );
        """)

        available = cursor.fetchone()[0]

        if not available:
            logger.error("✗ pgvector extension not available")
            logger.error("  Please install pgvector extension first:")
            logger.error("  https://github.com/pgvector/pgvector")
            sys.exit(1)

        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_extension
                WHERE extname = 'vector'
            );
        """)

        enabled = cursor.fetchone()[0]

        if enabled:
            logger.info("✓ pgvector extension already enabled")
        else:
            logger.info("⚠ pgvector extension available but not enabled")
            logger.info("  Migration will enable it")

    except Exception as e:
        logger.error(f"✗ Failed to check pgvector extension: {e}")
        sys.exit(1)
    finally:
        cursor.close()


def run_migration(conn, migration_file):
    """Execute migration SQL file"""
    cursor = conn.cursor()

    try:
        with open(migration_file, 'r') as f:
            migration_sql = f.read()

        logger.info(f"Executing migration: {migration_file}")
        logger.info("=" * 70)

        cursor.execute(migration_sql)
        conn.commit()

        logger.info("=" * 70)
        logger.info("✓ Migration executed successfully")

        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('code_embeddings', 'code_patterns', 'code_relationships', 'embedding_cache_stats')
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        logger.info(f"\nCreated {len(tables)} tables:")
        for table in tables:
            logger.info(f"  - {table[0]}")

    except Exception as e:
        conn.rollback()
        logger.error(f"✗ Migration failed: {e}")
        logger.error("\nMigration rolled back")
        sys.exit(1)
    finally:
        cursor.close()


def verify_migration(conn):
    """Verify migration was successful"""
    cursor = conn.cursor()

    try:
        logger.info("\nVerifying migration...")

        cursor.execute("""
            SELECT table_name,
                   (SELECT count(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public'
            AND table_name IN ('code_embeddings', 'code_patterns', 'code_relationships', 'embedding_cache_stats')
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()

        if len(tables) != 4:
            logger.error(f"✗ Expected 4 tables, found {len(tables)}")
            sys.exit(1)

        logger.info("✓ All tables created successfully:")
        for table_name, column_count in tables:
            logger.info(f"  - {table_name}: {column_count} columns")

        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename IN ('code_embeddings', 'code_patterns', 'code_relationships')
            AND indexname LIKE '%_idx';
        """)

        indexes = cursor.fetchall()
        logger.info(f"\n✓ Created {len(indexes)} indexes for performance")

        cursor.execute(
            "SELECT extname FROM pg_extension WHERE extname = 'vector';")
        pgvector = cursor.fetchone()

        if pgvector:
            logger.info("✓ pgvector extension enabled")
        else:
            logger.warning("⚠ pgvector extension not found (may cause issues)")

    except Exception as e:
        logger.error(f"✗ Verification failed: {e}")
        sys.exit(1)
    finally:
        cursor.close()


def main():
    """Main migration workflow"""
    logger.info("=" * 70)
    logger.info("Knowledge Graph Migration Tool")
    logger.info("Phase 1 Week 5: Database Setup")
    logger.info("=" * 70)

    migrations_dir = Path(__file__).parent
    migration_files = [
        migrations_dir / "001_create_knowledge_graph_tables.sql",
        migrations_dir / "002_add_rls_policies.sql"
    ]

    for migration_file in migration_files:
        if not migration_file.exists():
            logger.error(f"✗ Migration file not found: {migration_file}")
            sys.exit(1)

    logger.info(f"\nFound {len(migration_files)} migration files")

    logger.info("\n--- Pre-flight Checks ---")
    conn = get_db_connection()

    try:
        check_migration_status(conn)
        check_pgvector_extension(conn)

        logger.info("\n--- Ready to Execute Migrations ---")
        logger.info("This will:")
        logger.info("  1. Create tables (code_embeddings, code_patterns, etc.)")
        logger.info("  2. Create indexes and triggers")
        logger.info("  3. Enable Row Level Security (RLS) policies")
        logger.info("\nRLS policies ensure proper access control for all tables.")

        response = input("\nProceed with migrations? (yes/no): ")

        if response.lower() != 'yes':
            logger.info("Migration cancelled by user")
            sys.exit(0)

        logger.info("\n--- Executing Migrations ---")
        for idx, migration_file in enumerate(migration_files, 1):
            logger.info(f"\n[{idx}/{len(migration_files)}] Running: {migration_file.name}")
            run_migration(conn, migration_file)

        logger.info("\n--- Verification ---")
        verify_migration(conn)

        cursor = conn.cursor()
        cursor.execute("""
            SELECT schemaname, tablename, rowsecurity
            FROM pg_tables
            WHERE tablename IN ('code_embeddings', 'code_patterns', 'code_relationships', 'embedding_cache_stats')
            ORDER BY tablename;
        """)
        tables_rls = cursor.fetchall()
        logger.info("\n✓ Row Level Security status:")
        for schema, table, rls_enabled in tables_rls:
            status = "✓ ENABLED" if rls_enabled else "✗ DISABLED"
            logger.info(f"  - {table}: {status}")
        cursor.close()

        logger.info("\n" + "=" * 70)
        logger.info("✓ All migrations completed successfully!")
        logger.info("=" * 70)

        logger.info("\nNext steps:")
        logger.info("  1. Set OPENAI_API_KEY for embedding generation")
        logger.info("  2. Set REDIS_URL for caching (optional)")
        logger.info("  3. Run: python agents/dev_agent/examples/knowledge_graph_example.py")

    except KeyboardInterrupt:
        logger.info("\n\nMigration cancelled by user")
        sys.exit(0)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
