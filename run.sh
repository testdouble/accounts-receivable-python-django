#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
uv run python manage.py runserver "${1:-8000}"
