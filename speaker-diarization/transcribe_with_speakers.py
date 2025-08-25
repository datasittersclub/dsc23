#!/usr/bin/env python3
"""
WhisperX + PyAnnote Speaker Diarization Pipeline
Complete solution for transcription with speaker identification

Author: Lucid
Date: 2024
License: MIT
"""

import whisperx
import torch
import gc
import os
import json
import argparse
import re
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")


class SpeakerDiarizer:
    """
    Complete speaker diarization pipeline using WhisperX and PyAnnote.
    Includes automatic correction for common transcription errors.
    """
    
    def __init__(self, hf_token=None, device=None):
        """
        Initialize the diarizer.
        
        Args:
            hf_token: HuggingFace token for PyAnnote access
            device: "cuda" or "cpu" (auto-detected if None)
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.hf_token = hf_token or os.environ.get("HF_TOKEN")
        
        # Common transcription corrections for academic discourse
        self.word_corrections = {
            "Asian face": "agent-based",
            "open-ass": "OpenAI's",
            "co-pilot ship": "co-pilot shit",
            "make-e": "makey",
            "wilded": "all the",
            "COE": "GUI",
            "hundred and first": "",
            "we're happening": "happening",
            "Bond and Reading": "The Babysitters Club",
            "deep personalized": "depersonalized"
        }
        
        print(f"Initialized with device: {self.device}")
        if self.device == "cuda":
            print(f"GPU: {torch.cuda.get_device_name(0)}")
    
    def transcribe_with_speakers(
        self,
        audio_file,
        whisper_model="base",
        language="en",
        num_speakers=2,
        batch_size=8,
        apply_corrections=True
    ):
        """
        Complete pipeline for transcription with speaker diarization.
        
        Args:
            audio_file: Path to audio file
            whisper_model: Whisper model size (tiny, base, small, medium, large, large-v3)
            language: Language code or None for auto-detection
            num_speakers: Expected number of speakers
            batch_size: Processing batch size
            apply_corrections: Whether to apply automatic corrections
        
        Returns:
            Dictionary with segments containing speaker labels and text
        """
        print(f"\nProcessing: {audio_file}")
        print(f"Model: {whisper_model}, Language: {language}, Speakers: {num_speakers}")
        print("-" * 50)
        
        # Step 1: Transcription
        print("\n1. Transcribing audio...")
        compute_type = "float16" if self.device == "cuda" else "float32"
        
        model = whisperx.load_model(
            whisper_model,
            self.device,
            compute_type=compute_type,
            language=language
        )
        
        audio = whisperx.load_audio(audio_file)
        result = model.transcribe(audio, batch_size=batch_size, language=language)
        
        print(f"   ✓ Transcribed {len(result['segments'])} segments")
        
        # Cleanup
        del model
        gc.collect()
        if self.device == "cuda":
            torch.cuda.empty_cache()
        
        # Step 2: Alignment
        print("\n2. Aligning timestamps...")
        try:
            model_a, metadata = whisperx.load_align_model(
                language_code=result.get("language", "en"),
                device=self.device
            )
            result = whisperx.align(
                result["segments"],
                model_a,
                metadata,
                audio,
                self.device,
                return_char_alignments=False
            )
            del model_a
            gc.collect()
            print("   ✓ Alignment complete")
        except Exception as e:
            print(f"   ⚠ Alignment skipped: {e}")
            result = {"segments": result["segments"]}
        
        # Step 3: Speaker Diarization
        if self.hf_token:
            print("\n3. Identifying speakers...")
            try:
                from whisperx.diarize import DiarizationPipeline
                
                diarize_model = DiarizationPipeline(
                    use_auth_token=self.hf_token,
                    device=self.device
                )
                
                diarize_segments = diarize_model(audio, num_speakers=num_speakers)
                result = whisperx.assign_word_speakers(diarize_segments, result)
                
                # Count speakers
                speakers = set()
                for segment in result["segments"]:
                    if "speaker" in segment:
                        speakers.add(segment["speaker"])
                
                print(f"   ✓ Identified {len(speakers)} speakers: {sorted(speakers)}")
                
            except Exception as e:
                print(f"   ⚠ Speaker diarization failed: {e}")
                print("   Continuing without speaker labels...")
        else:
            print("\n3. Speaker diarization skipped (no HuggingFace token)")
        
        # Step 4: Apply corrections
        if apply_corrections:
            print("\n4. Applying corrections...")
            result = self.apply_corrections(result)
            print("   ✓ Corrections applied")
        
        return result
    
    def apply_corrections(self, result):
        """
        Apply automatic corrections to transcript.
        
        Args:
            result: Transcript with segments
        
        Returns:
            Corrected transcript
        """
        for segment in result.get("segments", []):
            text = segment.get("text", "")
            
            # Apply word corrections
            for error, correction in self.word_corrections.items():
                text = text.replace(error, correction)
            
            segment["text"] = text
            
            # Mark potential interjections
            if self._is_interjection(text):
                segment["interjection"] = True
        
        return result
    
    def _is_interjection(self, text):
        """Check if text is likely an interjection."""
        text = text.strip()
        # Short confirmations/responses
        if re.match(r'^(Right|Yeah|Yes|No|Okay|Mm-hmm|Uh-huh)\.?$', text, re.I):
            return True
        # Very short segments (less than 4 words)
        if len(text.split()) <= 3:
            return True
        return False
    
    def save_outputs(self, result, base_name, output_dir="output"):
        """
        Save transcript in multiple formats.
        
        Args:
            result: Transcript data
            base_name: Base filename for outputs
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 1. Text transcript
        transcript = self.format_transcript(result)
        txt_path = output_path / f"{base_name}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(transcript)
        print(f"   ✓ Text: {txt_path}")
        
        # 2. JSON data
        json_data = {
            "metadata": {
                "processed_at": datetime.now().isoformat(),
                "device": self.device,
                "total_segments": len(result.get("segments", []))
            },
            "segments": result.get("segments", [])
        }
        json_path = output_path / f"{base_name}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print(f"   ✓ JSON: {json_path}")
        
        # 3. SRT subtitles
        srt_content = self.generate_srt(result)
        srt_path = output_path / f"{base_name}.srt"
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        print(f"   ✓ SRT: {srt_path}")
    
    def format_transcript(self, result):
        """Format transcript with speaker labels."""
        lines = ["TRANSCRIPT WITH SPEAKER DIARIZATION", "=" * 50, ""]
        
        current_speaker = None
        speaker_text = []
        
        for segment in result.get("segments", []):
            speaker = segment.get("speaker", "UNKNOWN")
            text = segment.get("text", "").strip()
            
            # Mark interjections
            if segment.get("interjection"):
                text = f"*{text}*"
            
            if speaker != current_speaker:
                if current_speaker and speaker_text:
                    lines.append(f"\n[{current_speaker}]:")
                    lines.append(" ".join(speaker_text))
                current_speaker = speaker
                speaker_text = [text]
            else:
                speaker_text.append(text)
        
        # Don't forget last speaker
        if current_speaker and speaker_text:
            lines.append(f"\n[{current_speaker}]:")
            lines.append(" ".join(speaker_text))
        
        return "\n".join(lines)
    
    def generate_srt(self, result):
        """Generate SRT subtitle format."""
        srt_lines = []
        
        for i, segment in enumerate(result.get("segments", []), 1):
            start = segment.get("start", 0)
            end = segment.get("end", 0)
            speaker = segment.get("speaker", "UNKNOWN")
            text = segment.get("text", "").strip()
            
            # Format timestamps
            start_time = self._format_srt_time(start)
            end_time = self._format_srt_time(end)
            
            srt_lines.append(str(i))
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(f"[{speaker}]: {text}")
            srt_lines.append("")
        
        return "\n".join(srt_lines)
    
    def _format_srt_time(self, seconds):
        """Format seconds to SRT timestamp."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Transcribe audio with speaker diarization using WhisperX and PyAnnote"
    )
    
    parser.add_argument(
        "audio_file",
        help="Path to audio file (MP3, WAV, etc.)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory (default: output)"
    )
    
    parser.add_argument(
        "--whisper-model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large", "large-v3"],
        help="Whisper model size (default: base)"
    )
    
    parser.add_argument(
        "--language",
        default="en",
        help="Language code (default: en)"
    )
    
    parser.add_argument(
        "--num-speakers",
        type=int,
        default=2,
        help="Number of speakers (default: 2)"
    )
    
    parser.add_argument(
        "--hf-token",
        help="HuggingFace token (or set HF_TOKEN environment variable)"
    )
    
    parser.add_argument(
        "--no-corrections",
        action="store_true",
        help="Disable automatic corrections"
    )
    
    parser.add_argument(
        "--device",
        choices=["cuda", "cpu"],
        help="Force specific device (auto-detected by default)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Batch size for processing (default: 8)"
    )
    
    args = parser.parse_args()
    
    # Validate input
    if not Path(args.audio_file).exists():
        print(f"Error: Audio file not found: {args.audio_file}")
        return 1
    
    print("=" * 60)
    print("SPEAKER DIARIZATION PIPELINE")
    print("=" * 60)
    print(f"Audio: {args.audio_file}")
    print(f"Size: {Path(args.audio_file).stat().st_size / 1024 / 1024:.2f} MB")
    
    # Initialize diarizer
    diarizer = SpeakerDiarizer(
        hf_token=args.hf_token,
        device=args.device
    )
    
    # Process audio
    try:
        result = diarizer.transcribe_with_speakers(
            args.audio_file,
            whisper_model=args.whisper_model,
            language=args.language,
            num_speakers=args.num_speakers,
            batch_size=args.batch_size,
            apply_corrections=not args.no_corrections
        )
        
        # Save outputs
        print("\n5. Saving outputs...")
        base_name = Path(args.audio_file).stem + "_transcribed"
        diarizer.save_outputs(result, base_name, args.output_dir)
        
        # Summary
        segments = result.get("segments", [])
        speakers = set(seg.get("speaker", "UNKNOWN") for seg in segments)
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Total segments: {len(segments)}")
        print(f"Speakers identified: {len(speakers)}")
        
        if segments:
            duration = segments[-1].get("end", 0)
            print(f"Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
        
        print(f"\n✓ Processing complete!")
        print(f"✓ Check '{args.output_dir}' directory for outputs")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())