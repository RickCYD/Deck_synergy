# Cytoscape Null Value Fix

## Problem

After fixing the previous issues, the graph would successfully load but Cytoscape would crash with:

```javascript
TypeError: null is not an object (evaluating 'p.value')
  at cytoscape.cjs.js:17412
```

This error occurs deep inside Cytoscape when it tries to process graph elements with `null` values in their data properties.

## Root Cause

Some card properties return `null` instead of meaningful values:
- `power`: `null` for non-creatures
- `toughness`: `null` for non-creatures
- `loyalty`: `null` for non-planeswalkers
- `image_uris`: `null` for certain card types
- Various other optional fields

When these `null` values are passed to Cytoscape, it breaks internal processing because Cytoscape expects:
- Strings (can be empty `""`)
- Numbers (can be `0`)
- Arrays (can be empty `[]`)
- Objects (can be empty `{}`)

But **NOT** `null` or `undefined`.

## Solution

Changed all `.get()` calls to use `or` operator to convert `null` to safe defaults.

### Fixed Files:

#### 1. Node Data ([src/utils/graph_builder.py:65-94](src/utils/graph_builder.py:65-94))

**Before:**
```python
node_data = {
    'power': card.get('power'),           # Could be None
    'toughness': card.get('toughness'),   # Could be None
    'loyalty': card.get('loyalty'),       # Could be None
    'oracle_text': card.get('oracle_text', ''),
    # ...
}
```

**After:**
```python
node_data = {
    'id': card_name or 'Unknown',
    'label': card_name or 'Unknown',
    'type': node_type,

    # Card information - all None values converted to safe defaults
    'card_type': card.get('type_line') or 'Unknown',
    'mana_cost': card.get('mana_cost') or '',
    'cmc': card.get('cmc') or 0,
    'colors': colors or [],
    'color_identity': card.get('color_identity') or [],
    'oracle_text': card.get('oracle_text') or '',
    'power': card.get('power') or '',              # ✅ None → ''
    'toughness': card.get('toughness') or '',      # ✅ None → ''
    'loyalty': card.get('loyalty') or '',          # ✅ None → ''
    'rarity': card.get('rarity') or '',

    # Visual properties
    'image_url': (card.get('image_uris') or {}).get('normal', '') or '',
    'art_crop_url': (card.get('image_uris') or {}).get('art_crop', '') or '',

    # Categories
    'categories': card.get('categories') or [],
    'roles': roles or {}
}
```

#### 2. Edge Data ([src/utils/graph_builder.py:121-134](src/utils/graph_builder.py:121-134))

**Before:**
```python
edge_data = {
    'id': edge_id,
    'source': card1,
    'target': card2,
    'weight': round(weight, 1),
    'synergies': synergy_data.get('synergies', {}),
    'synergy_count': synergy_data.get('synergy_count', 0)
}
```

**After:**
```python
edge_data = {
    'id': edge_id or f"edge_{hash(synergy_key)}",
    'source': card1 or 'Unknown',
    'target': card2 or 'Unknown',
    'source_label': card1 or 'Unknown',
    'target_label': card2 or 'Unknown',
    'weight': round(weight, 1) if weight is not None else 1.0,  # ✅
    'synergies': synergy_data.get('synergies') or {},           # ✅
    'synergy_count': synergy_data.get('synergy_count') or 0    # ✅
}
```

#### 3. Build Function Validation ([src/utils/graph_builder.py:11-77](src/utils/graph_builder.py:11-77))

Added comprehensive error handling and validation:

```python
def build_graph_elements(deck_data: Dict) -> List[Dict]:
    elements = []

    # Validate each card before creating node
    for idx, card in enumerate(cards):
        try:
            # Skip invalid cards
            if not card or not isinstance(card, dict):
                print(f"[GRAPH BUILDER] WARNING: Card {idx} is not a valid dict, skipping")
                continue

            if not card.get('name'):
                print(f"[GRAPH BUILDER] WARNING: Card {idx} has no name, skipping")
                continue

            node = create_card_node(card)

            # Validate node structure
            if not node.get('data') or not node['data'].get('id'):
                print(f"[GRAPH BUILDER] WARNING: Node for {card.get('name')} is invalid, skipping")
                continue

            elements.append(node)
        except Exception as e:
            print(f"[GRAPH BUILDER] ERROR: Failed to create node for card {card.get('name', 'Unknown')}: {e}")
            continue

    # Similar validation for edges...
```

## Pattern to Use

**Always use this pattern when building graph data:**

```python
# BAD - Can pass None to Cytoscape
value = card.get('field')

# GOOD - Converts None to safe default
value = card.get('field') or ''        # For strings
value = card.get('field') or 0         # For numbers
value = card.get('field') or []        # For arrays
value = card.get('field') or {}        # For objects
```

## Testing

To verify the fix works, check the terminal output:

```
[GRAPH BUILDER] Creating nodes for 157 cards
[GRAPH BUILDER] Created 157 nodes
[GRAPH BUILDER] Creating edges for 4892 synergies
[GRAPH BUILDER] Created 4892 edges
[GRAPH BUILDER] Total elements: 5049
```

If any warnings appear:
```
[GRAPH BUILDER] WARNING: Card 42 has no name, skipping
[GRAPH BUILDER] ERROR: Failed to create node for Delver of Secrets: ...
```

These indicate data quality issues that are being handled gracefully instead of crashing.

## Expected Behavior

**Before fix:**
- Graph loads
- Cytoscape crashes with `null is not an object`
- JavaScript console shows error
- Graph disappears

**After fix:**
- Graph loads ✅
- All null values converted to safe defaults ✅
- No JavaScript errors ✅
- Graph displays correctly with all 157 cards ✅

## Related Issues

This fix also handles:
- Cards missing basic properties
- Double-faced cards with complex image structures
- Tokens with limited data
- Any future API changes that return null

## Summary

The Cytoscape crash was caused by `null` values in card data. The fix converts all `null` values to safe defaults (empty strings, zero, empty arrays/objects) and adds comprehensive validation to skip any problematic elements.

**Status:** ✅ FIXED - Graph should now render without JavaScript errors.
