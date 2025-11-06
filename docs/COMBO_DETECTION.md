# Verified Combo Detection

This document explains the new verified combo detection feature that integrates real combo data from [Commander Spellbook](https://commanderspellbook.com/).

## Overview

The combo detection system identifies **verified combos** in your deck by querying the Commander Spellbook database, which contains over 40,000 documented combos for the Commander/EDH format.

## Features

### 1. Real Combo Data
- **Source**: Commander Spellbook API (https://backend.commanderspellbook.com/)
- **Coverage**: 40,000+ verified combos
- **Accuracy**: Community-maintained, wiki-style database
- **License**: MIT License (open source)

### 2. Visual Indicators

#### Combo Badge
Synergies that are verified combos display a **⚡ COMBO** badge in gold:
- Visible in the card details panel
- Helps distinguish real combos from generic synergies
- Tooltips explain "Verified combo from Commander Spellbook"

#### Combo Edge Styling
Verified combo connections appear as **golden/orange edges** in the graph:
- Color: `#f39c12` (golden orange)
- Width: 5px (thicker than regular synergies)
- Arrow: Triangle arrow pointing to target
- Z-index: Brings combos to the front of the graph

### 3. Detailed Combo Explanations

When you click on a card with combo synergies, you'll see:

- **🃏 All Combo Pieces**: List of all cards required (for 3+ card combos)
- **🎯 Results**: What the combo produces (e.g., "Infinite mana", "Infinite damage")
- **📋 Prerequisites**: Conditions needed before executing the combo
- **🔄 Steps**: Ordered list of actions to execute the combo
- **🔗 Link**: Direct link to Commander Spellbook for full details

### 4. High Priority Synergies

Verified combos are assigned:
- **Category**: `combo`
- **Subcategory**: `verified_combo`
- **Base Value**: 10.0 (very high)
- **Category Weight**: 2.0 (combo category multiplier)
- **Total Weight**: 20.0+ (combos appear at the top of synergy lists)

## How It Works

### 1. Detection Process

When you load a deck:

```
1. Analyze regular synergies (existing rules)
2. Query Commander Spellbook API with deck card list
3. Match combos where all pieces are in the deck
4. Merge combo data into synergy graph
5. Display with special visual treatment
```

### 2. API Integration

**Endpoint**: `POST https://backend.commanderspellbook.com/find-my-combos/`

**Request**:
```json
{
  "cards": "Card Name 1\nCard Name 2\nCard Name 3\n..."
}
```

**Response**:
```json
{
  "results": [
    {
      "id": "12345",
      "uses": [
        {
          "card": {"name": "Card 1", "oracle_id": "..."},
          "zone_locations": ["Battlefield"]
        }
      ],
      "produces": [
        {"feature": {"name": "Infinite mana"}}
      ],
      "requires": [
        {"feature": {"name": "Permanent cards"}}
      ],
      "description": "Step 1...\nStep 2...",
      "identity": "UBR"
    }
  ]
}
```

### 3. Data Models

#### Combo Class
```python
@dataclass
class Combo:
    id: str
    cards: List[ComboCard]
    prerequisites: List[str]
    steps: List[str]
    results: List[str]
    color_identity: str
    permalink: Optional[str]
    mana_needed: Optional[str]
    other_requirements: List[str]
    has_banned_card: bool
    has_spoiled_card: bool
```

#### ComboCard Class
```python
@dataclass
class ComboCard:
    name: str
    oracle_id: Optional[str]
    card_type: Optional[str]
    zone_locations: List[str]  # battlefield, graveyard, command zone, etc.
```

## File Structure

### New Files

- **`src/models/combo.py`**: Data models for combos
- **`src/api/commander_spellbook.py`**: API client for Commander Spellbook
- **`src/synergy_engine/combo_detector.py`**: Combo detection logic
- **`docs/COMBO_DETECTION.md`**: This documentation

### Modified Files

- **`src/synergy_engine/analyzer.py`**: Integrated combo detection
- **`src/utils/graph_builder.py`**: Added combo edge classes
- **`app.py`**: Added combo UI rendering (badges, explanations)

## Usage

### For Users

1. **Load a deck** as normal (Archidekt URL or saved deck)
2. **View the synergy graph** - combo edges appear in golden/orange
3. **Click on a card** - combo synergies show with ⚡ badge
4. **Expand combo details** - see all pieces, results, prerequisites, and steps
5. **Click the link** - view the combo on Commander Spellbook for more info

### For Developers

#### Query Combos Programmatically

```python
from src.api.commander_spellbook import spellbook_api

# Find combos in a deck
card_names = ["Sol Ring", "Basalt Monolith", "Rings of Brighthearth"]
combos = spellbook_api.find_my_combos(card_names)

for combo in combos:
    print(f"Combo: {combo.card_names}")
    print(f"Results: {combo.results}")
    print(f"Steps: {combo.steps}")
```

#### Detect Combos in Deck

```python
from src.synergy_engine.combo_detector import combo_detector

deck_cards = [
    {"name": "Sol Ring", "oracle_text": "..."},
    {"name": "Basalt Monolith", "oracle_text": "..."},
    # ... more cards
]

result = combo_detector.detect_combos_in_deck(deck_cards)

print(f"Complete combos: {len(result['combos'])}")
print(f"Near combos (missing 1-2 cards): {len(result['near_combos'])}")
```

#### Get Combo Suggestions

```python
# Get cards that would complete near-combos
suggestions = combo_detector.get_combo_suggestions(deck_cards, max_missing=1)

for suggestion in suggestions[:5]:
    print(f"Add {suggestion['card_name']}")
    print(f"  Completes: {suggestion['combo'].primary_result}")
    print(f"  With: {suggestion['cards_in_deck']}")
```

## Addressing False Positives

### Before: Generic Combo Detection

The old `detect_combo_potential()` function had issues:

```python
# ❌ Problem: Too broad
if "whenever you cast" in card1_text and "untap" in card2_text:
    return combo_potential  # Often false positive!
```

**Example False Positive**:
- **Cards**: Cornered by Black Mages + Frantic Search
- **Reason**: Both mention combo keywords ("whenever you cast", "untap")
- **Reality**: No actual combo interaction
- **Strength**: 10.00 (misleading!)

### After: Verified Combo Detection

```python
# ✅ Solution: Use real combo database
combos = spellbook_api.find_my_combos(deck_cards)
# Only returns documented, verified combos
```

**Now**:
- Only **documented combos** are flagged
- Generic keyword matching is still used for thematic synergies
- Verified combos get special `⚡ COMBO` badge
- Clear distinction between "synergy" and "combo"

## Configuration

### Disabling Combo Detection

If the API is unavailable or you want to disable combo detection:

```python
# In analyzer.py
COMBO_DETECTION_ENABLED = False
```

The app will gracefully fall back to regular synergy detection.

### API Rate Limiting

The Commander Spellbook API is free and open, but be respectful:
- Cache results using `@lru_cache` (already implemented)
- Batch requests where possible
- Timeout: 30 seconds for find-my-combos
- Max retries: 3 (handled by requests library)

## Examples

### Example 1: Infinite Mana Combo

**Cards**: Basalt Monolith + Rings of Brighthearth

**Detection**:
```
⚡ COMBO badge appears
Golden edge connects the two cards
```

**Details**:
```
🎯 Results:
  • Infinite colorless mana

📋 Prerequisites:
  • Basalt Monolith on the battlefield
  • Rings of Brighthearth on the battlefield

🔄 Steps:
  1. Activate Basalt Monolith's untap ability by paying {3}
  2. Rings of Brighthearth triggers, copying the untap ability
  3. Pay {2} to copy the ability
  4. Resolve both untap abilities
  5. Basalt Monolith is now untapped and you have {3} floating
  6. Repeat for infinite mana

🔗 View on Commander Spellbook
```

### Example 2: 3-Card Combo

**Cards**: Devoted Druid + Vizier of Remedies + Intruder Alarm

**Detection**:
```
All three cards show combo connections
Multiple edges appear in golden/orange
```

**Details**:
```
🃏 All Combo Pieces: Devoted Druid, Vizier of Remedies, Intruder Alarm

🎯 Results:
  • Infinite mana
  • Infinite untap triggers

📋 Prerequisites:
  • All three creatures on the battlefield

🔄 Steps:
  [Detailed step-by-step combo execution]
```

## Troubleshooting

### Combo Not Detected

**Possible reasons**:
1. Combo doesn't exist in Commander Spellbook database
2. Card names don't match exactly (check for typos, special characters)
3. API request failed (check network, logs)
4. Combo requires specific conditions not met

**Solution**: Check the [Commander Spellbook website](https://commanderspellbook.com/) manually

### API Timeout

```
Warning: Combo detection failed: Request timeout
```

**Solution**: API took too long (>30s). Try again or check network connection.

### No Combos Found

This is normal! Not every deck has combos. The detector only reports **documented** combos from the database.

## Future Enhancements

Potential improvements:

1. **Near-Combo Suggestions**: Show cards that would complete combos (missing 1-2 pieces)
2. **Combo Filtering**: Filter graph to show only combo pieces
3. **Combo Statistics**: Track combos by type (infinite mana, infinite damage, etc.)
4. **Local Combo Database**: Cache the entire combo database locally for faster lookups
5. **Custom Combos**: Allow users to add their own undocumented combos

## Credits

- **Commander Spellbook**: https://commanderspellbook.com/
- **API Backend**: https://backend.commanderspellbook.com/
- **GitHub**: https://github.com/SpaceCowMedia/commander-spellbook-backend
- **License**: MIT License

The Commander Spellbook project is community-maintained and powers EDHREC's combo features.

## Changelog

### v2.0.0 - Verified Combo Detection

**Added**:
- Commander Spellbook API integration
- Combo data models (Combo, ComboCard)
- Combo detector with find-my-combos support
- ⚡ COMBO badge UI
- Golden/orange combo edge styling
- Detailed combo explanations (results, prerequisites, steps)
- Links to Commander Spellbook

**Modified**:
- Synergy analyzer to merge combo data
- Graph builder to add verified-combo class
- UI to render combo details with special formatting

**Fixed**:
- False positive combo detection from generic keyword matching
- Misleading high strength scores for non-combos
