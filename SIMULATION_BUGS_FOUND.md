# Simulation Bugs Found

## Summary

The deck effectiveness simulation is producing **extremely low damage values** (5-10 damage over 10 turns instead of expected 30-100+). I've identified several issues:

## Issues Found

### 1. ✅ FIXED: Combo Parsing Errors
**File:** `src/models/combo.py:118`

**Problem:** The API sometimes returns strings instead of dicts in the `uses`, `requires`, and `produces` arrays, causing `'str' object has no attribute 'get'` errors.

**Fix:** Added type checking to handle both string and dict formats:
```python
if isinstance(card_data, str):
    cards.append(ComboCard(name=card_data))
elif isinstance(card_data, dict):
    card_info = card_data.get('card', {})
    # ... rest of dict handling
```

### 2. 🔍 IDENTIFIED: Aggressive Mulligan Logic
**File:** `Simulation/draw_starting_hand.py:18`

**Problem:** The mulligan logic requires exactly 3-5 lands in the opening hand, which is very restrictive. If the deck keeps mulliganing, the hand size can drop to 4 cards or less.

**Impact:** Players start with very small hands (4 cards seen in testing), reducing the number of spells that can be cast early.

**Example from test output:**
```
Hand: Mountain 10, Mountain 30, Mountain 14, Mountain 28
```
All 4 cards are lands after mulliganing!

**Possible fixes:**
- Adjust mulligan criteria (e.g., 2-6 lands instead of 3-5)
- Reduce number of mulligans taken
- Better card selection during mulligan bottoming

### 3. 🔍 IDENTIFIED: Opponent Blocking Simulation
**Files:** `Simulation/simulate_game.py`, `Simulation/boardstate.py`

**Problem:** The simulation models opponents with creatures that block damage:
```
Opponent_1 gets a 2/1 creature
Combat: 3 damage blocked, 3 damage dealt to Opponent_2
```

**Impact:** This is **realistic** Commander gameplay, but it significantly reduces total damage dealt. In a real game, you'd deal damage through:
- Going wide (too many creatures to block all)
- Evasion (flying, unblockable, etc.)
- Removal (killing blockers)
- Politics (attacking undefended opponents)

**Current behavior:** The simulation naively attacks and gets blocked, reducing damage output.

**Possible fixes:**
- Adjust opponent simulation to have fewer/weaker blockers
- Add logic for evasion keywords (flying, trample, unblockable)
- Add removal spell simulation
- Add "open opponent" attack logic (attack opponents with no blockers)

### 4. ⚠️ POTENTIAL: Mana Pool Persistence
**Observed:** Mana pool appears to carry over between turns in verbose output:
```
Turn 6: Mana pool now: R, R
Turn 7: Mana pool now: R, R, R, R, R, R, R
```

**Expected:** Mana should empty at end of each turn (except for specific cards that say otherwise).

**Status:** Needs verification - might just be display issue

### 5. ⚠️ POTENTIAL: Card Casting Logic
**Observed:** Even with mana available, many castable spells are not being cast.

**Possible causes:**
- Small hand size from mulligans
- Prioritization issues in casting order
- Bugs in castability checking

**Status:** Needs further investigation

## Test Results

### Test 1: Aggressive Haste Deck
**Deck composition:**
- 35 lands
- 10 x 2/1 haste creatures (1 mana)
- 10 x 3/3 haste creatures (4 mana)
- 5 x 5/5 haste+trample creatures (6 mana)

**Expected:** 30+ damage over 10 turns
**Actual:** 5.4 damage over 10 turns

**Validation failures:**
- ❌ Total damage too low (5.4 vs >30)
- ❌ Peak power too low (2.0 vs >10)
- ❌ Commander never cast (turn 11 vs <6)

### Test 2: User's Token/Aristocrats Deck
**Deck:** 127 cards, token/aristocrats theme
**Expected:** 50+ damage (tokens + drain triggers)
**Actual:** ~9 damage over 10 turns

**Issues:**
- Very low combat damage
- Possibly low token generation
- Death triggers may not be firing correctly

## Recommendations

### Immediate Fixes (High Priority)

1. **Adjust mulligan criteria** to be less aggressive
   - Change from 3-5 lands to 2-6 lands
   - Stop mulliganing after 1-2 mulligans instead of continuing down to 3 cards

2. **Reduce opponent blocking** to better reflect Commander gameplay
   - Give opponents fewer blockers
   - Add logic to attack "open" opponents without blockers
   - Implement evasion keyword effects (flying, trample, etc.)

3. **Fix mana pool clearing** if it's actually carrying over

### Medium Priority

4. **Improve creature casting logic**
   - Cast creatures more aggressively
   - Better mana curve management
   - Prioritize haste creatures early

5. **Add removal simulation**
   - Simulate removal spells killing blockers
   - Add board wipe logic

### Lower Priority

6. **Better deck construction in tests**
   - Use more realistic mana ratios (37-40 lands for 100-card decks)
   - Add ramp spells
   - Add card draw

7. **Validation suite**
   - Create suite of test decks with known expected outcomes
   - Test aggro, midrange, control, combo archetypes

## Next Steps

1. ✅ Fix combo parsing errors (DONE)
2. 🔄 Adjust mulligan logic
3. 🔄 Improve opponent simulation
4. 🔄 Verify and fix other issues
5. 🔄 Re-test with user's deck
6. 🔄 Commit and push fixes

## Files Modified

- ✅ `src/models/combo.py` - Fixed combo parsing
- ⏳ `Simulation/draw_starting_hand.py` - Needs mulligan adjustment
- ⏳ `Simulation/simulate_game.py` - Needs opponent/combat improvement
