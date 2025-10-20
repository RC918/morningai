"""
FAQ Agent Example Usage
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools import (
    create_faq_search_tool,
    create_faq_management_tool,
    create_embedding_tool
)


async def example_create_faq():
    """Example: Create a new FAQ"""
    print("\n" + "="*70)
    print("Example 1: Create FAQ")
    print("="*70)
    
    mgmt_tool = create_faq_management_tool()
    
    result = await mgmt_tool.create_faq(
        question="如何使用 Ops Agent 監控系統健康？",
        answer="""
Ops Agent 提供了 MonitoringTool 來監控系統健康：

```python
from agents.ops_agent.tools import MonitoringTool

tool = MonitoringTool()
result = await tool.get_system_metrics()

print(f"CPU: {result['metrics']['cpu']['percent']}%")
print(f"記憶體: {result['metrics']['memory']['percent']}%")
print(f"磁碟: {result['metrics']['disk']['percent']}%")
```

系統會返回 CPU、記憶體和磁碟使用率。
        """.strip(),
        category="ops_agent",
        tags=["ops", "monitoring", "系統健康"],
        created_by="admin"
    )
    
    if result['success']:
        print(f"✅ FAQ 創建成功！")
        print(f"ID: {result['faq']['id']}")
        print(f"問題: {result['faq']['question']}")
    else:
        print(f"❌ 錯誤: {result['error']}")
    
    return result


async def example_search_faq():
    """Example: Search FAQs"""
    print("\n" + "="*70)
    print("Example 2: Search FAQ")
    print("="*70)
    
    search_tool = create_faq_search_tool()
    
    query = "怎麼檢查系統健康？"
    print(f"查詢: {query}")
    
    result = await search_tool.search(
        query=query,
        limit=3,
        threshold=0.6
    )
    
    if result['success']:
        print(f"\n✅ 找到 {result['count']} 個相關 FAQ\n")
        
        for i, faq in enumerate(result['results'], 1):
            print(f"{i}. 問題: {faq['question']}")
            print(f"   相似度: {faq.get('similarity', 0):.2%}")
            print(f"   分類: {faq.get('category', 'N/A')}")
            print(f"   觀看次數: {faq.get('view_count', 0)}")
            print()
    else:
        print(f"❌ 錯誤: {result['error']}")
    
    return result


async def example_bulk_create():
    """Example: Bulk create FAQs"""
    print("\n" + "="*70)
    print("Example 3: Bulk Create FAQs")
    print("="*70)
    
    mgmt_tool = create_faq_management_tool()
    
    faqs = [
        {
            "question": "如何檢查 Vercel 部署狀態？",
            "answer": "使用 DeploymentTool 的 list_deployments 方法檢查部署狀態。",
            "category": "ops_agent",
            "tags": ["ops", "vercel", "部署"]
        },
        {
            "question": "如何分析錯誤日誌？",
            "answer": "使用 LogAnalysisTool 的 analyze_error_patterns 方法分析錯誤。",
            "category": "ops_agent",
            "tags": ["ops", "日誌", "錯誤"]
        },
        {
            "question": "如何創建告警規則？",
            "answer": "使用 AlertManagementTool 的 create_alert_rule 方法創建規則。",
            "category": "ops_agent",
            "tags": ["ops", "告警"]
        }
    ]
    
    result = await mgmt_tool.bulk_create_faqs(faqs)
    
    if result['success']:
        print(f"✅ 批量創建成功！")
        print(f"成功: {result['created_count']}/{result['total']}")
        print(f"失敗: {result['failed_count']}")
    else:
        print(f"❌ 錯誤: {result['error']}")
    
    return result


async def example_get_stats():
    """Example: Get FAQ statistics"""
    print("\n" + "="*70)
    print("Example 4: FAQ Statistics")
    print("="*70)
    
    mgmt_tool = create_faq_management_tool()
    
    result = await mgmt_tool.get_stats()
    
    if result['success']:
        stats = result['stats']
        print(f"✅ FAQ 統計資訊：\n")
        print(f"總 FAQ 數: {stats['total_faqs']}")
        print(f"\n分類分布:")
        for category, count in stats['by_category'].items():
            print(f"  - {category}: {count}")
        
        print(f"\n最受歡迎（觀看次數）:")
        for i, faq in enumerate(stats['most_viewed'][:3], 1):
            print(f"  {i}. {faq['question'][:50]}... ({faq['view_count']} 次)")
        
        print(f"\n最有幫助（好評數）:")
        for i, faq in enumerate(stats['most_helpful'][:3], 1):
            print(f"  {i}. {faq['question'][:50]}... ({faq['helpful_count']} 票)")
    else:
        print(f"❌ 錯誤: {result['error']}")
    
    return result


async def example_record_feedback():
    """Example: Record user feedback"""
    print("\n" + "="*70)
    print("Example 5: Record Feedback")
    print("="*70)
    
    search_tool = create_faq_search_tool()
    
    search_result = await search_tool.search(
        query="系統健康",
        limit=1
    )
    
    if search_result['success'] and search_result['results']:
        faq_id = search_result['results'][0]['id']
        
        feedback_result = await search_tool.record_feedback(
            faq_id=faq_id,
            feedback='helpful'
        )
        
        if feedback_result['success']:
            print(f"✅ 反饋記錄成功：{feedback_result['message']}")
        else:
            print(f"❌ 錯誤: {feedback_result['error']}")
    else:
        print("⚠️  沒有找到 FAQ 來記錄反饋")


async def main():
    """Run all examples"""
    print("\n" + "🎯 FAQ Agent 示例" + "\n")
    
    required_env = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY', 'OPENAI_API_KEY']
    missing_env = [env for env in required_env if not os.getenv(env)]
    
    if missing_env:
        print(f"❌ 缺少環境變數: {', '.join(missing_env)}")
        print("\n請設置以下環境變數：")
        for env in missing_env:
            print(f"  export {env}='your-value'")
        return
    
    try:
        await example_create_faq()
        await example_search_faq()
        await example_bulk_create()
        await example_get_stats()
        await example_record_feedback()
        
        print("\n" + "="*70)
        print("✨ 所有示例運行完成！")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
