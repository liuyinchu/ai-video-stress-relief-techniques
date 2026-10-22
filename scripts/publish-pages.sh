#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
if [ -n "$(git status --porcelain -- site)" ]; then
  printf '%s\n' 'Commit site changes before publishing.' >&2
  exit 1
fi
source_commit="$(git rev-parse HEAD)"
site_tree="$(git rev-parse HEAD:site)"
if git ls-remote --exit-code origin refs/heads/gh-pages >/dev/null 2>&1; then
  git fetch --quiet origin gh-pages
  deploy_commit="$(git commit-tree "$site_tree" -p "$(git rev-parse FETCH_HEAD)" -m "Publish film website from ${source_commit}")"
else
  deploy_commit="$(git commit-tree "$site_tree" -m "Publish film website from ${source_commit}")"
fi
git push origin "${deploy_commit}:refs/heads/gh-pages"
printf 'Published site tree: %s\n' "$deploy_commit"
