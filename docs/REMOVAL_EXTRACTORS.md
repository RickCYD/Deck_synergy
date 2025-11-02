# Removal Mechanics Extractors

Comprehensive extraction and classification functions for MTG removal spells.

## Overview

The removal extractors module provides detailed classification of four main types of removal mechanics:

1. **Counterspells** - Counter target spell effects
2. **Destroy Effects** - Destroy target permanent/creature effects
3. **Exile Effects** - Exile target permanent/creature effects
4. **Bounce Effects** - Return to hand/library effects

## Functions

### 1. `extract_counterspell_mechanics(card: Dict) -> List[Dict]`

Extracts all counterspell mechanics from a card's oracle text.

**Subtypes Detected:**
- `unconditional` - Counter target spell (no restrictions)
- `conditional_type` - Counter target noncreature/creature/instant/sorcery spell
- `cmc_restriction` - Counter target spell with CMC ≤ X
- `soft_counter` - Counter unless controller pays
- `counter_plus` - Counter with additional effect (draw, scry, etc.)
- `redirect` - Change/redirect spell targets

**Example:**
```python
card = {
    'name': 'Counterspell',
    'oracle_text': 'Counter target spell.'
}

result = extract_counterspell_mechanics(card)
# [{'type': 'counterspell', 'subtype': 'unconditional', 'description': 'Counter target spell'}]
```

### 2. `extract_destroy_mechanics(card: Dict) -> List[Dict]`

Extracts all destroy effects from a card's oracle text.

**Subtypes Detected:**
- `creature_unconditional` - Destroy target creature (no restrictions)
- `creature_conditional` - Destroy target creature with restrictions (nonblack, power ≤ X, etc.)
- `artifact` - Destroy target artifact
- `enchantment` - Destroy target enchantment
- `permanent` - Destroy target permanent
- `planeswalker` - Destroy target planeswalker
- `mass_creatures` - Destroy all creatures (board wipe)
- `mass_removal` - Destroy all permanents of type

**Example:**
```python
card = {
    'name': 'Wrath of God',
    'oracle_text': 'Destroy all creatures. They can\'t be regenerated.'
}

result = extract_destroy_mechanics(card)
# [{'type': 'destroy', 'subtype': 'mass_creatures', 'target': 'all_creatures', 'is_board_wipe': True}]
```

### 3. `extract_exile_mechanics(card: Dict) -> List[Dict]`

Extracts all exile effects from a card's oracle text.

**Subtypes Detected:**
- `creature_permanent` - Exile target creature permanently
- `permanent_permanent` - Exile target permanent permanently
- `temporary_eot` - Exile and return at end of turn
- `flicker` - Exile and return immediately
- `oblivion_ring` - Exile until source leaves battlefield
- `graveyard_hate` - Exile from graveyard
- `mill_exile` - Exile from top of library
- `face_down` - Exile face down

**Example:**
```python
card = {
    'name': 'Swords to Plowshares',
    'oracle_text': 'Exile target creature. Its controller gains life equal to its power.'
}

result = extract_exile_mechanics(card)
# [{'type': 'exile', 'subtype': 'creature_permanent', 'is_permanent': True, 'target': 'creature'}]
```

### 4. `extract_bounce_mechanics(card: Dict) -> List[Dict]`

Extracts all bounce/return to hand effects from a card's oracle text.

**Subtypes Detected:**
- `creature` - Return target creature to hand
- `permanent` - Return target permanent to hand
- `artifact/enchantment` - Return target artifact/enchantment to hand
- `mass_creatures` - Return all creatures to hand
- `mass_permanents` - Return all permanents to hand
- `library_top` - Put target on top of library
- `library_bottom` - Put target on bottom of library
- `self_bounce` - Return your own permanent to hand

**Example:**
```python
card = {
    'name': 'Unsummon',
    'oracle_text': 'Return target creature to its owner\'s hand.'
}

result = extract_bounce_mechanics(card)
# [{'type': 'bounce', 'subtype': 'creature', 'target': 'creature', 'destination': 'hand'}]
```

### 5. `classify_removal_type(card: Dict) -> Dict`

Comprehensive classification of all removal mechanics in a card.

**Returns:**
```python
{
    'card_name': str,
    'counterspells': List[Dict],
    'destroy_effects': List[Dict],
    'exile_effects': List[Dict],
    'bounce_effects': List[Dict],
    'total_removal_mechanics': int
}
```

**Example:**
```python
card = {
    'name': 'Cryptic Command',
    'oracle_text': 'Choose two — • Counter target spell. • Return target permanent to its owner\'s hand. • Tap all creatures your opponents control. • Draw a card.'
}

result = classify_removal_type(card)
# {
#     'card_name': 'Cryptic Command',
#     'counterspells': [{'type': 'counterspell', 'subtype': 'unconditional', ...}],
#     'bounce_effects': [{'type': 'bounce', 'subtype': 'permanent', ...}],
#     'destroy_effects': [],
#     'exile_effects': [],
#     'total_removal_mechanics': 2
# }
```

## Test Results

All extraction functions have been tested with comprehensive test cases:

### Counterspells - ✅ All Passing
- Unconditional counters (Counterspell)
- Soft counters (Mana Leak, Spell Pierce)
- Conditional counters (Negate, Essence Scatter)
- Counter with effects (Ionize, draw effects)

### Destroy Effects - ✅ All Passing
- Unconditional destroy (Murder)
- Conditional destroy (Doom Blade, Vanquish the Weak)
- Board wipes (Wrath of God)
- Artifact/enchantment removal (Naturalize)
- Permanent removal (Vindicate)

### Exile Effects - ⚠️ Partially Passing
**Working:**
- Permanent exile (Swords to Plowshares)
- Flicker effects (Cloudshift)
- Temporary exile (Flickerwisp)

**Needs Improvement:**
- Oblivion Ring pattern (complex multi-trigger effects)
- Graveyard hate with replacement effects (Rest in Peace)
- Planeswalker abilities (Ashiok)

### Bounce Effects - ⚠️ Partially Passing
**Working:**
- Single target bounce (Unsummon)
- Library effects (Spin into Myth)

**Needs Improvement:**
- Mass bounce with "their owners' hands" pattern (Evacuation, Cyclonic Rift)
- Conditional bounce (attacking creatures)
- Self-bounce patterns

## Usage in Synergy Detection

These extractors can be integrated into synergy detection to identify:

1. **Removal Package Synergies**
   - Counterspell-heavy decks
   - Board wipe strategies
   - Exile-based graveyard hate

2. **ETB/LTB Synergies**
   - Flicker effects with ETB triggers
   - Bounce effects for repeatable ETBs
   - Oblivion Ring interactions

3. **Protection Synergies**
   - Self-bounce for protection
   - Temporary exile to dodge removal

## Future Improvements

1. **Pattern Recognition Enhancement**
   - Better handling of complex multi-trigger effects (Oblivion Ring)
   - Modal spells parsing (Cryptic Command modes)
   - Kicker/overload alternate costs

2. **Additional Mechanics**
   - Sacrifice effects
   - -X/-X effects
   - Phasing/protection
   - Tuck effects (library manipulation)

3. **Performance Optimization**
   - Compile regex patterns once
   - Cache common patterns
   - Batch processing for deck analysis

## Files

- **Implementation**: `src/utils/removal_extractors.py`
- **Tests**: `tests/test_removal_extractors.py`
- **Documentation**: `docs/REMOVAL_EXTRACTORS.md` (this file)
