#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${1:-git@github.com:aviralsingh839/endo-twin-nexus-v8.3.git}"

git init -b main
git add .
git commit -m "Base ENDO-TWIN Nexus V8.3 from supplied superbuild" || true
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REPO_URL"
else
  git remote add origin "$REPO_URL"
fi
git push -u origin main
