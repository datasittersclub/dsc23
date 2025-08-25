#!/usr/bin/env python3
"""
Run full corpus analysis with incremental visualization updates.
This script processes all books in the corpus and updates the visualization
JSON file after each book is completed.
"""

import os
import sys
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

from modules.story_processor import SimpleStoryProcessor
from modules.corpus_manager import process_entire_corpus
from modules.llm_provider import LLMProvider

def main():
    print("🕹️ Baby-Sitters Club Full Corpus Analysis")
    print("=" * 60)
    
    # Configuration
    data_dir = "corpus_clean/clean corpus no paratext"
    llm_base_url = "http://172.21.144.1:11434"
    model_name = "gpt-oss:latest"
    
    # Verify data directory exists
    if not Path(data_dir).exists():
        print(f"❌ Error: Data directory '{data_dir}' not found!")
        return
    
    # Count total files
    corpus_path = Path(data_dir)
    txt_files = list(corpus_path.glob("*.txt"))
    total_files = len(txt_files)
    
    print(f"📚 Found {total_files} books to analyze")
    print(f"🤖 Using model: {model_name}")
    print(f"🌐 LLM server: {llm_base_url}")
    print(f"📊 Visualization will update after each book")
    
    # Ask for confirmation
    response = input(f"\n⚡ Process all {total_files} books with incremental updates? (y/N): ")
    if response.lower() != 'y':
        print("❌ Analysis cancelled")
        return
    
    # Initialize components
    try:
        llm_provider = LLMProvider(
            provider='ollama',
            model=model_name,
            api_keys={},
            ollama_url=llm_base_url
        )
        processor = SimpleStoryProcessor(llm_provider)
        
        print(f"\n🚀 Starting analysis...")
        print(f"💡 You can monitor progress by checking the visualization file")
        print(f"📂 File: '{Path(data_dir).name}_gpt-oss:latest_visualization.json'")
        print(f"🌐 Or refresh the dashboard at http://172.21.148.127:5002/dashboard")
        
        # Process the entire corpus with incremental updates
        results = process_entire_corpus(data_dir, processor)
        
        if results:
            print(f"\n✨ SUCCESS! Analysis complete!")
            print(f"📊 Processed {len(results)} books successfully")
            print(f"📈 Check the dashboard for updated visualizations")
        else:
            print(f"\n❌ No results generated")
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Analysis interrupted by user")
        print(f"📊 Partial results may be available in the visualization file")
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
