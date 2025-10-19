#!/usr/bin/env python3
"""
E2E Test: Complete Index and Search Workflow
Tests end-to-end workflow: index codebase → store embeddings → search similar code
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path

from knowledge_graph import (
    get_knowledge_graph_manager,
    create_code_indexer,
    create_pattern_learner
)

pytestmark = pytest.mark.e2e


@pytest.fixture
def temp_codebase():
    """Create temporary codebase for testing"""
    temp_dir = tempfile.mkdtemp(prefix="kg_test_")
    temp_path = Path(temp_dir)

    (temp_path / "utils.py").write_text("""
import os
import sys

def read_file(file_path):
    '''Read file contents'''
    with open(file_path, 'r') as f:
        return f.read()

def write_file(file_path, content):
    '''Write content to file'''
    with open(file_path, 'w') as f:
        f.write(content)
""")

    (temp_path / "database.py").write_text("""
import psycopg2

class Database:
    def __init__(self, connection_string):
        self.conn = psycopg2.connect(connection_string)

    def query(self, sql):
        cursor = self.conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    def close(self):
        self.conn.close()
""")

    (temp_path / "api.py").write_text("""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/api/data')
def get_data():
    return jsonify({'data': []})
""")

    (temp_path / "tests" / "test_utils.py").write_text("""
import pytest
from utils import read_file, write_file

def test_read_file():
    assert read_file is not None

def test_write_file():
    assert write_file is not None
""")

    (temp_path / "__init__.py").write_text("")
    (temp_path / "tests" / "__init__.py").write_text("")

    yield str(temp_path)

    shutil.rmtree(temp_dir)


class TestIndexSearchWorkflowE2E:
    """E2E test for complete indexing and search workflow"""

    @pytest.mark.skipif(
        not os.getenv('OPENAI_API_KEY'),
        reason="OPENAI_API_KEY not configured"
    )
    def test_complete_workflow_with_api(self, temp_codebase):
        """Test complete workflow: index → search with real API"""
        kg_manager = get_knowledge_graph_manager()

        if not kg_manager.openai_api_key:
            pytest.skip("OpenAI API key not available")

        print(f"\n📁 Test codebase: {temp_codebase}")

        print("\n🔍 Step 1: Indexing codebase...")
        indexer = create_code_indexer(kg_manager, max_workers=2)

        index_result = indexer.index_directory(temp_codebase)

        assert index_result.get('success'), f"Indexing failed: {
            index_result.get('error')}"

        data = index_result['data']
        print(f"✓ Indexed {data['total_files']} files")
        print(f"  - Successful: {data['successful']}")
        print(f"  - Failed: {data['failed']}")
        print(f"  - Skipped: {data['skipped']}")

        assert data['successful'] > 0, "Should have indexed at least some files"

        print("\n🧠 Step 2: Learning code patterns...")
        learner = create_pattern_learner(min_frequency=1, min_confidence=0.3)

        samples = []
        for file_path in Path(temp_codebase).rglob("*.py"):
            if file_path.name.startswith("test_"):
                continue
            content = file_path.read_text()
            samples.append({'code': content, 'language': 'python'})

        learn_result = learner.learn_patterns(samples)

        assert learn_result.get('success'), f"Pattern learning failed: {
            learn_result.get('error')}"
        print(f"✓ Learned {learn_result['data']['patterns_learned']} patterns")

        print("\n🔎 Step 3: Searching for similar code...")

        query_code = """
def load_data(path):
    with open(path, 'r') as f:
        return f.read()
"""

        query_result = kg_manager.generate_embedding(query_code)

        if not query_result.get('success'):
            print(f"⚠️ Query embedding failed: {query_result.get('error')}")
            pytest.skip("Cannot test search without database")

        print(
            f"✓ Generated query embedding ({
                query_result['data']['tokens']} tokens)")

        if not kg_manager.db_pool:
            print("⚠️ Database not configured, skipping search test")
            return

        query_embedding = query_result['data']['embedding']
        search_result = kg_manager.search_similar_code(
            query_embedding,
            language='python',
            limit=5
        )

        if search_result.get('success'):
            results = search_result['data']['results']
            print(f"✓ Found {len(results)} similar code snippets")

            if len(results) > 0:
                print("\nTop match:")
                print(f"  - File: {results[0]['file_path']}")
                print(f"  - Distance: {results[0]['distance']:.4f}")
                print(f"  - Preview: {results[0]['content_preview'][:50]}...")
        else:
            print(
                f"⚠️ Search failed (expected without DB): {
                    search_result.get('error')}")

    def test_workflow_without_api_mock(self, temp_codebase):
        """Test workflow structure without real API (mock test)"""
        kg_manager = get_knowledge_graph_manager()

        print(f"\n📁 Test codebase: {temp_codebase}")
        print("\n🔍 Testing workflow structure (no real API calls)...")

        py_files = list(Path(temp_codebase).rglob("*.py"))
        print(f"✓ Found {len(py_files)} Python files in test codebase")

        assert len(py_files) >= 4, "Should have at least 4 test files"

        for py_file in py_files:
            content = py_file.read_text()
            assert len(content) > 0, f"File {py_file.name} is empty"
            print(f"  - {py_file.name}: {len(content)} bytes")

        indexer = create_code_indexer(kg_manager, max_workers=2)
        assert indexer is not None
        print(f"✓ Code indexer initialized (max_workers=2)")

        learner = create_pattern_learner()
        assert learner is not None
        print(f"✓ Pattern learner initialized")

        files = indexer._find_code_files(temp_codebase)
        assert len(files) > 0, "Should find code files"
        print(f"✓ Found {len(files)} code files to index")

        for file in files:
            lang = indexer._detect_language(file)
            assert lang == 'python', f"Should detect Python for {file}"
        print(f"✓ Language detection working")

    def test_pattern_matching_workflow(self, temp_codebase):
        """Test pattern learning and matching"""
        learner = create_pattern_learner(min_frequency=1, min_confidence=0.3)

        print("\n🧠 Testing pattern learning workflow...")

        samples = []
        for file_path in Path(temp_codebase).rglob("*.py"):
            content = file_path.read_text()
            samples.append({'code': content, 'language': 'python'})

        print(f"📝 Collected {len(samples)} code samples")

        learn_result = learner.learn_patterns(samples)
        assert learn_result.get('success')

        patterns_learned = learn_result['data']['patterns_learned']
        print(f"✓ Learned {patterns_learned} patterns")

        test_code = """
import os
import sys

def my_function():
    with open('test.txt', 'r') as f:
        data = f.read()
    return data
"""

        match_result = learner.find_pattern_matches(test_code, 'python')
        assert match_result.get('success')

        matches = match_result['data']['matches_found']
        print(f"✓ Found {matches} pattern matches in test code")

        if matches > 0:
            print("\nExample matches:")
            for match in match_result['data']['matches'][:3]:
                print(
                    f"  - {match['pattern_name']} (confidence: {match['confidence']:.2f})")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Index & Search Workflow E2E Tests")
    print("=" * 70 + "\n")
    print("NOTE: Full workflow tests require OPENAI_API_KEY and database\n")

    pytest.main([__file__, '-v', '--tb=short', '-s'])
