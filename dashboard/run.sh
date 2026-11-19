#!/usr/bin/env bash
# Run dashboard in Docker (no local pandas/Dash install required).
set -euo pipefail
cd "$(dirname "$0")"
docker network create kpihub-net 2>/dev/null || true
docker compose up --build -d
echo "Open http://localhost:8052"
echo "Logs: docker compose logs -f kpihub-weekly-dash"