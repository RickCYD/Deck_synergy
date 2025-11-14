# 🤖 AI Model Guide - MTG Deck Synergy Analyzer

**Purpose:** This guide helps AI models quickly understand and navigate the MTG Deck Synergy Analyzer project to make effective contributions.

---

## 📋 Quick Navigation

**Jump to:**
- [Project Overview](#project-overview)
- [File Responsibilities](#file-responsibilities)
- [Adding New Features](#adding-new-features)
- [MTG Rules Location](#mtg-rules-location)
- [Common Tasks](#common-tasks)
- [Architecture Patterns](#architecture-patterns)

---

## Project Overview

This is a **Python-based MTG Commander deck analyzer** with three main components:

1. **Synergy Analysis Engine** - Detects 69+ types of card interactions
2. **Game Simulation Engine** - Runs goldfish simulations to calculate deck power
3. **Web Dashboard** - Interactive Dash/Flask app with graph visualization

**Technology Stack:**
- **Backend:** Python 3.x, Flask, Dash
- **Frontend:** Dash, Cytoscape (graph visualization), Plotly
- **Data:** Scryfall API, Commander Spellbook API
- **ML:** Anthropic Claude API (optional recommendations)

---

## File Responsibilities

### 🎯 Entry Points (Start Here)

| File | Purpose | When to Use |
|------|---------|-------------|
| `app.py` (3,387 lines) | **Main dashboard application** | Modifying UI, adding dashboard features, callbacks |
| `src/synergy_engine/analyzer.py` | **Synergy analysis orchestrator** | Adding synergy detection features |
| `Simulation/simulate_game.py` | **Game simulation main loop** | Modifying simulation behavior |
| `Simulation/boardstate.py` (194KB) | **Core MTG game mechanics** | Adding new game rules/mechanics |

### 📁 Directory Structure

```
/home/user/Deck_synergy/
│
├── app.py                          # Main Dash web application (START HERE for UI)
├── requirements.txt                # Python dependencies
├── shared_mechanics.py             # Shared detection logic for consistency
│
├── src/                            # Modern, well-organized source code
│   ├── api/                        # External API integrations
│   │   ├── archidekt.py            # Import decks from Archidekt
│   │   ├── scryfall.py             # Fetch card data from Scryfall
│   │   ├── local_cards.py          # Local card cache (34,000+ cards)
│   │   ├── commander_spellbook.py  # Verified combo database
│   │   └── recommendations.py      # AI-powered card suggestions
│   │
│   ├── synergy_engine/             # Core synergy detection (START HERE for synergies)
│   │   ├── analyzer.py             # MAIN ENTRY POINT - orchestrates analysis
│   │   ├── rules.py                # 69+ synergy detection rules
│   │   ├── combo_detector.py       # Verified combo detection
│   │   ├── card_advantage_synergies.py  # Draw/tutor synergies
│   │   ├── recursion_synergies.py  # Graveyard recursion
│   │   ├── three_way_synergies.py  # Multi-card combos
│   │   ├── categories.py           # Synergy categorization
│   │   ├── embedding_analyzer.py   # ML-based analysis (optional)
│   │   ├── incremental_analyzer.py # Performance optimization
│   │   └── regex_cache.py          # Caching for speed
│   │
│   ├── utils/                      # Extractors for card mechanics (START HERE for new mechanics)
│   │   ├── aristocrats_extractors.py    # Sacrifice/death triggers
│   │   ├── token_extractors.py          # Token generation
│   │   ├── graveyard_extractors.py      # Graveyard interactions
│   │   ├── ramp_extractors.py           # Mana acceleration
│   │   ├── removal_extractors.py        # Removal spells
│   │   ├── boardwipe_extractors.py      # Board wipes
│   │   ├── keyword_extractors.py        # Keywords (flying, haste, etc.)
│   │   ├── damage_extractors.py         # Damage effects
│   │   ├── card_advantage_extractors.py # Card draw
│   │   ├── protection_extractors.py     # Protection effects
│   │   ├── combat_extractors.py         # Combat mechanics
│   │   ├── recursion_extractors.py      # Recursion mechanics
│   │   ├── card_roles.py                # Categorize cards by function
│   │   └── graph_builder.py             # Build synergy graphs
│   │
│   ├── models/                     # Data structures
│   │   ├── deck.py                 # Deck data model
│   │   ├── combo.py                # Combo data model
│   │   └── deck_session.py         # Session management
│   │
│   ├── analysis/                   # Analysis tools
│   │   ├── weakness_detector.py    # Find deck weaknesses
│   │   ├── impact_analyzer.py      # Card impact analysis
│   │   └── replacement_analyzer.py # Suggest replacements
│   │
│   └── simulation/                 # Simulation wrappers (bridge to legacy code)
│       ├── deck_simulator.py       # Integration wrapper
│       └── mana_simulator.py       # Mana curve analysis
│
├── Simulation/                     # Legacy game simulation engine (START HERE for game rules)
│   ├── boardstate.py (194KB)       # CORE GAME MECHANICS - ALL MTG RULES
│   ├── simulate_game.py (35KB)     # MAIN GAME LOOP - turn phases, decisions
│   ├── oracle_text_parser.py (27KB)# Parse card abilities from text
│   ├── deck_loader.py              # Load decks from various formats
│   ├── run_simulation.py           # Batch simulation runner
│   ├── statistical_analysis.py     # Stats & metrics
│   ├── turn_phases.py              # Turn phase logic
│   ├── mtg_abilities.py            # Ability data structures
│   ├── Creature.py                 # Creature class
│   ├── draw_starting_hand.py       # Starting hand logic
│   ├── compare_decks.py            # Deck comparison
│   └── tests/                      # 22 test files for simulation
│
├── tests/                          # Synergy engine tests (10 files)
├── scripts/                        # Utility scripts (data preprocessing, etc.)
├── data/                           # Card databases (34MB+ of MTG card data)
├── docs/                           # Documentation (56+ files)
└── assets/                         # CSS/styling
```

---

## Adding New Features

### ✅ Feature Type Decision Tree

```
What do you want to add?
│
├─ New Card Mechanic Detection (e.g., "Foretell", "Amass")
│  └─> Add to: src/utils/keyword_extractors.py or create new extractor
│
├─ New Synergy Type (e.g., "Energy synergies")
│  └─> 1. Add extractor in src/utils/
│     2. Add synergy rule in src/synergy_engine/rules.py
│     3. Add category in src/synergy_engine/categories.py
│
├─ New Simulation Mechanic (e.g., "Day/Night", "Dungeons")
│  └─> Add to: Simulation/boardstate.py (for game state)
│     └─> Add parsing in: Simulation/oracle_text_parser.py
│
├─ New Dashboard Feature (e.g., "Export to CSV")
│  └─> Add to: app.py (callbacks and layout)
│
├─ New Analysis Tool (e.g., "Mana base analyzer")
│  └─> Create in: src/analysis/ directory
│
└─ New API Integration (e.g., "EDHREC recommendations")
   └─> Create in: src/api/ directory
```

---

## 🏗️ **IMPORTANT: Unified Architecture (NEW!)**

**⚠️ READ THIS FIRST before adding mechanics or parsing oracle text!**

As of Part 5 completion, this project has a **unified architecture** for card parsing, trigger execution, and synergy detection. This is the **RECOMMENDED** approach for all new development.

### 🎯 What is the Unified Architecture?

A comprehensive system that:
1. **Parses cards once** - Single source of truth (`src/core/card_parser.py`)
2. **Registers triggers** - Central trigger management (`src/core/trigger_registry.py`)
3. **Executes effects** - Rally, prowess, tokens all work (`Simulation/boardstate_extensions.py`)
4. **Detects synergies** - Using parsed abilities (`src/core/synergy_simulation_bridge.py`)

### 📖 Complete Guides:

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **`UNIFIED_ARCHITECTURE_GUIDE.md`** | Complete architecture overview | Understanding the system |
| **`ADDING_NEW_MECHANICS_CHECKLIST.md`** | Step-by-step guide | Adding new MTG mechanics |
| **`IMPLEMENTATION_PROGRESS.md`** | Implementation details | Technical reference |
| **`tests/test_end_to_end_unified_system.py`** | Working example | See it in action |

### ✅ Use Unified Architecture For:

- Adding NEW mechanics (Landfall, Cascade, Storm, etc.)
- Parsing oracle text for triggers or abilities
- Synergy detection that involves triggers
- Making triggers execute in simulation
- Anything that needs consistent card data

### Example: Before vs After

**Before (OLD way - DON'T do this):**
```python
# Creating new extractor file ❌
src/utils/landfall_extractors.py

def extract_landfall_triggers(card):
    text = card.get('oracle_text', '')
    if 'landfall' in text.lower():
        return True
    return False
```

**After (NEW way - DO this):**
```python
# Add to unified parser ✅
src/core/card_parser.py

class UnifiedCardParser:
    def _parse_landfall_triggers(self, text, type_line):
        """Parse landfall triggers."""
        # Returns TriggerAbility objects
        # Automatically works in synergies AND simulation
```

### 🚀 Quick Start:

1. **Read** `UNIFIED_ARCHITECTURE_GUIDE.md` (5-10 min overview)
2. **Follow** `ADDING_NEW_MECHANICS_CHECKLIST.md` (step-by-step)
3. **Test** using patterns from `tests/test_end_to_end_unified_system.py`

---

### 📝 Step-by-Step: Adding a New Synergy Type (Legacy)

**Example: Adding "Equipment Synergies"**

1. **Create Extractor** (`src/utils/equipment_extractors.py`):
   ```python
   import re

   def extract_equipment_matters(card):
       """Detect if a card cares about Equipment"""
       text = card.get('oracle_text', '').lower()

       patterns = [
           r'whenever.*equipped',
           r'equipment.*you control',
           r'attach.*equipment',
       ]

       for pattern in patterns:
           if re.search(pattern, text):
               return True
       return False
   ```

2. **Add Synergy Rule** (`src/synergy_engine/rules.py`):
   ```python
   from src.utils.equipment_extractors import extract_equipment_matters

   def detect_equipment_synergy(card1, card2):
       """Detect equipment synergies"""
       synergies = []

       # Check if one creates equipment and other cares
       if card1.get('type_line', '').lower().contains('equipment'):
           if extract_equipment_matters(card2):
               synergies.append({
                   'type': 'equipment_synergy',
                   'reason': f"{card2['name']} benefits from equipment like {card1['name']}",
                   'strength': 0.6
               })

       return synergies
   ```

3. **Add Category** (`src/synergy_engine/categories.py`):
   ```python
   SYNERGY_CATEGORIES = {
       # ... existing categories ...
       'equipment_synergy': {
           'label': 'Equipment Synergy',
           'color': '#8B4513',
           'description': 'Cards that interact with Equipment'
       }
   }
   ```

4. **Register Rule** (`src/synergy_engine/analyzer.py`):
   ```python
   from src.synergy_engine.rules import detect_equipment_synergy

   # Add to rule list in analyze_deck()
   synergy_rules = [
       # ... existing rules ...
       detect_equipment_synergy,
   ]
   ```

5. **Test**: Create `tests/test_equipment_synergies.py`

### 📝 Step-by-Step: Adding a New Game Mechanic to Simulation

**Example: Adding "Day/Night" mechanic**

1. **Add to Boardstate** (`Simulation/boardstate.py`):
   ```python
   class BoardState:
       def __init__(self):
           # ... existing init ...
           self.is_day = True  # Day/Night tracking

       def check_daybound_transform(self):
           """Check if Day/Night should transform"""
           # Implement transformation logic
           pass
   ```

2. **Add Parsing** (`Simulation/oracle_text_parser.py`):
   ```python
   def parse_daybound_ability(oracle_text):
       """Parse Daybound/Nightbound abilities"""
       if 'daybound' in oracle_text.lower():
           return {'type': 'daybound', 'triggers': [...]}
       return None
   ```

3. **Integrate into Game Loop** (`Simulation/simulate_game.py`):
   ```python
   def end_of_turn_phase(board_state):
       # ... existing code ...
       board_state.check_daybound_transform()
   ```

4. **Test**: Create `Simulation/tests/test_daybound.py`

---

## MTG Rules Location

### 🎴 Card Text Parsing & Detection

**Location:** `src/utils/*_extractors.py` (14 files)

**These files contain ALL the regex patterns and logic for detecting card mechanics:**

| File | Detects |
|------|---------|
| `aristocrats_extractors.py` | Sacrifice outlets, death triggers, blood artist effects |
| `token_extractors.py` | Token creation, token doublers, populate |
| `graveyard_extractors.py` | Reanimation, mill, self-mill, graveyard recursion |
| `ramp_extractors.py` | Land ramp, mana rocks, dorks, cost reduction |
| `removal_extractors.py` | Spot removal, exile effects, bounce |
| `boardwipe_extractors.py` | Mass removal, asymmetric wraths |
| `keyword_extractors.py` | All keywords (flying, haste, trample, etc.) |
| `damage_extractors.py` | Direct damage, burn, life loss |
| `card_advantage_extractors.py` | Card draw, tutors, card selection |
| `protection_extractors.py` | Hexproof, indestructible, regeneration |
| `combat_extractors.py` | Attack triggers, combat tricks, evasion |
| `recursion_extractors.py` | Bring back from graveyard, flashback |

**Shared Detection Logic:** `shared_mechanics.py`
- Functions used across multiple extractors for consistency

### ⚙️ Game Simulation Rules

**Location:** `Simulation/boardstate.py` (194KB, ~4,800 lines)

**This file contains ALL game mechanics implemented in the simulator:**

- **Permanents Management**: play_permanent(), remove_permanent()
- **Sacrifice Mechanics**: sacrifice_permanent(), process_death_triggers()
- **Token System**: create_token(), double_tokens()
- **Combat System**: declare_attackers(), resolve_combat()
- **Triggers**:
  - ETB (enter the battlefield)
  - Death triggers
  - Attack triggers
  - Landfall triggers
  - Upkeep triggers
- **Counters**: add_counter(), proliferate()
- **Mana**: add_mana(), spend_mana()
- **Card Draw**: draw_card(), draw_cards()
- **Equipment**: attach_equipment(), equipment_triggers()
- **Anthems**: apply_anthem_effects()
- **Keywords**: flying, trample, haste, vigilance, etc.

**Game Loop:** `Simulation/simulate_game.py`
- Turn structure (untap, upkeep, main, combat, end)
- Priority passing
- Goldfish AI decision making

**Text Parsing:** `Simulation/oracle_text_parser.py`
- Converts card oracle text into executable abilities
- Detects triggers, activated abilities, static effects

### 📊 Synergy Rules

**Location:** `src/synergy_engine/rules.py`

**69+ synergy detection functions:**
- Tribal synergies
- Sacrifice/aristocrats
- Token synergies
- Ramp synergies
- Card draw synergies
- Graveyard synergies
- Protection synergies
- Voltron synergies
- Spellslinger synergies
- Creature-based synergies
- Artifact/enchantment synergies
- And many more...

---

## Common Tasks

### 🔍 Task 1: Find where a specific card mechanic is detected

1. **Search in extractors**: `grep -r "mechanic_name" src/utils/`
2. **Check shared logic**: Look in `shared_mechanics.py`
3. **For simulation**: Check `Simulation/oracle_text_parser.py`

**Example: Find "Cascade" detection**
```bash
grep -r "cascade" src/utils/
# Check: src/utils/keyword_extractors.py
```

### ✏️ Task 2: Modify how synergies are displayed in the dashboard

1. **Graph styling**: `app.py` search for "cytoscape_stylesheet"
2. **Synergy descriptions**: `src/synergy_engine/rules.py` (modify 'reason' field)
3. **Categories/colors**: `src/synergy_engine/categories.py`
4. **CSS**: `assets/search_styles.css`

### 🎮 Task 3: Fix a simulation bug (e.g., tokens not doubling correctly)

1. **Identify the mechanic**: Check `Simulation/boardstate.py`
2. **Find the function**: Search for "token" or "double"
3. **Check parsing**: Look at `Simulation/oracle_text_parser.py`
4. **Add test**: Create in `Simulation/tests/test_token_doubling.py`

### 📈 Task 4: Add a new metric to dashboard statistics

1. **Calculate metric**: Add function to `src/analysis/impact_analyzer.py`
2. **Display in UI**: Add to `app.py` in the statistics callback
3. **Update layout**: Modify layout in `app.py`

### 🔌 Task 5: Add a new API integration

1. **Create API module**: `src/api/new_api_integration.py`
2. **Add caching**: Use pattern from `src/api/scryfall.py`
3. **Integrate**: Import in relevant analyzer or app.py

---

## Architecture Patterns

### 🏗️ Pattern 1: Extractor Pattern

**Used in:** `src/utils/*_extractors.py`

```python
def extract_mechanic(card):
    """
    Detects if a card has a specific mechanic

    Args:
        card (dict): Card object with 'oracle_text', 'type_line', etc.

    Returns:
        bool or dict: True/False or detailed info
    """
    oracle_text = card.get('oracle_text', '').lower()
    type_line = card.get('type_line', '').lower()

    # Pattern matching
    if re.search(r'pattern', oracle_text):
        return True

    return False
```

**Key Points:**
- Always check `card.get('field', '')` with defaults
- Use `.lower()` for case-insensitive matching
- Return bool for simple detection, dict for detailed info

### 🏗️ Pattern 2: Synergy Detection Pattern

**Used in:** `src/synergy_engine/rules.py`

```python
def detect_synergy_type(card1, card2):
    """
    Detects synergy between two cards

    Returns:
        list: List of synergy dictionaries
    """
    synergies = []

    # Check bidirectional synergy
    if condition1(card1) and condition2(card2):
        synergies.append({
            'type': 'synergy_category',
            'reason': f"{card1['name']} works with {card2['name']} because...",
            'strength': 0.7  # 0.0 to 1.0
        })

    # Check reverse direction
    if condition1(card2) and condition2(card1):
        synergies.append({
            'type': 'synergy_category',
            'reason': f"{card2['name']} works with {card1['name']} because...",
            'strength': 0.7
        })

    return synergies
```

**Key Points:**
- Always return a list (even if empty)
- Check both directions (card1→card2 and card2→card1)
- Include human-readable 'reason'
- Strength: 0.0-1.0 (0.5=moderate, 0.7=strong, 0.9+=infinite combo)

### 🏗️ Pattern 3: Simulation State Pattern

**Used in:** `Simulation/boardstate.py`

```python
class BoardState:
    def modify_game_state(self, action):
        """
        Modifies game state and processes triggers

        1. Perform action
        2. Check for triggers
        3. Process triggers in order
        4. Check state-based actions
        """
        # Step 1: Perform the action
        result = self._do_action(action)

        # Step 2: Collect triggers
        triggers = self._check_triggers(result)

        # Step 3: Process triggers
        for trigger in triggers:
            self._process_trigger(trigger)

        # Step 4: State-based actions
        self._check_state_based_actions()

        return result
```

**Key Points:**
- Always process triggers after state changes
- Maintain trigger ordering (ETB before death, etc.)
- Check for infinite loops
- Log important state changes for debugging

### 🏗️ Pattern 4: Dashboard Callback Pattern

**Used in:** `app.py`

```python
@app.callback(
    Output('component-id', 'property'),
    Input('trigger-component', 'trigger-property'),
    State('state-component', 'state-property')
)
def callback_function(trigger_value, state_value):
    """
    Handles dashboard interaction

    Returns:
        Value for the output property
    """
    # Validate inputs
    if not trigger_value:
        return default_value

    # Process
    result = process_data(trigger_value, state_value)

    # Return
    return result
```

**Key Points:**
- Always validate inputs
- Use State for values that don't trigger callback
- Return appropriate type for Output property
- Handle errors gracefully

---

## Testing Strategy

### 🧪 Running Tests

**All tests:**
```bash
# Synergy engine tests
pytest tests/

# Simulation tests
pytest Simulation/tests/

# Run all
pytest tests/ Simulation/tests/
```

**Single test:**
```bash
pytest tests/test_specific.py::test_function_name
```

### 🧪 Writing Tests

**Synergy tests** (`tests/`):
```python
def test_synergy_detection():
    card1 = {
        'name': 'Card Name',
        'oracle_text': 'Card text here',
        'type_line': 'Creature — Type'
    }
    card2 = {...}

    synergies = detect_synergy(card1, card2)

    assert len(synergies) > 0
    assert synergies[0]['type'] == 'expected_type'
```

**Simulation tests** (`Simulation/tests/`):
```python
from Simulation.boardstate import BoardState

def test_game_mechanic():
    board = BoardState()

    # Setup
    card = {...}
    board.play_permanent(card)

    # Action
    result = board.trigger_ability(card)

    # Assert
    assert result['success'] == True
    assert board.life_total_change == expected_value
```

---

## Performance Considerations

### ⚡ Optimization Tips

1. **Synergy Analysis is O(n²)**
   - Analyzing 100 cards = 10,000 comparisons
   - Use `src/synergy_engine/incremental_analyzer.py` for large decks
   - Results are cached in `src/synergy_engine/regex_cache.py`

2. **Simulation is Slow**
   - 1000 games can take 1-5 minutes
   - Use `Simulation/run_simulation.py` for batch processing
   - Consider parallel processing for multiple decks

3. **Card Database is Large**
   - `cards-minimal.json`: 34MB (all cards)
   - `cards-preprocessed.json`: 17MB (optimized)
   - Always use preprocessed version in production

4. **Dashboard Responsiveness**
   - Graph with 100+ nodes can be slow
   - Filter synergies by strength threshold
   - Use `layout` parameter in Cytoscape for performance

---

## Common Pitfalls

### ⚠️ Pitfall 1: Case Sensitivity

**Problem:** Card text is mixed case, patterns may fail

**Solution:**
```python
# ALWAYS use .lower() for text matching
oracle_text = card.get('oracle_text', '').lower()
if 'sacrifice' in oracle_text:  # Now case-insensitive
```

### ⚠️ Pitfall 2: Missing Card Fields

**Problem:** Not all cards have all fields (oracle_text, type_line, etc.)

**Solution:**
```python
# ALWAYS use .get() with defaults
oracle_text = card.get('oracle_text', '')  # Returns '' if missing
type_line = card.get('type_line', '')
```

### ⚠️ Pitfall 3: Bidirectional Synergies

**Problem:** Forgetting to check both directions

**Solution:**
```python
# Check card1 → card2
if creates_tokens(card1) and cares_about_tokens(card2):
    synergies.append(...)

# Check card2 → card1 (IMPORTANT!)
if creates_tokens(card2) and cares_about_tokens(card1):
    synergies.append(...)
```

### ⚠️ Pitfall 4: Simulation State Desync

**Problem:** Game state becomes inconsistent (e.g., creature in multiple zones)

**Solution:**
```python
# Always update state atomically
def sacrifice_permanent(self, card):
    # 1. Remove from battlefield
    self.battlefield.remove(card)
    # 2. Add to graveyard
    self.graveyard.append(card)
    # 3. Process triggers AFTER state change
    self.process_death_triggers(card)
```

---

## Key Configuration Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies - modify when adding new libraries |
| `Procfile` | Heroku deployment config |
| `.gitignore` | Git ignore patterns |
| `data/cards/cards-preprocessed.json` | Main card database (17MB) |
| `data/cards/cards-minimal.json` | Full card database (34MB) |

---

## Helpful Commands

```bash
# Run the dashboard locally
python app.py

# Run simulation on a deck
python Simulation/run_simulation.py path/to/deck.txt

# Run all tests
pytest

# Generate new card database (from Scryfall)
python scripts/create_preprocessed_cards.py

# Create embeddings for ML features
python scripts/generate_embeddings.py

# Check synergy rules coverage
python scripts/synergy_rules_report.py
```

---

## Getting Help

**Documentation:**
- `docs/ARCHITECTURE.md` - System architecture deep dive
- `docs/USER_GUIDE.md` - User-facing features
- `docs/SYNERGY_SYSTEM.md` - Synergy detection details
- `docs/SIMULATION_ACCURACY_COMPLETE.md` - Simulation capabilities

**Code Examples:**
- Look at existing extractors in `src/utils/`
- Look at existing synergy rules in `src/synergy_engine/rules.py`
- Look at existing tests in `tests/` and `Simulation/tests/`

**Need to understand a specific mechanic?**
1. Search codebase: `grep -r "mechanic_name" src/ Simulation/`
2. Check documentation: `grep -r "mechanic_name" docs/`
3. Look at tests: `grep -r "mechanic_name" tests/ Simulation/tests/`

---

## 🎯 Quick Start Checklist for AI Models

When approaching this codebase for the first time:

- [ ] Read this guide (you're doing it!)
- [ ] Check `app.py` to understand the UI
- [ ] Browse `src/synergy_engine/analyzer.py` to see how analysis works
- [ ] Look at 2-3 extractors in `src/utils/` to understand patterns
- [ ] Skim `Simulation/boardstate.py` to see simulation scope
- [ ] Run the app locally: `python app.py`
- [ ] Try analyzing a sample deck
- [ ] Read `docs/ARCHITECTURE.md` for deeper understanding

**You're now ready to contribute! 🚀**

---

*Last Updated: 2025-11-14*
*For questions or clarifications, check the docs/ directory or examine existing code patterns.*
