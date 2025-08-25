// Transform the new data structure to match the static HTML expectations
function transformData(newData) {
    const transformed = {
        scenes: [],
        goals: [],
        conflicts: [],
        categories: {
            goals: {}
        }
    };

    if (!newData.books) {
        console.error('No books data found');
        return transformed;
    }

    // Process each book
    newData.books.forEach(book => {
        // Process scenes
        if (book.scenes) {
            book.scenes.forEach(scene => {
                const sceneObj = {
                    id: scene.scene_id || `${book.book_id}_scene_${scene.scene_num || 'unknown'}`,
                    scene_length: scene.text_length || 0,
                    scene_num: scene.scene_num || 0,
                    book_id: book.book_id,
                    book_title: book.book_title,
                    text_preview: scene.text_preview || '',
                    goals_count: 0,
                    conflicts_count: 0
                };
                transformed.scenes.push(sceneObj);
            });
        }

        // Process goals
        if (book.goals) {
            book.goals.forEach(goal => {
                const goalObj = {
                    goal_id: goal.goal_id,
                    scene_id: goal.scene_id,
                    character: goal.character,
                    goal_text: goal.goal_text,
                    category: goal.category || 'unknown',
                    motivation_type: goal.motivation_type,
                    evidence: goal.evidence,
                    confidence: goal.confidence,
                    book_id: goal.book_id
                };
                transformed.goals.push(goalObj);

                // Count goals by category
                const category = goal.category || 'unknown';
                transformed.categories.goals[category] = (transformed.categories.goals[category] || 0) + 1;

                // Update scene goals count
                const scene = transformed.scenes.find(s => s.id === goal.scene_id);
                if (scene) {
                    scene.goals_count++;
                }
            });
        }

        // Process conflicts
        if (book.conflicts) {
            book.conflicts.forEach(conflict => {
                const conflictObj = {
                    conflict_id: conflict.conflict_id,
                    scene_id: conflict.scene_id || `${book.book_id}_scene_unknown`,
                    characters: conflict.characters || [],
                    conflict_type: conflict.conflict_type,
                    description: conflict.description,
                    evidence: conflict.evidence,
                    book_id: conflict.book_id || book.book_id
                };
                transformed.conflicts.push(conflictObj);

                // Update scene conflicts count
                const scene = transformed.scenes.find(s => s.id === conflict.scene_id);
                if (scene) {
                    scene.conflicts_count++;
                }
            });
        }
    });

    // Add network data for compatibility
    if (newData.characters) {
        transformed.characters = newData.characters;
    }
    if (newData.character_books) {
        transformed.character_books = newData.character_books;
    }
    if (newData.conflict_network) {
        transformed.conflict_network = newData.conflict_network;
    }

    return transformed;
}

// If running in Node.js environment
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { transformData };
}
