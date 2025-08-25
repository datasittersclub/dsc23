#!/usr/bin/env python3
"""
Test incremental corpus analysis with just a few books.
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
    print("🧪 Testing Incremental Corpus Analysis")
    print("=" * 50)
    
    # Configuration
    data_dir = "corpus_clean/clean corpus no paratext"
    llm_base_url = "http://172.21.144.1:11434"
    model_name = "gpt-oss:latest"
    sample_size = 5  # Test with just 5 books
    
    # Verify data directory exists
    if not Path(data_dir).exists():
        print(f"❌ Error: Data directory '{data_dir}' not found!")
        return
    
    print(f"📚 Testing with {sample_size} books")
    print(f"🤖 Using model: {model_name}")
    print(f"📊 Visualization will update after each book")
    
    # Initialize components
    try:
        llm_provider = LLMProvider(
            provider='ollama',
            model=model_name,
            api_keys={},
            ollama_url=llm_base_url
        )
        processor = SimpleStoryProcessor(llm_provider)
        
        print(f"\n🚀 Starting test analysis...")
        
        # Process sample with incremental updates
        results = process_entire_corpus(data_dir, processor, sample_size=sample_size)
        
        if results:
            print(f"\n✨ Test complete!")
            print(f"📊 Processed {len(results)} books successfully")
            print(f"📈 Check the visualization file for updates")
        else:
            print(f"\n❌ No results generated")
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
