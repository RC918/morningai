#!/usr/bin/env python3
"""
Phase 3 Deployment - User Notification Email Sender
Sends email notifications to all Morning AI users via Mailtrap

Features:
- Batch processing (configurable batch size)
- Rate limiting to avoid API throttling
- Automatic retry mechanism with exponential backoff
- Progress tracking and resumable sending
- Detailed logging
"""
import os
import sys
import json
import requests
import time
from datetime import datetime
from pathlib import Path

from common.config.settings import settings

MAILTRAP_API_TOKEN = settings.mailtrap_api_token
SUPABASE_URL = (settings.supabase_url or '').rstrip('/')
SUPABASE_SERVICE_KEY = settings.supabase_service_role_key

BATCH_SIZE = 10  # Send 10 emails per batch
RATE_LIMIT_DELAY = 1.0  # 1 second delay between emails
RETRY_ATTEMPTS = 3  # Retry failed emails up to 3 times
RETRY_DELAY = 5  # Initial retry delay in seconds (exponential backoff)

PROGRESS_FILE = Path(__file__).parent / '.email_progress.json'

if not MAILTRAP_API_TOKEN:
    print("ERROR: Mailtrap_API_TOKEN not found in environment variables")
    sys.exit(1)

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("ERROR: Supabase credentials not found")
    sys.exit(1)

EMAIL_SUBJECT = "🎉 Morning AI 更新：全新團隊協作功能上線！"

EMAIL_BODY_HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Morning AI 更新</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang TC', 'Microsoft JhengHei', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #1a56db;
            font-size: 24px;
            margin-bottom: 20px;
        }
        h2 {
            color: #1f2937;
            font-size: 18px;
            margin-top: 25px;
            margin-bottom: 15px;
        }
        .feature {
            background-color: #f9fafb;
            border-left: 4px solid #1a56db;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }
        .feature h3 {
            margin: 0 0 8px 0;
            color: #1f2937;
            font-size: 16px;
        }
        .feature p {
            margin: 0;
            color: #6b7280;
            font-size: 14px;
        }
        .info-box {
            background-color: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 6px;
            padding: 15px;
            margin: 20px 0;
        }
        .info-box p {
            margin: 0;
            color: #1e40af;
        }
        .button {
            display: inline-block;
            background-color: #1a56db;
            color: #ffffff;
            text-decoration: none;
            padding: 12px 24px;
            border-radius: 6px;
            margin: 20px 0;
            font-weight: 500;
        }
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            font-size: 14px;
            color: #6b7280;
        }
        ul {
            margin: 10px 0;
            padding-left: 20px;
        }
        li {
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎉 親愛的 Morning AI 用戶，您好！</h1>
        
        <p>我們很高興地宣布，Morning AI 已成功升級至全新版本，帶來更強大的團隊協作功能！</p>
        
        <h2>🎯 本次更新重點</h2>
        
        <div class="feature">
            <h3>👥 團隊管理功能</h3>
            <p>您現在可以在「系統設置」中查看和管理團隊成員<br>
            新增成員角色管理：擁有者、管理員、成員、查看者<br>
            每個組織的數據完全隔離，確保資料安全</p>
        </div>
        
        <div class="feature">
            <h3>🔐 增強的資料安全性</h3>
            <p>實施了企業級的租戶隔離機制<br>
            您的數據只有您的組織成員可以訪問<br>
            符合最新的資料保護標準</p>
        </div>
        
        <div class="feature">
            <h3>⚡ 更流暢的使用體驗</h3>
            <p>優化了登入流程<br>
            改善了 API 響應速度<br>
            修復了多項已知問題</p>
        </div>
        
        <h2>📝 您需要做什麼？</h2>
        
        <div class="info-box">
            <p><strong>無需任何操作！</strong> 所有更新已自動完成，您可以直接登入使用。</p>
        </div>
        
        <p>首次登入後，系統會自動為您分配到預設組織。如果您需要：</p>
        <ul>
            <li>邀請團隊成員</li>
            <li>調整成員權限</li>
            <li>查看組織資訊</li>
        </ul>
        
        <p>請前往：<strong>系統設置 → 配置管理 → 團隊管理</strong></p>
        
        <h2>🔐 關於資料安全</h2>
        
        <p>這次更新大幅提升了資料安全性：</p>
        <ul>
            <li>✅ 所有資料都有組織層級的隔離保護</li>
            <li>✅ 跨組織資料存取已被完全阻隔</li>
            <li>✅ 通過了完整的安全性測試</li>
        </ul>
        
        <p>您的歷史資料已自動遷移，無任何遺失或異常。</p>
        
        <h2>📞 需要協助？</h2>
        
        <p>如果您在使用過程中遇到任何問題，請隨時聯繫我們：</p>
        <ul>
            <li>📧 Email: support@morningai.com</li>
            <li>💬 應用內客服：點擊右下角圖標</li>
            <li>📚 幫助文檔：<a href="https://docs.morningai.com">https://docs.morningai.com</a></li>
        </ul>
        
        <p>感謝您一直以來對 Morning AI 的支持！</p>
        
        <div class="footer">
            <p><strong>Morning AI 團隊</strong><br>
            {date}</p>
            
            <p style="margin-top: 15px; font-size: 12px; color: #9ca3af;">
            P.S. 如果您有任何建議或反饋，歡迎直接回覆此郵件，我們非常重視每一位用戶的聲音！
            </p>
        </div>
    </div>
</body>
</html>
""".format(date=datetime.now().strftime("%Y年%m月%d日"))

EMAIL_BODY_TEXT = """
親愛的 Morning AI 用戶，您好！

我們很高興地宣布，Morning AI 已成功升級至全新版本，帶來更強大的團隊協作功能！


1. 團隊管理功能
   - 您現在可以在「系統設置」中查看和管理團隊成員
   - 新增成員角色管理：擁有者、管理員、成員、查看者
   - 每個組織的數據完全隔離，確保資料安全

2. 增強的資料安全性
   - 實施了企業級的租戶隔離機制
   - 您的數據只有您的組織成員可以訪問
   - 符合最新的資料保護標準

3. 更流暢的使用體驗
   - 優化了登入流程
   - 改善了 API 響應速度
   - 修復了多項已知問題


無需任何操作！所有更新已自動完成，您可以直接登入使用。

首次登入後，系統會自動為您分配到預設組織。如果您需要：
- 邀請團隊成員
- 調整成員權限
- 查看組織資訊

請前往：系統設置 → 配置管理 → 團隊管理


這次更新大幅提升了資料安全性：
✓ 所有資料都有組織層級的隔離保護
✓ 跨組織資料存取已被完全阻隔
✓ 通過了完整的安全性測試

您的歷史資料已自動遷移，無任何遺失或異常。


如果您在使用過程中遇到任何問題，請隨時聯繫我們：
- Email: support@morningai.com
- 應用內客服：點擊右下角圖標
- 幫助文檔：https://docs.morningai.com

感謝您一直以來對 Morning AI 的支持！

Morning AI 團隊
{date}

P.S. 如果您有任何建議或反饋，歡迎直接回覆此郵件，我們非常重視每一位用戶的聲音！
""".format(date=datetime.now().strftime("%Y年%m月%d日"))


def fetch_user_emails():
    """Fetch all user emails from Supabase auth.users"""
    print("Fetching user emails from Supabase...")
    
    url = f"{SUPABASE_URL}/rest/v1/rpc/get_user_emails"
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            f"{SUPABASE_URL}/auth/v1/admin/users",
            headers=headers,
            params={'per_page': 1000}
        )
        
        if response.status_code == 200:
            users = response.json().get('users', [])
            emails = [u['email'] for u in users if u.get('email')]
            print(f"Found {len(emails)} user emails")
            return emails
        else:
            print(f"Failed to fetch users: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return []
    except Exception as e:
        print(f"Error fetching emails: {e}")
        return []


def load_progress():
    """Load sending progress from file"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'sent': [], 'failed': []}


def save_progress(progress):
    """Save sending progress to file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def send_email_via_mailtrap(to_email, subject, html_body, text_body, attempt=1):
    """Send email using Mailtrap API with retry logic"""
    url = "https://send.api.mailtrap.io/api/send"
    
    headers = {
        "Authorization": f"Bearer {MAILTRAP_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "from": {
            "email": "noreply@morningai.com",
            "name": "Morning AI Team"
        },
        "to": [
            {
                "email": to_email
            }
        ],
        "subject": subject,
        "html": html_body,
        "text": text_body,
        "category": "Phase 3 Deployment Notification"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code in [200, 201, 202]:
            return True, "Success"
        else:
            error_msg = f"Status {response.status_code}: {response.text[:100]}"
            
            if attempt < RETRY_ATTEMPTS:
                delay = RETRY_DELAY * (2 ** (attempt - 1))
                print(f"    Retry {attempt}/{RETRY_ATTEMPTS} in {delay}s...", end=" ")
                time.sleep(delay)
                return send_email_via_mailtrap(to_email, subject, html_body, text_body, attempt + 1)
            
            return False, error_msg
    except Exception as e:
        error_msg = str(e)
        
        if attempt < RETRY_ATTEMPTS:
            delay = RETRY_DELAY * (2 ** (attempt - 1))
            print(f"    Retry {attempt}/{RETRY_ATTEMPTS} in {delay}s...", end=" ")
            time.sleep(delay)
            return send_email_via_mailtrap(to_email, subject, html_body, text_body, attempt + 1)
        
        return False, error_msg


def main():
    print("=" * 80)
    print("Morning AI Phase 3 - Email Notification Sender (Enhanced)")
    print("=" * 80)
    print()
    print("Features:")
    print(f"  ✓ Batch processing ({BATCH_SIZE} emails per batch)")
    print(f"  ✓ Rate limiting ({RATE_LIMIT_DELAY}s delay between emails)")
    print(f"  ✓ Automatic retry (up to {RETRY_ATTEMPTS} attempts)")
    print(f"  ✓ Progress tracking (resumable)")
    print()
    
    progress = load_progress()
    
    emails = fetch_user_emails()
    
    if not emails:
        print("No user emails found. Using test email...")
        emails = ["ryan@morningai.com"]
    
    emails_to_send = [e for e in emails if e not in progress['sent']]
    
    if not emails_to_send:
        print("All emails have already been sent!")
        print(f"Total sent: {len(progress['sent'])}")
        print(f"Total failed: {len(progress['failed'])}")
        return
    
    print(f"\nTotal recipients: {len(emails)}")
    print(f"Already sent: {len(progress['sent'])}")
    print(f"Remaining: {len(emails_to_send)}")
    print(f"Subject: {EMAIL_SUBJECT}")
    print()
    
    response = input(f"Send {len(emails_to_send)} emails? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("Cancelled by user")
        return
    
    print()
    print("Starting email sending...")
    print("=" * 80)
    
    success_count = 0
    failed_count = 0
    start_time = time.time()
    
    for i, email in enumerate(emails_to_send, 1):
        print(f"[{i}/{len(emails_to_send)}] {email}...", end=" ")
        
        success, message = send_email_via_mailtrap(
            email,
            EMAIL_SUBJECT,
            EMAIL_BODY_HTML,
            EMAIL_BODY_TEXT
        )
        
        if success:
            print("✓")
            success_count += 1
            progress['sent'].append(email)
        else:
            print(f"✗ {message}")
            failed_count += 1
            progress['failed'].append({'email': email, 'error': message})
        
        save_progress(progress)
        
        if i % BATCH_SIZE == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = (len(emails_to_send) - i) * avg_time
            print(f"    Batch complete. Estimated time remaining: {remaining:.1f}s")
            print()
        
        if i < len(emails_to_send):
            time.sleep(RATE_LIMIT_DELAY)
    
    elapsed = time.time() - start_time
    
    print()
    print("=" * 80)
    print(f"Email sending complete!")
    print(f"Total time: {elapsed:.1f}s")
    print(f"Success: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"Success rate: {success_count / len(emails_to_send) * 100:.1f}%")
    
    if failed_count > 0:
        print()
        print("Failed emails:")
        for item in progress['failed']:
            print(f"  - {item['email']}: {item['error']}")
    
    print("=" * 80)
    
    if failed_count == 0:
        print("\n✅ Cleaning up progress file...")
        PROGRESS_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
