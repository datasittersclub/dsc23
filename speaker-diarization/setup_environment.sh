#!/bin/bash

# WhisperX + PyAnnote Environment Setup Script
# This script sets up the required environment for speaker diarization

echo "==================================="
echo "WhisperX + PyAnnote Setup"
echo "==================================="

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "Error: Conda is not installed. Please install Anaconda or Miniconda first."
    echo "Visit: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Create conda environment
echo "Creating conda environment with Python 3.10..."
conda create -n whisperx python=3.10 -y

# Activate environment
echo "Activating environment..."
eval "$(conda shell.bash hook)"
conda activate whisperx

# Install PyTorch with CUDA support
echo "Installing PyTorch with CUDA support..."
# Check for CUDA availability and install appropriate version
if command -v nvidia-smi &> /dev/null; then
    echo "CUDA detected, installing PyTorch with CUDA 11.8 support..."
    conda install pytorch==2.0.1 torchaudio==2.0.2 pytorch-cuda=11.8 -c pytorch -c nvidia -y
else
    echo "No CUDA detected, installing CPU-only PyTorch..."
    conda install pytorch==2.0.1 torchaudio==2.0.2 cpuonly -c pytorch -y
fi

# Install WhisperX
echo "Installing WhisperX..."
pip install git+https://github.com/m-bain/whisperX.git

# Install PyAnnote and other dependencies
echo "Installing PyAnnote.audio and dependencies..."
pip install pyannote.audio==3.1.1
pip install faster-whisper
pip install huggingface_hub
pip install librosa
pip install soundfile

# Install system dependencies reminder
echo ""
echo "==================================="
echo "System Dependencies Required:"
echo "==================================="
echo "Please ensure you have installed:"
echo ""
echo "For Ubuntu/Debian:"
echo "  sudo apt update && sudo apt install ffmpeg sox libsndfile1"
echo ""
echo "For macOS:"
echo "  brew install ffmpeg sox"
echo ""
echo "==================================="
echo "HuggingFace Authentication Required:"
echo "==================================="
echo "You need to authenticate with HuggingFace to access PyAnnote models."
echo "1. Create a HuggingFace account at: https://huggingface.co/join"
echo "2. Get your access token from: https://huggingface.co/settings/tokens"
echo "3. Run: huggingface-cli login"
echo "4. Accept the pyannote/speaker-diarization-3.1 model conditions at:"
echo "   https://huggingface.co/pyannote/speaker-diarization-3.1"
echo ""
echo "Setup complete! Activate the environment with: conda activate whisperx"