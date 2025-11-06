# Three-Way Synergies

This document explains the three-way synergy detection system that identifies synergies requiring 3 specific cards to work together.

## Overview

While most synergies involve 2 cards (pairwise), some powerful interactions require 3 cards present simultaneously. The three-way synergy system detects these triangular relationships.

## Detected Patterns

### 1. Equipment Engine
**Pattern**: Equipment + Creature + Equipment Matters

**Example**: Sword of Fire and Ice + Equipped Creature + Bruenor Battlehammer

**Description**: An equipment piece, a creature to equip it to, and a card that provides additional value for equipped creatures (like Bruenor giving +2/+0 and double strike).

### 2. Aristocrats Engine
**Pattern**: Token Generator + Sacrifice Outlet + Death Payoff

**Example**: Tendershoot Dryad + Ashnod's Altar + Blood Artist

**Description**: Creates tokens, has a way to sacrifice them, and gets value whenever creatures die.

### 3. ETB Value Engine
**Pattern**: ETB Creature + Flicker Effect + ETB Multiplier

**Example**: Mulldrifter + Ephemerate + Panharmonicon

**Description**: A creature with enters-the-battlefield trigger, a way to flicker it, and a card that doubles ETB triggers.

### 4. Reanimator Engine
**Pattern**: Mill/Entomb + Reanimate + Big Creature

**Example**: Entomb + Animate Dead + Elesh Norn

**Description**: A way to put creatures in the graveyard, a reanimation spell, and a high-value creature (CMC 6+) to reanimate.

### 5. Spellslinger Engine
**Pattern**: Cost Reducer + Cantrip + Spell Payoff

**Example**: Baral + Brainstorm + Aetherflux Reservoir

**Description**: Reduces spell costs, cheap spells to cast, and payoffs that trigger on spell casts.

### 6. Tap/Untap Engine
**Pattern**: Tap for Value + Untapper + Additional Untapper

**Example**: Gilded Lotus + Seedborn Muse + Unwinding Clock

**Description**: A permanent with a tap ability that generates value, plus multiple ways to untap it.

### 7. Discard Value Engine
**Pattern**: Draw Spell + Discard Synergy + Madness/Flashback

**Example**: Wheel of Fortune + Containment Construct + Flashback Spell

**Description**: Drawing cards, getting value from discarding, and cards that want to be discarded (madness, flashback, etc.).

## Visual Representation

### Triangular Edges
Three-way synergies are visualized as **triangular connections** in the graph:

```
    Card1
    /   \
   /  3  \
  /_______\
Card2 --- Card3
```

Each three-way synergy creates 3 dashed purple edges forming a triangle.

### Styling
- **Color**: Purple (`#9b59b6`)
- **Style**: Dashed lines
- **Width**: 4px
- **Opacity**: 0.7
- **Z-Index**: 50 (below combos, above regular synergies)

## Data Structure

Three-way synergies are stored separately from two-way synergies:

```python
{
    'two_way': {
        'Card1||Card2': {...}
    },
    'three_way': {
        'Card1||Card2||Card3': {
            'card1': 'Card1',
            'card2': 'Card2',
            'card3': 'Card3',
            'total_weight': 5.5,
            'synergies': {
                'type_synergy': [{
                    'name': 'Equipment Engine',
                    'description': '...',
                    'value': 5.0,
                    'category': 'type_synergy',
                    'subcategory': 'equipment_engine',
                    'cards': ['Card1', 'Card2', 'Card3']
                }]
            },
            'synergy_count': 1
        }
    }
}
```

## Usage

### Enabling Three-Way Detection

By default, three-way synergies are detected:

```python
from src.synergy_engine.analyzer import analyze_deck_synergies

# With three-way synergies (default)
result = analyze_deck_synergies(cards, include_three_way=True)

# two_way and three_way synergies
two_way = result['two_way']
three_way = result['three_way']
```

### Disabling for Performance

For large decks (100+ cards), three-way detection can be slow:

```python
# Disable for faster analysis
result = analyze_deck_synergies(cards, include_three_way=False)

# Returns only two_way synergies (backward compatible)
synergies = result  # Just the two_way dict
```

## Performance

### Complexity
- **Two-way**: O(n²) - checks all pairs
- **Three-way**: O(n³) - checks all triplets

### Example Times
For a 100-card deck (excluding lands):
- **Two-way**: ~12 seconds
- **Three-way**: ~30 seconds

For decks > 60 non-land cards, the system automatically limits analysis to prevent excessive wait times.

## API Reference

### Functions

#### `analyze_card_triple(card1, card2, card3)`
Detect synergies between three cards.

**Returns**: List of three-way synergy dictionaries

#### `analyze_three_way_synergies(cards, min_synergy_threshold)`
Analyze all three-card combinations in a deck.

**Args**:
- `cards`: List of card dictionaries
- `min_synergy_threshold`: Minimum strength to include (default: 0.5)

**Returns**: Dictionary mapping triplets to synergies

### Detection Rules

All rules are in `src/synergy_engine/three_way_synergies.py`:

```python
THREE_WAY_SYNERGY_RULES = [
    detect_equipment_matters_three_way,
    detect_token_aristocrats_three_way,
    detect_etb_flicker_payoff_three_way,
    detect_mill_reanimate_target_three_way,
    detect_cost_reducer_cantrip_payoff_three_way,
    detect_tap_untap_combo_three_way,
    detect_draw_discard_madness_three_way
]
```

## Examples

### Equipment Engine

**Cards**:
- Colossus Hammer (Equipment)
- Equipped Creature
- Bruenor Battlehammer (Equipment matters)

**Synergy**:
```
Name: Equipment Engine
Description: Colossus Hammer equips Creature, Bruenor Battlehammer
             provides additional value for equipped creatures
Value: 5.0
Category: type_synergy
Subcategory: equipment_engine
```

### Aristocrats Engine

**Cards**:
- Tendershoot Dryad (Creates Saproling tokens)
- Ashnod's Altar (Sacrifice for mana)
- Blood Artist (Drains on death)

**Synergy**:
```
Name: Aristocrats Engine
Description: Tendershoot Dryad creates tokens, Ashnod's Altar
             sacrifices them, Blood Artist triggers on each death
Value: 6.0
Category: role_interaction
Subcategory: aristocrats_engine
```

## Graph Highlighting

### Clicking a Card in a Three-Way Synergy

When you click a card that's part of a three-way synergy:

1. **All 3 edges light up** (the triangle)
2. **All 3 cards are highlighted**
3. **Synergy details show** the three-way engine explanation

### Finding Three-Way Synergies

In the card details panel, three-way synergies are displayed with a special indicator:

```
🔺 Three-Way Synergy (3 cards)

Cards: Card1, Card2, Card3
Synergy: Equipment Engine
Strength: 5.5
```

## Adding New Three-Way Patterns

To add a new three-way synergy pattern:

1. **Create a detection function** in `three_way_synergies.py`:

```python
def detect_my_new_pattern(card1: Dict, card2: Dict, card3: Dict) -> Optional[Dict]:
    """
    Detect [Your Pattern]
    Example: [Example cards]

    Pattern: [Description]
    """
    # Identify the roles
    piece_a = None
    piece_b = None
    piece_c = None

    for card in [card1, card2, card3]:
        card_text = card.get('oracle_text', '').lower()

        # Check for piece A
        if re.search(r'pattern_a', card_text):
            piece_a = card

        # Check for piece B
        if re.search(r'pattern_b', card_text):
            piece_b = card

        # Check for piece C
        if re.search(r'pattern_c', card_text):
            piece_c = card

    # All three pieces must be present
    if piece_a and piece_b and piece_c:
        return {
            'name': 'My Engine Name',
            'description': f"{piece_a['name']} does X, {piece_b['name']} does Y, {piece_c['name']} provides Z",
            'value': 5.5,  # Strength value
            'category': 'role_interaction',
            'subcategory': 'my_engine',
            'cards': [piece_a['name'], piece_b['name'], piece_c['name']]
        }

    return None
```

2. **Add to the rules list**:

```python
THREE_WAY_SYNERGY_RULES = [
    # ... existing rules ...
    detect_my_new_pattern
]
```

## Troubleshooting

### No Three-Way Synergies Detected

**Possible reasons**:
1. `include_three_way=False` in analyzer call
2. No matching patterns in the deck
3. Strength below threshold (0.5)

**Solution**: Check the console output for "Detecting three-way synergies..." message

### Analysis Takes Too Long

**Problem**: Three-way detection is slow for large decks

**Solution**: Reduce the deck size or disable three-way detection:
```python
result = analyze_deck_synergies(cards, include_three_way=False)
```

### Triangle Not Showing in Graph

**Problem**: Three-way edges not visible

**Possible causes**:
1. Graph layout obscuring edges
2. Cards too far apart

**Solution**:
- Try different layout (force-directed layouts work best)
- Zoom in to see dashed purple edges

## Future Enhancements

Potential improvements:

1. **Four-Way Synergies**: Extend to 4-card combinations
2. **Smart Detection**: Use AI to identify patterns automatically
3. **User-Defined Patterns**: Allow custom three-way synergy rules
4. **Hyperedge Nodes**: Create special nodes for three-way synergies
5. **Performance**: Parallel processing for O(n³) combinations
6. **Filtering**: Show only three-way synergies in graph view

## Comparison: Two-Way vs Three-Way

| Aspect | Two-Way | Three-Way |
|--------|---------|-----------|
| **Cards** | 2 cards | 3 cards |
| **Edges** | 1 edge | 3 edges (triangle) |
| **Color** | Red gradient | Purple |
| **Style** | Solid | Dashed |
| **Complexity** | O(n²) | O(n³) |
| **Typical Count** | 100-300 | 5-20 |
| **Examples** | Equipment + Tutor | Equipment + Creature + Matters |

## Changelog

### v2.1.0 - Three-Way Synergies

**Added**:
- 7 three-way synergy detection patterns
- Triangular edge visualization (purple, dashed)
- `analyze_card_triple()` function
- `analyze_three_way_synergies()` function
- `create_three_way_edges()` for graph visualization
- `three_way_synergies` field in Deck model
- `include_three_way` parameter in `analyze_deck_synergies()`

**Modified**:
- `analyze_deck_synergies()` now returns dict with 'two_way' and 'three_way' keys
- Graph builder handles three-way synergies
- Stylesheet includes three-way synergy styling

**Files Created**:
- `src/synergy_engine/three_way_synergies.py`
- `docs/THREE_WAY_SYNERGIES.md`

**Files Modified**:
- `src/synergy_engine/analyzer.py`
- `src/models/deck.py`
- `src/utils/graph_builder.py`
- `app.py`
