# Development Guide

This guide is for developers who want to contribute to or extend the MTG Commander Deck Synergy Visualizer.

## Table of Contents
- [Development Setup](#development-setup)
- [Architecture Overview](#architecture-overview)
- [Adding New Synergies](#adding-new-synergies)
- [Testing](#testing)
- [Code Style](#code-style)
- [Common Tasks](#common-tasks)

## Development Setup

### 1. Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd Deck_synergy

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download card data
python3 scripts/create_minimal_cards.py
```

### 2. Development Dependencies

```bash
# Install development tools (optional)
pip install black pytest ipython jupyter
```

### 3. Running in Development Mode

```bash
# Run with auto-reload
python app.py

# The app runs in debug mode by default (DEBUG=True in app.py)
# Any code changes will trigger an automatic reload
```

## Architecture Overview

### Data Flow

```
User Input (Archidekt URL)
    ↓
Archidekt API → Fetch deck list
    ↓
Scryfall API / Local Cache → Fetch card details
    ↓
Synergy Engine → Analyze pairwise synergies
    ↓
Graph Builder → Create Cytoscape elements
    ↓
Dash UI → Display interactive graph
```

### Key Components

#### 1. **Synergy Engine** (`src/synergy_engine/`)
- **analyzer.py**: Orchestrates all synergy detection
- **Individual synergy files**: Each handles one category (ETB, tokens, etc.)
- **Returns**: List of synergy dictionaries with strength scores

#### 2. **Card Extractors** (`src/utils/card_advantage_extractors.py`)
- **Purpose**: Extract specific mechanics from card text
- **extract_tutors()**: Identifies tutors and their restrictions
- **extract_card_draw()**: Identifies card draw effects
- **classify_card_advantage()**: Aggregates all mechanics

#### 3. **Recommendation Engine** (`src/api/recommendations.py`)
- **Purpose**: Suggest cards to add to decks
- **Scoring**: Multi-level (pairwise, three-way, global)
- **Database**: Uses preprocessed card database with synergy tags

#### 4. **Graph Builder** (`src/utils/graph_builder.py`)
- **Purpose**: Convert deck + synergies → Cytoscape format
- **create_node()**: Builds card nodes with metadata
- **create_edge()**: Builds synergy edges with weights

## Adding New Synergies

### Step 1: Add Detection Logic

Create or edit a synergy file in `src/synergy_engine/`:

```python
# src/synergy_engine/my_new_synergy.py

def detect_my_new_synergy(card1: Dict, card2: Dict) -> List[Dict]:
    """
    Detect synergies for [describe what it detects]

    Examples:
    - Card A + Card B = [describe interaction]

    Args:
        card1: First card dictionary
        card2: Second card dictionary

    Returns:
        List of synergy dictionaries with 'category', 'strength', 'description'
    """
    synergies = []

    # Get card properties
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Check for synergy condition
    if 'keyword in card1' in card1_text and 'keyword in card2' in card2_text:
        synergies.append({
            'category': 'My Synergy Category',
            'card1_role': 'Enabler',
            'card2_role': 'Payoff',
            'description': f"{card1['name']} enables {card2['name']}",
            'strength': 2.0,  # Adjust based on power level
            'combo_notes': 'Optional additional notes'
        })

    return synergies
```

### Step 2: Register in Analyzer

Edit `src/synergy_engine/analyzer.py`:

```python
from src.synergy_engine.my_new_synergy import detect_my_new_synergy

# In analyze_deck_synergies():
synergy_functions = [
    # ... existing functions ...
    detect_my_new_synergy,  # Add your function
]
```

### Step 3: Add Synergy Tags (Optional)

If you want recommendations to use this synergy, add tags to `scripts/create_preprocessed_cards.py`:

```python
def extract_synergy_tags(card: Dict) -> List[str]:
    tags = []
    text = card.get('oracle_text', '').lower()

    # Add your tag detection
    if re.search(r'your pattern here', text):
        tags.append('my_new_tag')

    return tags
```

Then regenerate the database:

```bash
python3 scripts/create_preprocessed_cards.py
```

### Step 4: Add Scoring Rules (Optional)

If you want the recommendation engine to score this synergy, edit `src/api/recommendations.py`:

```python
# In _calculate_synergy_score():

# Add to strategic_tags for higher weight
strategic_tags = {
    # ... existing tags ...
    'my_new_tag',
}

# Or add complementary pair for +50 bonus
complementary_pairs = [
    # ... existing pairs ...
    ('my_tag1', 'my_tag2', 5, 3),  # Need 5+ tag1 and 3+ tag2
]
```

### Step 5: Test with Real Decks

```python
# Test in Python REPL
from src.synergy_engine.my_new_synergy import detect_my_new_synergy

card1 = {
    'name': 'Test Card 1',
    'oracle_text': 'Your test text...'
}
card2 = {
    'name': 'Test Card 2',
    'oracle_text': 'Your test text...'
}

result = detect_my_new_synergy(card1, card2)
print(result)
```

## Testing

### Manual Testing

1. Load a deck with the expected synergy
2. Check the graph for the synergy edge
3. Click on one of the cards
4. Verify the synergy appears in the right panel with correct description

### Python REPL Testing

```python
# Test synergy detection
from src.synergy_engine.analyzer import analyze_deck_synergies

deck_data = {
    'cards': [
        {'name': 'Card 1', 'oracle_text': '...'},
        {'name': 'Card 2', 'oracle_text': '...'},
    ]
}

synergies = analyze_deck_synergies(deck_data)
print(f"Found {len(synergies)} synergies")

# Test card extraction
from src.utils.card_advantage_extractors import extract_tutors

card = {'name': 'Demonic Tutor', 'oracle_text': '...'}
result = extract_tutors(card)
print(result)
```

### Integration Testing

```bash
# Run full analysis on a saved deck
python3 -c "
import json
from src.synergy_engine.analyzer import analyze_deck_synergies

with open('data/decks/your_deck.json') as f:
    deck_data = json.load(f)

synergies = analyze_deck_synergies(deck_data)
print(f'Found {len(synergies)} synergies')
for syn in synergies[:5]:
    print(f\"  {syn['card1']} ↔ {syn['card2']}: {syn['category']}\")
"
```

## Code Style

### Python Style Guide

- **PEP 8** compliance
- **4 spaces** for indentation
- **Snake_case** for functions and variables
- **PascalCase** for classes
- **UPPER_CASE** for constants

### Documentation Standards

```python
def my_function(param1: str, param2: int) -> Dict:
    """
    Brief description of what the function does.

    Longer description with more details about behavior,
    edge cases, and usage notes.

    Args:
        param1: Description of first parameter
        param2: Description of second parameter

    Returns:
        Description of return value and its structure

    Examples:
        >>> my_function('test', 5)
        {'result': 'value'}
    """
    pass
```

### Commit Messages

```
<type>: <short description>

<optional detailed description>

Examples:
- feat: Add landfall synergy detection
- fix: Correct Recruiter of the Guard toughness restriction
- docs: Update README with new features
- refactor: Extract tutor validation to separate function
```

## Common Tasks

### Update Card Cache

When Scryfall releases new cards:

```bash
# Download latest Scryfall data
curl -o data/cards/oracle-cards.json https://api.scryfall.com/bulk-data/oracle-cards

# Regenerate minimal cache
python3 scripts/create_minimal_cards.py

# Regenerate preprocessed cache
python3 scripts/create_preprocessed_cards.py
```

### Add a New Card Role

Edit `src/utils/card_roles.py`:

```python
ROLE_CATEGORIES = {
    'resource_generation': {
        'label': 'Resource Generation',
        'roles': [
            # ... existing roles ...
            {
                'key': 'my_new_role',
                'label': 'My New Role',
                'patterns': [r'pattern to match in oracle text']
            }
        ]
    }
}
```

### Debug Synergy Detection

Add debug prints:

```python
def detect_my_synergy(card1, card2):
    synergies = []

    # Add debug output
    print(f"[DEBUG] Checking {card1['name']} + {card2['name']}")

    if condition:
        print(f"[DEBUG] Found synergy!")
        synergies.append({...})

    return synergies
```

Or use the built-in debug mode in recommendations:

```python
# In app.py, when calling get_recommendations:
rec_result = recommendations.get_recommendations(
    deck_cards=deck_cards,
    color_identity=colors,
    limit=10,
    debug=True  # Enables detailed scoring output
)
```

### Profile Performance

```python
import cProfile
import pstats

# Profile synergy analysis
pr = cProfile.Profile()
pr.enable()

synergies = analyze_deck_synergies(deck_data)

pr.disable()
stats = pstats.Stats(pr)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 slowest functions
```

### Add Custom Synergy Weights

Edit `src/synergy_engine/analyzer.py`:

```python
# Adjust synergy strength based on card properties
def calculate_synergy_strength(base_strength: float, card1: Dict, card2: Dict) -> float:
    strength = base_strength

    # Boost for expensive cards
    if card2.get('cmc', 0) >= 6:
        strength += 0.5

    # Boost for legendary creatures
    if 'legendary' in card2.get('type_line', '').lower():
        strength += 0.3

    return strength
```

## Troubleshooting Development Issues

### Import Errors

```bash
# Make sure you're in the project root
cd /path/to/Deck_synergy

# Make sure virtual environment is activated
source venv/bin/activate

# Make sure src/ is in Python path (should be automatic)
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Database Issues

```bash
# Regenerate all cached data
python3 scripts/create_minimal_cards.py
python3 scripts/create_preprocessed_cards.py

# Check database sizes
ls -lh data/cards/
```

### Memory Issues with Large Decks

```python
# Reduce analysis scope in analyzer.py
SYNERGY_THRESHOLD = 0.5  # Increase to filter more synergies
MAX_SYNERGIES_PER_CARD = 50  # Limit synergies per card
```

## Resources

- **Scryfall API Docs**: https://scryfall.com/docs/api
- **Dash Documentation**: https://dash.plotly.com/
- **Cytoscape.js Docs**: https://js.cytoscape.org/
- **MTG Comprehensive Rules**: https://magic.wizards.com/en/rules

## Getting Help

- Check existing [Issues](https://github.com/username/Deck_synergy/issues)
- Review [Architecture Docs](ARCHITECTURE.md)
- Ask in [Discussions](https://github.com/username/Deck_synergy/discussions)

---

Happy coding! 🚀
