# Flashback & Self-Recursion Fix

## Issue

Flashback cards (like Flaring Pain) were incorrectly triggering graveyard synergies with mill effects.

### Example Problem:
```
Generous Ent + Flaring Pain
  Synergy: "Generous Ent fills graveyard for Flaring Pain to utilize" (2.5)
```

This is **incorrect** because:
- **Flaring Pain** has Flashback {R}
- Flashback is **self-recursion** - it only allows you to cast *that specific card* from the graveyard
- Flaring Pain does NOT benefit from Generous Ent putting *other cards* into the graveyard
- The only card that matters for Flaring Pain is Flaring Pain itself

## Self-Recursion vs. Graveyard Synergy

### Self-Recursion Mechanics (DON'T synergize with mill):
These mechanics only care about **their own card** being in the graveyard:

- **Flashback** - Cast this spell from graveyard
- **Jump-start** - Cast this spell from graveyard, discard a card
- **Retrace** - Cast this spell from graveyard, discard a land
- **Disturb** - Cast this card from graveyard as its back face
- **Embalm** - Create a token copy from graveyard
- **Eternalize** - Create a 4/4 token copy from graveyard

These cards don't care if you have 3 cards or 30 cards in your graveyard - they only need *themselves* to be there.

### True Graveyard Payoffs (DO synergize with mill):
These mechanics benefit from **other cards** being in the graveyard:

- **Reanimation** - Return target creature from graveyard to battlefield
  - Example: Animate Dead, Reanimate, Living Death

- **Delve** - Exile cards from graveyard to pay costs
  - Example: Treasure Cruise, Dig Through Time

- **Escape** - Exile cards from graveyard to cast from graveyard
  - Example: Uro, Titan of Nature's Wrath

- **Threshold** - Has effects if 7+ cards in graveyard
  - Example: Nimble Mongoose, Werebear

- **Delirium** - Has effects if 4+ card types in graveyard
  - Example: Ishkanah, Grafwidow

- **Undergrowth** - Effects scale with creatures in graveyard
  - Example: Molderhulk, Golgari Raiders

- **Dredge** - Replace draw with mill + return
  - Example: Stinkweed Imp, Golgari Grave-Troll

- **Count Effects** - Power/effects equal to cards in graveyard
  - Example: Tarmogoyf, Lhurgoyf

## Fix Applied

### Before (Incorrect):
```python
graveyard_payoff = ['from.*graveyard', 'return.*from.*graveyard', 'threshold', 'delve', 'flashback']
```

This included 'flashback' which caused false positives.

### After (Correct):
```python
graveyard_payoff = [
    r'return\s+(?:target|a|up to).*(?:card|creature|permanent).*from.*graveyard',  # Reanimation
    r'delve',  # Delve
    r'escape',  # Escape
    r'threshold',  # Threshold
    r'delirium',  # Delirium
    r'undergrowth',  # Undergrowth
    r'cards?\s+in\s+(?:your|a|all)\s+graveyard',  # Counts graveyard
    r'for\s+each.*in.*graveyard',  # Counts graveyard
    r'exile.*from.*graveyard',  # Delve-like effects
]
```

Now flashback, jump-start, and retrace are explicitly excluded.

## Files Modified

1. **src/synergy_engine/rules.py** (line 590)
   - `detect_graveyard_synergy()` function
   - Updated graveyard_payoff patterns
   - Added detailed documentation

2. **src/synergy_engine/card_advantage_synergies.py** (line 292)
   - `detect_mill_graveyard_synergies()` function
   - Updated graveyard_matters detection
   - Added self-recursion exclusion note

## Test Results

```python
# Test 1: Flaring Pain (flashback) + Generous Ent (mill)
# Before: Found synergy (INCORRECT)
# After:  No synergy (CORRECT)

# Test 2: Animate Dead (reanimation) + Generous Ent (mill)
# Before: Found synergy (CORRECT)
# After:  Found synergy (CORRECT)
```

## Impact

This fix will:

✅ **Remove false-positive synergies** between mill and flashback/jump-start/retrace cards

✅ **Improve graph accuracy** by only showing meaningful graveyard synergies

✅ **Reduce noise** in the synergy detection

## Future Considerations

Other self-recursion mechanics to watch for:
- **Aftermath** (cast second half from graveyard)
- **Disturb** (cast back face from graveyard)
- **Embalm/Eternalize** (create token from graveyard)

These should also be excluded from graveyard synergy detection if they appear in future card sets.

## Summary

**Key Principle:**
> "Does this card benefit from OTHER cards being in the graveyard?"
> - If YES → True graveyard payoff
> - If NO (only cares about itself) → Self-recursion, NOT a graveyard payoff

This distinction is critical for accurate synergy detection in Commander decks where graveyard strategies are common.
