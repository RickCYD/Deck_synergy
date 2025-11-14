# AI Navigation Guide for MTG Deck Analyzer

**Last Updated:** 2025-11-14
**Purpose:** Help AI models quickly understand and work with this codebase

---

## 🎯 Quick Project Overview

This is a **Magic: The Gathering (MTG) deck analyzer** built with Python, Flask, and Dash. It provides:

1. **Synergy Analysis** - Identifies card interactions and synergies within a deck
2. **Game Simulation** - Runs simulated MTG games to calculate deck power and effectiveness
3. **Interactive Dashboard** - Web UI with graph visualization of card relationships
4. **Combo Detection** - Finds known combos from Commander Spellbook database

---

## 📁 Project Structure (Clean & Organized)

```
Deck_synergy/
│
├── app.py                          # MAIN APPLICATION - Dash web interface (3,387 lines)
├── requirements.txt                # Production dependencies
├── Procfile                        # Heroku deployment config
│
├── src/                           # CORE SOURCE CODE (Modern, organized)
│   ├── api/                       # External API integrations (5 files)
│   │   ├── archidekt.py          # Import decks from Archidekt
│   │   ├── scryfall.py           # Scryfall card data API
│   │   ├── local_cards.py        # Local card database (34K cards)
│   │   ├── commander_spellbook.py # Verified combo database
│   │   └── recommendations.py     # Card suggestion engine
│   │
│   ├── models/                    # Data models (3 files)
│   │   ├── card.py               # Card data structure
│   │   ├── deck.py               # Deck data structure
│   │   └── synergy.py            # Synergy relationship model
│   │
│   ├── synergy_engine/            # SYNERGY DETECTION SYSTEM (12 files)
│   │   ├── analyzer.py           # Main orchestrator - START HERE
│   │   ├── rules.py              # 69+ synergy detection rules
│   │   ├── combo_detector.py    # Commander Spellbook integration
│   │   ├── card_advantage_synergies.py  # Draw/tutor synergies
│   │   ├── recursion_synergies.py       # Graveyard recursion
│   │   ├── three_way_synergies.py       # Multi-card combos
│   │   ├── categories.py                # Synergy categorization
│   │   ├── embedding_analyzer.py        # ML-based semantic analysis
│   │   ├── incremental_analyzer.py      # Performance optimization
│   │   └── regex_cache.py               # Caching for speed
│   │
│   ├── utils/                     # EXTRACTORS & UTILITIES (14 files)
│   │   ├── *_extractor.py        # Extract mechanics from card text:
│   │   │   ├── aristocrats_extractor.py  # Sacrifice/death triggers
│   │   │   ├── token_extractor.py        # Token generation
│   │   │   ├── graveyard_extractor.py    # Graveyard interactions
│   │   │   ├── ramp_extractor.py         # Mana acceleration
│   │   │   ├── removal_extractor.py      # Removal spells
│   │   │   └── ... (10 more extractors)
│   │   ├── card_roles.py         # Categorize cards by function
│   │   ├── graph_builder.py      # Build synergy graphs
│   │   └── fuzzy_search.py       # Card name search
│   │
│   └── simulation/                # Simulation wrappers (3 files)
│       ├── runner.py             # High-level simulation runner
│       ├── metrics.py            # Calculate deck metrics
│       └── wrapper.py            # Interface to Simulation/
│
├── Simulation/                    # GAME SIMULATION ENGINE (Legacy)
│   ├── boardstate.py             # CORE: Board state & game mechanics (194KB)
│   ├── simulate_game.py          # CORE: Game simulation loop (35KB)
│   ├── oracle_text_parser.py    # Parse card abilities from text (27KB)
│   ├── deck_loader.py            # Load cards from various formats (19KB)
│   ├── turn_phases.py            # MTG turn phases (4KB)
│   ├── mtg_abilities.py          # Ability data structures (2.4KB)
│   ├── draw_starting_hand.py     # Starting hand logic
│   │
│   └── tests/                    # Simulation unit tests (18 files)
│       ├── test_landfall_triggers.py
│       ├── test_attack_triggers.py
│       ├── test_counters.py
│       └── ... (15 more test files)
│
├── data/
│   ├── cards/
│   │   ├── cards-minimal.json           # 34MB - All MTG cards database
│   │   └── cards-preprocessed.json      # 17MB - Preprocessed with tags
│   └── decks/                            # Saved deck analyses
│
├── tests/                         # Synergy engine unit tests (10 files)
│   ├── test_boardwipe_extractors.py
│   ├── test_damage_extractors.py
│   └── ... (8 more test files)
│
├── scripts/                       # Utility scripts (8 files)
│   ├── create_minimal_cards.py   # Build card database
│   ├── generate_embeddings.py    # ML embeddings for cards
│   └── verify_and_filter_cards.py # Data validation
│
├── docs/                          # COMPREHENSIVE DOCUMENTATION (43 files)
│   ├── ARCHITECTURE.md           # System architecture overview
│   ├── DEVELOPER.md              # Developer setup guide
│   ├── USER_GUIDE.md             # User documentation
│   ├── SYNERGY_SYSTEM.md         # How synergy detection works
│   ├── COMBO_DETECTION.md        # Combo finder documentation
│   ├── SIMULATION_ACCURACY_COMPLETE.md  # What simulation can handle
│   │
│   ├── archives/                 # Historical analyses
│   └── fixes/                    # Bug fix documentation
│
├── assets/                        # CSS and static files
│
├── README.md                      # PROJECT OVERVIEW - START HERE
├── QUICK_REFERENCE.md            # Quick command reference
├── RELEASE_NOTES.md              # Version history
├── PROVIDE_DECKLIST.md           # How to load a deck
└── READY_FOR_YOUR_DECK.md        # User instructions
```

---

## 🚀 Entry Points for Common Tasks

### Task 1: Understanding the Project
**Start with these files in order:**
1. `README.md` - Project overview
2. `docs/ARCHITECTURE.md` - System architecture
3. `docs/USER_GUIDE.md` - How it works from user perspective
4. `app.py:1-100` - Main application structure

### Task 2: Understanding Synergy Detection
**Read these files:**
1. `src/synergy_engine/analyzer.py` - Main entry point (analyze_deck function)
2. `src/synergy_engine/rules.py` - All synergy rules
3. `docs/SYNERGY_SYSTEM.md` - Comprehensive documentation
4. `src/utils/*_extractor.py` - How mechanics are extracted from card text

**Key Functions:**
- `analyzer.py:analyze_deck()` - Main analysis function
- `rules.py:check_synergy()` - Rule-based synergy detection
- `combo_detector.py:find_combos()` - Find known combos

### Task 3: Understanding Game Simulation
**Read these files:**
1. `Simulation/simulate_game.py:simulate_game()` - Main simulation loop
2. `Simulation/boardstate.py` - All game mechanics (sacrifice, tokens, combat, etc.)
3. `Simulation/oracle_text_parser.py` - Parse card abilities
4. `docs/SIMULATION_ACCURACY_COMPLETE.md` - What mechanics are implemented

**Key Functions:**
- `simulate_game.py:simulate_game()` - Run a single game
- `boardstate.py:BoardState` - Game state management
- `boardstate.py:handle_death_triggers()` - Aristocrats mechanics
- `boardstate.py:handle_token_generation()` - Token creation

### Task 4: Understanding the Dashboard
**Read these files:**
1. `app.py:50-500` - Layout and callbacks
2. `src/utils/graph_builder.py` - Graph visualization
3. Look for `@app.callback` decorators in `app.py` - These handle user interactions

**Key Callbacks:**
- `app.py:update_graph()` - Updates the synergy graph
- `app.py:load_deck()` - Loads deck from various sources
- `app.py:run_simulation()` - Triggers game simulation

### Task 5: Adding New Synergy Detection
**Steps:**
1. Create extractor in `src/utils/` (e.g., `new_mechanic_extractor.py`)
2. Add synergy rules in `src/synergy_engine/rules.py`
3. Register new tags in `src/synergy_engine/categories.py`
4. Write tests in `tests/test_new_mechanic_extractors.py`

**Example extractor structure:**
```python
import re

def extract_mechanic(card):
    """Extract specific mechanic from card text."""
    text = card.get('oracle_text', '').lower()

    # Pattern matching
    if re.search(r'mechanic pattern', text):
        return {'mechanic_tag': True}

    return {}
```

### Task 6: Adding New Game Mechanics to Simulation
**Steps:**
1. Add parsing logic in `Simulation/oracle_text_parser.py`
2. Add game logic in `Simulation/boardstate.py`
3. Write tests in `Simulation/tests/test_new_mechanic.py`

**Key Simulation Mechanics Already Implemented:**
- ✅ Sacrifice triggers (Aristocrats)
- ✅ Death triggers
- ✅ Token generation & doublers
- ✅ Combat damage & triggers
- ✅ Landfall triggers
- ✅ Attack triggers
- ✅ Equipment
- ✅ +1/+1 counters & anthems
- ✅ Mana generation

### Task 7: Improving Performance
**Performance-critical files:**
1. `src/synergy_engine/incremental_analyzer.py` - Incremental analysis
2. `src/synergy_engine/regex_cache.py` - Caching
3. `src/synergy_engine/embedding_analyzer.py` - ML-based analysis (expensive)

**Performance tips:**
- Synergy analysis can be slow for large decks (100+ cards)
- Simulation runs multiple games (default: 1000 iterations)
- Graph rendering slows down with 500+ edges

### Task 8: Debugging Issues
**Common issue locations:**
1. **Card not found** → `src/api/local_cards.py:get_card()`
2. **Synergy not detected** → `src/synergy_engine/rules.py` + relevant extractor
3. **Simulation error** → `Simulation/boardstate.py` (check specific mechanic handler)
4. **Graph rendering issue** → `app.py` (search for 'cytoscape')

---

## 🔍 Key Data Structures

### Card Object
```python
{
    "name": "Sol Ring",
    "mana_cost": "{1}",
    "cmc": 1,
    "type_line": "Artifact",
    "oracle_text": "{T}: Add {C}{C}.",
    "colors": [],
    "keywords": [],
    "image_uris": {"normal": "url"},
    # Extracted mechanics (added by extractors):
    "tags": {
        "ramp": True,
        "fast_mana": True,
        "mana_rocks": True
    }
}
```

### Synergy Object
```python
{
    "card1": "Goblin Bombardment",
    "card2": "Putrid Goblin",
    "strength": 5,
    "category": "combo",
    "explanation": "Infinite sacrifice combo with persist",
    "tags": ["aristocrats", "infinite_combo"]
}
```

### Board State (Simulation)
```python
class BoardState:
    hand: List[Card]
    battlefield: List[Card]
    graveyard: List[Card]
    library: List[Card]
    mana_pool: Dict[str, int]
    life: int
    turn_number: int
    phase: str
```

---

## 📊 Important Metrics & Calculations

### Deck Power Score
Calculated in: `src/simulation/metrics.py`
- **Range:** 0-100
- **Factors:** Win rate, average damage, mana efficiency, card draw

### Card Impact Score
Calculated in: `src/simulation/metrics.py`
- **Measures:** Individual card's contribution to deck performance
- **Method:** Compare deck performance with/without card

### Synergy Strength
Calculated in: `src/synergy_engine/rules.py`
- **Range:** 1-5
- **1-2:** Weak synergy
- **3:** Moderate synergy
- **4:** Strong synergy
- **5:** Combo/Critical synergy

---

## 🧪 Testing

### Run All Tests
```bash
# Synergy engine tests
pytest tests/

# Simulation tests
pytest Simulation/tests/

# Specific test
pytest tests/test_boardwipe_extractors.py -v
```

### Test Coverage
- Synergy extractors: `tests/test_*_extractors.py`
- Simulation mechanics: `Simulation/tests/test_*.py`
- No integration tests yet (good opportunity for contribution!)

---

## 🎨 Dashboard Architecture

### Technology Stack
- **Backend:** Flask
- **Frontend:** Dash (Plotly)
- **Graph Visualization:** Cytoscape.js (via dash-cytoscape)
- **Styling:** Custom CSS in `assets/`

### Main Components (app.py)
1. **Deck Input** - Text area or URL import
2. **Synergy Graph** - Interactive Cytoscape graph
3. **Combo Display** - Known combos from Commander Spellbook
4. **Recommendations** - Suggested cards
5. **Simulation Results** - Deck power, win rate, metrics
6. **Mana Curve** - Histogram of CMC distribution

---

## 🔧 Common Code Patterns

### Loading a Card
```python
from src.api.local_cards import get_card

card = get_card("Sol Ring")
if card:
    print(card['oracle_text'])
```

### Extracting Mechanics
```python
from src.utils.ramp_extractor import extract_ramp

card = get_card("Sol Ring")
ramp_info = extract_ramp(card)
# Returns: {'ramp': True, 'fast_mana': True}
```

### Running Synergy Analysis
```python
from src.synergy_engine.analyzer import analyze_deck

deck_list = ["Sol Ring", "Mana Crypt", "Command Tower"]
synergies = analyze_deck(deck_list)
```

### Running Simulation
```python
from Simulation.simulate_game import simulate_game
from Simulation.deck_loader import load_deck

deck = load_deck(["Sol Ring", "Plains", "Plains", ...])
result = simulate_game(deck, num_turns=10)
print(f"Life: {result['life']}, Damage: {result['damage_dealt']}")
```

---

## 💡 Tips for AI Models Working on This Project

### 1. Always Check These First
- `README.md` - Project context
- `docs/ARCHITECTURE.md` - System design
- This file (`AI_GUIDE.md`) - Navigation

### 2. File Size Awareness
- `app.py` is 3,387 lines - search for specific callbacks, don't read the whole file
- `Simulation/boardstate.py` is 194KB - search for specific mechanics
- Use search/grep instead of reading large files linearly

### 3. Code Organization Principles
- **Modern code:** `src/` directory (well-organized, type hints, docstrings)
- **Legacy code:** `Simulation/` directory (functional but needs refactoring)
- **Tests are separate:** `tests/` and `Simulation/tests/`

### 4. When Adding Features
- **Synergy detection:** Add extractor in `src/utils/`, rules in `src/synergy_engine/rules.py`
- **Simulation mechanics:** Add to `Simulation/boardstate.py` and `oracle_text_parser.py`
- **UI features:** Add to `app.py` (callbacks and layout)
- **Always write tests** in appropriate test directory

### 5. Common Pitfalls
- Card names are case-sensitive in some places
- Oracle text has special symbols: `{T}` (tap), `{W}` (white mana), etc.
- Simulation is goldfish mode (no opponent interaction)
- Not all MTG mechanics are implemented in simulation

### 6. Performance Considerations
- Synergy analysis: O(n²) for pairwise synergies
- Simulation: O(num_games × num_turns × deck_size)
- Graph rendering: Slow with >500 edges
- Use caching where possible

### 7. Dependencies
Check `requirements.txt` for all dependencies. Key ones:
- `dash` - Web framework
- `dash-cytoscape` - Graph visualization
- `scryfall` - MTG card data
- `requests` - API calls
- `numpy` - Numerical operations

---

## 📞 Quick Reference - "Where Do I Find...?"

| What You're Looking For | Location |
|------------------------|----------|
| Main application entry point | `app.py` |
| Synergy detection logic | `src/synergy_engine/analyzer.py` |
| Game simulation logic | `Simulation/simulate_game.py` |
| Card loading from Scryfall | `src/api/scryfall.py` |
| Local card database | `data/cards/cards-minimal.json` |
| Mechanic extraction | `src/utils/*_extractor.py` |
| Synergy rules | `src/synergy_engine/rules.py` |
| Combo detection | `src/synergy_engine/combo_detector.py` |
| Board state management | `Simulation/boardstate.py` |
| Parse card abilities | `Simulation/oracle_text_parser.py` |
| Graph visualization | `app.py` (search for 'cytoscape') |
| Tests for synergies | `tests/` |
| Tests for simulation | `Simulation/tests/` |
| Documentation | `docs/` |
| Architecture overview | `docs/ARCHITECTURE.md` |
| User guide | `docs/USER_GUIDE.md` |
| Deployment config | `Procfile` |

---

## 🚦 Project Status

### What Works Well ✅
- Synergy detection for 69+ mechanic types
- Combo detection from Commander Spellbook (40,000+ combos)
- Game simulation with aristocrats, tokens, combat, landfall
- Interactive dashboard with graph visualization
- Deck import from Archidekt, Scryfall, text files

### Known Limitations ⚠️
- Simulation is goldfish mode only (no opponent)
- Not all MTG mechanics implemented (see `docs/SIMULATION_GAPS_PRIORITY.md`)
- Performance degrades with very large decks (200+ cards)
- Some edge cases in synergy detection

### Good First Contributions 🎯
1. Add missing mechanic extractors (prowess, energy, experience counters)
2. Improve synergy explanations (more detailed text)
3. Add integration tests
4. Optimize graph rendering for large decks
5. Add more simulation mechanics (see gap analysis in docs)

---

## 📚 Further Reading

### Essential Documentation
1. `docs/ARCHITECTURE.md` - System architecture
2. `docs/SYNERGY_SYSTEM.md` - How synergy detection works
3. `docs/SIMULATION_ACCURACY_COMPLETE.md` - Simulation capabilities
4. `docs/DEVELOPER.md` - Development setup

### For Specific Features
- **Combos:** `docs/COMBO_DETECTION.md`
- **Statistical Analysis:** `docs/STATISTICAL_ANALYSIS_GUIDE.md`
- **Bug Fixes:** `docs/fixes/` directory
- **Historical Context:** `docs/archives/` directory

---

## 🤖 How to Ask AI Models for Help

### Good Questions ✅

**Specific and Contextual:**
```
"How does the aristocrats synergy detection work? Please explain the logic
in src/utils/aristocrats_extractor.py and how it's used in
src/synergy_engine/rules.py"
```

**Feature Requests with Context:**
```
"I want to add prowess mechanic detection. Show me:
1. How to create a prowess_extractor.py
2. Where to add synergy rules for prowess
3. Example of similar mechanics (like heroic or magecraft)"
```

**Debugging with Details:**
```
"The simulation isn't counting damage from [[Zurzoth, Chaos Rider]].
The card creates tokens that deal damage on attack. Check:
1. Simulation/oracle_text_parser.py for parsing
2. Simulation/boardstate.py for attack trigger handling
3. Simulation/tests/ for similar test cases"
```

### Bad Questions ❌

**Too Vague:**
```
"How does this project work?"
→ Too broad! Start with README.md and docs/ARCHITECTURE.md
```

**No Context:**
```
"Fix the bug"
→ What bug? Where? What's the error message?
```

**Asking for Complete Rewrites:**
```
"Rewrite the entire simulation engine"
→ Too large! Break into smaller tasks
```

---

## 🎓 Learning Path for New AI Models

### Phase 1: Understanding (1-2 hours)
1. Read `README.md`
2. Read this guide (`AI_GUIDE.md`)
3. Read `docs/ARCHITECTURE.md`
4. Skim `app.py` structure (just the layout, not all code)

### Phase 2: Deep Dive - Pick One Area (2-4 hours)
**Option A: Synergy System**
- Read `src/synergy_engine/analyzer.py`
- Read 2-3 extractors in `src/utils/`
- Read `src/synergy_engine/rules.py`
- Run tests: `pytest tests/`

**Option B: Simulation System**
- Read `Simulation/simulate_game.py`
- Read `Simulation/boardstate.py` (focus on one mechanic)
- Read `Simulation/oracle_text_parser.py`
- Run tests: `pytest Simulation/tests/`

**Option C: Dashboard**
- Read `app.py` callbacks
- Understand Dash/Cytoscape integration
- Trace one user flow (e.g., loading a deck)

### Phase 3: Contributing (varies)
1. Pick a small issue or improvement
2. Write tests first (TDD approach)
3. Implement the feature
4. Verify tests pass
5. Document your changes

---

## 🔗 External Resources

### MTG Rules & Data
- [Scryfall API](https://scryfall.com/docs/api) - Card data
- [MTG Comprehensive Rules](https://magic.wizards.com/en/rules) - Official rules
- [Commander Spellbook](https://commanderspellbook.com/) - Combo database

### Technologies Used
- [Dash Documentation](https://dash.plotly.com/) - Web framework
- [Cytoscape.js](https://js.cytoscape.org/) - Graph visualization
- [Flask](https://flask.palletsprojects.com/) - Backend framework
- [Pytest](https://docs.pytest.org/) - Testing framework

---

## ✅ Quick Health Checks

### Is the Project Working?
```bash
# Test card loading
python -c "from src.api.local_cards import get_card; print(get_card('Sol Ring'))"

# Test synergy analysis
python -c "from src.synergy_engine.analyzer import analyze_deck; print(len(analyze_deck(['Sol Ring', 'Mana Crypt'])))"

# Test simulation
python -c "from Simulation.simulate_game import simulate_game; from Simulation.deck_loader import load_deck; print(simulate_game(load_deck(['Plains'] * 60), num_turns=5))"

# Run tests
pytest tests/ -v
pytest Simulation/tests/ -v

# Start web app (should see "Dash is running on...")
python app.py
```

---

## 🎯 Summary: Most Important Files

If you can only read 10 files, read these:

1. **README.md** - Project overview
2. **AI_GUIDE.md** (this file) - Navigation guide
3. **docs/ARCHITECTURE.md** - System design
4. **app.py** (first 200 lines) - Main application structure
5. **src/synergy_engine/analyzer.py** - Synergy detection entry point
6. **src/synergy_engine/rules.py** - Synergy rules
7. **Simulation/simulate_game.py** - Game simulation loop
8. **Simulation/boardstate.py** (any one mechanic) - Game mechanics
9. **src/api/local_cards.py** - Card data access
10. **src/utils/** (any one extractor) - Mechanic extraction pattern

---

**Happy coding! This project is well-organized and ready for AI-assisted development.** 🚀
