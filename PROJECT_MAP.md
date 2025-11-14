# 🗺️ Project Map - Quick Reference

**Quick file lookup for MTG Deck Synergy Analyzer**

---

## 🎯 Primary Entry Points

| File | Lines | Purpose |
|------|-------|---------|
| `app.py` | 3,387 | **Main dashboard** - All UI, callbacks, graph visualization |
| `src/synergy_engine/analyzer.py` | ~500 | **Synergy analysis** - Orchestrates all synergy detection |
| `Simulation/simulate_game.py` | ~900 | **Game simulation** - Main game loop, turn phases |
| `Simulation/boardstate.py` | ~4,800 | **Core MTG rules** - ALL game mechanics implementation |

---

## 📂 Directory Quick Reference

### Root Level
```
/home/user/Deck_synergy/
├── app.py                      ← DASHBOARD ENTRY POINT
├── requirements.txt            ← Dependencies
├── shared_mechanics.py         ← Shared detection logic
└── Procfile                    ← Heroku deployment
```

### src/ - Modern Source Code
```
src/
├── api/
│   ├── archidekt.py           ← Import decks from Archidekt
│   ├── scryfall.py            ← Fetch card data
│   ├── local_cards.py         ← Local card cache (34K cards)
│   ├── commander_spellbook.py ← Verified combos
│   └── recommendations.py     ← AI card suggestions
│
├── synergy_engine/             ← SYNERGY DETECTION
│   ├── analyzer.py            ← MAIN SYNERGY ENTRY POINT
│   ├── rules.py               ← 69+ synergy rules
│   ├── combo_detector.py      ← Verified combo detection
│   ├── card_advantage_synergies.py
│   ├── recursion_synergies.py
│   ├── three_way_synergies.py
│   ├── categories.py          ← Synergy categories/colors
│   ├── embedding_analyzer.py  ← ML-based analysis
│   ├── incremental_analyzer.py ← Performance optimization
│   └── regex_cache.py         ← Caching
│
├── utils/                      ← CARD MECHANIC EXTRACTORS
│   ├── aristocrats_extractors.py     ← Sacrifice/death
│   ├── token_extractors.py           ← Tokens
│   ├── graveyard_extractors.py       ← Graveyard
│   ├── ramp_extractors.py            ← Mana ramp
│   ├── removal_extractors.py         ← Removal
│   ├── boardwipe_extractors.py       ← Board wipes
│   ├── keyword_extractors.py         ← Keywords
│   ├── damage_extractors.py          ← Damage
│   ├── card_advantage_extractors.py  ← Draw
│   ├── protection_extractors.py      ← Protection
│   ├── combat_extractors.py          ← Combat
│   ├── recursion_extractors.py       ← Recursion
│   ├── card_roles.py                 ← Card categorization
│   └── graph_builder.py              ← Synergy graph builder
│
├── models/
│   ├── deck.py                ← Deck data structure
│   ├── combo.py               ← Combo data model
│   └── deck_session.py        ← Session management
│
├── analysis/
│   ├── weakness_detector.py   ← Find deck weaknesses
│   ├── impact_analyzer.py     ← Card impact scores
│   └── replacement_analyzer.py ← Suggest replacements
│
└── simulation/                 ← Wrappers for legacy simulation
    ├── deck_simulator.py      ← Integration bridge
    └── mana_simulator.py      ← Mana curve analysis
```

### Simulation/ - Game Engine (Legacy)
```
Simulation/
├── boardstate.py (194KB)       ← ALL MTG GAME MECHANICS
├── simulate_game.py (35KB)     ← MAIN GAME LOOP
├── oracle_text_parser.py (27KB) ← Parse card abilities
├── deck_loader.py              ← Load decks
├── run_simulation.py           ← Batch simulator
├── statistical_analysis.py     ← Stats calculation
├── turn_phases.py              ← Turn structure
├── mtg_abilities.py            ← Ability data structures
├── Creature.py                 ← Creature class
├── draw_starting_hand.py       ← Starting hands
├── compare_decks.py            ← Deck comparison
├── convert_dataframe_deck.py   ← Deck conversion
└── tests/                      ← 22 simulation tests
```

### Other Directories
```
tests/                          ← 10 synergy engine tests
scripts/                        ← 8 utility scripts
data/cards/                     ← Card databases (34MB+)
docs/                           ← 56+ documentation files
assets/                         ← CSS/styling
```

---

## 🎯 Common Tasks → File Lookup

### UI/Dashboard Changes
- **Modify layout** → `app.py` (search "layout")
- **Add callback** → `app.py` (search "@app.callback")
- **Change graph style** → `app.py` (search "cytoscape_stylesheet")
- **Update CSS** → `assets/search_styles.css`

### Synergy Detection
- **Add new synergy** → `src/synergy_engine/rules.py`
- **Modify categories** → `src/synergy_engine/categories.py`
- **Add new extractor** → `src/utils/[category]_extractors.py`
- **Main orchestration** → `src/synergy_engine/analyzer.py`

### Card Mechanic Detection
- **Keywords** → `src/utils/keyword_extractors.py`
- **Tokens** → `src/utils/token_extractors.py`
- **Sacrifice** → `src/utils/aristocrats_extractors.py`
- **Graveyard** → `src/utils/graveyard_extractors.py`
- **Ramp** → `src/utils/ramp_extractors.py`
- **Draw** → `src/utils/card_advantage_extractors.py`
- **Removal** → `src/utils/removal_extractors.py`
- **Damage** → `src/utils/damage_extractors.py`
- **Combat** → `src/utils/combat_extractors.py`

### Game Simulation
- **Game mechanics** → `Simulation/boardstate.py`
- **Turn structure** → `Simulation/simulate_game.py`
- **Parse card text** → `Simulation/oracle_text_parser.py`
- **Run simulations** → `Simulation/run_simulation.py`
- **Statistics** → `Simulation/statistical_analysis.py`

### API Integration
- **Scryfall** → `src/api/scryfall.py`
- **Archidekt** → `src/api/archidekt.py`
- **Combos** → `src/api/commander_spellbook.py`
- **Recommendations** → `src/api/recommendations.py`
- **Local cards** → `src/api/local_cards.py`

### Analysis Tools
- **Weaknesses** → `src/analysis/weakness_detector.py`
- **Card impact** → `src/analysis/impact_analyzer.py`
- **Replacements** → `src/analysis/replacement_analyzer.py`

### Data Management
- **Card database** → `data/cards/cards-preprocessed.json` (17MB)
- **Full database** → `data/cards/cards-minimal.json` (34MB)
- **Preprocess cards** → `scripts/create_preprocessed_cards.py`
- **Generate embeddings** → `scripts/generate_embeddings.py`

---

## 📊 File Size Reference

| File | Size | Lines |
|------|------|-------|
| `app.py` | 141KB | 3,387 |
| `Simulation/boardstate.py` | 194KB | ~4,800 |
| `Simulation/simulate_game.py` | 35KB | ~900 |
| `Simulation/oracle_text_parser.py` | 27KB | ~700 |
| `src/synergy_engine/analyzer.py` | ~20KB | ~500 |
| `src/synergy_engine/rules.py` | ~35KB | ~900 |
| `data/cards/cards-minimal.json` | 34MB | - |
| `data/cards/cards-preprocessed.json` | 17MB | - |

---

## 🔧 MTG Rules Implementation

### Where to find MTG rules/mechanics:

| Mechanic Type | Location |
|---------------|----------|
| **Text Detection** | `src/utils/*_extractors.py` |
| **Shared Detection** | `shared_mechanics.py` |
| **Synergy Rules** | `src/synergy_engine/rules.py` |
| **Game Mechanics** | `Simulation/boardstate.py` |
| **Ability Parsing** | `Simulation/oracle_text_parser.py` |

### Specific MTG mechanics:

| Mechanic | File |
|----------|------|
| Sacrifice | `Simulation/boardstate.py:sacrifice_permanent()` |
| Tokens | `Simulation/boardstate.py:create_token()` |
| Death triggers | `Simulation/boardstate.py:process_death_triggers()` |
| ETB triggers | `Simulation/boardstate.py:process_etb_triggers()` |
| Combat | `Simulation/boardstate.py:resolve_combat()` |
| Landfall | `Simulation/boardstate.py:trigger_landfall()` |
| Counters | `Simulation/boardstate.py:add_counter()` |
| Proliferate | `Simulation/boardstate.py:proliferate()` |
| Equipment | `Simulation/boardstate.py:attach_equipment()` |
| Mana | `Simulation/boardstate.py:add_mana()` |
| Card draw | `Simulation/boardstate.py:draw_card()` |

---

## 📚 Documentation Map

| Doc | Purpose |
|-----|---------|
| `AI_GUIDE_FOR_MODELS.md` | **Comprehensive AI guide** (this is the main guide) |
| `PROJECT_MAP.md` | **This file** - Quick reference |
| `CONTRIBUTING_FOR_AI.md` | Step-by-step feature addition guide |
| `README.md` | Project overview |
| `docs/ARCHITECTURE.md` | System architecture |
| `docs/USER_GUIDE.md` | User-facing features |
| `docs/SYNERGY_SYSTEM.md` | Synergy detection details |
| `docs/SIMULATION_ACCURACY_COMPLETE.md` | Simulation capabilities |

---

## 🚀 Quick Commands

```bash
# Run dashboard
python app.py

# Run simulation
python Simulation/run_simulation.py deck.txt

# Run tests
pytest                                    # All tests
pytest tests/                             # Synergy tests only
pytest Simulation/tests/                  # Simulation tests only

# Data management
python scripts/create_preprocessed_cards.py    # Update card database
python scripts/generate_embeddings.py          # Generate ML embeddings
python scripts/synergy_rules_report.py         # Synergy coverage report
```

---

## 🎯 Decision Tree: "Where do I make this change?"

```
Q: What do you want to change?

A: Dashboard UI/UX
   → app.py

A: Synergy detection logic
   → src/synergy_engine/rules.py

A: How cards are categorized
   → src/utils/[category]_extractors.py

A: Game simulation behavior
   → Simulation/boardstate.py or Simulation/simulate_game.py

A: Card text parsing
   → Simulation/oracle_text_parser.py

A: API integrations
   → src/api/[service].py

A: Analysis features
   → src/analysis/[feature].py

A: Card database
   → scripts/create_preprocessed_cards.py

A: Synergy categories/colors
   → src/synergy_engine/categories.py

A: Graph visualization
   → app.py (search "cytoscape")
```

---

*For detailed explanations, see `AI_GUIDE_FOR_MODELS.md`*
*Last Updated: 2025-11-14*
