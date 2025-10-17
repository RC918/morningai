#!/usr/bin/env python3
"""
E2E Test: Database Migration Creates Tables
Tests that migration script correctly creates all required tables with pgvector
"""
import pytest
import os
import psycopg2
import subprocess
import time

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def temp_postgres():
    """Start temporary PostgreSQL with pgvector for testing"""
    container_name = "test-kg-postgres"

    try:
        subprocess.run(["docker", "--version"],
                       check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("Docker not available for integration testing")

    print("\n🐳 Starting temporary PostgreSQL container with pgvector...")
    subprocess.run([
        "docker", "run", "-d",
        "--name", container_name,
        "-e", "POSTGRES_PASSWORD=testpass",
        "-p", "5555:5432",
        "ankane/pgvector:latest"
    ], check=True, capture_output=True)

    time.sleep(5)
    max_retries = 10
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5555,
                user="postgres",
                password="testpass",
                database="postgres"
            )
            conn.close()
            print("✓ PostgreSQL is ready")
            break
        except psycopg2.OperationalError:
            if i == max_retries - 1:
                subprocess.run(
                    ["docker", "stop", container_name], capture_output=True)
                subprocess.run(["docker", "rm", container_name],
                               capture_output=True)
                pytest.skip("PostgreSQL failed to start")
            time.sleep(2)

    db_url = "postgresql://postgres:testpass@localhost:5555/postgres"

    yield db_url

    print("\n🧹 Cleaning up temporary PostgreSQL container...")
    subprocess.run(["docker", "stop", container_name], capture_output=True)
    subprocess.run(["docker", "rm", container_name], capture_output=True)


class TestMigrationCreatesTablesE2E:
    """E2E test for database migration"""

    def test_pgvector_extension_available(self, temp_postgres):
        """Test that pgvector extension is available"""
        conn = psycopg2.connect(temp_postgres)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_available_extensions
                WHERE name = 'vector'
            );
        """)

        available = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        assert available, "pgvector extension not available in PostgreSQL"
        print("✓ pgvector extension is available")

    def test_migration_creates_all_tables(self, temp_postgres):
        """Test that migration script creates all required tables"""
        migration_path = "agents/dev_agent/migrations/001_create_knowledge_graph_tables.sql"

        if not os.path.exists(migration_path):
            pytest.skip("Migration SQL file not found")

        with open(migration_path, 'r') as f:
            migration_sql = f.read()

        conn = psycopg2.connect(temp_postgres)
        cursor = conn.cursor()

        try:
            cursor.execute(migration_sql)
            conn.commit()
            print("✓ Migration executed successfully")
        except Exception as e:
            conn.rollback()
            pytest.fail(f"Migration failed: {e}")

        expected_tables = [
            'code_embeddings',
            'code_patterns',
            'code_relationships',
            'embedding_cache_stats'
        ]

        for table_name in expected_tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                );
            """, (table_name,))

            exists = cursor.fetchone()[0]
            assert exists, f"Table {table_name} was not created"
            print(f"✓ Table '{table_name}' exists")

        cursor.close()
        conn.close()

    def test_migration_creates_indexes(self, temp_postgres):
        """Test that migration creates required indexes"""
        migration_path = "agents/dev_agent/migrations/001_create_knowledge_graph_tables.sql"

        with open(migration_path, 'r') as f:
            migration_sql = f.read()

        conn = psycopg2.connect(temp_postgres)
        cursor = conn.cursor()

        cursor.execute(migration_sql)
        conn.commit()

        cursor.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'code_embeddings'
            AND indexname LIKE '%embedding%';
        """)

        indexes = cursor.fetchall()
        assert len(indexes) > 0, "No embedding index found"

        index_def = indexes[0][1]
        assert 'hnsw' in index_def.lower(), "Index is not using HNSW"
        print(f"✓ HNSW index created: {indexes[0][0]}")

        cursor.close()
        conn.close()

    def test_migration_creates_unique_constraints(self, temp_postgres):
        """Test that unique constraints are created"""
        migration_path = "agents/dev_agent/migrations/001_create_knowledge_graph_tables.sql"

        with open(migration_path, 'r') as f:
            migration_sql = f.read()

        conn = psycopg2.connect(temp_postgres)
        cursor = conn.cursor()

        cursor.execute(migration_sql)
        conn.commit()

        cursor.execute("""
            INSERT INTO code_embeddings
            (file_path, file_hash, content_preview, embedding, language, tokens_count)
            VALUES
            ('test.py', 'hash123', 'preview', '[0.1]'::vector, 'python', 100);
        """)
        conn.commit()

        try:
            cursor.execute("""
                INSERT INTO code_embeddings
                (file_path, file_hash, content_preview, embedding, language, tokens_count)
                VALUES
                ('test.py', 'hash123', 'preview2', '[0.2]'::vector, 'python', 200);
            """)
            conn.commit()
            pytest.fail("Duplicate insert should have failed")
        except psycopg2.IntegrityError:
            conn.rollback()
            print("✓ Unique constraint working (duplicate rejected)")

        cursor.close()
        conn.close()

    def test_vector_operations_work(self, temp_postgres):
        """Test that pgvector operations work correctly"""
        migration_path = "agents/dev_agent/migrations/001_create_knowledge_graph_tables.sql"

        with open(migration_path, 'r') as f:
            migration_sql = f.read()

        conn = psycopg2.connect(temp_postgres)
        cursor = conn.cursor()

        cursor.execute(migration_sql)
        conn.commit()

        test_embedding = [0.1] * 1536  # 1536-dimensional vector

        cursor.execute("""
            INSERT INTO code_embeddings
            (file_path, file_hash, content_preview, embedding, language, tokens_count)
            VALUES
            ('test1.py', 'hash1', 'test code', %s::vector, 'python', 100);
        """, (test_embedding,))

        cursor.execute("""
            INSERT INTO code_embeddings
            (file_path, file_hash, content_preview, embedding, language, tokens_count)
            VALUES
            ('test2.py', 'hash2', 'similar code', %s::vector, 'python', 120);
        """, (test_embedding,))

        conn.commit()

        query_embedding = [0.1] * 1536
        cursor.execute("""
            SELECT file_path, embedding <=> %s::vector AS distance
            FROM code_embeddings
            ORDER BY distance
            LIMIT 2;
        """, (query_embedding,))

        results = cursor.fetchall()
        assert len(results) == 2, "Vector search returned wrong number of results"
        assert results[0][1] == 0.0, "Distance should be 0 for identical vectors"
        print(f"✓ Vector similarity search works (distance: {results[0][1]})")

        cursor.close()
        conn.close()


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Knowledge Graph Migration E2E Tests")
    print("=" * 70 + "\n")

    pytest.main([__file__, '-v', '--tb=short', '-s'])
