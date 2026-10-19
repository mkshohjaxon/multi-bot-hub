#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

if [ -f "$DIR/venv/bin/python3" ]; then
    PY="$DIR/venv/bin/python3"
elif [ -f "/home/shohjaxon/tg-account-manager/venv/bin/python" ]; then
    PY="/home/shohjaxon/tg-account-manager/venv/bin/python"
elif command -v python3 &>/dev/null; then
    PY="python3"
else
    PY="python"
fi

exec "$PY" "$DIR/run.py" "$@"
