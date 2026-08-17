#!/usr/bin/env bash
# Create the public GitHub repository and push this project to it.
#
# Requires a one-time interactive login first:
#     gh auth login
#
# Then:
#     bash scripts/publish_github.sh [repo-name]
set -euo pipefail

REPO="${1:-deployment-layer-selection}"
DESC="Deployment-layer selection in evolutionary AI-race dynamics: closed-form liability thresholds, bistability and hysteresis"

if ! gh auth status >/dev/null 2>&1; then
  echo "not logged in; run 'gh auth login' first" >&2
  exit 1
fi

if git remote get-url origin >/dev/null 2>&1; then
  echo "remote 'origin' already exists: $(git remote get-url origin)"
  git push -u origin HEAD
else
  gh repo create "$REPO" --public --source=. --remote=origin \
     --description "$DESC" --push
fi

gh repo edit --add-topic evolutionary-game-theory \
             --add-topic replicator-dynamics \
             --add-topic ai-safety \
             --add-topic egttools \
             --add-topic hysteresis || true

echo "published: $(gh repo view --json url -q .url)"
