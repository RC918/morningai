"""
Minimal smoke test for FAQ Agent
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.faq_search_tool import FAQSearchTool
from tools.faq_management_tool import FAQManagementTool

async def smoke_test():
    """Run minimal smoke test"""
    print("🔥 FAQ Agent Smoke Test")
    print("=" * 40)
    
    try:
        # Test 1: Init tools
        print("\n1. Initializing tools...")
        search_tool = FAQSearchTool()
        mgmt_tool = FAQManagementTool()
        print("   ✅ Tools initialized")
        
        # Test 2: Get categories
        print("\n2. Testing database connection...")
        result = await mgmt_tool.get_categories()
        assert result['success'], f"Failed: {result.get('error')}"
        print(f"   ✅ Found {result['count']} categories")
        
        # Test 3: Search
        print("\n3. Testing search...")
        result = await search_tool.search("test", limit=1)
        assert result['success'], f"Failed: {result.get('error')}"
        print(f"   ✅ Search returned {result['count']} results")
        
        print("\n" + "=" * 40)
        print("✅ All smoke tests PASSED")
        return 0
        
    except Exception as e:
        print(f"\n❌ Smoke test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(smoke_test())
    sys.exit(exit_code)
