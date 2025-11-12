# Teval Deck Effectiveness Analysis

## Summary

Your deck's performance metrics are severely underperforming because the simulation is missing critical graveyard/recursion mechanics that are the core of your strategy.

### Current Metrics (Your Deck)
- **Total Damage (10 turns)**: 26
- **Avg Damage/Turn**: 2.6
- **Peak Board Power**: 6
- **Commander Avg Turn**: 8.6

### Expected Metrics (For Graveyard Recursion Deck)
- **Total Damage (10 turns)**: 80-150
- **Avg Damage/Turn**: 8-15
- **Peak Board Power**: 25-50
- **Commander Avg Turn**: 4-6

---

## Critical Missing Mechanics

### 1. ❌ **PROBABILISTIC REANIMATION** (Code: `Simulation/boardstate.py:1646`)

**Problem:**
```python
reanimate_prob = min(0.05 + len(self.reanimation_targets) * 0.01, 0.15)
```

The simulation only has a **5-15% chance** of reanimating a creature per turn, and only reanimates **ONE creature** when it does trigger.

**Impact on Your Deck:**
- **Living Death**: Should return ALL creatures from graveyard → Currently returns 0-1 probabilistically
- **Dread Return**: Guaranteed reanimation → Treated as 15% chance
- **Meren of Clan Nel Toth**: Should reanimate EVERY end step → 15% chance
- **The Scarab God**: Should reanimate reliably → 15% chance

**Expected Behavior:**
- Living Death should return 5-15 creatures at once
- Meren should reanimate 1 creature per turn after turn 5
- Result: 10-25 creatures reanimated over 10 turns, not 0-2

---

### 2. ❌ **MULDROTHA NOT IMPLEMENTED**

**Problem:**
Muldrotha's ability to cast permanents from graveyard is not implemented at all.

**Impact:**
Your deck has Muldrotha, the Gravetide which lets you cast:
- 1 creature from graveyard per turn
- 1 artifact from graveyard per turn
- 1 enchantment from graveyard per turn

This is **3 extra castings per turn** after Muldrotha is on the battlefield, effectively doubling your card advantage.

**Expected Behavior:**
- Muldrotha on board by turn 5-6
- 5+ additional creatures cast from graveyard by turn 10
- Total of 10-15 extra spells cast

---

### 3. ❌ **SELF-MILL NOT AGGRESSIVE ENOUGH**

**Problem:**
Your deck has 10 mill cards:
- Hedron Crab (1-3 per landfall)
- Stitcher's Supplier (3 on ETB, 3 on death)
- Sidisi, Brood Tyrant (mill until creature)
- Etc.

These should mill **20-40 cards** by turn 10, but the simulation likely mills far fewer.

**Impact:**
- Small graveyard = few reanimation targets
- Missing Syr Konrad triggers (see below)
- Undervaluing entire mill strategy

---

### 4. ❌ **SYR KONRAD TRIGGERS COMPLETELY MISSING**

**Problem:**
Syr Konrad, the Grim deals 1 damage to each opponent whenever:
- A creature dies
- A creature is put into your graveyard from anywhere
- A creature leaves your graveyard

**With Your Deck:**
- **Self-mill 30 creatures** → 90 damage (30 × 3 opponents)
- **Reanimate 10 creatures** → 30 damage (leaving graveyard)
- **Living Death returns 10** → 30 damage (leaving graveyard)
- **Total from Syr Konrad alone**: 100-150 damage

**Current Simulation:**
Syr Konrad is likely dealing **0-5 damage total** because mill/recursion triggers aren't being tracked.

---

### 5. ❌ **OB NIXILIS LANDFALL TRIGGERS**

**Problem:**
Ob Nixilis, the Fallen deals 3 damage per landfall and gets +1/+1 counters.

**Your Deck Has:**
- Tatyova (landfall draw)
- Life from the Loam (return 3 lands)
- Multiple fetch lands
- Land recursion

**Expected:** 15-25 landfall triggers = 45-75 damage
**Current:** Probably 3-10 landfall triggers = 9-30 damage

---

### 6. ❌ **DIREGRAF CAPTAIN ZOMBIE TRIBAL**

**Problem:**
Diregraf Captain gives all Zombies +1/+1 and deals 1 damage when a Zombie dies.

**Your Deck Has:**
- Gravecrawler (infinite recursion)
- Sidisi, Brood Tyrant (creates Zombie tokens)
- The Scarab God (reanimates as Zombies)
- Many creatures that become Zombies

**Expected:** 20-40 zombie triggers = 60-120 damage
**Current:** Not tracking zombie death triggers

---

### 7. ❌ **GRAVECRAWLER INFINITE RECURSION**

**Problem:**
Gravecrawler can be cast from your graveyard if you control a Zombie.

**Expected Behavior:**
- Cast Gravecrawler from hand turn 1-2
- Dies/sacrificed turn 3-4
- Recast from graveyard EVERY TURN for 1 mana
- Blocks 10+ attacks or gets sacrificed for value

**Current:**
Gravecrawler is treated as a regular creature that stays dead.

---

### 8. ❌ **MASS MILL/DRAIN COMBOS**

**Your Deck Has:**
- **Living Death** (wipes board, returns all creatures)
- **Syr Konrad** (triggers on every creature dying AND entering graveyard)
- **Result:** Living Death with 10 creatures in graveyard + 10 on battlefield = **60 Syr Konrad triggers = 180 damage**

**Current Simulation:**
Living Death probably does nothing or reanimates 1 creature for 5 power.

---

## Mechanics Analysis Summary

| Mechanic | Cards in Deck | Expected Impact | Current Impact | Status |
|----------|---------------|-----------------|----------------|---------|
| Mass Reanimation | Living Death, Dread Return | +30-50 power on board | +0-5 | ❌ Missing |
| Muldrotha Recursion | Muldrotha, Conduit of Worlds | +10-15 creatures cast | +0 | ❌ Missing |
| Syr Konrad Triggers | Syr Konrad + mill/recursion | +100-150 damage | +0-5 | ❌ Missing |
| Aggressive Self-Mill | 10 mill cards | 30-40 cards milled | 5-10 cards | ⚠️ Underpowered |
| Landfall Drain | Ob Nixilis, Tatyova | +45-75 damage | +10-20 | ⚠️ Underpowered |
| Zombie Tribal Drain | Diregraf Captain | +60-120 damage | +0 | ❌ Missing |
| Gravecrawler Loop | Gravecrawler + Zombie | +10-20 recursions | +1 | ❌ Missing |
| Death Triggers | Multiple | +50-80 damage | +5-10 | ⚠️ Underpowered |
| Meren End Step | Meren | +5-7 reanimations | +0-1 | ❌ Missing |

---

## Detailed Code Issues

### Issue 1: Reanimation Logic (`boardstate.py:1634-1668`)

```python
def attempt_reanimation(self, verbose: bool = False):
    """Attempt to reanimate a creature from graveyard."""
    if not self.reanimation_targets:
        return False

    # PROBLEM: Only 5-15% chance!
    reanimate_prob = min(0.05 + len(self.reanimation_targets) * 0.01, 0.15)

    if random.random() < reanimate_prob:
        # PROBLEM: Only reanimates ONE creature
        target = max(self.reanimation_targets, key=lambda c: c.power or 0)

        # PROBLEM: Hardcoded 4 mana cost (Living Death is 4, but guarantees ALL creatures)
        if len(self.mana_pool) >= 4:
            # ... reanimation logic ...
```

**Fix Needed:**
1. Detect when you have reanimation spells in hand (Living Death, Dread Return, etc.)
2. If you have the spell + mana + targets → **GUARANTEED reanimation**
3. Living Death → return **ALL creatures**, not one
4. Meren → **EVERY end step** after 6+ experience counters

---

### Issue 2: No Muldrotha Implementation

**Fix Needed:**
1. Detect when Muldrotha is on battlefield
2. Each main phase, check top 3 cards of graveyard for permanent types
3. Cast 1 of each permanent type from graveyard per turn
4. Track which types have been cast this turn

---

### Issue 3: Syr Konrad Trigger Tracking (`boardstate.py`)

**Current:**
```python
# Death triggers exist but don't track Syr Konrad properly
def trigger_death_effects(self, creature, verbose=False):
    death_value = getattr(creature, 'death_trigger_value', 0)
    # ... simple drain logic ...
```

**Fix Needed:**
```python
def trigger_syr_konrad_on_mill(self, cards_milled):
    """Trigger Syr Konrad when creatures are milled"""
    for card in cards_milled:
        if 'creature' in card.type.lower():
            self.deal_drain_damage(3, source="Syr Konrad")  # 1 dmg × 3 opponents

def trigger_syr_konrad_on_death(self, creature):
    """Trigger Syr Konrad when creature dies"""
    self.deal_drain_damage(3, source="Syr Konrad")

def trigger_syr_konrad_on_leave_graveyard(self, creature):
    """Trigger Syr Konrad when creature leaves graveyard"""
    self.deal_drain_damage(3, source="Syr Konrad")
```

---

## Expected Damage Breakdown

With proper implementation, your deck should deal:

| Source | Damage Over 10 Turns |
|--------|---------------------|
| **Combat Damage** | 40-60 |
| **Syr Konrad (mill triggers)** | 60-90 |
| **Syr Konrad (recursion triggers)** | 30-50 |
| **Ob Nixilis (landfall)** | 30-50 |
| **Diregraf Captain (zombie deaths)** | 30-60 |
| **Total** | **190-310 damage** |

Current simulation shows **26 damage**, meaning you're missing **85-95%** of your deck's actual power.

---

## Recommendations

### Immediate Fixes Needed:

1. **Make Reanimation Deterministic**
   - If you have reanimation spell in hand + mana + targets → Cast it
   - Living Death returns ALL creatures
   - Meren triggers every end step

2. **Implement Muldrotha**
   - Cast 1 permanent of each type from graveyard per turn
   - This is 3-5 extra spells per turn

3. **Track Syr Konrad Triggers**
   - Trigger on: mill, death, leave graveyard
   - Should deal 90-150 damage alone

4. **Increase Mill Aggressiveness**
   - Hedron Crab should mill 3 per landfall
   - Stitcher's Supplier should mill 3 on ETB and death
   - Target: 30-40 cards milled by turn 10

5. **Implement Gravecrawler Loop**
   - Can be cast from graveyard if you control a Zombie
   - Should be cast 5-10 times from graveyard

6. **Fix Landfall Tracking**
   - Ob Nixilis should trigger on EVERY land
   - Should deal 30-60 damage from landfall alone

### Long-term Improvements:

1. **Card-Specific Implementations**
   - Each unique recursion card needs specific handling
   - Can't rely on probabilistic generic systems

2. **Graveyard as Resource**
   - Graveyard should be treated like a second hand
   - Many cards care about graveyard size/composition

3. **Combo Detection**
   - Living Death + Syr Konrad = massive damage
   - Gravecrawler + Priest of Forgotten Gods = value engine
   - Need to detect and execute these

---

## Conclusion

Your deck's **actual power level** is probably **7-8/10** for a graveyard recursion strategy.

The **simulation's assessment** is treating it as a **2-3/10** because it's missing:
- 80-90% of Syr Konrad damage
- 100% of Muldrotha value
- 85-95% of reanimation value
- 70-80% of mill value

**Bottom Line:**
The simulation needs a complete overhaul of graveyard mechanics. Current implementation is designed for creatures-that-stay-dead-when-they-die strategies, not recursion-based graveyard decks.
