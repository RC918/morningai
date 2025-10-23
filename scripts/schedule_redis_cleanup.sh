#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

CRON_COMMAND="0 2 * * * cd $PROJECT_ROOT && python scripts/cleanup_redis_cost_keys.py >> logs/redis_cleanup.log 2>&1"

echo "📅 Scheduling Redis cleanup cron job..."
echo ""
echo "Cron command:"
echo "$CRON_COMMAND"
echo ""

if crontab -l 2>/dev/null | grep -q "cleanup_redis_cost_keys.py"; then
    echo "⚠️  Cron job already exists. Skipping..."
    echo ""
    echo "Current cron jobs:"
    crontab -l | grep "cleanup_redis_cost_keys.py"
    exit 0
fi

(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ Cron job added successfully!"
    echo ""
    echo "The cleanup script will run daily at 2:00 AM"
    echo ""
    echo "To view all cron jobs:"
    echo "  crontab -l"
    echo ""
    echo "To remove this cron job:"
    echo "  crontab -e"
    echo "  (then delete the line containing 'cleanup_redis_cost_keys.py')"
else
    echo "❌ Failed to add cron job"
    exit 1
fi
