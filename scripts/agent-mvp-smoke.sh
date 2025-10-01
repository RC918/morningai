#!/usr/bin/env bash
set -euo pipefail
echo "🔎 Smoke: 檢查核心 API 與健康端點"
BASE="https://morningai-backend-v2.onrender.com"
for ep in /healthz /api/billing/plans; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE$ep")
  echo "$ep => $code"; [ "$code" = "200" ] || exit 1
done
echo "✅ OK"
