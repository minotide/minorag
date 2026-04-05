#!/bin/bash
set -e

cd /workspaces/minorag

echo "Installing Python dependencies..."
pip install -q -r requirements.txt

echo "Starting minorag GUI..."
python main.py
