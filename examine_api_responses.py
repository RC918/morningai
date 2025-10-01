"""
Examine actual API response structures to fix unit test mismatches
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from phase4_meta_agent_api import api_governance_status, api_meta_agent_ooda_cycle
from phase5_data_intelligence_api import api_get_dashboard_insights, api_generate_marketing_content
from phase6_security_governance_api import api_evaluate_access_request, api_review_security_event

async def examine_api_responses():
    print('=== Phase 4 API Response Structures ===')
    
    try:
        result4_governance = await api_governance_status()
        print('api_governance_status response keys:', list(result4_governance.keys()))
        print('Sample response:', result4_governance)
        print()
        
        result4_ooda = await api_meta_agent_ooda_cycle()
        print('api_meta_agent_ooda_cycle response keys:', list(result4_ooda.keys()))
        print('Sample response:', result4_ooda)
        print()
    except Exception as e:
        print(f'Phase 4 API error: {e}')
    
    print('=== Phase 5 API Response Structures ===')
    
    try:
        result5_insights = await api_get_dashboard_insights("test_dashboard_123")
        print('api_get_dashboard_insights response keys:', list(result5_insights.keys()))
        print('Sample response:', result5_insights)
        print()
        
        content_request = {
            "content_type": "email",
            "target_audience": "new_users",
            "campaign_goal": "engagement"
        }
        result5_content = await api_generate_marketing_content(content_request)
        print('api_generate_marketing_content response keys:', list(result5_content.keys()))
        print('Sample response:', result5_content)
        print()
    except Exception as e:
        print(f'Phase 5 API error: {e}')
    
    print('=== Phase 6 API Response Structures ===')
    
    try:
        test_request = {
            "user_id": "test_user",
            "resource": "test_resource", 
            "action": "read",
            "context": {"ip": "192.168.1.1"}
        }
        result6_access = await api_evaluate_access_request(test_request)
        print('api_evaluate_access_request response keys:', list(result6_access.keys()))
        print('Sample response:', result6_access)
        print()
        
        event_data = {
            "event_id": "test_event_123",
            "event_type": "suspicious_login",
            "severity": "medium",
            "details": {"ip": "192.168.1.1", "user": "test_user"}
        }
        result6_event = await api_review_security_event(event_data)
        print('api_review_security_event response keys:', list(result6_event.keys()))
        print('Sample response:', result6_event)
        print()
    except Exception as e:
        print(f'Phase 6 API error: {e}')

if __name__ == "__main__":
    asyncio.run(examine_api_responses())
