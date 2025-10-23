#!/usr/bin/env python3
"""
Setup script for Telegram notifications for Agent Governance Framework

This script configures Telegram bot notifications for:
- Daily governance reports
- Budget alerts
- Violation notifications
- Permission level changes

Usage:
    python scripts/setup_telegram_notifications.py --bot-token YOUR_BOT_TOKEN --chat-id YOUR_CHAT_ID
"""

import os
import sys
import argparse
import requests
from pathlib import Path

def test_telegram_connection(bot_token, chat_id):
    """Test Telegram bot connection"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": "🤖 Agent Governance Framework - Telegram notifications configured successfully!\n\nYou will receive:\n- Daily governance reports\n- Budget alerts\n- Violation notifications\n- Permission level changes",
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        print("✅ Telegram connection test successful!")
        print(f"   Message sent to chat ID: {chat_id}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Telegram connection test failed: {e}")
        return False


def update_env_file(bot_token, chat_id):
    """Update .env file with Telegram credentials"""
    env_file = Path(__file__).parent.parent / '.env'
    
    env_vars = {
        'TELEGRAM_BOT_TOKEN': bot_token,
        'TELEGRAM_ADMIN_CHAT_ID': chat_id
    }
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        updated_vars = set()
        new_lines = []
        
        for line in lines:
            if line.strip() and not line.strip().startswith('#'):
                key = line.split('=')[0].strip()
                if key in env_vars:
                    new_lines.append(f"{key}={env_vars[key]}\n")
                    updated_vars.add(key)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        for key, value in env_vars.items():
            if key not in updated_vars:
                new_lines.append(f"{key}={value}\n")
        
        with open(env_file, 'w') as f:
            f.writelines(new_lines)
        
        print(f"✅ Updated {env_file}")
    else:
        with open(env_file, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        print(f"✅ Created {env_file}")
    
    return True


def create_notification_script():
    """Create a script for sending governance notifications"""
    script_path = Path(__file__).parent / 'send_governance_notification.py'
    
    script_content = '''#!/usr/bin/env python3
"""Send governance notification via Telegram"""
import os
import sys
import requests
import argparse

def send_notification(message, parse_mode='Markdown'):
    """Send notification to Telegram"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ TELEGRAM_BOT_TOKEN or TELEGRAM_ADMIN_CHAT_ID not set")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        print("✅ Notification sent successfully")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send notification: {e}")
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send governance notification')
    parser.add_argument('--message', required=True, help='Message to send')
    parser.add_argument('--parse-mode', default='Markdown', help='Parse mode (Markdown or HTML)')
    
    args = parser.parse_args()
    
    success = send_notification(args.message, args.parse_mode)
    sys.exit(0 if success else 1)
'''
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    os.chmod(script_path, 0o755)
    
    print(f"✅ Created {script_path}")
    return True


def update_daily_reputation_script():
    """Update daily reputation script to send Telegram notifications"""
    script_path = Path(__file__).parent / 'update_reputation_daily.py'
    
    if not script_path.exists():
        print(f"⚠️  {script_path} not found, skipping update")
        return False
    
    with open(script_path, 'r') as f:
        content = f.read()
    
    if 'send_telegram_notification' in content:
        print(f"✅ {script_path} already has Telegram notifications")
        return True
    
    telegram_function = '''
def send_telegram_notification(message):
    """Send notification to Telegram"""
    import requests
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID')
    
    if not bot_token or not chat_id:
        logger.warning("Telegram credentials not configured")
        return
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info("Telegram notification sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")
'''
    
    import_section = content.split('if __name__')[0]
    main_section = 'if __name__' + content.split('if __name__')[1]
    
    updated_content = import_section + telegram_function + '\n' + main_section
    
    updated_main = main_section.replace(
        'logger.info("Daily reputation update completed successfully")',
        '''logger.info("Daily reputation update completed successfully")
        
        stats = reputation_engine.get_statistics()
        message = f"""🤖 *Daily Governance Report*
        
📊 *Statistics*
- Total Agents: {stats.get('total_agents', 0)}
- Average Score: {stats.get('average_score', 0):.1f}
- High Reputation: {stats.get('high_reputation_agents', 0)}

🏆 *Top Agents*
{chr(10).join([f"- {a['agent_type']}: {a['reputation_score']}" for a in reputation_engine.get_leaderboard(limit=3)])}

✅ Daily update completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        send_telegram_notification(message)'''
    )
    
    updated_content = import_section + telegram_function + '\n' + updated_main
    
    with open(script_path, 'w') as f:
        f.write(updated_content)
    
    print(f"✅ Updated {script_path} with Telegram notifications")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Setup Telegram notifications for Agent Governance Framework'
    )
    parser.add_argument('--bot-token', required=True, help='Telegram bot token')
    parser.add_argument('--chat-id', required=True, help='Telegram chat ID')
    parser.add_argument('--skip-test', action='store_true', help='Skip connection test')
    
    args = parser.parse_args()
    
    print("🚀 Setting up Telegram notifications...")
    print()
    
    if not args.skip_test:
        print("1. Testing Telegram connection...")
        if not test_telegram_connection(args.bot_token, args.chat_id):
            print("\n❌ Setup failed: Could not connect to Telegram")
            sys.exit(1)
        print()
    
    print("2. Updating .env file...")
    if not update_env_file(args.bot_token, args.chat_id):
        print("\n❌ Setup failed: Could not update .env file")
        sys.exit(1)
    print()
    
    print("3. Creating notification script...")
    if not create_notification_script():
        print("\n❌ Setup failed: Could not create notification script")
        sys.exit(1)
    print()
    
    print("4. Updating daily reputation script...")
    update_daily_reputation_script()
    print()
    
    print("✅ Telegram notifications setup completed!")
    print()
    print("📝 Next steps:")
    print("   1. Verify GitHub Actions secrets are set:")
    print("      - TELEGRAM_BOT_TOKEN")
    print("      - TELEGRAM_ADMIN_CHAT_ID")
    print("   2. Test notifications:")
    print(f"      python scripts/send_governance_notification.py --message 'Test notification'")
    print("   3. Daily reports will be sent automatically via GitHub Actions")
    print()


if __name__ == '__main__':
    main()
