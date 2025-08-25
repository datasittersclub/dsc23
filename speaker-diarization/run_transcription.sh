#!/bin/bash
# Simple script to run transcription with speaker diarization

# Default values
AUDIO_FILE="${1:-Balancing AI and Human Connection.mp3}"
MODEL="${2:-base}"
SPEAKERS="${3:-2}"

# Check if audio file exists
if [ ! -f "$AUDIO_FILE" ]; then
    echo "Error: Audio file '$AUDIO_FILE' not found"
    echo "Usage: $0 [audio_file] [model_size] [num_speakers]"
    echo "  audio_file: Path to audio file (default: 'Balancing AI and Human Connection.mp3')"
    echo "  model_size: tiny, base, small, medium, large, large-v3 (default: base)"
    echo "  num_speakers: Number of speakers (default: 2)"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Export FFmpeg path if local binary exists
if [ -f "./ffmpeg" ]; then
    export PATH="$PWD:$PATH"
    echo "Using local ffmpeg"
fi

# Check for HuggingFace token
if [ -z "$HF_TOKEN" ]; then
    echo "Warning: HF_TOKEN not set. Speaker diarization may not work."
    echo "Set it with: export HF_TOKEN='your_token_here'"
fi

# Run transcription
echo "Starting transcription..."
echo "Audio: $AUDIO_FILE"
echo "Model: $MODEL"
echo "Speakers: $SPEAKERS"
echo "================================"

python transcribe_with_speakers.py \
    "$AUDIO_FILE" \
    --whisper-model "$MODEL" \
    --num-speakers "$SPEAKERS" \
    --output-dir output

echo "================================"
echo "Done! Check the 'output' directory for results."