#!/bin/bash
set -e

echo "Starting Ollama server..."
nohup ollama serve > /tmp/ollama.log 2>&1 &
