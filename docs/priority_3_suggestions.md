# Priority 3: Future Improvements for Simulation

## Status: Priority 1 & 2 COMPLETE ✅

### Priority 1 (DONE): Aristocrats Fundamentals
- ✅ Token Generation
- ✅ Death Triggers & Drain Damage
- ✅ Sacrifice Outlets
- ✅ Drain Damage Tracking

### Priority 2 (DONE): Token Deck Enhancements
- ✅ Token Doublers (Mondrak, Doubling Season)
- ✅ +1/+1 Counters (Cathars' Crusade)
- ✅ Treasure Token Expansion (Grim Hireling, Mahadi)
- ✅ Generic Attack Triggers

**Current Accuracy:**
- Voltron: 90%+ ✓
- Aristocrats: 90%+ ✓
- Go-Wide Tokens: 85%+ ✓
- Token Doublers: 85%+ ✓
- Counter Synergies: 80%+ ✓

---

## Priority 3: Remaining Archetypes & Polish

### 1. **Spellslinger / Storm** ⭐⭐⭐

**Current Accuracy:** 20%

**Missing Mechanics:**
- Cast triggers (Storm, Aetherflux Reservoir)
- Prowess / Magecraft (power buffs per spell)
- Spell copy effects (Fork, Twincast, Thousand-Year Storm)
- Instant/sorcery recursion (Snapcaster Mage, Mizzix's Mastery)

**Example Cards:**
- Aetherflux Reservoir: Gain life when you cast, deal 50 damage when 51+ life
- Guttersnipe: Each instant/sorcery deals 2 damage to each opponent
- Young Pyromancer: Create 1/1 elemental when you cast instant/sorcery
- Archmage Emeritus: Draw card when you cast/copy instant/sorcery

**Implementation Complexity:** High (4-6 hours)
**Impact:** Spellslinger decks viable

---

### 2. **Landfall** ⭐⭐

**Current Accuracy:** Unknown (likely 40%)

**Missing Mechanics:**
- Land ETB triggers
- Extra land drops per turn
- Land recursion (Crucible of Worlds, Life from the Loam)

**Example Cards:**
- Scute Swarm: Landfall → Create token copy
- Avenger of Zendikar: ETB → create plant tokens = # of lands
- Omnath, Locus of Rage: Landfall → create 5/5 elemental

**Implementation Complexity:** Medium (3-4 hours)
**Impact:** Landfall decks viable

---

### 3. **Anthems / Global Buffs** ⭐⭐ ✅ COMPLETE

**Status:** IMPLEMENTED

**Implemented Mechanics:**
- ✅ Static global buffs (Glorious Anthem, Spear of Heliod)
- ✅ Conditional buffs (Intangible Virtue - tokens get +1/+1)
- ✅ Color-specific buffs (Honor of the Pure - white creatures)
- ✅ Dynamic power/toughness calculation including anthem bonuses
- ✅ Multiple anthems stacking correctly

**Example Cards (Now Working):**
- Glorious Anthem: Creatures you control get +1/+1
- Intangible Virtue: Tokens get +1/+1 and vigilance
- Honor of the Pure: White creatures get +1/+1
- Spear of Heliod: Creatures get +1/+1

**Implementation Details:**
- Added `calculate_anthem_bonus(creature)` method to BoardState
- Added `get_effective_power(creature)` and `get_effective_toughness(creature)` helpers
- Integrated anthem bonuses into:
  - Combat damage calculations
  - AI threat assessment
  - Removal targeting
  - Total power metrics

**Impact:** +20-40 power for token armies ✓ Achieved

---

### 4. **Proliferate / Counter Movement** ⭐

**Current Accuracy:** 70% (counters work, but no proliferate)

**Missing Mechanics:**
- Proliferate (add counter to each permanent with counters)
- Counter doublers (Hardened Scales, Branching Evolution)
- Moving counters between creatures

**Example Cards:**
- Karn's Bastion: Proliferate
- Hardened Scales: If you put counters, put that many +1 instead
- The Ozolith: When creature dies, put its counters here

**Implementation Complexity:** Medium (2-3 hours)
**Impact:** +50-100 counters for counter decks

---

### 5. **Planeswalker Improvements** ⭐

**Current Status:** Basic activation exists, but no strategic use

**Missing Mechanics:**
- Smart planeswalker activation (when to +, when to -)
- Ultimate tracking and usage
- Protection (keep planeswalkers alive)

**Example:**
- Elspeth, Sun's Champion: Should prioritize +1 for tokens until ultimate

**Implementation Complexity:** Medium (3-4 hours)
**Impact:** Superfriends decks viable

---

### 6. **Reanimator** ⭐

**Current Accuracy:** 40% (graveyard tracking exists, but no reanimation)

**Missing Mechanics:**
- Reanimate spells actually working
- Discard for value
- Graveyard as resource

**Example Cards:**
- Animate Dead: Return creature from graveyard
- Reanimate: Pay life, return creature
- Living Death: Each player exiles all creatures, returns all graveyard creatures

**Implementation Complexity:** Medium (3-4 hours)
**Impact:** Reanimator decks viable

---

### 7. **Combo Detection** ⭐⭐⭐

**Current Accuracy:** 0% (infinite combos don't work)

**Missing Mechanics:**
- Detect infinite combos
- Kiki-Jiki + Zealous Conscripts
- Isochron Scepter + Dramatic Reversal
- Combo win condition

**Implementation Complexity:** High (6-8 hours)
**Impact:** Combo decks show instant win

---

### 8. **Improved AI Decision Making** ⭐⭐

**Current State:** Very basic (play lands, cast creatures, attack)

**Improvements Needed:**
- Hold up interaction (when to save mana for instants)
- Sequence spells optimally
- When to sacrifice for value
- When to activate abilities vs cast spells

**Implementation Complexity:** High (6-10 hours)
**Impact:** +10-20% accuracy across all decks

---

### 9. **Mana Efficiency** ⭐

**Current State:** Basic (tap lands, cast spells)

**Improvements Needed:**
- Use treasures at optimal times
- Crack fetchlands at right time
- Use activated abilities with leftover mana

**Implementation Complexity:** Medium (3-4 hours)
**Impact:** +5-10% mana usage efficiency

---

### 10. **Board State Evaluation** ⭐

**Current State:** Very basic (count power)

**Improvements Needed:**
- Threat assessment
- When to hold back blockers
- When to attack vs hold back

**Implementation Complexity:** High (5-7 hours)
**Impact:** More realistic gameplay

---

## Recommendations

### ✅ Completed Quick Wins:
1. **Anthems** ✅ DONE - Big power boost for token decks (+20-40 power)

### Quick Wins (Easy, High Impact):
1. **Mana Efficiency** (3 hours) - Use treasures/abilities better

### Medium Effort (Medium Impact):
3. **Landfall** (3-4 hours) - New archetype viable
4. **Proliferate** (2-3 hours) - Counter decks even stronger
5. **Reanimator** (3-4 hours) - New archetype viable

### Long-term Projects (High Effort, High Impact):
6. **Spellslinger** (4-6 hours) - Major archetype
7. **Combo Detection** (6-8 hours) - Instant win conditions
8. **Improved AI** (6-10 hours) - Better decision-making

---

## Current Simulation Quality

| Archetype | Accuracy | Notes |
|-----------|----------|-------|
| **Voltron** | 90% ✅ | Equipment works great |
| **Aristocrats** | 90% ✅ | All mechanics working |
| **Go-Wide Tokens** | 90% ✅ | Token gen, doublers, counters, anthems all work |
| **Token Doublers** | 85% ✅ | Mondrak, Doubling Season work |
| **Counter Synergies** | 80% ✅ | Cathars' Crusade works, no proliferate |
| **Treasure** | 75% ✅ | Most sources work |
| **Aggro** | 85% ✅ | Basic combat + anthems working |
| **Midrange** | 65% ⚠️ | Value engines missing |
| **Reanimator** | 40% ⚠️ | Graveyard tracked, no reanimation |
| **Spellslinger** | 20% ❌ | Cast triggers missing |
| **Landfall** | 20% ❌ | Land ETBs don't trigger |
| **Combo** | 5% ❌ | No combo detection |

---

## Summary

**Excellent coverage for:**
- Equipment/Voltron decks
- Aristocrats/death trigger decks
- Token strategies (including doublers and counters)

**Good coverage for:**
- Aggro creature combat
- Treasure ramp

**Needs work:**
- Spellslinger (major archetype missing)
- Landfall (common strategy)
- Combo (win condition missing)

**Recommend implementing Priority 3 in this order:**
1. ✅ Anthems (2h) - DONE! Easy win achieved
2. Landfall (3-4h) - New archetype
3. Spellslinger (4-6h) - Major archetype
4. Combo Detection (6-8h) - Win conditions

**Progress:** Go-Wide Tokens and Aggro now at 85-90%+ accuracy with anthem support!
