from .llm_provider import LLMProvider
from .data_models import Scene, Goal, Conflict
import json
import re

class SimpleStoryProcessor:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    def analyze_story(self, story_text, story_id="story"):
        """Three-phase analysis: Scene segmentation, goal extraction, conflict analysis"""
        print(f"🎬 Phase 1: Segmenting scenes for {story_id}")
        
        # Phase 1: Scene segmentation
        scenes = self.segment_scenes(story_text, story_id)
        if not scenes:
            print(f"❌ No scenes found for {story_id}")
            return {"scenes": [], "goals": [], "conflicts": []}
        
        print(f"✅ Found {len(scenes)} scenes")
        print(f"🎯 Phase 2: Analyzing goals across {len(scenes)} scenes")
        
        # Phase 2: Goal analysis
        all_goals = []
        for i, scene in enumerate(scenes, 1):
            print(f"   Analyzing goals in scene {i}/{len(scenes)}...")
            scene_goals = self.analyze_goals(scene)
            all_goals.extend(scene_goals)
        
        print(f"✅ Found {len(all_goals)} total goals")
        print(f"⚡ Phase 3: Analyzing conflicts across {len(scenes)} scenes")
        
        # Phase 3: Conflict analysis
        all_conflicts = []
        for i, scene in enumerate(scenes, 1):
            print(f"   Analyzing conflicts in scene {i}/{len(scenes)}...")
            scene_conflicts = self.analyze_conflicts(scene, all_goals)
            all_conflicts.extend(scene_conflicts)
        
        print(f"✅ Found {len(all_conflicts)} total conflicts")
        
        return {
            "scenes": scenes,
            "goals": all_goals,
            "conflicts": all_conflicts
        }

    def segment_chapters(self, story_text, story_id="story"):
        """Phase 1a: Segment story into chapters first"""
        
        # Look for common chapter markers in Baby-Sitters Club books
        import re
        
        # Common chapter patterns
        chapter_patterns = [
            r'Chapter \d+',
            r'CHAPTER \d+', 
            r'Chapter [IVX]+',
            r'CHAPTER [IVX]+',
            r'\n\d+\n',  # Standalone numbers
            r'\n[IVX]+\n'  # Roman numerals
        ]
        
        chapters = []
        current_pos = 0
        
        # Find all chapter breaks
        for pattern in chapter_patterns:
            matches = list(re.finditer(pattern, story_text, re.IGNORECASE))
            if matches:
                # Use the first pattern that finds chapters
                for i, match in enumerate(matches):
                    chapter_start = current_pos if i == 0 else matches[i-1].end()
                    chapter_end = match.start() if i > 0 else len(story_text)
                    
                    if i > 0:  # Skip first iteration
                        chapter_text = story_text[chapter_start:chapter_end].strip()
                        if len(chapter_text) > 100:  # Only include substantial chapters
                            chapters.append({
                                'chapter_id': f"{story_id}_chapter_{i}",
                                'chapter_num': i,
                                'text': chapter_text
                            })
                    
                    current_pos = match.end()
                
                # Add final chapter
                final_text = story_text[current_pos:].strip()
                if len(final_text) > 100:
                    chapters.append({
                        'chapter_id': f"{story_id}_chapter_{len(matches)+1}",
                        'chapter_num': len(matches) + 1,
                        'text': final_text
                    })
                break
        
        # If no chapters found, treat whole story as one chapter
        if not chapters:
            chapters = [{
                'chapter_id': f"{story_id}_chapter_1",
                'chapter_num': 1,
                'text': story_text
            }]
        
        return chapters

    def identify_narrator(self, chapter_text):
        """Identify the narrator/POV character for this chapter"""
        
        # Limit text for narrator identification
        sample_text = chapter_text[:2000]
        
        prompt = f'''Identify the narrator/point-of-view character in this Baby-sitters Club chapter excerpt.

Look for:
- First person pronouns ("I", "my", "me") 
- Character names mentioned as the speaker
- Self-identification ("My name is...")
- Perspective clues

Text:
{sample_text}

Return JSON:
{{
  "narrator": "character_name",
  "confidence": "high/medium/low",
  "evidence": "Brief quote showing narrator identity"
}}'''

        try:
            response_text = self.llm_provider.call_llm(prompt)
            json_text = self._extract_json(response_text)
            if json_text:
                data = json.loads(json_text)
                return data.get('narrator', 'Unknown')
        except:
            pass
        
        return 'Unknown'

    def _extract_json(self, response_text):
        """Helper method to extract JSON from LLM response"""
        import re
        import json
        
        if isinstance(response_text, str):
            # Try to find JSON in the response
            if response_text.strip().startswith('{'):
                return response_text.strip()
            else:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    return json_match.group()
        return None

    def segment_scenes(self, story_text, story_id="story"):
        """Phase 1: Segment story into chapters, then scenes"""
        
        # First segment into chapters
        chapters = self.segment_chapters(story_text, story_id)
        
        all_scenes = []
        
        for chapter in chapters:
            chapter_text = chapter['text']
            chapter_id = chapter['chapter_id']
            chapter_num = chapter['chapter_num']
            
            # Identify narrator for this chapter
            narrator = self.identify_narrator(chapter_text)
            
            # Segment chapter into scenes (with size limit)
            if len(chapter_text) > 6000:
                chapter_text = chapter_text[:6000]
            
            prompt = f'''Analyze this Baby-sitters Club chapter and identify scene breaks within it.

Chapter {chapter_num} (Narrator: {narrator})

A scene is a continuous sequence in the same location/time. Look for:
- Location changes
- Time jumps  
- Major topic shifts
- Character group changes

Text:
{chapter_text}

Return JSON with this structure:
{{
  "scenes": [
    {{
      "scene_id": "scene_1",
      "description": "Brief description of what happens",
      "text": "The actual scene text"
    }}
  ]
}}'''

            response_text = self.llm_provider.call_llm(prompt)
            
            # Process scenes from this chapter
            json_text = self._extract_json(response_text)
            if json_text:
                try:
                    data = json.loads(json_text)
                    for i, scene_data in enumerate(data.get('scenes', []), 1):
                        scene = Scene(
                            scene_id=f"{chapter_id}_scene_{i}",
                            book_id=story_id,
                            chapter_num=chapter_num,
                            scene_num=i,
                            text=scene_data.get('text', ''),
                            narrator=narrator  # Add narrator info
                        )
                        all_scenes.append(scene)
                except json.JSONDecodeError as e:
                    print(f"JSON parsing error for {chapter_id}: {e}")
                    # Fallback: treat whole chapter as one scene
                    scene = Scene(
                        scene_id=f"{chapter_id}_scene_1",
                        book_id=story_id,
                        chapter_num=chapter_num,
                        scene_num=1,
                        text=chapter_text,
                        narrator=narrator
                    )
                    all_scenes.append(scene)
            else:
                # Fallback: treat whole chapter as one scene
                scene = Scene(
                    scene_id=f"{chapter_id}_scene_1",
                    book_id=story_id,
                    chapter_num=chapter_num,
                    scene_num=1,
                    text=chapter_text,
                    narrator=narrator
                )
                all_scenes.append(scene)
        
        return all_scenes

    def analyze_goals(self, scene):
        """Phase 2: Analyze character goals within a scene"""
        
        text = scene.text
        if len(text) > 4000:  # Limit text size for goal analysis
            text = text[:4000]
        
        prompt = f'''Analyze character goals in this Baby-sitters Club scene:

Scene: {scene.scene_id} (Chapter {scene.chapter_num})
Narrator/POV: {scene.narrator or 'Unknown'}

Text:
{text}

Find what characters want or try to achieve. Pay special attention to the narrator's goals and motivations since this is their perspective.

For each goal, provide a DIRECT QUOTE from the text as evidence.

Respond in JSON:
{{
  "goals": [
    {{
      "character": "Character Name",
      "goal": "What they want to achieve", 
      "evidence": "EXACT quote from text that shows this goal",
      "category": "social/family/personal/academic/babysitting/other",
      "is_narrator": true/false
    }}
  ]
}}

IMPORTANT: 
- Evidence must be exact quotes from the text (phrases or sentences)
- Only include goals with clear textual evidence
- Mark if the goal belongs to the narrator character
- Focus especially on the narrator's internal motivations
- Each goal needs a direct quote showing the character's intention'''
        
        response_text = self.llm_provider.call_llm(prompt)
        
        # Parse JSON response
        json_text = None
        if isinstance(response_text, str):
            if response_text.strip().startswith('{'):
                json_text = response_text.strip()
            else:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group()
        
        if json_text:
            try:
                data = json.loads(json_text)
                goals = []
                for goal_data in data.get('goals', []):
                    goal = Goal(
                        goal_id=f"{scene.scene_id}_goal_{len(goals)+1}",
                        scene_id=scene.scene_id,
                        character=goal_data.get('character', 'Unknown'),
                        goal_text=goal_data.get('goal', ''),
                        motivation_type=goal_data.get('category', 'other'),
                        category=goal_data.get('category', 'other'),
                        evidence=goal_data.get('evidence', ''),
                        confidence=0.8,
                        book_id=scene.book_id
                    )
                    goals.append(goal)
                return goals
            except json.JSONDecodeError as e:
                print(f"JSON parsing error in goal analysis: {e}")
                return []
        return []

    def analyze_conflicts(self, scene, all_goals):
        """Phase 3: Analyze conflicts within a scene"""
        
        text = scene.text
        if len(text) > 4000:  # Limit text size for conflict analysis
            text = text[:4000]
        
        # Find goals from this scene for context
        scene_goals = [g for g in all_goals if g.scene_id == scene.scene_id]
        goals_context = ""
        if scene_goals:
            goals_context = "\n".join([f"- {g.character}: {g.goal_text}" for g in scene_goals])
        
        prompt = f'''Analyze conflicts in this Baby-sitters Club scene:

Scene: {scene.scene_id} (Chapter {scene.chapter_num})
Narrator/POV: {scene.narrator or 'Unknown'}

Text:
{text}

Identified Goals in this scene:
{goals_context}

Find disagreements, tensions, or conflicts between characters. Consider the narrator's perspective since this is their viewpoint.

Respond in JSON:
{{
  "conflicts": [
    {{
      "character1": "First Character Name",
      "character2": "Second Character Name", 
      "conflict_type": "disagreement/rivalry/misunderstanding/competition/other",
      "description": "Brief description of the conflict",
      "evidence": "EXACT quote showing the conflict",
      "involves_narrator": true/false
    }}
  ]
}}

IMPORTANT:
- Evidence must be exact quotes from the text
- Only include conflicts with clear textual evidence  
- Mark if the narrator is involved in the conflict
- Focus on interpersonal tensions and disagreements
- Each conflict needs a direct quote as evidence'''
        
        response_text = self.llm_provider.call_llm(prompt)
        
        # Parse JSON response
        json_text = None
        if isinstance(response_text, str):
            if response_text.strip().startswith('{'):
                json_text = response_text.strip()
            else:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group()
        
        if json_text:
            try:
                data = json.loads(json_text)
                conflicts = []
                for conflict_data in data.get('conflicts', []):
                    # Find affected goal IDs based on characters involved
                    affected_goals = []
                    involved_chars = conflict_data.get('characters_involved', [])
                    for goal in scene_goals:
                        if goal.character in involved_chars:
                            affected_goals.append(goal.goal_id)
                    
                    conflict = Conflict(
                        conflict_id=f"{scene.scene_id}_conflict_{len(conflicts)+1}",
                        scene_id=scene.scene_id,
                        conflict_type=conflict_data.get('type', 'external_obstacle'),
                        description=conflict_data.get('description', ''),
                        characters_involved=involved_chars,
                        goals_affected=affected_goals,
                        evidence=conflict_data.get('evidence', ''),
                        rationale=conflict_data.get('rationale', ''),
                        severity=conflict_data.get('severity', 'medium'),
                        book_id=scene.book_id
                    )
                    conflicts.append(conflict)
                return conflicts
            except json.JSONDecodeError as e:
                print(f"JSON parsing error in conflict analysis: {e}")
                return []
        return []
