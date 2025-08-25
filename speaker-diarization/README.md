# Speaker Diarization with WhisperX and PyAnnote

This project implements speaker diarization (identifying "who spoke when") using WhisperX for transcription and PyAnnote.audio for speaker identification. The system includes automatic correction for common transcription errors and handles natural conversation dynamics including interjections and overlapping speech.

## Quick Start

### 1. Setup Environment

Choose one of the following setup methods:

#### Option A: Quick Setup (Python venv)
```bash
# For a simple setup using Python's built-in venv
chmod +x quick_setup.sh
./quick_setup.sh
source venv/bin/activate
```

#### Option B: Conda Setup (recommended for GPU)
```bash
# For conda users or if you need GPU support
chmod +x setup_environment.sh
./setup_environment.sh
conda activate whisperx
```

### 2. Configure HuggingFace Access

You need a HuggingFace token to use PyAnnote models:

1. Create account at: https://huggingface.co/join
2. Get token from: https://huggingface.co/settings/tokens
3. Accept model conditions at: 
   - https://huggingface.co/pyannote/speaker-diarization-3.1
   - https://huggingface.co/pyannote/segmentation-3.0
4. Set token:
   ```bash
   export HF_TOKEN=your_token_here
   ```

### 3. Process Audio

#### Simplest Usage
```bash
./run_transcription.sh "your_audio.mp3"
```

#### Web Interface
```bash
./run_web_interface.sh
# Opens at http://localhost:5000
```

#### Command-Line Interface
```bash
python transcribe_with_speakers.py "audio_file.mp3" \
    --whisper-model base \
    --num-speakers 2 \
    --output-dir output
```

#### Advanced Options
```bash
python transcribe_with_speakers.py "audio.mp3" \
    --whisper-model large-v3 \
    --num-speakers 3 \
    --language en \
    --device cuda \
    --batch-size 16 \
    --no-corrections  # Disable automatic corrections
```

## Main Files

- `transcribe_with_speakers.py` - Main consolidated transcription pipeline
- `run_transcription.sh` - Simple bash wrapper for easy execution
- `run_web_interface.sh` - Web interface startup script
- `web_app_subprocess.py` - Flask web application for browser-based processing
- `templates/index.html` - Web interface HTML template
- `setup_environment.sh` - Environment setup script
- `requirements.txt` - Python package requirements

## Output Formats

The system generates three output formats in the `output/` directory:

1. **Text Transcript** (`*.txt`) - Human-readable format with speaker labels
2. **JSON Data** (`*.json`) - Structured data for programmatic access
3. **SRT Subtitles** (`*.srt`) - Subtitle format with speaker labels

## Features

### Web Interface
- Browser-based file upload and processing
- Real-time progress tracking
- Transcript viewer with download options
- Support for multiple concurrent jobs
- Automatic file format detection

### Automatic Corrections
The system automatically corrects common transcription errors:
- Technical terms (e.g., "agent-based tools" vs "Asian face tools")
- Academic jargon and domain-specific vocabulary
- Common ASR mistakes in conversational speech

### Interjection Detection
Identifies and marks:
- Short confirmations ("Right", "Yeah", "Okay")
- Back-channel responses
- Overlapping speech patterns

### Speaker Diarization
- Supports 2+ speakers
- Uses PyAnnote 3.1 for state-of-the-art performance
- Maintains speaker consistency throughout conversation

## System Requirements

- **GPU**: NVIDIA GPU with 8GB+ VRAM recommended (CPU mode available)
- **RAM**: 16GB minimum, 32GB recommended
- **Python**: 3.10+ (3.10 recommended for compatibility)
- **FFmpeg**: Required for audio processing
- **CUDA**: 11.8 or 12.1+ (for GPU acceleration)

## Command-Line Options

```bash
python transcribe_with_speakers.py --help
```

Key options:
- `--whisper-model`: Model size (tiny, base, small, medium, large, large-v3)
- `--num-speakers`: Number of speakers in the audio
- `--language`: Force specific language (default: auto-detect)
- `--device`: Use cuda or cpu
- `--batch-size`: Adjust for memory constraints
- `--no-corrections`: Disable automatic error corrections
- `--hf-token`: HuggingFace token (or use HF_TOKEN env variable)

## Troubleshooting

### CUDA Out of Memory
```bash
# Reduce batch size
python transcribe_with_speakers.py audio.mp3 --batch-size 4

# Use smaller model
python transcribe_with_speakers.py audio.mp3 --whisper-model small

# Force CPU mode
python transcribe_with_speakers.py audio.mp3 --device cpu
```

### No Speaker Labels
- Ensure HuggingFace token is set: `export HF_TOKEN=your_token`
- Accept model terms at HuggingFace website
- Check internet connection for model download

### Poor Speaker Separation
- Specify exact number of speakers: `--num-speakers 2`
- Ensure good audio quality (clear speech, minimal background noise)
- Try larger Whisper model for better transcription

## Performance

Expected processing times:

| Audio Length | GPU (RTX 3060+) | CPU Mode |
|--------------|-----------------|----------|
| 1 minute     | ~30 seconds     | ~3 minutes |
| 10 minutes   | ~2-3 minutes    | ~15-20 minutes |
| 1 hour       | ~10-15 minutes  | ~60-90 minutes |

## Documentation

- `speaker_diarization_journey.md` - Blog-style narrative of the development process
- `pipeline_improvements.md` - Technical details on enhancement techniques
- `CLAUDE.md` - Guidelines for Claude Code when working with this repository

## Credit

John T. Murray, 2025 (https://jtm.io)

## Archive

Experimental and older versions are stored in the `archive/` folder for reference but are not part of the main pipeline.


## License

MIT License - See LICENSE file for details

## Acknowledgments

- WhisperX by m-bain
- PyAnnote.audio by Hervé Bredin
- OpenAI Whisper team
- Claude (Opus 4.1), Claude Code (Sonnet 4.1) & Github Copilot
