#!/usr/bin/env python3
"""
Simple test for OpenAI embedding generation (no database required)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from agents.dev_agent.knowledge_graph.knowledge_graph_manager import KnowledgeGraphManager

def test_openai_only():
    """Test OpenAI embedding generation without database"""
    print("\n=== Testing OpenAI Embedding Generation ===\n")
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ OPENAI_API_KEY not configured")
        print("   Please set OPENAI_API_KEY in your .env file")
        return False
    
    print(f"✓ OPENAI_API_KEY configured: {openai_key[:10]}...{openai_key[-4:]}")
    
    print("\nInitializing Knowledge Graph Manager (OpenAI only)...")
    kg_manager = KnowledgeGraphManager(
        openai_api_key=openai_key,
        enable_cache=False  # Disable Redis cache for simplicity
    )
    
    test_code = """
def calculate_sum(numbers):
    '''Calculate the sum of a list of numbers'''
    total = 0
    for num in numbers:
        total += num
    return total
"""
    
    print(f"\nGenerating embedding for test code...")
    print(f"Code length: {len(test_code)} characters")
    
    result = kg_manager.generate_embedding(test_code)
    
    print(f"\nAPI Response:")
    print(f"  - Success: {result.get('success')}")
    print(f"  - Raw result keys: {list(result.keys())}")
    
    if result.get('success'):
        embedding = result.get('embedding', [])
        print(f"  - Embedding type: {type(embedding)}")
        print(f"  - Embedding is list: {isinstance(embedding, list)}")
        
        print(f"\n✅ Embedding generated successfully!")
        print(f"  - Dimensions: {len(embedding)}")
        print(f"  - Tokens used: {result.get('tokens', 'N/A')}")
        print(f"  - Cost: ${result.get('cost', 0):.6f}")
        print(f"  - Cached: {result.get('cached', False)}")
        if len(embedding) > 0:
            print(f"  - First 5 values: {embedding[:5]}")
        else:
            print(f"  - ⚠️ Embedding is empty!")
        return len(embedding) > 0
    else:
        error = result.get('error', {})
        print(f"\n❌ Failed to generate embedding")
        print(f"  - Error code: {error.get('code', 'N/A')}")
        print(f"  - Message: {error.get('message', 'Unknown error')}")
        print(f"  - Hint: {error.get('hint', 'Check configuration')}")
        return False

if __name__ == '__main__':
    print("=" * 70)
    print("Basic OpenAI Embedding Test")
    print("=" * 70)
    
    success = test_openai_only()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ Test PASSED - OpenAI integration working!")
    else:
        print("❌ Test FAILED - Check error messages above")
    print("=" * 70 + "\n")
    
    sys.exit(0 if success else 1)
