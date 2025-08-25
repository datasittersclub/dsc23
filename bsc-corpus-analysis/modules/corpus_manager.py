from pathlib import Path
from modules.story_processor import SimpleStoryProcessor
from modules.visualization import prepare_visualization_data
import json

def process_entire_corpus(data_dir, processor, sample_size=None):
    corpus_path = Path(data_dir)
    txt_files = list(corpus_path.glob("*.txt"))
    
    # Sort files alphabetically for consistent processing order
    txt_files.sort(key=lambda x: x.name)
    
    # Apply sample size if specified
    if sample_size and sample_size < len(txt_files):
        txt_files = txt_files[:sample_size]
    
    all_results = {}
    total_books = len(txt_files)
    
    print(f"🚀 Starting corpus analysis of {total_books} books...")
    print(f"📊 Visualization will update after each book")
    print("=" * 60)
    
    for i, book_file in enumerate(txt_files, 1):
        book_id = book_file.stem
        
        print(f"\n📖 Processing book {i}/{total_books}: {book_id}")
        
        with open(book_file, 'r', encoding='utf-8') as f:
            text = f.read().strip()
        
        # Three-phase processing returns {"scenes": [...], "goals": [...], "conflicts": [...]}
        result = processor.analyze_story(text, book_id)
        
        if result and result.get('scenes'):
            scenes = result['scenes']
            goals = result.get('goals', [])
            conflicts = result.get('conflicts', [])
            
            all_results[book_id] = {
                'scenes': scenes,
                'goals': goals,
                'conflicts': conflicts,
                'book_title': book_id.replace('_', ' ').title(),
                'scene_count': len(scenes),
                'goal_count': len(goals),
                'conflict_count': len(conflicts)
            }
            
            print(f"   ✅ Analysis complete: {len(scenes)} scenes, {len(goals)} goals, {len(conflicts)} conflicts")
            
            # Save incremental results after each book
            print(f"   💾 Updating visualization with {len(all_results)} books...")
            save_corpus_results(all_results, data_dir, is_incremental=True)
            
        else:
            print(f"   ❌ Failed to process {book_id}")
    
    print(f"\n🎉 Corpus analysis complete!")
    print(f"📚 Final results: {len(all_results)} books processed")
    
    # Final save with detailed summary
    if all_results:
        print(f"\n📊 Generating final visualization summary...")
        save_corpus_results(all_results, data_dir, is_incremental=False)
    
    return all_results

def save_corpus_results(results, data_dir, is_incremental=True):
    """Save corpus analysis results as visualization JSON"""
    try:
        # Create visualization data
        viz_data = prepare_visualization_data(results)
        
        # Create filename based on data directory
        dir_name = Path(data_dir).name
        filename = f"{dir_name}_gpt-oss:latest_visualization.json"
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(viz_data, f, indent=2, default=str)
        
        if is_incremental:
            # Brief progress update for incremental saves
            print(f"   📊 Updated: {viz_data['metadata']['total_books']} books, "
                  f"{viz_data['metadata']['total_scenes']} scenes, "
                  f"{viz_data['metadata']['total_goals']} goals, "
                  f"{viz_data['metadata']['total_conflicts']} conflicts")
        else:
            # Detailed summary for final save
            print(f"📊 Results saved to: {filename}")
            print(f"📈 Total books: {viz_data['metadata']['total_books']}")
            print(f"🎬 Total scenes: {viz_data['metadata']['total_scenes']}")
            print(f"🎯 Total goals: {viz_data['metadata']['total_goals']}")
            print(f"⚔️ Total conflicts: {viz_data['metadata']['total_conflicts']}")
        
    except Exception as e:
        print(f"❌ Error saving results: {e}")
        import traceback
        traceback.print_exc()
