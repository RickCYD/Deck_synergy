# Token Copy Mechanics Implementation

## Overview

This document describes the implementation of token copy mechanics for cards like **Irenicus's Vile Duplication**, which create token copies of creatures with modifications.

**Card Example:**
```
Irenicus's Vile Duplication {3}{U}
Sorcery
Create a token that's a copy of target creature you control, except the token has flying and it isn't legendary.
```

## Implementation Components

### 1. Token Copy Extractor (`src/utils/token_extractors.py`)

**Function:** `extract_token_copy_effects(card: Dict) -> Dict`

Detects when a card creates token copies of creatures and extracts:
- Whether it creates token copies
- What it can target (your creatures, any creature, etc.)
- How many copies it creates
- What modifications are applied (keywords, legendary removal, etc.)
- Trigger type (spell, ETB, activated, etc.)

**Example Output for Irenicus's Vile Duplication:**
```python
{
    'creates_token_copies': True,
    'copy_target': 'your_creature',
    'copy_count': 1,
    'modifications': ['flying', 'not_legendary'],
    'trigger_type': 'spell',
    'repeatable': False
}
```

### 2. Enhanced Synergy Detection (`src/synergy_engine/rules.py`)

**Function:** `detect_copy_synergy(card1: Dict, card2: Dict) -> Optional[Dict]`

Enhanced to detect:
- **Token copy + ETB triggers**: High value synergy (4.0-5.0)
- **Legendary + not_legendary modification**: Bonus value (5.0) when copying legendary creatures
- **Token copy + powerful abilities**: Synergy with static abilities (3.5)

**Synergy Examples:**
- Irenicus's Vile Duplication + Mulldrifter = 4.0 value
- Irenicus's Vile Duplication + Legendary creature with ETB = 5.0 value
- Irenicus's Vile Duplication + Creature with powerful static ability = 3.5 value

**Synergy Output:**
```python
{
    'name': 'Token Copy + ETB Value',
    'description': "Irenicus's Vile Duplication creates token copies that trigger Mulldrifter's ETB again",
    'value': 4.0,
    'category': 'tokens',
    'subcategory': 'token_copy'
}
```

### 3. Simulation Support (`Simulation/boardstate.py`)

**Method:** `create_token_copy(source_creature, modifications=None, verbose=False)`

Creates a token copy of a creature with optional modifications:
- Deep copies the source creature
- Applies keyword modifications (flying, haste, etc.)
- Removes legendary status if specified
- Triggers ETB effects
- Supports token doublers (Doubling Season, etc.)

**Example Usage:**
```python
# Copy a creature with Irenicus's Vile Duplication
token = board.create_token_copy(
    source_creature=mulldrifter,
    modifications={
        'keywords': ['flying'],
        'not_legendary': True
    },
    verbose=True
)
```

**Supported Modifications:**
- `keywords`: List of keywords to add (flying, haste, trample, etc.)
- `not_legendary`: Remove legendary status
- `count`: Number of copies to create
- `power_mod`: Modify power (+X or -X)
- `toughness_mod`: Modify toughness (+X or -X)

## Test Results

All tests passed successfully:

### ✓ Test 1: Token Copy Extractor
- Correctly identifies Irenicus's Vile Duplication as creating token copies
- Detects target type: "your_creature"
- Extracts modifications: flying, not_legendary
- Identifies trigger type: spell

### ✓ Test 2: Synergy Detection
- Detects synergy with ETB creatures (Mulldrifter)
- Assigns appropriate value (4.0 for non-legendary, 5.0 for legendary with not_legendary mod)
- Categorizes as 'tokens' with subcategory 'token_copy'

### ✓ Test 3: Simulation Token Copy
- Creates token copy with same characteristics as original
- Applies modifications (flying, not_legendary)
- Adds "Token" to type line
- Triggers ETB effects properly

## Example Cards Supported

This implementation works with various token copy effects:

1. **Irenicus's Vile Duplication** - Copy with flying and not legendary
2. **Cackling Counterpart** - Simple copy
3. **Rite of Replication** - Create 5 copies
4. **Helm of the Host** - Create token copy each combat
5. **Quasiduplicate** - Copy with jump-start
6. **Phantasmal Image** - Copy as it enters (creature)
7. **Spark Double** - Copy with +1/+1 counter and not legendary

## Synergy Highlights

Token copy effects create particularly strong synergies with:

### High-Value ETB Triggers
- **Mulldrifter**: Draw 2 cards again
- **Archaeomancer**: Return instant/sorcery again
- **Eternal Witness**: Return any card again
- **Ravenous Chupacabra**: Destroy another creature
- **Agent of Treachery**: Steal another permanent

### Legendary Creatures (with not_legendary modification)
- Can have both original and token on battlefield
- Double the static abilities
- Examples: Thassa, Purphoros, Rhystic Study-attached commanders

### Powerful Static Abilities
- **Impact Tremors**: Each copy triggers damage
- **Cathars' Crusade**: Each copy gets counters
- **Purphoros, God of the Forge**: Each copy deals damage

## Files Modified

1. **src/utils/token_extractors.py**
   - Added `extract_token_copy_effects()` function
   - Updated `classify_token_mechanics()` to include token copy effects

2. **src/synergy_engine/rules.py**
   - Enhanced `detect_copy_synergy()` function
   - Added detection for token copy + ETB synergies
   - Added bonus value for legendary + not_legendary combinations
   - Added detection for token copy + powerful abilities

3. **Simulation/boardstate.py**
   - Added `create_token_copy()` method
   - Supports modifications (keywords, legendary removal, count, P/T)
   - Integrates with ETB triggers and counter effects
   - Works with token doublers

## Future Enhancements

Potential improvements for future versions:

1. **Extended Modification Support**
   - Color changes
   - Mana cost modifications
   - Additional +X/+X modifications

2. **More Synergy Patterns**
   - Copy effects + sacrifice outlets
   - Copy effects + flicker/blink
   - Copy effects + death triggers

3. **Oracle Text Parsing**
   - Auto-detect copy effects in oracle text parser
   - Auto-apply modifications from oracle text

4. **Copy Permanent Support**
   - Extend to artifacts, enchantments, planeswalkers
   - Handle legendary permanents generically

## Conclusion

The token copy mechanics implementation provides complete support for cards like Irenicus's Vile Duplication:

- ✅ **Detection**: Extracts copy effects and modifications
- ✅ **Synergy**: Identifies high-value interactions
- ✅ **Simulation**: Creates proper token copies with modifications
- ✅ **Legendary Support**: Handles legendary removal correctly

This enables the analyzer to properly evaluate token copy strategies and recommend synergistic cards for Commander decks.
