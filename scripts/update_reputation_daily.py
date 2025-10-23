#!/usr/bin/env python3
"""Daily Reputation Update Script

This script runs daily to:
1. Apply reputation decay for inactive agents
2. Update permission levels based on scores
3. Generate reputation statistics
4. Send alerts for agents with low reputation
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../handoff/20250928/40_App/orchestrator'))

from governance.reputation_engine import get_reputation_engine


def update_all_agents():
    """Update reputation for all agents"""
    engine = get_reputation_engine()
    
    print(f"[{datetime.now().isoformat()}] Starting daily reputation update")
    
    supabase = engine._get_supabase()
    if not supabase:
        print("[ERROR] Supabase unavailable, aborting")
        return False
    
    try:
        response = supabase.table('agent_reputation').select('*').execute()
        agents = response.data if response.data else []
        
        print(f"[INFO] Found {len(agents)} agents to process")
        
        updated_count = 0
        decayed_count = 0
        
        for agent in agents:
            agent_id = agent['agent_id']
            agent_type = agent['agent_type']
            current_score = agent['reputation_score']
            current_level = agent['permission_level']
            
            print(f"\n[INFO] Processing {agent_type} (ID: {agent_id})")
            print(f"  Current score: {current_score}, Level: {current_level}")
            
            if engine.apply_decay(agent_id):
                decayed_count += 1
                new_score = engine.get_reputation_score(agent_id)
                print(f"  Applied decay: {current_score} -> {new_score}")
            
            new_level = engine.update_permission_level(agent_id)
            if new_level != current_level:
                print(f"  Permission level changed: {current_level} -> {new_level}")
                updated_count += 1
        
        print(f"\n[SUCCESS] Daily update complete:")
        print(f"  - Agents processed: {len(agents)}")
        print(f"  - Decay applied: {decayed_count}")
        print(f"  - Permission updates: {updated_count}")
        
        stats = engine.get_statistics()
        print(f"\n[STATS] System statistics:")
        print(f"  - Total agents: {stats.get('total_agents', 0)}")
        print(f"  - Average score: {stats.get('average_score', 0)}")
        print(f"  - High reputation (≥130): {stats.get('high_reputation_agents', 0)}")
        print(f"  - Low reputation (<90): {stats.get('low_reputation_agents', 0)}")
        print(f"  - By level: {stats.get('agents_by_level', {})}")
        
        low_rep_agents = [a for a in agents if a['reputation_score'] < 70]
        if low_rep_agents:
            print(f"\n[ALERT] {len(low_rep_agents)} agents with critically low reputation:")
            for agent in low_rep_agents:
                print(f"  - {agent['agent_type']}: score={agent['reputation_score']}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to update agents: {e}")
        import traceback
        traceback.print_exc()
        return False


def send_summary_notification():
    """Send summary notification via Telegram"""
    try:
        import requests
        
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID')
        
        if not bot_token or not chat_id:
            print("[INFO] Telegram not configured, skipping notification")
            return
        
        engine = get_reputation_engine()
        stats = engine.get_statistics()
        
        message = f"""🤖 Daily Reputation Update Complete

📊 Statistics:
• Total agents: {stats.get('total_agents', 0)}
• Average score: {stats.get('average_score', 0):.1f}
• High reputation (≥130): {stats.get('high_reputation_agents', 0)}
• Low reputation (<90): {stats.get('low_reputation_agents', 0)}

📈 By Permission Level:
{chr(10).join(f"• {level}: {count}" for level, count in stats.get('agents_by_level', {}).items())}

Date: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
"""
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        response = requests.post(url, json={
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        })
        
        if response.status_code == 200:
            print("[INFO] Telegram notification sent successfully")
        else:
            print(f"[WARNING] Telegram notification failed: {response.text}")
            
    except Exception as e:
        print(f"[WARNING] Failed to send notification: {e}")


def main():
    """Main entry point"""
    print("=" * 80)
    print("Daily Reputation Update")
    print("=" * 80)
    
    success = update_all_agents()
    
    if success:
        send_summary_notification()
        print("\n[SUCCESS] Daily reputation update completed successfully")
        return 0
    else:
        print("\n[ERROR] Daily reputation update failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
