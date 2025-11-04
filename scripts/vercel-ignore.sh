#!/usr/bin/env bash
set -e

#

e="${VERCEL_ENV:-}"
r="${VERCEL_GIT_COMMIT_REF:-}"

if [ "$e" = "preview" ]; then
  echo "✅ Allowing preview deployment for branch: $r"
  exit 1
fi

case "$r" in
  main|production|release/*|hotfix/*)
    echo "✅ Allowing production deployment for branch: $r"
    exit 1
    ;;
  *)
    echo "⏭️  Skipping deployment for branch: $r"
    exit 0
    ;;
esac
