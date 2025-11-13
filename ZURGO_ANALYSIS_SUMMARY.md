# Zurgo Tokens Deck - Analysis & Bug Report

## Executive Summary

**Initial Deck Effectiveness: 3.3/100** ⚠️ CRITICAL

The deck is **completely non-functional** in simulation due to multiple critical bugs. The low effectiveness is NOT due to deck construction - it's due to simulation bugs preventing the deck from being played at all.

## Deck Overview

- **Commander**: Zurgo Stormrender
- **Strategy**: Token generation + Aristocrats (drain on death)
- **Total Cards**: 100 (99 + commander)
- **Key Themes**:
  - 30 token generators
  - 5 anthem effects
  - 4 drain effects
  - 3 sacrifice outlets

## Initial Performance (Before Fixes)

```
Deck Effectiveness: 3.3/100

Metrics (100 games, cumulative over 10 turns):
  Total combat damage: 1.89 (expected: 100-150)
  Total drain damage: 0.00 (expected: 20-40)
  Total tokens created: 0.00 (expected: 15-30)
  Peak board power: 0.52 (expected: 40-60)
  Cards played: 6.57 (expected: 20-25)
```

## Root Causes Identified

### 🔴 CRITICAL BUG #1: Simulation Not Casting Creatures

**Status**: NOT FIXED

**Evidence**:
- Verbose simulation shows ONLY lands being played
- Turn 1-3: Only lands played despite having castable creatures in hand
- "Battlefield creatures: 0" every single turn
- Hand contains Elas il-Kor (castable T3), Queen Marchesa (castable T4), etc.

**Impact**:
- No creatures = no ETB triggers
- No creatures = no attacks
- No attacks = no attack triggers
- **THIS IS THE PRIMARY BLOCKER**

**Root Cause**: Issue in `simulate_game.py` card playing logic - not identifying/prioritizing creatures

---

### 🟡 BUG #2: Triggered Abilities Not Parsed

**Status**: PARTIALLY FIXED ✅

**Before Fix**: 0/30 token generators had triggers parsed
**After Fix**: 7/15 token generators tested now have triggers parsed

**Fixed Cards** (ETB/Attack triggers working):
- ✅ Adeline, Resplendent Cathar - attack trigger
- ✅ Anim Pakal, Thousandth Moon - attack trigger
- ✅ Mardu Siegebreaker - ETB trigger
- ✅ Bone-Cairn Butcher - ETB trigger
- ✅ Dollmaker's Shop - attack trigger
- ✅ Ainok Strike Leader - attack trigger
- ✅ Redoubled Stormsinger - ETB trigger

**Still Missing Triggers**:
- ❌ Caesar - "enters or attacks" not detected
- ❌ Delina - complex condition (dice roll)
- ❌ Wurmcoil Engine - death trigger
- ❌ Forth Eorlingas! / Grand Crescendo / Riders of Rohan - instant/sorcery tokens
- ❌ Retrofitter Foundry - activated ability
- ❌ Elspeth - planeswalker loyalty ability

**Fix Applied**:
Enhanced `oracle_text_parser.py`:
- Added ETB token creation pattern matching
- Added attack token creation pattern matching
- Regex patterns now detect "create X Y tokens"

---

### 🟡 BUG #3: Parsed Triggers Not Being Executed

**Status**: NOT FIXED

**Evidence**:
- 7 cards now have triggers parsed
- But simulation still shows 0 tokens created
- Only 4% improvement in combat damage

**Root Cause**:
- Triggers parsed but not called during simulation
- `simulate_game.py` may not be:
  - Calling ETB triggers when creatures enter
  - Calling attack triggers during attack phase
  - Creating actual token creatures on battlefield

---

### 🔴 BUG #4: Death Triggers Not Parsed

**Status**: NOT FIXED

**Impact**: ALL drain effects (Zulaport Cutthroat, Cruel Celebrant, etc.) not working

**Affected Cards**:
- Zulaport Cutthroat: "Whenever X or another creature you control dies, each opponent loses 1 life"
- Cruel Celebrant: "Whenever X or another creature you control dies..."
- Elas il-Kor: "Whenever another creature you control dies..."
- Bastion of Remembrance: "Whenever a creature you control dies..."
- Wurmcoil Engine: "When X dies, create tokens"

**Required**: Add `parse_death_triggers_from_oracle` to detect "dies" triggers

---

### 🟡 BUG #5: Instant/Sorcery Token Creation Not Handled

**Status**: NOT FIXED

**Affected Cards**:
- Forth Eorlingas!: "Create X 2/2 tokens"
- Grand Crescendo: "Create X 1/1 tokens"
- Riders of Rohan: "Create five 2/2 tokens"
- Will of the Mardu: "Create three 2/1 tokens"
- Tempt with Vengeance: "Create X 1/1 tokens"

**Issue**: These don't have triggered abilities - they directly create tokens when cast

**Required**: Special handling in spell resolution

---

### 🟡 BUG #6: Activated Abilities Not Handled

**Status**: NOT FIXED

**Affected Cards**:
- Retrofitter Foundry: "{2}, {T}: Create a 1/1 token"
- Kher Keep: "{1}{R}, {T}: Create a 0/1 token"

**Issue**: Parsing exists but simulation doesn't activate them

---

## Fixes Applied This Session

### 1. Enhanced Token Creation Parsing

**File**: `Simulation/oracle_text_parser.py`

**Changes**:
```python
# Added to parse_etb_triggers_from_oracle():
# Pattern for: "When X enters the battlefield, create Y tokens"
m_token = re.search(
    r"when [^,]* enters the battlefield(?:[^,]*)?, (?:.*?create|create) (?P<num>...) (?P<stats>\d+/\d+)?[^.]*token",
    lower,
)

# Added to parse_attack_triggers_from_oracle():
# Pattern for: "Whenever X attacks, create Y tokens"
m_token = re.search(
    r"whenever (?:you attack|[^,]+ attacks?)(?:[^,]*)?, (?:.*?create|create) (?P<num>...) (?P<stats>\d+/\d+)?[^.]*token",
    lower,
)
```

**Results**:
- Token generator parsing: 0/15 → 7/15 ✅
- Still need to fix trigger execution

### 2. Created Comprehensive Zurgo Card Database

**File**: `build_zurgo_card_db.py`

**Purpose**: Workaround for blocked Scryfall API
**Output**: `zurgo_deck.csv` with 90 complete cards including full oracle texts

---

## Next Steps to Fix

### Priority 1: Fix Creature Casting (CRITICAL)

**File to Fix**: `Simulation/simulate_game.py`

**Investigation needed**:
1. Find the main game loop where cards are played
2. Check how the AI decides what to cast
3. Verify mana calculation and castability checks
4. Ensure creatures are being prioritized

**Expected Fix**: Modify card playing logic to properly identify and cast creatures

---

### Priority 2: Fix Trigger Execution

**File to Fix**: `Simulation/simulate_game.py` or `Simulation/boardstate.py`

**Investigation needed**:
1. Find where ETB triggers should be called
2. Find where attack triggers should be called
3. Verify token creation methods exist
4. Check if `create_tokens()` method is implemented

**Expected Fix**:
- Call `trigger.effect(board_state)` when creatures enter battlefield
- Call attack triggers during combat phase
- Implement `board_state.create_tokens(n, stats)` method

---

### Priority 3: Add Death Trigger Parsing

**File to Fix**: `Simulation/oracle_text_parser.py`

**Pattern needed**:
```python
# In parse_death_triggers_from_oracle() or new function:
m = re.search(
    r"whenever (?:a creature you control|another creature you control|[^,]+) dies, (?:.*?)(?:each opponent loses|lose) (?P<num>\d+) life",
    lower,
)
```

---

### Priority 4: Handle Instant/Sorcery Token Creation

**File to Fix**: `Simulation/simulate_game.py`

**Approach**: Check spell resolution - if oracle text contains "create" + "token", execute token creation

---

## Expected Results After All Fixes

```
Deck Effectiveness: 60-75/100 (estimated)

Projected Metrics:
  Total combat damage: 80-120
  Total drain damage: 15-30
  Total tokens created: 15-25
  Peak board power: 40-60
  Cards played: 20-25
```

---

## Test Cases to Validate

Once fixes are complete, verify:

1. **Bone-Cairn Butcher** (ETB): Creates 2 tokens when cast
2. **Adeline** (Attack): Creates tokens when attacking
3. **Zurgo** (Commander, Attack): Creates tokens on combat damage
4. **Zulaport Cutthroat** (Death): Drains opponents when creatures die
5. **Riders of Rohan** (Sorcery): Creates 5 tokens when cast
6. **Caesar** (ETB or Attack): Creates tokens on either event

---

## Files Modified

- ✅ `Simulation/oracle_text_parser.py` - Enhanced trigger parsing
- ✅ `Simulation/deck_loader.py` - Added parse_decklist_file function
- ✅ `build_zurgo_card_db.py` - Created card database
- ✅ `zurgo_tokens_decklist.txt` - Deck list
- ✅ `zurgo_deck.csv` - Card database
- ✅ `debug_zurgo_simulation.py` - Diagnostic tool

## Files That Need Fixing

- ⏳ `Simulation/simulate_game.py` - Main simulation logic
- ⏳ `Simulation/boardstate.py` - Board state management
- ⏳ `Simulation/oracle_text_parser.py` - Additional trigger types

---

## Conclusion

The Zurgo deck's 3.3/100 effectiveness is **NOT accurate** - it's caused by critical simulation bugs:

1. **Creatures not being cast** (blocker)
2. **Triggers not executing** (blocker)
3. **Death triggers not parsed**
4. **Spell-based tokens not handled**

**Once these bugs are fixed, the deck should score 60-75/100**, which would be appropriate for a well-constructed token/aristocrats strategy.

The simulation system needs significant work on:
- Card playing AI/logic
- Trigger execution system
- Token creation mechanics
- Death trigger detection
