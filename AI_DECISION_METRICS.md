# Real-Time AI Decision Metrics - Phase 1 Complete

## Overview

This document describes the real-time decision metrics added to the simulation AI (Phase 1 of Option C: Hybrid Approach).

**Status:** ✅ Phase 1 Complete - Metrics Implemented & Tested
**Next:** Phase 2 - Integrate into greedy loop
**Future:** Phase 3 - Activate ImprovedAI class

---

## Problem Statement

The simulation AI previously used a simple greedy algorithm with no card counting or resource management:
- No look-ahead planning
- No mana efficiency optimization
- No resource scarcity detection
- No opportunity cost evaluation

This resulted in suboptimal play and lower win rates than achievable.

---

## Solution: Real-Time Metrics (Phase 1)

Added **6 real-time decision metrics** to `BoardState` class that can be queried DURING gameplay to make intelligent decisions.

### Location
**File:** `Simulation/boardstate.py` (lines 6532-6767)

---

## The 6 Metrics

### 1. **Library Stats** - `get_library_stats()`

Tracks deck depletion for resource planning.

**Returns:**
```python
{
    'cards_remaining': int,      # Cards left in library
    'draw_probability': float,   # Probability of drawing (0-1)
    'scarcity_level': float,     # How depleted library is (0-1)
    'turns_until_empty': int,    # Estimated turns until empty
}
```

**Use Cases:**
- Detect when to prioritize card draw
- Know when to be aggressive vs conservative
- Plan for late game

**Example:**
```python
stats = board.get_library_stats()
if stats['scarcity_level'] > 0.7:
    # Library running low, prioritize card draw spells
    prioritize_draw = True
```

---

### 2. **Hand Resource Analysis** - `analyze_hand_resources()`

Analyzes current hand composition for strategic decisions.

**Returns:**
```python
{
    'hand_size': int,           # Total cards in hand
    'hand_lands': int,          # Number of lands
    'hand_spells': int,         # Number of spells
    'land_ratio': float,        # % lands in hand
    'spell_ratio': float,       # % spells in hand
    'diversity_score': float,   # Type diversity (0-1)
    'types_in_hand': list,      # Card types present
}
```

**Use Cases:**
- Avoid flooding (too many lands)
- Detect spell-heavy hands
- Evaluate hand quality

**Example:**
```python
hand = board.analyze_hand_resources()
if hand['land_ratio'] > 0.5:
    # Too many lands, prioritize playing spells
    prefer_spells = True
```

---

### 3. **Mana Efficiency** - `calculate_mana_efficiency()`

Calculates optimal mana usage to minimize waste.

**Returns:**
```python
{
    'mana_available': int,      # Total mana in pool
    'optimal_mana_usage': int,  # Max mana we can spend
    'wasted_mana': int,         # Mana that will be wasted
    'efficiency_score': float,  # 0-1, higher = better
    'castable_count': int,      # # of castable cards
}
```

**Use Cases:**
- Sequence spells to minimize wasted mana
- Decide when to hold vs cast
- Optimize turn efficiency

**Example:**
```python
eff = board.calculate_mana_efficiency()
if eff['wasted_mana'] > 2:
    # We'll waste mana, look for cheaper spells
    find_filler_spell = True
```

---

### 4. **Look-Ahead Playability** - `can_play_next_turn(card, look_ahead_turns=1)`

Forecasts when expensive cards become playable.

**Args:**
- `card`: Card to evaluate
- `look_ahead_turns`: How many turns ahead to check

**Returns:**
```python
{
    'turn_1': {
        'playable': bool,       # Can play next turn?
        'expected_mana': int,   # Expected mana available
        'card_cost': int,       # Card's mana cost
        'mana_short': int,      # How much short if unplayable
    },
    'turn_2': {...},  # If look_ahead_turns > 1
    ...
}
```

**Use Cases:**
- Decide whether to hold expensive cards
- Plan sequencing of plays
- Evaluate ramp effectiveness

**Example:**
```python
lookahead = board.can_play_next_turn(expensive_card, look_ahead_turns=2)
if lookahead['turn_1']['playable']:
    # Keep the card, we can play it next turn
    hold_card = True
else:
    # Won't be playable soon, maybe discard it
    consider_discarding = True
```

---

### 5. **Resource Scarcity Detection** - `detect_resource_scarcity()`

Detects when resources are running low and draw should be prioritized.

**Returns:**
```python
{
    'scarcity_score': float,     # 0-1, higher = more scarce
    'turns_until_empty': float,  # Estimated turns until out of cards
    'prioritize_draw': bool,     # Should prioritize draw?
    'critical_scarcity': bool,   # Critical resource shortage?
    'hand_size': int,           # Current hand size
    'library_size': int,        # Current library size
}
```

**Scarcity Score Factors:**
- Library running low (< 10 turns): +0.4
- Library moderately low (< 20 turns): +0.2
- Hand size < 3: +0.3
- Hand size < 5: +0.1
- No playable cards: +0.3

**Use Cases:**
- Prioritize card draw when scarce
- Decide when to be aggressive
- Manage resources effectively

**Example:**
```python
scarcity = board.detect_resource_scarcity()
if scarcity['prioritize_draw']:
    # Play draw spells before threats
    sort_key = lambda c: -getattr(c, 'draw_cards', 0)
```

---

### 6. **Opportunity Cost Calculator** - `calculate_opportunity_cost(card)`

Evaluates whether to play a card NOW or HOLD for later.

**Args:**
- `card`: Card to evaluate

**Returns:**
```python
{
    'immediate_value': float,   # Value of playing now
    'future_value': float,      # Value of holding
    'net_value': float,         # immediate - future
    'recommendation': str,      # 'PLAY_NOW', 'HOLD', or 'NEUTRAL'
    'confidence': float,        # How confident (0-1)
}
```

**Immediate Value Factors:**
- Haste creatures: +0.5
- Creature power: +power * 0.1
- Card draw (when scarce): +draw * 0.3
- Mana rocks (early game): +production * 0.1 * (turns_left / 10)

**Future Value Factors:**
- Can't play next turn: +0.2 (might as well hold)
- Hand size > 5: +0.1 (have options)

**Recommendation:**
- `net_value > 0.3`: PLAY_NOW
- `net_value < -0.3`: HOLD
- Otherwise: NEUTRAL

**Use Cases:**
- Decide play sequencing
- Avoid playing all threats at once
- Save resources for better opportunities

**Example:**
```python
opp_cost = board.calculate_opportunity_cost(card)
if opp_cost['recommendation'] == 'HOLD':
    # Don't play this card yet
    continue
```

---

## Testing

**Test File:** `test_realtime_metrics.py`

All 6 metrics have been tested and verified:
- ✅ Library Stats
- ✅ Hand Resource Analysis
- ✅ Mana Efficiency
- ✅ Look-Ahead Playability
- ✅ Resource Scarcity Detection
- ✅ Opportunity Cost Calculation

**Run Tests:**
```bash
python test_realtime_metrics.py
```

**Expected Output:**
```
🎉 ALL TESTS PASSED! 🎉
```

---

## Integration Guide (Phase 2)

### How to Use in Greedy Loop

Currently, the greedy loop in `simulate_game.py` (lines 476-667) doesn't use these metrics.

**Example Integration:**

```python
# BEFORE (greedy):
creature = board.get_best_creature_to_cast(verbose=verbose)
if creature:
    board.play_card(creature, verbose=verbose)

# AFTER (intelligent):
creature = board.get_best_creature_to_cast(verbose=verbose)
if creature:
    # Check opportunity cost
    opp_cost = board.calculate_opportunity_cost(creature)

    if opp_cost['recommendation'] == 'HOLD':
        # Don't play yet, move to next option
        continue

    # Check if we should prioritize draw instead
    scarcity = board.detect_resource_scarcity()
    if scarcity['prioritize_draw']:
        # Look for draw spells first
        draw_spell = next((c for c in board.hand
                          if getattr(c, 'draw_cards', 0) > 0), None)
        if draw_spell and Mana_utils.can_pay(draw_spell.mana_cost, board.mana_pool):
            board.play_card(draw_spell, verbose=verbose)
            continue

    # Play the creature
    board.play_card(creature, verbose=verbose)
```

---

## Performance Impact

**Computational Overhead:**
- All metrics: O(n) where n = hand size (typically 7-10)
- Negligible impact on simulation speed
- Worth the improved decision quality

**Measured:**
- Baseline: ~1.55 cards/turn
- With metrics: TBD (Phase 2)

---

## Next Steps (Phase 2)

1. **Integrate metrics into greedy loop** (`simulate_game.py`)
   - Add resource scarcity checks
   - Add opportunity cost evaluation
   - Add mana efficiency optimization

2. **Measure improvement**
   - Run 100 simulations baseline
   - Run 100 simulations with metrics
   - Compare:
     - Win rate
     - Average win turn
     - Card velocity
     - Mana efficiency

3. **Document results**
   - Quantify improvement
   - Identify remaining gaps

---

## Future: Phase 3 - ImprovedAI Integration

The `ImprovedAI` class (win_metrics.py:312-491) already exists but is unused.

**Phase 3 Plan:**
1. Wire up `ImprovedAI` class
2. Replace greedy card selection with `evaluate_card_priority()`
3. Use `get_optimal_play_sequence()` for spell ordering
4. Integrate with real-time metrics from Phase 1

**Expected Gains:**
- 10-20% improvement in win rate
- Better damage output
- More efficient resource usage

---

## Files Modified

| File | Lines | Changes |
|------|-------|---------|
| `Simulation/boardstate.py` | +235 | Added 6 real-time metric methods |
| `test_realtime_metrics.py` | +360 | Created comprehensive test suite |
| `AI_DECISION_METRICS.md` | NEW | This documentation |

---

## Summary

**Phase 1 Complete:** ✅
- Real-time metrics implemented
- All tests passing
- Ready for integration

**What We Can Now Do:**
1. ✅ Track library depletion
2. ✅ Analyze hand composition
3. ✅ Calculate mana efficiency
4. ✅ Look ahead for playability
5. ✅ Detect resource scarcity
6. ✅ Evaluate opportunity cost

**What's Next:**
- Integrate into greedy loop (Phase 2)
- Measure improvement
- Activate ImprovedAI (Phase 3)

---

**Ready for deployment!** 🚀
