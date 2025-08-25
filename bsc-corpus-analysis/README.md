# Story Corpus Analysis

This project provides a complete workflow for analyzing narrative structure, character goals, and scene segmentation in a literary corpus (e.g., Baby-Sitters Club books). It includes a Jupyter notebook for processing and annotation, and an interactive HTML dashboard for visualization.

## Contents
- `corpus_goal_annotations.ipynb`: Jupyter notebook for corpus analysis, scene segmentation, goal/conflict annotation, and HTML data export.
- `index.html`: Interactive dashboard visualizing scene, goal, and conflict data using D3.js.

## Features
### Notebook (`corpus_goal_annotations.ipynb`)
- **LLM Provider Setup**: Choose and configure Anthropic, OpenAI, or Ollama models for text analysis.
- **Environment Setup**: Loads environment variables and dependencies.
- **Scene & Goal Data Classes**: Defines structured data for scenes and goals.
- **Corpus Processing**: Segments scenes, identifies narrators, and annotates character goals/conflicts across the corpus.
- **Visualization Export**: Generates JSON data for use in the dashboard.
- **Download Gutenberg Books**: Includes a cell to download plain text files from Project Gutenberg via their API.

### Dashboard (`index.html`)
- **Dataset Overview**: Displays key statistics (scenes, goals, conflicts, categories).
- **Goal Categories Distribution**: Bar chart of goal types.
- **Scene Length Distribution**: Histogram of scene lengths.
- **Goals vs Conflicts Scatter**: Visualizes scene-level relationships.
- **Character-Goal Network**: Interactive network graph of characters and goal categories.
- **Scene Details Panel**: View detailed annotations for any scene.

## Usage
1. **Run the Notebook**:
   - Restart the kernel and run setup cells (2-9).
   - Test with sample data (cell 9).
   - Process the full corpus (cell 10).
   - Export visualization data (cell 11).
2. **View the Dashboard**:
   - Open `index.html` in a browser.
   - Ensure `scene_analysis_visualization.json` (exported from the notebook) is in the same directory.
3. **Download Gutenberg Books**:
   - Use the last cell in the notebook to download books by ID: `download_gutenberg_books([1342, 1661, 2701])`

## Requirements
- Python 3.8+
- Jupyter Notebook
- Required packages: `ipywidgets`, `requests`, `pandas`, `numpy`, `tqdm`, `python-dotenv`, `d3.js` (for dashboard)
- API keys for LLM providers (if using Anthropic/OpenAI)

## License
This project is for educational and research use. See individual files for additional license information.
