# DSC23 Repository

This repository contains three projects that were showcased in issue 23 of the [Data Sitter's Club](https://datasittersclub.github.io/site/) by Anastasia Salter and John Murray.

## Projects Overview

### 1. [DSC Retro Tech Archive](./dsc-retro-tech/)
**Author:** [@amsucf](https://github.com/amsucf) (Anastasia Salter)

A nostalgic 90s-style interactive website showcasing technology mentions from The Baby-Sitters Club book series. Features authentic retro aesthetics with a CRT monitor display and classic BSC vibes.

**Key Features:**
- Authentic 90s web design with CSS animations
- Interactive technology term explorer
- Auto-rotating mentions with keyboard navigation
- Responsive design for all devices
- GitHub Pages ready deployment

**Files:**
- `index.html` - Main retro website
- `styles.css` - 90s aesthetic styling
- `script.js` - Interactive functionality
- `concordance.json` - Technology mention data


### 2. [Speaker Diarization](./speaker-diarization/)
**Author:** [@lucidbard](https://github.com/lucidbard) (John Murray)

A complete speaker diarization pipeline that identifies "who spoke when" in audio recordings using WhisperX for transcription and PyAnnote.audio for speaker identification. Includes automatic correction for common transcription errors and handles natural conversation dynamics.

**Key Features:**
- WhisperX + PyAnnote integration for accurate speaker identification
- Automatic transcription error correction
- Web interface for easy audio processing
- Support for both CPU and GPU processing
- Comprehensive output formatting

### 3. [BSC Corpus Analysis](./bsc-corpus-analysis/) 
**Author:** [@lucidbard](https://github.com/lucidbard) (John Murray)

A comprehensive workflow for analyzing narrative structure, character goals, and scene segmentation in literary corpora. This project provides both a Jupyter notebook for processing and annotation, and an interactive HTML dashboard for visualization. There is also a sample dataset extracted from an analysis of Baby Sitter's Club books using openai-oss. 

**Key Features:**
- Scene segmentation and narrator identification
- Character goal and conflict annotation using LLM analysis
- Interactive D3.js visualization dashboard
- Support for multiple LLM providers (Anthropic, OpenAI, Ollama)
- Project Gutenberg integration for text acquisition

## Getting Started

Each project has its own README with detailed setup instructions:

- **BSC Corpus Analysis**: See [bsc-corpus-analysis/README.md](./bsc-corpus-analysis/README.md)
- **Speaker Diarization**: See [speaker-diarization/README.md](./speaker-diarization/README.md)  
- **DSC Retro Tech**: See [dsc-retro-tech/README.md](./dsc-retro-tech/README.md)

## Repository Structure

```
dsc23/
├── README.md                    # This file
├── bsc-corpus-analysis/         # Literary corpus analysis tools
├── speaker-diarization/         # Audio speaker identification
└── dsc-retro-tech/             # 90s-style tech concordance
