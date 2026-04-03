#!/bin/bash
set -e

# Install system dependencies
sudo apt-get update && sudo apt-get install -y zstd

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Ollama
echo "Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sudo bash

# Verify installation
if ! command -v ollama &> /dev/null; then
    echo "ERROR: ollama not found on PATH after install"
    echo "Attempting direct binary download..."
    sudo curl -fsSL -o /usr/local/bin/ollama https://ollama.com/download/ollama-linux-amd64
    sudo chmod +x /usr/local/bin/ollama
fi

# Start Ollama server temporarily to pull models
echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!
sleep 5

# Pull models
echo "Pulling nomic-embed-text model..."
ollama pull nomic-embed-text

echo "Pulling qwen2.5-coder:3b model..."
ollama pull qwen2.5-coder:3b

# Stop temporary server (postStartCommand will start it properly)
kill $OLLAMA_PID 2>/dev/null || true

echo "Setup complete!"
