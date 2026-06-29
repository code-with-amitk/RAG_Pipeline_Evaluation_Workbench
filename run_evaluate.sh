#!/usr/bin/env bash
# Always run evaluation with the project virtual environment.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$ROOT/venv/bin/python" "$ROOT/evaluate.py" "$@"
