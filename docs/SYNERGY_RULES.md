# Synergy Detection Rules Documentation

## Overview

This document details all synergy detection rules implemented in the application. Each rule is a function that analyzes two cards and determines if they have a specific type of synergy.

## Rule Function Pattern

All detection rules follow this pattern:

```python
def detect_xxx_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Brief description of what this rule detects

    Returns:
        Synergy dictionary if synergy exists, None otherwise
    """
    # Detection logic
    if synergy_exists:
        return {
            'name': 'Human-readable synergy name',
            'description': 'Explanation of why cards synergize',
            'value': float,  # Base synergy value (1.0-5.0)
            'category': 'category_name',
            'subcategory': 'subcategory_name'
        }
    return None
```

---

## Detection Rules

### 1. ETB Triggers (`detect_etb_triggers`)

**Category:** triggers
**Subcategory:** etb_trigger
**Base Value:** 3.0
**Weight Multiplier:** 1.0
**Final Weight:** 3.0

**What it detects:**
Cards that have "enters the battlefield" (ETB) abilities paired with cards that can repeatedly trigger them.

**Detection Logic:**
1. Check if one card has ETB keywords:
   - "enters the battlefield"
   - "when .* enters"
   - "whenever .* enters"

2. Check if the other card can trigger ETBs:
   - "exile.*return"
   - "blink"
   - "flicker"
   - "return.*to the battlefield"

**Example Synergies:**
- **Card A:** "When Mulldrifter enters the battlefield, draw two cards"
- **Card B:** "Exile target creature, then return it to the battlefield"
- **Synergy:** Card B can repeatedly trigger Card A's ETB ability

**Real MTG Examples:**
- Eternal Witness + Ghostly Flicker
- Archaeomancer + Deadeye Navigator
- Palinchron + Equilibrium

---

### 2. Sacrifice Synergy (`detect_sacrifice_synergy`)

**Category:** role_interaction
**Subcategory:** sacrifice
**Base Value:** 2.5
**Weight Multiplier:** 0.8
**Final Weight:** 2.0

**What it detects:**
Sacrifice outlets paired with cards that create tokens or benefit from death triggers.

**Detection Logic:**
1. Check if one card is a sacrifice outlet:
   - Contains "sacrifice"
   - "as an additional cost"
   - "you may sacrifice"

2. Check if the other card provides fodder or triggers:
   - "create.*token"
   - "put.*token"
   - "when .* dies"
   - "whenever .* dies"

**Example Synergies:**
- **Card A:** "Sacrifice a creature: Draw a card"
- **Card B:** "Create two 1/1 tokens"
- **Synergy:** Card A can sacrifice tokens from Card B for value

**Real MTG Examples:**
- Ashnod's Altar + Grave Pact
- Viscera Seer + Awakening Zone
- Goblin Bombardment + Young Pyromancer

---

### 3. Mana Color Synergy (`detect_mana_color_synergy`)

**Category:** mana_synergy
**Subcategory:** color_match
**Base Value:** 2.0 × overlap_ratio
**Weight Multiplier:** 0.5
**Final Weight:** 0.5-1.0

**What it detects:**
Cards that share color identity.

**Detection Logic:**
1. Get color arrays for both cards
2. Calculate intersection (shared colors)
3. Calculate overlap ratio: shared_colors / max(card1_colors, card2_colors)
4. If overlap ≥ 50%, create synergy

**Value Calculation:**
```python
value = overlap_ratio * 2.0
# 50% overlap = 1.0 value
# 100% overlap = 2.0 value
```

**Example Synergies:**
- **Card A:** {U}{R} (Blue/Red)
- **Card B:** {U}{R}{W} (Blue/Red/White)
- **Overlap:** 2/3 = 67%
- **Value:** 1.33
- **Synergy:** "Cards share 2 color(s): U, R"

**Why it matters:**
- Color consistency in mana base
- Color-specific strategies
- Commander color identity

---

### 4. Tribal Synergy (`detect_tribal_synergy`)

**Category:** benefits
**Subcategory:** tribal
**Base Value:** 3.0 (tribal lords) or 1.5 (shared types)
**Weight Multiplier:** 0.7
**Final Weight:** 2.1 or 1.05

**What it detects:**
1. Cards that care about creature types and creatures of that type
2. Creatures that share creature types

**Detection Logic:**

**Type 1: Tribal Lords**
1. Extract subtypes from both cards
2. Check if one card's oracle text mentions the other's creature type
3. If match found, it's a lord/tribal synergy

**Type 2: Shared Types**
1. Extract creature subtypes
2. Find intersection
3. If both are creatures with shared types, weak synergy

**Example Synergies:**

**Tribal Lord:**
- **Card A:** "Elves you control get +1/+1"
- **Card B:** Creature type: Elf
- **Value:** 3.0
- **Synergy:** Card A cares about Elves, Card B is an Elf

**Shared Type:**
- **Card A:** Creature — Elf Warrior
- **Card B:** Creature — Elf Shaman
- **Value:** 1.5
- **Synergy:** Both cards share creature type(s): Elf

**Real MTG Examples:**
- Elvish Champion + Llanowar Elves
- Lord of Atlantis + Merfolk of the Pearl Trident
- Goblin King + Goblin Chieftain

---

### 5. Card Draw Synergy (`detect_card_draw_synergy`)

**Category:** card_advantage
**Subcategory:** draw_engine
**Base Value:** 2.0
**Weight Multiplier:** 0.9
**Final Weight:** 1.8

**What it detects:**
Cards that both contribute to card advantage, forming a draw engine.

**Detection Logic:**
1. Check if both cards have draw keywords:
   - "draw.*card"
   - "draws.*card"
   - "you draw"
   - "each player draws"
   - "discard.*hand.*draw" (wheel effects)

2. If both draw cards, they form an engine

**Example Synergies:**
- **Card A:** "Whenever you cast a spell, draw a card"
- **Card B:** "At the beginning of your upkeep, draw a card"
- **Synergy:** Both cards contribute to card advantage

**Real MTG Examples:**
- Rhystic Study + Consecrated Sphinx
- Phyrexian Arena + Necropotence
- Sylvan Library + Abundance

---

### 6. Ramp Synergy (`detect_ramp_synergy`)

**Category:** role_interaction
**Subcategory:** ramp
**Base Value:** 2.0
**Weight Multiplier:** 0.8
**Final Weight:** 1.6

**What it detects:**
Mana ramp cards paired with high-CMC cards they help cast.

**Detection Logic:**
1. Check if one card is ramp:
   - "search.*library.*land"
   - "put.*land.*battlefield"
   - "add.*mana"
   - Land type with "add" in text

2. Check if other card has CMC ≥ 6

3. If match, ramp enables expensive card

**Example Synergies:**
- **Card A:** "Search your library for a land and put it onto the battlefield"
- **Card B:** 8-mana Eldrazi creature
- **Synergy:** Card A helps cast expensive Card B (CMC 8)

**Real MTG Examples:**
- Cultivate + Ulamog, the Infinite Gyre
- Sol Ring + Expropriate
- Kodama's Reach + Avenger of Zendikar

---

### 7. Type Matters Synergy (`detect_type_matters_synergy`)

**Category:** type_synergy
**Subcategory:** Various (artifact_matters, creature_matters, etc.)
**Base Value:** 2.5
**Weight Multiplier:** 0.6
**Final Weight:** 1.5

**What it detects:**
Cards that care about specific card types paired with cards of that type.

**Supported Types:**
- artifact → artifact_matters
- enchantment → enchantment_matters
- creature → creature_matters
- instant/sorcery → instant_sorcery_matters
- planeswalker → planeswalker_synergy
- land → land_matters

**Detection Logic:**
1. For each card type:
   - Check if card1's text mentions the type
   - Check if card2's type line includes that type
   - If match, create synergy

**Example Synergies:**

**Artifact Matters:**
- **Card A:** "Whenever you cast an artifact spell, draw a card"
- **Card B:** Artifact type
- **Synergy:** Card A cares about artifacts, Card B is an artifact

**Creature Matters:**
- **Card A:** "Creatures you control get +1/+1"
- **Card B:** Creature type
- **Synergy:** Card A cares about creatures, Card B is a creature

**Real MTG Examples:**
- Sai, Master Thopterist + Any Artifact
- Purphoros, God of the Forge + Any Creature
- Tatyova, Benthic Druid + Any Land

---

### 8. Combo Potential (`detect_combo_potential`)

**Category:** combo
**Subcategory:** infinite_mana or two_card_combo
**Base Value:** 5.0 (infinite_mana) or 3.5 (general combo)
**Weight Multiplier:** 2.0
**Final Weight:** 10.0 or 7.0

**What it detects:**
Cards that may form infinite combos or game-winning interactions.

**Detection Logic:**

**Step 1: Check for combo keywords**
Both cards must have at least one:
- "infinite"
- "untap"
- "copy"
- "extra turn"
- "extra combat"
- "whenever you cast"
- "storm"
- "cascade"

**Step 2: Specific combo detection**
- If one has "untap" and other has "mana" → Infinite Mana (value: 5.0)
- If both have combo words but not infinite → General Combo (value: 3.5)

**Example Synergies:**

**Infinite Mana:**
- **Card A:** "Untap all permanents you control"
- **Card B:** "Add {U}{U}{U}"
- **Synergy:** Potential infinite mana combo (Weight: 10.0!)

**General Combo:**
- **Card A:** "Copy target instant or sorcery spell"
- **Card B:** "Take an extra turn after this one"
- **Synergy:** Potential combo interaction (Weight: 7.0)

**Real MTG Examples:**
- Palinchron + High Tide (Infinite Mana)
- Deadeye Navigator + Peregrine Drake (Infinite Mana)
- Kiki-Jiki + Zealous Conscripts (Infinite Creatures)

**Note:** This rule uses keywords as heuristics. Not all detected "combos" are actually infinite combos. Manual verification recommended.

---

### 9. Protection Synergy (`detect_protection_synergy`)

**Category:** role_interaction
**Subcategory:** protection
**Base Value:** 2.0
**Weight Multiplier:** 0.8
**Final Weight:** 1.6

**What it detects:**
Cards that grant protection abilities to creatures.

**Detection Logic:**
1. Check if one card grants protection:
   - Text includes "creatures you control have" or "target creature gains"
   - AND includes protection keywords: hexproof, shroud, indestructible, protection, ward

2. Check if other card is a creature

3. If match, protection synergy exists

**Example Synergies:**
- **Card A:** "Creatures you control have hexproof"
- **Card B:** Any creature
- **Synergy:** Card A can protect Card B

**Real MTG Examples:**
- Asceticism + Any Creature
- Lightning Greaves + Commander
- Heroic Intervention + Creature Board

---

### 10. Token Synergy (`detect_token_synergy`)

**Category:** role_interaction
**Subcategory:** token_generation
**Base Value:** 2.5
**Weight Multiplier:** 0.8
**Final Weight:** 2.0

**What it detects:**
Token generators paired with cards that care about tokens.

**Detection Logic:**
1. Check for token generation:
   - "create.*token"
   - "put.*token"

2. Check for token payoffs:
   - "whenever.*token"
   - "token.*you control"
   - "for each.*token"

3. If generator + payoff match, create synergy

**Example Synergies:**
- **Card A:** "Create two 1/1 Soldier tokens"
- **Card B:** "Whenever a token enters the battlefield, draw a card"
- **Synergy:** Card A creates tokens that Card B benefits from

**Real MTG Examples:**
- Krenko, Mob Boss + Impact Tremors
- Anointed Procession + Rhys the Redeemed
- Doubling Season + Avenger of Zendikar

---

### 11. Graveyard Synergy (`detect_graveyard_synergy`)

**Category:** role_interaction
**Subcategory:** recursion
**Base Value:** 2.5
**Weight Multiplier:** 0.8
**Final Weight:** 2.0

**What it detects:**
Cards that fill the graveyard paired with cards that benefit from a full graveyard.

**Detection Logic:**

**Graveyard Fillers:**
- "mill"
- "put.*into.*graveyard"
- "discard"

**Graveyard Payoffs:**
- "from.*graveyard"
- "return.*from.*graveyard"
- "threshold"
- "delve"
- "flashback"

**Example Synergies:**
- **Card A:** "Each player mills five cards"
- **Card B:** "Delve (You may exile cards from your graveyard to pay for this)"
- **Synergy:** Card A fills graveyard for Card B to utilize

**Real MTG Examples:**
- Buried Alive + Reanimate
- Entomb + Animate Dead
- Stitcher's Supplier + Muldrotha

---

## Synergy Weight Calculation

### Formula

```
Final Weight = Σ(Synergy Value × Category Weight)
```

### Example Calculation

**Cards:** Ashnod's Altar + Grave Pact

**Detected Synergies:**
1. **Sacrifice Synergy**
   - Category: role_interaction (weight: 0.8)
   - Value: 2.5
   - Weighted: 2.5 × 0.8 = 2.0

2. **Type Synergy** (both artifacts)
   - Category: type_synergy (weight: 0.6)
   - Value: 2.5
   - Weighted: 2.5 × 0.6 = 1.5

3. **Color Synergy** (both colorless)
   - Category: mana_synergy (weight: 0.5)
   - Value: 2.0
   - Weighted: 2.0 × 0.5 = 1.0

**Total Edge Weight:** 2.0 + 1.5 + 1.0 = **4.5**

---

## Category Weights Reference

| Category | Weight | Rationale |
|----------|--------|-----------|
| combo | 2.0 | Highest impact, can win games |
| card_advantage | 0.9 | Very important for Commander |
| role_interaction | 0.8 | Functional synergies |
| benefits | 0.7 | Enhancement effects |
| type_synergy | 0.6 | Theme-specific |
| mana_synergy | 0.5 | Supporting role |
| triggers | 1.0 | Baseline/neutral weight |

---

## Adding New Rules

### Step 1: Create Detection Function

```python
def detect_my_new_synergy(card1: Dict, card2: Dict) -> Optional[Dict]:
    """
    Describe what this detects
    """
    # Your logic here
    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    # Check for specific patterns
    if your_condition:
        return {
            'name': 'Descriptive Name',
            'description': f"Explain why {card1['name']} and {card2['name']} synergize",
            'value': 2.5,  # Choose appropriate value
            'category': 'appropriate_category',
            'subcategory': 'your_subcategory'
        }

    return None
```

### Step 2: Add to Rules List

In `src/synergy_engine/rules.py`:

```python
ALL_RULES = [
    detect_etb_triggers,
    detect_sacrifice_synergy,
    # ... existing rules ...
    detect_my_new_synergy,  # Add your new rule
]
```

### Step 3: Test

```python
# Test with sample cards
card1 = {'name': 'Test Card 1', 'oracle_text': '...'}
card2 = {'name': 'Test Card 2', 'oracle_text': '...'}

result = detect_my_new_synergy(card1, card2)
print(result)
```

### Step 4: Document

Add to this document following the pattern above.

---

## Guidelines for Rule Design

### 1. Value Assignment

- **1.0-2.0:** Weak/incidental synergies
- **2.0-3.0:** Moderate synergies
- **3.0-4.0:** Strong synergies
- **4.0-5.0:** Very strong synergies
- **5.0+:** Game-winning combos (rare)

### 2. Bidirectional Checks

Always check both directions:
```python
# Check if card1 has X and card2 has Y
if card1_has_x and card2_has_y:
    return synergy

# Also check reverse
if card2_has_x and card1_has_y:
    return synergy
```

### 3. Use Regex for Flexibility

```python
import re

# Instead of exact string match:
if 'enters the battlefield' in text:

# Use regex for variations:
if re.search(r'enters?.*battlefield', text):
```

### 4. Handle Missing Data

```python
oracle_text = card.get('oracle_text', '')
if not oracle_text:
    return None
```

### 5. Avoid False Positives

Be specific enough to avoid too many weak synergies:
```python
# Too broad:
if 'creature' in text1 and 'Creature' in type2:

# Better:
if 'creatures you control' in text1 and 'Creature' in type2:
```

---

## Future Rule Ideas

### Potential New Rules

1. **Equipment Synergy**
   - Equipment + Creatures that benefit from being equipped
   - Equipment + Equipment tutors

2. **Landfall Synergy**
   - Cards with landfall + Cards that play extra lands
   - Landfall + Land ramp

3. **Spell Slinger Synergy**
   - Instant/sorcery payoffs + Cheap spells
   - Copy effects + Big spells

4. **Aristocrats Synergy**
   - Death triggers + Recursive creatures
   - Sacrifice outlets + Token doublers

5. **+1/+1 Counter Synergy**
   - Counter placers + Counter doublers
   - Proliferate + Planeswalkers

6. **Energy Synergy**
   - Energy generators + Energy consumers

7. **Keyword Soup**
   - Cards that grant keywords + Creatures
   - Keyword-matters cards

8. **Storm Synergy**
   - Storm cards + Cost reducers
   - Storm + Ritual effects

9. **Voltron Synergy**
   - Auras + Aura tutors
   - Equipment + Creatures with evasion

10. **Control Synergy**
    - Board wipes + Indestructible creatures
    - Counterspells + Instant-speed draw

---

## Maintenance

### When to Update Rules

1. **New MTG Mechanics:** When new sets introduce mechanics not covered
2. **False Positives:** If a rule creates too many weak synergies
3. **False Negatives:** If obvious synergies are missed
4. **User Feedback:** Based on community input

### Testing Checklist

When modifying rules:
- [ ] Test with known synergy pairs (should detect)
- [ ] Test with non-synergistic pairs (should not detect)
- [ ] Test with edge cases (double-faced cards, etc.)
- [ ] Verify value assignments are reasonable
- [ ] Check performance (should be < 1ms per pair)
- [ ] Update documentation

---

## Performance Notes

### Optimization Tips

1. **Early Returns:** Exit as soon as synergy is found
2. **Lowercase Once:** Convert text to lowercase once, not repeatedly
3. **Compile Regex:** For frequently used patterns, compile regex
4. **Simple Checks First:** Check simple conditions before complex regex

### Current Performance

- Average time per rule: < 0.5ms
- Total time for 100-card deck: ~30-45 seconds
- Bottleneck: Scryfall API calls, not synergy detection

---

## Conclusion

The synergy detection system is designed to be:
- **Extensible:** Easy to add new rules
- **Maintainable:** Clear patterns and documentation
- **Accurate:** Balance between false positives and false negatives
- **Performant:** Fast enough for real-time use

Future improvements will focus on:
- More sophisticated NLP for oracle text parsing
- Machine learning for synergy strength estimation
- Community-contributed rule packs
- Rule testing framework
