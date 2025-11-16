# CLAUDE.md - AI Assistant Guide for Deck Synergy Analyzer

> **Purpose:** This guide is specifically designed for Claude Code and other AI assistants working on the MTG Commander Deck Synergy Analyzer. It provides essential context, workflows, and conventions to ensure effective contributions.

**Last Updated:** 2025-11-16
**Version:** 2.0
**Repository:** Deck_synergy

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Project Overview](#project-overview)
3. [Codebase Architecture](#codebase-architecture)
4. [Development Workflows](#development-workflows)
5. [Git Conventions](#git-conventions)
6. [Coding Conventions](#coding-conventions)
7. [Common Tasks](#common-tasks)
8. [Testing Guidelines](#testing-guidelines)
9. [Critical Files Reference](#critical-files-reference)
10. [Dos and Don'ts](#dos-and-donts)

---

## Quick Start

### Essential Context
- **Language:** Python 3.9+
- **Framework:** Dash (Flask-based), Plotly, Cytoscape.js
- **Domain:** Magic: The Gathering (MTG) card game mechanics
- **Main Purpose:** Analyze Commander decks for synergies and simulate gameplay
- **Codebase Size:** ~19,000 lines of Python across 80+ files
- **Key Feature:** Detects 69+ types of card interactions

### First Steps
1. **Read this file completely** - You're doing it!
2. **Check existing AI guides:**
   - `AI_GUIDE_FOR_MODELS.md` - Comprehensive navigation guide
   - `PROJECT_MAP.md` - Quick file lookup reference
   - `CONTRIBUTING_FOR_AI.md` - Feature addition tutorials
3. **Understand the three main systems:**
   - Synergy Analysis Engine (fast, pattern-based)
   - Game Simulation Engine (slow, rule-accurate)
   - Web Dashboard (Dash/Flask application)

### Running the Application
```bash
# Activate virtual environment (if using one)
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Download card data (first time only)
python scripts/create_minimal_cards.py

# Start the dashboard
python app.py

# Access at http://localhost:8050
```

### Running Tests
```bash
# All tests
pytest

# Synergy engine tests only
pytest tests/

# Simulation engine tests only
pytest Simulation/tests/

# Specific test file
pytest tests/test_synergy_rules.py -v
```

---

## Project Overview

### What This Project Does

The **MTG Commander Deck Synergy Analyzer** is a sophisticated web application that:

1. **Imports** Commander decks from Archidekt URLs
2. **Analyzes** card interactions using 69+ synergy detection rules
3. **Visualizes** synergies as an interactive graph network
4. **Simulates** deck performance with statistical game simulations
5. **Recommends** card additions/removals to optimize deck synergy
6. **Detects** verified infinite combos from Commander Spellbook database

### Three Main Systems

#### 1. Synergy Analysis Engine
- **Location:** `src/synergy_engine/`
- **Entry Point:** `analyzer.py`
- **Speed:** Fast (15-30 seconds per deck)
- **Method:** Rule-based pattern matching
- **Output:** Synergy scores, categories, and descriptions

**How it works:**
```python
For each card pair (card1, card2) in deck:
    For each rule in 69+ synergy rules:
        If rule.detect(card1, card2):
            Add synergy with strength score (1.0 - 50.0)
```

#### 2. Game Simulation Engine
- **Location:** `Simulation/`
- **Entry Point:** `simulate_game.py`
- **Speed:** Slow (seconds per simulation, thousands needed)
- **Method:** Full MTG rules implementation
- **Output:** Statistical deck performance metrics

**Core Files:**
- `boardstate.py` (194KB) - ALL MTG game mechanics
- `simulate_game.py` - Game loop and turn phases
- `oracle_text_parser.py` - Parse card abilities

#### 3. Web Dashboard
- **Location:** `app.py` (3,387 lines)
- **Framework:** Dash (React-based Python framework)
- **Visualization:** Cytoscape.js for graphs, Plotly for charts
- **Pattern:** Callback-based reactive updates

### Key Technologies

| Technology | Purpose | Where Used |
|------------|---------|------------|
| **Dash** | Web framework | `app.py` |
| **Cytoscape.js** | Graph visualization | Synergy network display |
| **Plotly** | Charts/graphs | Mana curve, role distribution |
| **Pandas** | Data manipulation | Deck analysis, simulation results |
| **Scryfall API** | Card data | `src/api/scryfall.py` |
| **Archidekt API** | Deck import | `src/api/archidekt.py` |
| **Commander Spellbook** | Combo verification | `src/api/commander_spellbook.py` |
| **Anthropic Claude** | AI recommendations | `src/api/recommendations.py` |

---

## Codebase Architecture

### Directory Structure

```
/home/user/Deck_synergy/
│
├── app.py (3,387 lines)              # MAIN ENTRY: Web dashboard
├── requirements.txt                   # Python dependencies
├── Procfile                           # Heroku deployment config
├── shared_mechanics.py                # Shared detection logic
│
├── src/                               # Modern, organized source code
│   ├── api/                           # External API integrations
│   │   ├── archidekt.py              # Deck import from Archidekt
│   │   ├── scryfall.py               # Card data from Scryfall
│   │   ├── local_cards.py            # Local cache (34K+ cards)
│   │   ├── commander_spellbook.py    # Verified combo database
│   │   └── recommendations.py        # AI-powered suggestions
│   │
│   ├── core/                         # Unified architecture (NEW)
│   │   ├── card_parser.py           # Single source of truth for parsing
│   │   ├── trigger_registry.py      # Centralized trigger management
│   │   ├── trigger_effects.py       # Effect creation utilities
│   │   └── synergy_simulation_bridge.py  # Link synergy ↔ simulation
│   │
│   ├── synergy_engine/               # SYNERGY DETECTION SYSTEM
│   │   ├── analyzer.py              # MAIN ENTRY - orchestrates analysis
│   │   ├── rules.py (~900 lines)    # 69+ synergy detection rules
│   │   ├── combo_detector.py        # Verified combo detection
│   │   ├── three_way_synergies.py   # Multi-card combos
│   │   ├── categories.py            # Synergy categorization/coloring
│   │   └── ... (7 more files)
│   │
│   ├── utils/                        # Mechanic extractors (24 files)
│   │   ├── aristocrats_extractors.py    # Sacrifice/death triggers
│   │   ├── token_extractors.py          # Token generation
│   │   ├── graveyard_extractors.py      # Graveyard mechanics
│   │   ├── ramp_extractors.py           # Mana acceleration
│   │   ├── removal_extractors.py        # Removal spells
│   │   ├── card_advantage_extractors.py # Card draw
│   │   ├── keyword_extractors.py        # Keywords (flying, haste, etc.)
│   │   ├── card_roles.py                # Card categorization
│   │   ├── graph_builder.py             # Build synergy graphs
│   │   └── ... (15 more utilities)
│   │
│   ├── models/                       # Data structures
│   │   ├── deck.py                  # Deck model with methods
│   │   ├── combo.py                 # Combo representation
│   │   └── deck_session.py          # Session management
│   │
│   ├── analysis/                     # Analysis tools
│   │   ├── deck_archetype_detector.py   # Detect deck archetypes
│   │   ├── weakness_detector.py         # Find deck weaknesses
│   │   └── impact_analyzer.py           # Card impact analysis
│   │
│   └── simulation/                   # Simulation wrappers
│       ├── deck_simulator.py        # High-level simulation interface
│       └── mana_simulator.py        # Mana curve analysis
│
├── Simulation/                        # Legacy game simulation engine
│   ├── boardstate.py (194KB)         # CORE: All MTG mechanics
│   ├── simulate_game.py (35KB)       # MAIN LOOP: Game simulation
│   ├── oracle_text_parser.py (27KB)  # Parse card abilities
│   ├── turn_phases.py                # MTG turn structure
│   ├── mtg_abilities.py              # Ability data structures
│   └── tests/ (22 files)             # Comprehensive test coverage
│
├── tests/                             # Synergy engine tests (10 files)
├── scripts/                           # Utility scripts (8 files)
├── data/                              # Card databases
│   └── cards/
│       ├── cards-minimal.json        # 34MB - All MTG cards
│       └── cards-preprocessed.json   # 17MB - Preprocessed with tags
│
├── docs/                              # Comprehensive documentation (56+ files)
│   ├── ARCHITECTURE.md               # System architecture
│   ├── DEVELOPER.md                  # Developer setup
│   ├── SYNERGY_SYSTEM.md             # Synergy detection guide
│   ├── COMBO_DETECTION.md            # Combo finder documentation
│   └── ... (52 more docs)
│
└── assets/                            # CSS and static files
```

### Architectural Patterns

#### Pattern 1: Unified Architecture (Single Source of Truth)
- **File:** `src/core/card_parser.py`
- **Purpose:** Parse each card ONCE, use everywhere
- **Key Insight:** Replaced 14+ separate parsing files with one unified parser

```python
# OLD WAY (deprecated)
from src.utils.token_extractors import extract_token_creation
from src.utils.graveyard_extractors import extract_graveyard_mechanics
# ... 12 more imports

# NEW WAY (unified)
from src.core.card_parser import parse_card_abilities

abilities = parse_card_abilities(card)
# Returns: CardAbilities dataclass with ALL parsed data
```

#### Pattern 2: Rule-Based Synergy Detection
- **File:** `src/synergy_engine/rules.py`
- **Pattern:** Each function = one synergy type
- **Orchestrated by:** `analyzer.py`

```python
def detect_tap_untap_engines(card1, card2, deck_info=None):
    """Detect tap/untap synergies"""
    # Check if card1 taps creatures for value
    # Check if card2 untaps creatures
    # Return synergy if both conditions met
    pass

# Called by analyzer.py for every card pair
```

#### Pattern 3: Extractor Pattern
- **Files:** `src/utils/*_extractors.py` (24 files)
- **Pattern:** One file per mechanic category
- **Returns:** Structured extraction data

```python
# Example: src/utils/token_extractors.py
def extract_token_creation(card):
    """
    Returns:
        {
            'creates_tokens': bool,
            'token_types': List[Dict],
            'creation_type': str,  # 'etb', 'activated', 'triggered'
            ...
        }
    """
```

#### Pattern 4: Callback-Based Dashboard
- **File:** `app.py`
- **Framework:** Dash (declarative callbacks)
- **Pattern:** `@app.callback` decorators for reactive updates

```python
@app.callback(
    Output('synergy-graph', 'elements'),
    Input('load-deck-button', 'n_clicks'),
    State('deck-url-input', 'value')
)
def update_graph(n_clicks, deck_url):
    # Load deck → Analyze synergies → Return graph elements
    pass
```

### Data Flow: Deck Analysis

```
User enters Archidekt URL
  ↓
app.py @callback triggered
  ↓
src/api/archidekt.py: fetch_deck_from_archidekt(url)
  ↓
src/api/scryfall.py OR local_cards.py: get_card_details()
  ↓
src/models/deck.py: create Deck object
  ↓
src/synergy_engine/analyzer.py: analyze_deck_synergies(deck)
  ├─ For each card pair:
  │   ├─ Run 69+ rules from rules.py
  │   ├─ Calculate synergy strength (1.0 - 50.0)
  │   └─ Categorize synergy type
  ├─ Detect three-way synergies
  └─ Query Commander Spellbook for verified combos
  ↓
src/utils/graph_builder.py: build_cytoscape_graph(deck)
  ↓
app.py: render dashboard with graph + metrics
```

---

## Development Workflows

### Workflow 1: Adding a New Synergy Type

**Example:** Adding "Energy counter synergies"

1. **Create Extractor** (if needed)
   ```bash
   # File: src/utils/energy_extractors.py
   ```
   - Add functions: `extract_produces_energy()`, `extract_uses_energy()`
   - Follow existing extractor patterns (see `token_extractors.py`)

2. **Add Detection Rule**
   ```bash
   # File: src/synergy_engine/rules.py
   ```
   - Add function: `detect_energy_synergies(card1, card2, deck_info=None)`
   - Import your extractors
   - Return synergy dict with `name`, `category`, `strength`, `description`

3. **Add to Rule Registry**
   ```python
   # In rules.py, add to ALL_RULES list:
   ALL_RULES = [
       detect_tap_untap_engines,
       detect_tribal_synergies,
       # ... existing rules
       detect_energy_synergies,  # ADD HERE
   ]
   ```

4. **Add Category (if new)**
   ```bash
   # File: src/synergy_engine/categories.py
   ```
   - Add to `CATEGORY_COLORS` dict
   - Add to `CATEGORY_DISPLAY_NAMES` dict

5. **Test**
   ```bash
   pytest tests/test_synergy_rules.py -v
   ```

**See:** `CONTRIBUTING_FOR_AI.md` Section 1 for detailed code examples

### Workflow 2: Adding a New Dashboard Feature

**Example:** Adding a "Mana Curve" chart

1. **Add Layout Component**
   ```python
   # In app.py, find the layout = html.Div([...]) section
   # Add your new component:
   dcc.Graph(id='mana-curve-chart')
   ```

2. **Create Callback**
   ```python
   @app.callback(
       Output('mana-curve-chart', 'figure'),
       Input('deck-store', 'data')
   )
   def update_mana_curve(deck_data):
       if not deck_data:
           return {}

       # Process deck_data
       # Create Plotly figure
       fig = go.Figure(...)
       return fig
   ```

3. **Test Interactively**
   ```bash
   python app.py
   # Visit http://localhost:8050 and test
   ```

### Workflow 3: Adding a New Simulation Mechanic

**Example:** Adding "Cascade" keyword support

1. **Add to Unified Parser**
   ```bash
   # File: src/core/card_parser.py
   ```
   - Add cascade detection to `parse_keywords()` or appropriate section
   - Update `CardAbilities` dataclass if needed

2. **Implement Game Mechanic**
   ```bash
   # File: Simulation/boardstate.py
   ```
   - Add method: `def resolve_cascade(self, card, ...)`
   - Hook into appropriate trigger point (cast, ETB, etc.)

3. **Add Tests**
   ```bash
   # File: Simulation/tests/test_cascade.py
   ```
   - Test basic cascade
   - Test edge cases (empty library, all cards too expensive, etc.)

4. **Run Simulation Tests**
   ```bash
   pytest Simulation/tests/test_cascade.py -v
   ```

### Workflow 4: Debugging a Synergy Issue

**User reports:** "Card X and Card Y should synergize but don't show up"

1. **Verify Cards Loaded**
   ```python
   # In app.py or a test script:
   from src.api.local_cards import get_card_by_name
   card1 = get_card_by_name("Card X")
   card2 = get_card_by_name("Card Y")
   print(card1['oracle_text'])
   print(card2['oracle_text'])
   ```

2. **Test Extractors**
   ```python
   from src.utils.token_extractors import extract_token_creation
   result = extract_token_creation(card1)
   print(result)  # Does it detect the expected mechanic?
   ```

3. **Test Synergy Rules**
   ```python
   from src.synergy_engine.rules import detect_token_synergies
   synergies = detect_token_synergies(card1, card2)
   print(synergies)  # Does the rule fire?
   ```

4. **Check Rule Registry**
   ```python
   from src.synergy_engine.rules import ALL_RULES
   print([rule.__name__ for rule in ALL_RULES])
   # Is your rule in the list?
   ```

5. **Fix and Test**
   - Fix the extractor or rule
   - Add a test case to prevent regression
   - Run: `pytest tests/ -v`

---

## Git Conventions

### Branch Naming

**Pattern:** `claude/<description>-<session-id>`

**Examples:**
- `claude/add-energy-synergies-01UGVtp4M5X2yL2g`
- `claude/fix-token-detection-01sPRcn2psqhSU8d`
- `claude/review-project-documentation-01UGVtp4M5X2yL2g`

**CRITICAL:**
- Branch MUST start with `claude/`
- Branch MUST end with matching session ID
- Otherwise `git push` will fail with 403 HTTP error

### Commit Messages

**Style:** Conventional Commits format

```
<type>: <description>

<optional body>

<optional footer>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding/updating tests
- `chore:` - Maintenance tasks

**Examples:**
```
feat: Add energy counter synergy detection

- Created energy_extractors.py with produces/uses energy detection
- Added detect_energy_synergies rule to rules.py
- Added 'energy' category to categories.py
- Tested with Kaladesh energy deck

Closes #123
```

```
fix: Correct token type detection for Food tokens

Food tokens were incorrectly categorized as Treasure tokens.
Updated token_extractors.py regex pattern.

Fixes #456
```

**Best Practices:**
- Focus on WHY, not just WHAT
- Keep subject line under 72 characters
- Use imperative mood ("Add feature" not "Added feature")
- Reference issue numbers when applicable

### Pull Request Workflow

**Creating a PR:**

```bash
# 1. Ensure you're on the correct branch
git branch
# Should show: claude/your-feature-<session-id>

# 2. Commit your changes
git add .
git commit -m "$(cat <<'EOF'
feat: Add energy counter synergy detection

- Created energy_extractors.py
- Added detection rules
- Added tests
EOF
)"

# 3. Push to remote (CRITICAL: use -u flag for new branches)
git push -u origin claude/your-feature-<session-id>

# 4. Create PR using GitHub CLI (if available) or web interface
gh pr create --title "Add energy counter synergy detection" --body "$(cat <<'EOF'
## Summary
- Implements energy counter synergy detection
- Adds comprehensive tests
- Updates documentation

## Test Plan
- [x] Run pytest tests/
- [x] Test with Kaladesh energy deck
- [x] Verify UI displays energy synergies correctly
EOF
)"
```

**PR Best Practices:**
- Include summary of changes
- List what was tested
- Reference related issues
- Add screenshots for UI changes

### Git Safety Protocol

**NEVER:**
- Update git config
- Run destructive commands (`push --force`, `hard reset`)
- Skip hooks (`--no-verify`, `--no-gpg-sign`)
- Force push to main/master
- Commit without explicit user request

**ALWAYS:**
- Use `git push -u origin <branch-name>` for first push
- Retry network failures up to 4 times with exponential backoff (2s, 4s, 8s, 16s)
- Check authorship before amending commits
- Verify status after commits

---

## Coding Conventions

### Python Style

**Standard:** PEP 8 with type hints (PEP 484)

**Type Hints:** REQUIRED for all new functions

```python
# GOOD
def analyze_card_pair(card1: Dict, card2: Dict, deck_info: Optional[Dict] = None) -> List[Dict]:
    """Analyze synergies between two cards."""
    pass

# BAD (no type hints)
def analyze_card_pair(card1, card2, deck_info=None):
    pass
```

**Docstrings:** Google-style format

```python
def extract_token_creation(card: Dict) -> Dict:
    """Extract token creation mechanics from a card.

    Args:
        card: Card dictionary from Scryfall with oracle_text, type_line, etc.

    Returns:
        Dictionary containing:
            - creates_tokens (bool): Whether card creates tokens
            - token_types (List[Dict]): List of token type dicts
            - creation_type (str): 'etb', 'activated', or 'triggered'
            - count (int): Number of tokens created

    Example:
        >>> card = {'oracle_text': 'When ~ enters, create two 1/1 Goblin tokens'}
        >>> extract_token_creation(card)
        {
            'creates_tokens': True,
            'token_types': [{'power': 1, 'toughness': 1, 'types': ['Goblin']}],
            'creation_type': 'etb',
            'count': 2
        }
    """
    pass
```

### Error Handling

**Pattern:** Graceful degradation, don't crash

```python
# GOOD
try:
    from .combo_detector import detect_combos
    COMBO_DETECTION_ENABLED = True
except ImportError:
    COMBO_DETECTION_ENABLED = False
    print("Warning: Combo detection not available")

# Continue execution despite errors in individual rules
for rule_func in ALL_RULES:
    try:
        synergies = rule_func(card1, card2)
        all_synergies.extend(synergies)
    except Exception as e:
        print(f"Error in {rule_func.__name__}: {e}")
        # Continue with next rule
        continue
```

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| **Functions** | Verb-first, snake_case | `extract_token_creation()`, `detect_tribal_synergies()` |
| **Classes** | PascalCase | `DeckAnalyzer`, `CardAbilities` |
| **Variables** | snake_case | `oracle_text`, `synergy_score` |
| **Constants** | UPPER_SNAKE_CASE | `MAX_SYNERGY_SCORE`, `CATEGORY_COLORS` |
| **Private** | Leading underscore | `_internal_helper()`, `_cache` |

**Verb Patterns:**
- Extraction: `extract_*` (e.g., `extract_graveyard_mechanics`)
- Detection: `detect_*` (e.g., `detect_aristocrat_synergies`)
- Building: `build_*` (e.g., `build_synergy_graph`)
- Analysis: `analyze_*` (e.g., `analyze_deck_composition`)
- Parsing: `parse_*` (e.g., `parse_card_abilities`)

### Data Structure Conventions

**Card Dictionary (from Scryfall/local cache):**
```python
{
    'name': str,              # Card name
    'oracle_text': str,       # Rules text
    'type_line': str,         # e.g., "Legendary Creature — Human Wizard"
    'colors': List[str],      # ['W', 'U', 'B', 'R', 'G']
    'mana_cost': str,         # e.g., "{2}{G}{W}"
    'cmc': int,               # Converted mana cost
    'power': str,             # Creature power (or None)
    'toughness': str,         # Creature toughness (or None)
    'keywords': List[str],    # ['Flying', 'Haste', ...]
    'is_commander': bool,     # True for deck's commander
    'scryfall_id': str,       # Unique Scryfall UUID
    'image_uris': Dict,       # Image URLs
    ...
}
```

**Synergy Dictionary (returned by rules):**
```python
{
    'name': str,              # Synergy name (e.g., "Token Generation & Sacrifice Outlet")
    'category': str,          # Main category (e.g., 'tokens', 'aristocrats', 'ramp')
    'subcategory': str,       # Optional subcategory
    'strength': float,        # 1.0 to 50.0 (50.0 = infinite combo)
    'description': str,       # Human-readable explanation
    'target_cards': List[str],# Card names involved (for 3+ card synergies)
    'combo': bool,            # True if this is an infinite combo
    'combo_id': str,          # Commander Spellbook ID (if verified combo)
}
```

**Strength Scale:**
- `50.0` - Infinite combo
- `30.0` - Very powerful synergy (engine pieces)
- `10.0` - Strong synergy
- `5.0` - Good synergy
- `1.0` - Mild synergy

### Import Organization

**Order:**
1. Standard library
2. Third-party packages
3. Local imports

```python
# Standard library
import re
import json
from typing import Dict, List, Optional

# Third-party
import pandas as pd
import numpy as np
from dash import dcc, html

# Local
from src.utils.token_extractors import extract_token_creation
from src.models.deck import Deck
```

### File Organization

**Standard file structure:**
```python
"""Module docstring explaining purpose."""

# Imports
import ...

# Constants
MAX_SYNERGY_SCORE = 50.0

# Helper functions (private)
def _internal_helper():
    pass

# Public functions (exported)
def public_function():
    pass

# Main execution (if script)
if __name__ == "__main__":
    pass
```

---

## Common Tasks

### Task 1: Find Where a Specific Card Interaction is Detected

**Question:** "Where is the code that detects Skullclamp + creature tokens synergy?"

**Steps:**
1. Identify the mechanic types: Equipment + Tokens + Sacrifice
2. Check extractors:
   ```bash
   # Look in:
   src/utils/equipment_extractors.py
   src/utils/token_extractors.py
   src/utils/aristocrats_extractors.py
   ```
3. Check synergy rules:
   ```bash
   # Search in:
   src/synergy_engine/rules.py

   # Look for functions like:
   # - detect_equipment_synergies()
   # - detect_aristocrat_synergies()
   ```

### Task 2: Add a New Card to Test With

**Steps:**
1. Find card on Scryfall: `https://scryfall.com/search?q=cardname`
2. Add to test deck in your test file:
   ```python
   test_cards = [
       {
           'name': 'Skullclamp',
           'oracle_text': 'Equipped creature gets +1/-1.\nWhenever equipped creature dies, draw two cards.',
           'type_line': 'Artifact — Equipment',
           'cmc': 1,
           'keywords': [],
       },
       # ... more cards
   ]
   ```
3. Or use API:
   ```python
   from src.api.scryfall import get_card_by_name
   skullclamp = get_card_by_name("Skullclamp")
   ```

### Task 3: Debug Why a Synergy Isn't Showing Up

**Checklist:**
1. ✓ Are both cards in the deck?
2. ✓ Are the extractors working?
   ```python
   from src.utils.token_extractors import extract_token_creation
   print(extract_token_creation(card))
   ```
3. ✓ Is the rule firing?
   ```python
   from src.synergy_engine.rules import detect_token_synergies
   print(detect_token_synergies(card1, card2))
   ```
4. ✓ Is the rule registered?
   ```python
   from src.synergy_engine.rules import ALL_RULES
   print([r.__name__ for r in ALL_RULES])
   ```
5. ✓ Is the synergy strength above threshold?
   - Default threshold: 1.0
   - Check in dashboard UI settings

### Task 4: Update Card Database

**When:** New MTG set released, card data outdated

**Steps:**
```bash
# 1. Update cards-minimal.json from Scryfall
python scripts/create_minimal_cards.py

# 2. Regenerate preprocessed database (with tags)
python scripts/create_preprocessed_cards.py

# 3. Verify
python scripts/verify_and_filter_cards.py

# 4. Test
python app.py
# Load a deck with new cards
```

### Task 5: Profile Performance

**Find slow code:**
```python
import cProfile
import pstats

from src.synergy_engine.analyzer import analyze_deck_synergies
from src.api.archidekt import fetch_deck_from_archidekt

# Load deck
deck = fetch_deck_from_archidekt("https://archidekt.com/decks/...")

# Profile
profiler = cProfile.Profile()
profiler.enable()
synergies = analyze_deck_synergies(deck)
profiler.disable()

# Print stats
stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(20)  # Top 20 slowest functions
```

### Task 6: Add a New API Integration

**Example:** Integrate with EDHREC API

**Steps:**
1. Create API module:
   ```bash
   # File: src/api/edhrec.py
   ```
2. Implement functions:
   ```python
   import requests

   def get_top_cards_for_commander(commander_name: str) -> List[Dict]:
       """Fetch top cards for a commander from EDHREC."""
       url = f"https://edhrec-json.s3.amazonaws.com/en/commanders/{commander_name}.json"
       response = requests.get(url)
       # ... process response
       return cards
   ```
3. Add to recommendations:
   ```python
   # In src/api/recommendations.py
   from .edhrec import get_top_cards_for_commander

   def get_recommendations(deck):
       edhrec_recs = get_top_cards_for_commander(deck.commander)
       # ... merge with existing recommendations
   ```
4. Test:
   ```python
   pytest tests/test_edhrec_integration.py -v
   ```

---

## Testing Guidelines

### Test Organization

**Structure:**
```
tests/                          # Synergy engine tests
├── test_synergy_rules.py      # Main synergy rule tests
├── test_extractors.py          # Extractor tests
├── test_graph_builder.py       # Graph generation tests
└── ...

Simulation/tests/               # Simulation engine tests
├── test_boardstate.py          # Game mechanic tests
├── test_landfall.py            # Landfall mechanic
├── test_sacrifice.py           # Sacrifice mechanics
└── ...
```

### Writing Tests

**Pattern:** Arrange, Act, Assert

```python
import pytest
from src.synergy_engine.rules import detect_token_synergies

def test_token_sacrifice_synergy():
    """Test that token generators synergize with sacrifice outlets."""

    # Arrange
    token_generator = {
        'name': 'Krenko, Mob Boss',
        'oracle_text': '{T}: Create X 1/1 red Goblin creature tokens, where X is the number of Goblins you control.',
        'type_line': 'Legendary Creature — Goblin Warrior',
    }

    sacrifice_outlet = {
        'name': 'Ashnod\'s Altar',
        'oracle_text': 'Sacrifice a creature: Add {C}{C}.',
        'type_line': 'Artifact',
    }

    # Act
    synergies = detect_token_synergies(token_generator, sacrifice_outlet)

    # Assert
    assert len(synergies) > 0, "Should detect token + sacrifice synergy"
    assert synergies[0]['category'] == 'tokens', "Should be categorized as tokens"
    assert synergies[0]['strength'] >= 5.0, "Should be strong synergy"
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_synergy_rules.py

# Specific test function
pytest tests/test_synergy_rules.py::test_token_sacrifice_synergy

# With verbose output
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Only synergy tests
pytest tests/

# Only simulation tests
pytest Simulation/tests/

# Failed tests only
pytest --lf
```

### Test Coverage Goals

**Target:** 80%+ coverage for new code

**Priority:**
1. **Critical:** Synergy detection rules (90%+ coverage)
2. **High:** Extractors (80%+ coverage)
3. **Medium:** API integrations (60%+ coverage)
4. **Low:** UI callbacks (manual testing)

### Mock Data

**Use real card data when possible:**
```python
# GOOD - Real card data
from src.api.scryfall import get_card_by_name
card = get_card_by_name("Skullclamp")

# ACCEPTABLE - Minimal mock for unit tests
card = {
    'name': 'Test Card',
    'oracle_text': 'Draw a card.',
    'type_line': 'Instant',
}
```

### Regression Tests

**When:** Bug fixed → Add test to prevent regression

```python
def test_regression_issue_123_food_tokens():
    """Regression test for issue #123: Food tokens misidentified as Treasure."""

    food_creator = {
        'name': 'Gilded Goose',
        'oracle_text': 'When Gilded Goose enters the battlefield, create a Food token.',
    }

    result = extract_token_creation(food_creator)

    assert result['token_types'][0]['name'] == 'Food', "Should detect Food, not Treasure"
```

---

## Critical Files Reference

### Most Important Files (START HERE)

| File | Lines | Purpose | Modify When... |
|------|-------|---------|----------------|
| `app.py` | 3,387 | **Main web dashboard** | Adding UI features, callbacks, layout changes |
| `src/synergy_engine/analyzer.py` | ~500 | **Synergy orchestrator** | Changing analysis pipeline, adding global features |
| `src/synergy_engine/rules.py` | ~900 | **69+ synergy rules** | Adding new synergy types |
| `Simulation/boardstate.py` | ~4,800 | **ALL MTG mechanics** | Adding game mechanics for simulation |
| `Simulation/simulate_game.py` | ~900 | **Game loop** | Changing simulation behavior |

### Configuration Files

| File | Purpose | Modify When... |
|------|---------|----------------|
| `requirements.txt` | Python dependencies | Adding new packages |
| `Procfile` | Heroku deployment | Changing deployment config |
| `.gitignore` | Git exclusions | Adding new file types to ignore |
| `.python-version` | Python version | Upgrading Python version |

### Data Files (DO NOT MODIFY MANUALLY)

| File | Size | Purpose | Generate With... |
|------|------|---------|-----------------|
| `data/cards/cards-minimal.json` | 34MB | All MTG cards | `python scripts/create_minimal_cards.py` |
| `data/cards/cards-preprocessed.json` | 17MB | Preprocessed with tags | `python scripts/create_preprocessed_cards.py` |

### Documentation Files (READ THESE)

| File | Purpose | Read When... |
|------|---------|--------------|
| `README.md` | Project overview | First time working on project |
| `AI_GUIDE_FOR_MODELS.md` | Comprehensive AI guide | Understanding navigation and architecture |
| `PROJECT_MAP.md` | Quick file lookup | Finding specific files |
| `CONTRIBUTING_FOR_AI.md` | Feature tutorials | Adding new features |
| `docs/ARCHITECTURE.md` | System architecture | Understanding overall design |
| `docs/SYNERGY_SYSTEM.md` | Synergy detection guide | Working on synergy detection |
| `docs/COMBO_DETECTION.md` | Combo system | Working on combo features |

---

## Dos and Don'ts

### DO ✓

1. **DO** read existing code patterns before adding new code
2. **DO** add type hints to all new functions
3. **DO** write docstrings for all public functions
4. **DO** add tests for new features
5. **DO** handle errors gracefully (try/except with logging)
6. **DO** use the unified parser (`src/core/card_parser.py`) for new mechanics
7. **DO** follow the extractor pattern for new mechanic detection
8. **DO** add your rule to the `ALL_RULES` registry
9. **DO** use meaningful variable names (even if longer)
10. **DO** commit frequently with clear messages
11. **DO** test with real MTG decks from Archidekt
12. **DO** check existing extractors before creating new ones
13. **DO** use caching for expensive operations
14. **DO** profile performance for slow operations
15. **DO** ask questions if MTG rules are unclear

### DON'T ✗

1. **DON'T** modify card database files manually
2. **DON'T** skip type hints on new functions
3. **DON'T** create duplicate extractors (check `src/utils/` first)
4. **DON'T** add rules without testing with real decks
5. **DON'T** commit without testing (`pytest`)
6. **DON'T** use global variables (use function parameters)
7. **DON'T** hard-code card names in rules (use pattern matching)
8. **DON'T** forget to add new rules to `ALL_RULES` registry
9. **DON'T** use `print()` for logging (use `logging` module or graceful errors)
10. **DON'T** create circular imports
11. **DON'T** modify `Simulation/boardstate.py` unless necessary (large file, complex)
12. **DON'T** force push to branches
13. **DON'T** commit secrets or API keys
14. **DON'T** break backward compatibility without discussion
15. **DON'T** assume MTG rules (check gatherer.wizards.com)

### Performance Best Practices

**DO:**
- Cache regex patterns (`re.compile()` outside functions)
- Use sets for membership testing (not lists)
- Batch API requests when possible
- Use local card cache instead of API calls
- Profile before optimizing (don't guess)

**DON'T:**
- Call APIs in loops
- Re-parse cards multiple times
- Create regex patterns in tight loops
- Load full card database if you only need a few cards

### Security Best Practices

**DO:**
- Validate user inputs (URLs, deck lists)
- Use environment variables for API keys
- Sanitize data before displaying in UI
- Handle API rate limits gracefully

**DON'T:**
- Commit API keys or secrets
- Trust user input without validation
- Execute arbitrary code from card text
- Expose internal paths in error messages

---

## Appendix: Quick Reference

### File Path Cheat Sheet

```bash
# Main entry points
/home/user/Deck_synergy/app.py
/home/user/Deck_synergy/src/synergy_engine/analyzer.py
/home/user/Deck_synergy/Simulation/simulate_game.py

# Synergy detection
/home/user/Deck_synergy/src/synergy_engine/rules.py
/home/user/Deck_synergy/src/synergy_engine/categories.py

# Extractors
/home/user/Deck_synergy/src/utils/token_extractors.py
/home/user/Deck_synergy/src/utils/graveyard_extractors.py
/home/user/Deck_synergy/src/utils/aristocrats_extractors.py

# APIs
/home/user/Deck_synergy/src/api/scryfall.py
/home/user/Deck_synergy/src/api/archidekt.py
/home/user/Deck_synergy/src/api/commander_spellbook.py

# Data
/home/user/Deck_synergy/data/cards/cards-minimal.json
/home/user/Deck_synergy/data/cards/cards-preprocessed.json

# Tests
/home/user/Deck_synergy/tests/
/home/user/Deck_synergy/Simulation/tests/

# Documentation
/home/user/Deck_synergy/README.md
/home/user/Deck_synergy/AI_GUIDE_FOR_MODELS.md
/home/user/Deck_synergy/docs/ARCHITECTURE.md
```

### Command Cheat Sheet

```bash
# Run dashboard
python app.py

# Run all tests
pytest

# Run specific test file
pytest tests/test_synergy_rules.py -v

# Run simulation tests
pytest Simulation/tests/ -v

# Update card database
python scripts/create_minimal_cards.py
python scripts/create_preprocessed_cards.py

# Generate embeddings (if using ML features)
python scripts/generate_embeddings.py

# Profile performance
python -m cProfile -o output.prof app.py

# Git workflow
git status
git add .
git commit -m "feat: Add new feature"
git push -u origin claude/branch-name-<session-id>
```

### Common Patterns

**Detect a mechanic:**
```python
def extract_mechanic(card: Dict) -> Dict:
    oracle_text = card.get('oracle_text', '').lower()

    if re.search(r'pattern', oracle_text):
        return {'has_mechanic': True, ...}

    return {'has_mechanic': False}
```

**Add a synergy rule:**
```python
def detect_my_synergy(card1: Dict, card2: Dict, deck_info: Optional[Dict] = None) -> List[Dict]:
    synergies = []

    # Check if cards interact
    if condition_met(card1, card2):
        synergies.append({
            'name': 'Synergy Name',
            'category': 'category',
            'strength': 5.0,
            'description': 'Why they synergize',
        })

    return synergies
```

**Add a dashboard callback:**
```python
@app.callback(
    Output('component-id', 'property'),
    Input('trigger-id', 'n_clicks'),
    State('data-id', 'data')
)
def update_component(n_clicks, data):
    if not n_clicks or not data:
        return default_value

    # Process data
    result = process(data)

    return result
```

---

## Final Notes

### Getting Help

1. **Check documentation first:**
   - `AI_GUIDE_FOR_MODELS.md` - Comprehensive guide
   - `PROJECT_MAP.md` - Quick lookup
   - `CONTRIBUTING_FOR_AI.md` - How-to tutorials

2. **Search codebase:**
   - Use `grep` to find similar patterns
   - Check `src/synergy_engine/rules.py` for examples
   - Look at `src/utils/` for extractor patterns

3. **Test with real data:**
   - Load a deck from Archidekt
   - Use `pytest` to run existing tests
   - Add print statements to debug

4. **Reference MTG rules:**
   - Gatherer: https://gatherer.wizards.com/
   - Comprehensive Rules: https://magic.wizards.com/en/rules
   - MTG Wiki: https://mtg.fandom.com/

### Project Philosophy

1. **Accuracy over speed** - Correct synergy detection is more important than performance
2. **Graceful degradation** - Don't crash on errors, log and continue
3. **Extensibility** - Make it easy to add new synergies and mechanics
4. **User-friendly** - Dashboard should be intuitive and informative
5. **Well-documented** - Code should be self-explanatory with good docs

### Common Pitfalls

1. **Forgetting to register rules** - Add to `ALL_RULES` in `rules.py`
2. **Over-matching extractors** - Be specific in regex patterns
3. **Circular imports** - Keep imports clean and unidirectional
4. **Not testing with real decks** - Synthetic tests miss edge cases
5. **Ignoring performance** - Cache and optimize hot paths

---

**Last Updated:** 2025-11-16
**Version:** 2.0
**Maintained by:** AI-assisted development team

**Questions or issues?** Check the GitHub Issues or Discussions.

---

*Happy coding! May your synergies be strong and your combos infinite!* ⚡🃏
