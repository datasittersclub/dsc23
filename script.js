// BSC Retro Tech Concordance JavaScript

let concordanceData = null;
let currentTerm = null;
let currentContexts = [];
let currentIndex = 0;
let rotationInterval = null;

// Load the concordance data
async function loadConcordanceData() {
    try {
        const response = await fetch('concordance.json');
        concordanceData = await response.json();
        initializeApp();
    } catch (error) {
        console.error('Error loading concordance data:', error);
        document.getElementById('contentArea').innerHTML = `
            <div class="welcome-message">
                <h3>Error Loading Data</h3>
                <p>Could not load the concordance data. Please check that concordance.json is available.</p>
            </div>
        `;
    }
}

// Initialize the application
function initializeApp() {
    if (!concordanceData) return;
    
    createTermButtons();
    updateStats();
}

// Create dropdown options for each term
function createTermButtons() {
    const dropdown = document.getElementById('termDropdown');
    const terms = concordanceData.top_20_terms;
    
    // Clear existing options (except the first placeholder)
    dropdown.innerHTML = '<option value="">-- Choose a Tech Term --</option>';
    
    terms.forEach(termData => {
        const option = document.createElement('option');
        option.value = termData.term;
        option.textContent = `${termData.term} (${termData.count} mentions)`;
        dropdown.appendChild(option);
    });
    
    // Add event listener for dropdown changes
    dropdown.addEventListener('change', (event) => {
        if (event.target.value) {
            selectTerm(event.target.value);
        } else {
            clearSelection();
        }
    });
}

// Select a term and start displaying its contexts
function selectTerm(termName) {
    // Clear any existing rotation
    if (rotationInterval) {
        clearInterval(rotationInterval);
    }
    
    // Find the term data
    const termData = concordanceData.top_20_terms.find(t => t.term === termName);
    if (!termData) return;
    
    currentTerm = termName;
    currentContexts = termData.contexts;
    currentIndex = 0;
    
    // Update UI
    updateActiveButton(termName);
    updateMonitorInfo(termName, termData.count);
    
    // Start rotation
    displayCurrentContext();
    startRotation();
}

// Update which dropdown option appears selected
function updateActiveButton(activeTerm) {
    const dropdown = document.getElementById('termDropdown');
    const statusText = document.getElementById('statusText');
    
    dropdown.value = activeTerm;
    
    // Update status text and visual feedback
    if (activeTerm) {
        statusText.textContent = `ANALYZING: ${activeTerm.toUpperCase()}`;
        dropdown.style.borderColor = 'var(--accent-yellow)';
        dropdown.style.boxShadow = 'inset 0 2px 4px rgba(0,0,0,0.5), 0 0 20px rgba(255,215,0,0.3)';
    } else {
        statusText.textContent = 'READY TO SEARCH';
        dropdown.style.borderColor = '#555';
        dropdown.style.boxShadow = 'inset 0 2px 4px rgba(0,0,0,0.5), 0 0 10px rgba(0,255,0,0.2)';
    }
}

// Display the current context
function displayCurrentContext() {
    if (!currentContexts || currentContexts.length === 0) return;
    
    const context = currentContexts[currentIndex];
    const contentArea = document.getElementById('contentArea');
    
    // Create highlighted context text
    const contextText = context.context.replace(
        `[${context.term_found}]`,
        `<span class="highlight">${context.term_found}</span>`
    );
    
    contentArea.innerHTML = `
        <div class="concordance-entry">
            <div class="context-text">${contextText}</div>
            <div class="entry-info">
                <div>📖 Book: ${formatBookTitle(context.file)}</div>
                <div>🔍 Term found: "${context.term_found}"</div>
                <div>📍 Position: ${context.position.toLocaleString()}</div>
            </div>
        </div>
    `;
    
    // Update counter
    updateCounter();
}

// Format book title for display with proper capitalization
function formatBookTitle(filename) {
    // Remove file extension
    let title = filename.replace('.txt', '');
    
    // Remove everything before and including the first underscore (like "012c_")
    const underscoreIndex = title.indexOf('_');
    if (underscoreIndex !== -1) {
        title = title.substring(underscoreIndex + 1);
    }
    
    // Replace underscores with spaces
    title = title.replace(/_/g, ' ');
    
    // Words that should not be capitalized (except when they're the first word)
    const lowercaseWords = ['and', 'the', 'at', 'in', 'on', 'of', 'a', 'an', 'or', 'but', 'for', 'nor', 'so', 'yet', 'to', 'with', 'by', 'from'];
    
    // Split into words and capitalize appropriately
    const words = title.split(' ');
    const formattedWords = words.map((word, index) => {
        const lowerWord = word.toLowerCase();
        
        // Always capitalize the first word, or if it's not in the lowercase list
        if (index === 0 || !lowercaseWords.includes(lowerWord)) {
            return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
        } else {
            return lowerWord;
        }
    });
    
    return formattedWords.join(' ');
}

// Clear selection and return to welcome screen
function clearSelection() {
    // Clear any existing rotation
    if (rotationInterval) {
        clearInterval(rotationInterval);
        rotationInterval = null;
    }
    
    currentTerm = null;
    currentContexts = [];
    currentIndex = 0;
    
    // Reset dropdown and status
    const dropdown = document.getElementById('termDropdown');
    const statusText = document.getElementById('statusText');
    dropdown.value = '';
    statusText.textContent = 'READY TO SEARCH';
    updateActiveButton('');
    
    // Show welcome message
    document.getElementById('contentArea').innerHTML = `
        <div class="welcome-message">
            <h3>🌟 Welcome to the BSC Tech Archive! 🌟</h3>
            <p>📚 Explore technology mentions from The Babysitter's Club books! 📚</p>
            <div class="welcome-features">
                <div>🎮 Interactive retro display</div>
                <div>⚡ Auto-rotating mentions</div>
                <div>🔍 20 tech terms to discover</div>
            </div>
            <div class="blink">► Select a term from the control panel below! ◄</div>
        </div>
    `;
    
    document.getElementById('currentTerm').textContent = 'No term selected';
    document.getElementById('mentionCounter').textContent = '0 / 0';
}

// Start automatic rotation through contexts
function startRotation() {
    if (rotationInterval) {
        clearInterval(rotationInterval);
    }
    
    rotationInterval = setInterval(() => {
        currentIndex = (currentIndex + 1) % currentContexts.length;
        displayCurrentContext();
    }, 4000); // Rotate every 4 seconds
}

// Update the monitor info display
function updateMonitorInfo(termName, totalMentions) {
    document.getElementById('currentTerm').textContent = `Current: ${termName}`;
    document.getElementById('mentionCounter').textContent = `${currentIndex + 1} / ${totalMentions}`;
}

// Update the mention counter
function updateCounter() {
    if (currentTerm && currentContexts) {
        document.getElementById('mentionCounter').textContent = 
            `${currentIndex + 1} / ${currentContexts.length}`;
    }
}

// Update statistics display
function updateStats() {
    if (!concordanceData) return;
    
    const stats = concordanceData.summary;
    document.getElementById('statsInfo').textContent = 
        `📊 ${stats.total_mentions} total mentions • ${stats.total_unique_terms_found} unique terms • ${stats.total_files_processed} books processed 📊`;
}

// Add keyboard navigation
document.addEventListener('keydown', (event) => {
    if (!currentContexts || currentContexts.length === 0) return;
    
    switch(event.key) {
        case 'ArrowLeft':
        case 'ArrowUp':
            // Previous context
            currentIndex = currentIndex === 0 ? currentContexts.length - 1 : currentIndex - 1;
            displayCurrentContext();
            break;
            
        case 'ArrowRight':
        case 'ArrowDown':
        case ' ':
            // Next context
            currentIndex = (currentIndex + 1) % currentContexts.length;
            displayCurrentContext();
            break;
            
        case 'Escape':
            // Clear selection
            clearSelection();
            break;
    }
    
    // Prevent default for navigation keys
    if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', ' '].includes(event.key)) {
        event.preventDefault();
    }
});

// Add some retro sound effects (optional - requires user interaction)
function playRetroBeep() {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.2);
    } catch (error) {
        // Silently fail if audio context is not available
    }
}

// Add click sound to dropdown
document.addEventListener('change', (event) => {
    if (event.target.id === 'termDropdown') {
        playRetroBeep();
    }
});

// Easter egg: Konami code
let konamiSequence = [];
const konamiCode = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'KeyB', 'KeyA'];

// Konami code easter egg handler (separate from navigation)
document.addEventListener('keydown', (event) => {
    // Handle Konami code separately
    konamiSequence.push(event.code);
    
    if (konamiSequence.length > konamiCode.length) {
        konamiSequence.shift();
    }
    
    if (konamiSequence.length === konamiCode.length && 
        konamiSequence.every((key, index) => key === konamiCode[index])) {
        
        // Easter egg activated!
        document.body.style.animation = 'rainbow 0.5s infinite';
        setTimeout(() => {
            document.body.style.animation = '';
        }, 5000);
        
        // Show special message
        const contentArea = document.getElementById('contentArea');
        const originalContent = contentArea.innerHTML;
        contentArea.innerHTML = `
            <div class="welcome-message">
                <h3>🌈 KONAMI CODE ACTIVATED! 🌈</h3>
                <p>You've unlocked the secret BSC rainbow mode!</p>
                <p style="color: var(--accent-yellow);">Kristy would be proud of your gaming skills! 🎮</p>
                <div class="blink">► 30 lives added! (Just kidding!) 😄</div>
            </div>
        `;
        
        setTimeout(() => {
            if (currentTerm) {
                displayCurrentContext();
            } else {
                contentArea.innerHTML = originalContent;
            }
        }, 5000);
        
        konamiSequence = [];
    }
});

// Add rainbow animation for easter egg
const style = document.createElement('style');
style.textContent = `
    @keyframes rainbow {
        0% { filter: hue-rotate(0deg); }
        100% { filter: hue-rotate(360deg); }
    }
`;
document.head.appendChild(style);

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', loadConcordanceData);

// Add some helpful instructions
console.log(`
🌟 BSC Retro Tech Concordance Controls 🌟
- Select a term from the dropdown to start viewing mentions
- Use arrow keys or spacebar to navigate through mentions
- Press Escape to return to the welcome screen
- Try the Konami code for a surprise! ⬆⬆⬇⬇⬅➡⬅➡BA
`);
