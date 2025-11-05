# Synergy System Reference

Complete reference for all synergy types, tags, and scoring in the MTG Commander Deck Synergy Visualizer.

## Table of Contents
- [System Overview](#system-overview)
- [Synergy Levels](#synergy-levels)
- [All Synergy Tags](#all-synergy-tags)
- [Synergy Categories](#synergy-categories)
- [Scoring System](#scoring-system)
- [Examples](#examples)

## System Overview

The synergy system operates on **73 unique tags** that classify card mechanics and interactions. These tags are used in three ways:

1. **Pairwise Detection**: Direct synergies between two cards (e.g., ETB + Flicker)
2. **Global Scoring**: Cards that scale with deck composition
3. **Recommendations**: Suggesting cards that fit the deck's strategy

### Data Flow

```
Card Text → Tag Extraction → Synergy Detection → Scoring
                ↓
        Preprocessed Database
        (34,253 cards with tags)
```

## Synergy Levels

### Level 1: Pairwise/Complementary (+50 points)
**Strongest synergies** - Two cards that directly enable each other

Requirements: Both tags must be present in sufficient quantities

| Tag 1 | Tag 2 | Min Count 1 | Min Count 2 | Example |
|-------|-------|-------------|-------------|---------|
| has_etb | flicker | 5 | 3 | Mulldrifter + Ghostly Flicker |
| token_gen | sacrifice_outlet | 5 | 3 | Bitterblossom + Goblin Bombardment |
| equipment | equipment_matters | 3 | 5 | Sword of Fire and Ice + Puresteel Paladin |
| attack_trigger | trigger_doubler | 5 | 1 | Combat Celebrant + Panharmonicon |
| death_trigger | sacrifice_outlet | 3 | 3 | Blood Artist + Ashnod's Altar |

### Level 2: Three-Way (+30 points)
**Complex synergies** - Requires 3+ components working together

| Synergy | Components Required | Example |
|---------|---------------------|---------|
| Land Recursion | lands (25+) + graveyard (5+) + recursion_land | Conduit of Worlds + Life from the Loam |
| Artifact Recursion | artifacts (15+) + graveyard (5+) + recursion_artifact | Daretti + Goblin Welder |
| Equipment Voltron | equipment (3+) + creatures + equipment_enabler | Ardenn + Bruenor Battlehammer |

### Level 3: Global/Scaling (10-20 points max)
**Scales with deck composition** - Grows stronger with more of a card type

| Tag | Scales With | Multiplier | Cap | Example |
|-----|-------------|------------|-----|---------|
| scales_with_artifacts | Artifact count | 0.4 per card | 20 pts | Inspiring Statuary (20 artifacts = 8 pts) |
| scales_with_equipment | Equipment count | 0.5 per card | 20 pts | Hammer of Nazahn (10 equipment = 5 pts) |
| scales_with_spells | Instant/Sorcery count | 0.3 per card | 15 pts | Sword of Once and Future |
| scales_with_creatures | Creature count | 0.3 per card | 15 pts | Coat of Arms |
| scales_with_lands | Land count | 0.2 per card | 10 pts | Conduit of Worlds |

### Level 4: Local/Tag Overlap (0.1-0.5 per card)
**Foundation synergies** - Cards that share strategy tags

| Tag Type | Weight | Examples |
|----------|--------|----------|
| Generic Utility | 0.1 per card | ramp, card_draw, removal, counters, protection |
| Strategic | 0.5 per card | token_gen, equipment, death_trigger, spellslinger |
| Default | 0.3 per card | All other tags |

## All Synergy Tags (73 Total)

### Combat & Triggers (11 tags)
- **attack_trigger**: "Whenever X attacks" effects
- **block_trigger**: "Whenever X blocks/becomes blocked"
- **trigger_doubler**: Doubles triggered abilities (Panharmonicon, Yarok)
- **death_trigger**: "When creature dies" triggers
- **cast_creature_trigger**: "When you cast a creature spell"
- **cast_spell_trigger**: "When you cast instant/sorcery"
- **has_etb**: Enters-the-battlefield triggers
- **landfall**: "Whenever a land enters"
- **counters**: +1/+1 counters and counter synergies
- **untap_others**: Untaps other permanents
- **protection**: Grants protection/indestructible

### Card Advantage (5 tags)
- **card_draw**: Draws cards
- **mill**: Mills opponent's library
- **self_mill**: Mills own library
- **spellslinger**: Cares about casting instants/sorceries
- **mana_ability**: Generates mana

### Graveyard & Recursion (9 tags)
- **graveyard**: General graveyard interaction
- **recursion_land**: Plays lands from graveyard
- **recursion_artifact**: Returns artifacts from graveyard
- **recursion_creature**: Returns creatures from graveyard
- **recursion_spell**: Flashback, retrace, spell recursion
- **flicker**: Exile and return (blink effects)

### Sacrifice & Tokens (7 tags)
- **token_gen**: Creates tokens
- **sacrifice_outlet**: Sacrifices permanents for value
- **sac_creature**: Specifically sacrifices creatures
- **sac_token**: Specifically sacrifices tokens
- **sac_artifact**: Specifically sacrifices artifacts
- **sac_land**: Specifically sacrifices lands
- **sac_permanent**: Generic permanent sacrifice
- **sac_nonland**: Sacrifices nonland permanents

### Equipment & Artifacts (6 tags)
- **equipment**: Equipment cards
- **equipment_matters**: Cares about equipment
- **equipment_enabler**: Moves/attaches equipment
- **artifact_synergy**: Artifact synergies
- **scales_with_artifacts**: Grows with artifact count
- **scales_with_equipment**: Grows with equipment count

### Scaling Synergies (6 tags)
- **scales_with_artifacts**: Counts artifacts you control
- **scales_with_equipment**: Counts equipment you control
- **scales_with_spells**: Counts instants/sorceries
- **scales_with_creatures**: Counts creatures you control
- **scales_with_lands**: Counts lands you control
- **scales_with_permanents**: Counts all permanents

### Tribal (29 tags)
- **tribal_payoff**: Generic tribal rewards
- **tribal_angel**, **tribal_beast**, **tribal_bird**, **tribal_cat**
- **tribal_demon**, **tribal_dinosaur**, **tribal_dog**, **tribal_dragon**
- **tribal_elemental**, **tribal_elf**, **tribal_elves**, **tribal_goblin**
- **tribal_human**, **tribal_insect**, **tribal_knight**, **tribal_merfolk**
- **tribal_rat**, **tribal_sliver**, **tribal_snake**, **tribal_soldier**
- **tribal_spider**, **tribal_spirit**, **tribal_vampire**, **tribal_warrior**
- **tribal_wizard**, **tribal_wolf**, **tribal_zombie**

### Utility (5 tags)
- **ramp**: Mana acceleration
- **removal**: Destroys/exiles permanents
- **enchantment_synergy**: Enchantment synergies
- **aura**: Aura enchantments

## Synergy Categories

Categories shown in the UI when viewing synergies:

### ETB Synergies
- **ETB → Payoff**: Cards with ETBs + flicker/recursion
- **Flicker → ETB**: Flicker effects find ETB targets
- **Example**: Mulldrifter + Ghostly Flicker

### Token Synergies
- **Token → Sacrifice**: Token generators + sacrifice outlets
- **Sacrifice → Tokens**: Sacrifice outlets value tokens
- **Example**: Bitterblossom + Goblin Bombardment

### Equipment Synergies
- **Equipment → Payoff**: Equipment + equipment matters cards
- **Equipment Enabler**: Cards that move/attach equipment
- **Example**: Colossus Hammer + Sigarda's Aid

### Graveyard Synergies
- **Graveyard → Recursion**: Self-mill + graveyard recursion
- **Self-Mill → Payoff**: Self-mill enables graveyard strategies
- **Example**: Entomb + Reanimate

### Tutor Synergies
- **Tutor → Target**: Tutors can find valuable targets
- **Validates**: CMC, power, toughness restrictions
- **Example**: Recruiter of the Guard → Creatures with toughness ≤2

### Combat Synergies
- **Attack → Damage**: Attack triggers + damage multipliers
- **Damage → Payoff**: Damage triggers life gain/drain effects
- **Example**: Boros Charm + Fiery Emancipation

### Ramp Synergies
- **Ramp → Payoff**: Mana acceleration enables expensive spells
- **Landfall → Ramp**: Land ramp triggers landfall
- **Example**: Cultivate + Tatyova, Benthic Druid

### Tribal Synergies
- **Tribal Overlap**: Cards share creature types
- **Tribal Bonus**: +100 if deck has 10+ of one tribe
- **Example**: Elves deck with Elvish Archdruid

## Scoring System

### Total Card Score Calculation

```python
score = (
    (generic_tag_overlap × 0.1) +
    (strategic_tag_overlap × 0.5) +
    (complementary_pair_bonus) +  # +50 if qualified
    (three_way_bonus) +           # +30 if qualified
    (global_scaling_score) +      # 0-20 capped
    (tribal_bonus)                # +5-100 based on count
)
```

### Score Interpretation

| Score Range | Interpretation | Example |
|-------------|----------------|---------|
| 0-10 | Minimal synergy | Generic utility cards |
| 10-30 | Moderate synergy | Cards that share some tags |
| 30-60 | Strong synergy | Core strategy pieces |
| 60-100 | Very strong synergy | Combo pieces, tribal payoffs |
| 100+ | Exceptional synergy | Perfect fit, multiple synergies |

### Example Calculations

#### Example 1: Puresteel Paladin in Equipment Deck
- Equipment deck: 12 equipment, 8 equipment_matters cards
- **Local**: equipment_matters (0.5 × 8) = 4.0
- **Complementary**: equipment + equipment_matters = +50.0
- **Global**: scales_with_equipment (0.5 × 12) = 6.0
- **Total**: **60.0 points**

#### Example 2: Inspiring Statuary in Artifact Deck
- Artifact deck: 25 artifacts, 5 artifact_synergy cards
- **Local**: artifact_synergy (0.5 × 5) = 2.5
- **Global**: scales_with_artifacts (0.4 × 25) = 10.0 (capped at 20)
- **Total**: **12.5 points**

#### Example 3: Panharmonicon in ETB Deck
- ETB deck: 15 has_etb cards, 3 flicker cards
- **Local**: flicker (0.5 × 3) = 1.5
- **Complementary**: has_etb + flicker = +50.0 (needs 5+ ETB)
- **Total**: **51.5 points**

## Examples

### Complete Synergy Chain: Blink Deck

**Core Cards**:
1. **Mulldrifter** (has_etb, card_draw)
2. **Ghostly Flicker** (flicker)
3. **Archaeomancer** (has_etb, recursion_spell)
4. **Panharmonicon** (trigger_doubler)

**Synergies Detected**:
- Mulldrifter ↔ Ghostly Flicker: **ETB → Payoff** (+50)
- Archaeomancer ↔ Ghostly Flicker: **Recursion Loop** (+50)
- Panharmonicon ↔ Mulldrifter: **ETB Doubler** (+50)
- Panharmonicon ↔ Archaeomancer: **ETB Doubler** (+50)

**Total Deck Score**: Very High (multiple combo lines)

### Complete Synergy Chain: Token Aristocrats

**Core Cards**:
1. **Bitterblossom** (token_gen)
2. **Goblin Bombardment** (sacrifice_outlet, sac_creature)
3. **Blood Artist** (death_trigger)
4. **Pitiless Plunderer** (death_trigger, token_gen)

**Synergies Detected**:
- Bitterblossom ↔ Goblin Bombardment: **Token → Sacrifice** (+50)
- Blood Artist ↔ Goblin Bombardment: **Death → Sacrifice** (+50)
- Pitiless Plunderer ↔ Blood Artist: **Death Trigger Chain** (+50)
- Pitiless Plunderer ↔ Bitterblossom: **Token Synergy** (local)

**Total Deck Score**: Exceptional (infinite combo potential)

## Tag Detection Patterns

### Sample Patterns (from create_preprocessed_cards.py)

```python
# ETB Detection
if re.search(r'when .* enters the battlefield', text):
    tags.append('has_etb')

# Equipment Detection
if 'equipment' in type_line.lower():
    tags.append('equipment')

# Trigger Doubler Detection
if re.search(r'triggers an additional time', text):
    tags.append('trigger_doubler')

# Scaling Detection
if re.search(r'for each artifact you control', text):
    tags.append('scales_with_artifacts')

# Tutor Detection (with restrictions)
if 'search your library for' in text:
    if re.search(r'with toughness (\d+) or less', text):
        restriction = f'toughness_restriction_{match.group(1)}'
```

## Future Enhancements

Planned improvements to the synergy system:

1. **Storm synergies**: Detect and score storm strategies
2. **Voltron scoring**: Better detection of commander damage strategies
3. **Color-based synergies**: Devotion, color matters effects
4. **Mana value synergies**: CMC matters (Cascade, X spells)
5. **Planeswalker synergies**: Proliferate, superfriends
6. **Energy counters**: Kaladesh energy mechanics
7. **Historic synergies**: Legendary, artifact, saga synergies

## Troubleshooting

### Synergy Not Detected

1. **Check tag presence**: Use recommendations debug mode
2. **Verify threshold**: Minimum counts may not be met
3. **Check text patterns**: Card text may not match regex
4. **Regenerate database**: Tags may be missing from preprocessed DB

### Score Too High/Low

1. **Review weights**: Check strategic_tags classification
2. **Check caps**: Global synergies are capped at 10-20
3. **Verify counts**: Complementary pairs need minimum counts
4. **Check tribal bonus**: 10+ creatures gives huge (+100) bonus

### Missing Restrictions

1. **Tutor restrictions**: Power/toughness/CMC are validated
2. **Update extractors**: Add new restriction patterns
3. **Test with card**: Use Python REPL to test extraction

---

For implementation details, see [DEVELOPMENT.md](DEVELOPMENT.md)
