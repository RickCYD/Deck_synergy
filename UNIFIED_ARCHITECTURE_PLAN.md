# Unified Synergy & Simulation Architecture Plan

**Date:** 2025-11-14
**Goal:** Create a unified system where oracle text is parsed once, synergies automatically work in simulation, and adding new mechanics updates both systems simultaneously.

---

## 🎯 Current Problems

### 1. **Duplicate Oracle Text Parsing**
- `src/utils/*_extractors.py` - Used by synergy detection (14 files)
- `Simulation/oracle_text_parser.py` - Used by simulation (1 file)
- **Problem:** Same mechanics parsed twice with different logic

### 2. **Disconnected Systems**
- Synergy detection finds interactions but simulation doesn't use them
- Adding rally synergies didn't improve simulation results
- No feedback loop between the two systems

### 3. **Missing Simulation Methods**
- `BoardState.grant_keyword_until_eot()` - Doesn't exist
- `BoardState.put_counter_on_creatures()` - Doesn't exist
- Rally triggers parsed but not executed

### 4. **Inconsistent Logic**
- Rally detection in `etb_extractors.py` vs `oracle_text_parser.py`
- Prowess handled differently in each system
- No single source of truth

---

## 🏗️ Solution Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    UNIFIED CARD PARSER                       │
│  (Single source of truth for all card abilities)            │
│  Location: src/core/card_parser.py                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ├──────────────┬──────────────┐
                              ▼              ▼              ▼
                    ┌─────────────┐  ┌─────────────┐  ┌──────────┐
                    │  EXTRACTORS │  │   TRIGGERS  │  │ ABILITIES │
                    │  (Read-only)│  │  (Registry) │  │ (Effects) │
                    └─────────────┘  └─────────────┘  └──────────┘
                              │              │              │
                ┌─────────────┴──────────────┴──────────────┴─────┐
                │                                                  │
                ▼                                                  ▼
    ┌──────────────────────┐                        ┌──────────────────────┐
    │  SYNERGY DETECTION   │                        │    GAME SIMULATION   │
    │  (Finds interactions)│                        │  (Executes triggers) │
    └──────────────────────┘                        └──────────────────────┘
                │                                                  │
                │                  ┌──────────────┐               │
                └─────────────────>│   METRICS    │<──────────────┘
                                   │ (Combined)   │
                                   └──────────────┘
```

---

## 📋 Implementation Plan

---

## **PART 1: Unified Card Parser** (Core Foundation)

### 1.1 Create Central Card Parser

**File:** `src/core/card_parser.py`

```python
"""
Unified Card Parser - Single Source of Truth
All card ability extraction happens here.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Set
import re

@dataclass
class TriggerAbility:
    """Unified trigger representation"""
    event: str  # 'etb', 'attack', 'death', 'cast_spell', 'rally', etc.
    condition: Optional[str]  # e.g., "if you control an artifact"
    effect: str  # What happens
    effect_type: str  # 'damage', 'draw', 'anthem', 'tokens', etc.
    targets: List[str]  # What's affected
    value: float  # Numeric value if applicable
    metadata: Dict  # Additional info

@dataclass
class StaticAbility:
    """Static effects like anthems, cost reduction"""
    ability_type: str  # 'anthem', 'cost_reduction', 'keyword_grant'
    effect: str
    targets: List[str]
    value: float
    conditions: List[str]

@dataclass
class ActivatedAbility:
    """Activated abilities with costs"""
    cost: str  # Mana/tap/sacrifice cost
    effect: str
    effect_type: str
    value: float

@dataclass
class CardAbilities:
    """Complete parsed card abilities"""
    name: str
    triggers: List[TriggerAbility]
    static_abilities: List[StaticAbility]
    activated_abilities: List[ActivatedAbility]
    keywords: Set[str]
    creature_types: Set[str]

    # Cached flags for quick checks
    has_etb: bool
    has_rally: bool
    has_prowess: bool
    creates_tokens: bool
    is_removal: bool
    is_ramp: bool
    is_draw: bool

class UnifiedCardParser:
    """
    Parses card oracle text ONCE and extracts all abilities.
    Used by both synergy detection and simulation.
    """

    def parse_card(self, card: Dict) -> CardAbilities:
        """
        Main entry point - parse everything about a card.

        Args:
            card: Card dict with 'oracle_text', 'type_line', etc.

        Returns:
            CardAbilities with all extracted information
        """
        text = card.get('oracle_text', '').lower()
        type_line = card.get('type_line', '')

        # Parse all ability types
        triggers = self._parse_triggers(text, type_line)
        static = self._parse_static_abilities(text, type_line)
        activated = self._parse_activated_abilities(text)
        keywords = self._parse_keywords(card)
        types = self._parse_creature_types(type_line)

        # Set cached flags
        flags = self._calculate_flags(triggers, static, activated, keywords)

        return CardAbilities(
            name=card.get('name', ''),
            triggers=triggers,
            static_abilities=static,
            activated_abilities=activated,
            keywords=keywords,
            creature_types=types,
            **flags
        )

    def _parse_triggers(self, text: str, type_line: str) -> List[TriggerAbility]:
        """Parse all triggered abilities"""
        triggers = []

        # ETB triggers
        triggers.extend(self._parse_etb_triggers(text))

        # Rally (Ally ETB) triggers
        triggers.extend(self._parse_rally_triggers(text, type_line))

        # Attack triggers
        triggers.extend(self._parse_attack_triggers(text))

        # Cast spell triggers (prowess, magecraft, spellslinger)
        triggers.extend(self._parse_cast_triggers(text))

        # Death triggers
        triggers.extend(self._parse_death_triggers(text))

        # Other triggers (landfall, constellation, etc.)
        triggers.extend(self._parse_other_triggers(text))

        return triggers

    def _parse_rally_triggers(self, text: str, type_line: str) -> List[TriggerAbility]:
        """
        Parse Rally mechanic (Ally ETB triggers).
        Replaces logic from both etb_extractors.py and oracle_text_parser.py
        """
        triggers = []

        rally_pattern = r'(?:rally.*?whenever|whenever.*(?:this creature or another ally|.*ally.*).*enters)'
        if re.search(rally_pattern, text):
            # Determine effect type
            effect_type = 'unknown'
            effect_value = 0.0

            if 'gain haste' in text:
                effect_type = 'grant_keyword'
                effect = 'haste'
            elif 'gain vigilance' in text:
                effect_type = 'grant_keyword'
                effect = 'vigilance'
            elif 'gain lifelink' in text:
                effect_type = 'grant_keyword'
                effect = 'lifelink'
            elif 'gain double strike' in text:
                effect_type = 'grant_keyword'
                effect = 'double strike'
            elif re.search(r'put.*\+1/\+1 counter', text):
                effect_type = 'counters'
                effect = '+1/+1 counters'
                effect_value = 1.0
            else:
                effect = text[:100]  # First 100 chars as fallback

            triggers.append(TriggerAbility(
                event='rally',
                condition='ally_enters',
                effect=effect,
                effect_type=effect_type,
                targets=['creatures_you_control'],
                value=effect_value,
                metadata={'is_ally': 'ally' in type_line.lower()}
            ))

        return triggers

    # ... more parsing methods ...
```

**Testing:**
```python
# Test that unified parser matches both old systems
def test_rally_parsing_consistency():
    card = get_card_by_name("Chasm Guide")

    # Old way (etb_extractors)
    old_rally = extract_rally_triggers(card)

    # New way (unified parser)
    parser = UnifiedCardParser()
    abilities = parser.parse_card(card)
    new_rally = [t for t in abilities.triggers if t.event == 'rally']

    assert old_rally['has_rally'] == (len(new_rally) > 0)
    assert old_rally['effect_type'] == new_rally[0].effect_type
```

### 1.2 Migrate Existing Extractors

**Create adapter layer for backward compatibility:**

```python
# src/utils/extractor_adapters.py
"""
Adapter layer - maps old extractor API to new unified parser.
Allows gradual migration without breaking existing code.
"""

from src.core.card_parser import UnifiedCardParser, CardAbilities

_parser = UnifiedCardParser()
_cache = {}  # Cache parsed results

def _get_parsed_card(card: Dict) -> CardAbilities:
    """Get cached or parse card"""
    name = card.get('name')
    if name not in _cache:
        _cache[name] = _parser.parse_card(card)
    return _cache[name]

# Adapt old extractor functions
def extract_rally_triggers(card: Dict) -> Dict:
    """Adapter for old rally extractor API"""
    abilities = _get_parsed_card(card)
    rally_triggers = [t for t in abilities.triggers if t.event == 'rally']

    if rally_triggers:
        trigger = rally_triggers[0]
        return {
            'has_rally': True,
            'effect_type': trigger.effect_type,
            'effect_description': trigger.effect,
            'is_ally': trigger.metadata.get('is_ally', False)
        }
    return {
        'has_rally': False,
        'effect_type': None,
        'effect_description': '',
        'is_ally': 'Ally' in card.get('type_line', '')
    }

# ... adapt all other extractors ...
```

### 1.3 Replace Duplicate Parsers

**Files to modify:**
- ✏️ `src/utils/etb_extractors.py` - Use unified parser
- ✏️ `Simulation/oracle_text_parser.py` - Use unified parser
- ✏️ All other `src/utils/*_extractors.py` - Use unified parser

---

## **PART 2: Unified Trigger Registry** (Execution Layer)

### 2.1 Create Trigger Registry

**File:** `src/core/trigger_registry.py`

```python
"""
Trigger Registry - Central trigger management for both systems.
When synergy detection finds a trigger, simulation can execute it.
"""

from typing import Dict, List, Callable, Any
from dataclasses import dataclass

@dataclass
class RegisteredTrigger:
    """A trigger that can be executed in simulation"""
    card_name: str
    event: str  # 'etb', 'rally', 'attack', etc.
    effect_function: Callable  # Function to execute in simulation
    priority: int  # Execution order
    conditions: List[str]  # When it triggers

class TriggerRegistry:
    """
    Global registry of all triggers in the game.
    Both synergy detection and simulation use this.
    """

    def __init__(self):
        self.triggers: Dict[str, List[RegisteredTrigger]] = {}

    def register_trigger(self, card_name: str, trigger: TriggerAbility,
                        effect_function: Callable):
        """
        Register a trigger from parsed card abilities.

        Args:
            card_name: Name of card
            trigger: TriggerAbility from unified parser
            effect_function: Function to execute (for simulation)
        """
        event = trigger.event
        if event not in self.triggers:
            self.triggers[event] = []

        self.triggers[event].append(RegisteredTrigger(
            card_name=card_name,
            event=event,
            effect_function=effect_function,
            priority=self._calculate_priority(trigger),
            conditions=self._parse_conditions(trigger)
        ))

    def get_triggers(self, event: str, game_state: Any = None) -> List[RegisteredTrigger]:
        """
        Get all triggers for an event, filtered by conditions.

        Args:
            event: Trigger event type
            game_state: Current game state (for condition checking)

        Returns:
            List of triggers that should fire
        """
        triggers = self.triggers.get(event, [])

        if game_state is None:
            return triggers

        # Filter by conditions
        valid_triggers = []
        for trigger in triggers:
            if self._check_conditions(trigger, game_state):
                valid_triggers.append(trigger)

        # Sort by priority
        return sorted(valid_triggers, key=lambda t: t.priority)

    def execute_triggers(self, event: str, game_state: Any):
        """
        Execute all triggers for an event in priority order.
        Used by simulation.
        """
        triggers = self.get_triggers(event, game_state)

        for trigger in triggers:
            try:
                trigger.effect_function(game_state)
            except Exception as e:
                print(f"Error executing trigger {trigger.card_name}: {e}")

    # ... more methods ...

# Global registry instance
TRIGGER_REGISTRY = TriggerRegistry()
```

### 2.2 Trigger Effect Functions

**File:** `src/core/trigger_effects.py`

```python
"""
Standard trigger effect functions.
Unified between synergy detection and simulation.
"""

def create_rally_haste_effect(card_name: str):
    """Create a rally effect that grants haste"""
    def effect(board_state):
        # Grant haste to all creatures
        board_state.grant_keyword_until_eot('haste')
        board_state.log_action(f"{card_name} rally: creatures gain haste")
    return effect

def create_rally_vigilance_effect(card_name: str):
    """Create a rally effect that grants vigilance"""
    def effect(board_state):
        board_state.grant_keyword_until_eot('vigilance')
        board_state.log_action(f"{card_name} rally: creatures gain vigilance")
    return effect

def create_prowess_effect(card_name: str):
    """Create a prowess trigger effect"""
    def effect(board_state):
        # Find creature with prowess
        creature = board_state.find_permanent_by_name(card_name)
        if creature:
            board_state.buff_creature_until_eot(creature, +1, +1)
            board_state.log_action(f"{card_name} prowess: +1/+1 until EOT")
    return effect

def create_token_creation_effect(token_count: int, token_type: str):
    """Create a token creation effect"""
    def effect(board_state):
        board_state.create_tokens(token_count, token_type)
        board_state.log_action(f"Created {token_count} {token_type} token(s)")
    return effect

# ... more effect creators ...
```

---

## **PART 3: Enhanced BoardState** (Simulation Execution)

### 3.1 Add Missing Methods to BoardState

**File:** `Simulation/boardstate.py`

Add these methods:

```python
class BoardState:
    def __init__(self):
        # ... existing init ...

        # NEW: Temporary keyword grants
        self.temporary_keywords = {}  # {creature_id: [keywords]}

        # NEW: Trigger registry integration
        from src.core.trigger_registry import TRIGGER_REGISTRY
        self.trigger_registry = TRIGGER_REGISTRY

    def grant_keyword_until_eot(self, keyword: str, target='all'):
        """
        Grant a keyword to creatures until end of turn.
        Used by rally, anthems, combat tricks.

        Args:
            keyword: Keyword to grant ('haste', 'vigilance', etc.)
            target: 'all', 'allies', or specific creature
        """
        for creature in self.battlefield:
            if target == 'all' or self._matches_target(creature, target):
                creature_id = id(creature)
                if creature_id not in self.temporary_keywords:
                    self.temporary_keywords[creature_id] = []
                self.temporary_keywords[creature_id].append(keyword)

                # Update creature's effective keywords
                if not hasattr(creature, 'active_keywords'):
                    creature.active_keywords = set()
                creature.active_keywords.add(keyword)

    def cleanup_temporary_keywords(self):
        """
        Remove temporary keyword grants at end of turn.
        Called in end_of_turn_phase.
        """
        for creature in self.battlefield:
            creature_id = id(creature)
            if creature_id in self.temporary_keywords:
                # Remove temporary keywords
                temp_keywords = self.temporary_keywords[creature_id]
                if hasattr(creature, 'active_keywords'):
                    for kw in temp_keywords:
                        creature.active_keywords.discard(kw)

        self.temporary_keywords.clear()

    def put_counter_on_creatures(self, num_counters: int, target='all'):
        """
        Put +1/+1 counters on creatures.
        Used by rally, cathars' crusade, etc.

        Args:
            num_counters: Number of counters
            target: 'all', 'allies', 'attacking', etc.
        """
        for creature in self.battlefield:
            if target == 'all' or self._matches_target(creature, target):
                creature.power += num_counters
                creature.toughness += num_counters

                if not hasattr(creature, 'counters'):
                    creature.counters = 0
                creature.counters += num_counters

    def buff_creature_until_eot(self, creature, power_bonus: int, toughness_bonus: int):
        """
        Temporarily buff a creature until end of turn.
        Used by prowess, combat tricks, etc.
        """
        if not hasattr(creature, 'temporary_buffs'):
            creature.temporary_buffs = {'power': 0, 'toughness': 0}

        creature.temporary_buffs['power'] += power_bonus
        creature.temporary_buffs['toughness'] += toughness_bonus

        # Update effective stats
        creature.power += power_bonus
        creature.toughness += toughness_bonus

    def cleanup_temporary_buffs(self):
        """Remove temporary buffs at end of turn"""
        for creature in self.battlefield:
            if hasattr(creature, 'temporary_buffs'):
                creature.power -= creature.temporary_buffs['power']
                creature.toughness -= creature.temporary_buffs['toughness']
                creature.temporary_buffs = {'power': 0, 'toughness': 0}

    def find_permanent_by_name(self, name: str):
        """Find a permanent on battlefield by name"""
        for permanent in self.battlefield:
            if permanent.name == name:
                return permanent
        return None

    def _matches_target(self, creature, target: str) -> bool:
        """Check if creature matches target selector"""
        if target == 'all':
            return True
        elif target == 'allies':
            return 'Ally' in creature.type_line
        elif target == 'attacking':
            return hasattr(creature, 'is_attacking') and creature.is_attacking
        # Add more target types as needed
        return False

    def trigger_event(self, event: str, context: Dict = None):
        """
        Trigger all registered triggers for an event.
        Integrates with trigger registry.

        Args:
            event: Event name ('etb', 'rally', 'attack', etc.)
            context: Additional context (card that triggered, etc.)
        """
        self.trigger_registry.execute_triggers(event, self)
```

### 3.2 Update Turn Phases

**File:** `Simulation/simulate_game.py`

```python
def end_of_turn_phase(board_state):
    """End of turn cleanup"""

    # ... existing end of turn logic ...

    # NEW: Cleanup temporary effects
    board_state.cleanup_temporary_keywords()
    board_state.cleanup_temporary_buffs()

    # Trigger end of turn effects
    board_state.trigger_event('end_of_turn')

def play_creature(board_state, creature_card):
    """Play a creature"""

    # ... existing play logic ...

    # NEW: Trigger ETB events
    board_state.trigger_event('etb', {'card': creature_card})

    # NEW: If creature is an Ally, trigger rally
    if 'Ally' in creature_card.type_line:
        board_state.trigger_event('rally', {'card': creature_card})

def cast_spell(board_state, spell):
    """Cast a spell"""

    # ... existing cast logic ...

    # NEW: Trigger cast_spell events (prowess, magecraft, spellslinger)
    is_noncreature = 'Creature' not in spell.type_line
    if is_noncreature:
        board_state.trigger_event('cast_noncreature_spell', {'spell': spell})
```

---

## **PART 4: Synergy → Simulation Pipeline** (Integration)

### 4.1 Create Bridge System

**File:** `src/core/synergy_simulation_bridge.py`

```python
"""
Bridge between synergy detection and simulation.
When synergies are detected, they inform simulation behavior.
"""

from src.core.card_parser import UnifiedCardParser
from src.core.trigger_registry import TRIGGER_REGISTRY
from src.core.trigger_effects import *

class SynergySimulationBridge:
    """
    Connects synergy detection to simulation execution.
    When analyzing a deck:
    1. Parse all cards with unified parser
    2. Register triggers for simulation
    3. Calculate synergy-based card priorities
    """

    def __init__(self):
        self.parser = UnifiedCardParser()
        self.registry = TRIGGER_REGISTRY

    def prepare_deck_for_simulation(self, deck_cards: List[Dict]) -> Dict:
        """
        Prepare deck for simulation by:
        1. Parsing all abilities
        2. Registering triggers
        3. Calculating priorities based on synergies

        Args:
            deck_cards: List of card dicts

        Returns:
            {
                'parsed_cards': List[CardAbilities],
                'trigger_count': int,
                'synergy_weights': Dict[str, float]
            }
        """
        parsed_cards = []
        self.registry.clear()  # Clear previous deck

        for card in deck_cards:
            # Parse card
            abilities = self.parser.parse_card(card)
            parsed_cards.append(abilities)

            # Register triggers for simulation
            self._register_card_triggers(card, abilities)

        # Calculate synergy weights (used by simulation AI)
        synergy_weights = self._calculate_synergy_weights(parsed_cards)

        return {
            'parsed_cards': parsed_cards,
            'trigger_count': len(self.registry.get_all_triggers()),
            'synergy_weights': synergy_weights
        }

    def _register_card_triggers(self, card: Dict, abilities: CardAbilities):
        """Register all triggers from a card"""
        for trigger in abilities.triggers:
            effect_func = self._create_effect_function(card, trigger)
            if effect_func:
                self.registry.register_trigger(
                    card_name=card['name'],
                    trigger=trigger,
                    effect_function=effect_func
                )

    def _create_effect_function(self, card: Dict, trigger: TriggerAbility) -> Callable:
        """Create simulation effect function from trigger"""
        card_name = card['name']

        if trigger.event == 'rally':
            if trigger.effect == 'haste':
                return create_rally_haste_effect(card_name)
            elif trigger.effect == 'vigilance':
                return create_rally_vigilance_effect(card_name)
            # ... more rally effects ...

        elif trigger.event == 'cast_noncreature_spell':
            if 'prowess' in card.get('keywords', []):
                return create_prowess_effect(card_name)

        # ... more trigger types ...

        return None

    def _calculate_synergy_weights(self, parsed_cards: List[CardAbilities]) -> Dict[str, float]:
        """
        Calculate card priorities based on synergies.
        Cards involved in more synergies are higher priority.
        """
        weights = {}

        # Analyze synergies between all pairs
        for i, card1 in enumerate(parsed_cards):
            for card2 in parsed_cards[i+1:]:
                synergy_value = self._calculate_synergy_value(card1, card2)
                if synergy_value > 0:
                    weights[card1.name] = weights.get(card1.name, 0) + synergy_value
                    weights[card2.name] = weights.get(card2.name, 0) + synergy_value

        return weights

    def _calculate_synergy_value(self, card1: CardAbilities,
                                 card2: CardAbilities) -> float:
        """Calculate synergy value between two parsed cards"""
        value = 0.0

        # Rally + Token Creation
        if card1.has_rally and card2.creates_tokens:
            value += 6.0 if 'Ally' in card2.creature_types else 4.0

        # Prowess + Cheap Spell
        if card1.has_prowess and card2.is_spell and card2.cmc <= 2:
            value += 5.0

        # ... more synergy checks ...

        return value

# Global bridge instance
BRIDGE = SynergySimulationBridge()
```

### 4.2 Update Simulation Runner

**File:** `Simulation/run_simulation.py`

```python
from src.core.synergy_simulation_bridge import BRIDGE

def run_simulation_with_synergies(deck_cards: List[Dict], num_games: int = 100):
    """
    Run simulation with synergy-aware priorities.

    Args:
        deck_cards: List of card dicts
        num_games: Number of games to simulate

    Returns:
        {
            'simulation_results': {...},
            'synergy_info': {
                'trigger_count': int,
                'synergy_weights': Dict
            }
        }
    """
    # Prepare deck using bridge
    prep_info = BRIDGE.prepare_deck_for_simulation(deck_cards)

    print(f"Deck prepared: {prep_info['trigger_count']} triggers registered")
    print(f"Synergy weights calculated for {len(prep_info['synergy_weights'])} cards")

    # Run simulation (now uses registered triggers)
    results = run_simulation(deck_cards, num_games=num_games)

    return {
        'simulation_results': results,
        'synergy_info': {
            'trigger_count': prep_info['trigger_count'],
            'synergy_weights': prep_info['synergy_weights']
        }
    }
```

---

## **PART 5: Testing Framework** (Validation)

### 5.1 End-to-End Test Template

**File:** `tests/test_unified_system.py`

```python
"""
End-to-end tests for unified synergy + simulation system.
Every new synergy MUST have a test here.
"""

import pytest
from src.core.card_parser import UnifiedCardParser
from src.core.synergy_simulation_bridge import BRIDGE
from src.api.local_cards import get_card_by_name, load_local_database

@pytest.fixture(scope="module")
def parser():
    load_local_database()
    return UnifiedCardParser()

def test_rally_full_pipeline(parser):
    """
    Test rally mechanic end-to-end:
    1. Parsing detects rally
    2. Synergy detection finds rally + token synergy
    3. Simulation executes rally triggers
    """
    # Get test cards
    chasm_guide = get_card_by_name("Chasm Guide")
    gideon = get_card_by_name("Gideon, Ally of Zendikar")

    # STEP 1: Parse abilities
    chasm_abilities = parser.parse_card(chasm_guide)
    gideon_abilities = parser.parse_card(gideon)

    # Verify rally detected
    rally_triggers = [t for t in chasm_abilities.triggers if t.event == 'rally']
    assert len(rally_triggers) > 0
    assert rally_triggers[0].effect == 'haste'

    # Verify token creation detected
    assert gideon_abilities.creates_tokens

    # STEP 2: Synergy detection
    from src.synergy_engine.ally_prowess_synergies import detect_rally_token_synergy
    synergy = detect_rally_token_synergy(chasm_guide, gideon)

    assert synergy is not None
    assert synergy['value'] == 6.0  # High value because ally tokens

    # STEP 3: Simulation execution
    deck = [chasm_guide, gideon]
    prep_info = BRIDGE.prepare_deck_for_simulation(deck)

    # Verify trigger registered
    assert prep_info['trigger_count'] >= 1

    # Verify synergy weight calculated
    assert 'Chasm Guide' in prep_info['synergy_weights']
    assert prep_info['synergy_weights']['Chasm Guide'] > 0

    # TODO: Run actual simulation and verify haste granted

def test_prowess_full_pipeline(parser):
    """Test prowess + cheap spell end-to-end"""
    # Similar structure to test_rally_full_pipeline
    # ... test parsing, synergy, simulation ...

def test_new_synergy_template(parser):
    """
    Template for testing new synergies.
    Copy this when adding a new synergy type.
    """
    # STEP 1: Get test cards
    card1 = get_card_by_name("Card Name 1")
    card2 = get_card_by_name("Card Name 2")

    # STEP 2: Parse and verify abilities detected
    abilities1 = parser.parse_card(card1)
    # assert abilities1.has_xxx == True

    # STEP 3: Test synergy detection
    from src.synergy_engine.xxx_synergies import detect_xxx_synergy
    synergy = detect_xxx_synergy(card1, card2)
    assert synergy is not None

    # STEP 4: Test simulation integration
    deck = [card1, card2]
    prep_info = BRIDGE.prepare_deck_for_simulation(deck)
    assert prep_info['trigger_count'] > 0
```

### 5.2 Regression Test Suite

**File:** `tests/test_no_regressions.py`

```python
"""
Regression tests - ensure unified system matches old behavior.
"""

def test_rally_backwards_compatible():
    """Rally extraction matches old extractor"""
    from src.utils.etb_extractors import extract_rally_triggers
    from src.core.card_parser import UnifiedCardParser

    parser = UnifiedCardParser()
    card = get_card_by_name("Chasm Guide")

    # Old way
    old_result = extract_rally_triggers(card)

    # New way
    abilities = parser.parse_card(card)
    new_result = any(t.event == 'rally' for t in abilities.triggers)

    assert old_result['has_rally'] == new_result

# Test ALL existing extractors for backward compatibility
```

---

## **PART 6: Documentation & AI Guide** (Knowledge Transfer)

### 6.1 Update AI Guide

**File:** `AI_GUIDE_FOR_MODELS.md` - Add new section:

```markdown
## 🔗 UNIFIED ARCHITECTURE (2025-11-14 Update)

### Critical Change: Single Source of Truth

**OLD ARCHITECTURE (Before 2025-11-14):**
```
Oracle Text Parsing:
├─ src/utils/*_extractors.py (synergy detection)
└─ Simulation/oracle_text_parser.py (simulation)
Problem: Same logic duplicated, synergies don't affect simulation
```

**NEW ARCHITECTURE (After 2025-11-14):**
```
src/core/card_parser.py (SINGLE PARSER)
    │
    ├─> Synergy Detection (finds interactions)
    └─> Simulation (executes triggers)
```

### Adding a New Mechanic (New Process)

**Example: Adding "Revolt" mechanic**

#### Step 1: Parse in Unified Parser

**File:** `src/core/card_parser.py`

```python
def _parse_other_triggers(self, text: str) -> List[TriggerAbility]:
    # ... existing triggers ...

    # NEW: Revolt (triggers if permanent left battlefield this turn)
    if 'revolt' in text:
        effect_type = self._determine_effect_type(text)
        triggers.append(TriggerAbility(
            event='revolt',
            condition='permanent_left_battlefield_this_turn',
            effect=text[:100],
            effect_type=effect_type,
            targets=self._extract_targets(text),
            value=self._extract_value(text),
            metadata={}
        ))
```

#### Step 2: Create Effect Function

**File:** `src/core/trigger_effects.py`

```python
def create_revolt_effect(card_name: str, effect_type: str, value: float):
    """Create a revolt trigger effect"""
    def effect(board_state):
        if board_state.permanent_left_this_turn:
            if effect_type == 'tokens':
                board_state.create_tokens(int(value), '1/1')
            elif effect_type == 'draw':
                board_state.draw_card(int(value))
            # ... handle other effect types ...
            board_state.log_action(f"{card_name} revolt triggered")
    return effect
```

#### Step 3: Add Synergy Rule

**File:** `src/synergy_engine/revolt_synergies.py` (NEW FILE)

```python
def detect_revolt_sacrifice_synergy(card1, card2):
    """
    Revolt + Sacrifice Outlet synergy.
    Sacrifice outlets enable revolt triggers.
    """
    from src.core.card_parser import UnifiedCardParser
    parser = UnifiedCardParser()

    abilities1 = parser.parse_card(card1)
    abilities2 = parser.parse_card(card2)

    # Card1 has revolt, Card2 is sacrifice outlet
    has_revolt1 = any(t.event == 'revolt' for t in abilities1.triggers)
    is_sac_outlet2 = abilities2.is_sacrifice_outlet

    if has_revolt1 and is_sac_outlet2:
        return {
            'name': 'Revolt + Sacrifice Outlet',
            'description': f"{card2['name']} enables {card1['name']}'s revolt",
            'value': 5.0,
            'category': 'triggers',
            'subcategory': 'revolt_synergy'
        }

    # Check reverse
    # ...
```

#### Step 4: Register in Bridge

**File:** `src/core/synergy_simulation_bridge.py`

```python
def _create_effect_function(self, card: Dict, trigger: TriggerAbility):
    # ... existing triggers ...

    elif trigger.event == 'revolt':
        return create_revolt_effect(
            card['name'],
            trigger.effect_type,
            trigger.value
        )
```

#### Step 5: Update BoardState (if needed)

**File:** `Simulation/boardstate.py`

```python
def __init__(self):
    # ... existing init ...
    self.permanent_left_this_turn = False  # Track for revolt

def remove_permanent(self, permanent):
    # ... existing removal ...
    self.permanent_left_this_turn = True  # Flag for revolt

def end_of_turn_cleanup(self):
    # ... existing cleanup ...
    self.permanent_left_this_turn = False  # Reset
```

#### Step 6: Write Tests

**File:** `tests/test_unified_system.py`

```python
def test_revolt_full_pipeline(parser):
    """Test revolt mechanic end-to-end"""
    card1 = get_card_by_name("Fatal Push")  # Has revolt
    card2 = get_card_by_name("Viscera Seer")  # Sacrifice outlet

    # Parse
    abilities1 = parser.parse_card(card1)
    revolt_triggers = [t for t in abilities1.triggers if t.event == 'revolt']
    assert len(revolt_triggers) > 0

    # Synergy
    from src.synergy_engine.revolt_synergies import detect_revolt_sacrifice_synergy
    synergy = detect_revolt_sacrifice_synergy(card1, card2)
    assert synergy is not None
    assert synergy['value'] == 5.0

    # Simulation
    deck = [card1, card2]
    prep_info = BRIDGE.prepare_deck_for_simulation(deck)
    assert prep_info['trigger_count'] > 0
```

#### Step 7: Run Full Test Suite

```bash
# Test parsing
pytest tests/test_unified_system.py::test_revolt_full_pipeline -v

# Test no regressions
pytest tests/test_no_regressions.py -v

# Test synergy detection
python count_synergies.py  # Should show revolt synergies

# Test simulation
python Simulation/run_simulation.py deck_with_revolt.txt
```

### Key Principle: One Change, Three Validations

When adding a new mechanic:
1. ✅ Parsing test passes
2. ✅ Synergy detection finds it
3. ✅ Simulation executes it

If any of these fails, the implementation is incomplete.
```

### 6.2 Create Implementation Checklist

**File:** `ADDING_NEW_MECHANICS_CHECKLIST.md`

```markdown
# ✅ Checklist for Adding New Mechanics

## Before You Start
- [ ] Read `UNIFIED_ARCHITECTURE_PLAN.md`
- [ ] Understand the unified flow: Parse → Synergy → Simulation
- [ ] Have test cards ready (cards that use the mechanic)

## Implementation Steps

### 1. Parsing (src/core/card_parser.py)
- [ ] Add pattern to detect mechanic in oracle text
- [ ] Extract effect type, targets, and value
- [ ] Create `TriggerAbility` or `StaticAbility` or `ActivatedAbility`
- [ ] Add cached flag to `CardAbilities` if needed
- [ ] Test: `abilities = parser.parse_card(card)` returns expected data

### 2. Effect Function (src/core/trigger_effects.py)
- [ ] Create `create_xxx_effect()` function
- [ ] Function takes board_state and modifies it appropriately
- [ ] Add logging for debugging
- [ ] Test: Effect function runs without errors

### 3. Synergy Rules (src/synergy_engine/xxx_synergies.py)
- [ ] Create new synergy detection file (if new category)
- [ ] Implement `detect_xxx_synergy(card1, card2)` function
- [ ] Use unified parser to check abilities
- [ ] Return synergy dict with appropriate value
- [ ] Add to `SYNERGY_RULES` list in relevant file
- [ ] Test: Synergy detected between appropriate cards

### 4. Bridge Integration (src/core/synergy_simulation_bridge.py)
- [ ] Add case in `_create_effect_function()`
- [ ] Map parsed trigger to effect function
- [ ] Test: Effect registered in trigger registry

### 5. BoardState (Simulation/boardstate.py) - If Needed
- [ ] Add state tracking variables
- [ ] Add helper methods if needed
- [ ] Add cleanup logic in end of turn
- [ ] Test: State updates correctly

### 6. Simulation Phases (Simulation/simulate_game.py) - If Needed
- [ ] Add trigger_event() call in appropriate phase
- [ ] Ensure context passed correctly
- [ ] Test: Trigger fires at correct time

### 7. Testing (tests/test_unified_system.py)
- [ ] Copy `test_new_synergy_template()`
- [ ] Fill in with actual cards
- [ ] Test parsing → synergy → simulation
- [ ] Run: `pytest tests/test_unified_system.py::test_xxx -v`

### 8. Regression Testing
- [ ] Run full test suite: `pytest`
- [ ] Check no existing tests broke
- [ ] Run count_synergies.py on sample deck
- [ ] Run simulation on sample deck

### 9. Documentation
- [ ] Add example to AI_GUIDE_FOR_MODELS.md
- [ ] Update SYNERGY_SYSTEM.md if new category
- [ ] Update SIMULATION_ACCURACY_COMPLETE.md

### 10. Validation
- [ ] Parsing test passes ✅
- [ ] Synergy detection finds it ✅
- [ ] Simulation executes it ✅
- [ ] All three working = Implementation complete!

## Common Pitfalls

❌ Only adding to synergy detection but not simulation
❌ Only adding to simulation but not synergy detection
❌ Forgetting to register trigger in bridge
❌ Not cleaning up temporary effects at end of turn
❌ Parsing returns inconsistent data types

✅ Use unified parser for all extraction
✅ Test all three systems (parse, synergy, simulation)
✅ Follow existing patterns
✅ Add comprehensive tests
```

---

## **PART 7: Migration Strategy** (Rollout Plan)

### 7.1 Phase 1: Foundation (Week 1)
- [ ] Create `src/core/card_parser.py` with unified parser
- [ ] Create `src/core/trigger_registry.py`
- [ ] Create `src/core/trigger_effects.py`
- [ ] Write tests for core components

### 7.2 Phase 2: Adapter Layer (Week 1-2)
- [ ] Create `src/utils/extractor_adapters.py`
- [ ] Map old extractor API to new parser
- [ ] Ensure backward compatibility
- [ ] Run regression tests

### 7.3 Phase 3: BoardState Enhancement (Week 2)
- [ ] Add missing methods to BoardState
- [ ] Update turn phases to use trigger registry
- [ ] Test rally, prowess triggers work

### 7.4 Phase 4: Bridge System (Week 2-3)
- [ ] Create `src/core/synergy_simulation_bridge.py`
- [ ] Integrate with simulation runner
- [ ] Test synergy weights affect simulation

### 7.5 Phase 5: Migrate Extractors (Week 3-4)
- [ ] Migrate one extractor at a time
- [ ] Test each migration
- [ ] Update dependent code
- [ ] Remove duplicate parsing

### 7.6 Phase 6: Testing & Documentation (Week 4)
- [ ] Create comprehensive test suite
- [ ] Update all documentation
- [ ] Write migration guide
- [ ] Validate with real decks

---

## **Expected Outcomes**

### Before Unification
```
Add Rally Synergy:
1. Add to src/utils/etb_extractors.py (1 hour)
2. Add to src/synergy_engine/ally_prowess_synergies.py (1 hour)
3. Add to Simulation/oracle_text_parser.py (1 hour)
4. Add to Simulation/boardstate.py (2 hours)
Total: 5 hours, simulation may not work correctly
```

### After Unification
```
Add Rally Synergy:
1. Add to src/core/card_parser.py (30 min)
2. Add synergy rule (30 min)
3. Tests auto-verify simulation works (0 min)
Total: 1 hour, guaranteed to work in both systems
```

### Benefits
- ✅ **80% less code duplication**
- ✅ **Synergies automatically work in simulation**
- ✅ **Single source of truth for all parsing**
- ✅ **4x faster to add new mechanics**
- ✅ **Comprehensive testing ensures correctness**
- ✅ **Clear AI documentation for future additions**

---

## File Summary

**New Files to Create:**
1. `src/core/card_parser.py` - Unified parser (500 lines)
2. `src/core/trigger_registry.py` - Trigger management (300 lines)
3. `src/core/trigger_effects.py` - Standard effects (400 lines)
4. `src/core/synergy_simulation_bridge.py` - Integration (300 lines)
5. `src/utils/extractor_adapters.py` - Backward compatibility (200 lines)
6. `tests/test_unified_system.py` - End-to-end tests (500 lines)
7. `tests/test_no_regressions.py` - Regression tests (300 lines)
8. `ADDING_NEW_MECHANICS_CHECKLIST.md` - Implementation guide
9. `UNIFIED_ARCHITECTURE_PLAN.md` - This document

**Files to Modify:**
1. `Simulation/boardstate.py` - Add missing methods
2. `Simulation/simulate_game.py` - Use trigger registry
3. `Simulation/run_simulation.py` - Use bridge
4. `src/synergy_engine/analyzer.py` - Use unified parser
5. `AI_GUIDE_FOR_MODELS.md` - Update with new architecture
6. All `src/utils/*_extractors.py` - Migrate to unified parser

**Total Estimated Lines:** ~3,500 new lines, ~1,000 lines modified

**Estimated Time:** 3-4 weeks for complete migration

---

This unified architecture will solve the core problem: **synergies and simulation will finally work together**. Rally triggers, prowess, and all future mechanics will automatically work in both systems with a single implementation.
