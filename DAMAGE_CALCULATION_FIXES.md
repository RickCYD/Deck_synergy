# Damage Calculation Bugs Fixed

## Summary
Fixed 5 critical bugs where damage VALUES were calculated incorrectly in the simulation engine.

---

## Bug #1: Blocked Damage Missing `damage_multiplier`

**File:** `Simulation/boardstate.py:1951`

**Problem:**
```python
# OLD - Blocked damage didn't apply damage_multiplier
blocked_damage += attack_power * damage_mult

# But unblocked damage DID apply it
damage = int(attack_power * self.damage_multiplier * damage_mult)
```

**Impact:**
- Damage doublers (like "Dictate of the Twin Gods" or "Fiery Emancipation") didn't work on blocked combat damage
- A 3/3 creature blocking with `damage_multiplier = 2.0` would take 3 damage instead of 6

**Fix:**
```python
# NEW - Blocked damage now applies damage_multiplier
blocked_damage += int(attack_power * self.damage_multiplier * damage_mult)
```

---

## Bug #2: Spell Damage Distribution Loses Damage (Integer Division)

**File:** `Simulation/boardstate.py:3984`

**Problem:**
```python
# OLD - Integer division loses fractional damage
damage_per_opp = spell_damage // len(alive_opps)
for opp in alive_opps:
    opp['life_total'] -= damage_per_opp
```

**Impact:**
- Example: 7 spell damage to 3 opponents
  - OLD: 7 // 3 = 2 damage each = 6 total (LOST 1 damage!)
  - Should be: 2, 2, 3 damage = 7 total

**Fix:**
```python
# NEW - Distribute evenly with remainder to avoid losing damage
damage_per_opp = spell_damage // len(alive_opps)
remainder = spell_damage % len(alive_opps)

for i, opp in enumerate(alive_opps):
    # First opponent gets the remainder
    opp_damage = damage_per_opp + (remainder if i == 0 else 0)
    opp['life_total'] -= opp_damage
```

---

## Bug #3: Drain Damage Distribution Loses Damage (Integer Division)

**File:** `Simulation/boardstate.py:3553`

**Problem:**
```python
# OLD - Same integer division bug as spell damage
drain_per_opp = drain_total // len(alive_opps)
for opp in alive_opps:
    opp['life_total'] -= drain_per_opp
```

**Impact:**
- Same as Bug #2
- Aristocrats decks (Zulaport Cutthroat, Blood Artist, etc.) lose drain damage

**Fix:**
```python
# NEW - Distribute evenly with remainder
drain_per_opp = drain_total // len(alive_opps)
remainder = drain_total % len(alive_opps)

for i, opp in enumerate(alive_opps):
    opp_drain = drain_per_opp + (remainder if i == 0 else 0)
    opp['life_total'] -= opp_drain
```

---

## Bug #4: Commander Damage Truncates Instead of Rounding

**File:** `Simulation/boardstate.py:2004`

**Problem:**
```python
# OLD - int() truncates, always rounding DOWN
commander_contribution = int(unblocked_damage * commander_power / total_power)
```

**Impact:**
- Example: 10 damage total, commander power = 3, total power = 7
  - Calculation: 10 * 3 / 7 = 4.2857...
  - OLD: int(4.2857) = 4 commander damage
  - NEW: round(4.2857) = 4 commander damage (this example rounds same)
  - But 10 * 4 / 7 = 5.714... → OLD: 5, NEW: 6 (gains 1 damage)

**Fix:**
```python
# NEW - round() for proper rounding
commander_contribution = round(unblocked_damage * commander_power / total_power)
```

---

## Bug #5: `take_damage()` Reduces Toughness (Completely Wrong)

**Files:**
- `Simulation/simulate_game.py:177-184`
- `Simulation/Creature.py:15-18`

**Problem (Card class):**
```python
# OLD - Limited damage to toughness AND reduced toughness
def take_damage(self, amount: int) -> int:
    if self.toughness is None:
        return amount
    dealt = min(amount, self.toughness)  # BUG: Limits damage
    self.toughness -= dealt               # BUG: Reduces toughness
    return dealt
```

**Problem (Creature class):**
```python
# OLD - Even MORE wrong!
def take_damage(self, damage):
    effective_damage = max(0, damage - self.toughness)  # Completely backward
    self.toughness -= effective_damage
    return effective_damage
```

**Impact:**
- In MTG, damage doesn't reduce toughness - it marks damage
- OLD behavior:
  - 3/3 creature takes 2 damage → becomes 3/1 (WRONG!)
  - Then takes 2 more damage → becomes 3/-1 (dead but toughness modified)
- Creature class was even worse:
  - 3/3 takes 5 damage → effective_damage = max(0, 5-3) = 2
  - toughness becomes 3 - 2 = 1 (should be dead!)

**Fix:**
```python
# NEW - Don't modify toughness at all
def take_damage(self, amount: int) -> int:
    """Mark damage on this creature and return the damage dealt.

    Note: In this simplified simulation, damage doesn't modify toughness.
    Combat code manually checks if creatures die based on comparing
    damage to toughness.
    """
    return amount
```

---

## Testing

All fixes maintain backward compatibility. The combat resolution code already manually checks if creatures should die by comparing damage to toughness, so removing the toughness modification from `take_damage()` doesn't break anything - it fixes the broken behavior.

### Example Test Cases

**Test 1: Damage Doubler on Blocked Damage**
- Board: Creature with 5 power attacking, `damage_multiplier = 2.0`, gets blocked
- OLD: 5 blocked damage (wrong)
- NEW: 10 blocked damage (correct)

**Test 2: Spell Damage Distribution**
- Spell: Deal 7 damage to 3 opponents at 40 life each
- OLD: Opponents at 38, 38, 38 life (lost 1 damage)
- NEW: Opponents at 38, 38, 37 life (all 7 damage dealt)

**Test 3: take_damage() Doesn't Reduce Toughness**
- Creature: 3/3
- Takes 2 damage
- OLD: Becomes 3/1 permanently
- NEW: Still 3/3 (damage tracked externally)

---

## Files Modified

1. `Simulation/boardstate.py`
   - Line 1951: Added `damage_multiplier` to blocked damage
   - Lines 3553-3565: Fixed drain damage distribution
   - Lines 3984-3996: Fixed spell damage distribution
   - Line 2004: Changed `int()` to `round()` for commander damage

2. `Simulation/simulate_game.py`
   - Lines 177-186: Fixed `Card.take_damage()` to not modify toughness

3. `Simulation/Creature.py`
   - Lines 15-22: Fixed `Creature.take_damage()` to not modify toughness
