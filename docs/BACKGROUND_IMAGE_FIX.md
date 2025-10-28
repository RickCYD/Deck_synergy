# Background Image CSS Fix

## Problem

Despite fixing null values in node data, Cytoscape was still crashing with:

```
[Warning] The style property `background-image: ` is invalid
[Error] TypeError: null is not an object (evaluating 'p.value')
  at cytoscape.cjs.js:17412
```

## Root Cause

The stylesheet was applying `background-image: data(art_crop_url)` to ALL nodes. When a card had NO image (empty string `''`), Cytoscape generated invalid CSS:

```css
background-image: ;  /* INVALID - missing value */
```

This invalid CSS causes Cytoscape's style parser to crash when trying to process the style object.

## The Specific Issue

**In app.py stylesheet:**
```python
{
    'selector': 'node',
    'style': {
        'background-image': 'data(art_crop_url)',  # ❌ Applied to ALL nodes
        # ...
    }
}
```

**When art_crop_url is empty string:**
- Node data: `{ ..., 'art_crop_url': '' }`
- Generated CSS: `background-image: ` ← **INVALID!**
- Result: Cytoscape crashes

## Solution

**Two-part fix:**

### Part 1: Conditional Stylesheet ([app.py:84-89](app.py:84-89))

**Before:**
```python
{
    'selector': 'node',
    'style': {
        'background-image': 'data(art_crop_url)',  # Applied to all
        # ...
    }
}
```

**After:**
```python
{
    'selector': 'node',
    'style': {
        # Don't set background-image in base style
        # ...
    }
},
{
    'selector': 'node[art_crop_url]',  # Only nodes WITH art_crop_url
    'style': {
        'background-image': 'data(art_crop_url)'
    }
}
```

### Part 2: Omit Empty Properties ([src/utils/graph_builder.py:141-145](src/utils/graph_builder.py:141-145))

**Before:**
```python
node_data = {
    # ...
    'art_crop_url': (card.get('image_uris') or {}).get('art_crop', '') or '',
    # ❌ Always includes property, even if empty string
}
```

**After:**
```python
# Get image URLs
image_uris = card.get('image_uris') or {}
art_crop_url = image_uris.get('art_crop', '') or image_uris.get('normal', '') or ''
image_url = image_uris.get('normal', '') or ''

node_data = {
    # ... other properties ...
}

# Only add image URLs if they're not empty
if image_url:
    node_data['image_url'] = image_url
if art_crop_url:
    node_data['art_crop_url'] = art_crop_url
```

## How It Works Now

**Card WITH image:**
```python
node_data = {
    'id': 'Lightning Bolt',
    'art_crop_url': 'https://...image.png',  # ✅ Property exists
    # ...
}
```
- Matches selector: `node[art_crop_url]`
- CSS applied: `background-image: url(https://...image.png)` ✅

**Card WITHOUT image:**
```python
node_data = {
    'id': 'Unknown Card',
    # art_crop_url property NOT included
    # ...
}
```
- Does NOT match selector: `node[art_crop_url]`
- NO background-image CSS applied ✅
- Shows just the color background ✅

## Why This Pattern Works

Cytoscape selectors work like CSS attribute selectors:
- `node` - matches all nodes
- `node[art_crop_url]` - matches nodes that HAVE the `art_crop_url` property
- `node[art_crop_url=""]` - would match nodes where property is empty string

By omitting the property entirely when empty, we ensure the selector doesn't match, preventing invalid CSS from being generated.

## Cards Affected

Cards typically without images:
- Tokens (may not have Scryfall images)
- Double-faced cards (images in `card_faces` instead)
- Custom/proxy cards
- API errors during card fetch

All these cards now display correctly with just their color background instead of crashing the graph.

## Testing

To verify the fix:

1. Look for the warning in browser console - should NOT appear:
   ```
   ❌ [Warning] The style property `background-image: ` is invalid
   ```

2. Check terminal output - should see cards created without errors:
   ```
   [GRAPH BUILDER] Created 157 nodes
   [UPDATE GRAPH] SUCCESS - Graph updated!
   ```

3. Graph should display with:
   - Cards WITH images: show artwork ✅
   - Cards WITHOUT images: show just color background ✅
   - No crashes ✅

## Related Files Changed

1. **app.py (lines 84-89)** - Split node style into base + conditional image style
2. **src/utils/graph_builder.py (lines 107-145)** - Omit empty image URLs from node data

## Summary

The crash was caused by Cytoscape trying to apply invalid CSS `background-image: ` (missing value). The fix:
1. Only apply background-image style to nodes that have the property
2. Only include the property in node data if it's not empty

This prevents invalid CSS from being generated while still displaying images for cards that have them.

**Status:** ✅ FIXED - Graph should now render without "background-image" errors.
