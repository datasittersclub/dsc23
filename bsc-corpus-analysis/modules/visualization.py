import json
from pathlib import Path
from dataclasses import asdict

def prepare_visualization_data(results_dict):
    visualization_data = {
        "metadata": {
            "generated_date": "2025-08-11",
            "total_books": len(results_dict),
            "total_scenes": sum(r['scene_count'] for r in results_dict.values()),
            "total_goals": sum(r['goal_count'] for r in results_dict.values()),
            "total_conflicts": sum(r['conflict_count'] for r in results_dict.values()),
            "processor": "SimpleStoryProcessor"
        },
        "books": [],
        "characters": {},
        "character_books": {},
        "conflict_network": [],
        "goals": [],  # Flattened goals for static HTML compatibility
        "goal_network": []  # Goal network data
    }
    
    all_characters = set()
    
    for book_id, book_data in results_dict.items():
        # Convert dataclass objects to dictionaries
        scenes_data = []
        for scene in book_data['scenes']:
            if hasattr(scene, '__dict__'):
                scene_dict = asdict(scene)
            else:
                scene_dict = scene
            scenes_data.append(scene_dict)
            
        goals_data = []
        for goal in book_data['goals']:
            if hasattr(goal, '__dict__'):
                goal_dict = asdict(goal)
            else:
                goal_dict = goal
            goals_data.append(goal_dict)
            all_characters.add(goal_dict.get('character', 'Unknown'))
            
        conflicts_data = []
        for conflict in book_data['conflicts']:
            if hasattr(conflict, '__dict__'):
                conflict_dict = asdict(conflict)
            else:
                conflict_dict = conflict
            conflicts_data.append(conflict_dict)
            
            # Add characters from conflicts
            for char in conflict_dict.get('characters_involved', []):
                all_characters.add(char)
        
        book_viz = {
            "book_id": book_id,
            "book_title": book_data['book_title'],
            "scene_count": book_data['scene_count'],
            "goal_count": book_data['goal_count'],
            "conflict_count": book_data['conflict_count'],
            "scenes": scenes_data,
            "goals": goals_data,
            "conflicts": conflicts_data
        }
        visualization_data["books"].append(book_viz)
        
        # Build character-book relationships
        book_characters = set()
        for goal in goals_data:
            char = goal.get('character', 'Unknown')
            book_characters.add(char)
            if char not in visualization_data["character_books"]:
                visualization_data["character_books"][char] = []
            if book_id not in visualization_data["character_books"][char]:
                visualization_data["character_books"][char].append(book_id)
        
        # Build conflict network
        for conflict in conflicts_data:
            chars = conflict.get('characters_involved', [])
            if len(chars) >= 2:
                visualization_data["conflict_network"].append({
                    "conflict_id": conflict.get('conflict_id'),
                    "characters": chars,
                    "book_id": book_id,
                    "conflict_type": conflict.get('conflict_type'),
                    "description": conflict.get('description', ''),
                    "evidence": conflict.get('evidence', '')
                })
    
    # Character summary
    for char in all_characters:
        if char != 'Unknown':
            char_books = visualization_data["character_books"].get(char, [])
            char_conflicts = [c for c in visualization_data["conflict_network"] if char in c["characters"]]
            visualization_data["characters"][char] = {
                "books": char_books,
                "book_count": len(char_books),
                "conflict_count": len(char_conflicts)
            }
    
    return visualization_data

def export_for_html_visualization(visualization_data, filename="scene_analysis_visualization.json"):
    output_file = Path(filename)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(visualization_data, f, indent=2, ensure_ascii=False)
    return output_file
