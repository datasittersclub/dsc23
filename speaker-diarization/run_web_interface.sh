#!/bin/bash

# Start the speaker diarization web interface
echo "====================================="
echo "Speaker Diarization Web Interface"
echo "====================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found."
    echo "Please run: ./quick_setup.sh first"
    exit 1
fi

# Activate virtual environment and start server
echo "Activating virtual environment and starting server..."
echo "Server will be available at: http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"
python web_app_subprocess.py