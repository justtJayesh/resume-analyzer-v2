#!/usr/bin/env bash
set -euo pipefail

# Non-destructive checks for changed Python files.
# Supports `pre-commit` (staged files) and `post-commit` (latest commit files).

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

HOOK_PHASE="${1:-post-commit}"

if [[ "${SKIP_POST_EDIT_REVIEW:-0}" == "1" || "${SKIP_PRE_COMMIT_REVIEW:-0}" == "1" ]]; then
  exit 0
fi

changed_files=()
if [[ "$HOOK_PHASE" == "pre-commit" ]]; then
  while IFS= read -r file; do
    changed_files+=("$file")
  done < <(git diff --cached --name-only --diff-filter=ACMR -- '*.py')
else
  while IFS= read -r file; do
    changed_files+=("$file")
  done < <(git diff-tree --no-commit-id --name-only -r HEAD -- '*.py')
fi

if [[ "${#changed_files[@]}" -eq 0 ]]; then
  echo "[post-edit-review] No changed Python files for $HOOK_PHASE. Skipping."
  exit 0
fi

echo "[post-edit-review] ($HOOK_PHASE) Running checks for: ${changed_files[*]}"

if command -v python3 >/dev/null 2>&1; then
  python3 -m py_compile "${changed_files[@]}"
else
  echo "[post-edit-review] python3 not found; skipping syntax check."
fi

if command -v ruff >/dev/null 2>&1; then
  ruff check "${changed_files[@]}"
else
  echo "[post-edit-review] ruff not found; skipping ruff check."
fi

if command -v black >/dev/null 2>&1; then
  black --check "${changed_files[@]}"
else
  echo "[post-edit-review] black not found; skipping black --check."
fi

if command -v pytest >/dev/null 2>&1; then
  pytest -q tests
else
  echo "[post-edit-review] pytest not found; skipping tests."
fi
