#!/usr/bin/env bash

set -euo pipefail
gh repo set-default RC918/morningai

BASE="v$(date +%Y%m%d-%H%M)"
TAG="$BASE"
git rev-parse -q --verify "refs/tags/$TAG" >/dev/null && TAG="${BASE}-$(date +%S)"

git fetch origin
git checkout main
git reset --hard origin/main

git tag -a "$TAG" -m "Release $TAG"
git push origin "$TAG"
gh release create "$TAG" --generate-notes -t "$TAG"
gh release view "$TAG"
