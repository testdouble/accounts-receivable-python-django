#!/usr/bin/env bash
# One-shot bootstrap. Safe to re-run.
set -euo pipefail
cd "$(dirname "$0")"

EXPECTED="$(awk '/^python /{print $2}' .tool-versions)"

echo "==> Installing Python $EXPECTED via asdf"
asdf install
asdf reshim python

echo "==> Creating .venv on the asdf interpreter"
# uv does NOT read .tool-versions -- it reads .python-version, then scans PATH.
# Homebrew's python3 also satisfies requires-python, so pin the interpreter
# explicitly rather than letting uv pick.
uv venv --python "$(asdf which python)"

ACTUAL="$(.venv/bin/python -c 'import platform; print(platform.python_version())')"
if [ "$ACTUAL" != "$EXPECTED" ]; then
  echo "ERROR: .venv is on Python $ACTUAL but .tool-versions says $EXPECTED." >&2
  echo "       uv most likely picked a different interpreter off PATH." >&2
  exit 1
fi
echo "    Python $ACTUAL confirmed"

echo "==> Installing dependencies"
uv sync

echo "==> Applying migrations"
uv run python manage.py migrate

echo
echo "Done. Start the server with ./run.sh and run the tests with ./test.sh"
