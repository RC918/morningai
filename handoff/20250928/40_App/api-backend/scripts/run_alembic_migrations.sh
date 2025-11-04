#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

cd "$BACKEND_DIR"

COMMAND="${1:-upgrade}"

case "$COMMAND" in
    upgrade)
        echo "Running Alembic migrations (upgrade to head)..."
        alembic upgrade head
        echo "✅ Migrations completed successfully"
        ;;
    downgrade)
        STEPS="${2:--1}"
        echo "Downgrading migrations by $STEPS..."
        alembic downgrade "$STEPS"
        echo "✅ Downgrade completed"
        ;;
    current)
        echo "Current migration version:"
        alembic current
        ;;
    history)
        echo "Migration history:"
        alembic history --verbose
        ;;
    revision)
        MESSAGE="${2:-Auto-generated migration}"
        echo "Creating new migration: $MESSAGE"
        alembic revision --autogenerate -m "$MESSAGE"
        echo "✅ Migration file created"
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Usage: $0 [upgrade|downgrade|current|history|revision] [args]"
        exit 1
        ;;
esac
