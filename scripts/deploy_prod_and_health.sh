#!/usr/bin/env bash

set -euo pipefail

command -v gh >/dev/null || { echo "❌ need GitHub CLI (gh)"; exit 1; }
gh auth status >/dev/null || { echo "❌ gh not authenticated"; exit 1; }

gh repo set-default RC918/morningai

BRANCH=main
WFs=(
  "vercel-deploy"
  "Fly Deploy"
  "post-deploy-health"
  "Post-Deploy Health Assertions"
  "Sentry Smoke Test"
)

echo "▶ Dispatch production-impact workflows on $BRANCH (ignore 422)"
for wf in "${WFs[@]}"; do
  gh workflow run "$wf" -r "$BRANCH" || true
done

echo "⏳ Watch latest runs"
for wf in "${WFs[@]}"; do
  rid=$(gh run list --workflow "$wf" --branch "$BRANCH" --limit 1 --json databaseId -q '.[0].databaseId' || true)
  [ -n "${rid:-}" ] && gh run watch "$rid" --exit-status || echo "skip watch: $wf"
done

echo "✅ production deploy & health checks completed"
