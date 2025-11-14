# System Architecture Diagram

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ WEB INTERFACE (app.py)                                          │
│ - Dash web server                                               │
│ - Card input/visualization                                      │
│ - Synergy graph display                                         │
└──────────┬──────────────────────────────────────────────────────┘
           │
           ├─────────────────┬──────────────────────┬──────────────┐
           │                 │                      │              │
       ┌───▼───┐      ┌─────▼────┐        ┌────────▼──────┐  ┌────▼────┐
       │Archidekt      │ Scryfall  │       │ Commander     │  │ Local   │
       │ Importer      │ API       │       │ Spellbook     │  │ Cache   │
       └───┬───┘       └─────┬────┘       └────────┬──────┘  └────┬────┘
           │                 │                      │              │
           └─────────────────┼──────────────────────┼──────────────┘
                             │                      │
                    ┌────────▼──────────────────────▼──────────┐
                    │ Deck Model (src/models/deck.py)          │
                    │ - Cards list                             │
                    │ - Synergies dictionary                   │
                    │ - Metadata                               │
                    └────────┬─────────────────────────────────┘
                             │
            ┌────────────────┼─────────────────────┐
            │                │                     │
      ┌─────▼─────┐  ┌───────▼─────────┐  ┌───────▼────────┐
      │Synergy    │  │ Combo Detector  │  │ Deck Simulator │
      │Engine     │  │ (Verified)      │  │ (Game sim)     │
      │(src/...)  │  │ (src/api/...)   │  │ (Simulation/)  │
      └─────┬─────┘  └───────┬─────────┘  └───────┬────────┘
            │                │                     │
      ┌─────▼──────────────────────┐      ┌────────▼──────────────┐
      │ Synergy Pairs Dictionary    │      │ Game Simulation       │
      │ Card1 || Card2 → Strength   │      │ - Turn-by-turn logic  │
      │                            │      │ - 30+ metrics         │
      │ Organized by category      │      │ - Combat resolution   │
      └─────┬──────────────────────┘      └────────┬──────────────┘
            │                                      │
            └──────────────┬───────────────────────┘
                           │
                    ┌──────▼──────────────┐
                    │ Graph Builder       │
                    │ (Cytoscape format)  │
                    │ - Nodes (cards)     │
                    │ - Edges (synergies) │
                    └──────┬──────────────┘
                           │
                    ┌──────▼──────────────┐
                    │ Web Visualization   │
                    │ - Interactive graph │
                    │ - Card details      │
                    │ - Synergy explanations
                    └─────────────────────┘
```

---

## Simulation Loop (Core Engine)

```
simulate_game(deck_cards, commander_card, max_turns=10)
│
└─ Initialize BoardState
   ├─ Shuffle library
   ├─ Draw starting hand (7 cards or mulligan)
   ├─ Detect deck archetype (voltron/go-wide/combo/etc)
   └─ Initialize opponent tracking
   
└─ FOR turn = 1 to max_turns:
   │
   ├─ UNTAP PHASE
   │  └─ Untap all permanents, refresh abilities
   │
   ├─ UPKEEP PHASE
   │  ├─ Advance sagas (chapters)
   │  └─ Trigger upkeep effects
   │
   ├─ DRAW PHASE
   │  └─ Draw 1 card from library
   │
   ├─ MAIN PHASE (Complex AI Loop)
   │  │
   │  ├─ Choose best land to play
   │  │  ├─ Check ETB tapped conditions
   │  │  └─ Trigger landfall effects
   │  │
   │  ├─ Greedy Loop: While can do something:
   │  │  │
   │  │  ├─ Play all mana rocks (without delaying commander)
   │  │  │  └─ Evaluate: simulate + check commander affordable
   │  │  │
   │  │  ├─ Play commander ASAP
   │  │  │  ├─ Pay base cost + command tax (2 per cast)
   │  │  │  └─ Auto-equip available equipment
   │  │  │
   │  │  ├─ Play ramp sorceries (put lands into play)
   │  │  │
   │  │  ├─ Play creatures
   │  │  │  ├─ Check AI hold-back logic
   │  │  │  ├─ Trigger ETB effects
   │  │  │  └─ Apply counter effects (Cathars' Crusade)
   │  │  │
   │  │  └─ Play equipment and attach
   │  │
   │  └─ Optimize leftover mana (instants, abilities)
   │
   ├─ COMBAT PHASE
   │  ├─ All creatures attack
   │  ├─ Generate opponent creatures
   │  ├─ Calculate threat levels
   │  ├─ Opponent chooses to block
   │  ├─ Resolve combat (damage, deaths)
   │  ├─ Trigger death effects
   │  └─ Create treasures (Grim Hireling)
   │
   ├─ INTERACTION PHASE
   │  ├─ Simulate opponent removals
   │  │  ├─ Archetype-aware probability
   │  │  ├─ Target highest power creature
   │  │  └─ Trigger death effects
   │  │
   │  ├─ Simulate board wipes
   │  │  └─ Trigger death effects for all creatures
   │  │
   │  ├─ Attempt reanimation
   │  │  └─ Bring creatures back from graveyard
   │  │
   │  └─ Activate planeswalkers
   │
   ├─ SACRIFICE PHASE
   │  ├─ Check for sacrifice opportunities
   │  │  └─ Sacrifice weak creatures to outlets
   │  │
   │  ├─ Simulate attack triggers
   │  │  └─ Generate tokens on attack (Adeline, Anim Pakal, etc)
   │  │
   │  └─ Calculate drain damage
   │
   ├─ END PHASE
   │  ├─ Trigger end-of-turn treasures (Mahadi)
   │  └─ Check victory conditions
   │
   └─ Record metrics and check if opponent eliminated
   
└─ Return metrics dictionary with 30+ tracked values
```

---

## Class Hierarchy

```
CARD SYSTEM
===========

Card (simulate_game.py)
├─ Core Stats
│  ├─ name, type, mana_cost
│  ├─ power, toughness, base_power, base_toughness
│  └─ is_commander, is_legendary
├─ Keywords
│  ├─ has_haste, has_flash, has_trample
│  ├─ has_lifelink, has_deathtouch, has_vigilance
│  ├─ has_flying, has_menace, is_unblockable
│  └─ has_first_strike
├─ Mana Production
│  ├─ mana_production (int)
│  ├─ produces_colors (list)
│  └─ cost_reduction, has_affinity
├─ Abilities
│  ├─ activated_abilities: list[ManaAbility]
│  ├─ triggered_abilities: list[TriggeredAbility]
│  └─ oracle_text
├─ Special Properties
│  ├─ token_type ('Treasure', 'Food', etc)
│  ├─ counters: dict
│  ├─ death_trigger_value (drain on death)
│  ├─ sacrifice_outlet (bool)
│  ├─ creates_tokens: list
│  └─ is_saga, saga_chapters, saga_current_chapter
└─ Methods
   ├─ add_counter(type, amount)
   ├─ remove_counter(type, amount)
   └─ take_damage(amount)


ABILITY SYSTEM
==============

ManaAbility / ActivatedAbility (mtg_abilities.py)
├─ cost: str (e.g., "{T}" or "{1}{R}")
├─ produces_colors: list[str]
├─ tap: bool
└─ requires_equipped: bool

TriggeredAbility (mtg_abilities.py)
├─ event: str ("etb", "attack", "landfall", "damage")
├─ effect: Callable[[BoardState], Any]
├─ description: str
├─ requires_haste: bool
├─ requires_flash: bool
└─ requires_another_legendary: bool


BOARD STATE SYSTEM
==================

BoardState (boardstate.py)
├─ ZONES
│  ├─ library: list[Card]
│  ├─ hand: list[Card]
│  ├─ graveyard: list[Card]
│  ├─ exile: list[Card]
│  ├─ lands_untapped/tapped: list[Card]
│  ├─ creatures: list[Card]
│  ├─ artifacts: list[Card]
│  ├─ enchantments: list[Card]
│  ├─ planeswalkers: list[Card]
│  └─ command_zone: list[Card] (commander)
├─ GAME STATE
│  ├─ mana_pool: list[tuple(colors)]
│  ├─ turn: int
│  ├─ life_total: int
│  └─ opponent: dict[] (3+ opponents)
├─ TRACKING
│  ├─ equipment_attached: dict (equipment → creature)
│  ├─ drain_damage_this_turn: int
│  ├─ tokens_created_this_turn: int
│  ├─ creatures_died_this_turn: int
│  ├─ creatures_sacrificed: int
│  └─ commander_cast_count: int (for command tax)
├─ AI STATE
│  ├─ deck_archetype: str (voltron/go-wide/combo/etc)
│  ├─ removal_probability: float
│  ├─ board_wipe_probability: float
│  └─ threat_threshold: int
└─ MECHANICS
   ├─ Mana Management
   │  ├─ play_card(card)
   │  ├─ play_land(card)
   │  ├─ play_creature(card)
   │  ├─ play_artifact(card)
   │  ├─ play_equipment(card)
   │  ├─ play_sorcery(card)
   │  └─ equip_equipment(equipment, creature)
   ├─ Triggers
   │  ├─ _execute_triggers(event, card)
   │  ├─ _trigger_landfall()
   │  ├─ deal_damage(creature, amount)
   │  └─ attack(creature)
   ├─ Tokens & Treasures
   │  ├─ create_token(name, power, toughness)
   │  └─ create_treasure()
   ├─ Sacrifice & Death
   │  ├─ sacrifice_creature(creature)
   │  └─ trigger_death_effects(creature)
   ├─ Combat
   │  └─ resolve_combat_with_blockers()
   ├─ Interactions
   │  ├─ generate_opponent_creatures(turn)
   │  ├─ simulate_removal()
   │  ├─ simulate_board_wipe()
   │  └─ attempt_reanimation()
   ├─ Anthems
   │  ├─ calculate_anthem_bonus(creature)
   │  ├─ get_effective_power(creature)
   │  └─ get_effective_toughness(creature)
   └─ AI
      ├─ should_hold_back_creature(creature)
      ├─ assess_primary_threat()
      ├─ choose_land_to_play()
      └─ optimize_mana_usage()
```

---

## Data Flow for Synergy Analysis

```
┌──────────────────────────┐
│ Load Deck (Archidekt URL)│
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ Fetch Cards from APIs            │
│ - Archidekt: Deck structure      │
│ - Scryfall: Card details         │
│ - Local cache: Pre-loaded data   │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ Build Deck Model                 │
│ deck.cards = [Card1, Card2, ...]│
│ deck.synergies = {} (empty)      │
└────────────┬─────────────────────┘
             │
             ├─────────────────────────────────┐
             │                                 │
             ▼                                 ▼
    ┌──────────────────┐          ┌──────────────────────┐
    │ Detect Verified  │          │ Analyze Synergies    │
    │ Combos           │          │ (src/synergy_engine) │
    │                  │          │                      │
    │ - Query combo DB │          │ For each card pair:  │
    │ - Find matches   │          │ ├─ Check triggers    │
    │ - Get steps      │          │ ├─ Check keywords    │
    │ - Get results    │          │ ├─ Check effects     │
    │ - Assign value   │          │ ├─ Calculate score   │
    │                  │          │ └─ Categorize        │
    └──────────┬───────┘          └──────────┬───────────┘
               │                             │
               └─────────────────┬───────────┘
                                 │
                        ┌────────▼──────────┐
                        │ Merge Results     │
                        │                   │
                        │ deck.synergies = {│
                        │   "Card1||Card2": │
                        │   {               │
                        │     'card1': ..., │
                        │     'card2': ..., │
                        │     'total_weight',
                        │     'synergies': {│
                        │       'triggers',│
                        │       'combos',   │
                        │       'themes'    │
                        │     }             │
                        │   }               │
                        │ }                 │
                        └────────┬──────────┘
                                 │
                        ┌────────▼──────────┐
                        │ Build Graph       │
                        │                   │
                        │ Nodes = cards     │
                        │ Edges = synergies │
                        │ Weight = strength │
                        └────────┬──────────┘
                                 │
                        ┌────────▼──────────┐
                        │ Visualize         │
                        │                   │
                        │ Cytoscape graph   │
                        │ Interactive UI    │
                        └───────────────────┘
```

---

## Synergy Categories & Values

```
TRIGGERS (High value: 5.0-8.0)
├─ ETB Triggers ("when enters, draw a card")
├─ Death Triggers ("when dies, drain")
├─ Attack Triggers ("whenever attacks, create token")
├─ Landfall Triggers ("when land enters, +1/+1")
└─ Damage Triggers ("whenever dealt damage")

BENEFITS (Medium-High: 3.0-6.0)
├─ Card Advantage ("draw cards" synergy)
├─ Mana Generation ("ramp synergies")
├─ Token Creation ("tokens + sacrifice outlets")
└─ Life Gain ("lifelink + drain protection")

COMBO (Highest: 10.0)
├─ Verified Combos (from Commander Spellbook)
├─ Infinite Mana (e.g., Basalt Monolith + Rings)
├─ Infinite Tokens (doubler + generator)
└─ Infinite Damage (drain outlet + token loop)

TRIBAL (Medium: 2.0-4.0)
├─ Elf Synergies
├─ Zombie Synergies
├─ Dragon Synergies
└─ Creature Type synergies

THEMES (Medium: 2.0-5.0)
├─ Sacrifice ("outlets + payoffs")
├─ Graveyard ("reanimation synergies")
├─ Tokens ("generation + payoffs")
├─ Counters ("+1/+1 + proliferate")
└─ Equipment ("ramp + keywords")

ROLE INTERACTIONS (Low-Medium: 1.0-3.0)
├─ Ramp + Draw
├─ Sacrifice + Tokens
├─ Removal + Card Draw
└─ Protection + Voltron
```

---

## Oracle Text Parser Pipeline

```
Card Oracle Text
    │
    ├─ parse_mana_production()
    │  └─ Returns: int (mana per activation)
    │
    ├─ parse_etb_triggers_from_oracle()
    │  ├─ Pattern: "when .* enters.*draw"
    │  ├─ Pattern: "when .* enters.*proliferate"
    │  └─ Returns: list[TriggeredAbility]
    │
    ├─ parse_attack_triggers_from_oracle()
    │  ├─ Pattern: "whenever .* attacks.*draw"
    │  ├─ Pattern: "whenever .* attacks.*+1/+1"
    │  └─ Returns: list[TriggeredAbility]
    │
    ├─ parse_damage_triggers_from_oracle()
    │  └─ Pattern: "whenever .* is dealt damage"
    │
    ├─ parse_activated_abilities()
    │  └─ Pattern: "{T}: add {R}{G}"
    │
    └─ parse_etb_tapped_conditions()
       └─ Pattern: "enters tapped unless you control X"
```

---

## Testing Architecture

```
Unit Tests (Simulation/tests/)
├─ Ability Tests
│  ├─ test_activated_ability.py (mana abilities)
│  ├─ test_triggered_ability.py (trigger system)
│  └─ test_attack_triggers.py (combat triggers)
├─ Mechanic Tests
│  ├─ test_counters.py (+1/+1 tracking)
│  ├─ test_proliferate.py (counter doubling)
│  ├─ test_landfall_triggers.py (land entry)
│  └─ test_draw_effects.py (card draw)
├─ Land Tests
│  ├─ test_fetch_land.py (fetch mechanics)
│  ├─ test_land_selection.py (heuristics)
│  └─ test_first_strike_if_equipped.py (equipment)
└─ Integration Tests
   ├─ test_starting_hand.py (mulligan logic)
   ├─ test_legendary_attack_trigger.py (complex)
   ├─ test_forth_eorlingas.py (saga mechanics)
   ├─ test_openai_parser.py (GPT parsing)
   ├─ test_load_deck_csv.py (deck loading)
   └─ test_parallel_simulation.py (performance)

Performance Tests (root)
├─ test_add_card_performance.py
├─ test_parallel_processing.py
├─ test_three_way_performance.py
└─ test_simulation.py
```

---

## Key Interaction Points for Landfall Development

```
Landfall Archetype Implementation
├─ Oracle Text Parsing
│  └─ parse_landfall_triggers_from_oracle()
│     ├─ Pattern: "whenever a land enters"
│     └─ Create: TriggeredAbility(event="landfall", ...)
│
├─ Card Properties
│  └─ card.triggered_abilities += landfall_trigger
│
├─ Board State Mechanics
│  ├─ play_land()
│  │  └─ Calls: board._trigger_landfall()
│  │
│  └─ _trigger_landfall()
│     ├─ Execute all "landfall" events
│     ├─ Trigger token creation
│     ├─ Apply +1/+1 counters
│     └─ Deal damage (optional)
│
├─ Simulation Integration
│  ├─ Track: landfall_triggers_activated (per turn)
│  ├─ Combine: landfall + ramp (land search)
│  └─ Calculate: total mana from landfall ramp
│
├─ Synergy Detection
│  ├─ Fetch lands + landfall creatures
│  ├─ Land ramp + land enter payoffs
│  ├─ Token creation + sacrifice outlets
│  └─ Mana generation + spell payoffs
│
└─ Testing
   ├─ test_landfall_basics.py
   ├─ test_landfall_tokens.py
   ├─ test_fetch_landfall.py
   ├─ test_landfall_ramp.py
   └─ test_landfall_archetype.py
```

