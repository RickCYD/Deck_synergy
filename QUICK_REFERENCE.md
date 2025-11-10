# Quick Reference Guide - Common Development Tasks

## 1. Adding a New Card Mechanic

### Step 1: Add Card Property
```python
# In simulate_game.py, Card.__init__():
self.my_mechanic = my_mechanic
```

### Step 2: Parse from Oracle Text
```python
# In oracle_text_parser.py:
def parse_my_mechanic(text: str) -> bool:
    return "specific phrase" in text.lower()

# In deck_loader.py, build_card_from_row():
my_mechanic = parse_my_mechanic(row["OracleText"])
```

### Step 3: Trigger in Board State
```python
# In boardstate.py:
def trigger_my_mechanic(self, verbose: bool = False):
    for permanent in self.creatures + self.enchantments:
        if getattr(permanent, 'my_mechanic', False):
            # Do something
            pass
```

### Step 4: Call in Appropriate Phase
```python
# In simulate_game.py, main loop around line 650:
if board.creatures:
    board.trigger_my_mechanic(verbose=verbose)
```

### Step 5: Add Test
```python
# In Simulation/tests/test_my_mechanic.py:
def test_my_mechanic():
    card = Card(..., my_mechanic=True)
    board = BoardState([...], commander)
    board.creatures.append(card)
    # Test the behavior
```

---

## 2. Adding a New Triggered Ability Event

### Existing Events
- `"etb"` - Enters the battlefield
- `"attack"` - Creature attacks
- `"landfall"` - Land enters
- `"damage"` - Creature takes damage
- `"equip"` - Equipment attached

### To Add New Event

1. **Create trigger detection** in `oracle_text_parser.py`:
```python
def parse_my_trigger_from_oracle(text: str) -> list[TriggeredAbility]:
    if not text:
        return []
    
    triggers = []
    if "specific pattern" in text.lower():
        def effect(board_state):
            # Your effect code
            pass
        
        triggers.append(TriggeredAbility(
            event="my_event",
            effect=effect,
            description="What this does"
        ))
    
    return triggers
```

2. **Add to card building**:
```python
# In deck_loader.py:
my_triggers = parse_my_trigger_from_oracle(row["OracleText"])
# Merge with other triggers
```

3. **Add execution point**:
```python
# In boardstate.py:
def _execute_triggers(self, event: str, card, verbose=False):
    for trig in getattr(card, "triggered_abilities", []):
        if trig.event != event:
            continue
        # ... existing code ...
        trig.effect(self)
```

4. **Call at right time** in simulate_game.py main loop

---

## 3. Adding a New Synergy Category

### In `src/synergy_engine/categories.py`:
```python
SYNERGY_CATEGORIES = {
    'my_category': {
        'name': 'My Category',
        'description': 'Synergies related to...',
        'icon': '🔥',
        'base_weight': 3.0  # 1-10 scale
    }
}
```

### Create extractor in `src/utils/`:
```python
# my_synergy_extractors.py
def extract_my_synergy(card1, card2) -> dict | None:
    """
    Returns synergy dict or None if not applicable.
    
    Synergy dict structure:
    {
        'name': 'Synergy Name',
        'description': 'Human readable',
        'value': 3.5,
        'category': 'my_category',
        'subcategory': 'optional_subcat'
    }
    """
    # Check card1 and card2 for interactions
    if some_condition(card1) and some_condition(card2):
        return {
            'name': 'My Synergy',
            'description': f"{card1.name} + {card2.name}",
            'value': 3.5,
            'category': 'my_category'
        }
    return None
```

### Add to analyzer in `src/synergy_engine/analyzer.py`:
```python
from utils.my_synergy_extractors import extract_my_synergy

# In analyze_deck_synergies():
synergy_extractors = [
    # ... existing extractors ...
    extract_my_synergy
]
```

---

## 4. Working with Mana System

### Check if Mana Available
```python
# Always use Mana_utils.can_pay() before casting
from boardstate import Mana_utils

if Mana_utils.can_pay(card.mana_cost, board.mana_pool):
    board.play_card(card)
else:
    print("Not enough mana!")
```

### Parse Mana Cost
```python
colours, generic = Mana_utils.parse_req("2WUB")
# colours = ['W', 'U', 'B']
# generic = 2

# Or use the static method
cmc = BoardState.parse_mana_cost("3RRG")
# cmc = 5
```

### Add Mana to Pool
```python
# When a land enters
mana_tuple = tuple(land.produces_colors or ['C'])
board.mana_pool.append(mana_tuple)

# For multi-color
board.mana_pool.append(('R', 'G'))  # Can pay as R or G
board.mana_pool.append(('Any',))     # Can pay as any color
```

### Pay Mana
```python
Mana_utils.pay("2RG", board.mana_pool)
# Removes 2 generic + 1 red + 1 green from pool
```

---

## 5. Working with Tokens

### Create Simple Token
```python
board.create_token(
    token_name="Goblin",
    power=1,
    toughness=1,
    has_haste=True,
    verbose=True
)
```

### Create Token with Keywords
```python
board.create_token(
    token_name="Knight",
    power=2,
    toughness=2,
    keywords=['vigilance', 'lifelink'],
    verbose=True
)
```

### Token Doublers (Handled Automatically)
```python
# create_token() automatically detects:
# - Mondrak, Glory Dominus
# - Doubling Season
# - Parallel Lives
# - Anointed Procession
# And doubles token count

# So this creates 2 tokens if doubler present:
board.create_token("Goblin", 1, 1)
```

### Create Treasure Token
```python
board.create_treasure(verbose=True)
# Creates artifact token that taps for any color
```

---

## 6. Working with Death Triggers

### Trigger Death Effects
```python
# Called automatically when creature dies in combat/removal
# But you can manually trigger:
board.trigger_death_effects(creature, verbose=True)

# Handles:
# - Zulaport Cutthroat style drain
# - Pitiless Plunderer treasure creation
# - Any death-triggered ability
```

### Check for Death Payoffs
```python
# Before deciding to sacrifice
death_payoffs = sum(1 for perm in board.creatures + board.enchantments
                   if getattr(perm, 'death_trigger_value', 0) > 0)

if death_payoffs > 0:
    # Safe to sacrifice for value
    pass
```

### Drain Damage
```python
# Tracked separately from combat damage
print(f"Drain this turn: {board.drain_damage_this_turn}")

# After combat phase:
metrics["drain_damage"][turn] = board.drain_damage_this_turn

# This is SEPARATE from:
metrics["combat_damage"][turn]
```

---

## 7. Debugging Simulation

### Run with Verbose Output
```python
from Simulation.simulate_game import simulate_game, Card
from Simulation.boardstate import BoardState

metrics = simulate_game(
    deck_cards,
    commander_card,
    max_turns=10,
    verbose=True  # Prints every action
)
```

### Key Debugging Checks
```python
# Turn number
print(f"Current turn: {board.turn}")

# Mana pool
print(f"Mana available: {board.mana_pool}")
print(f"Mana string: {board._mana_pool_str()}")

# Creatures on board
print(f"Creatures: {[c.name for c in board.creatures]}")

# Metrics during simulation
print(f"Total power: {metrics['total_power'][turn]}")
print(f"Tokens created: {metrics['tokens_created'][turn]}")
print(f"Drain damage: {metrics['drain_damage'][turn]}")
```

### Test Specific Interaction
```python
def test_my_interaction():
    # Create specific board state
    commander = Card(...)
    board = BoardState([...], commander)
    
    # Add cards
    card1 = Card(name="Card 1", ...)
    card2 = Card(name="Card 2", ...)
    board.creatures.append(card1)
    board.creatures.append(card2)
    
    # Manually trigger interaction
    board._execute_triggers("etb", card1, verbose=True)
    
    # Assert results
    assert card2.power == expected_power
```

---

## 8. Working with Anthems

### Get Effective Power (Including Anthems)
```python
# Use this instead of creature.power:
effective_power = board.get_effective_power(creature)

# Same for toughness:
effective_toughness = board.get_effective_toughness(creature)
```

### Manual Anthem Bonus Calculation
```python
power_bonus, toughness_bonus = board.calculate_anthem_bonus(creature)
# Returns tuple of bonuses from all anthem effects
```

### Known Anthems in System
- Glorious Anthem: +1/+1 to all creatures
- Intangible Virtue: +1/+1 to tokens
- Honor of the Pure: +1/+1 to white creatures
- Spear of Heliod: +1/+1 to all creatures
- Benalish Marshal: conditional anthem

---

## 9. Testing Pattern

### Basic Test Template
```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mtg_abilities import TriggeredAbility
from simulate_game import Card
from boardstate import BoardState

def test_my_feature():
    # Setup
    commander = Card(
        name="Test Commander",
        type="Commander",
        mana_cost="",
        power=0,
        toughness=0,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
    )
    
    board = BoardState([], commander)
    
    # Execute
    # ... add cards, trigger events, etc ...
    
    # Assert
    assert something == expected_value
    print("✓ Test passed")

if __name__ == "__main__":
    test_my_feature()
```

### Run Tests
```bash
# Single test
python Simulation/tests/test_my_feature.py

# All tests in directory
pytest Simulation/tests/

# Specific test function
pytest Simulation/tests/test_my_feature.py::test_my_specific_test
```

---

## 10. Git Workflow for New Features

### Create Feature Branch
```bash
git checkout -b claude/feature-name-xxxxxxxx
```

### Make Changes & Test
```bash
# Write tests first (TDD)
# Implement feature
# Run tests
pytest Simulation/tests/
```

### Commit Changes
```bash
git add Simulation/
git commit -m "Implement Feature Name

- Detailed change 1
- Detailed change 2
- Testing notes"
```

### Create PR (if needed)
```bash
git push origin claude/feature-name-xxxxxxxx
# Create PR on GitHub
```

---

## Quick Command Reference

### Run Simulation
```bash
python Simulation/run_simulation.py
```

### Start Web UI
```bash
python app.py
# Visit http://localhost:8050
```

### Run Tests
```bash
pytest Simulation/tests/
pytest tests/  # Synergy engine tests
```

### Check Code Quality
```bash
python -m py_compile Simulation/simulate_game.py
```

---

## Common File Locations

| Task | File |
|------|------|
| Add mechanic | `Simulation/simulate_game.py` (Card class) |
| Add trigger | `Simulation/mtg_abilities.py` + `oracle_text_parser.py` |
| Board logic | `Simulation/boardstate.py` |
| Parsing | `Simulation/oracle_text_parser.py` |
| Card loading | `Simulation/deck_loader.py` |
| Synergies | `src/synergy_engine/analyzer.py` + utils |
| Web UI | `app.py` |
| Tests | `Simulation/tests/test_*.py` |

---

## Key Metrics to Track

### Simulation Metrics
```python
metrics['total_power']           # Sum of creature power (with anthems)
metrics['total_toughness']       # Sum of creature toughness
metrics['combat_damage']         # Unblocked damage to opponent
metrics['drain_damage']          # Aristocrats drain (separate!)
metrics['tokens_created']        # Tokens generated
metrics['creatures_sacrificed']  # Sacrifices made
metrics['mana_spent']            # Mana consumed
metrics['lands_played']          # Lands put into play
metrics['castable_spells']       # Spells payable with current mana
```

### Opponent Tracking
```python
opponent = {
    'name': 'Opponent_1',
    'life_total': 40,
    'creatures': [list of creatures],
    'commander_damage': 0,
    'is_alive': True,
    'threat_level': 0.0-1.0
}
```

---

## Common Patterns

### Iterate Over All Permanents
```python
battlefield = (
    board.lands_untapped
    + board.lands_tapped
    + board.creatures
    + board.artifacts
    + board.enchantments
    + board.planeswalkers
)

for permanent in battlefield:
    # Process
    pass
```

### Safe Property Access
```python
# Always use getattr with default
if getattr(card, 'my_property', False):
    # Do something
    pass

oracle = getattr(card, 'oracle_text', '').lower()
if 'specific phrase' in oracle:
    # Found it
    pass
```

### Create Creature for Board State
```python
creature = Card(
    name="Creature Name",
    type="Creature",
    mana_cost="2RG",
    power=2,
    toughness=2,
    produces_colors=[],
    mana_production=0,
    etb_tapped=False,
    etb_tapped_conditions={},
    has_haste=False,
)

board.creatures.append(creature)
board._execute_triggers("etb", creature, verbose=True)
```

