# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a speaker diarization project using WhisperX (OpenAI Whisper) for transcription and PyAnnote.audio for speaker identification. The system processes audio files to produce transcripts with speaker attribution.

## Key Commands

### Environment Setup
```bash
# Create and setup conda environment
chmod +x setup_environment.sh
./setup_environment.sh
conda activate whisperx

# Install dependencies if needed
pip install -r requirements.txt
```

### Processing Audio

#### Web Interface
```bash
# Start web interface
./run_web_interface.sh
# Access at http://localhost:5000
```

#### Command Line
```bash
# Simple processing for the provided MP3
python transcribe_with_speakers.py "audio.mp3"

# Advanced processing with options
python transcribe_with_speakers.py "audio.mp3" --num-speakers 2 --whisper-model medium --device cpu
```

### Testing
```bash
# Test basic functionality
python -c "import whisperx; import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Test with sample audio
python diarize.py "Balancing AI and Human Connection.mp3" --output-dir test_output
```

## Architecture

### Core Components

1. **SpeakerDiarizer class** (`transcribe_with_speakers.py:17-291`)
   - Main processing pipeline
   - Handles WhisperX transcription
   - Manages PyAnnote speaker diarization
   - GPU memory management

2. **Web Interface** (`web_app_subprocess.py`)
   - Flask-based web server
   - File upload handling
   - Progress tracking
   - Real-time status updates

3. **Processing Pipeline**:
   - Load audio → Transcribe (Whisper) → Align timestamps → Diarize speakers → Assign speakers to words

4. **Output Formats**:
   - Text transcript with timestamps
   - JSON structured data
   - SRT subtitle format

### Key Dependencies

- **whisperx**: Main transcription and alignment
- **pyannote.audio==3.1.1**: Speaker diarization (requires HuggingFace token)
- **torch/torchaudio**: Deep learning backend
- **faster-whisper**: Optimized Whisper implementation

## Important Configuration

### HuggingFace Token
Required for PyAnnote models. Set via:
- Environment: `export HF_TOKEN=your_token`
- Command line: `--hf-token your_token`
- Must accept model conditions at: https://huggingface.co/pyannote/speaker-diarization-3.1

### GPU/CUDA Setup
- Requires CUDA 11.8+ for GPU acceleration
- Falls back to CPU if CUDA unavailable
- Memory management via `clear_gpu_cache()` method

## Common Tasks

### Process new audio file
```bash
python diarize.py "new_audio.mp3" --num-speakers 3 --export-json
```

### Debug memory issues
```bash
python diarize.py "audio.mp3" --batch-size 4 --whisper-model small
```

### Process without speaker labels (no HF token)
```bash
python diarize.py "audio.mp3" --whisper-model large-v3
```

## Error Handling

- CUDA OOM: Reduce batch_size or use smaller model
- Missing HF token: Continues with transcription only
- Unsupported language: Skips alignment step
- Audio format issues: Supports MP3, WAV, M4A via ffmpeg