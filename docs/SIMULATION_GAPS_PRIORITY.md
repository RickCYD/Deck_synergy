# Simulation Gaps - Priority Fix List

## 🔴 CRITICAL GAPS (Block Most Decks)

### 1. Direct Damage Spells NOT Simulated
**Impact**: All red decks, spellslinger strategies
**Problem**: Lightning Bolt, Lava Spike, etc. are PARSED but do nothing when cast
**Files**: Need to add damage execution in `boardstate.py:play_sorcery()` and `play_instant()`
**Estimated Fix**: Medium complexity (add target selection logic)

### 2. Non-Mana Activated Abilities NOT Implemented
**Impact**: Huge - affects most powerful cards
**Problem**: Only mana abilities work. Cards with "Pay 2: Draw a card" do nothing
**Files**: `mtg_abilities.py` (expand ActivatedAbility), `boardstate.py` (add activation logic)
**Estimated Fix**: High complexity (requires effect framework)

### 3. Death/Sacrifice Trigger Execution Incomplete
**Impact**: Aristocrats decks (4% accuracy)
**Problem**: Triggers are PARSED but execution is limited
**Files**: `oracle_text_parser.py:279` (parsing exists), `boardstate.py` (needs execution)
**Estimated Fix**: Medium complexity (add death event handling)

---

## 🟡 HIGH PRIORITY (Affects Specific Archetypes)

### 4. Upkeep/End-of-Turn Triggers Missing
**Impact**: Many permanent effects, enchantments
**Problem**: "At the beginning of your upkeep" triggers never fire
**Files**: `turn_phases.py:upkeep_phase()` is a placeholder
**Estimated Fix**: Low-medium complexity (add trigger execution)

### 5. Board-Wide Damage NOT Implemented
**Impact**: Board wipes, mass removal
**Problem**: Blasphemous Act, Earthquake do nothing
**Files**: Need new damage type in `boardstate.py`
**Estimated Fix**: Medium complexity (add AoE damage system)

### 6. AI Decision-Making is Greedy
**Impact**: All decks (underestimates potential)
**Problem**: Plays first castable card, not best card
**Files**: `turn_phases.py:main_phase()` - needs heuristics
**Estimated Fix**: High complexity (requires strategic evaluation)

---

## 🟢 MEDIUM PRIORITY (Quality of Life)

### 7. Separate Drain Sources in Metrics
**Impact**: Analysis clarity
**Problem**: ETB drain + death drain + landfall all combined into `drain_damage`
**Files**: `simulate_game.py` metrics tracking
**Estimated Fix**: Low complexity (add separate counters)

### 8. Commander Damage in Metrics
**Impact**: Voltron deck analysis
**Problem**: Commander damage tracked for 21-damage rule but not reported
**Files**: `simulate_game.py` - expose `commander_damage` metric
**Estimated Fix**: Low complexity (add to metrics dict)

### 9. Variable X Damage
**Impact**: X-spells (Fireball, Comet Storm)
**Problem**: `x_value` attribute exists but unused
**Files**: `boardstate.py` - use x_value in damage calculation
**Estimated Fix**: Low complexity (conditional damage)

---

## 🔵 LOW PRIORITY (Edge Cases)

### 10. Token Doubling Effects
**Impact**: Token strategies
**Problem**: Doubling Season, Anointed Procession not implemented
**Files**: `boardstate.py:create_token()` needs doubling logic
**Estimated Fix**: Low-medium complexity

### 11. Spell Copying
**Impact**: Spellslinger combos
**Problem**: Fork, Twincast, etc. not implemented
**Files**: Needs spell stack system
**Estimated Fix**: High complexity

### 12. Storm Mechanic
**Impact**: Storm decks
**Problem**: Not implemented at all
**Files**: Needs spell counter + copying
**Estimated Fix**: High complexity

---

## ⚪ GOLDFISH-IRRELEVANT (No Opponents)

### 13. Trample
**Status**: Keyword exists but irrelevant (no blockers)

### 14. Block Triggers
**Status**: N/A in goldfish mode

### 15. Protection/Hexproof
**Status**: N/A without opponents

### 16. Removal Spells Targeting
**Status**: Can't test effectiveness without opponents

---

## RECOMMENDED FIX ORDER

**Phase 1: Core Mechanics (Weeks 1-2)**
1. Direct damage spells (🔴 Critical)
2. Upkeep/end-of-turn triggers (🟡 High)
3. Separate drain metrics (🟢 Medium)

**Phase 2: Activated Abilities (Weeks 3-4)**
4. Non-mana activated abilities framework (🔴 Critical)
5. Death trigger execution (🔴 Critical)

**Phase 3: Advanced (Weeks 5-6)**
6. Board-wide damage (🟡 High)
7. AI decision improvements (🟡 High)
8. Commander damage metrics (🟢 Medium)

**Phase 4: Polish (Weeks 7+)**
9. Variable X damage (🟢 Medium)
10. Token doubling (🔵 Low)
11. Advanced mechanics as needed

---

## IMPACT ON STATISTICAL ANALYSIS

**Current State**:
- Statistical analysis is **valid for what's implemented**
- But **won't fix missing mechanics**

**Archetype Reliability**:
| Archetype | Accuracy | Reason | Statistical Analysis Useful? |
|-----------|----------|--------|------------------------------|
| Voltron/Equipment | 85% | Most mechanics work | ✅ YES - low CV expected |
| Combat-focused Aggro | 70% | Core combat works | ✅ YES - sample size matters |
| Aristocrats | 4% | Death triggers incomplete | ❌ NO - fix mechanics first |
| Spellslinger | 20% | Direct damage missing | ❌ NO - fix mechanics first |
| Ramp/Goodstuff | 60% | Basics work, complex cards don't | ⚠️ MAYBE - depends on deck |

**Key Insight**:
- For **consistent, working mechanics** → Statistical analysis helps determine sample size
- For **broken/missing mechanics** → Even 10,000 samples won't help

**Recommendation**:
1. Fix Critical Gaps (🔴) first
2. THEN re-run statistical analysis
3. High CV might indicate missing mechanics, not deck variance

---

## HOW TO TEST IMPROVEMENTS

After fixing each gap, test with:

```bash
# Run statistical analysis
python Simulation/test_sample_sizes.py deck.txt --sample-sizes 100 300

# Check if CV decreased after fix
# If CV is still >0.30, more mechanics may be missing
```

**Before Fix vs After Fix**:
- **Before**: High CV (0.40+) due to broken mechanics
- **After**: Lower CV (0.15-0.25) revealing true deck variance
- **Result**: Statistical analysis becomes meaningful

---

## CONCLUSION

**To answer your question**:

1. **Direct damage**: ❌ Parsed but NOT simulated
2. **Card draw**: ✅ Mechanically works, ❌ AI doesn't use it strategically
3. **Abilities**:
   - Mana abilities: ✅ FULLY WORKING
   - Triggered abilities: ⚠️ 5 types work, many missing
   - Activated abilities (non-mana): ❌ NOT IMPLEMENTED

**The statistical analysis I added is valuable BUT only for decks using working mechanics.**

For spellslinger/aristocrats/ability-heavy decks, fix the mechanics first, THEN worry about sample size.
