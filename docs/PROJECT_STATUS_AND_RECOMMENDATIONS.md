# Project Status and Recommendations

**Last Updated:** October 27, 2024

## Current Project State

### ✅ Completed Extractors and Features

#### 1. **Removal Mechanics Extractors** (src/utils/removal_extractors.py)
- **Size:** 15KB, ~430 lines
- **Coverage:**
  - ✅ Counterspells (7 subtypes)
  - ✅ Destroy effects (8 subtypes)
  - ✅ Exile effects (8 subtypes)
  - ✅ Bounce effects (8 subtypes)
- **Test Coverage:** 70-100% across categories
- **Documentation:** Complete (docs/REMOVAL_EXTRACTORS.md)

#### 2. **Mana Land Extractors** (src/utils/mana_extractors.py)
- **Size:** 15KB, ~620 lines
- **Coverage:**
  - ✅ Basic lands (including snow-covered)
  - ✅ Fetch lands (typed & slow fetches)
  - ✅ Dual lands (8 subtypes: shock, check, pain, bounce, gain, scry, fast, original)
  - ✅ Triomes (3-color lands)
  - ✅ Special lands (Command Tower, utility lands)
- **Test Coverage:** 100% for duals, 75-100% for others
- **Features:** Extracts colors, tapped status, untap conditions

#### 3. **Keyword Extractors** (src/utils/keyword_extractors.py)
- **Size:** 12KB, ~450 lines
- **Coverage:** 50+ MTG keywords across 11 categories
  - ✅ Combat keywords (13)
  - ✅ Evasion keywords (7)
  - ✅ Protection keywords (5)
  - ✅ Triggered abilities (6)
  - ✅ Resource keywords (4)
  - ✅ Card advantage (4)
  - ✅ Tokens, counters, graveyard, timing keywords
- **Test Coverage:** 70-100%
- **Special Features:** Detects granted keywords, keyword synergies between cards

#### 4. **Board Wipe Extractors** (src/utils/boardwipe_extractors.py)
- **Size:** 14KB, ~520 lines
- **Coverage:**
  - ✅ Creature wipes (destroy, damage, -X/-X, exile, bounce)
  - ✅ Artifact/enchantment wipes
  - ✅ Land wipes (mass land destruction)
  - ✅ Token wipes
  - ✅ Permanent wipes (everything)
- **Key Features:**
  - One-sided vs symmetrical detection
  - Severity rating (apocalypse, severe, moderate, selective)
- **Test Coverage:** 70-100%

#### 5. **Core Graph Features** (app.py, src/*)
- ✅ Dynamic graph visualization with Cytoscape
- ✅ Local card database (35K+ cards)
- ✅ Preprocessed recommendation database
- ✅ Card recommendation system (top 10 not in deck)
- ✅ Cards to cut analysis (bottom 10 synergy)
- ✅ Top cards view (highest synergy centrality)
- ✅ Role-based filtering
- ✅ Moxfield/Archidekt deck import
- ✅ **Fixed:** Sol Ring colorless mana synergies
- ✅ **Fixed:** Synergy iteration (dict vs list handling)

---

## 📊 Analysis of Current State

### Strengths
1. **Comprehensive Removal Coverage** - All major removal types covered
2. **Rich Mana Base Analysis** - Complete land classification system
3. **Extensive Keyword Database** - 50+ keywords with synergy detection
4. **Board Wipe Intelligence** - Distinguishes one-sided vs symmetrical
5. **Solid Foundation** - All extractors are modular and testable

### Gaps Identified

#### 🔴 Critical Missing Categories

1. **Damage & Life Drain Effects** ⚠️ HIGH PRIORITY
   - Single target burn (Lightning Bolt, Shock)
   - Each opponent burn (Earthquake, Sulfuric Vortex)
   - Single drain (Bump in the Night, Sign in Blood)
   - Each opponent drain (Gray Merchant, Kokusho)
   - Life gain (Soul Warden, Rhox Faithmender)
   - Each player effects (Mana Barbs, Ankh of Mishra)

2. **Card Draw & Card Advantage** ⚠️ HIGH PRIORITY
   - Draw X cards
   - Each player draws
   - Discard effects (single, each opponent, symmetrical)
   - Wheel effects (everyone discards and draws 7)
   - Tutors (search for card types)
   - Mill effects (target player, each opponent)

3. **Token Generation** ⚠️ MEDIUM PRIORITY
   - Create X tokens
   - Create tokens on trigger (ETB, attack, damage)
   - Token doublers (Doubling Season, Anointed Procession)
   - Token types and colors

4. **Ramp & Mana Acceleration** ⚠️ MEDIUM PRIORITY
   - Search for basic lands
   - Put lands into play
   - Mana rocks/dorks (add mana effects)
   - Cost reduction effects
   - Extra land drops per turn

5. **Combat Modifiers** ⚠️ MEDIUM PRIORITY
   - Extra combat phases
   - Cannot block effects
   - Must attack/block effects
   - Combat damage modifiers (+X/+0, double damage)
   - Attack triggers (Sword of X and Y)

6. **Protection & Prevention** ⚠️ LOW PRIORITY
   - Prevent damage
   - Redirect damage
   - Phase out effects
   - Regeneration
   - Totem armor

7. **Graveyard Interaction** ⚠️ LOW PRIORITY
   - Reanimation (return from graveyard)
   - Recursion (return to hand)
   - Graveyard filling (self-mill)
   - Graveyard hate (already partially in exile_extractors)

8. **ETB/LTB Triggers** ⚠️ LOW PRIORITY
   - When this enters the battlefield
   - When this leaves the battlefield
   - When this dies
   - Trigger counting for synergy strength

---

## 🎯 Recommended Next Additions (Priority Order)

### Phase 1: Core Interactions (Weeks 1-2)

#### 1.1. **Damage & Life Drain Extractor** 🔴 START HERE
**Why First:** Most impactful for synergy detection, affects multiple archetypes
- **File:** `src/utils/damage_extractors.py`
- **Functions:**
  ```python
  extract_direct_damage(card)     # Lightning Bolt, Shock
  extract_burn_effects(card)      # Each opponent damage
  extract_drain_effects(card)     # Drain X life
  extract_life_gain(card)         # Gain X life
  extract_player_damage(card)     # Each player effects
  classify_damage_effect(card)    # Comprehensive
  ```
- **Synergies Enabled:**
  - Aristocrats strategies
  - Burn strategies
  - Lifegain strategies
  - Damage doublers (Torbran, Fiery Emancipation)
  - Lifelink + lifegain payoffs

#### 1.2. **Card Draw & Advantage Extractor**
**Why Second:** Core to every deck, enables combo detection
- **File:** `src/utils/card_advantage_extractors.py`
- **Functions:**
  ```python
  extract_draw_effects(card)       # Draw X cards
  extract_discard_effects(card)    # Discard effects
  extract_wheel_effects(card)      # Wheel of Fortune
  extract_tutor_effects(card)      # Search library
  extract_mill_effects(card)       # Mill X cards
  classify_card_advantage(card)    # Comprehensive
  ```
- **Synergies Enabled:**
  - Wheels + Narset/Hullbreacher
  - Tutors + reanimation
  - Draw triggers (Psychosis Crawler, Niv-Mizzet)
  - Discard payoffs (Waste Not, Tinybones)

### Phase 2: Resource & Acceleration (Weeks 3-4)

#### 2.1. **Token Generation Extractor**
- **File:** `src/utils/token_extractors.py`
- Synergies: Token doublers, sacrifice outlets, go-wide strategies

#### 2.2. **Ramp & Acceleration Extractor**
- **File:** `src/utils/ramp_extractors.py`
- Synergies: Landfall, big mana payoffs, land count matters

### Phase 3: Combat & Interaction (Weeks 5-6)

#### 3.1. **Combat Modifiers Extractor**
- **File:** `src/utils/combat_extractors.py`
- Synergies: Extra combats, attack triggers, combat tricks

#### 3.2. **Protection & Prevention Extractor**
- **File:** `src/utils/protection_extractors.py`
- Synergies: Prevent damage combos, phasing interactions

### Phase 4: Advanced Mechanics (Weeks 7-8)

#### 4.1. **Graveyard Interaction Extractor**
- **File:** `src/utils/graveyard_extractors.py`
- Synergies: Reanimator, recursion, self-mill

#### 4.2. **Trigger Detection Extractor**
- **File:** `src/utils/trigger_extractors.py`
- Synergies: ETB doubling, trigger copying, death triggers

---

## 🔗 Integration with Synergy Detection

### Current Synergy Rules (src/synergy_engine/rules.py)
The existing synergy detection has these functions:
- `detect_etb_synergy()` - ETB triggers
- `detect_sacrifice_synergy()` - Sacrifice outlets
- `detect_token_synergy()` - Token generation
- `detect_graveyard_synergy()` - Graveyard recursion
- `detect_tribal_synergy()` - Creature types
- `detect_mana_color_synergy()` - Mana fixing

### How New Extractors Enhance Synergies

#### Example 1: Damage Extractor → Synergy Detection
```python
# Card 1: Lightning Bolt
damage_data = extract_direct_damage(lightning_bolt)
# {'type': 'direct_damage', 'amount': 3, 'target': 'any'}

# Card 2: Torbran, Thane of Red Fell
# "If a red source you control would deal damage, it deals that much +2"

# NEW SYNERGY RULE:
def detect_damage_amplification_synergy(card1, card2):
    if has_damage_effect(card1) and amplifies_damage(card2):
        return synergy_found(value=3.0)
```

#### Example 2: Draw Extractor → Synergy Detection
```python
# Card 1: Rhystic Study (draw when opponent doesn't pay)
draw_data = extract_draw_effects(rhystic_study)
# {'type': 'conditional_draw', 'trigger': 'opponent_casts_spell'}

# Card 2: Consecrated Sphinx (draw when opponent draws)
# NEW SYNERGY: Draw chains!

# Card 3: Psychosis Crawler (damage equal to cards in hand)
# NEW SYNERGY: Draw damage combo!
```

---

## 📈 Impact Analysis

### With Damage & Card Advantage Extractors Added:

**New Synergy Categories Detected:**
1. **Aristocrats Package** (10+ new synergies)
   - Drain effects + death triggers + sacrifice outlets
   - Blood Artist + Zulaport Cutthroat + Goblin Bombardment

2. **Wheel Strategy** (8+ new synergies)
   - Wheel effects + Narset + Notion Thief
   - Discard triggers + Waste Not

3. **Burn Amplification** (6+ new synergies)
   - Direct damage + damage doublers
   - Torbran + Fiery Emancipation + Furnace of Rath

4. **Lifegain Combo** (12+ new synergies)
   - Life gain + Soul Warden/Essence Warden + Ajani's Pridemate
   - Oloro triggers + lifegain doublers

5. **Draw Engine** (15+ new synergies)
   - Card draw + Psychosis Crawler + Niv-Mizzet
   - Wheels + flash hulk payoffs

**Estimated Graph Improvements:**
- **30-50% more edges** in average commander deck
- **Better detection** of combo lines
- **Improved recommendations** based on life total strategies

---

## 🛠️ Implementation Recommendations

### For Damage & Life Drain Extractor:

**Pattern Detection Priorities:**
1. **Direct Damage:** `deals X damage to (any target|target creature|target player)`
2. **Each Opponent:** `deals X damage to each opponent`
3. **Drain:** `target (player|opponent) loses X life.*you gain X life`
4. **Each Opponent Drain:** `each opponent loses X life.*you gain`
5. **Life Gain:** `you gain X life`
6. **Symmetrical:** `each player (loses|gains) X life`

**Output Format:**
```python
{
    'type': 'damage_effect',  # or 'drain', 'life_gain'
    'subtype': 'single_target',  # or 'each_opponent', 'each_player', 'conditional'
    'amount': 3,  # or 'X', 'variable'
    'target': 'any',  # or 'creature', 'player', 'opponent', 'planeswalker'
    'conditions': [],  # e.g., 'creature you control dies'
    'is_triggered': False,  # or True if on ETB/attack/etc
    'is_repeatable': False  # or True if activated/triggered ability
}
```

### Testing Strategy:
- Test with real cards: Lightning Bolt, Gray Merchant, Zulaport Cutthroat
- Test edge cases: X damage, conditional triggers, each opponent vs each player
- Measure synergy detection improvement on sample decks

---

## 📝 Documentation Needs

Once damage extractor is complete, update:
1. **docs/DAMAGE_EXTRACTORS.md** - New documentation file
2. **docs/SYNERGY_RULES.md** - Add new synergy rules using damage data
3. **README.md** - Update feature list
4. **RELEASE_NOTES.md** - Add to next version notes

---

## 🎮 User-Facing Impact

### New Features Enabled:

1. **"Damage Package" Button**
   - Shows all burn/damage spells in deck
   - Highlights damage amplifiers
   - Suggests burn targets

2. **"Lifegain Package" Button**
   - Shows life gain effects
   - Highlights lifegain payoffs
   - Suggests soul sisters strategy

3. **Enhanced Recommendations**
   - "Your deck has 5 drain effects, consider adding blood artist"
   - "You have Torbran, add more red damage sources"

4. **Better Cut Suggestions**
   - "This burn spell has low synergy with your control deck"
   - Identifies anti-synergies (life gain in Necropotence deck)

---

## 📊 Success Metrics

After implementing Damage & Card Advantage extractors, measure:

1. **Synergy Detection Rate**
   - Before: ~40-60 synergies per 100-card deck
   - Target: ~70-100 synergies per deck (+50% increase)

2. **Recommendation Quality**
   - Test on 10 known archetypes (aristocrats, burn, control, etc.)
   - Measure if recommendations match known synergy pieces

3. **User Satisfaction**
   - "Cards to Cut" suggestions make more sense
   - Recommendations align with deck strategy
   - Graph shows meaningful connections

---

## 🚀 Next Steps (Action Items)

### This Week:
1. ✅ Review current state (this document)
2. ⏭️ **Start implementing `damage_extractors.py`**
3. ⏭️ Write comprehensive tests for damage effects
4. ⏭️ Integrate with synergy detection rules

### Next Week:
5. ⏭️ Implement `card_advantage_extractors.py`
6. ⏭️ Create new synergy rules using both extractors
7. ⏭️ Test on real commander decks
8. ⏭️ Update documentation

### Future:
- Continue with token, ramp, combat extractors
- Build synergy strength scoring system
- Add combo detection (infinite loops, game-winning lines)
- Machine learning for synergy prediction?

---

## 💡 Long-Term Vision

**Ultimate Goal:** A graph that shows not just "these cards work together" but **why** and **how much**:
- Visual strength indicators (thick edges = strong synergy)
- Color-coded edge types (removal, ramp, draw, damage, combo)
- Combo line detection (A + B + C = win condition)
- Strategy recommendations (your deck is 60% aristocrats, 40% tokens)

**The graph becomes a deck building assistant that:**
- Suggests next cards based on existing synergies
- Warns about anti-synergies
- Shows optimal card combinations
- Identifies missing pieces for strategies
