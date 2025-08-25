#!/bin/bash

# Quick setup script for system Python
echo "==================================="
echo "WhisperX + PyAnnote Quick Setup"
echo "==================================="

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate environment
echo "Activating environment..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install PyTorch (CPU version for compatibility)
echo "Installing PyTorch..."
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install WhisperX
echo "Installing WhisperX..."
pip install git+https://github.com/m-bain/whisperX.git

# Install other dependencies
echo "Installing additional dependencies..."
pip install pyannote.audio==3.1.1
pip install faster-whisper
pip install huggingface_hub
pip install librosa
pip install soundfile
pip install openai-whisper

echo ""
echo "Setup complete!"
echo "Activate with: source venv/bin/activate"