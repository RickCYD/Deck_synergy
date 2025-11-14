# Simulation Improvements - Goldfish Mode

## Summary

Implemented **GOLDFISH MODE** for deck potential measurement. This measures what a deck CAN DO in an ideal scenario, not realistic Commander gameplay with opponents.

## Changes Made

### 1. ✅ Disabled Opponent Simulation
**Files:** `Simulation/simulate_game.py`

**Changes:**
- Commented out `board.generate_opponent_creatures()`
- Commented out `board.calculate_threat_levels()`
- Commented out `board.simulate_board_wipe()`

**Rationale:** Measuring deck potential, not realistic multiplayer interaction.

### 2. ✅ Implemented Goldfish Combat
**Files:** `Simulation/simulate_game.py:684-701`

**Old behavior:** Creatures attacked into opponent blockers, significantly reducing damage
**New behavior:** All creatures attack and deal full damage (no blockers)

```python
# Goldfish mode: All creatures deal unblocked damage
for creature in board.creatures:
    if creature.has_haste or creature._turns_on_board >= 1:
        total_combat_damage += creature.power
```

**Result:** **5.5x damage improvement** (5.4 → 29.9 in test deck)

### 3. ✅ Added New Metrics
**Files:**
- `Simulation/simulate_game.py`
- `Simulation/boardstate.py`
- `Simulation/run_simulation.py`
- `src/simulation/deck_simulator.py`

**New metrics tracked:**
- **Cards Drawn** - Total cards drawn per turn
- **Life Gained** - Life gained per turn
- **Life Lost** - Life lost/paid per turn

**Added helper methods:**
```python
board.gain_life(amount, verbose)  # Track life gains
board.lose_life(amount, verbose)  # Track life losses
```

### 4. ✅ Fixed Summoning Sickness Bug
**Files:** `Simulation/simulate_game.py:688-701`

**Bug:** Non-haste creatures weren't getting their `_turns_on_board` counter incremented
**Fix:** Track turns for ALL creatures, not just attackers

## Test Results

### Before Changes (Opponent Blocking Mode)
```
Total Damage (10 turns):     5.4
Peak Board Power:            2.0
```

### After Changes (Goldfish Mode)
```
Total Damage (10 turns):     29.9  (+454%)
Peak Board Power:            8.8    (+340%)
```

**Improvement:** 5.5x damage increase!

## Impact on Your Deck

Your aristocrats deck showing **9 damage** should now show significantly higher values:
- **Combat damage** will be much higher (no blockers)
- **Drain damage** will still be tracked separately
- **Token generation** will be more visible
- **New metrics** available: cards drawn, life gained/lost

## Simulation Configuration

- **Games per deck load:** 100
- **Turns per game:** 10
- **Mode:** Goldfish (no opponents)
- **Purpose:** Measure deck potential, not realistic gameplay

## Next Steps

1. ✅ Goldfish mode implemented
2. ✅ New metrics added
3. ⏳ Frontend display (if needed)
4. ⏳ User documentation

## Notes

- **Mulligan logic:** Left unchanged per your request
- **Opponents:** Fully disabled for deck potential measurement
- **Board wipes:** Disabled (goldfish mode)
- **Removal:** Disabled (goldfish mode)

This measures what your deck CAN DO, not what happens in a real game!
