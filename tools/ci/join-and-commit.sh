#!/usr/bin/env bash
# Run tools/join.py on the issue event and commit what it changed. If another ping pushed first, start
# again from the new main: joining is idempotent, so a rerun just adds this peer to the newer list.
set -euo pipefail
git config user.name "github-actions[bot]"
git config user.email "41898283+github-actions[bot]@users.noreply.github.com"
branch=$(git rev-parse --abbrev-ref HEAD)
pushed=no
for attempt in 1 2 3 4 5; do
  result=$(GITHUB_OUTPUT=/dev/null uv run --with-requirements tools/requirements.txt python tools/join.py)
  action=${result##*action=}
  if [[ $action != join && $action != leave ]]; then
    pushed=n/a
    break
  fi
  git add peers.json assets/banner.svg
  git commit -q -m "ping: a peer ${action}s the network (issue #${ISSUE_NUMBER:-?})"
  if git push -q origin HEAD; then
    pushed=yes
    break
  fi
  echo "push rejected (attempt $attempt), starting again from origin/$branch"
  git fetch -q origin "$branch"
  git reset -q --hard "origin/$branch"
done
if [[ $pushed == no ]]; then
  echo "could not push after 5 attempts; not replying" >&2
  exit 1
fi
echo "action=$action" >> "$GITHUB_OUTPUT"
