#!/bin/bash

set -e

echo "==================================="
echo "FAQ Agent Deployment Script"
echo "==================================="

required_vars=("SUPABASE_URL" "SUPABASE_SERVICE_ROLE_KEY" "OPENAI_API_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var is not set"
        exit 1
    fi
done

echo "✅ Environment variables verified"

echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Running database migration..."
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL not set, using Supabase URL..."
    DB_CONNECTION="postgresql://postgres:${DATABASE_PASSWORD}@${SUPABASE_URL#https://}/postgres"
else
    DB_CONNECTION="$DATABASE_URL"
fi

psql "$DB_CONNECTION" -f migrations/001_create_faq_tables.sql

echo "✅ Database migration completed"

echo ""
echo "Running tests..."
python -m pytest tests/ -v

echo "✅ All tests passed"

if [ "$RUN_INTEGRATION_TESTS" = "true" ]; then
    echo ""
    echo "Running integration tests..."
    python test_real_integration.py
    echo "✅ Integration tests passed"
fi

echo ""
echo "==================================="
echo "✅ Deployment completed successfully"
echo "==================================="
