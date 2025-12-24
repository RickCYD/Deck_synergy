# Synergy-Simulation Gap Analysis

**Generated:** 2025-12-24
**Purpose:** Identify synergies detected by the analyzer that are NOT properly implemented in the simulation engine

---

## EXECUTIVE SUMMARY

- **Total Synergies Detected:** 121+
- **Fully Implemented:** ~45 (37%)
- **Partially Implemented:** ~35 (29%)
- **Not Implemented:** ~41 (34%)

---

## ✅ FULLY IMPLEMENTED SYNERGIES (Working in Simulation)

### Triggers & ETB
- ✅ ETB Trigger Synergy
- ✅ Blink/ETB Synergy (flicker implemented)
- ✅ Creature ETB Triggers
- ✅ Attack Triggers
- ✅ Death Triggers
- ✅ Sacrifice Synergy
- ✅ Aristocrats Synergy

### Tokens & Sacrifice
- ✅ Token Synergy (basic creation)
- ✅ Token Doublers (basic multiplier)
- ✅ Artifact Token Triggers
- ✅ Sacrifice Outlet Synergy

### Graveyard & Recursion
- ✅ Graveyard Synergy
- ✅ Flashback Synergy (implemented)
- ✅ Reanimation Big Creatures
- ✅ Persist/Undying (implemented in extended_mechanics.py)
- ✅ Mill Self Payoff

### Ramp & Mana
- ✅ Ramp Synergy
- ✅ Mana Color Synergy
- ✅ Fetch Land Synergy
- ✅ Convoke/Improvise (cost reduction implemented)

### Landfall
- ✅ Landfall Synergy (full implementation with Scute Swarm, Omnath, Avenger)

### Spellslinger (Basic)
- ✅ Spellslinger Payoffs (cast triggers work)
- ✅ Cantrip Synergy (card draw works)
- ✅ Treasure Generation Spell (Storm-Kiln Artist works)
- ✅ Token Generation Spell (Kykar works)

### Tribal (Basic)
- ✅ Rally + Token Creation
- ✅ Rally + Rally
- ✅ Ally Tribal Synergy

### Counters
- ✅ Counter Synergy (counter placement works)
- ✅ Proliferate Synergy (basic proliferate works)
- ✅ The Ozolith (custom implementation)

### Life & Resources
- ✅ Lifegain Payoffs (drain tracking)
- ✅ Lifelink Damage Synergy (lifelink keyword tracked)

### Combat (Basic)
- ✅ Commander Damage Synergy
- ✅ Creature Damage Synergy
- ✅ Burn Synergy (damage tracking)

### Modal & Cascade
- ✅ Modal spells (implemented in extended_mechanics.py)
- ✅ Cascade (implemented)

---

## ⚠️ PARTIALLY IMPLEMENTED SYNERGIES (Limited Support)

### Tribal
- ⚠️ **Tribal Synergy** - Type checking works, but no +1/+1 lord effects
- ⚠️ **Tribal Chosen Type** - Partial (creature type selection works, but benefits limited)
- ⚠️ **Tribal Same Type** - Detection only, no global type benefits
- ⚠️ **Tribal Trigger Synergy** - Basic triggers, no complex conditions

### Tokens
- ⚠️ **Token Anthems** - Detected but no +1/+1 anthem effects applied
- ⚠️ **Food Synergy** - Food tokens created but no food payoffs
- ⚠️ **Blood Synergy** - Blood tokens detected but not created/used
- ⚠️ **Investigate Synergy** - Clue tokens detected but limited implementation
- ⚠️ **Role Token Synergy** - Role tokens not implemented

### Combat Keywords
- ⚠️ **Double Strike Synergy** - Damage doubling works, but no actual strike order
- ⚠️ **Trample Pump Synergy** - Trample detected but excess damage not calculated
- ⚠️ **Flying Evasion Synergy** - Flying keyword tracked but not enforced (goldfish)
- ⚠️ **Haste Enabler Synergy** - Haste works but enablers not tracked
- ⚠️ **Vigilance Tap Synergy** - Vigilance tracked but untap not enforced (goldfish)
- ⚠️ **Deathtouch Pingers** - Deathtouch tracked but not enforced
- ⚠️ **First Strike Damage** - Detected but not implemented
- ⚠️ **Menace Token Synergy** - Menace tracked but not enforced (goldfish)

### Evasion & Protection
- ⚠️ **Protection Synergy** - Protection keyword tracked but not enforced
- ⚠️ **Indestructible Board Wipe** - Indestructible tracked but not enforced
- ⚠️ **Hexproof Aura Synergy** - Hexproof tracked but not enforced

### Damage Types
- ⚠️ **Infect Damage Synergy** - Infect tracked but poison counters not implemented
- ⚠️ **Lifelink Damage Synergy** - Lifelink tracked but healing not processed

### Equipment & Enchantments
- ⚠️ **Equipment Synergy** - Basic equip works, but no keyword transfer
- ⚠️ **Voltron Evasion** - Equipment + keywords partially works
- ⚠️ **Enchantment Synergy** - Enchantments playable but no enchantment-matters triggers
- ⚠️ **Enchantress Effects** - Detected but no "when you cast enchantment" triggers

### Card Advantage
- ⚠️ **Card Draw Synergy** - Draw works, but no draw triggers
- ⚠️ **Draw Payoff Synergies** - Detected (Niv-Mizzet) but no "when you draw" triggers
- ⚠️ **Damage-Based Card Draw** - Detected but connection not implemented

### Planeswalkers
- ⚠️ **Planeswalker Proliferate** - Proliferate works on creatures, not PWs
- ⚠️ **Planeswalker Protection** - PWs playable but protection not enforced

---

## ❌ NOT IMPLEMENTED SYNERGIES (Detection Only)

### High-Priority Missing Mechanics

#### 1. Tap/Untap Engines (CRITICAL GAP)
- ❌ **Tap Untap Engines** - Detected but untapping creatures not implemented
- ❌ **Jeskai Ascendancy Untap** - Untap on spell cast not implemented
- ❌ **Jeskai Ascendancy Creature** - Untap + tap abilities not implemented
- ❌ **Untap Land Synergy** - Untap effects don't work

**Impact:** Major engine strategies don't work (Jeskai Ascendancy, Seedborn Muse, etc.)

#### 2. Trigger Doubling (CRITICAL GAP)
- ❌ **Veyran Trigger Doubling** - Trigger doubling not implemented
- ❌ No trigger doubling system at all

**Impact:** Veyran, Panharmonicon, Yarok strategies don't work

#### 3. Spell Copy (CRITICAL GAP)
- ❌ **Copy Synergy** - Spell copy detected but not implemented
- ❌ **Spell Copy Extra Turns** - Infinite combo not possible in simulation

**Impact:** Major combo strategies don't work (Fork, Dualcaster Mage, etc.)

#### 4. Extra Combat (HIGH PRIORITY)
- ❌ **Extra Combat Synergy** - Extra combat phases not implemented

**Impact:** Combat-focused strategies undervalued

#### 5. Wheel Effects (HIGH PRIORITY)
- ❌ **Wheel & Discard** - Wheel effects not implemented
- ❌ **Wheel & Deal** - Not implemented

**Impact:** Discard strategies, hand cycling don't work

### Card Advantage & Draw
- ❌ **Draw Payoff Synergies** - "When you draw" triggers not implemented
- ❌ **Wheel & Discard** - Wheel effects not implemented
- ❌ **Tutor Combo** - Tutors detected but no tutoring in simulation
- ❌ **Looting Reanimation** - Looting effects not implemented

### Topdeck Manipulation
- ❌ **Scry Synergy** - Scry not implemented
- ❌ **Surveil Synergy** - Surveil not implemented
- ❌ **Topdeck Manipulation** - Generic topdeck effects not implemented
- ❌ **Miracle Synergy** - Miracle mechanic not implemented

### Storm & Copy
- ❌ **Storm Synergy** - Storm count tracked but storm mechanic not implemented
- ❌ **Spell Cost Reduction** - Cost reduction detected but not implemented

### Advanced Mechanics
- ❌ **Threaten & Sac** - Theft effects not implemented
- ❌ **Cheat Big Spells** - Cheating mechanics (Breach, Show and Tell) not implemented
- ❌ **Fling Effects** - Fling/sacrifice for damage not implemented

### Specialized Keywords
- ❌ **Flash Synergy** - Flash tracked but instant-speed casting not enforced
- ❌ **Saga Synergy** - Saga chapters partially implemented but limited
- ❌ **Room Synergy** - Room mechanic not implemented
- ❌ **Vehicle Synergy** - Vehicles not implemented
- ❌ **Ninjutsu Synergy** - Ninjutsu not implemented
- ❌ **Mutate Synergy** - Mutate not implemented
- ❌ **Companion Synergy** - Companion mechanic not implemented
- ❌ **Party Synergy** - Party counting not implemented
- ❌ **Foretell Synergy** - Foretell not implemented
- ❌ **Boast Synergy** - Boast not implemented
- ❌ **Backup Synergy** - Backup not implemented
- ❌ **Blitz Synergy** - Blitz not implemented
- ❌ **Craft Synergy** - Craft not implemented
- ❌ **Discover Synergy** - Discover not implemented
- ❌ **Incubate Synergy** - Incubate not implemented

### Specific Card Mechanics
- ❌ **Bargain Synergy** - Bargain mechanic not implemented
- ❌ **Modified Synergy** - Modified creature counting not implemented
- ❌ **Affinity Synergy** - Affinity cost reduction not implemented
- ❌ **Kicker Synergy** - Kicker not implemented
- ❌ **Overload Synergy** - Overload not implemented
- ❌ **Energy Synergy** - Energy counters not implemented
- ❌ **Stax Synergy** - Stax effects not implemented
- ❌ **Type Matters Synergy** - Type-based bonuses not implemented

### Specialized Spellslinger
- ❌ **Kindred Discovery** - Partial implementation (ETB works, type filtering limited)
- ❌ **Whirlwind of Thought** - Draw on spell cast not implemented

---

## PRIORITIZATION FRAMEWORK

### Tier 1: CRITICAL (Implement First)
**Impact:** Major strategies don't work at all
1. **Tap/Untap Engines** - Jeskai Ascendancy, Seedborn Muse, Paradox Engine
2. **Trigger Doubling** - Panharmonicon, Yarok, Veyran
3. **Spell Copy** - Fork, Dualcaster Mage, infinite combos
4. **Extra Combat** - Combat-focused strategies
5. **Tribal Lords** - +1/+1 global effects

### Tier 2: HIGH PRIORITY (Implement Next)
**Impact:** Common strategies underperform
1. **Token Anthems** - Global +1/+1 for tokens
2. **Wheel Effects** - Hand cycling, discard strategies
3. **Draw Triggers** - "When you draw" payoffs
4. **Storm Mechanic** - Storm count → storm copies
5. **Energy Counters** - Energy strategies

### Tier 3: MEDIUM PRIORITY
**Impact:** Specific decks affected
1. **Scry/Surveil** - Topdeck manipulation
2. **Enchantress Triggers** - "When you cast enchantment"
3. **Flash Instant Speed** - Timing matters
4. **Tutor Effects** - Deck searching
5. **Fling Effects** - Sacrifice for damage

### Tier 4: LOW PRIORITY
**Impact:** Niche mechanics, recent sets
1. **Newer Keywords** - Foretell, Boast, Backup, Blitz, Craft, Discover, Incubate
2. **Protection Keywords** - Already goldfish mode (not needed)
3. **Companion** - Rare mechanic
4. **Party** - Tribal-lite mechanic
5. **Vehicles** - Niche strategy

---

## RECOMMENDED IMPLEMENTATION ROADMAP

### Phase 1: Critical Engine Mechanics (Week 1)
**Goal:** Make major strategies work
- [ ] Implement tap/untap system for creatures
- [ ] Implement trigger doubling (Panharmonicon, Yarok, Veyran)
- [ ] Implement spell copy mechanic
- [ ] Implement tribal lord +1/+1 effects
- [ ] Fix token anthem effects

**Estimated LOC:** ~800 lines across boardstate.py and extended_mechanics.py

### Phase 2: Combat & Card Advantage (Week 2)
**Goal:** Improve combat strategies and draw engines
- [ ] Implement extra combat phases
- [ ] Implement "when you draw" triggers
- [ ] Implement wheel effects (discard hand, draw 7)
- [ ] Implement proper first strike/double strike combat
- [ ] Improve damage calculation with trample

**Estimated LOC:** ~600 lines

### Phase 3: Cost Reduction & Storm (Week 3)
**Goal:** Support spell-heavy strategies
- [ ] Implement spell cost reduction
- [ ] Implement storm mechanic (copies based on storm count)
- [ ] Implement kicker/overload
- [ ] Implement generic cost reduction tracking

**Estimated LOC:** ~400 lines

### Phase 4: Topdeck & Tutoring (Week 4)
**Goal:** Add library manipulation
- [ ] Implement scry/surveil
- [ ] Implement miracle mechanic
- [ ] Implement tutor effects (search library)
- [ ] Improve library management

**Estimated LOC:** ~500 lines

### Phase 5: Specialized Mechanics (Week 5+)
**Goal:** Fill in remaining gaps
- [ ] Implement energy counters
- [ ] Implement enchantress triggers
- [ ] Implement fling effects
- [ ] Implement theft (threaten) effects
- [ ] Implement remaining modern mechanics

**Estimated LOC:** ~1000+ lines

---

## TESTING STRATEGY

For each implemented mechanic, test with:
1. **Unit Tests:** Single card interactions
2. **Integration Tests:** Multi-card combos
3. **Real Deck Tests:** Load deck from Archidekt with that strategy
4. **Goldfish Validation:** Compare simulation results to expected behavior

**Example Test Decks:**
- **Jeskai Ascendancy:** Shu Yun Jeskai Ascendancy deck
- **Panharmonicon:** Yarok ETB value deck
- **Storm:** Veyran spellslinger storm
- **Tribal Lords:** Edgar Markov vampire tribal
- **Extra Combat:** Isshin extra combat triggers

---

## ESTIMATED EFFORT

**Total Estimated Lines of Code:** ~3,300 lines
**Total Estimated Time:** 5-6 weeks (one person, full-time)
**Priority Time:** Week 1 critical mechanics = 50% of value

**Current Simulation Size:** 5,548 lines (boardstate.py) + 1,444 lines (extended_mechanics.py) = 6,992 lines
**Post-Implementation Size:** ~10,300 lines (+47% increase)

---

## CONCLUSION

The synergy detection system is far more comprehensive than the simulation engine. Implementing the **Tier 1 (Critical)** and **Tier 2 (High Priority)** mechanics would dramatically improve simulation accuracy for common Commander strategies.

**Recommended Starting Point:** Phase 1 (Tap/Untap, Trigger Doubling, Spell Copy, Tribal Lords)
**Expected Impact:** 60-70% of common Commander strategies would work correctly

---

**Next Steps:**
1. Review this analysis with development team
2. Prioritize Phase 1 mechanics
3. Create detailed implementation specs for each mechanic
4. Begin implementation with tap/untap system
5. Test iteratively with real decks
