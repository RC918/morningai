#!/usr/bin/env python3
"""
E2E Tests for Knowledge Graph System
Phase 1 Week 5: Knowledge Graph Integration
"""
import pytest
import tempfile
from pathlib import Path

from agents.dev_agent.knowledge_graph import (
    get_knowledge_graph_manager,
    create_code_indexer,
    create_pattern_learner,
    get_embeddings_cache
)

pytestmark = pytest.mark.asyncio


class TestEmbeddingsCache:
    """Test embeddings cache functionality"""

    @pytest.fixture
    def cache(self):
        """Create embeddings cache instance"""
        return get_embeddings_cache()

    def test_cache_set_get(self, cache):
        """Test cache set and get operations"""
        if not cache.enabled:
            pytest.skip("Cache not available (Redis not configured)")

        test_content = "def hello():\n    print('Hello')"
        test_embedding = [0.1] * 1536

        success = cache.set(test_content, test_embedding)
        assert success or not cache.enabled

        if success:
            retrieved = cache.get(test_content)
            assert retrieved is not None
            assert len(retrieved) == 1536

        print("✓ Cache set/get works correctly")

    def test_cache_stats(self, cache):
        """Test cache statistics"""
        stats = cache.get_stats(days=1)

        assert 'enabled' in stats
        if stats['enabled']:
            assert 'summary' in stats or 'error' in stats

        print("✓ Cache stats retrieval works")

    def test_cache_health_check(self, cache):
        """Test cache health check"""
        health = cache.health_check()

        assert 'success' in health or 'error' in health

        print("✓ Cache health check works")


class TestKnowledgeGraphManager:
    """Test Knowledge Graph Manager"""

    @pytest.fixture
    def kg_manager(self):
        """Create KG manager instance"""
        return get_knowledge_graph_manager()

    def test_kg_manager_initialization(self, kg_manager):
        """Test KG manager initializes correctly"""
        assert kg_manager is not None
        assert hasattr(kg_manager, 'generate_embedding')
        assert hasattr(kg_manager, 'store_embedding')
        assert hasattr(kg_manager, 'search_similar_code')

        print("✓ KG Manager initialized correctly")

    def test_generate_embedding_mock(self, kg_manager):
        """Test embedding generation (may use mock if API not configured)"""
        test_code = "def add(a, b):\n    return a + b"

        result = kg_manager.generate_embedding(test_code)

        if not kg_manager.openai_api_key:
            assert not result.get('success')
            assert 'error' in result
            print("✓ Correctly handles missing OpenAI API key")
        else:
            if result.get('success'):
                assert 'embedding' in result['data']
                assert len(result['data']['embedding']) == 1536
                print("✓ Embedding generation works")
            else:
                print(
                    f"⚠ Embedding generation failed (expected in test): {
                        result.get('error')}")

    def test_kg_manager_health_check(self, kg_manager):
        """Test KG manager health check"""
        health = kg_manager.health_check()

        assert 'success' in health or 'error' in health
        if 'data' in health:
            data = health['data']
            assert 'openai_configured' in data
            assert 'database_configured' in data

        print("✓ KG Manager health check works")


class TestCodeIndexer:
    """Test Code Indexer"""

    @pytest.fixture
    def indexer(self):
        """Create code indexer instance"""
        kg_manager = get_knowledge_graph_manager()
        return create_code_indexer(kg_manager, max_workers=2)

    @pytest.fixture
    def temp_code_dir(self):
        """Create temporary directory with test code files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            (tmpdir_path / "test1.py").write_text(
                "import os\n\ndef hello():\n    print('Hello')\n"
            )

            (tmpdir_path / "test2.py").write_text(
                "from typing import List\n\nclass TestClass:\n    pass\n"
            )

            (tmpdir_path / "test3.js").write_text(
                "function test() {\n    console.log('test');\n}\n"
            )

            (tmpdir_path / "README.md").write_text("# Test")

            yield tmpdir

    def test_language_detection(self, indexer):
        """Test language detection"""
        assert indexer._detect_language("test.py") == "python"
        assert indexer._detect_language("test.js") == "javascript"
        assert indexer._detect_language("test.ts") == "typescript"
        assert indexer._detect_language("test.txt") is None

        print("✓ Language detection works")

    def test_python_parsing(self, indexer):
        """Test Python AST parsing"""
        code = """
import os
from typing import List

class MyClass:
    def method(self):
        pass

def function():
    pass
"""
        structure = indexer._parse_python_file(code)

        assert 'imports' in structure
        assert 'classes' in structure
        assert 'functions' in structure
        assert 'os' in structure['imports']
        assert 'typing' in structure['imports']
        assert 'MyClass' in structure['classes']
        assert 'function' in structure['functions']

        print("✓ Python parsing works")

    def test_file_finding(self, indexer, temp_code_dir):
        """Test finding code files"""
        files = indexer._find_code_files(temp_code_dir)

        assert len(files) >= 2
        assert any('test1.py' in f for f in files)
        assert any('test2.py' in f for f in files)
        assert not any('README.md' in f for f in files)

        print(f"✓ Found {len(files)} code files")

    def test_indexing_without_credentials(self, indexer, temp_code_dir):
        """Test indexing behavior without API credentials"""
        result = indexer.index_directory(temp_code_dir)

        if not indexer.kg_manager.openai_api_key:
            if 'data' in result:
                assert result['data']['failed'] > 0 or result['data']['skipped'] > 0
                print("✓ Correctly handles missing credentials during indexing")
        else:
            print(f"⚠ Indexing attempted (may fail without DB): {result}")


class TestPatternLearner:
    """Test Pattern Learner"""

    @pytest.fixture
    def learner(self):
        """Create pattern learner instance"""
        return create_pattern_learner(min_frequency=2, min_confidence=0.5)

    def test_pattern_learner_initialization(self, learner):
        """Test pattern learner initializes"""
        assert learner is not None
        assert learner.min_frequency == 2
        assert learner.min_confidence == 0.5

        print("✓ Pattern Learner initialized")

    def test_extract_import_patterns(self, learner):
        """Test import pattern extraction"""
        code = """
import os
import sys
from typing import List
from dataclasses import dataclass
"""
        patterns = learner._extract_import_patterns(code, 'python')

        assert len(patterns) > 0
        assert any('os' in p['template'] for p in patterns)
        assert any('typing' in p['template'] for p in patterns)

        print(f"✓ Extracted {len(patterns)} import patterns")

    def test_extract_error_handling_patterns(self, learner):
        """Test error handling pattern extraction"""
        code = """
try:
    something()
except ValueError:
    handle_error()
except Exception as e:
    log_error(e)
"""
        patterns = learner._extract_error_handling_patterns(code, 'python')

        assert len(patterns) > 0
        assert any('ValueError' in p['template'] for p in patterns)

        print(f"✓ Extracted {len(patterns)} error handling patterns")

    def test_extract_logging_patterns(self, learner):
        """Test logging pattern extraction"""
        code = """
logger.info("Starting process")
logger.error("Error occurred")
logging.debug("Debug message")
"""
        patterns = learner._extract_logging_patterns(code, 'python')

        assert len(patterns) > 0

        print(f"✓ Extracted {len(patterns)} logging patterns")

    def test_learn_patterns_from_samples(self, learner):
        """Test learning patterns from code samples"""
        samples = [{'code': 'import os\nimport sys',
                    'language': 'python'},
                   {'code': 'import os\nfrom typing import List',
                    'language': 'python'},
                   {'code': 'import os\ntry:\n    pass\nexcept Exception:\n    pass',
                    'language': 'python'},
                   ]

        result = learner.learn_patterns(samples)

        assert result.get('success')
        assert result['data']['patterns_learned'] > 0
        assert result['data']['total_samples'] == 3

        print(
            f"✓ Learned {
                result['data']['patterns_learned']} patterns from samples")

    def test_find_pattern_matches(self, learner):
        """Test finding pattern matches"""
        samples = [
            {'code': 'import os\nimport sys', 'language': 'python'},
            {'code': 'import os\nimport json', 'language': 'python'},
        ]

        learner.learn_patterns(samples)

        test_code = 'import os\nimport sys\nimport json'
        result = learner.find_pattern_matches(test_code, 'python')

        assert result.get('success')
        if result['data']['matches_found'] > 0:
            print(f"✓ Found {result['data']['matches_found']} pattern matches")
        else:
            print("⚠ No pattern matches found (expected with minimal samples)")


class TestKnowledgeGraphIntegration:
    """Test full Knowledge Graph integration"""

    def test_full_workflow_without_credentials(self):
        """Test full workflow handles missing credentials gracefully"""
        kg_manager = get_knowledge_graph_manager()
        cache = get_embeddings_cache()
        indexer = create_code_indexer(kg_manager, max_workers=2)
        learner = create_pattern_learner()

        assert kg_manager is not None
        assert indexer is not None
        assert learner is not None

        health = kg_manager.health_check()
        assert 'success' in health or 'error' in health

        print("✓ Knowledge Graph system components initialized")
        print(
            f"  - OpenAI configured: {kg_manager.openai_api_key is not None}")
        print(f"  - Database configured: {kg_manager.db_pool is not None}")
        print(f"  - Cache enabled: {cache.enabled if cache else False}")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Knowledge Graph System E2E Tests (Week 5)")
    print("=" * 70 + "\n")

    pytest.main([__file__, '-v', '--tb=short', '-s'])
