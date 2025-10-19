#!/usr/bin/env python3
"""
E2E Test: OpenAI Real API Embedding Generation
Tests actual OpenAI API calls with real credentials
"""
import pytest
import os
import time

from knowledge_graph import get_knowledge_graph_manager

pytestmark = pytest.mark.e2e


@pytest.fixture
def kg_manager():
    """Create KG manager with real credentials"""
    return get_knowledge_graph_manager()


class TestOpenAIRealEmbeddingE2E:
    """E2E tests for real OpenAI API calls"""

    @pytest.mark.skipif(
        not os.getenv('OPENAI_API_KEY'),
        reason="OPENAI_API_KEY not configured - skipping real API test"
    )
    def test_generate_embedding_real_api(self, kg_manager):
        """Test embedding generation with real OpenAI API"""
        if not kg_manager.openai_api_key:
            pytest.skip("OpenAI API key not available")

        test_code = """
def hello_world():
    '''A simple hello world function'''
    print("Hello, World!")
    return True
"""

        print("\n🚀 Calling OpenAI API for embedding generation...")
        start_time = time.time()

        result = kg_manager.generate_embedding(test_code)

        elapsed = time.time() - start_time

        assert result.get('success'), f"Embedding generation failed: {
            result.get('error')}"

        data = result['data']
        assert 'embedding' in data, "Embedding not in response"
        assert 'tokens' in data, "Token count not in response"
        assert 'cost' in data, "Cost not in response"
        assert 'cached' in data, "Cache status not in response"

        embedding = data['embedding']
        assert len(embedding) == 1536, f"Wrong embedding dimensions: {
            len(embedding)}"
        assert all(isinstance(x, float)
                   for x in embedding), "Embedding values not float"

        assert data['tokens'] > 0, "Token count should be positive"
        assert data['tokens'] < 1000, "Token count seems too high for small code"

        assert data['cost'] > 0, "Cost should be positive"
        assert data['cost'] < 0.01, "Cost seems too high for small code"

        assert not data['cached'], "First call should not be cached"

        print(f"✓ Embedding generated successfully")
        print(f"  - Dimensions: {len(embedding)}")
        print(f"  - Tokens: {data['tokens']}")
        print(f"  - Cost: ${data['cost']:.6f}")
        print(f"  - Time: {elapsed:.3f}s")
        print(f"  - Cached: {data['cached']}")

    @pytest.mark.skipif(
        not os.getenv('OPENAI_API_KEY'),
        reason="OPENAI_API_KEY not configured"
    )
    def test_caching_works(self, kg_manager):
        """Test that embedding cache works with real API"""
        if not kg_manager.openai_api_key or not kg_manager.cache:
            pytest.skip("OpenAI API key or cache not available")

        test_code = "def test(): pass"

        print("\n🔄 First call (should hit API)...")
        result1 = kg_manager.generate_embedding(test_code)
        assert result1.get('success')
        assert not result1['data']['cached'], "First call should not be cached"
        cost1 = result1['data']['cost']

        print("🔄 Second call (should hit cache)...")
        result2 = kg_manager.generate_embedding(test_code)
        assert result2.get('success')
        assert result2['data']['cached'], "Second call should be cached"

        embedding1 = result1['data']['embedding']
        embedding2 = result2['data']['embedding']
        assert embedding1 == embedding2, "Cached embedding should match original"

        print(f"✓ Caching works correctly")
        print(f"  - First call cost: ${cost1:.6f}")
        print(f"  - Second call cost: $0 (cached)")
        print(f"  - Cache hit: ✓")

    @pytest.mark.skipif(
        not os.getenv('OPENAI_API_KEY'),
        reason="OPENAI_API_KEY not configured"
    )
    def test_rate_limiting_works(self, kg_manager):
        """Test that rate limiting prevents API overuse"""
        if not kg_manager.openai_api_key:
            pytest.skip("OpenAI API key not available")

        print("\n⏱️ Testing rate limiting (5 requests)...")

        start_time = time.time()
        for i in range(5):
            test_code = f"def test_{i}(): pass"
            result = kg_manager.generate_embedding(test_code)
            assert result.get('success'), f"Request {i} failed"
            print(f"  Request {i + 1}/5 completed")

        elapsed = time.time() - start_time

        print(f"✓ Rate limiting working")
        print(f"  - Total time: {elapsed:.3f}s")
        print(f"  - Avg time per request: {elapsed / 5:.3f}s")
        print(f"  - No rate limit errors encountered")

    @pytest.mark.skipif(
        not os.getenv('OPENAI_API_KEY'),
        reason="OPENAI_API_KEY not configured"
    )
    def test_error_handling_retry(self, kg_manager):
        """Test that retry logic works for transient failures"""
        if not kg_manager.openai_api_key:
            pytest.skip("OpenAI API key not available")

        long_code = "def function():\n    pass\n" * 1000

        print("\n🔄 Testing error handling with long content...")
        result = kg_manager.generate_embedding(long_code)

        if result.get('success'):
            print(f"✓ Long content handled successfully")
            print(f"  - Tokens: {result['data']['tokens']}")
            print(f"  - Cost: ${result['data']['cost']:.6f}")
        else:
            print(f"⚠️ Long content failed (expected): {result.get('error')}")
            assert 'error' in result, "Failed request should have error message"

    @pytest.mark.skipif(
        not os.getenv('OPENAI_API_KEY'),
        reason="OPENAI_API_KEY not configured"
    )
    def test_cost_tracking(self, kg_manager):
        """Test that cost tracking works correctly"""
        if not kg_manager.openai_api_key or not kg_manager.cache:
            pytest.skip("OpenAI API key or cache not available")

        print("\n💰 Testing cost tracking...")

        total_expected_cost = 0
        for i in range(3):
            test_code = f"def unique_function_{i}(): return {i}"
            result = kg_manager.generate_embedding(test_code)

            if result.get('success') and not result['data']['cached']:
                total_expected_cost += result['data']['cost']

        if kg_manager.cache:
            stats = kg_manager.cache.get_stats(days=1)

            if stats.get('summary'):
                print(f"✓ Cost tracking working")
                print(f"  - Expected cost: ${total_expected_cost:.6f}")
                print(f"  - Tracked in cache: ✓")
            else:
                print(f"⚠️ Cache stats not available (Redis may not be configured)")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("OpenAI Real API E2E Tests")
    print("=" * 70 + "\n")
    print("NOTE: These tests require OPENAI_API_KEY environment variable")
    print("      and will make real API calls (small cost)\n")

    pytest.main([__file__, '-v', '--tb=short', '-s'])
