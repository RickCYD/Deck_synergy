# False Positive Audit & Remaining Issues

## Executive Summary

**Status**: 3/6 critical bugs fixed. 3 additional issues identified.

This document tracks false positives in the synergy detection system based on real user testing.

---

## ✅ **FIXED** - Critical Bugs (November 6, 2025)

### 1. ✅ Generous Gift Token Synergy (FIXED)
**Problem**: Opponent tokens counted as your tokens
**Status**: Fixed with opponent token exclusion patterns
**See**: `docs/BUG_FIXES_2025_11_06.md`

### 2. ✅ Cultivate "Cheat" Synergy (FIXED)
**Problem**: Land ramp confused with cheat-into-play effects
**Status**: Fixed with specific permanent type matching and ramp exclusions
**See**: `docs/BUG_FIXES_2025_11_06.md`

### 3. ✅ Sram Spellslinger Synergy (FIXED)
**Problem**: Aura/Equipment triggers matched with all spells
**Status**: Fixed with Aura/Equipment-specific trigger exclusions
**See**: `docs/BUG_FIXES_2025_11_06.md`

---

## 🟠 **REMAINING** - Known Issues

### 4. 🟠 Generic Death Trigger Matching (Needs Fix)

**Example false positive reported by user:**
```
✗ "Vincent, Vengeful Atoner and Professor Hojo both trigger when creatures die"
```

**Problem**: Two cards that both have death triggers are marked as synergistic, even if they don't actually interact.

**Current Code** (`rules.py:2224-2231`):
```python
# Death trigger with death trigger (aristocrats package)
if card1_has_death_trigger and card2_has_death_trigger:
    return {
        'name': 'Death Trigger Synergy',
        'description': f"{card1['name']} and {card2['name']} both trigger when creatures die",
        'value': 2.5,  # ⚠️ May be too generous
        'category': 'triggers',
        'subcategory': 'death_triggers'
    }
```

**Why this is problematic:**
- Card A: "Whenever a creature dies, draw a card"
- Card B: "Whenever a creature dies, gain 1 life"
- These cards don't actually synergize - they just both trigger on the same event
- No combo, no enabler/payoff relationship

**Severity**: 🟠 Medium - Creates weak/meaningless synergies

**Recommended Fix Options:**

**Option A: Increase specificity**
Only count as synergy if:
- One card creates death triggers (sacrifice outlet, board wipe)
- Other card benefits from deaths (drain, draw, etc.)

**Option B: Lower the value**
```python
'value': 0.5,  # Very weak synergy - just incidental overlap
```

**Option C: Remove entirely**
Generic death trigger overlap may not be worth detecting at all.

**Action Required**: User/developer decision on which approach to take

---

### 5. 🟡 Firion "Cheat" Detection (Needs Investigation)

**Example false positive reported by user:**
```
✗ "Firion, Wild Rose Warrior cheats Vanquish the Horde (CMC 8.0) into play"
```

**Problem**: Need to check what Firion actually does. If it's cost reduction or conditional casting, it shouldn't be labeled as "cheating".

**Requires**: Card text analysis for Firion

**Severity**: 🟡 Low-Medium - Depends on Firion's actual text

**Status**: Needs investigation

---

### 6. 🟡 Professor Hojo "Cheat" Detection (Needs Investigation)

**Example false positive reported by user:**
```
✗ "Professor Hojo cheats Austere Command (CMC 6.0) into play"
```

**Problem**: Need to check what Professor Hojo actually does.

**Requires**: Card text analysis for Professor Hojo

**Severity**: 🟡 Low-Medium - Depends on card text

**Status**: Needs investigation

---

## 📋 Priority Matrix

| Issue | Severity | Impact | Effort | Priority | Status |
|-------|----------|--------|--------|----------|--------|
| **Opponent Tokens** | 🔴 Critical | High | Low | P0 | ✅ Fixed |
| **Ramp as Cheat** | 🔴 Critical | High | Low | P0 | ✅ Fixed |
| **Aura/Equipment Spellslinger** | 🔴 Critical | High | Medium | P0 | ✅ Fixed |
| **Generic Death Triggers** | 🟠 High | Medium | Low | P1 | ⏳ Needs decision |
| **Firion Cheat Detection** | 🟡 Medium | Low | Low | P2 | ⏳ Needs investigation |
| **Professor Hojo Cheat** | 🟡 Medium | Low | Low | P2 | ⏳ Needs investigation |

---

## 🔍 Recommended Investigation Process

For remaining issues (#5-6), follow this process:

### Step 1: Get Card Text
```bash
python3 -c "
import json
cards_file = 'data/cards/cards-minimal.json'
with open(cards_file) as f:
    cards = json.load(f)

target_cards = ['Firion, Wild Rose Warrior', 'Professor Hojo']
for card in cards:
    if card['name'] in target_cards:
        print(f\"\n{card['name']}:\")
        print(f\"Type: {card.get('type_line', 'N/A')}\")
        print(f\"Oracle: {card.get('oracle_text', 'N/A')}\")
"
```

### Step 2: Check Which Pattern Matched
Add debug logging to `detect_cheat_big_spells()`:
```python
for pattern in cheat_patterns:
    if re.search(pattern, card1_text):
        print(f"MATCHED: {pattern} in {card1['name']}")
```

### Step 3: Determine Fix
- If cost reduction: Update description to say "reduces cost" not "cheats"
- If conditional casting: Update description appropriately
- If false positive: Add exclusion pattern

---

## 🧪 Test Suite Recommendations

Create automated tests for these cases:

### Test File: `tests/test_false_positives.py`

```python
def test_opponent_tokens_not_synergistic():
    """Generous Gift should NOT synergize with anthem effects"""
    generous_gift = load_card("Generous Gift")
    intangible_virtue = load_card("Intangible Virtue")

    synergy = detect_token_anthems(generous_gift, intangible_virtue)
    assert synergy is None, "Opponent tokens should not create synergy"

def test_ramp_not_cheat():
    """Cultivate should NOT be detected as 'cheat into play'"""
    cultivate = load_card("Cultivate")
    ulamog = load_card("Ulamog, the Infinite Gyre")

    synergy = detect_cheat_big_spells(cultivate, ulamog)
    # Ramp synergy is OK, but NOT cheat synergy
    if synergy:
        assert "cheat" not in synergy['description'].lower()

def test_aura_triggers_not_spellslinger():
    """Sram should NOT synergize with non-Aura spells"""
    sram = load_card("Sram, Senior Edificer")
    vandalblast = load_card("Vandalblast")

    synergy = detect_spellslinger_payoffs(sram, vandalblast)
    assert synergy is None, "Aura triggers should not match instants/sorceries"

def test_generic_death_triggers():
    """Generic death triggers may need lower value or removal"""
    # TODO: Define expected behavior
    pass
```

---

## 📊 Impact Assessment

### Before Fixes
- **False Positive Rate**: ~15-20% (estimated from user examples)
- **User Trust**: Low - multiple obvious errors
- **Usability**: Poor - users can't rely on synergies

### After Critical Fixes (Current)
- **False Positive Rate**: ~5-10% (estimated)
- **User Trust**: Moderate - major errors fixed
- **Usability**: Good - most synergies now accurate

### After All Fixes (Target)
- **False Positive Rate**: <5%
- **User Trust**: High - reliable synergies
- **Usability**: Excellent - users can trust recommendations

---

## 🎯 Next Steps

### Immediate (P1):
1. **Investigate Firion & Professor Hojo** - Check card texts
2. **Decide on death trigger approach** - Remove, lower value, or increase specificity?
3. **Run full test suite** - Validate fixes don't break other synergies

### Short-term (P2):
4. **Create automated tests** - Prevent regression
5. **Audit ALL detection functions** - Look for similar patterns
6. **Add debug mode** - Log which patterns match which cards

### Long-term (P3):
7. **User feedback system** - Let users report false positives in-app
8. **Machine learning validation** - Use ML to validate synergies
9. **Community rules** - Let users contribute synergy rules

---

## 📝 Known Limitations

Even with fixes, the system has inherent limitations:

### 1. Regex-Based Detection
- **Limitation**: Can't understand context or card complexity
- **Example**: May miss synergies with complex interactions
- **Mitigation**: Add more specific patterns over time

### 2. No Game State Awareness
- **Limitation**: Can't model actual gameplay scenarios
- **Example**: May suggest synergies that are hard to execute
- **Mitigation**: Add timing/mana efficiency fields (future work)

### 3. No Meta Knowledge
- **Limitation**: Doesn't know which synergies are actually good in practice
- **Example**: May rate weak combos same as strong ones
- **Mitigation**: Add competitive ratings (future work)

### 4. Binary Detection
- **Limitation**: Either synergizes or doesn't - no nuance
- **Example**: Can't express "synergizes well if you also have X"
- **Mitigation**: Add conditional synergies (future work)

---

## 🙏 Acknowledgments

Thank you to our users for:
- Testing with real decks
- Providing specific examples of false positives
- Holding us accountable for accuracy

**Your feedback makes this tool better.** Keep the reports coming!

---

## 📅 Changelog

### 2025-11-06
- ✅ Fixed: Opponent token detection (Generous Gift)
- ✅ Fixed: Ramp vs cheat detection (Cultivate)
- ✅ Fixed: Aura/Equipment trigger specificity (Sram)
- 📝 Documented: Generic death trigger issue
- 🔍 Identified: Firion & Professor Hojo need investigation

---

**Last Updated**: November 6, 2025
**Status**: 3 critical bugs fixed, 3 issues remaining
**Next Review**: After investigating Firion & Professor Hojo
