#!/usr/bin/env bash
set -euo pipefail

# Installs repo-local Git hooks path without touching global Git config.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

chmod +x .githooks/pre-commit .githooks/post-commit scripts/run_post_edit_review.sh
git config --local core.hooksPath .githooks

echo "[hooks] Installed project hooks."
echo "[hooks] core.hooksPath=$(git config --local core.hooksPath)"
