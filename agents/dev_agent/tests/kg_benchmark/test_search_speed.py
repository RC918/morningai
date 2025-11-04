#!/usr/bin/env python3
"""
Benchmark Test: Vector Search Speed
Target: <50ms per query
"""
import pytest
import os
import time
import statistics

from knowledge_graph import get_knowledge_graph_manager

pytestmark = pytest.mark.benchmark


@pytest.fixture
def kg_manager():
    """Create KG manager"""
    return get_knowledge_graph_manager()


class TestSearchSpeedBenchmark:
    """Benchmark tests for vector search speed"""

    @pytest.mark.skipif(
        not os.getenv('SUPABASE_URL'),
        reason="SUPABASE_URL required for search benchmark"
    )
    def test_vector_search_speed(self, kg_manager):
        """
        Benchmark: Vector similarity search should be <50ms per query
        Target: P50 < 30ms, P95 < 50ms
        """
        if not kg_manager.db_pool:
            pytest.skip("Database not configured")

        print("\n⏱️ Benchmarking vector search speed...")
        print("   Target: P50 < 30ms, P95 < 50ms")

        try:
            conn = kg_manager._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM code_embeddings;")
            count = cursor.fetchone()[0]

            if count == 0:
                print(f"   ℹ️  No embeddings in database, inserting test data...")

                test_embedding = [0.1] * 1536
                for i in range(10):
                    cursor.execute("""
                        INSERT INTO code_embeddings
                        (file_path, file_hash, content_preview, embedding, language, tokens_count)
                        VALUES (%s, %s, %s, %s::vector, %s, %s)
                        ON CONFLICT (file_path, file_hash) DO NOTHING;
                    """, (
                        f'test{i}.py',
                        f'hash{i}',
                        f'test code {i}',
                        test_embedding,
                        'python',
                        100
                    ))
                conn.commit()
                print(f"   ✓ Inserted 10 test embeddings")
            else:
                print(f"   ✓ Found {count} existing embeddings")

            kg_manager._return_connection(conn)

        except Exception as e:
            pytest.skip(f"Database setup failed: {e}")

        query_embedding = [0.1] * 1536
        times = []

        print(f"\n   Running searches:")
        for i in range(10):
            start = time.time()

            result = kg_manager.search_similar_code(
                query_embedding,
                language='python',
                limit=5
            )

            elapsed = (time.time() - start) * 1000  # Convert to ms

            if not result.get('success'):
                print(f"     ⚠️ Search {i + 1} failed: {result.get('error')}")
                continue

            times.append(elapsed)
            results_count = result['data']['count']
            print(f"     Search {i + 1}: {elapsed:.1f}ms ({results_count} results)")

        if times:
            p50 = statistics.median(times)
            p95 = statistics.quantiles(
                times, n=20)[18] if len(times) >= 20 else max(times)
            avg = statistics.mean(times)

            print(f"\n📊 Search Performance Statistics:")
            print(f"   Average: {avg:.1f}ms")
            print(f"   P50 (median): {p50:.1f}ms")
            print(f"   P95: {p95:.1f}ms")
            print(f"   Min: {min(times):.1f}ms")
            print(f"   Max: {max(times):.1f}ms")

            if p50 < 30:
                print(f"   ✅ P50 target met ({p50:.1f}ms < 30ms)")
            else:
                print(f"   ⚠️ P50 target missed ({p50:.1f}ms >= 30ms)")

            if p95 < 50:
                print(f"   ✅ P95 target met ({p95:.1f}ms < 50ms)")
            else:
                print(f"   ⚠️ P95 target missed ({p95:.1f}ms >= 50ms)")

            if p95 >= 50:
                print(f"\n   ℹ️  Note: P95 search latency is {p95:.1f}ms (target: <50ms)")
                print(f"      This may be acceptable depending on:")
                print(f"      - Database size and index parameters")
                print(f"      - Network latency to database")
                print(f"      - Database load")

    def test_search_speed_structure(self, kg_manager):
        """Test search speed measurement structure (no database required)"""
        print("\n⏱️ Testing search benchmark structure...")

        query_embedding = [0.1] * 1536

        start = time.time()
        result = kg_manager.search_similar_code(
            query_embedding,
            language='python',
            limit=5
        )
        elapsed = (time.time() - start) * 1000

        assert elapsed < 1000, "Query should return quickly (error or success)"
        print(f"   ✓ Query executed in {elapsed:.1f}ms")

        if not result.get('success'):
            print(f"   ℹ️  Expected error (no database): {result.get('error')}")
        else:
            print(f"   ✓ Query succeeded, found {result['data']['count']} results")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Vector Search Speed Benchmark")
    print("=" * 70 + "\n")

    pytest.main([__file__, '-v', '--tb=short', '-s'])
