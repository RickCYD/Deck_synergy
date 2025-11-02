# Debugging Large Deck Loading Issues

## Problem
When loading decks with 120+ cards, you may see:
- ⚠️ "Please load a deck first" error
- Graph does not load
- Deck appears to load but nothing happens

## Debug Steps

### 1. Check Terminal Output

With the new logging added, you should see detailed output in your terminal when loading a deck:

```
[DECK LOAD] Starting to load deck from URL: https://archidekt.com/decks/...
[DECK LOAD] Step 1: Fetching from Archidekt...
[DECK LOAD] Got deck: My Deck with 120 cards
[DECK LOAD] Step 2: Fetching card details from Scryfall...
[DECK LOAD] Fetched details for 120 cards
[DECK LOAD] Step 3: Assigning roles...
[DECK LOAD] Step 4: Creating deck object...
[DECK LOAD] Step 5: Analyzing synergies for 120 cards...
[DECK LOAD] This may take 1-2 minutes for large decks. Please wait...

Analyzing synergies for 120 cards...
  Progress: 500/7140 pairs (7.0%) - Elapsed: 5.2s - ETA: 68.8s
  Progress: 1000/7140 pairs (14.0%) - Elapsed: 10.1s - ETA: 62.1s
  ...
  Completed in 74.2s (96 pairs/sec)
  Found 1243 synergies above threshold (0.5)

[DECK LOAD] Synergy analysis complete! Found 1243 synergies
[DECK LOAD] Step 6: Saving deck to file...
[DECK SAVE] File written and flushed: data/decks/My_Deck_12345.json
[DECK SAVE] File size: 2048576 bytes
[DECK SAVE] File exists: True
[DECK LOAD] Deck saved to: data/decks/My_Deck_12345.json
[DECK LOAD] SUCCESS! Deck loaded: My Deck

[UPDATE GRAPH] Called with deck_file: data/decks/My_Deck_12345.json
[UPDATE GRAPH] Loading deck from file: data/decks/My_Deck_12345.json
[UPDATE GRAPH] Loaded 120 cards and 1243 synergies
[UPDATE GRAPH] Building graph elements...
[UPDATE GRAPH] Built 3603 graph elements
[UPDATE GRAPH] SUCCESS - Graph updated!
```

### 2. Common Issues and Solutions

#### Issue 1: Process stops during "Analyzing synergies"
**Symptoms:**
```
[DECK LOAD] Step 5: Analyzing synergies for 120 cards...
Analyzing synergies for 120 cards...
  Progress: 500/7140 pairs (7.0%) - Elapsed: 5.2s - ETA: 68.8s
[Then nothing...]
```

**Possible Causes:**
- Python process crashed
- Out of memory
- Regex timeout in one of the synergy rules

**Solutions:**
1. Check if Python process is still running: `ps aux | grep python`
2. Monitor memory usage: `top` or `htop`
3. If memory is an issue, try a smaller deck first (60-80 cards)
4. Check for specific card causing issues in the terminal output

#### Issue 2: Deck loads but graph doesn't update
**Symptoms:**
```
[DECK LOAD] SUCCESS! Deck loaded: My Deck
[No UPDATE GRAPH messages...]
```

**Possible Causes:**
- Dash callback didn't trigger
- File path not being passed correctly
- Browser JavaScript error

**Solutions:**
1. Check browser console (F12) for JavaScript errors
2. Manually select the deck from the dropdown after loading
3. Refresh the page and select the deck from the dropdown

#### Issue 3: "Please load a deck first" error
**Symptoms:**
- Deck appears to load successfully
- But clicking "Cards to Cut" or "Get Recommendations" shows error

**Possible Causes:**
- `deck_file` not being stored in the Dash state
- File was not saved properly

**Solutions:**
1. Check terminal for "[DECK SAVE] File exists: True"
2. Verify file exists: `ls -lh data/decks/*.json`
3. Check file is not empty: `du -h data/decks/*.json`
4. Try manually selecting the deck from dropdown

### 3. Manual Debugging

If the issue persists, you can manually test the synergy analysis:

```python
# Run this in a Python shell
import sys
sys.path.insert(0, '/Users/lucymoreira/projetos/Deck_optimizer/Deck_synergy')

from src.api.archidekt import fetch_deck_from_archidekt
from src.api.scryfall import fetch_card_details
from src.synergy_engine.analyzer import analyze_deck_synergies

# Replace with your deck URL
url = "https://archidekt.com/decks/YOUR_DECK_ID"

# Step 1: Fetch deck
print("Fetching deck...")
deck_info = fetch_deck_from_archidekt(url)
print(f"Got {len(deck_info['cards'])} cards")

# Step 2: Fetch card details
print("Fetching card details...")
cards = fetch_card_details(deck_info['cards'])
print(f"Got details for {len(cards)} cards")

# Step 3: Analyze synergies (this is the slow part)
print("Analyzing synergies...")
synergies = analyze_deck_synergies(cards)
print(f"Found {len(synergies)} synergies")
print("SUCCESS!")
```

### 4. Performance Expectations

Based on deck size, here's what to expect:

| Deck Size | Card Pairs | Analysis Time | Expected Synergies |
|-----------|-----------|---------------|-------------------|
| 60 cards  | 1,770     | 15-25 seconds | 300-500          |
| 80 cards  | 3,160     | 30-45 seconds | 500-800          |
| 100 cards | 4,950     | 45-70 seconds | 800-1200         |
| 120 cards | 7,140     | 60-90 seconds | 1000-1500        |
| 150 cards | 11,175    | 90-150 seconds| 1500-2200        |

**Note:** Times are approximate and depend on:
- Your CPU speed
- Deck complexity (more synergistic decks = more edges)
- Number of cards with damage/drain effects (slower to analyze)

### 5. Workarounds

If you absolutely cannot load a large deck:

#### Option A: Reduce deck size temporarily
1. Create a smaller version of your deck (60-80 cards)
2. Load and analyze it
3. Use "Get Recommendations" to find cards to add back

#### Option B: Increase threshold
Edit [src/synergy_engine/analyzer.py](src/synergy_engine/analyzer.py:91):

```python
# Change from 0.5 to 1.0 to reduce synergies found
def analyze_deck_synergies(cards: List[Dict], min_synergy_threshold: float = 1.0):
```

This will find fewer synergies but run faster.

#### Option C: Disable slow synergy rules temporarily
Edit [src/synergy_engine/rules.py](src/synergy_engine/rules.py:2234-2238):

Comment out the damage synergy rules (these are slowest):
```python
ALL_RULES = [
    # ... existing rules ...
    # detect_aristocrats_synergy,      # DISABLED FOR LARGE DECKS
    # detect_burn_synergy,              # DISABLED FOR LARGE DECKS
    # detect_lifegain_payoffs,          # DISABLED FOR LARGE DECKS
    # detect_damage_based_card_draw,    # DISABLED FOR LARGE DECKS
    # detect_creature_damage_synergy    # DISABLED FOR LARGE DECKS
]
```

This will make analysis ~2x faster but lose damage synergy detection.

### 6. Getting Help

If you're still stuck, provide this information:

1. **Deck size:** How many cards?
2. **Last log message:** What was the last [DECK LOAD] or [UPDATE GRAPH] message?
3. **Error message:** Full error from terminal or browser console
4. **File exists:** Does `data/decks/*.json` have your deck file?
5. **File size:** What is the size of the deck file?

Example:
```bash
# Check if files exist
ls -lh data/decks/

# Check last 50 lines of terminal output
# (copy and paste this)

# Check file contents
head -20 data/decks/YOUR_DECK_FILE.json
```

## Summary

The new logging should help you identify exactly where the loading process fails. Most issues are caused by:
1. **Long analysis time** - Just wait, watch the progress
2. **Memory issues** - Try a smaller deck or increase swap
3. **Dash state issues** - Manually select deck from dropdown after loading

If you see `[DECK LOAD] SUCCESS!` but graph doesn't load, try **manually selecting the deck from the dropdown** - this should trigger the graph update.
