#!/usr/bin/env bash
# Commit the given paths as github-actions[bot] if they changed, and push, rebasing on a race.
# Usage: tools/ci/commit.sh "message" path...
set -euo pipefail
message=$1
shift
git config user.name "github-actions[bot]"
git config user.email "41898283+github-actions[bot]@users.noreply.github.com"
git add -- "$@"
if git diff --cached --quiet; then
  echo "nothing changed"
  exit 0
fi
git commit -q -m "$message"
for attempt in 1 2 3 4 5; do
  if git push -q origin HEAD; then
    exit 0
  fi
  echo "push rejected (attempt $attempt), rebasing"
  git pull -q --rebase origin "$(git rev-parse --abbrev-ref HEAD)"
done
echo "could not push after 5 attempts" >&2
exit 1
