#!/usr/bin/env bash
set -e


e="${VERCEL_ENV:-}"
r="${VERCEL_GIT_COMMIT_REF:-main}"

sha="${VERCEL_GIT_COMMIT_SHA:-$(git rev-parse HEAD)}"
changed="$(git show --pretty='' --name-only "$sha" 2>/dev/null || echo '')"

if [ -n "$changed" ]; then
  if ! echo "$changed" | grep -Ev '^(docs/|.*\.md$)' >/dev/null; then
    echo "⏭️  Skipping deployment: only documentation changed"
    exit 0
  fi
fi

if [ "$e" = "preview" ]; then
  case "$r" in
    develop|feature/*|fix/*|devin/*)
      echo "✅ Allowing preview deployment for branch: $r"
      exit 1
      ;;
    *)
      echo "⏭️  Skipping preview deployment for branch: $r (not a develop/feature/fix/devin branch)"
      exit 0
      ;;
  esac
fi

if [ "$e" = "production" ]; then
  if [ "$r" = "main" ]; then
    echo "✅ Allowing production deployment for branch: $r"
    exit 1
  else
    echo "⏭️  Skipping production deployment for branch: $r (not main)"
    exit 0
  fi
fi

echo "⏭️  Skipping deployment for env: $e, branch: $r"
exit 0
