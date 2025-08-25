# Usage Guide

## Quick Start

### Basic Usage
```bash
# Process any audio file with default settings (2 speakers, base model)
./run_transcription.sh "path/to/your/audio.mp3"
```

### With HuggingFace Token
```bash
# Set your token first
export HF_TOKEN="your_huggingface_token_here"

# Then run transcription
python transcribe_with_speakers.py "meeting_recording.mp3"
```

## Common Use Cases

### Academic Interview (2 speakers)
```bash
python transcribe_with_speakers.py "interview.mp3" \
    --num-speakers 2 \
    --whisper-model base
```

### Panel Discussion (multiple speakers)
```bash
python transcribe_with_speakers.py "panel.mp3" \
    --num-speakers 4 \
    --whisper-model large-v3 \
    --batch-size 8
```

### Podcast with High Quality Audio
```bash
python transcribe_with_speakers.py "podcast.mp3" \
    --whisper-model large-v3 \
    --num-speakers 2 \
    --device cuda \
    --batch-size 16
```

### Low-Resource System (CPU only)
```bash
python transcribe_with_speakers.py "audio.mp3" \
    --whisper-model tiny \
    --device cpu \
    --batch-size 4
```

## Output Files

After processing, you'll find in the `output/` directory:

- `yourfile_transcribed.txt` - Human-readable transcript with speaker labels
- `yourfile_transcribed.json` - Structured data with timestamps and metadata
- `yourfile_transcribed.srt` - Subtitle file for video applications

## Tips for Best Results

1. **Audio Quality**: Clear audio with minimal background noise works best
2. **Speaker Count**: If you know the exact number of speakers, specify it with `--num-speakers`
3. **Model Selection**: 
   - `tiny`/`base`: Fast, good for quick drafts
   - `small`/`medium`: Balanced speed and accuracy
   - `large`/`large-v3`: Best accuracy, slower processing
4. **Memory Management**: Reduce `--batch-size` if you encounter memory errors

## Processing Multiple Files

Create a simple bash loop:
```bash
for audio in *.mp3; do
    python transcribe_with_speakers.py "$audio" --num-speakers 2
done
```

## Integrating with Other Tools

The JSON output can be easily parsed for further processing:
```python
import json

with open('output/yourfile_transcribed.json', 'r') as f:
    data = json.load(f)
    
for segment in data['segments']:
    print(f"{segment['speaker']}: {segment['text']}")
```