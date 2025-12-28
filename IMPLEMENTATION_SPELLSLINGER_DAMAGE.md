# Spellslinger Damage Mechanics Implementation

## Overview

This document describes the generic implementation of spellslinger damage mechanics for cards like **Guttersnipe** that deal damage whenever you cast instant or sorcery spells.

**Card Example:**
```
Guttersnipe {2}{R}
Creature — Goblin Shaman
Whenever you cast an instant or sorcery spell, Guttersnipe deals 2 damage to each opponent.
2/2
```

## Implementation Components

### 1. Damage-on-Spell Extractor (`src/utils/spellslinger_extractors.py`)

**Function:** `extract_deals_damage_on_spell(card: Dict) -> Dict`

Detects when a card deals damage triggered by casting spells:
- Damage amount
- Spell type (instant/sorcery, noncreature, any)
- Damage target (each opponent, any target, etc.)
- Magecraft keyword support

**Example Output for Guttersnipe:**
```python
{
    'deals_damage_on_spell': True,
    'spell_type': 'instant_sorcery',
    'damage_amount': 2,
    'damage_target': 'each_opponent',
    'magecraft': False
}
```

### 2. Synergy Detection (`src/synergy_engine/spellslinger_engine_synergies.py`)

**Function:** `detect_damage_on_spell_synergy(card1: Dict, card2: Dict) -> Optional[Dict]`

Detects synergies between damage-on-spell cards and spells:
- **Free spells** (0 CMC): +3.0 bonus value
- **1 CMC spells**: +2.0 bonus value
- **2 CMC spells**: +1.0 bonus value
- **Cantrips** (draw effects): +1.0 bonus value
- **Each opponent** damage: +0.5 bonus value

**Value Calculation:**
```
Base: 5.0
+ CMC bonus (0-3.0)
+ Cantrip bonus (0-1.0)
+ Multiplayer bonus (0-0.5)
= Total value
```

**Example Synergies:**
- **Guttersnipe + Brainstorm** (1 CMC cantrip) = 8.5 value
  - 5.0 base + 2.0 (1 CMC) + 1.0 (cantrip) + 0.5 (each opponent)
- **Guttersnipe + Lightning Bolt** (1 CMC) = 7.5 value
  - 5.0 base + 2.0 (1 CMC) + 0.5 (each opponent)
- **Guttersnipe + Cultivate** (3 CMC) = 5.5 value
  - 5.0 base + 0.5 (each opponent)

### 3. Oracle Text Parsing (`Simulation/oracle_text_parser.py`)

**Function:** `parse_spell_cast_triggers_from_oracle(text: str, card_name: str = "") -> list[TriggeredAbility]`

Generically parses spell cast triggers from oracle text:
- **Pattern 1**: Damage on instant/sorcery cast
- **Pattern 2**: Damage on noncreature spell cast
- **Pattern 3**: Token creation on instant/sorcery cast
- **Pattern 4**: Token creation on noncreature spell cast

**Trigger Events:**
- `spell_cast_instant_sorcery` - For instant/sorcery triggers
- `spell_cast_noncreature` - For noncreature spell triggers

**Implementation (integrated into deck loader):**
```python
# In Simulation/deck_loader.py
df["TriggeredAbilities"] = df["OracleText"].apply(
    lambda text: (
        parse_etb_triggers_from_oracle(text)
        + parse_attack_triggers_from_oracle(text)
        + parse_damage_triggers_from_oracle(text)
        + parse_death_triggers_from_oracle(text)
        + parse_spell_cast_triggers_from_oracle(text)  # NEW!
    )
)
```

## Test Results

All tests passed successfully:

### ✓ Test 1: Damage-on-Spell Extractor
- Correctly detects Guttersnipe's damage trigger
- Identifies spell type: instant/sorcery
- Extracts damage amount: 2
- Identifies target: each opponent

### ✓ Test 2: Synergy Detection
- **Guttersnipe + Brainstorm**: 8.5 value (cheap cantrip)
- **Guttersnipe + Lightning Bolt**: 7.5 value (cheap instant)
- **Guttersnipe + Opt**: 8.5 value (cantrip + scry)
- **Guttersnipe + Cultivate**: 5.5 value (expensive spell)

### ✓ Test 3: Oracle Text Parsing
- Generically parses spell cast damage triggers
- Creates appropriate trigger events
- Calculates damage correctly (2 damage × 3 opponents = 6 total)

### ✓ Test 4: Firebrand Archer (Noncreature Variant)
- Correctly handles noncreature spell triggers
- Works with different damage amounts (1 damage)

## Supported Cards

This implementation works with various spellslinger damage cards:

### Instant/Sorcery Triggers
- **Guttersnipe** - 2 damage to each opponent
- **Electrostatic Field** - 1 damage to each opponent
- **Thermo-Alchemist** - 1 damage to target (activated, not trigger)

### Noncreature Spell Triggers
- **Firebrand Archer** - 1 damage to each opponent
- **Electrostatic Field** - 1 damage to each opponent (also works)

### Magecraft Triggers
- **Archmage Emeritus** - Draw a card (not damage, but same pattern)
- **Arcane Bombardment** - Exile and cast (complex)

## Synergy Highlights

Spellslinger damage creates particularly strong synergies with:

### Free Spells (0 CMC)
- **Gitaxian Probe** - Free damage + draw
- **Pact of Negation** - Free damage + counterspell
- **Force of Will** - Free damage + protection

### Cheap Cantrips (1-2 CMC)
- **Brainstorm** - 1 mana, draw 3, deal damage
- **Ponder** - 1 mana, dig, deal damage
- **Opt** - 1 mana, scry + draw, deal damage
- **Lightning Bolt** - 1 mana, 3 damage + 2 to each opponent

### Storm/Copy Effects
- **Grapeshot** - Each copy triggers Guttersnipe!
- **Mind's Desire** - Each card cast triggers
- **Thousand-Year Storm** - Copies trigger damage

### Token Generators on Spell Cast
- **Young Pyromancer** - Create token AND deal damage
- **Talrand, Sky Summoner** - Create token AND deal damage
- **Murmuring Mystic** - Create token AND deal damage

## Files Modified

1. **src/utils/spellslinger_extractors.py**
   - Added `extract_deals_damage_on_spell()` function
   - Detects damage triggers, spell types, targets

2. **src/synergy_engine/spellslinger_engine_synergies.py**
   - Added `detect_damage_on_spell_synergy()` function
   - Values cheap spells and cantrips highly
   - Bonus for multiplayer damage

3. **Simulation/oracle_text_parser.py**
   - Added `parse_spell_cast_triggers_from_oracle()` function
   - Generic parsing for spell cast triggers
   - Handles damage and token creation triggers

4. **Simulation/deck_loader.py**
   - Added import for `parse_spell_cast_triggers_from_oracle`
   - Integrated into triggered abilities collection

## Key Design Principles

### 1. Generic Implementation
- **NO card-specific hardcoded logic**
- Works with any card that matches the pattern
- Easily extensible to new cards

### 2. Synergy Value Scaling
- Cheap spells = higher value (can cast multiple)
- Cantrips = bonus (replace themselves)
- Multiplayer damage = bonus (hits all opponents)

### 3. Trigger Event System
- Uses standard trigger events (`spell_cast_instant_sorcery`)
- Integrates with existing simulation framework
- Effects calculated correctly (damage × 3 opponents)

## Example Deck Strategy

A typical Guttersnipe deck would include:

**Damage Triggers (4-6 cards):**
- Guttersnipe
- Firebrand Archer
- Electrostatic Field

**Cheap Cantrips (12-15 cards):**
- Brainstorm
- Ponder
- Preordain
- Opt
- Consider
- Gitaxian Probe

**Removal/Interaction (8-10 cards):**
- Lightning Bolt
- Counterspell
- Mana Leak
- Pyroblast

**Card Advantage (6-8 cards):**
- Treasure Cruise
- Dig Through Time
- Fact or Fiction

This creates a deck where every spell you cast deals 2-4+ damage to each opponent while providing value, leading to incremental wins through spellslinging!

## Future Enhancements

Potential improvements for future versions:

1. **Magecraft Keyword Expansion**
   - Better support for "cast or copy" triggers
   - Track spell copies separately

2. **Variable Damage**
   - Support for "deals damage equal to X"
   - Power-matters damage

3. **Additional Targets**
   - Single target damage
   - "Any target" damage allocation

4. **Prowess Integration**
   - Combine damage triggers with prowess
   - Creature pump + damage synergies

## Conclusion

The spellslinger damage mechanics implementation provides complete, generic support for cards like Guttersnipe:

- ✅ **Detection**: Extracts damage triggers from any card
- ✅ **Synergy**: Identifies high-value interactions with spells
- ✅ **Simulation**: Generically handles spell cast triggers
- ✅ **Scalability**: Works with variants (noncreature, magecraft)

This enables the analyzer to properly evaluate spellslinger damage strategies and recommend synergistic cards for Commander decks.
