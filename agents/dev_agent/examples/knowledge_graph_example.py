#!/usr/bin/env python3
"""
Knowledge Graph System Usage Example
Phase 1 Week 5
"""
import asyncio
import os

from agents.dev_agent.knowledge_graph import (
    get_knowledge_graph_manager,
    create_code_indexer,
    create_pattern_learner
)


async def example_1_embeddings():
    """Example 1: Generate and cache embeddings"""
    print("\n=== Example 1: Generate Embeddings ===")

    kg_manager = get_knowledge_graph_manager()

    test_code = """
def calculate_sum(numbers):
    '''Calculate the sum of a list of numbers'''
    total = 0
    for num in numbers:
        total += num
    return total
"""

    result = kg_manager.generate_embedding(test_code)

    if result.get('success'):
        data = result['data']
        print("✓ Generated embedding:")
        print(f"  - Dimensions: {len(data['embedding'])}")
        print(f"  - Tokens used: {data.get('tokens', 'N/A')}")
        print(f"  - Cost: ${data.get('cost', 0):.6f}")
        print(f"  - Cached: {data.get('cached', False)}")
    else:
        print(
            f"✗ Failed: {
                result.get(
                    'error',
                    {}).get(
                    'message',
                    'Unknown error')}")
        print(
            f"  Hint: {
                result.get(
                    'error',
                    {}).get(
                    'hint',
                    'Check configuration')}")


def example_2_code_indexing():
    """Example 2: Index a directory of code files"""
    print("\n=== Example 2: Index Code Directory ===")

    kg_manager = get_knowledge_graph_manager()
    indexer = create_code_indexer(kg_manager, max_workers=4)

    target_dir = os.path.join(os.path.dirname(__file__), '..')

    def progress_callback(progress):
        """Callback to display progress"""
        print(f"Progress: {progress.progress_percent:.1f}% - "
              f"Processing: {progress.current_file}")

    result = indexer.index_directory(
        target_dir,
        progress_callback=progress_callback
    )

    if result.get('success'):
        data = result['data']
        print("\n✓ Indexing completed:")
        print(f"  - Total files: {data['total_files']}")
        print(f"  - Successful: {data['successful']}")
        print(f"  - Failed: {data['failed']}")
        print(f"  - Skipped: {data['skipped']}")
        print(f"  - Time: {data['elapsed_time']:.2f}s")
        print(f"  - Speed: {data['files_per_second']:.2f} files/s")
    else:
        print(
            f"✗ Failed: {
                result.get(
                    'error',
                    {}).get(
                    'message',
                    'Unknown error')}")


def example_3_pattern_learning():
    """Example 3: Learn patterns from code samples"""
    print("\n=== Example 3: Learn Code Patterns ===")

    learner = create_pattern_learner(min_frequency=2, min_confidence=0.6)

    code_samples = [
        {
            'code': '''
import os
import sys
from typing import List

def process_data(data: List[str]):
    try:
        result = do_something(data)
        logger.info("Processing completed")
        return result
    except ValueError as e:
        logger.error(f"Processing failed: {e}")
        return None
''',
            'language': 'python'
        },
        {
            'code': '''
import os
import json
from pathlib import Path

def load_config(path: str):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Config file not found")
        return {}
''',
            'language': 'python'
        },
        {
            'code': '''
import os
from typing import Dict
import logging

logger = logging.getLogger(__name__)

def save_results(data: Dict):
    try:
        with open('results.json', 'w') as f:
            json.dump(data, f)
        logger.info("Results saved")
    except Exception as e:
        logger.error(f"Save failed: {e}")
''',
            'language': 'python'
        }
    ]

    result = learner.learn_patterns(code_samples)

    if result.get('success'):
        data = result['data']
        print(
            f"✓ Learned {
                data['patterns_learned']} patterns from {
                data['total_samples']} samples")
        print("\nPatterns discovered:")
        for pattern in data['patterns'][:10]:
            print(f"  - {pattern['type']}: {pattern['template']}")
            print(
                f"    Confidence: {
                    pattern['confidence']:.2%}, Frequency: {
                    pattern['frequency']}")
    else:
        print(
            f"✗ Failed: {
                result.get(
                    'error',
                    {}).get(
                    'message',
                    'Unknown error')}")


def example_4_pattern_matching():
    """Example 4: Find pattern matches in code"""
    print("\n=== Example 4: Pattern Matching ===")

    learner = create_pattern_learner(min_frequency=1, min_confidence=0.5)

    training_samples = [
        {'code': 'import os\nimport sys', 'language': 'python'},
        {'code': 'import os\nimport json', 'language': 'python'},
    ]

    learner.learn_patterns(training_samples)

    test_code = '''
import os
import sys
import json

def main():
    print("Hello")
'''

    result = learner.find_pattern_matches(test_code, 'python')

    if result.get('success'):
        data = result['data']
        print(f"✓ Found {data['matches_found']} pattern matches")
        if data['matches_found'] > 0:
            print("\nMatches:")
            for match in data['matches'][:5]:
                print(f"  - Pattern: {match['pattern_type']}")
                print(f"    Template: {match['template']}")
                print(f"    Code: {match['matched_code']}")
    else:
        print(
            f"✗ Failed: {
                result.get(
                    'error',
                    {}).get(
                    'message',
                    'Unknown error')}")


def example_5_similarity_search():
    """Example 5: Semantic code search"""
    print("\n=== Example 5: Semantic Code Search ===")

    kg_manager = get_knowledge_graph_manager()

    query_code = "def add(a, b): return a + b"

    embedding_result = kg_manager.generate_embedding(query_code)

    if embedding_result.get('success'):
        query_embedding = embedding_result['data']['embedding']

        search_result = kg_manager.search_similar_code(
            query_embedding,
            language='python',
            limit=5
        )

        if search_result.get('success'):
            data = search_result['data']
            print(f"✓ Found {data['count']} similar code snippets")
            for i, result in enumerate(data['results'][:5], 1):
                print(f"\n{i}. {result['file_path']}")
                print(f"   Similarity: {result['similarity']:.2%}")
                print(f"   Preview: {result['content_preview'][:100]}...")
        else:
            print(
                f"✗ Search failed: {
                    search_result.get(
                        'error',
                        {}).get(
                        'message',
                        'Unknown error')}")
    else:
        print(
            f"✗ Embedding failed: {
                embedding_result.get(
                    'error',
                    {}).get(
                    'message',
                    'Unknown error')}")


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("Knowledge Graph System Examples")
    print("=" * 70)

    print("\nNote: These examples require:")
    print("  - OPENAI_API_KEY for embedding generation")
    print("  - SUPABASE_URL and SUPABASE_DB_PASSWORD for database operations")
    print("  - REDIS_URL for caching (optional)")
    print("\nExamples will demonstrate graceful degradation if credentials are missing.\n")

    asyncio.run(example_1_embeddings())

    example_2_code_indexing()

    example_3_pattern_learning()

    example_4_pattern_matching()

    example_5_similarity_search()

    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
