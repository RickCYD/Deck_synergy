# MTG Deck Synergy Simulation - Architecture Overview

## Project Overview

This is a Magic: The Gathering (MTG) Commander deck simulation engine that:
- Simulates deck games turn-by-turn
- Models complex card mechanics and interactions
- Analyzes deck synergies
- Implements aristocrats and other complex mechanics

**Current State**: Priority 1-2 mechanics implemented; working on Priority 3 (Landfall Archetype)

---

## Directory Structure

```
Deck_synergy/
├── Simulation/                    # Core game simulation engine
│   ├── simulate_game.py          # Main simulation loop & turn structure
│   ├── boardstate.py             # Board state management & mechanics
│   ├── Creature.py               # Legacy creature class
│   ├── mtg_abilities.py          # Ability definitions (ManaAbility, TriggeredAbility)
│   ├── oracle_text_parser.py    # Parse card abilities from text
│   ├── turn_phases.py            # Turn phase implementations
│   ├── deck_loader.py            # Load cards from data files
│   ├── draw_starting_hand.py     # Starting hand logic
│   └── tests/                    # Unit tests for mechanics
│       ├── test_landfall_triggers.py
│       ├── test_attack_triggers.py
│       ├── test_triggered_ability.py
│       ├── test_counters.py
│       └── ... (20+ test files)
├── src/                          # Synergy analysis & web framework
│   ├── simulation/
│   │   ├── deck_simulator.py     # Simulation wrapper
│   │   └── mana_simulator.py
│   ├── models/
│   │   ├── combo.py             # Combo detection models
│   │   ├── deck.py
│   │   └── deck_session.py
│   ├── synergy_engine/           # Synergy detection
│   │   ├── analyzer.py           # Main synergy analyzer
│   │   ├── combo_detector.py     # Verified combo detection
│   │   ├── card_advantage_synergies.py
│   │   └── ... (various synergy extractors)
│   ├── api/
│   │   ├── scryfall.py           # Scryfall card API
│   │   ├── commander_spellbook.py # Combo database API
│   │   └── archidekt.py          # Archidekt deck import
│   └── utils/                    # Card analysis utilities
│       ├── keyword_extractors.py
│       ├── token_extractors.py
│       └── ... (role/ability extractors)
├── data/cards/                   # Card databases
│   ├── cards-minimal.json        # ~50MB minimal dataset
│   └── cards-preprocessed.json   # ~17MB preprocessed dataset
├── app.py                        # Flask/Dash web interface (142KB!)
└── docs/                         # Documentation
    ├── COMBO_DETECTION.md
    └── ... (various docs)
```

---

## Core Architecture - The Simulation Loop

### Main Simulation Flow (simulate_game.py)

**Entry Point**: `simulate_game(deck_cards, commander_card, max_turns=10, verbose=True)`

**Turn Structure**:
1. **Untap Phase** - Untap permanents, refresh abilities
2. **Upkeep Phase** - Trigger upkeep effects, advance sagas
3. **Draw Phase** - Draw one card from library
4. **Main Phase** - Complex greedy AI loop:
   - Play one land (using land selection heuristics)
   - Play all mana rocks without delaying commander
   - Play commander as soon as affordable
   - Play ramp sorceries
   - Play creatures with AI hold-back logic
   - Play equipment
   - Optimize leftover mana usage
5. **Combat Phase** - Resolve combat with opponent blocking
6. **Opponent Phase** - Generate opponent creatures, attempt removals
7. **Aristocrats Phase** - Trigger sacrifice opportunities & death effects
8. **End Phase** - Check for end-of-turn treasures

**Key Metrics Tracked** (30+ metrics):
- `lands_played`, `total_mana`, `castable_spells`
- `combat_damage`, `drain_damage` (separate from combat!)
- `tokens_created`, `creatures_sacrificed`
- `total_power`, `total_toughness`, `power_from_counters`
- Per-turn mana availability by color
- Opponent threat levels

---

## Board State Management (boardstate.py)

The `BoardState` class is the central manager for all board information and mechanics.

### Key Collections
```python
board.library           # Deck cards (shuffled)
board.hand              # Cards in hand
board.graveyard         # Dead permanents
board.lands_untapped/tapped
board.creatures         # Battlers
board.artifacts         # Mana rocks, treasures, etc.
board.enchantments      # Auras, enchantment effects
board.planeswalkers     # Walkers

board.mana_pool         # Available mana: list[tuple(colors)]
```

### Key Subsystems

#### 1. **Mana Management**
- `Mana_utils.parse_req(cost_str)` - Parse mana costs to colors + generic
- `Mana_utils.can_pay(cost_str, pool)` - Check if pool can pay cost
- `Mana_utils.pay(cost_str, pool)` - Consume mana from pool
- `mana_sources_from_board()` - Calculate available mana from lands, artifacts, creatures

#### 2. **Card Playing**
- `play_card(card)` - Smart dispatcher to play_<type> methods
- `play_land()` - Check ETB tapped conditions, trigger landfall
- `play_creature()` - Pay mana, add to battlefield, trigger ETB + counters
- `play_artifact()` / `play_equipment()` - Mana rocks & equipment
- `play_commander()` - Track command tax (2 mana per cast)

#### 3. **Trigger System**
```python
board._execute_triggers(event, card, verbose)
```
Supported events:
- `"etb"` - Enters the battlefield
- `"equip"` - Equipment attached
- `"attack"` - Creature attacks
- `"landfall"` - Land enters
- `"damage"` - Creature takes damage

#### 4. **Archetype Detection**
`board._analyze_deck_strategy(deck)` - Detects archetype and adjusts opponent interaction rates:
- **Voltron** - Many equipment, few creatures (20% removal)
- **Go-wide** - Token generators (120% removals, 80% wipes)
- **Aggro** - Many creatures (standard rates)
- **Midrange** - Balanced (90% of base rates)
- **Combo/Control** - Few creatures (50% removal)

---

## Card System (simulate_game.py)

The `Card` class represents all permanents (creatures, artifacts, etc.):

### Core Properties
```python
card.name, card.type, card.mana_cost
card.power, card.toughness
card.has_haste, card.has_flash, card.has_trample
card.has_lifelink, card.has_deathtouch, card.has_vigilance
card.is_unblockable, card.is_commander, card.is_legendary
```

### Advanced Properties
```python
card.mana_production       # Mana produced (for rocks/dorks)
card.produces_colors       # Colors produced

card.activated_abilities   # list[ActivatedAbility]
card.triggered_abilities   # list[TriggeredAbility]
card.oracle_text           # Full oracle rules text

card.token_type            # 'Treasure', 'Food', 'Clue', etc.
card.counters              # dict: {"+1/+1": count, ...}
card.death_trigger_value   # Drain value when dies
card.sacrifice_outlet      # Can sacrifice creatures
```

### Key Methods
```python
card.add_counter(type, amount)      # Add counters, updates power/toughness
card.remove_counter(type, amount)   # Remove counters
card.take_damage(amount)            # Mark damage
```

---

## Ability System (mtg_abilities.py)

### Two Ability Types

#### 1. **ManaAbility (ActivatedAbility)**
```python
@dataclass
class ManaAbility:
    cost: str                   # "{T}" or "{R}{G}" etc.
    produces_colors: List[str]  # ['R', 'G'] or ['Any']
    tap: bool                   # Does it tap?
    requires_equipped: bool     # Only works when equipped?
```

#### 2. **TriggeredAbility**
```python
@dataclass
class TriggeredAbility:
    event: str                  # "etb", "attack", "landfall", "damage"
    effect: Callable            # Function to execute
    description: str            # "draw 2 cards"
    requires_haste: bool        # Only if creature has haste?
    requires_flash: bool        # Only if creature has flash?
    requires_another_legendary: bool
```

**Examples of trigger effects**:
```python
def sonic_attack_effect(card):
    def effect(board_state):
        card.add_counter("+1/+1")
    return effect

def proliferate_effect():
    def effect(board_state):
        board_state.proliferate()
    return effect
```

---

## Implemented Mechanics (Priority 1-2)

### Priority 1: Aristocrats Mechanics
- **Sacrifice outlets** - Cards that sacrifice creatures for value
- **Death triggers** - Drain effects when creatures die
  - `Zulaport Cutthroat` - Each opponent loses 1 life per creature death
  - `Cruel Celebrant` - Same effect
  - `Bastion of Remembrance` - Enchantment payoff
- **Token creation** - Creatures that make tokens
- **Drain mechanics** - Combat + aristocrat drain tracked separately

**Key Methods**:
```python
board.sacrifice_creature(creature)      # Remove from battlefield, trigger effects
board.trigger_death_effects(creature)   # Drain + treasure generation
board.check_for_sacrifice_opportunities()
```

### Priority 2: Token & Treasure Mechanics
- **Token generation** - Create creature tokens
- **Token doublers** - `Mondrak`, `Doubling Season`, `Parallel Lives`
- **Treasure tokens** - Sacrifice for any color mana
- **+1/+1 counters** - `Cathars' Crusade` triggers on ETB
- **Attack triggers** - Token generation on attack
  - `Adeline, Resplendent Cathar` - Creates X tokens (X = # opponents)
  - `Anim Pakal, Thousandth Moon` - Creates gnomes
  - `Brimaz, King of Oreskos` - Creates cat tokens
  - `Hero of Bladehold` - Creates soldier tokens

**Key Methods**:
```python
board.create_token(name, power, toughness)  # Auto-handles doublers
board.apply_etb_counter_effects(creature)   # Cathars' Crusade
board.simulate_attack_triggers()            # Token generation on attack
board.check_end_of_turn_treasures()         # Mahadi treasures
board.create_treasure()                     # Single treasure
```

### Priority 3: Anthem/Global Buff System (CURRENT)
- **Anthem effects** - Creatures you control get +X/+X
  - `Glorious Anthem` - All creatures get +1/+1
  - `Intangible Virtue` - Tokens get +1/+1
  - `Honor of the Pure` - White creatures get +1/+1
  - `Spear of Heliod` - All creatures get +1/+1
  - `Benalish Marshal` - Creatures with protection counters get +1/+1

**Key Methods**:
```python
board.calculate_anthem_bonus(creature)  # Returns (power_bonus, toughness_bonus)
board.get_effective_power(creature)     # Base power + equipment + counters + anthems
board.get_effective_toughness(creature) # Same for toughness
```

---

## Oracle Text Parser (oracle_text_parser.py)

Automatically extracts abilities from card oracle text:

### Parsing Functions
```python
parse_mana_production(oracle_text, type_line, card_name)
    # Returns: int (max mana per activation)
    # Examples: "Sol Ring" → 2, "Forest" → 1

parse_etb_triggers_from_oracle(text)
    # Returns: list[TriggeredAbility]
    # Finds: "When X enters, draw N cards"

parse_attack_triggers_from_oracle(text)
    # Returns: list[TriggeredAbility]
    # Finds: "Whenever X attacks, draw N cards"

parse_damage_triggers_from_oracle(text)
    # Returns: list[TriggeredAbility]
    # Finds: "Whenever X is dealt damage..."

parse_activated_abilities(text)
    # Returns: list[ActivatedAbility]
    # Finds: "{T}: add {R}{G}"

parse_etb_tapped_conditions(text)
    # Returns: dict (conditions for ETB tapped status)
    # Examples: "enters tapped unless you control a Swamp"
```

---

## Card Loading (deck_loader.py)

### Data Sources
1. **cards-minimal.json** (35MB) - Basic card properties
2. **cards-preprocessed.json** (17MB) - Pre-parsed abilities

### Card Building
```python
build_card_from_row(row):
    # Parses CSV/database row into Card object
    # - Extracts mana production
    # - Parses fetch land abilities
    # - Parses triggered abilities from oracle text
    # - Determines card type, keywords, etc.
```

---

## Combat System (boardstate.py)

### Combat Resolution
```python
board.resolve_combat_with_blockers(verbose=False) -> int
```

**Flow**:
1. Select target opponent (highest threat level)
2. For each creature:
   - Check evasion (flying, unblockable, menace)
   - Determine if blocked
   - Apply combat damage
   - Remove dead creatures
3. Trigger death effects for blocked creatures
4. Create treasures for damage-based effects (Grim Hireling)
5. Track commander damage

**Keywords Supported**:
- `has_flying` - Harder to block
- `has_menace` - Requires 2 blockers
- `has_lifelink` - Gain life on damage
- `has_deathtouch` - 1 damage kills
- `is_unblockable` - Cannot be blocked

---

## Opponent Modeling (boardstate.py)

### Opponent State
```python
opponent = {
    'name': 'Opponent_1',
    'life_total': 40,
    'creatures': [...],
    'commander_damage': 0,
    'is_alive': True,
    'threat_level': 0.0-1.0
}
```

### Opponent Mechanics
```python
board.generate_opponent_creatures(turn)  # Create creatures each turn
board.calculate_threat_levels()          # Update threat values
board.simulate_removal(verbose)          # Remove your creatures
board.simulate_board_wipe(verbose)       # Destroy all creatures
board.attempt_reanimation()              # Reanimate from graveyard
```

---

## Interaction System (boardstate.py)

**Base Rates** (archetype-aware):
- Removal: 5% per turn (0-5% depending on archetype)
- Board wipes: 3% per turn (0-3% depending on archetype)
- Reanimation: 5% + 1% per card in graveyard, capped at 15%

**Strategic Adjustments**:
- Voltron: 40% removal (protection from being focused)
- Go-wide: 120% removal, 80% wipes
- Aggro: Standard rates
- Combo: 50% removal (harder to remove combo pieces)

---

## Test Coverage

### Test Files (~28 test files)
```
Simulation/tests/
├── test_landfall_triggers.py    # Landfall mechanic
├── test_attack_triggers.py      # Attack-based triggers
├── test_triggered_ability.py    # Trigger system
├── test_counters.py             # Counter mechanics
├── test_draw_effects.py         # Draw triggers
├── test_activated_ability.py    # Activated ability system
├── test_parallel_simulation.py  # Parallel execution
├── test_proliferate.py          # Proliferate mechanic
└── ... (20+ more)
```

---

## What's Currently Implemented

### ✅ Complete
- Simulation loop with turn structure
- Mana system & spell casting
- Basic combat resolution
- Equipment system
- Saga mechanics
- Artifact ramp optimization
- Land ETB tapped conditions
- Fetch lands
- Landfall triggers
- Death triggers & aristocrats drain
- Token generation & token doublers
- +1/+1 counter mechanics (Cathars' Crusade)
- Attack triggers for token generation
- Command tax tracking
- Opponent modeling & interaction
- Board wipes & removal simulation
- Anthem/global buff system

### 🚧 In Progress
- **Landfall Archetype** - Integration test suite
  - Fetch land interactions
  - Ramp + landfall synergies
  - Treasure generation from landfall
  - Token generation on landfall

### 📋 Future Priorities
- Proliferate optimizations
- Flash mechanics
- Stax/tax effects
- More complex trigger interactions
- Parallel simulation optimization
- Additional combat keywords

---

## Key Takeaways for Development

### 1. **Architecture Philosophy**
- **Simulation-first**: Mechanics validated through game simulation
- **Turn-based phases**: Strictly follows MTG phase structure
- **Oracle text parsing**: Auto-extract abilities from card text
- **Flexible triggers**: Events-based system for any trigger type

### 2. **Adding New Mechanics**
```python
# 1. Add property to Card class
card.my_new_mechanic = True

# 2. Add parsing to oracle_text_parser.py
def parse_my_mechanic(text):
    # Extract from oracle text
    return ability

# 3. Add trigger/effect to BoardState
def trigger_my_mechanic(self, verbose):
    # Implement logic

# 4. Call in appropriate phase
# (untap/upkeep/main/combat/end)

# 5. Add test
def test_my_mechanic():
    # Verify behavior
```

### 3. **Common Patterns**
- **Death triggers**: `board.trigger_death_effects(creature)`
- **ETB effects**: Called automatically via `_execute_triggers("etb", card)`
- **Token creation**: `board.create_token()` handles doublers
- **Mana checking**: Always use `Mana_utils.can_pay()` before casting

### 4. **Debugging Tips**
- Always run with `verbose=True` for detailed turn logs
- Check `board.mana_pool` to see available mana
- Look at `board.turn` for current turn number
- Check `metrics["drain_damage"]` for aristocrats tracking

---

## File Sizes & Complexity

| File | Lines | Purpose |
|------|-------|---------|
| app.py | 4,200 | Web UI (Flask/Dash) |
| simulate_game.py | 700 | Game loop |
| boardstate.py | 2,100+ | Board mechanics |
| oracle_text_parser.py | 500+ | Card parsing |
| mtg_abilities.py | 80 | Ability types |
| deck_loader.py | 200 | Card loading |

---

## Next Steps for Landfall

The current branch is working on implementing the Landfall Archetype (Priority 3.1).

**Already in place**:
- Landfall trigger infrastructure
- ETB tapped conditions parsing
- Fetch land mechanics
- Land selection heuristics

**Still needed**:
- Complete integration tests
- Landfall-specific synergy detection
- Ramp optimization for landfall decks
- Token generation from landfall triggers

