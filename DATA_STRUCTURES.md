# Data Structure Reference

This document defines the canonical data structures used throughout the MTG Commander Deck Synergy Visualizer.

## Table of Contents
- [Card Structure](#card-structure)
- [Synergy Structure](#synergy-structure)
- [Deck Structure](#deck-structure)
- [Graph Elements](#graph-elements)

---

## Card Structure

### Canonical Card Format

```python
{
    # Core Identification
    'name': str,                    # Card name (required)
    'scryfall_id': str | None,      # Scryfall UUID (optional, from API only)

    # Archidekt Metadata
    'quantity': int,                # Number of copies (default: 1)
    'categories': list[str],        # Archidekt categories
    'is_commander': bool,           # Is this the commander? (default: False)

    # Mana Information
    'mana_cost': str,               # Mana cost string (e.g., "{2}{U}{B}")
    'cmc': float,                   # Converted mana cost
    'colors': list[str],            # Color array (e.g., ['U', 'B'])
    'color_identity': list[str],    # Color identity (e.g., ['U', 'B', 'G'])
    'produced_mana': list[str],     # Mana this card can produce

    # Type Information
    'type_line': str,               # Full type line
    'card_types': dict,             # Parsed types (see Card Types below)
    'supertypes': list[str],        # Supertypes (e.g., ['Legendary'])
    'subtypes': list[str],          # Subtypes (e.g., ['Zombie', 'Wizard'])

    # Card Text
    'oracle_text': str,             # Oracle rules text
    'keywords': list[str],          # Keyword abilities

    # Stats
    'power': str | None,            # Power (for creatures)
    'toughness': str | None,        # Toughness (for creatures)
    'loyalty': str | None,          # Loyalty (for planeswalkers)

    # Images
    'image_uris': dict | None,      # Image URLs (see Image URIs below)

    # Metadata (from API only)
    'rarity': str | None,           # Card rarity
    'set': str | None,              # Set code
    'set_name': str | None,         # Set name
    'prices': dict,                 # Price data
    'legalities': dict,             # Format legalities
    'edhrec_rank': int | None,      # EDHREC rank

    # Roles (computed)
    'roles': list[str],             # Functional roles (see Roles below)

    # Internal
    '_from_local_cache': bool,      # True if from local cache
    '_scryfall_raw': dict | None,   # Raw Scryfall data (API only)
    'error': str | None             # Error message if fetch failed
}
```

### Card Types Structure

```python
{
    'supertypes': list[str],  # e.g., ['Legendary']
    'main_types': list[str],  # e.g., ['Creature', 'Artifact']
    'subtypes': list[str]     # e.g., ['Zombie', 'Wizard']
}
```

### Image URIs Structure

```python
{
    'art_crop': str | None  # URL to cropped artwork
}
```

### Functional Roles

Valid role values:
- `'ramp'` - Mana acceleration
- `'color_correction'` - Basic land fetching for color fixing
- `'draw'` - Card draw
- `'removal'` - Single target removal
- `'board_wipe'` - Mass removal
- `'protection'` - Protects permanents
- `'finisher'` - Win conditions
- `'tutor'` - Library search
- `'recursion'` - Graveyard retrieval
- `'combo_piece'` - Combo enabler
- `'stax'` - Tax/restriction effects

---

## Synergy Structure

### ⚠️ IMPORTANT: Synergies Dictionary Format

**THE CANONICAL FORMAT** for `deck.synergies` is a **DICTIONARY** mapping card pair keys to synergy data:

```python
synergies: dict[str, dict] = {
    "Card A||Card B": {
        'card1': str,              # First card name
        'card2': str,              # Second card name
        'total_weight': float,     # Sum of weighted synergy values
        'synergies': dict,         # Organized by category (see below)
        'synergy_count': int       # Total number of synergy instances
    }
}
```

### Synergies Nested Structure

```python
'synergies': {
    'category_name': [
        {
            'name': str,           # Synergy name (e.g., "ETB Trigger Synergy")
            'description': str,    # Human-readable description
            'value': float,        # Base synergy strength (1.0-10.0)
            'category': str,       # Category (see Categories below)
            'subcategory': str | None  # Optional subcategory
        },
        ...
    ],
    ...
}
```

### Synergy Categories

Valid category values:
- `'triggers'` - ETB, LTB, death triggers
- `'benefits'` - Generic beneficial interactions
- `'combo'` - Combo pieces
- `'tribal'` - Tribal synergies
- `'themes'` - Thematic synergies (counters, tokens, etc.)
- `'role_interactions'` - Role-based synergies
- `'other'` - Miscellaneous

### Synergy Subcategories

Examples by category:
- **triggers**: `'etb_trigger'`, `'death_trigger'`, `'ltb_trigger'`
- **combo**: `'infinite_mana'`, `'infinite_combo'`
- **tribal**: `'elf'`, `'goblin'`, `'zombie'`, etc.
- **themes**: `'sacrifice'`, `'graveyard'`, `'tokens'`, `'counters'`
- **role_interactions**: `'ramp_draw'`, `'sacrifice_tokens'`

---

## Deck Structure

### Deck JSON File Format

```python
{
    'deck_id': str,          # Unique deck ID (from Archidekt)
    'name': str,             # Deck name
    'cards': list[Card],     # List of card dictionaries (see Card Structure)
    'synergies': dict,       # Synergies dictionary (see Synergy Structure)
    'metadata': dict         # Additional metadata (see Metadata below)
}
```

### Metadata Structure

```python
{
    'created_at': str,    # ISO timestamp
    'updated_at': str,    # ISO timestamp
    # Add custom metadata as needed
}
```

---

## Graph Elements

### Cytoscape Graph Format

The graph uses Cytoscape.js format with nodes and edges.

### Node Element

```python
{
    'data': {
        'id': str,              # Unique node ID (card name)
        'label': str,           # Display label (card name)
        'type': str,            # 'commander' or 'card'
        'color_code': str,      # Background color code
        'border_color': str,    # Border color code
        'is_multicolor': bool,  # Has multiple colors?
        'art_crop_url': str,    # URL to card art
        'card_data': dict       # Full card data
    }
}
```

### Edge Element

```python
{
    'data': {
        'source': str,          # Source card name
        'target': str,          # Target card name
        'weight': float,        # Synergy weight (for styling)
        'synergies': dict,      # Synergy data (organized by category)
        'synergy_count': int    # Number of synergies
    }
}
```

---

## Data Validation Rules

### Rule 1: Synergies Must Be a Dictionary

✅ **CORRECT**:
```python
deck_obj['synergies'] = {
    "Sol Ring||Arcane Signet": {
        'card1': 'Sol Ring',
        'card2': 'Arcane Signet',
        'total_weight': 2.5,
        'synergies': {...},
        'synergy_count': 1
    }
}
```

❌ **WRONG**:
```python
deck_obj['synergies'] = [
    "Sol Ring||Arcane Signet"  # Never use a list!
]
```

### Rule 2: Always Check Dictionary Types

When iterating over synergies:

✅ **CORRECT**:
```python
for key, synergy_data in deck_obj.get('synergies', {}).items():
    if isinstance(synergy_data, dict):
        card1 = synergy_data.get('card1')
        card2 = synergy_data.get('card2')
        strength = synergy_data.get('total_weight', 0)
```

❌ **WRONG**:
```python
for synergy in deck_obj.get('synergies', []):
    # Assumes synergies is a list - WRONG!
    card1 = synergy.get('card1')  # Will fail if synergy is a string
```

### Rule 3: Card Must Have a Name

Every card **must** have a `'name'` key:

```python
card_name = card.get('name')
if not card_name:
    # Skip or log error
    continue
```

### Rule 4: Validate Data on Load

Always validate when loading from files:

```python
def validate_deck_data(deck_data: dict) -> bool:
    """Validate deck data structure"""
    if not isinstance(deck_data.get('synergies'), dict):
        print(f"ERROR: synergies must be a dict, got {type(deck_data.get('synergies'))}")
        return False

    if not isinstance(deck_data.get('cards'), list):
        print(f"ERROR: cards must be a list, got {type(deck_data.get('cards'))}")
        return False

    return True
```

---

## Common Pitfalls

### Pitfall 1: Mixing List and Dict for Synergies

**Problem**: Old code used `deck.add_synergy()` which stored synergies as lists, but `analyze_deck_synergies()` returns a dict.

**Solution**: Always use the dict format from `analyze_deck_synergies()`. The `add_synergy()` method is deprecated.

### Pitfall 2: Assuming Synergies Exist

**Problem**: Accessing `deck_obj['synergies']` without checking if it exists.

**Solution**: Always use `.get()` with a default:
```python
synergies = deck_obj.get('synergies', {})
```

### Pitfall 3: Not Validating Types

**Problem**: Assuming data is always the correct type.

**Solution**: Use `isinstance()` checks:
```python
if isinstance(synergy_data, dict):
    # Safe to use .get()
```

---

## Migration Notes

### From Old Format to New Format

If you have old deck files with synergies as lists, migrate them:

```python
def migrate_synergies(old_deck_data):
    """Migrate old synergy format to new format"""
    old_synergies = old_deck_data.get('synergies', [])

    if isinstance(old_synergies, list):
        # Need to re-analyze the deck
        from src.synergy_engine.analyzer import analyze_deck_synergies
        new_synergies = analyze_deck_synergies(old_deck_data['cards'])
        old_deck_data['synergies'] = new_synergies

    return old_deck_data
```

---

## Testing Data Integrity

### Unit Test Template

```python
def test_deck_data_structure():
    """Test deck data structure integrity"""
    deck_data = load_deck_from_file('test_deck.json')

    # Test cards is a list
    assert isinstance(deck_data['cards'], list)

    # Test synergies is a dict
    assert isinstance(deck_data['synergies'], dict)

    # Test each synergy value is a dict
    for key, synergy_data in deck_data['synergies'].items():
        assert isinstance(synergy_data, dict)
        assert 'card1' in synergy_data
        assert 'card2' in synergy_data
        assert 'total_weight' in synergy_data

    # Test each card has a name
    for card in deck_data['cards']:
        assert 'name' in card
        assert isinstance(card['name'], str)
```

---

## Version History

- **v1.0** (2025-10-27): Initial data structure documentation
- Defined canonical formats for cards, synergies, and decks
- Documented common pitfalls and validation rules

---

**Last Updated**: 2025-10-27
**Maintainer**: Claude Code
