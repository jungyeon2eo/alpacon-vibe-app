#!/usr/bin/env bash
# Single-command deploy entrypoint so the Alpacon command ACL can whitelist
# exactly this one path (least privilege) instead of a wildcard.
set -euo pipefail
cd "$HOME/alpacon-vibe-app"
git pull
docker compose up -d --build
