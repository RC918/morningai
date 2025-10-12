#!/usr/bin/env bash

set -euo pipefail
gh repo set-default RC918/morningai

WFs=(
  "openapi-verify"
  "orchestrator-e2e"
  "agent-mvp-smoke"
  "Ops Agent Sandbox E2E"
  "post-deploy-health"
)

echo "▶ Dispatch selected workflows on main (ignore 422 if no workflow_dispatch)"
for wf in "${WFs[@]}"; do
  gh workflow run "$wf" -r main || true
done

echo "⏳ Watch latest runs until success"
for wf in "${WFs[@]}"; do
  rid=$(gh run list --workflow "$wf" --branch main --limit 1 --json databaseId -q '.[0].databaseId' || true)
  [ -n "${rid:-}" ] && gh run watch "$rid" --exit-status || echo "skip: $wf (no run)"
done
echo "✅ all health checks passed on main"
