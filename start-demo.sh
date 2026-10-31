#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
if command -v python3.12 >/dev/null 2>&1; then
  exec python3.12 run_demo.py "$@"
fi
exec python3 run_demo.py "$@"
