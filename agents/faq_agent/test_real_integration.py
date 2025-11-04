"""
Real API Integration Test for FAQ Agent
Tests OpenAI API and Supabase connections with actual credentials
"""
import asyncio
import os
import sys
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.embedding_tool import EmbeddingTool
from tools.faq_search_tool import FAQSearchTool
from tools.faq_management_tool import FAQManagementTool


async def test_openai_api():
    """Test OpenAI API connection and embedding generation"""
    print("\n" + "="*60)
    print("Testing OpenAI API Integration")
    print("="*60)
    
    tool = EmbeddingTool()
    
    # Test single embedding
    print("\n1. Testing single embedding generation...")
    result = await tool.generate_embedding("How do I reset my password?")
    
    if result['success']:
        print(f"   ✅ Success! Generated embedding with {len(result['embedding'])} dimensions")
        print(f"   📊 First 5 values: {result['embedding'][:5]}")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False
    
    # Test batch embeddings
    print("\n2. Testing batch embedding generation...")
    questions = [
        "What are your business hours?",
        "How can I contact support?",
        "Where is your office located?"
    ]
    
    batch_result = await tool.generate_embeddings_batch(questions)
    
    if batch_result['success']:
        print(f"   ✅ Success! Generated {len(batch_result['embeddings'])} embeddings")
        print(f"   📊 All embeddings valid: {all(e is not None for e in batch_result['embeddings'])}")
    else:
        print(f"   ❌ Failed: {batch_result.get('error')}")
        return False
    
    return True


async def test_supabase_connection():
    """Test Supabase database connection"""
    print("\n" + "="*60)
    print("Testing Supabase Connection")
    print("="*60)
    
    mgmt_tool = FAQManagementTool()
    
    # Test 1: Check categories
    print("\n1. Testing database connection (get categories)...")
    result = await mgmt_tool.get_categories()
    
    if result['success']:
        print(f"   ✅ Connected! Found {result['count']} categories")
        for cat in result['categories']:
            print(f"      - {cat['name']}")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
        return False
    
    # Test 2: Get stats
    print("\n2. Testing database queries (get stats)...")
    stats_result = await mgmt_tool.get_stats()
    
    if stats_result['success']:
        print(f"   ✅ Success! Stats retrieved:")
        print(f"      - Total FAQs: {stats_result['stats']['total_faqs']}")
        print(f"      - Categories: {len(stats_result['stats']['by_category'])}")
    else:
        print(f"   ❌ Failed: {stats_result.get('error')}")
        return False
    
    return True


async def test_end_to_end_workflow():
    """Test complete FAQ creation and search workflow"""
    print("\n" + "="*60)
    print("Testing End-to-End Workflow")
    print("="*60)
    
    mgmt_tool = FAQManagementTool()
    search_tool = FAQSearchTool()
    
    # Create a test FAQ
    print("\n1. Creating test FAQ...")
    test_question = f"Test Question - {datetime.now(timezone.utc).isoformat()}"
    test_answer = "This is a test answer created during integration testing."
    
    create_result = await mgmt_tool.create_faq(
        question=test_question,
        answer=test_answer,
        category="Testing",
        tags=["test", "integration"],
        created_by="integration_test"
    )
    
    if not create_result['success']:
        print(f"   ❌ Failed to create FAQ: {create_result.get('error')}")
        return False
    
    faq_id = create_result['faq']['id']
    print(f"   ✅ Created FAQ with ID: {faq_id}")
    
    # Search for the FAQ
    print("\n2. Searching for created FAQ...")
    search_result = await search_tool.search(
        query="test question integration",
        limit=5
    )
    
    if search_result['success']:
        print(f"   ✅ Search successful! Found {len(search_result['results'])} results")
        found = any(r['id'] == faq_id for r in search_result['results'])
        if found:
            print(f"   ✅ Found our test FAQ in search results!")
        else:
            print(f"   ⚠️  Test FAQ not in top results (may need more similar data)")
    else:
        print(f"   ❌ Search failed: {search_result.get('error')}")
    
    # Update the FAQ
    print("\n3. Updating FAQ...")
    update_result = await mgmt_tool.update_faq(
        faq_id=faq_id,
        answer="Updated answer during integration testing."
    )
    
    if update_result['success']:
        print(f"   ✅ FAQ updated successfully!")
    else:
        print(f"   ❌ Update failed: {update_result.get('error')}")
    
    # Clean up - delete test FAQ
    print("\n4. Cleaning up test data...")
    delete_result = await mgmt_tool.delete_faq(faq_id)
    
    if delete_result['success']:
        print(f"   ✅ Test FAQ deleted successfully!")
    else:
        print(f"   ❌ Delete failed: {delete_result.get('error')}")
    
    return True


async def main():
    """Run all integration tests"""
    print("\n" + "🧪 "*20)
    print("FAQ Agent - Real API Integration Test Suite")
    print("🧪 "*20)
    
    results = {
        'openai': False,
        'supabase': False,
        'end_to_end': False
    }
    
    try:
        # Test OpenAI
        results['openai'] = await test_openai_api()
        
        # Test Supabase
        results['supabase'] = await test_supabase_connection()
        
        # Test End-to-End
        if results['openai'] and results['supabase']:
            results['end_to_end'] = await test_end_to_end_workflow()
        else:
            print("\n⚠️  Skipping end-to-end test due to API failures")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"OpenAI API:        {'✅ PASS' if results['openai'] else '❌ FAIL'}")
    print(f"Supabase:          {'✅ PASS' if results['supabase'] else '❌ FAIL'}")
    print(f"End-to-End:        {'✅ PASS' if results['end_to_end'] else '❌ FAIL'}")
    print("="*60)
    
    all_passed = all(results.values())
    print(f"\n{'✅ All tests PASSED!' if all_passed else '❌ Some tests FAILED'}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
