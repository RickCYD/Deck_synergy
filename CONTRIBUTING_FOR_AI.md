# 🤝 Contributing Guide for AI Models

**Step-by-step instructions for adding features to the MTG Deck Synergy Analyzer**

---

## 📖 Table of Contents

1. [Adding a New Synergy Type](#1-adding-a-new-synergy-type)
2. [Adding a New Card Mechanic Detector](#2-adding-a-new-card-mechanic-detector)
3. [Adding a New Game Mechanic to Simulation](#3-adding-a-new-game-mechanic-to-simulation)
4. [Adding a New Dashboard Feature](#4-adding-a-new-dashboard-feature)
5. [Adding a New API Integration](#5-adding-a-new-api-integration)
6. [Adding a New Analysis Tool](#6-adding-a-new-analysis-tool)
7. [Testing Your Changes](#7-testing-your-changes)

---

## 1. Adding a New Synergy Type

**Example:** Adding "Energy synergies" for cards that produce/use energy counters

### Step 1.1: Create an Extractor

**File:** `src/utils/energy_extractors.py` (create new file)

```python
"""Extractors for energy counter mechanics"""
import re

def extract_produces_energy(card):
    """
    Detect if a card produces energy counters

    Args:
        card (dict): Card object with oracle_text, type_line, etc.

    Returns:
        bool: True if card produces energy
    """
    oracle_text = card.get('oracle_text', '').lower()

    patterns = [
        r'get.*energy counter',
        r'you get.*\{e\}',
        r'gain.*energy counter',
    ]

    for pattern in patterns:
        if re.search(pattern, oracle_text):
            return True

    return False


def extract_uses_energy(card):
    """
    Detect if a card spends/uses energy counters

    Args:
        card (dict): Card object

    Returns:
        bool: True if card uses energy
    """
    oracle_text = card.get('oracle_text', '').lower()

    patterns = [
        r'pay.*\{e\}',
        r'remove.*energy counter',
        r'spend.*energy',
    ]

    for pattern in patterns:
        if re.search(pattern, oracle_text):
            return True

    return False


def extract_cares_about_energy(card):
    """
    Detect if a card benefits from energy counters

    Args:
        card (dict): Card object

    Returns:
        bool: True if card cares about energy
    """
    oracle_text = card.get('oracle_text', '').lower()

    patterns = [
        r'for each energy counter',
        r'if you have.*energy counter',
        r'energy counter.*you control',
    ]

    for pattern in patterns:
        if re.search(pattern, oracle_text):
            return True

    return False
```

### Step 1.2: Add Synergy Detection Rule

**File:** `src/synergy_engine/rules.py`

Add this function to the file:

```python
from src.utils.energy_extractors import (
    extract_produces_energy,
    extract_uses_energy,
    extract_cares_about_energy
)

def detect_energy_synergy(card1, card2):
    """
    Detect energy counter synergies between two cards

    Args:
        card1 (dict): First card
        card2 (dict): Second card

    Returns:
        list: List of synergy dictionaries
    """
    synergies = []

    # Producer + User synergy
    if extract_produces_energy(card1) and extract_uses_energy(card2):
        synergies.append({
            'type': 'energy_synergy',
            'reason': f"{card1['name']} produces energy that {card2['name']} can use",
            'strength': 0.7
        })

    # Producer + Cares synergy
    if extract_produces_energy(card1) and extract_cares_about_energy(card2):
        synergies.append({
            'type': 'energy_synergy',
            'reason': f"{card1['name']} generates energy for {card2['name']}'s abilities",
            'strength': 0.6
        })

    # Check reverse direction
    if extract_produces_energy(card2) and extract_uses_energy(card1):
        synergies.append({
            'type': 'energy_synergy',
            'reason': f"{card2['name']} produces energy that {card1['name']} can use",
            'strength': 0.7
        })

    if extract_produces_energy(card2) and extract_cares_about_energy(card1):
        synergies.append({
            'type': 'energy_synergy',
            'reason': f"{card2['name']} generates energy for {card1['name']}'s abilities",
            'strength': 0.6
        })

    return synergies
```

### Step 1.3: Add Synergy Category

**File:** `src/synergy_engine/categories.py`

Add to the `SYNERGY_CATEGORIES` dictionary:

```python
SYNERGY_CATEGORIES = {
    # ... existing categories ...

    'energy_synergy': {
        'label': 'Energy Synergy',
        'color': '#FFD700',  # Gold color
        'description': 'Cards that work together using energy counters',
        'icon': '⚡'
    },

    # ... rest of categories ...
}
```

### Step 1.4: Register the Rule

**File:** `src/synergy_engine/analyzer.py`

Find the synergy rules list and add your new rule:

```python
from src.synergy_engine.rules import (
    # ... existing imports ...
    detect_energy_synergy,
)

def analyze_deck(deck_cards):
    """Main analysis function"""

    # ... existing code ...

    # List of all synergy detection rules
    synergy_rules = [
        # ... existing rules ...
        detect_energy_synergy,
    ]

    # ... rest of function ...
```

### Step 1.5: Create Tests

**File:** `tests/test_energy_synergies.py` (create new file)

```python
import pytest
from src.synergy_engine.rules import detect_energy_synergy
from src.utils.energy_extractors import (
    extract_produces_energy,
    extract_uses_energy,
    extract_cares_about_energy
)

def test_extract_produces_energy():
    """Test energy production detection"""
    card = {
        'name': 'Aether Hub',
        'oracle_text': 'When Aether Hub enters the battlefield, you get {E} (an energy counter).'
    }

    assert extract_produces_energy(card) == True


def test_extract_uses_energy():
    """Test energy usage detection"""
    card = {
        'name': 'Harnessed Lightning',
        'oracle_text': 'Pay {E}{E}{E}: Deal 3 damage to target creature.'
    }

    assert extract_uses_energy(card) == True


def test_energy_synergy_detection():
    """Test energy synergy between producer and user"""
    producer = {
        'name': 'Aether Hub',
        'oracle_text': 'you get {E}'
    }

    user = {
        'name': 'Harnessed Lightning',
        'oracle_text': 'Pay {E}{E}: Deal 2 damage'
    }

    synergies = detect_energy_synergy(producer, user)

    assert len(synergies) > 0
    assert synergies[0]['type'] == 'energy_synergy'
    assert synergies[0]['strength'] == 0.7
```

### Step 1.6: Run Tests

```bash
pytest tests/test_energy_synergies.py -v
```

---

## 2. Adding a New Card Mechanic Detector

**Example:** Adding detection for "Foretell" mechanic

### Step 2.1: Identify the Right Extractor File

Foretell is a keyword mechanic, so it goes in:
**File:** `src/utils/keyword_extractors.py`

### Step 2.2: Add the Extraction Function

Add to `src/utils/keyword_extractors.py`:

```python
def extract_has_foretell(card):
    """
    Detect if a card has the Foretell mechanic

    Args:
        card (dict): Card object

    Returns:
        bool: True if card has Foretell
    """
    oracle_text = card.get('oracle_text', '').lower()

    # Check for foretell keyword
    if 'foretell' in oracle_text:
        return True

    return False


def extract_cares_about_foretell(card):
    """
    Detect if a card benefits from Foretell

    Args:
        card (dict): Card object

    Returns:
        bool: True if card cares about foretelling
    """
    oracle_text = card.get('oracle_text', '').lower()

    patterns = [
        r'whenever you foretell',
        r'foretold card',
        r'cast.*from exile',  # Foretell casts from exile
    ]

    for pattern in patterns:
        if re.search(pattern, oracle_text):
            return True

    return False
```

### Step 2.3: Use in Synergy Rules

Add to `src/synergy_engine/rules.py`:

```python
from src.utils.keyword_extractors import extract_has_foretell, extract_cares_about_foretell

def detect_foretell_synergy(card1, card2):
    """Detect foretell synergies"""
    synergies = []

    if extract_has_foretell(card1) and extract_cares_about_foretell(card2):
        synergies.append({
            'type': 'foretell_synergy',
            'reason': f"{card2['name']} benefits from {card1['name']}'s foretell ability",
            'strength': 0.5
        })

    # Check reverse
    if extract_has_foretell(card2) and extract_cares_about_foretell(card1):
        synergies.append({
            'type': 'foretell_synergy',
            'reason': f"{card1['name']} benefits from {card2['name']}'s foretell ability",
            'strength': 0.5
        })

    return synergies
```

### Step 2.4: Add Category and Register

Follow steps 1.3 and 1.4 from the previous section.

---

## 3. Adding a New Game Mechanic to Simulation

**Example:** Adding "Day/Night" mechanic from Innistrad: Midnight Hunt

### Step 3.1: Add State Tracking

**File:** `Simulation/boardstate.py`

Add to the `BoardState` class `__init__` method:

```python
class BoardState:
    def __init__(self):
        # ... existing initialization ...

        # Day/Night tracking
        self.is_day = None  # None = not started, True = day, False = night
        self.spells_cast_this_turn = 0
```

### Step 3.2: Add Transformation Logic

Add methods to `BoardState` class:

```python
def start_daybound(self):
    """Initialize day/night cycle"""
    if self.is_day is None:
        self.is_day = True  # Always starts as day
        self.log_action("Day/Night cycle begins. It becomes day.")


def check_daynight_transform(self):
    """Check if day/night should change"""
    if self.is_day is None:
        return  # Not tracking day/night

    # Day → Night: If no spells cast this turn
    if self.is_day and self.spells_cast_this_turn == 0:
        self.is_day = False
        self.transform_daynight_cards()
        self.log_action("It becomes night.")

    # Night → Day: If two or more spells cast this turn
    elif not self.is_day and self.spells_cast_this_turn >= 2:
        self.is_day = True
        self.transform_daynight_cards()
        self.log_action("It becomes day.")


def transform_daynight_cards(self):
    """Transform all daybound/nightbound cards"""
    for permanent in self.battlefield:
        if permanent.get('is_daybound') or permanent.get('is_nightbound'):
            # Flip the card
            if 'back_face' in permanent:
                self.transform_card(permanent)


def transform_card(self, card):
    """Transform a double-faced card"""
    # Swap front and back faces
    front = card.copy()
    back = card.get('back_face', {})

    # Update card with back face data
    card.update(back)
    card['back_face'] = front

    self.log_action(f"Transformed {card['name']}")
```

### Step 3.3: Integrate into Turn Cycle

**File:** `Simulation/simulate_game.py`

Add to the end of turn phase:

```python
def end_of_turn_phase(board_state, active_player):
    """End of turn cleanup"""

    # ... existing end of turn logic ...

    # Check day/night transformation
    board_state.check_daynight_transform()

    # Reset spell counter for next turn
    board_state.spells_cast_this_turn = 0
```

Add to spell casting:

```python
def cast_spell(board_state, spell):
    """Cast a spell"""

    # ... existing spell casting logic ...

    # Track spells for day/night
    board_state.spells_cast_this_turn += 1

    # ... rest of function ...
```

### Step 3.4: Add Card Parsing

**File:** `Simulation/oracle_text_parser.py`

Add parsing for daybound abilities:

```python
def parse_daybound(oracle_text, card):
    """Parse daybound ability from card text"""

    if 'daybound' in oracle_text.lower():
        card['is_daybound'] = True

        # If this card enters, start day/night
        card['on_enter_ability'] = {
            'type': 'start_daybound',
            'effect': 'initialize_daynight'
        }

    if 'nightbound' in oracle_text.lower():
        card['is_nightbound'] = True

    return card
```

Add to main parsing function:

```python
def parse_card_abilities(card):
    """Main parsing function"""
    oracle_text = card.get('oracle_text', '')

    # ... existing parsing ...

    # Parse daybound
    card = parse_daybound(oracle_text, card)

    return card
```

### Step 3.5: Create Tests

**File:** `Simulation/tests/test_daynight.py` (create new file)

```python
import pytest
from Simulation.boardstate import BoardState

def test_day_night_initialization():
    """Test that day/night starts as day"""
    board = BoardState()
    board.start_daybound()

    assert board.is_day == True


def test_day_to_night_transform():
    """Test day becomes night when no spells cast"""
    board = BoardState()
    board.start_daybound()
    board.spells_cast_this_turn = 0

    board.check_daynight_transform()

    assert board.is_day == False


def test_night_to_day_transform():
    """Test night becomes day when 2+ spells cast"""
    board = BoardState()
    board.start_daybound()
    board.is_day = False  # Start at night
    board.spells_cast_this_turn = 2

    board.check_daynight_transform()

    assert board.is_day == True


def test_no_transform_with_one_spell():
    """Test night doesn't become day with only 1 spell"""
    board = BoardState()
    board.start_daybound()
    board.is_day = False
    board.spells_cast_this_turn = 1

    board.check_daynight_transform()

    assert board.is_day == False  # Still night
```

### Step 3.6: Run Tests

```bash
pytest Simulation/tests/test_daynight.py -v
```

---

## 4. Adding a New Dashboard Feature

**Example:** Adding a "Deck Comparison" feature

### Step 4.1: Add UI Component

**File:** `app.py`

Add to the layout (find the layout section):

```python
app.layout = html.Div([
    # ... existing layout ...

    # New: Deck Comparison Section
    html.Div([
        html.H3("Deck Comparison"),

        dcc.Dropdown(
            id='comparison-deck-dropdown',
            options=[],  # Will be populated dynamically
            placeholder="Select a deck to compare"
        ),

        html.Div(id='comparison-results'),

        dcc.Graph(id='comparison-chart')
    ], style={'margin-top': '20px'}),

    # ... rest of layout ...
])
```

### Step 4.2: Add Callback

Add callback function:

```python
@app.callback(
    [Output('comparison-results', 'children'),
     Output('comparison-chart', 'figure')],
    [Input('comparison-deck-dropdown', 'value')],
    [State('current-deck-data', 'data')]
)
def compare_decks(comparison_deck_id, current_deck_data):
    """
    Compare current deck with selected deck

    Args:
        comparison_deck_id: ID of deck to compare
        current_deck_data: Current loaded deck data

    Returns:
        tuple: (comparison text, comparison chart)
    """
    if not comparison_deck_id or not current_deck_data:
        return "Load a deck to compare", {}

    # Load comparison deck
    comparison_deck = load_deck_from_storage(comparison_deck_id)

    # Calculate metrics for both decks
    current_metrics = calculate_deck_metrics(current_deck_data)
    comparison_metrics = calculate_deck_metrics(comparison_deck)

    # Create comparison text
    comparison_text = html.Div([
        html.H4("Comparison Results"),
        html.P(f"Current Deck Synergy Score: {current_metrics['synergy_score']:.2f}"),
        html.P(f"Comparison Deck Synergy Score: {comparison_metrics['synergy_score']:.2f}"),
        html.P(f"Difference: {current_metrics['synergy_score'] - comparison_metrics['synergy_score']:.2f}")
    ])

    # Create comparison chart
    chart = {
        'data': [
            {
                'x': ['Synergy', 'Power', 'Consistency'],
                'y': [current_metrics['synergy_score'],
                      current_metrics['power_score'],
                      current_metrics['consistency']],
                'type': 'bar',
                'name': 'Current Deck'
            },
            {
                'x': ['Synergy', 'Power', 'Consistency'],
                'y': [comparison_metrics['synergy_score'],
                      comparison_metrics['power_score'],
                      comparison_metrics['consistency']],
                'type': 'bar',
                'name': 'Comparison Deck'
            }
        ],
        'layout': {
            'title': 'Deck Metrics Comparison',
            'barmode': 'group'
        }
    }

    return comparison_text, chart


def calculate_deck_metrics(deck):
    """Calculate metrics for a deck"""
    # Implement metric calculation
    return {
        'synergy_score': 7.5,
        'power_score': 8.0,
        'consistency': 7.2
    }


def load_deck_from_storage(deck_id):
    """Load a saved deck"""
    # Implement deck loading
    pass
```

### Step 4.3: Test in Browser

```bash
python app.py
# Navigate to http://localhost:8050
# Test the new feature
```

---

## 5. Adding a New API Integration

**Example:** Adding EDHREC API integration for recommendations

### Step 5.1: Create API Module

**File:** `src/api/edhrec.py` (create new file)

```python
"""EDHREC API integration for card recommendations"""
import requests
import json
from typing import List, Dict

EDHREC_API_URL = "https://json.edhrec.com/pages"


def get_commander_recommendations(commander_name: str) -> List[Dict]:
    """
    Get card recommendations for a commander from EDHREC

    Args:
        commander_name: Name of the commander

    Returns:
        list: Recommended cards with scores
    """
    try:
        # Format commander name for URL
        url_name = commander_name.lower().replace(' ', '-').replace(',', '')
        url = f"{EDHREC_API_URL}/commanders/{url_name}.json"

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Extract recommendations
        recommendations = []
        for card in data.get('cardlists', [{}])[0].get('cardviews', []):
            recommendations.append({
                'name': card.get('name'),
                'synergy_score': card.get('synergy', 0),
                'inclusion_rate': card.get('num_decks', 0) / data.get('num_decks', 1),
                'price': card.get('price', 0)
            })

        return recommendations

    except requests.RequestException as e:
        print(f"Error fetching EDHREC data: {e}")
        return []
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Error parsing EDHREC data: {e}")
        return []


def get_theme_recommendations(theme: str, commander_colors: str) -> List[Dict]:
    """
    Get card recommendations for a specific theme

    Args:
        theme: Theme name (e.g., "tokens", "aristocrats")
        commander_colors: Color identity (e.g., "WBG")

    Returns:
        list: Recommended cards
    """
    try:
        url = f"{EDHREC_API_URL}/themes/{theme}.json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Filter by color identity
        recommendations = []
        for card in data.get('cardlists', [{}])[0].get('cardviews', []):
            card_colors = card.get('color_identity', '')

            # Check if card fits color identity
            if all(color in commander_colors for color in card_colors):
                recommendations.append({
                    'name': card.get('name'),
                    'synergy_score': card.get('synergy', 0),
                    'inclusion_rate': card.get('num_decks', 0)
                })

        return recommendations

    except requests.RequestException as e:
        print(f"Error fetching theme data: {e}")
        return []


# Cache for API requests
_edhrec_cache = {}


def get_recommendations_cached(commander_name: str) -> List[Dict]:
    """Get recommendations with caching"""
    if commander_name not in _edhrec_cache:
        _edhrec_cache[commander_name] = get_commander_recommendations(commander_name)

    return _edhrec_cache[commander_name]
```

### Step 5.2: Integrate into Analysis

**File:** `src/analysis/replacement_analyzer.py`

Add import and use:

```python
from src.api.edhrec import get_commander_recommendations

def suggest_replacements(deck, weak_cards):
    """Suggest better cards to replace weak ones"""

    # ... existing logic ...

    # Get EDHREC recommendations
    commander = deck.get('commander', {}).get('name')
    if commander:
        edhrec_recs = get_commander_recommendations(commander)

        # Filter out cards already in deck
        deck_names = [card['name'] for card in deck['cards']]
        new_recs = [rec for rec in edhrec_recs if rec['name'] not in deck_names]

        # Add to suggestions
        suggestions.extend(new_recs[:10])  # Top 10

    return suggestions
```

### Step 5.3: Add to Dashboard

**File:** `app.py`

Add callback to display EDHREC recommendations:

```python
from src.api.edhrec import get_commander_recommendations

@app.callback(
    Output('edhrec-recommendations', 'children'),
    Input('commander-name', 'data')
)
def display_edhrec_recommendations(commander_name):
    """Display EDHREC recommendations"""
    if not commander_name:
        return "Load a deck to see recommendations"

    recs = get_commander_recommendations(commander_name)

    if not recs:
        return "No recommendations found"

    # Create recommendation cards
    cards = []
    for rec in recs[:10]:
        cards.append(html.Div([
            html.H5(rec['name']),
            html.P(f"Synergy: {rec['synergy_score']:.1f}%"),
            html.P(f"Inclusion: {rec['inclusion_rate']:.1f}%"),
            html.P(f"Price: ${rec['price']:.2f}")
        ], style={'border': '1px solid #ccc', 'padding': '10px', 'margin': '5px'}))

    return html.Div(cards)
```

### Step 5.4: Add Tests

**File:** `tests/test_edhrec_api.py` (create new file)

```python
import pytest
from src.api.edhrec import get_commander_recommendations

def test_get_commander_recommendations():
    """Test EDHREC API integration"""
    # Use a well-known commander
    recs = get_commander_recommendations("Teysa Karlov")

    assert isinstance(recs, list)
    if recs:  # If API is available
        assert 'name' in recs[0]
        assert 'synergy_score' in recs[0]


def test_invalid_commander():
    """Test handling of invalid commander"""
    recs = get_commander_recommendations("Not A Real Commander XYZ123")

    assert isinstance(recs, list)
    assert len(recs) == 0  # Should return empty list, not error
```

---

## 6. Adding a New Analysis Tool

**Example:** Adding "Mana Base Analyzer"

### Step 6.1: Create Analysis Module

**File:** `src/analysis/manabase_analyzer.py` (create new file)

```python
"""Mana base analysis tool"""
from typing import Dict, List
from src.utils.ramp_extractors import extract_produces_mana


def analyze_mana_base(deck: Dict) -> Dict:
    """
    Analyze deck's mana base quality

    Args:
        deck: Deck dictionary with cards

    Returns:
        dict: Mana base analysis results
    """
    cards = deck.get('cards', [])

    # Count lands and mana sources
    lands = [c for c in cards if 'land' in c.get('type_line', '').lower()]
    mana_rocks = [c for c in cards if extract_produces_mana(c) and 'land' not in c.get('type_line', '').lower()]

    # Color analysis
    color_sources = count_color_sources(lands + mana_rocks)
    color_pips = count_color_pips(cards)

    # Calculate ratios
    total_cards = len(cards)
    land_ratio = len(lands) / total_cards if total_cards > 0 else 0
    mana_source_ratio = (len(lands) + len(mana_rocks)) / total_cards if total_cards > 0 else 0

    # Check for problems
    problems = []
    recommendations = []

    # Too few lands
    if land_ratio < 0.33:
        problems.append("Low land count - may have mana issues")
        recommendations.append(f"Add {int((0.35 * total_cards) - len(lands))} more lands")

    # Color imbalance
    for color, needed in color_pips.items():
        sources = color_sources.get(color, 0)
        ratio = sources / needed if needed > 0 else 0

        if ratio < 0.3:
            problems.append(f"Not enough {color} sources for {color} pips")
            recommendations.append(f"Add more {color} producing lands")

    return {
        'total_lands': len(lands),
        'total_mana_rocks': len(mana_rocks),
        'land_ratio': land_ratio,
        'mana_source_ratio': mana_source_ratio,
        'color_sources': color_sources,
        'color_pips': color_pips,
        'problems': problems,
        'recommendations': recommendations,
        'score': calculate_mana_base_score(land_ratio, color_sources, color_pips)
    }


def count_color_sources(mana_sources: List[Dict]) -> Dict[str, int]:
    """Count sources for each color"""
    sources = {'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0}

    for card in mana_sources:
        oracle_text = card.get('oracle_text', '').lower()

        # Check produced mana
        if '{w}' in oracle_text or 'add {w}' in oracle_text:
            sources['W'] += 1
        if '{u}' in oracle_text or 'add {u}' in oracle_text:
            sources['U'] += 1
        if '{b}' in oracle_text or 'add {b}' in oracle_text:
            sources['B'] += 1
        if '{r}' in oracle_text or 'add {r}' in oracle_text:
            sources['R'] += 1
        if '{g}' in oracle_text or 'add {g}' in oracle_text:
            sources['G'] += 1

    return sources


def count_color_pips(cards: List[Dict]) -> Dict[str, int]:
    """Count mana pip requirements"""
    pips = {'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0}

    for card in cards:
        mana_cost = card.get('mana_cost', '')

        pips['W'] += mana_cost.count('{W}')
        pips['U'] += mana_cost.count('{U}')
        pips['B'] += mana_cost.count('{B}')
        pips['R'] += mana_cost.count('{R}')
        pips['G'] += mana_cost.count('{G}')

    return pips


def calculate_mana_base_score(land_ratio: float, sources: Dict, pips: Dict) -> float:
    """Calculate overall mana base quality score (0-10)"""
    score = 10.0

    # Deduct for land ratio issues
    if land_ratio < 0.30:
        score -= 3.0
    elif land_ratio < 0.33:
        score -= 1.5
    elif land_ratio > 0.45:
        score -= 1.0

    # Deduct for color imbalance
    for color in ['W', 'U', 'B', 'R', 'G']:
        if pips[color] > 0:
            ratio = sources[color] / pips[color]
            if ratio < 0.25:
                score -= 2.0
            elif ratio < 0.3:
                score -= 1.0

    return max(0.0, min(10.0, score))
```

### Step 6.2: Integrate into Dashboard

**File:** `app.py`

Add callback:

```python
from src.analysis.manabase_analyzer import analyze_mana_base

@app.callback(
    Output('manabase-analysis', 'children'),
    Input('current-deck-data', 'data')
)
def display_manabase_analysis(deck_data):
    """Display mana base analysis"""
    if not deck_data:
        return "Load a deck to analyze mana base"

    analysis = analyze_mana_base(deck_data)

    return html.Div([
        html.H3(f"Mana Base Score: {analysis['score']:.1f}/10"),

        html.Div([
            html.H4("Summary"),
            html.P(f"Total Lands: {analysis['total_lands']}"),
            html.P(f"Mana Rocks: {analysis['total_mana_rocks']}"),
            html.P(f"Land Ratio: {analysis['land_ratio']:.1%}"),
        ]),

        html.Div([
            html.H4("Color Sources"),
            html.Ul([
                html.Li(f"{color}: {count} sources ({pips} pips needed)")
                for color, count in analysis['color_sources'].items()
                for pips in [analysis['color_pips'][color]]
                if pips > 0
            ])
        ]),

        html.Div([
            html.H4("Problems"),
            html.Ul([html.Li(p) for p in analysis['problems']])
        ]) if analysis['problems'] else None,

        html.Div([
            html.H4("Recommendations"),
            html.Ul([html.Li(r) for r in analysis['recommendations']])
        ]) if analysis['recommendations'] else None,
    ])
```

---

## 7. Testing Your Changes

### 7.1: Unit Tests

**Run all tests:**
```bash
pytest
```

**Run specific test file:**
```bash
pytest tests/test_your_feature.py
```

**Run with verbose output:**
```bash
pytest -v
```

**Run with coverage:**
```bash
pytest --cov=src --cov-report=html
```

### 7.2: Integration Testing

**Test synergy detection:**
```python
python -c "
from src.synergy_engine.analyzer import analyze_deck

deck = {
    'cards': [
        {'name': 'Card 1', 'oracle_text': '...'},
        {'name': 'Card 2', 'oracle_text': '...'},
    ]
}

synergies = analyze_deck(deck)
print(f'Found {len(synergies)} synergies')
"
```

**Test simulation:**
```bash
python Simulation/run_simulation.py path/to/test_deck.txt
```

**Test dashboard:**
```bash
python app.py
# Open browser to http://localhost:8050
```

### 7.3: Manual Testing Checklist

- [ ] Code runs without errors
- [ ] Tests pass
- [ ] Feature works as expected in UI (if applicable)
- [ ] No performance regression (test with large deck)
- [ ] Documentation updated
- [ ] Code follows existing patterns
- [ ] No new dependencies added (or added to requirements.txt)

---

## 📚 Additional Resources

- **Architecture:** See `docs/ARCHITECTURE.md`
- **Existing Patterns:** Look at similar features in codebase
- **API Documentation:** Check API provider docs
- **MTG Rules:** https://magic.wizards.com/en/rules

---

## 🎯 Quick Command Reference

```bash
# Development
python app.py                              # Run dashboard
python Simulation/run_simulation.py deck.txt  # Run simulation

# Testing
pytest                                     # All tests
pytest tests/                              # Synergy tests
pytest Simulation/tests/                   # Simulation tests
pytest tests/test_specific.py::test_func   # Single test

# Code Quality
black src/ tests/ Simulation/              # Format code
flake8 src/ tests/                         # Lint code
mypy src/                                  # Type check

# Data Management
python scripts/create_preprocessed_cards.py  # Update card database
python scripts/generate_embeddings.py        # Generate embeddings
python scripts/synergy_rules_report.py       # Coverage report
```

---

*For more details, see `AI_GUIDE_FOR_MODELS.md` and `PROJECT_MAP.md`*
