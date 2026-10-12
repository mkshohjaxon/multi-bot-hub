#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

PYTHON_BIN="/home/shohjaxon/tg-account-manager/venv/bin/python"
PORT=7777

echo "=========================================================="
echo "🚀 Starting MEGA AUTOMATION HUB on Port $PORT..."
echo "=========================================================="

exec "$PYTHON_BIN" main.py
