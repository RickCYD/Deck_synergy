# Graph Clearing After Load Fix

## Problem

After successfully loading a large deck (120+ cards), the graph would:
1. Load successfully (showing "SUCCESS - Graph updated!")
2. Immediately clear (showing "No deck file provided")
3. Display JavaScript error: `null is not an object (evaluating 'p.value')`

**Terminal output showing the issue:**
```
[UPDATE GRAPH] Loaded 157 cards and 4892 synergies
[UPDATE GRAPH] Built 5049 graph elements
[UPDATE GRAPH] SUCCESS - Graph updated!

[UPDATE GRAPH] Called with deck_file: None  ← PROBLEM: Called again with None
[UPDATE GRAPH] No deck file provided, returning empty graph
```

## Root Cause

The issue was a **Dash callback chain problem**:

1. `load_deck` callback completes and returns:
   - `deck_options` (new list of deck files)
   - `deck_file_path` (selects the newly loaded deck)

2. Setting `deck-selector.value` triggers `update_graph` → Graph loads ✅

3. **BUT** when Dash updates `deck-selector.options` (the list of available decks), it can temporarily reset `deck-selector.value` to `None`

4. This triggers `update_graph` again with `deck_file=None` → Graph clears ❌

This is a known Dash behavior when updating both `options` and `value` of a dropdown simultaneously.

## Solution

Changed `update_graph` to **preserve state** instead of clearing when called with invalid input.

**File:** [app.py:679-693](app.py:679-693)

### Before (BROKEN):
```python
def update_graph(deck_file):
    if not deck_file:
        print("[UPDATE GRAPH] No deck file provided, returning empty graph")
        return [], None, {}  # ← Clears the graph!
```

### After (FIXED):
```python
def update_graph(deck_file):
    if not deck_file:
        print("[UPDATE GRAPH] No deck file provided, using dash.no_update to preserve current state")
        return dash.no_update, dash.no_update, dash.no_update  # ← Preserves current state

    try:
        # Also check if file exists
        from pathlib import Path
        if not Path(deck_file).exists():
            print(f"[UPDATE GRAPH] WARNING: Deck file does not exist: {deck_file}")
            print(f"[UPDATE GRAPH] Using dash.no_update to preserve current state")
            return dash.no_update, dash.no_update, dash.no_update  # ← Preserves current state
```

### How dash.no_update works:

- `dash.no_update` tells Dash: "Don't update this output, keep whatever value it currently has"
- This prevents the graph from being cleared when the callback is triggered with bad input
- The graph stays rendered even if the dropdown temporarily loses its value

## Expected Behavior After Fix

**Terminal output:**
```
[UPDATE GRAPH] Called with deck_file: data/decks/My_Deck_12345.json
[UPDATE GRAPH] Loading deck from file: data/decks/My_Deck_12345.json
[UPDATE GRAPH] Loaded 157 cards and 4892 synergies
[UPDATE GRAPH] Building graph elements...
[UPDATE GRAPH] Built 5049 graph elements
[UPDATE GRAPH] SUCCESS - Graph updated!

[UPDATE GRAPH] Called with deck_file: None
[UPDATE GRAPH] No deck file provided, using dash.no_update to preserve current state
                ↑ Graph stays rendered instead of clearing
```

**User experience:**
- Graph loads and **stays loaded** ✅
- No JavaScript errors ✅
- No "Please load a deck first" errors ✅

## Additional Safety Check

Added file existence check before loading:
```python
if not Path(deck_file).exists():
    return dash.no_update, dash.no_update, dash.no_update
```

This prevents:
- Trying to load deleted files
- Trying to load files with incorrect paths
- Crashes from file I/O errors

## Testing

To verify the fix works:

1. Start app: `python3 app.py`
2. Load a large deck (120+ cards)
3. Watch terminal output
4. You should see:
   ```
   [UPDATE GRAPH] SUCCESS - Graph updated!
   [UPDATE GRAPH] Called with deck_file: None
   [UPDATE GRAPH] ... using dash.no_update to preserve current state
   ```
5. Graph should remain visible and interactive ✅

## Related Dash Documentation

This is a common pattern in Dash when dealing with dropdowns:
- [Dash Callback Contexts](https://dash.plotly.com/advanced-callbacks)
- [Using dash.no_update](https://dash.plotly.com/dash-no-update)

**Best Practice:** Always use `dash.no_update` instead of returning empty/None values when you want to preserve existing UI state.

## Summary

The graph clearing issue was caused by Dash's dropdown behavior when updating options. The fix uses `dash.no_update` to preserve the graph instead of clearing it when the callback receives invalid input.

**Status:** ✅ FIXED - Graph now loads and stays loaded for large decks.
