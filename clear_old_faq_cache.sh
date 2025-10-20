#!/bin/bash
# Script to clear old FAQ cache from Redis

echo "Clearing old FAQ cache keys..."
redis-cli KEYS "faq:cache:*" | xargs -r redis-cli DEL
echo "Old FAQ cache cleared successfully!"
