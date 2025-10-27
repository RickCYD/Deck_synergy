# MTG Card Extractor Coverage Map

Visual overview of implemented and missing extractors for the Deck Synergy Visualizer.

## ✅ Implemented Extractors (4 Complete)

```
┌─────────────────────────────────────────────────────────────┐
│                    REMOVAL EXTRACTORS                        │
│  ✅ Counterspells (7 types)                                  │
│  ✅ Destroy Effects (8 types)                                │
│  ✅ Exile Effects (8 types)                                  │
│  ✅ Bounce Effects (8 types)                                 │
│                                                              │
│  Coverage: 100% | Test: 70-100% | Size: 15KB                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    MANA EXTRACTORS                           │
│  ✅ Basic Lands (5 colors + snow + wastes)                   │
│  ✅ Fetch Lands (typed & slow)                               │
│  ✅ Dual Lands (8 subtypes)                                  │
│  ✅ Triomes (3-color lands)                                  │
│  ✅ Special Lands (Command Tower, utility)                   │
│                                                              │
│  Coverage: 100% | Test: 75-100% | Size: 15KB                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   KEYWORD EXTRACTORS                         │
│  ✅ 50+ Keywords across 11 categories                        │
│  ✅ Combat, Evasion, Protection                              │
│  ✅ Triggers, Resources, Counters                            │
│  ✅ Granted Keywords Detection                               │
│  ✅ Keyword Synergy Detection                                │
│                                                              │
│  Coverage: 50+ keywords | Test: 70-100% | Size: 12KB        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  BOARD WIPE EXTRACTORS                       │
│  ✅ Creature Wipes (destroy, damage, -X/-X, exile, bounce)   │
│  ✅ Artifact/Enchantment Wipes                               │
│  ✅ Land Wipes (mass land destruction)                       │
│  ✅ Token Wipes                                              │
│  ✅ Permanent Wipes                                          │
│  ✅ One-Sided vs Symmetrical Detection                       │
│                                                              │
│  Coverage: 5 categories | Test: 70-100% | Size: 14KB        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔴 High Priority Missing (Start Here!)

```
┌─────────────────────────────────────────────────────────────┐
│              🔴 DAMAGE & LIFE DRAIN EXTRACTORS               │
│  ❌ Direct Damage (Lightning Bolt, Shock)                    │
│  ❌ Each Opponent Burn (Earthquake, Sulfuric Vortex)         │
│  ❌ Single Drain (Bump in the Night, Sign in Blood)          │
│  ❌ Each Opponent Drain (Gray Merchant, Kokusho)             │
│  ❌ Life Gain (Soul Warden, Rhox Faithmender)                │
│  ❌ Each Player Effects (Mana Barbs, Ankh of Mishra)         │
│                                                              │
│  PRIORITY: 🔴 CRITICAL                                       │
│  IMPACT: Enables 30-50% more synergy detection              │
│  ARCHETYPES: Aristocrats, Burn, Lifegain, Damage Doublers   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│           🔴 CARD DRAW & ADVANTAGE EXTRACTORS                │
│  ❌ Draw X Cards (Divination, Ancestral Recall)              │
│  ❌ Each Player Draws (Howling Mine, Kami of the Crescent)   │
│  ❌ Discard Effects (Thoughtseize, Hymn to Tourach)          │
│  ❌ Wheel Effects (Wheel of Fortune, Windfall)               │
│  ❌ Tutors (Demonic Tutor, Worldly Tutor)                    │
│  ❌ Mill Effects (Glimpse the Unthinkable, Maddening Cacoph) │
│                                                              │
│  PRIORITY: 🔴 CRITICAL                                       │
│  IMPACT: Core to every deck, enables combo detection        │
│  ARCHETYPES: Wheels, Draw Matters, Mill, Discard Payoffs    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🟡 Medium Priority Missing

```
┌─────────────────────────────────────────────────────────────┐
│               🟡 TOKEN GENERATION EXTRACTORS                 │
│  ❌ Create X Tokens (ETB, cast, attack)                      │
│  ❌ Token Doublers (Doubling Season, Anointed Procession)    │
│  ❌ Token Types & Colors                                     │
│  ❌ Populate Effects                                         │
│                                                              │
│  PRIORITY: 🟡 MEDIUM                                         │
│  ARCHETYPES: Tokens, Go-Wide, Sacrifice                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│            🟡 RAMP & ACCELERATION EXTRACTORS                 │
│  ❌ Search for Lands (Cultivate, Kodama's Reach)             │
│  ❌ Put Lands into Play (Explosive Vegetation)               │
│  ❌ Mana Rocks/Dorks (Sol Ring, Birds of Paradise)           │
│  ❌ Cost Reduction (Urza's Incubator, Animar)                │
│  ❌ Extra Land Drops (Azusa, Exploration)                    │
│                                                              │
│  PRIORITY: 🟡 MEDIUM                                         │
│  ARCHETYPES: Ramp, Big Mana, Landfall                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                🟡 COMBAT MODIFIER EXTRACTORS                 │
│  ❌ Extra Combat Phases (Aggravated Assault, Relentless)     │
│  ❌ Cannot Block Effects (Rogue's Passage)                   │
│  ❌ Must Attack/Block (Propaganda, Ghostly Prison)           │
│  ❌ Combat Damage Modifiers (Torbran, Dictate of Twin Gods)  │
│  ❌ Attack Triggers (Sword of X and Y, Equipment)            │
│                                                              │
│  PRIORITY: 🟡 MEDIUM                                         │
│  ARCHETYPES: Combat, Voltron, Extra Combats                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🟢 Low Priority (Future)

```
┌─────────────────────────────────────────────────────────────┐
│            🟢 PROTECTION & PREVENTION EXTRACTORS             │
│  ❌ Prevent Damage                                           │
│  ❌ Redirect Damage                                          │
│  ❌ Phase Out Effects                                        │
│  ❌ Regeneration                                             │
│  ❌ Totem Armor                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│            🟢 GRAVEYARD INTERACTION EXTRACTORS               │
│  ❌ Reanimation (Reanimate, Animate Dead)                    │
│  ❌ Recursion (Eternal Witness, Regrowth)                    │
│  ❌ Self-Mill (Hermit Druid, Mesmeric Orb)                   │
│  ⚠️ Graveyard Hate (partially in exile extractors)          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                🟢 TRIGGER DETECTION EXTRACTORS               │
│  ❌ ETB Triggers (When this enters...)                       │
│  ❌ LTB Triggers (When this leaves...)                       │
│  ❌ Death Triggers (When this dies...)                       │
│  ❌ Trigger Counting for Synergy Strength                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Coverage Statistics

### Current State
```
Total Extractor Categories: 12
✅ Implemented: 4 (33%)
🔴 High Priority Missing: 2 (17%)
🟡 Medium Priority Missing: 3 (25%)
🟢 Low Priority Missing: 3 (25%)
```

### Test Coverage
```
Removal:       70-100% ✅
Mana:          75-100% ✅
Keywords:      70-100% ✅
Board Wipes:   70-100% ✅
```

### Lines of Code
```
Total Extractor Code: ~2,000 lines
Total Test Code: ~1,000 lines
Documentation: ~60 pages
```

---

## 🎯 Impact Map: What Each Extractor Enables

### Damage & Life Drain → Enables:
- Aristocrats synergies (drain on death)
- Burn amplification (Torbran + burn spells)
- Lifegain triggers (Soul Warden + Ajani's Pridemate)
- Damage doublers detection
- **Estimated +30 edges per deck**

### Card Draw & Advantage → Enables:
- Wheel synergies (Narset + Wheel of Fortune)
- Draw triggers (Psychosis Crawler + Rhystic Study)
- Discard payoffs (Waste Not + Windfall)
- Tutor chains
- **Estimated +40 edges per deck**

### Token Generation → Enables:
- Token doubler synergies
- Sacrifice outlet synergies
- Go-wide strategies
- **Estimated +25 edges per deck**

### Ramp & Acceleration → Enables:
- Landfall triggers
- Big mana payoffs
- Land count matters
- **Estimated +20 edges per deck**

### Combat Modifiers → Enables:
- Extra combat synergies
- Voltron strategies
- Attack trigger chains
- **Estimated +15 edges per deck**

---

## 🚀 Roadmap Timeline

### Month 1: Core Interactions
```
Week 1-2: Damage & Life Drain Extractor    🔴 HIGH PRIORITY
Week 3-4: Card Draw & Advantage Extractor  🔴 HIGH PRIORITY
```

### Month 2: Resources
```
Week 5-6: Token Generation Extractor       🟡 MEDIUM
Week 7-8: Ramp & Acceleration Extractor    🟡 MEDIUM
```

### Month 3: Combat & Advanced
```
Week 9-10: Combat Modifier Extractor       🟡 MEDIUM
Week 11-12: Protection & Prevention        🟢 LOW
```

### Month 4: Specialized
```
Week 13-14: Graveyard Interaction          🟢 LOW
Week 15-16: Trigger Detection              🟢 LOW
```

---

## 🎨 Visual Synergy Categories

Once all extractors are complete, the graph will color-code edges by synergy type:

```
🔴 RED     = Damage/Burn synergies
🔵 BLUE    = Card draw/advantage synergies
🟢 GREEN   = Ramp/mana synergies
⚫ BLACK   = Removal/destruction synergies
⚪ WHITE   = Protection/prevention synergies
🟣 PURPLE  = Combat/attack synergies
🟤 BROWN   = Graveyard synergies
🟡 YELLOW  = Token synergies
🟠 ORANGE  = Tribal synergies
```

**Example Graph Legend:**
- Thick edges = Strong synergy (3+ connections)
- Thin edges = Weak synergy (1 connection)
- Dashed edges = Conditional synergy
- Pulsing edges = Combo pieces

---

## 📈 Success Metrics

### Before (Current State)
- Average synergies per deck: 40-60
- Synergy categories: 8
- Edge types: 3 (removal, mana, tribal)

### After Phase 1 (Damage + Draw)
- Average synergies per deck: 70-100 (+50%)
- Synergy categories: 10
- Edge types: 5

### After Phase 2 (Token + Ramp)
- Average synergies per deck: 90-120 (+100%)
- Synergy categories: 12
- Edge types: 7

### After Complete (All Extractors)
- Average synergies per deck: 120-180 (+200%)
- Synergy categories: 16
- Edge types: 10
- **Combo detection enabled**
- **Strategy identification enabled**

---

## 🎯 Immediate Next Action

**START HERE:** Implement `src/utils/damage_extractors.py`

This single extractor will:
1. Enable aristocrats strategy detection
2. Identify damage amplification synergies
3. Detect lifegain payoffs
4. Add 30-50% more edges to graphs
5. Improve "Cards to Cut" accuracy

**Estimated Time:** 1-2 days
**Estimated Impact:** HIGH 🔴
