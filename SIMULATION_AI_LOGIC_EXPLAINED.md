# 🤖 Simulation AI Player Logic Explained

This document explains how the AI player makes decisions during deck simulation.

---

## 📋 Overview: Goldfish Mode

The simulation runs in **"goldfish mode"** - a solitaire-style game where:
- ✅ The AI plays its deck against **no opponents** (or opponents that don't block/interact)
- ✅ All creatures attack unblocked every turn
- ✅ The goal is to measure **maximum damage potential** over 10 turns
- ❌ No blocking, no opponent removal, no board wipes (unless testing resilience)

**Purpose**: Measure how fast and effectively your deck can execute its game plan in an ideal scenario.

**Code Reference**: `Simulation/simulate_game.py:218-820`

---

## 🔄 Turn Structure

Each turn follows standard MTG phases:

```
1. Untap Phase   → Untap all permanents
2. Upkeep Phase  → Process upkeep triggers (sagas, token creation)
3. Draw Phase    → Draw one card
4. Main Phase    → Play cards using AI decision-making ⭐
5. Combat Phase  → All creatures attack (goldfish mode)
6. End Phase     → End-of-turn effects, cleanup
```

**Code Reference**: `Simulation/turn_phases.py`

---

## 🎯 Main Phase: AI Priority System

The AI plays cards in a **strict priority order** to maximize deck effectiveness:

### Priority Order (Highest to Lowest):

```python
while (mana_available):
    1. Play ALL mana rocks (without delaying commander)
    2. Play commander (as soon as affordable)
       → Auto-equip all available equipment to commander
    3. Play ramp sorceries (Cultivate, Kodama's Reach, etc.)
    4. Play best creature (using AI scoring system) ⭐
       → Check if we should hold back to avoid overextending
       → Try to equip available equipment to this creature
    5. Try Muldrotha graveyard casts (if Muldrotha is on board)
    6. Try Gravecrawler recursion (if zombie is on board)
    7. Play equipment and attach to best target
    8. Break (no more actions possible)
```

**Code Reference**: `Simulation/simulate_game.py:457-636`

---

## 🧠 Creature Selection AI

When choosing which creature to cast, the AI uses a **scoring system** to prioritize high-value plays:

### Scoring System (prioritize_creature_for_casting)

| Priority | Creature Type | Score Bonus | Reasoning |
|----------|---------------|-------------|-----------|
| **1** | **Commander** | +1000 | Always cast commander ASAP |
| **2** | **Legendary (3+ power)** | +500 to +600 | Voltron targets (Aurelia, etc.) |
| **3** | **Attack draw trigger** | +300 | Card advantage engines |
| **3** | **Attack token trigger** | +250 | Value engines (Adeline, etc.) |
| **3** | **Attack treasure trigger** | +200 | Ramp engines |
| **3** | **Other attack triggers** | +150 | Generic value |
| **4** | **ETB draw** | +200 | Mulldrifter, etc. |
| **4** | **ETB tutor** | +180 | Tutors are powerful |
| **4** | **ETB token** | +150 | Token generators |
| **4** | **Other ETB** | +100 | Generic ETB value |
| **5** | **Mana dork** | +400 | Ramp is critical |
| **6** | **High power** | +5 per power | Bigger = better |
| **7** | **1/1 weenie** | -50 | Penalty for weak creatures |

**Example Scoring**:
```
Esper Sentinel (1/1, attack draw trigger)
= 100 (base) + 300 (attack draw) + 5 (1 power) - 50 (weenie) = 355

Solemn Simulacrum (2/2, ETB ramp)
= 100 (base) + 200 (ETB) + 10 (2 power) = 310

Llanowar Elves (1/1 mana dork)
= 100 (base) + 400 (mana dork) + 5 (1 power) - 50 (weenie) = 455
→ Llanowar Elves wins! (Ramp is prioritized)
```

**Code Reference**: `Simulation/boardstate.py:2650-2745`

---

## 🛡️ Hold Back Logic (Avoid Overextending)

The AI checks if it should **hold back** a creature to avoid overextending into board wipes:

```python
def should_hold_back_creature(creature):
    # If opponents have lots of power (threat of board wipe)
    if total_opponent_power > threat_threshold:
        # If this is a good creature (4+ power)
        # And we already have board presence (8+ power)
        if creature_power >= 4 and our_board_power >= 8:
            # 30% chance to hold back
            return random(0.3)

    return False  # Go ahead and play it
```

**When this matters**: In multiplayer simulations (not goldfish mode), the AI might hold back bombs to avoid losing everything to a board wipe.

**Code Reference**: `Simulation/boardstate.py:2841-2865`

---

## ⚔️ Equipment Targeting AI

When equipping equipment, the AI chooses the **best target** using this priority:

### Equipment Target Priority:

| Priority | Target | Score Bonus | Reasoning |
|----------|--------|-------------|-----------|
| **1** | Commander | +1000 | Voltron strategy |
| **2** | Legendary creatures | +500 | Secondary voltron targets |
| **3** | Attack draw trigger | +300 | Maximize value per attack |
| **3** | Attack token trigger | +200 | More attacks = more tokens |
| **3** | Other attack triggers | +150 | Generic value |
| **4** | First strike | +50 | Synergy with power buffs |
| **4** | Double strike | +100 | HUGE synergy with power buffs |
| **4** | Trample | +30 | Push damage through |
| **4** | Vigilance | +20 | Can attack + block |
| **5** | High current power | Power × 2 | Bigger = more damage |

**Example**:
```
Board:
- Zurgo Helmsmasher (Commander, 7/2)
- Esper Sentinel (1/1, attack draw)
- Solemn Simulacrum (2/2)

Equipment: Sword of Fire and Ice (+2/+2)

Scoring:
Zurgo    = 100 + 1000 (commander) + 14 (power×2) = 1114
Sentinel = 100 + 300 (attack draw) + 2 (power×2) = 402
Solemn   = 100 + 4 (power×2) = 104

→ Sword equips to Zurgo! (Commander priority)
```

**Code Reference**: `Simulation/boardstate.py:2781-2840`

---

## ⚔️ Combat Logic (Goldfish Mode)

In goldfish mode, combat is simplified:

```python
for creature in all_creatures:
    # Check summoning sickness
    can_attack = creature.has_haste OR creature.turns_on_board >= 1

    if can_attack:
        # All creatures attack
        # No blocking (goldfish mode)
        damage += creature.power

        # Trigger attack effects
        trigger_attack_abilities(creature)
```

**Key Points**:
- ✅ All creatures attack every turn (if able)
- ✅ All damage goes through (no blockers)
- ✅ Haste creatures attack immediately
- ✅ Non-haste creatures wait 1 turn (summoning sickness)
- ✅ Attack triggers fire (Boros Charm, etc.)

**Code Reference**: `Simulation/simulate_game.py:740-768`

---

## 💎 Mana Optimization

At the end of main phase, the AI tries to **use leftover mana**:

```python
def optimize_mana_usage():
    if mana_pool.is_empty():
        return

    # Try to activate abilities (70% chance per ability)
    for ability in available_abilities:
        if can_pay(ability.cost):
            if random() < 0.7:
                activate(ability)
                return

    # Try to cast instant-speed spells (50% chance)
    for instant in hand:
        if can_pay(instant.cost):
            if random() < 0.5:
                cast(instant)
                return
```

**Code Reference**: `Simulation/boardstate.py:2914-2938`

---

## 📊 Key Metrics Tracked

The simulation tracks these metrics every turn:

### Resource Metrics:
- Lands played
- Total mana available
- Mana spent vs. unspent
- Ramp cards played

### Board State Metrics:
- Total creature power/toughness
- Number of creatures
- Tokens created
- Creatures sacrificed

### Damage Metrics:
- **Combat damage** - Creature attack damage
- **Drain damage** - Aristocrats (Blood Artist, etc.)
- **Spell damage** - Burn spells, cast triggers

### Strategy-Specific Metrics:
- **Spellslinger**: Spells cast per turn, prowess creatures
- **Aristocrats**: Death triggers, sacrifice outlets
- **Counters**: +1/+1 counters, proliferate triggers
- **Reanimator**: Creatures reanimated, graveyard power

**Code Reference**: `Simulation/simulate_game.py:250-291`

---

## 🎲 Randomness & Variance

The AI uses randomness in a few places:

| Decision | Randomness | Purpose |
|----------|------------|---------|
| Hold back creature | 30% chance | Simulate caution vs. aggression |
| Activate ability | 70% chance | Don't always optimize perfectly |
| Cast instant | 50% chance | Simulate decision variance |

**Why?** Real players don't always make optimal plays. This simulates human-like variance.

---

## 🔍 Example Turn Walkthrough

**Turn 3 with Zurgo Helmsmasher deck**:

```
Hand: Plains, Boros Signet, Sword of Fire and Ice, Esper Sentinel
Board: 2 Mountains, 1 Plains (all untapped)
Mana Pool: {R}{R}{W}

1. UNTAP PHASE
   → All lands untap

2. UPKEEP PHASE
   → No triggers

3. DRAW PHASE
   → Draw: Aurelia, the Warleader

4. MAIN PHASE (AI Decision Making):

   Step 1: Play land
   → Play Plains from hand
   → Mana available: {R}{R}{W}{W}

   Step 2: Play mana rocks (Priority 1)
   → Cast Boros Signet (costs {2})
   → Signet produces {R}{W}
   → Mana pool: {R}{W} + {R}{W} from Signet = {R}{R}{W}{W}

   Step 3: Try to cast commander
   → Zurgo costs {2}{R}{W}
   → Can pay! Cast Zurgo.
   → Auto-equip Sword? No mana for equip cost.
   → Mana pool: {}

   Step 4: No more mana
   → End main phase

5. COMBAT PHASE
   → Zurgo has haste!
   → Zurgo attacks for 7 damage

6. END PHASE
   → Cleanup

Turn 3 damage: 7
Turn 3 board power: 7
Turn 3 commander cast: Yes
```

---

## 🎯 Design Philosophy

### Why This AI Design?

**Goal**: Measure **deck power ceiling** (best-case scenario)

**Approach**:
1. **Greedy resource deployment** - Play mana rocks ASAP for maximum acceleration
2. **Strategic creature priority** - Value engines > vanilla beaters
3. **Smart equipment targeting** - Voltron commanders, not weenies
4. **Goldfish combat** - Measure damage output without interaction

**Trade-offs**:
- ✅ **Consistent**: Same deck always produces similar results
- ✅ **Fast**: No complex decision trees or opponent modeling
- ✅ **Revealing**: Shows deck's potential when everything goes right
- ❌ **Unrealistic**: Real games have interaction, blockers, removal
- ❌ **Optimistic**: Assumes perfect draws and no disruption

---

## 🔧 Advanced Features

### Muldrotha Graveyard Recursion
- Tracks 4 permanent types cast from graveyard per turn
- Attempts graveyard casts after normal hand casting

**Code**: `Simulation/boardstate.py:attempt_muldrotha_casts()`

### Gravecrawler Infinite Recursion
- Automatically recasts Gravecrawler if a zombie is on board
- Simulates zombie tribal synergy

**Code**: `Simulation/boardstate.py:attempt_gravecrawler_cast()`

### Token Doublers
- Mondrak, Doubling Season, Parallel Lives
- Automatically doubles token creation

**Code**: `Simulation/boardstate.py:2944-3013`

### Aristocrats Damage Tracking
- Separate tracking for **combat damage** vs. **drain damage**
- Blood Artist, Zulaport Cutthroat triggers

**Code**: Throughout `boardstate.py` aristocrats mechanics

---

## 📚 Related Documentation

- **`SIMULATION_ACCURACY_COMPLETE.md`** - What mechanics are implemented
- **`STATISTICAL_ANALYSIS_GUIDE.md`** - How to interpret simulation results
- **`TROUBLESHOOTING.md`** - Common simulation issues

---

## 🛠️ For Developers

### Modifying AI Behavior

**Change creature priorities**:
→ Edit `boardstate.py:prioritize_creature_for_casting()`

**Change equipment targeting**:
→ Edit `boardstate.py:get_best_equipment_target()`

**Change main phase order**:
→ Edit `simulate_game.py:457-636` (main phase loop)

**Add new AI decision points**:
→ Add new functions in `boardstate.py` following existing patterns

---

*Last Updated: 2025-11-16*
*Simulation AI is designed to measure deck power ceiling in ideal conditions.*
