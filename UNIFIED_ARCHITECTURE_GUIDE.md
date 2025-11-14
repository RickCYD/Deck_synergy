# 🏗️ Unified Architecture Guide

**For AI Models: Understanding the New Architecture**

This guide explains the unified architecture that was implemented in Parts 1-5. This is the **RECOMMENDED** way to add new mechanics going forward.

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    RAW CARD DATA                             │
│  (from Scryfall, local cache, or deck import)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  PART 1: UNIFIED CARD PARSER                                │
│  File: src/core/card_parser.py                              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  • Single source of truth for all card ability parsing      │
│  • Parses oracle text once                                  │
│  • Outputs: CardAbilities with triggers, static abilities   │
│  • Cached flags: has_rally, has_prowess, creates_tokens     │
└──────────────────────┬──────────────────────────────────────┘
                       │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
┌───────────────────────┐  ┌────────────────────────────────┐
│ PART 4:               │  │ PART 2:                        │
│ SYNERGY BRIDGE        │  │ TRIGGER REGISTRY               │
│ ──────────────────    │  │ ─────────────────              │
│ File: src/core/       │  │ File: src/core/                │
│   synergy_simulation_ │  │   trigger_registry.py          │
│   bridge.py           │  │                                │
│                       │  │ • Registers triggers by event  │
│ • Detect synergies    │  │ • Creates effect functions     │
│ • Calculate priorities│  │ • Priority ordering            │
│ • Optimal card order  │  │ • Executes on game events      │
└───────────────────────┘  └────────┬───────────────────────┘
                                    │
                                    ▼
                       ┌────────────────────────────────────┐
                       │ PART 3:                            │
                       │ ENHANCED BOARDSTATE                │
                       │ ──────────────────                 │
                       │ Files: Simulation/                 │
                       │   boardstate_extensions.py         │
                       │   unified_integration.py           │
                       │                                    │
                       │ • Execute trigger effects          │
                       │ • Grant keywords (rally)           │
                       │ • Buff creatures (prowess)         │
                       │ • Create tokens                    │
                       │ • Cleanup at EOT                   │
                       └────────────────────────────────────┘
```

---

## 🎯 Key Concepts

### 1. Single Source of Truth (Part 1)

**Before:** Card parsing happened in 14+ different files
- `src/utils/token_extractors.py`
- `src/utils/aristocrats_extractors.py`
- `Simulation/oracle_text_parser.py`
- ... and 11 more

**Problem:** Duplicate logic, inconsistent results, hard to maintain

**After:** All parsing in `src/core/card_parser.py`
- Parse once, use everywhere
- Consistent data format
- Easy to maintain and extend

### 2. CardAbilities Data Structure

The unified parser outputs a `CardAbilities` object:

```python
@dataclass
class CardAbilities:
    name: str
    triggers: List[TriggerAbility]        # Event-based triggers
    static_abilities: List[StaticAbility]  # Always-on effects
    activated_abilities: List[ActivatedAbility]  # Tap/mana abilities
    keywords: Set[str]                     # Flying, haste, etc.
    creature_types: Set[str]               # Human, Ally, etc.

    # Cached flags for quick checks
    has_rally: bool
    has_prowess: bool
    has_magecraft: bool
    creates_tokens: bool
    # ... more flags
```

### 3. Trigger Registry (Part 2)

Central system for managing all triggers in a game:

```python
registry = TriggerRegistry()

# Register a card's triggers
card_id = registry.register_card(card_dict, abilities)

# When event occurs in game
registry.trigger_event('rally', board_state, event_data)
# → All rally triggers execute automatically

# When card leaves battlefield
registry.unregister_card(card_id)
```

### 4. Effect Functions (Part 2)

Standardized effect creators for common patterns:

```python
# Rally effect: grant haste to all creatures
effect_func = create_rally_haste_effect(trigger_data)

# Execute when triggered
effect_func(board_state, source_card)
# → All creatures gain haste until EOT
```

### 5. BoardState Extensions (Part 3)

New methods added to BoardState for trigger execution:

```python
# Grant temporary keywords
board.grant_keyword_until_eot('haste', 'all_creatures')

# Buff creatures temporarily
board.buff_creature_until_eot(power=1, toughness=1)

# Create tokens
board.create_token(count=1, token_type='Spirit', power=1, toughness=1)

# End of turn cleanup
board.cleanup_temporary_effects()
```

### 6. Synergy Bridge (Part 4)

Connects synergy detection with simulation:

```python
bridge = SynergyBridge()

# Detect all synergies using unified parser
synergies = bridge.detect_deck_synergies(deck_cards)
# → 60 synergies found, score: 32.1/100

# Calculate card priorities
priorities = bridge.get_card_play_priorities(deck_cards, synergies)
# → Dragon Fodder: 100.0, Rally cards: 26.8

# Get optimal play order based on board state
optimal_order = bridge.get_optimal_card_order(hand, board, metadata)
```

---

## 📂 File Organization

### Core Architecture (NEW)

```
src/core/
├── card_parser.py              # Part 1: Unified parser
│   ├── UnifiedCardParser       # Main parser class
│   ├── CardAbilities           # Output data structure
│   ├── TriggerAbility          # Triggered ability representation
│   ├── StaticAbility           # Static ability representation
│   └── ActivatedAbility        # Activated ability representation
│
├── trigger_registry.py         # Part 2: Trigger management
│   ├── TriggerRegistry         # Central registry
│   ├── RegisteredTrigger       # Registered trigger data
│   ├── register_card()         # Register triggers
│   ├── trigger_event()         # Execute triggers
│   └── unregister_card()       # Remove triggers
│
├── trigger_effects.py          # Part 2: Effect creators
│   ├── create_rally_haste_effect()
│   ├── create_rally_vigilance_effect()
│   ├── create_prowess_effect()
│   ├── create_token_effect()
│   ├── create_damage_effect()
│   ├── create_draw_effect()
│   └── EFFECT_TYPE_CREATORS    # Effect factory
│
└── synergy_simulation_bridge.py  # Part 4: Synergy bridge
    ├── SynergyBridge           # Main bridge class
    ├── parse_deck_abilities()  # Parse all cards
    ├── detect_deck_synergies() # Find synergies
    ├── get_card_play_priorities()  # Calculate priorities
    └── get_optimal_card_order()    # Optimal ordering
```

### Simulation Integration (NEW)

```
Simulation/
├── boardstate_extensions.py   # Part 3: New BoardState methods
│   ├── enhance_boardstate()    # Add methods to BoardState
│   ├── grant_keyword_until_eot()
│   ├── buff_creature_until_eot()
│   ├── create_token()
│   ├── cleanup_temporary_effects()
│   └── trigger_event()
│
└── unified_integration.py      # Part 3: Integration handlers
    ├── initialize_unified_system()  # Setup at game start
    ├── handle_card_etb()       # Card enters battlefield
    ├── handle_spell_cast()     # Spell cast
    ├── handle_end_of_turn()    # Cleanup phase
    └── handle_creature_attacks()    # Combat phase
```

### Testing (NEW)

```
tests/
├── test_end_to_end_unified_system.py  # Part 5: E2E test
│   └── 3-turn simulation validating complete pipeline
│
└── test_no_regressions.py     # Part 5: Regression tests
    └── Validates no functionality broken
```

---

## 🚀 When to Use Unified Architecture

### ✅ Use Unified Architecture For:

1. **Adding NEW mechanics** (Landfall, Cascade, etc.)
   - Follow `ADDING_NEW_MECHANICS_CHECKLIST.md`

2. **Synergy detection** that needs triggers
   - Use `CardAbilities` from unified parser

3. **Simulation features** that need game events
   - Use trigger registry and BoardState extensions

4. **Anything that touches oracle text parsing**
   - Use `UnifiedCardParser` instead of creating new extractors

### ⚠️ Legacy Code (Backwards Compatibility)

These still exist but should NOT be extended:

- `src/utils/*_extractors.py` - Use unified parser instead
- `Simulation/oracle_text_parser.py` - Use unified parser instead
- Individual synergy rule files - Use synergy bridge instead

**Migration (Part 7)** will gradually move these to unified architecture.

---

## 📖 Step-by-Step: Adding a New Mechanic

See `ADDING_NEW_MECHANICS_CHECKLIST.md` for complete guide.

### Quick Summary:

1. **Add to parser** (`src/core/card_parser.py`)
   - Add flag to CardAbilities
   - Add parsing method
   - Call in parse_card()

2. **Add effect creator** (`src/core/trigger_effects.py`)
   - Create effect function
   - Register in EFFECT_TYPE_CREATORS

3. **Add integration** (`Simulation/unified_integration.py`)
   - Create event handler (if needed)

4. **Add synergy detection** (`src/core/synergy_simulation_bridge.py`)
   - Update detect_deck_synergies()

5. **Test**
   - Add to `tests/test_end_to_end_unified_system.py`
   - Add to `tests/test_no_regressions.py`

---

## 🎓 Examples from Existing Code

### Example 1: Rally Mechanic

**Parser** (`src/core/card_parser.py:417-450`):
```python
def _parse_rally_triggers(self, text, type_line):
    """Parse Rally mechanic."""
    triggers = []

    if re.search(r'rally\s*—\s*whenever|whenever.*ally.*enters', text):
        if 'gain haste' in text:
            return TriggerAbility(
                event='rally',
                effect='haste',
                effect_type='rally_haste',
                value=2.0,
                # ...
            )
```

**Effect Creator** (`src/core/trigger_effects.py:19-45`):
```python
def create_rally_haste_effect(trigger_data):
    """Grant haste until EOT."""
    def effect(board_state, source_card, **kwargs):
        board_state.pending_effects.append({
            'type': 'grant_keyword',
            'keyword': 'haste',
            'targets': 'all_creatures',
        })
    return effect
```

**Integration** (`Simulation/unified_integration.py:60-86`):
```python
def handle_card_etb(board_state, card, card_dict):
    """Handle card entering battlefield."""
    # Parse abilities
    abilities = board_state.unified_parser.parse_card(card_dict)

    # Register triggers
    if abilities.triggers:
        registry_id = board_state.trigger_registry.register_card(card_dict, abilities)

    # Trigger ETB
    board_state.trigger_event('etb', event_data)

    # If Ally, trigger rally
    if 'Ally' in card.type:
        board_state.trigger_event('rally', event_data)
```

### Example 2: Prowess Mechanic

See `test_boardstate_integration.py:213-232` for complete example.

---

## 🔍 Finding What You Need

### "I want to add a new MTG mechanic"
→ See `ADDING_NEW_MECHANICS_CHECKLIST.md`

### "I want to detect a new synergy"
→ Use `SynergyBridge.detect_deck_synergies()`
→ Add detection logic there

### "I want to make triggers execute in simulation"
→ Add to `src/core/trigger_effects.py`
→ Add handler in `Simulation/unified_integration.py`

### "I want to understand how rally works"
→ Read `test_boardstate_integration.py:83-153`
→ Shows complete pipeline: parse → register → execute

### "I want to see the big picture"
→ Run `tests/test_end_to_end_unified_system.py`
→ Shows 3-turn game with all parts working together

---

## ✅ Benefits of Unified Architecture

1. **Single Source of Truth** - Parse once, use everywhere
2. **No Duplicate Code** - One parser instead of 14+ extractors
3. **Triggers Actually Execute** - Rally, prowess work in simulation
4. **Synergies Influence Gameplay** - Priorities affect card choices
5. **Easy to Extend** - Follow checklist, add mechanic
6. **Well Tested** - 14/14 tests pass (100%)
7. **High Performance** - 6M+ cards/second parsing

---

## 🚨 Common Pitfalls

### ❌ DON'T: Create new extractor files
```python
# DON'T DO THIS
src/utils/landfall_extractors.py  # ❌ Wrong approach
```

### ✅ DO: Add to unified parser
```python
# DO THIS
src/core/card_parser.py  # ✅ Correct approach
    def _parse_landfall_triggers(...)
```

### ❌ DON'T: Parse oracle text multiple times
```python
# DON'T DO THIS
text = card.get('oracle_text')
if 'landfall' in text:  # ❌ Parsing again
```

### ✅ DO: Use CardAbilities flags
```python
# DO THIS
abilities = parser.parse_card(card)
if abilities.has_landfall:  # ✅ Use cached flag
```

### ❌ DON'T: Create one-off trigger handling
```python
# DON'T DO THIS
if 'rally' in card.oracle_text:  # ❌ Manual trigger
    grant_haste_to_all()
```

### ✅ DO: Use trigger registry
```python
# DO THIS
board.trigger_event('rally', event_data)  # ✅ Automatic
```

---

## 📚 Further Reading

- `IMPLEMENTATION_PROGRESS.md` - Complete implementation details
- `UNIFIED_ARCHITECTURE_PLAN.md` - Original design document
- `ADDING_NEW_MECHANICS_CHECKLIST.md` - Step-by-step guide
- `tests/test_end_to_end_unified_system.py` - Complete example

---

## 🤝 Getting Help

If you're unsure whether to use unified architecture:

**Rule of thumb:** If it involves oracle text parsing or game triggers, use unified architecture.

**Examples:**
- Adding "Landfall" mechanic → **Use unified architecture** ✅
- Fixing UI bug in dashboard → Use existing code ❌
- Adding new graph visualization → Use existing code ❌
- Detecting "Storm" synergies → **Use unified architecture** ✅
- Adding new combo detection → Could use either (preference: unified)

**When in doubt, check the test files** - they show how everything works together.
