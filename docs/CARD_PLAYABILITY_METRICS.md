# Card Playability Metrics - Documentation

**Version:** 1.0
**Date:** 2025-12-25
**Status:** ✅ Implemented

---

## Overview

Card playability metrics have been added to the deck effectiveness dashboard to provide insights into:
- **Card availability**: How many cards are drawn each turn
- **Hand quality**: Hand size over time
- **Playability**: How many cards can actually be cast vs. stuck in hand
- **Efficiency**: What percentage of your hand is castable

These metrics help identify problems like:
- ❌ **Mana screw**: Not enough lands, can't cast spells
- ❌ **Color screw**: Wrong color mana, can't cast colored spells
- ❌ **Mana flood**: Too many lands, not enough spells
- ❌ **Dead turns**: Turns where you can't play anything meaningful

---

## Available Metrics

### 1. **Average Cards Drawn Per Turn**
- **What it measures**: Number of cards drawn each turn (including draw step + additional draws)
- **Ideal value**: 1+ (more is better for card advantage decks)
- **Low values indicate**: Deck may lack card draw engines

### 2. **Average Hand Size Per Turn**
- **What it measures**: Total cards in hand at start of main phase
- **Ideal range**: 3-7 cards
- **Low values indicate**: Either playing out hand efficiently OR running out of gas
- **High values indicate**: Either card draw engines working OR mana issues preventing plays

### 3. **Average Castable Non-Lands Per Turn**
- **What it measures**: Non-land cards in hand that CAN be cast with available mana
- **Ideal value**: 2-4 (depends on deck strategy)
- **High values indicate**: Good mana base, playable spells

### 4. **Average Uncastable Non-Lands Per Turn**
- **What it measures**: Non-land cards STUCK in hand (insufficient mana/wrong colors)
- **⚠️ WARNING metric**: High values = problem!
- **Ideal value**: 0-1
- **High values (3+) indicate**: Mana screw, color screw, or curve problems

### 5. **Castable Percentage Per Turn**
- **What it measures**: (Castable / Total Non-Lands) × 100
- **Ideal value**: 75-100%
- **Warning range**: 50-75% (playable but inefficient)
- **Critical range**: <50% (serious mana issues)

---

## Implementation Details

### Modified Files

#### 1. **`Simulation/win_metrics.py`**
**Changes:**
- Added 5 new fields to `WinMetrics` dataclass:
  - `avg_cards_drawn_per_turn: List[float]`
  - `avg_hand_size_per_turn: List[float]`
  - `avg_castable_non_lands_per_turn: List[float]`
  - `avg_uncastable_non_lands_per_turn: List[float]`
  - `avg_castable_percentage_per_turn: List[float]`

- Modified `run_goldfish_simulation_with_metrics()`:
  - Collects card playability metrics from each simulation
  - Aggregates across all simulations using `statistics.mean()`
  - Calculates castable percentage for each turn

- Modified `get_dashboard_metrics()`:
  - Exposes all 5 new metrics in dashboard data dict

**Lines changed:** ~150 lines added

#### 2. **`src/simulation/deck_effectiveness.py`**
**Changes:**
- Added 5 new visualization charts in `get_effectiveness_figures()`:
  1. **Card Draw Chart**: Line chart showing cards drawn per turn
  2. **Hand Size Chart**: Area chart showing hand size over time
  3. **Castable vs Uncastable Chart**: Stacked area chart (green=castable, red=stuck)
  4. **Castable Percentage Chart**: Line chart with reference lines at 100% and 50%
  5. Updated summary HTML to show Turn 6 playability stats

- Added color-coding:
  - 🟢 Green: Castable ≥ 75% (good)
  - 🟠 Orange: Castable 50-75% (warning)
  - 🔴 Red: Castable < 50% (critical)

**Lines changed:** ~150 lines added

#### 3. **`Simulation/tests/test_card_playability_metrics.py`** (NEW)
- Comprehensive test suite
- Verifies metrics are collected and aggregated
- Validates dashboard integration

**Lines:** ~250 lines

---

## Usage Example

### Python API

```python
from src.simulation.deck_effectiveness import (
    run_effectiveness_analysis,
    get_effectiveness_figures
)

# Run analysis
results = run_effectiveness_analysis(
    deck_cards=my_deck_cards,
    commander_card=my_commander,
    num_simulations=100,
    max_turns=10
)

# Access card playability metrics
dashboard_data = results['dashboard_data']

# Cards drawn each turn (list of 10 values, one per turn)
cards_drawn = dashboard_data['avg_cards_drawn_per_turn']
print(f"Turn 6 cards drawn: {cards_drawn[5]:.2f}")

# Hand size each turn
hand_size = dashboard_data['avg_hand_size_per_turn']
print(f"Turn 6 hand size: {hand_size[5]:.2f}")

# Castable cards
castable = dashboard_data['avg_castable_non_lands_per_turn']
uncastable = dashboard_data['avg_uncastable_non_lands_per_turn']
print(f"Turn 6: {castable[5]:.1f} castable, {uncastable[5]:.1f} stuck")

# Castable percentage
castable_pct = dashboard_data['avg_castable_percentage_per_turn']
print(f"Turn 6 castable: {castable_pct[5]:.1f}%")

# Generate visualizations
figures = get_effectiveness_figures(results)

# Access individual charts
card_draw_chart = figures['card_draw']
hand_size_chart = figures['hand_size']
playability_chart = figures['card_playability']
castable_pct_chart = figures['castable_percentage']
```

### Dashboard Integration

The metrics are automatically included in the deck effectiveness dashboard:

```python
# In app.py or dashboard code
results = run_effectiveness_analysis(deck_cards, commander)
figures = get_effectiveness_figures(results)

# Display charts
dcc.Graph(figure=figures['card_draw'])
dcc.Graph(figure=figures['hand_size'])
dcc.Graph(figure=figures['card_playability'])
dcc.Graph(figure=figures['castable_percentage'])
```

---

## Interpreting Results

### Example 1: Healthy Deck
```
Turn 6 Metrics:
  Cards Drawn: 1.2
  Hand Size: 5.3
  Castable: 3.1
  Uncastable: 0.8
  Castable %: 79.5%
```
**Analysis:** ✅ Good! Deck is drawing extra cards, hand size is healthy, most cards are castable.

### Example 2: Mana Screw
```
Turn 6 Metrics:
  Cards Drawn: 1.0
  Hand Size: 6.8
  Castable: 1.2
  Uncastable: 4.6
  Castable %: 20.7%
```
**Analysis:** ❌ Problem! High hand size but low castable % = mana screw. Need more lands or ramp.

### Example 3: Running Out of Gas
```
Turn 6 Metrics:
  Cards Drawn: 1.0
  Hand Size: 2.1
  Castable: 1.8
  Uncastable: 0.3
  Castable %: 85.7%
```
**Analysis:** ⚠️ Mixed. Good castable % but low hand size = running out of cards. Need more card draw.

### Example 4: Mana Flood
```
Turn 6 Metrics:
  Cards Drawn: 1.0
  Hand Size: 4.2
  Castable: 4.2
  Uncastable: 0.0
  Castable %: 100%
```
**Analysis:** ⚠️ Suspiciously high castable %. If hand is mostly lands, this is mana flood. Check what cards are castable.

---

## Technical Notes

### Data Collection

Metrics are collected from `simulate_game.py` which already tracks:
- `cards_drawn[turn]` - Cards drawn this turn
- `hand_size[turn]` - Hand size after draw step
- `castable_non_lands[turn]` - Non-lands that can be cast
- `uncastable_non_lands[turn]` - Non-lands stuck in hand

These are aggregated across N simulations using `statistics.mean()`.

### Castable Percentage Calculation

For each game, for each turn:
```python
castable_pct = (castable / (castable + uncastable)) * 100
```

Then averaged across all games.

### Turn Indexing

⚠️ **Important**: Arrays are 0-indexed but represent turns 1-10:
- `metrics.avg_hand_size_per_turn[0]` = Turn 1
- `metrics.avg_hand_size_per_turn[5]` = Turn 6
- `metrics.avg_hand_size_per_turn[9]` = Turn 10

---

## Future Enhancements

Potential additions:

### 1. **Dead Turn Detection**
Track turns where 0 non-land cards were played:
```python
dead_turns = [turn for turn in range(1, 11) if cards_played[turn] == 0]
dead_turn_percentage = len(dead_turns) / 10 * 100
```

### 2. **Color Screw Detection**
Track turns where you had spells but wrong color mana:
```python
has_spell_in_hand = uncastable_non_lands[turn] > 0
has_mana_available = total_mana[turn] >= spell_cmc
different_colors = spell_colors != available_colors
color_screw = has_spell_in_hand and has_mana_available and different_colors
```

### 3. **Mana Efficiency Score**
```python
efficiency = (mana_spent / mana_available) * 100
# 90%+ = efficient
# 50-90% = inefficient
# <50% = serious problems
```

### 4. **Hand Quality Score**
Composite metric:
```python
hand_quality = (
    (castable_pct * 0.5) +           # 50% weight
    (hand_size / 7 * 100 * 0.3) +    # 30% weight
    (cards_drawn * 20 * 0.2)         # 20% weight
)
```

---

## Troubleshooting

### Problem: All metrics show 0.0
**Cause**: `simulate_game.py` not returning card playability metrics
**Fix**: Verify `simulate_game()` populates these arrays:
```python
metrics["cards_drawn"][turn] = ...
metrics["hand_size"][turn] = ...
metrics["castable_non_lands"][turn] = ...
metrics["uncastable_non_lands"][turn] = ...
```

### Problem: Metrics only populated for some turns
**Cause**: Array size mismatch
**Fix**: Check that arrays are padded to `max_turns + 1` length in `run_goldfish_simulation_with_metrics()`

### Problem: Castable percentage is NaN or infinite
**Cause**: Division by zero when no non-lands in hand
**Fix**: Already handled - returns 0.0 when `total_non_lands == 0`

---

## Version History

**v1.0 (2025-12-25)**
- Initial implementation
- 5 core metrics added
- Dashboard integration complete
- Test suite created

---

## Related Documentation

- `docs/ARCHITECTURE.md` - System architecture
- `docs/SYNERGY_SYSTEM.md` - Synergy detection
- `Simulation/README.md` - Simulation engine docs
- `CLAUDE.md` - Main AI guide

---

**Questions or Issues?**

Contact the development team or file an issue on GitHub.
