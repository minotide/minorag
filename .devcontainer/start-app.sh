#!/bin/bash
set -e

cd /workspaces/minorag

echo "Installing Python dependencies..."
pip install -q -r requirements.txt

PORT="${WEB_PORT}"

if ss -tlnp | grep -q ":${PORT}"; then
    echo "App already running on port ${PORT}, skipping start."
    exit 0
fi

echo "Starting minorag on port ${PORT}..."
python main.py
