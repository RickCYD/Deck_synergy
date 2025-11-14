# Aristocrats Deck Fix - Death Triggers Now Working

## Problem

Aristocrats decks were showing extremely poor goldfish simulation metrics:
- **7 total damage in 10 turns** (expected: 200-350)
- **0 drain damage** (expected: 150-270)
- **Peak board power: 2** (expected: 15-30)

This was because **death drain triggers weren't firing at all** in the simulation.

## Root Cause

The simulation has two card loading paths:
1. **Simulation module** (`Simulation/deck_loader.py`) - Used when loading decks directly for testing
2. **App integration** (`src/simulation/deck_simulator.py`) - Used when the app runs simulations

The app's `convert_card_to_simulation_format()` function was creating Card objects without setting the `death_trigger_value` and `sacrifice_outlet` attributes. Even though the simulation code checks for these attributes before firing death triggers, they were always 0/False.

## Fixes Applied

### 1. Created Oracle Text Parsing Functions
**File**: `Simulation/oracle_text_parser.py`

Added two new functions:
- `parse_death_triggers_from_oracle(text)` - Detects death drain triggers
- `parse_sacrifice_outlet_from_oracle(text)` - Detects sacrifice outlets

These parse oracle text patterns:
- Death drains: `"dies"` + `"opponent"` + `"loses life"`
- Leaves battlefield: `"leaves the battlefield"` + `"opponent"` + `"loses life"`
- Sacrifice outlets: `"sacrifice [creature]:"` activation cost

### 2. Updated Deck Loader
**File**: `Simulation/deck_loader.py`

Modified `_df_to_cards()`, `fetch_cards_from_scryfall_bulk()`, and `fetch_card_from_scryfall()` to:
- Call the new parsing functions when loading cards
- Set `death_trigger_value` and `sacrifice_outlet` attributes on Card objects

### 3. Updated App Integration
**File**: `src/simulation/deck_simulator.py`

Modified `convert_card_to_simulation_format()` to:
- Import the new parsing functions
- Call them when converting cards from Scryfall format to simulation format
- Pass the attributes to the Card constructor

This ensures the app's simulation path also sets these attributes correctly.

### 4. Created Shared Detection Utilities
**File**: `src/utils/aristocrats_extractors.py`

Created a shared module that both the synergy engine and simulation can use:
- `detect_death_drain_trigger(oracle_text)` - Returns drain value
- `is_sacrifice_outlet(oracle_text)` - Returns True/False
- `has_death_trigger(oracle_text)` - Detects ANY death trigger
- `creates_tokens(oracle_text)` - Detects token generation
- `get_aristocrats_classification(oracle_text)` - Full classification

This ensures **consistent detection** across the entire codebase.

## Cards Now Detected Correctly

### Death Drain Triggers
- Zulaport Cutthroat
- Cruel Celebrant
- Bastion of Remembrance
- Nadier's Nightblade (token leaves battlefield)
- Elas il-Kor, Sadistic Pilgrim
- Mirkwood Bats (token-specific)

### Sacrifice Outlets
- Goblin Bombardment
- Viscera Seer
- Priest of Forgotten Gods
- Ashnod's Altar
- Phyrexian Altar

## Expected Results

After the fix, aristocrats decks should show:

| Metric | Before | After |
|--------|--------|-------|
| Total Damage (10 turns) | 7 | 200-350 |
| Combat Damage | 7 | 40-80 |
| Drain Damage | 0 | 150-270 |
| Peak Board Power | 2 | 15-30 |
| Tokens Created | ~10 | 20-40 |
| Avg Damage/Turn | 0.7 | 20-35 |

## Testing

### Unit Tests
Run the parsing function tests:
```bash
python test_death_parsing.py
```

This tests all critical aristocrats cards with their actual oracle text.

### Integration Test (when app is running)
1. Load your Queen Marchesa aristocrats deck in the app
2. The deck will be analyzed with synergies
3. Simulation will run automatically (100 games, 10 turns each)
4. Check the "Deck Effectiveness" section:
   - Total Damage should be 200-350
   - You should see both Combat and Drain damage broken down
   - Commander avg turn should be reasonable

## Files Changed

### Core Fixes
- `Simulation/oracle_text_parser.py` - Added parsing functions
- `Simulation/deck_loader.py` - Integrated parsing into card loading
- `src/simulation/deck_simulator.py` - Integrated parsing into app conversion

### Shared Utilities
- `src/utils/aristocrats_extractors.py` - NEW: Shared detection logic

### Tests
- `test_death_parsing.py` - Unit tests for parsing functions
- `test_direct_simulation.py` - Integration test (requires Scryfall API)
- `test_user_deck.py` - Full deck test (requires app API)

## Implementation Details

### Card Class
The `Card` class in `Simulation/simulate_game.py` already had these attributes:
```python
death_trigger_value=0  # Default: no death drain
sacrifice_outlet=False  # Default: not a sacrifice outlet
```

### Simulation Logic
The simulation in `Simulation/boardstate.py` already had the logic to use these attributes:
```python
def trigger_death_effects(self, creature, verbose=False):
    for permanent in self.creatures + self.enchantments + self.artifacts:
        death_value = getattr(permanent, 'death_trigger_value', 0)
        if death_value > 0:
            # Drain each opponent
```

The problem was just that `death_trigger_value` was never being set!

## Commits

1. `98b66ab` - fix: Parse death drain triggers and sacrifice outlets for aristocrats decks
2. `58b90ac` - test: Add additional death trigger test scripts
3. `5842873` - fix: Integrate death trigger parsing into app's deck simulator

## Future Improvements

1. **Synergy Engine Integration**: Update `src/synergy_engine/rules.py` to import from `src/utils/aristocrats_extractors.py` instead of using its own regex patterns

2. **More Aristocrats Mechanics**:
   - Blood Artist (life loss on ANY creature death, not just yours)
   - Syr Konrad (graveyard triggers)
   - Mayhem Devil (treasure/permanent sacrifice)

3. **ETB Drain Improvements**:
   - Impact Tremors detection is manual oracle text matching
   - Could be improved with better parsing

4. **Three-Way Synergies**:
   - Token Generator + Sacrifice Outlet + Death Payoff already detected
   - Now it should show correct values in simulation too

## Notes

- The parsing is intentionally conservative - it only detects life drain effects (`opponent loses life`), not general death triggers
- Cards like Pitiless Plunderer (creates treasure on death) don't get `death_trigger_value` set because they don't drain life
- The simulation handles these separately with oracle text checks
- This is intentional to keep the metrics focused on actual damage output
