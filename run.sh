#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-5173}"

cd "$(dirname "$0")/webapp"

echo "Launching PromoPack Studio on http://localhost:${PORT}"
echo "Press Ctrl+C to stop."

python3 -m http.server "${PORT}" --bind 0.0.0.0
