#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL is not set" >&2
  exit 1
fi

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$DIR/.." && pwd)"

MIG_DIR="$REPO_ROOT/migrations"

echo "Running migrations against: $DATABASE_URL"

psql "$DATABASE_URL" -f "$MIG_DIR/010_create_embeddings_tables.sql"
psql "$DATABASE_URL" -f "$MIG_DIR/011_create_trace_metrics_tables.sql"
psql "$DATABASE_URL" -f "$MIG_DIR/012_create_vector_visualization_views.sql"
psql "$DATABASE_URL" -f "$MIG_DIR/013_enable_supabase_ai_extensions.sql"

echo "All migrations applied successfully."
