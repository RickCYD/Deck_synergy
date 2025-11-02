# Image URIs AttributeError Fix

## Problem

When loading large decks (120+ cards), the graph would fail to render with this error:

```
[UPDATE GRAPH ERROR] Full traceback:
Traceback (most recent call last):
  File "/Users/lucymoreira/projetos/Deck_optimizer/Deck_synergy/app.py", line 703, in update_graph
    elements = build_graph_elements(deck_data)
  File "/Users/lucymoreira/projetos/Deck_optimizer/Deck_synergy/src/utils/graph_builder.py", line 26, in build_graph_elements
    node = create_card_node(card)
  File "/Users/lucymoreira/projetos/Deck_optimizer/Deck_synergy/src/utils/graph_builder.py", line 88, in create_card_node
    'image_url': card.get('image_uris', {}).get('normal', ''),
AttributeError: 'NoneType' object has no attribute 'get'
```

This would cause the error message: **"⚠️ Please load a deck first."** even though the deck was successfully loaded.

## Root Cause

Some cards in the Scryfall API return `'image_uris': None` instead of a dictionary or omitting the field entirely.

When the code tried to do:
```python
card.get('image_uris', {}).get('normal', '')
```

If `card.get('image_uris')` returned `None` (not missing, but explicitly `None`), Python would try to call `.get('normal', '')` on `None`, which causes an `AttributeError`.

**Why this happens:**
- Double-faced cards (MDFCs) may have `image_uris: null` in the API
- Transform cards have images in `card_faces` instead
- Some tokens or special cards don't have standard image URIs

## Solution

Changed the code to handle `None` values gracefully:

**File:** [src/utils/graph_builder.py](src/utils/graph_builder.py:88-89)

**Before (BROKEN):**
```python
'image_url': card.get('image_uris', {}).get('normal', ''),
'art_crop_url': card.get('image_uris', {}).get('art_crop', ''),
```

**After (FIXED):**
```python
'image_url': (card.get('image_uris') or {}).get('normal', ''),
'art_crop_url': (card.get('image_uris') or {}).get('art_crop', ''),
```

### How it works:

1. `card.get('image_uris')` returns the value (could be `dict`, `None`, or nothing)
2. `or {}` converts `None` to an empty dict `{}`
3. `.get('normal', '')` safely gets the image URL or returns empty string

### Test Results:

```python
✓ Test 1 (None):    result = ''
✓ Test 2 (dict):    result = 'https://example.com/image.png'
✓ Test 3 (missing): result = ''
✓ All tests passed!
```

## Impact

This fix resolves the "Please load a deck first" error for large decks that contain:
- Double-faced cards (MDFCs)
- Transform cards
- Split cards
- Adventure cards
- Any card with `image_uris: null` in the API

## Files Modified

1. **src/utils/graph_builder.py** (lines 88-89)
   - Fixed `image_url` field
   - Fixed `art_crop_url` field

## Testing

To test if a card will cause this issue:

```python
# Run in Python shell
from src.api.scryfall import fetch_card_details

# Test with a double-faced card
cards = [{'name': 'Delver of Secrets'}]
details = fetch_card_details(cards)

print("image_uris:", details[0].get('image_uris'))
# If this is None, the old code would crash
```

## Related Issues

This is a common pattern to watch for throughout the codebase. Any time you access nested dictionaries, use:

**BAD:**
```python
card.get('field', {}).get('subfield')  # Fails if field is None
```

**GOOD:**
```python
(card.get('field') or {}).get('subfield')  # Safe with None
```

**ALSO GOOD:**
```python
field = card.get('field')
if field:
    subfield = field.get('subfield')
```

## Summary

The large deck loading issue was caused by a single `AttributeError` when processing card images. The fix ensures that `None` values are handled gracefully, allowing all decks (including those with special card types) to load successfully.

**Status:** ✅ FIXED - Large decks should now load and display correctly.
