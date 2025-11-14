# Adding New Mechanics Checklist

**For AI Models and Developers**

This checklist guides you through adding a new MTG mechanic to the unified architecture. Follow these steps to ensure the mechanic works correctly in both synergy detection and game simulation.

---

## Example: Adding "Landfall" Mechanic

Let's walk through adding landfall (triggers when lands enter the battlefield) as a complete example.

---

## Step 1: Add Parsing to Unified Parser

**File:** `src/core/card_parser.py`

### 1.1 Add Flag to CardAbilities

```python
@dataclass
class CardAbilities:
    # ... existing fields ...
    has_landfall: bool = False  # ADD THIS
```

### 1.2 Add Parsing Method

```python
class UnifiedCardParser:
    def _parse_landfall_triggers(self, text: str, type_line: str) -> List[TriggerAbility]:
        """Parse landfall triggers."""
        triggers = []
        text_lower = text.lower()

        # Pattern: "Landfall — Whenever a land enters..."
        landfall_patterns = [
            r'landfall\s*—\s*whenever',
            r'whenever.*land.*enters.*battlefield',
        ]

        for pattern in landfall_patterns:
            if re.search(pattern, text_lower):
                # Determine effect type
                effect_type = 'generic'
                value = 1.0

                if 'create' in text_lower and 'token' in text_lower:
                    effect_type = 'tokens'
                    # Parse token count
                    token_match = re.search(r'create (\w+) (\d+/\d+)', text_lower)
                    if token_match:
                        value = 1.0
                elif 'draw' in text_lower:
                    effect_type = 'draw'
                elif '+1/+1 counter' in text_lower:
                    effect_type = 'counters'

                triggers.append(TriggerAbility(
                    event='landfall',
                    condition=None,
                    effect=f"landfall trigger",
                    effect_type=effect_type,
                    targets=['self'],
                    value=value,
                    metadata={'trigger_type': 'landfall'}
                ))

        return triggers
```

### 1.3 Call Parsing Method in parse_card()

```python
def parse_card(self, card: Dict) -> CardAbilities:
    # ... existing parsing ...

    # Parse landfall triggers
    landfall_triggers = self._parse_landfall_triggers(text, type_line)
    triggers.extend(landfall_triggers)

    # Set flag
    has_landfall = len(landfall_triggers) > 0

    return CardAbilities(
        # ... existing fields ...
        has_landfall=has_landfall,  # ADD THIS
    )
```

---

## Step 2: Add Effect Creator

**File:** `src/core/trigger_effects.py`

### 2.1 Create Effect Function

```python
def create_landfall_effect(trigger_data: Dict[str, Any]) -> Callable:
    """
    Create effect for landfall triggers.

    Used by: Scute Swarm, Lotus Cobra, etc.
    """
    effect_type = trigger_data.get('effect_type', 'generic')
    value = trigger_data.get('value', 1.0)

    def effect(board_state, source_card, **kwargs):
        """Execute landfall trigger."""
        logger.debug(f"{source_card.get('name', 'Unknown')} landfall triggered")

        if not hasattr(board_state, 'pending_effects'):
            board_state.pending_effects = []

        if effect_type == 'tokens':
            board_state.pending_effects.append({
                'type': 'create_tokens',
                'count': int(value),
                'token_type': 'creature',
                'power': 1,
                'toughness': 1,
                'types': [],
                'source': source_card.get('name', 'Unknown')
            })
        elif effect_type == 'draw':
            board_state.pending_effects.append({
                'type': 'draw_cards',
                'count': int(value),
                'source': source_card.get('name', 'Unknown')
            })
        # ... more effect types ...

    return effect
```

### 2.2 Register in Effect Factory

```python
EFFECT_TYPE_CREATORS = {
    # ... existing creators ...
    'landfall': create_landfall_effect,  # ADD THIS
}
```

### 2.3 Update create_effect_from_trigger()

```python
def create_effect_from_trigger(trigger) -> Optional[Callable]:
    """Create an executable effect function from a TriggerAbility."""
    effect_type = trigger.effect_type

    # Handle landfall
    if trigger.event == 'landfall':
        effect_type = 'landfall'  # ADD THIS

    # ... rest of function ...
```

---

## Step 3: Add BoardState Event Handler

**File:** `Simulation/unified_integration.py`

### 3.1 Create Event Handler

```python
def handle_land_etb(board_state, land_card, land_dict: Dict[str, Any] = None):
    """
    Handle a land entering the battlefield.

    This triggers 'landfall' event for all landfall triggers.

    Args:
        board_state: BoardState instance
        land_card: Land card that entered
        land_dict: Optional raw card data dict
    """
    if not hasattr(board_state, 'trigger_registry') or board_state.trigger_registry is None:
        return

    if land_dict is None:
        land_dict = _card_to_dict(land_card)

    # Trigger landfall event
    event_data = {
        'card': land_dict,
        'source_card': land_dict,
    }
    board_state.trigger_event('landfall', event_data)
    logger.debug(f"Landfall triggered by {land_card.name}")
```

### 3.2 Export the Handler

```python
# At top of file
from Simulation.unified_integration import (
    # ... existing handlers ...
    handle_land_etb,  # ADD THIS
)
```

---

## Step 4: Add Synergy Detection

**File:** `src/core/synergy_simulation_bridge.py`

### 4.1 Update detect_deck_synergies()

```python
def detect_deck_synergies(self, deck_cards: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Detect all synergies in a deck."""
    # ... existing synergy detection ...

    synergies = {
        # ... existing categories ...
        'landfall_synergies': [],  # ADD THIS
    }

    # Detect Landfall synergies (Landfall + Ramp)
    landfall_cards = [name for name, abilities in abilities_map.items() if abilities.has_landfall]
    ramp_cards = []

    # Find ramp cards (cards that put lands into play)
    for card in deck_cards:
        oracle_text = card.get('oracle_text', '').lower()
        if 'search your library for.*land' in oracle_text or 'put.*land.*battlefield' in oracle_text:
            ramp_cards.append(card.get('name'))

    for landfall_card in landfall_cards:
        for ramp_card in ramp_cards:
            synergies['landfall_synergies'].append({
                'card1': landfall_card,
                'card2': ramp_card,
                'type': 'landfall_ramp',
                'value': 5.0,
                'description': f"{landfall_card} triggers when {ramp_card} puts lands into play"
            })
            synergies['total_synergies'] += 1

    return synergies
```

---

## Step 5: Add Tests

### 5.1 Unit Test

**File:** `tests/test_landfall_mechanic.py`

```python
from src.api.local_cards import get_card_by_name, load_local_database
from src.core.card_parser import UnifiedCardParser

load_local_database()
parser = UnifiedCardParser()

# Test parsing
card = get_card_by_name("Scute Swarm")
abilities = parser.parse_card(card)

assert abilities.has_landfall, "Landfall flag not set"
landfall_triggers = abilities.get_triggers('landfall')
assert len(landfall_triggers) > 0, "No landfall triggers found"
print("✓ Landfall parsing works")
```

### 5.2 Integration Test

Add to `tests/test_end_to_end_unified_system.py`:

```python
# Turn 4: Test Landfall
print("\nTurn 4: Test Landfall")

scute_swarm = Card(
    name="Scute Swarm",
    type="Creature — Insect",
    mana_cost="{2}{G}",
    power=1,
    toughness=1,
    oracle_text="Landfall — Whenever a land enters the battlefield under your control, create a 1/1 green Insect creature token..."
)

board.creatures.append(scute_swarm)
scute_dict = get_card_by_name("Scute Swarm")
handle_card_etb(board, scute_swarm, scute_dict)

# Play a land (triggers landfall)
rampant_growth = Card(name="Forest", type="Basic Land — Forest", ...)
handle_land_etb(board, rampant_growth, forest_dict)

# Verify token created
assert len(board.creatures) > creatures_before, "Landfall token not created"
```

---

## Step 6: Update Documentation

### 6.1 Add to This Checklist

Add the new mechanic to the "Supported Mechanics" section at the end.

### 6.2 Add to IMPLEMENTATION_PROGRESS.md

```markdown
### Mechanics Supported:
- Rally (Ally tribal)
- Prowess
- Magecraft
- Token creation
- **Landfall** ← NEW
```

---

## Quick Reference: Files to Modify

When adding ANY new mechanic:

| Step | File | What to Add |
|------|------|-------------|
| 1 | `src/core/card_parser.py` | Flag + parsing method |
| 2 | `src/core/trigger_effects.py` | Effect creator function |
| 3 | `Simulation/unified_integration.py` | Event handler (optional) |
| 4 | `src/core/synergy_simulation_bridge.py` | Synergy detection |
| 5 | `tests/` | Unit + integration tests |
| 6 | Documentation | Update guides |

---

## Common Patterns

### Pattern 1: Simple Triggered Ability

**Examples:** Prowess, Magecraft, Landfall

```python
# 1. Parse pattern in oracle text
# 2. Create TriggerAbility with event type
# 3. Create effect function
# 4. Register in EFFECT_TYPE_CREATORS
```

### Pattern 2: Static Ability

**Examples:** Anthem effects, cost reduction

```python
# 1. Parse pattern in oracle text
# 2. Create StaticAbility
# 3. Create effect function (applies continuously)
# 4. Apply in board_state.apply_static_abilities()
```

### Pattern 3: Complex Interaction

**Examples:** Rally (tribal + ETB), Cascade

```python
# 1. Parse primary trigger
# 2. Parse condition/restriction
# 3. Create multi-step effect function
# 4. Handle state tracking in BoardState
```

---

## Testing Checklist

Before considering a mechanic "done":

- [ ] Parser detects the mechanic from oracle text
- [ ] Flag is set correctly (e.g., `has_landfall`)
- [ ] Triggers are registered with correct event type
- [ ] Effect function executes without errors
- [ ] Effect is visible in game state (creatures buffed, tokens created, etc.)
- [ ] Cleanup happens (for temporary effects)
- [ ] Synergies are detected
- [ ] Unit tests pass
- [ ] Integration test passes
- [ ] No regressions in existing tests

---

## Supported Mechanics (as of Part 6)

| Mechanic | Event Type | Effect Type | Example Card |
|----------|------------|-------------|--------------|
| Rally | `rally` | `rally_haste`, `rally_vigilance`, etc. | Chasm Guide |
| Prowess | `cast_noncreature_spell` | `prowess` | Monastery Swiftspear |
| Magecraft | `cast_or_copy_instant_sorcery` | varies | Veyran, Voice of Duality |
| Spellslinger | `cast_noncreature_spell` | `tokens`, `draw`, etc. | Kykar, Wind's Fury |
| ETB | `etb` | varies | Many cards |
| Attack | `attack` | varies | Narset, Enlightened Exile |
| Death | `death` | varies | Blood Artist |
| Token Creation | Various | `tokens` | Dragon Fodder |

---

## Troubleshooting

**Q: Parser sets flag but triggers aren't found**
- Check that `_parse_XXX_triggers()` is called in `parse_card()`
- Verify regex patterns match the oracle text
- Add debug logging to see what's being matched

**Q: Triggers register but don't execute**
- Check that effect function is in `EFFECT_TYPE_CREATORS`
- Verify `create_effect_from_trigger()` handles your event type
- Check that game events actually call `board_state.trigger_event()`

**Q: Effect executes but doesn't affect game state**
- Check `process_pending_effects()` handles your effect type
- Verify BoardState has the required method (e.g., `create_token()`)
- Add logging to see if effect data is created

**Q: Synergies not detected**
- Check `detect_deck_synergies()` in synergy bridge
- Verify synergy logic correctly identifies card pairs
- Test with actual deck cards, not theoretical examples

---

## Best Practices

1. **Always parse once** - Use unified parser, don't create separate extraction logic
2. **Use standard effect types** - Reuse existing effects when possible (tokens, draw, damage)
3. **Test incrementally** - Test parsing before effects, effects before synergies
4. **Follow naming conventions** - `has_XXX` for flags, `create_XXX_effect` for creators
5. **Document edge cases** - Note special interactions in code comments
6. **Update ALL tests** - Add to both unit and integration test suites

---

## Questions?

Check these files for examples:
- `src/core/card_parser.py` - Rally and prowess parsing
- `src/core/trigger_effects.py` - Rally effect creators
- `tests/test_end_to_end_unified_system.py` - Complete integration example

The unified architecture makes adding mechanics straightforward - just follow the pattern!
