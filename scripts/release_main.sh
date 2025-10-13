#!/usr/bin/env bash
#
# 
#
#
#
#
#   2. Sets repository default to RC918/morningai
#   5. Checks out and resets main branch to origin/main
#
#
#   ✅ Repository set to RC918/morningai
#
#
#

set -euo pipefail

command -v gh >/dev/null || { echo "❌ need GitHub CLI (gh)"; exit 1; }
gh auth status >/dev/null || { echo "❌ gh not authenticated"; exit 1; }

gh repo set-default RC918/morningai

BASE="v$(date +%Y%m%d-%H%M)"
TAG="$BASE"
git rev-parse -q --verify "refs/tags/$TAG" >/dev/null && TAG="${BASE}-$(date +%S)"

echo "📦 Creating release: $TAG"

git fetch origin
git checkout main
git reset --hard origin/main

git tag -a "$TAG" -m "Release $TAG"
git push origin "$TAG"
gh release create "$TAG" --generate-notes -t "$TAG"

echo "✅ Release published:"
gh release view "$TAG"

echo ""
echo "📝 Next Steps:"
echo "1. Copy /docs/release_notes_template.md to RELEASE_NOTES_${TAG}.md"
echo "2. Fill in detailed release notes with metrics and highlights"
echo "3. Update GitHub Release with detailed notes"
echo "4. Notify team about the new release"
