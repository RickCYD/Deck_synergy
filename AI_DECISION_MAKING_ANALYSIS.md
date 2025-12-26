# AI Decision-Making Deep Dive
## MTG Commander Deck Synergy Analyzer - Simulation Engine

**Date:** 2025-12-26
**Version:** Analysis v1.0
**Focus:** Understanding the AI decision-making system in goldfish simulation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [AI Architecture Overview](#ai-architecture-overview)
3. [The Two AI Implementations](#the-two-ai-implementations)
4. [Core Decision Functions](#core-decision-functions)
5. [Archetype-Aware Prioritization](#archetype-aware-prioritization)
6. [Resource Management System](#resource-management-system)
7. [Decision Trees & Flow](#decision-trees--flow)
8. [Strengths & Weaknesses](#strengths--weaknesses)
9. [Opportunities for Improvement](#opportunities-for-improvement)

---

## Executive Summary

The simulation engine uses a **two-tier AI system**:

1. **GreedyAI (Fallback)**: Simple priority-based decision-making focused on playing the highest-value cards
2. **ImprovedAI (Phase 3)**: Advanced decision-making with real-time metrics, archetype awareness, and resource scarcity detection

### Key Insights

- **Archetype-Aware**: AI adjusts priorities based on detected deck archetype (Aristocrats, Tokens, Voltron, etc.)
- **Real-Time Metrics**: Tracks resource scarcity, mana efficiency, hand composition, and opportunity costs
- **Priority-Based Scoring**: Every card gets a numeric score (0-1000+) determining cast order
- **Goldfish-Optimized**: Designed to maximize damage output in uncontested scenarios

**Files Analyzed:**
- `Simulation/win_metrics.py` (928 lines) - ImprovedAI implementation
- `Simulation/boardstate.py` (6,375 lines) - Core game mechanics & GreedyAI
- `Simulation/simulate_game.py` (914 lines) - Game loop integration

---

## AI Architecture Overview

### High-Level Flow

```
Game Start
    ↓
Initialize ImprovedAI (if available)
    ├─ Analyze deck archetype
    ├─ Set game plan (aggro/combo/midrange/voltron)
    └─ Prepare decision metrics
    ↓
Each Turn:
    ├─ Choose land to play (GreedyAI)
    ├─ Main Phase Loop:
    │   ├─ Play all mana rocks (GreedyAI)
    │   ├─ Cast commander (GreedyAI)
    │   ├─ Play ramp spells (GreedyAI)
    │   ├─ Play enchantments (GreedyAI)
    │   ├─ Choose best creature (ImprovedAI or GreedyAI)
    │   │   ├─ Get optimal play sequence (ImprovedAI)
    │   │   ├─ Check if should hold card (ImprovedAI)
    │   │   └─ Cast or skip
    │   └─ Play equipment (GreedyAI)
    ├─ Optimize leftover mana (GreedyAI)
    └─ Combat Phase (automatic)
```

### Key Integration Points

**File: simulate_game.py:599-650**
```python
# PHASE 3: Use ImprovedAI for intelligent creature selection
if ai:
    # Get all castable creatures
    castable_creatures = [
        c for c in board.hand
        if 'Creature' in c.type and Mana_utils.can_pay(c.mana_cost, board.mana_pool)
    ]

    if castable_creatures:
        # Use ImprovedAI to get optimal play sequence
        optimal_sequence = ai.get_optimal_play_sequence(castable_creatures)
        creature = optimal_sequence[0] if optimal_sequence else None
else:
    # Fallback to greedy AI
    creature = board.get_best_creature_to_cast(verbose=verbose)

# Check if we should hold back
if ai:
    should_hold = ai.should_hold_card(creature)
else:
    should_hold = board.should_hold_back_creature(creature, verbose=verbose)
```

---

## The Two AI Implementations

### 1. GreedyAI (BoardState Methods)

**Location:** `Simulation/boardstate.py`
**Philosophy:** Play the highest-priority card available without complex lookahead

#### Key Methods

| Method | Purpose | Priority Logic |
|--------|---------|----------------|
| `choose_land_to_play()` | Select which land to play | Prioritizes color-fixing, untapped lands, fetch lands |
| `get_best_creature_to_cast()` | Select creature to cast | Calls `prioritize_creature_for_casting()` |
| `prioritize_creature_for_casting()` | Score creatures 0-1000+ | Archetype-aware bonuses, ETB value, power, keywords |
| `get_best_equipment_target()` | Choose equipment target | Commander > Legendary > Attack triggers > Power |
| `should_hold_back_creature()` | Decide to hold card | Checks opponent threat level, avoids overextending |
| `optimize_mana_usage()` | Use floating mana | Activates abilities (70% chance), casts instants (50% chance) |

#### Example: Land Selection Heuristic

**File: boardstate.py:1895-2000 (approximate)**
```python
def choose_land_to_play(self):
    """
    Choose the best land to play this turn.
    Priorities:
    1. Color fixing (if missing colors)
    2. Untapped lands
    3. Fetch lands (for thinning)
    4. Basic lands
    """
    lands_in_hand = [c for c in self.hand if 'Land' in c.type]

    if not lands_in_hand:
        return None

    # Analyze current mana pool colors
    current_colors = set()
    for land in self.lands_untapped + self.lands_tapped:
        for color in land.produces_colors:
            current_colors.add(color)

    # Check what colors we need for hand
    needed_colors = analyze_hand_color_requirements(self.hand)
    missing_colors = needed_colors - current_colors

    # Priority 1: Lands that fix missing colors
    if missing_colors:
        for land in lands_in_hand:
            if any(c in land.produces_colors for c in missing_colors):
                if not land.etb_tapped:
                    return land  # Untapped color-fixing is best!

    # Priority 2: Untapped lands
    for land in lands_in_hand:
        if not land.etb_tapped:
            return land

    # Priority 3: Fetch lands
    for land in lands_in_hand:
        if land.fetch_basic:
            return land

    # Default: First land in hand
    return lands_in_hand[0]
```

### 2. ImprovedAI (Phase 3)

**Location:** `Simulation/win_metrics.py`
**Philosophy:** Intelligent decision-making using real-time metrics and archetype awareness

#### Core Components

**Class: ImprovedAI (lines 312-542)**

```python
class ImprovedAI:
    """
    Improved AI for goldfish simulation focusing on optimal damage output.

    Key improvements:
    1. Prioritize damage-dealing cards
    2. Sequence plays for maximum impact
    3. Track combo pieces
    4. Optimize mana usage
    """

    def __init__(self, board: 'BoardState'):
        self.board = board
        self.game_plan = self._determine_game_plan()
```

#### Key Methods

| Method | Purpose | Intelligence Level |
|--------|---------|-------------------|
| `_determine_game_plan()` | Detect deck strategy | Maps archetype → game plan |
| `evaluate_card_priority()` | Score individual cards | Integrates real-time metrics, scarcity detection |
| `get_optimal_play_sequence()` | Order multiple casts | Mana producers first, then by priority |
| `should_hold_card()` | Hold vs play decision | Opportunity cost, resource scarcity, future playability |

---

## Core Decision Functions

### Function 1: Card Priority Evaluation

**File: win_metrics.py:346-450**

```python
def evaluate_card_priority(self, card: 'Card') -> float:
    """
    Evaluate card priority for casting order.
    Higher score = cast sooner.

    Returns: Priority score (0-100)
    """
    score = 0.0
    oracle = getattr(card, 'oracle_text', '').lower()
    card_type = getattr(card, 'type', '')

    # PHASE 3: Use real-time metrics to adjust priorities
    try:
        scarcity = self.board.detect_resource_scarcity()
        hand_stats = self.board.analyze_hand_resources()
        mana_eff = self.board.calculate_mana_efficiency()

        # Boost card draw when resources are scarce
        draw = getattr(card, 'draw_cards', 0) or 0
        if draw > 0:
            if scarcity['prioritize_draw']:
                score += draw * 20  # Much higher priority when scarce
            else:
                score += draw * 8  # Normal priority

        # Boost mana rocks when hand is spell-heavy
        mana_prod = getattr(card, 'mana_production', 0) or 0
        if mana_prod > 0:
            turn_factor = max(1, 6 - self.board.turn)
            if hand_stats['spell_ratio'] > 0.7:
                # Hand is spell-heavy, prioritize mana
                score += mana_prod * 15 * turn_factor
            else:
                score += mana_prod * 10 * turn_factor

    except (AttributeError, Exception):
        # Fallback to original logic if metrics not available
        pass

    # Base scores by type
    if 'creature' in card_type.lower():
        power = getattr(card, 'power', 0) or 0
        score += power * 5

        # Haste bonus (immediate damage)
        if getattr(card, 'has_haste', False):
            score += 15

        # Evasion bonuses
        if getattr(card, 'has_flying', False):
            score += 8
        if 'unblockable' in oracle:
            score += 12

    # Game plan specific bonuses
    if self.game_plan == 'voltron':
        if 'equipment' in card_type.lower():
            score += 15
    elif self.game_plan == 'aggro':
        if 'creature' in card_type.lower():
            score += 10
    elif self.game_plan == 'combo':
        if 'tutor' in oracle or 'search' in oracle:
            score += 20

    return score
```

**Key Insight:** The AI dynamically adjusts priorities based on game state, not just static card properties!

### Function 2: Creature Prioritization (Archetype-Aware)

**File: boardstate.py:3610-3818**

This is the **most complex decision function** in the codebase. It scores creatures 0-1000+ based on:

#### Priority Tiers

1. **Commander**: +1000 (always highest)
2. **Archetype-Specific Bonuses**: +650-950 depending on synergy
3. **Legendary Creatures**: +500-600
4. **Attack Triggers**: +150-300
5. **ETB Value**: +100-200
6. **Mana Dorks**: +400
7. **Base Power**: +(power × 5)
8. **Weenie Penalty**: -50 (unless Go-Wide deck)

#### Archetype Examples

**Aristocrats Deck:**
```python
if self.primary_archetype == 'Aristocrats':
    # Death triggers
    if 'dies' in oracle and ('opponent' in oracle or 'each player' in oracle):
        archetype_bonus += 850  # Very high priority!

    # Sacrifice outlets
    if 'sacrifice' in oracle and ':' in oracle:
        archetype_bonus += 900  # Critical piece!

    # Token generators (as fodder)
    if 'create' in oracle and 'token' in oracle:
        archetype_bonus += 750
```

**Tokens Deck:**
```python
elif self.primary_archetype == 'Tokens':
    # Token doublers (highest priority)
    if 'twice that many' in oracle or 'double' in oracle and 'token' in oracle:
        archetype_bonus += 950

    # Token generators
    if 'create' in oracle and 'token' in oracle:
        archetype_bonus += 800

    # Anthems
    if 'creatures you control get +' in oracle:
        archetype_bonus += 700
```

**Result:** Aristocrats deck will cast Blood Artist (850 points) before a 5/5 vanilla creature (25 points)!

### Function 3: Hold vs Play Decision

**File: win_metrics.py:485-536**

```python
def should_hold_card(self, card: 'Card') -> bool:
    """
    Determine if we should hold a card for later.

    Returns: True if card should be held
    """
    # PHASE 3: Use real-time metrics
    try:
        # Check opportunity cost
        opp_cost = self.board.calculate_opportunity_cost(card)
        if opp_cost['recommendation'] == 'HOLD':
            return True

        # Check resource scarcity
        scarcity = self.board.detect_resource_scarcity()

        # If resources are scarce, hold expensive cards
        if scarcity['critical_scarcity']:
            cmc = self._get_cmc(card)
            if cmc >= 5:
                return True

        # Check if we can play it next turn
        look_ahead = self.board.can_play_next_turn(card, look_ahead_turns=1)
        if not look_ahead['turn_1']['playable']:
            # Can't play next turn, might as well hold
            return True

    except (AttributeError, Exception):
        # Fallback to original logic
        pass

    # Original logic: Check if we're close to winning
    cumulative_damage = sum(...)

    # If we're about to win, hold expensive cards
    if cumulative_damage >= 100:
        cmc = self._get_cmc(card)
        if cmc >= 6:
            return True

    return False
```

**Decision Factors:**
1. Opportunity cost analysis
2. Resource scarcity (low hand size, low library)
3. Future playability (can we cast it next turn?)
4. Win proximity (don't waste mana if winning soon)

---

## Archetype-Aware Prioritization

### Archetype Detection

**File: boardstate.py:252-361**

```python
def _analyze_deck_strategy(self, deck):
    """
    Analyze deck composition to detect archetype.

    Returns:
        - archetype: Detected deck strategy
        - removal_modifier: Multiplier for opponent removal
        - wipe_modifier: Multiplier for board wipes
        - protection_count: Number of protection spells
    """
    equipment_count = 0
    creature_count = 0
    token_generators = 0
    go_wide_count = 0

    # Count indicators
    for card in deck:
        if 'equipment' in card.type.lower():
            equipment_count += 1
        if 'creature' in card.type.lower():
            creature_count += 1
        if 'create' in oracle and 'token' in oracle:
            token_generators += 1
        if 'creatures you control get +' in oracle:
            go_wide_count += 1

    # Calculate ratios
    equipment_ratio = equipment_count / total_cards
    creature_ratio = creature_count / total_cards

    # Determine archetype
    if equipment_ratio > 0.12 and creature_ratio < 0.25:
        archetype = 'voltron'
    elif token_generators >= 5 or go_wide_count >= 3:
        archetype = 'go_wide'
    elif creature_ratio > 0.30 and equipment_ratio < 0.08:
        archetype = 'aggro'
    elif creature_ratio > 0.20 and creature_ratio < 0.35:
        archetype = 'midrange'
    elif creature_ratio < 0.15:
        archetype = 'combo_control'

    return archetype
```

### Supported Archetypes

| Archetype | Detection Criteria | Priority Boosts |
|-----------|-------------------|-----------------|
| **Aristocrats** | Detected via commander metadata | Death triggers (+850), Sacrifice outlets (+900), Token generators (+750) |
| **Tokens** | 5+ token generators OR 3+ anthems | Token doublers (+950), Generators (+800), Anthems (+700) |
| **Go-Wide** | Many token generators + anthems | Small creatures (+700), Anthems (+850) |
| **Counters** | Detected via commander metadata | Proliferate (+900), Counter generators (+850), Doublers (+950) |
| **Reanimator** | Detected via commander metadata | Big creatures (+650), Mill/discard (+700) |
| **Voltron** | 12%+ equipment, <25% creatures | Equipment (+15), Commander (+30), Legendary creatures (+500+) |
| **Aggro** | 30%+ creatures, <8% equipment | Creatures (+10) |
| **Combo/Control** | <15% creatures | Tutors (+20), removal immunity |

---

## Resource Management System

The ImprovedAI uses **5 real-time metric systems** to make intelligent decisions.

### System 1: Resource Scarcity Detection

**File: boardstate.py:6254-6297**

```python
def detect_resource_scarcity(self) -> dict:
    """
    Detect resource scarcity to prioritize card draw.

    Returns:
        - scarcity_score: 0-1, higher = more scarce
        - prioritize_draw: bool
        - critical_scarcity: bool
    """
    # Calculate turns until resources run out
    avg_cards_drawn_per_turn = 1.5
    turns_until_empty = library_size / avg_cards_drawn_per_turn

    scarcity_score = 0.0

    # Factor 1: Library running low
    if turns_until_empty < 10:
        scarcity_score += 0.4
    elif turns_until_empty < 20:
        scarcity_score += 0.2

    # Factor 2: Hand running low
    if hand_size < 3:
        scarcity_score += 0.3
    elif hand_size < 5:
        scarcity_score += 0.1

    # Factor 3: No playable cards
    if castable_count == 0:
        scarcity_score += 0.3

    scarcity_score = min(1.0, scarcity_score)

    return {
        'scarcity_score': scarcity_score,
        'prioritize_draw': scarcity_score > 0.5,
        'critical_scarcity': scarcity_score > 0.7,
    }
```

**Use Case:** When scarcity is high, card draw effects get **20×8 = 160% priority boost**!

### System 2: Hand Composition Analysis

**File: boardstate.py:6144-6178**

```python
def analyze_hand_resources(self) -> dict:
    """
    Analyze current hand composition.

    Returns:
        - hand_lands: Number of lands
        - hand_spells: Number of non-lands
        - land_ratio: Percentage of hand that's lands
        - spell_ratio: Percentage of hand that's spells
        - diversity_score: 0-1, types present / 5 major types
    """
    hand_lands = sum(1 for c in self.hand if 'Land' in c.type)
    hand_spells = len(self.hand) - hand_lands

    # Count unique card types
    card_types = {'creature', 'spell', 'artifact', 'enchantment', 'land'}
    present_types = set()
    for card in self.hand:
        if 'Creature' in card.type:
            present_types.add('creature')
        # ... (similar for other types)

    diversity_score = len(present_types) / 5.0

    return {
        'hand_size': len(self.hand),
        'hand_lands': hand_lands,
        'hand_spells': hand_spells,
        'land_ratio': hand_lands / hand_size,
        'spell_ratio': hand_spells / hand_size,
        'diversity_score': diversity_score,
    }
```

**Use Case:** If spell_ratio > 0.7, mana rocks get **50% higher priority** (15x vs 10x multiplier)!

### System 3: Mana Efficiency Calculator

**File: boardstate.py:6180-6219**

```python
def calculate_mana_efficiency(self) -> dict:
    """
    Calculate mana efficiency for optimal resource usage.

    Returns:
        - mana_available: Total mana in pool
        - optimal_mana_usage: Maximum mana we can spend
        - wasted_mana: Floating mana
        - efficiency_score: 0-1, higher is better
    """
    mana_available = len(self.mana_pool)

    # Calculate castable costs
    castable_costs = []
    for card in self.hand:
        if 'Land' not in card.type:
            cost = parse_mana_cost(card.mana_cost)
            if can_pay(card.mana_cost, self.mana_pool):
                castable_costs.append(cost)

    # Greedy knapsack: maximize mana spent
    castable_costs.sort(reverse=True)
    optimal_mana_usage = 0
    remaining = mana_available

    for cost in castable_costs:
        if cost <= remaining:
            optimal_mana_usage += cost
            remaining -= cost

    wasted_mana = mana_available - optimal_mana_usage
    efficiency_score = optimal_mana_usage / mana_available if mana_available > 0 else 1.0

    return {
        'mana_available': mana_available,
        'optimal_mana_usage': optimal_mana_usage,
        'wasted_mana': wasted_mana,
        'efficiency_score': efficiency_score,
    }
```

**Use Case:** Helps AI minimize wasted mana by casting optimal sequence!

### System 4: Future Playability (Look-Ahead)

**File: boardstate.py:6221-6252**

```python
def can_play_next_turn(self, card, look_ahead_turns: int = 1) -> dict:
    """
    Determine if a card will be playable in future turns.

    Args:
        card: Card to evaluate
        look_ahead_turns: How many turns to look ahead

    Returns:
        Dict with playability forecast
    """
    current_lands = len(self.lands_untapped) + len(self.lands_tapped)
    card_cost = parse_mana_cost(card.mana_cost)

    results = {}
    for turns_ahead in range(1, look_ahead_turns + 1):
        expected_lands = current_lands + turns_ahead  # Assume 1 land/turn
        expected_mana_sources = expected_lands + len(self.artifacts)
        expected_mana = expected_mana_sources

        playable = card_cost <= expected_mana

        results[f'turn_{turns_ahead}'] = {
            'playable': playable,
            'expected_mana': expected_mana,
            'card_cost': card_cost,
            'mana_short': max(0, card_cost - expected_mana),
        }

    return results
```

**Use Case:** If card won't be playable next turn, AI might hold it to avoid clogging hand!

### System 5: Opportunity Cost Analysis

**File: boardstate.py:6299-6370 (approximate)**

```python
def calculate_opportunity_cost(self, card) -> dict:
    """
    Calculate opportunity cost of playing a card now vs later.

    Returns:
        - immediate_value: Value of playing now
        - future_value: Value of waiting
        - recommendation: 'PLAY' or 'HOLD'
    """
    immediate_value = 0.0

    # Immediate value factors
    if 'Creature' in card.type and card.has_haste:
        immediate_value += 0.5  # Immediate damage

    # Card draw when scarce
    scarcity = self.detect_resource_scarcity()
    draw_value = card.draw_cards or 0
    if draw_value > 0 and scarcity['prioritize_draw']:
        immediate_value += draw_value * 0.3

    # Mana rocks early game
    mana_prod = card.mana_production or 0
    if mana_prod > 0:
        turns_left = 10 - self.turn
        immediate_value += mana_prod * 0.1 * (turns_left / 10)

    # Future value factors
    future_value = 0.0

    # Can we play better cards next turn if we wait?
    look_ahead = self.can_play_next_turn(card)
    if not look_ahead['turn_1']['playable']:
        future_value -= 0.5  # Can't play anyway, lose value

    # Compare
    if immediate_value > future_value:
        return {'recommendation': 'PLAY', 'immediate_value': immediate_value}
    else:
        return {'recommendation': 'HOLD', 'future_value': future_value}
```

**Use Case:** Complex cost-benefit analysis for every card!

---

## Decision Trees & Flow

### Main Phase Decision Tree

```
START Main Phase
    ↓
┌─────────────────────────────────────────┐
│ While True: (greedy loop)               │
├─────────────────────────────────────────┤
│                                         │
│ 1. Play ALL mana rocks                 │
│    ├─ Check: Won't delay commander?    │
│    ├─ Simulate pool after playing      │
│    └─ If still can cast cmd → play     │
│                                         │
│ 2. Cast commander (if affordable)      │
│    ├─ Pay mana                          │
│    ├─ Auto-equip equipment              │
│    └─ Update metrics                    │
│                                         │
│ 3. Play ramp sorceries                 │
│    └─ Cultivate, Rampant Growth, etc.  │
│                                         │
│ 4. Play enchantments                   │
│    └─ Impact Tremors, anthems, etc.    │
│                                         │
│ 5. Choose best creature                │
│    ├─ [ImprovedAI] Get optimal seq     │
│    │   ├─ Score all creatures          │
│    │   ├─ Mana producers first         │
│    │   └─ Return sorted list           │
│    │                                    │
│    ├─ [GreedyAI] Get best creature     │
│    │   └─ Score with archetype bonuses │
│    │                                    │
│    ├─ [ImprovedAI] Should hold?        │
│    │   ├─ Check opportunity cost       │
│    │   ├─ Check scarcity               │
│    │   └─ Check future playability     │
│    │                                    │
│    ├─ [GreedyAI] Should hold?          │
│    │   └─ Check opponent threat        │
│    │                                    │
│    └─ Cast or skip                     │
│                                         │
│ 6. Play equipment                      │
│    └─ Auto-attach to best target       │
│                                         │
│ 7. No actions possible?                │
│    └─ BREAK loop                       │
│                                         │
└─────────────────────────────────────────┘
    ↓
Optimize leftover mana
    ├─ Activate abilities (70% chance)
    └─ Cast instants (50% chance)
    ↓
END Main Phase
```

### Creature Scoring Decision Tree

```
Input: Creature card
    ↓
Base score = 100
    ↓
┌──────────────────────────────────────┐
│ Is Commander?                        │
│ YES → +1000 → RETURN                 │
│ NO  → Continue                       │
└──────────────────────────────────────┘
    ↓
┌──────────────────────────────────────┐
│ ARCHETYPE-SPECIFIC BONUSES           │
├──────────────────────────────────────┤
│                                      │
│ IF Aristocrats:                      │
│   ├─ Death trigger? +850             │
│   ├─ Sac outlet? +900                │
│   └─ Token gen? +750                 │
│                                      │
│ ELIF Tokens:                         │
│   ├─ Token doubler? +950             │
│   ├─ Token gen? +800                 │
│   └─ Anthem? +700                    │
│                                      │
│ ELIF Counters:                       │
│   ├─ Proliferate? +900               │
│   ├─ Counter gen? +850               │
│   └─ Counter doubler? +950           │
│                                      │
│ ... (other archetypes)               │
│                                      │
└──────────────────────────────────────┘
    ↓
┌──────────────────────────────────────┐
│ GENERAL BONUSES                      │
├──────────────────────────────────────┤
│                                      │
│ ├─ Legendary + power ≥3? +500-600   │
│ ├─ Attack draw trigger? +300        │
│ ├─ Attack token trigger? +250       │
│ ├─ ETB draw? +200                    │
│ ├─ ETB tutor? +180                   │
│ ├─ Mana dork? +400                   │
│ ├─ Base power × 5                    │
│ └─ Weenie penalty? -50 (unless Go-Wide)│
│                                      │
└──────────────────────────────────────┘
    ↓
Return final score
```

---

## Strengths & Weaknesses

### ✅ Strengths

1. **Archetype Awareness**
   - Detects deck strategy from card composition
   - Adjusts priorities dynamically (Aristocrats deck will prioritize Blood Artist over 5/5 vanilla)
   - Synergy-aware casting order maximizes deck potential

2. **Real-Time Metrics Integration**
   - Resource scarcity detection prevents flooding/starvation
   - Hand composition analysis optimizes spell vs land ratio
   - Mana efficiency calculator minimizes waste
   - Look-ahead system prevents unplayable cards clogging hand

3. **Two-Tier Fallback System**
   - ImprovedAI provides intelligent decisions when available
   - GreedyAI ensures simulation never fails
   - Graceful degradation on errors

4. **Goldfish Optimization**
   - Designed specifically for uncontested damage output measurement
   - Maximizes speed (average win turn) and consistency (win %)
   - Perfect for deck potential analysis

5. **Comprehensive Creature Prioritization**
   - 1000+ point scoring system allows fine-grained differentiation
   - Considers ETB value, attack triggers, keywords, power, synergies
   - Commander always prioritized correctly

6. **Equipment Intelligence**
   - Smart target selection (Commander > Legendary > Triggers > Power)
   - Auto-equip after casting creatures
   - Considers keywords that benefit from buffs (double strike, trample)

### ❌ Weaknesses

1. **Archetype Detection Limitations**
   - **Only detects from deck composition**, not commander abilities
   - Misses nuanced strategies (e.g., Aristocrats with few sacrifice outlets)
   - Hardcoded thresholds (12% equipment = Voltron) may not fit all decks
   - **Solution:** Integrate commander oracle text analysis, use ML clustering

2. **No Multi-Card Synergy Evaluation**
   - Evaluates cards in isolation, not combos
   - Won't recognize "This creature + that enchantment = game-winning combo"
   - Example: Won't prioritize casting Ashnod's Altar before Nim Deathmantle
   - **Solution:** Pre-compute 2-card and 3-card synergies from synergy engine

3. **Greedy Play Sequence**
   - Always plays mana rocks → commander → creatures in that order
   - Doesn't consider alternate sequences (e.g., creature → rock → bigger creature)
   - Knapsack mana optimization is greedy, not optimal
   - **Solution:** Implement dynamic programming for optimal mana usage

4. **Limited Instant-Speed Interaction**
   - Only uses floating mana with 50-70% probability (randomized!)
   - No strategic holding of instants for combat tricks
   - No bluffing or reactive play (but goldfish mode doesn't need it)
   - **Acceptable:** Goldfish simulation doesn't model opponents

5. **No Mulligan Strategy**
   - `should_mulligan()` exists but uses very simple rules (0-1 lands or 6-7 lands)
   - Doesn't consider hand playability, combo potential, or curve
   - **Solution:** Implement London mulligan strategy with hand simulation

6. **Hardcoded Probabilities**
   - `optimize_mana_usage()` uses random 70%/50% thresholds
   - `should_hold_back_creature()` uses random 30% threshold
   - Not data-driven or learned from simulations
   - **Solution:** Train decision probabilities from simulation results

7. **No Long-Term Planning**
   - Look-ahead is only 1 turn (`can_play_next_turn(look_ahead_turns=1)`)
   - Doesn't plan mana curve for next 3-5 turns
   - Won't hold expensive bombs for future turns strategically
   - **Solution:** Implement multi-turn planning with game tree search

8. **Opportunity Cost Calculation Incomplete**
   - `calculate_opportunity_cost()` is defined but implementation seems incomplete in the code
   - Would benefit from more sophisticated modeling
   - **Solution:** Implement full cost-benefit analysis

---

## Opportunities for Improvement

### 1. Machine Learning Integration

**Current State:** Rule-based priority scoring
**Opportunity:** Train ML model on simulation results

```python
# Potential approach
class MLImprovedAI(ImprovedAI):
    def __init__(self, board):
        super().__init__(board)
        self.model = load_trained_model('creature_priority_model.pkl')

    def evaluate_card_priority(self, card):
        # Extract features
        features = self.extract_card_features(card)

        # Get ML prediction
        ml_score = self.model.predict([features])[0]

        # Combine with rule-based score
        rule_score = super().evaluate_card_priority(card)

        # Weighted blend
        return 0.6 * ml_score + 0.4 * rule_score

    def extract_card_features(self, card):
        return [
            card.power or 0,
            card.toughness or 0,
            len(card.triggered_abilities),
            int(card.has_haste),
            int(card.has_flying),
            self.board.turn,
            len(self.board.creatures),
            len(self.board.mana_pool),
            # ... 50+ more features
        ]
```

**Benefits:**
- Learn from 100,000+ simulations
- Discover non-obvious patterns
- Adapt to specific deck types automatically

### 2. Combo Recognition

**Current State:** No combo detection during play
**Opportunity:** Integrate synergy engine's combo data

```python
def prioritize_creature_for_casting(self, creature, verbose=False):
    score = 100

    # NEW: Check if this creature completes a known combo
    for combo in self.board.known_combos:
        if creature.name in combo['cards']:
            # Check if other pieces are on board
            other_pieces = [c for c in combo['cards'] if c != creature.name]
            on_board = [c.name for c in self.board.creatures + self.board.artifacts + self.board.enchantments]

            if all(piece in on_board for piece in other_pieces):
                score += 2000  # MASSIVE bonus for completing combo!
                if verbose:
                    print(f"    COMBO PIECE: {creature.name} completes {combo['name']}!")

    # ... rest of scoring
```

**Benefits:**
- Win faster by assembling combos
- Prioritize combo pieces over vanilla creatures
- More accurate deck potential measurement

### 3. Multi-Turn Planning

**Current State:** 1-turn look-ahead
**Opportunity:** Game tree search for 3-5 turn planning

```python
def plan_next_turns(self, num_turns=3):
    """
    Simulate next N turns to find optimal play sequence.

    Returns:
        Best action sequence for maximum damage output
    """
    # Create game state copy
    sim_board = copy.deepcopy(self.board)

    # Search tree
    best_sequence = []
    max_damage = 0

    # Recursive search with pruning
    def search(board, turn, sequence, depth):
        if depth == 0:
            return calculate_total_damage(board)

        # Get all possible actions
        actions = get_possible_actions(board)

        for action in actions:
            # Apply action
            new_board = apply_action(board, action)

            # Recurse
            damage = search(new_board, turn + 1, sequence + [action], depth - 1)

            # Update best
            if damage > max_damage:
                max_damage = damage
                best_sequence = sequence + [action]

        return max_damage

    search(sim_board, self.board.turn, [], num_turns)
    return best_sequence
```

**Benefits:**
- Optimal mana curve planning
- Better bomb timing (don't play big creature if board wipe likely)
- Maximize damage over multiple turns, not just this turn

### 4. Archetype Metadata Integration

**Current State:** Archetype detected from deck composition only
**Opportunity:** Use commander's archetype metadata

```python
# In CLAUDE.md, it mentions:
# "Synergy-aware AI: Check if commander has detailed archetype info"

# Currently implemented (boardstate.py:90-102):
if hasattr(commander, 'deck_archetype') and commander.deck_archetype:
    archetype_data = commander.deck_archetype
    self.archetype_priorities = archetype_data.get('priorities', {})
    self.primary_archetype = archetype_data.get('primary_archetype', None)
```

**Enhancement:**
```python
# Populate commander.deck_archetype from synergy engine
from src.analysis.deck_archetype_detector import detect_deck_archetype

# In deck loading
commander.deck_archetype = detect_deck_archetype(deck)
# Returns:
# {
#     'primary_archetype': 'Aristocrats',
#     'secondary_archetype': 'Tokens',
#     'priorities': {
#         'death_triggers': 850,
#         'sacrifice_outlets': 900,
#         'token_generators_aristocrats': 750,
#     },
#     'combo_pieces': ['Blood Artist', 'Zulaport Cutthroat', 'Ashnod\'s Altar'],
# }
```

**Benefits:**
- More accurate archetype detection
- Leverage existing synergy analysis
- Better integration between systems

### 5. Dynamic Probability Tuning

**Current State:** Hardcoded 70%/50%/30% probabilities
**Opportunity:** Learn from simulation results

```python
class AdaptiveAI(ImprovedAI):
    def __init__(self, board):
        super().__init__(board)
        self.ability_activation_prob = 0.7  # Initial
        self.instant_cast_prob = 0.5
        self.hold_back_prob = 0.3

        # Track outcomes
        self.ability_outcomes = []  # [(activated, damage_gained)]
        self.instant_outcomes = []
        self.hold_outcomes = []

    def optimize_mana_usage(self, verbose=False):
        # Adaptive probability based on past outcomes
        if len(self.ability_outcomes) > 10:
            # Calculate average benefit
            avg_benefit = sum(d for a, d in self.ability_outcomes if a) / len([a for a, d in self.ability_outcomes if a])

            # Adjust probability (higher benefit → higher probability)
            self.ability_activation_prob = min(1.0, avg_benefit / 10)

        # Use adaptive probability
        if random.random() < self.ability_activation_prob:
            # Activate ability
            damage_before = sum(self.board.combat_damage)
            self.activate_ability(...)
            damage_after = sum(self.board.combat_damage)

            # Record outcome
            self.ability_outcomes.append((True, damage_after - damage_before))
```

**Benefits:**
- Learn optimal decision thresholds per deck
- Adapt to deck-specific strategies
- Data-driven decision-making

### 6. Simulation Caching & Parallelization

**Current State:** Each simulation runs independently
**Opportunity:** Cache repeated states, parallelize sims

```python
import multiprocessing
from functools import lru_cache

@lru_cache(maxsize=10000)
def simulate_turn(board_state_hash, turn):
    """Cache results for identical board states."""
    # Simulate this specific turn
    # ...

def run_parallel_simulations(deck, commander, num_sims=1000):
    """Run simulations in parallel."""
    with multiprocessing.Pool(processes=8) as pool:
        results = pool.starmap(
            simulate_game,
            [(deck.copy(), commander, 10, False) for _ in range(num_sims)]
        )
    return aggregate_results(results)
```

**Benefits:**
- 5-10x faster simulation (important for dashboard)
- Utilize multi-core CPUs
- Enable larger sample sizes (10,000+ sims)

### 7. Advanced Metrics Integration

**Current State:** Metrics calculated but not used in all decisions
**Opportunity:** Integrate metrics into every decision point

```python
def prioritize_creature_for_casting(self, creature, verbose=False):
    score = 100

    # NEW: Integrate all 5 metric systems
    scarcity = self.detect_resource_scarcity()
    hand_stats = self.analyze_hand_resources()
    mana_eff = self.calculate_mana_efficiency()
    library_stats = self.get_library_stats()

    # Adjust based on scarcity
    if scarcity['critical_scarcity']:
        # Prioritize immediate threats when resources low
        if creature.has_haste:
            score += 200  # "We need damage NOW!"
    else:
        # Prioritize value engines when resources abundant
        if 'draw' in creature.oracle_text:
            score += 100  # "We can afford to build value"

    # Adjust based on hand diversity
    if hand_stats['diversity_score'] < 0.4:
        # Hand is monotonous, prioritize different card types
        if 'Creature' not in creature.type:
            score += 50  # Slight boost to non-creatures

    # Adjust based on mana efficiency
    if mana_eff['wasted_mana'] > 3:
        # We're wasting mana, play cheaper cards to maximize usage
        if creature.cmc <= 3:
            score += 75

    return score
```

**Benefits:**
- Holistic decision-making
- Context-aware priorities
- Maximally utilize all available information

---

## Conclusion

The simulation engine's AI decision-making system is a **sophisticated two-tier architecture** that combines:

1. **GreedyAI**: Fast, reliable rule-based decisions
2. **ImprovedAI**: Intelligent, metric-driven optimization

**Key Strengths:**
- Archetype-aware prioritization
- Real-time resource management
- Comprehensive creature scoring
- Goldfish-optimized for deck potential measurement

**Key Opportunities:**
- ML integration for learned priorities
- Combo recognition from synergy engine
- Multi-turn planning with game tree search
- Dynamic probability tuning
- Advanced metrics integration

**Overall Assessment:**
The AI is **well-designed for its purpose** (goldfish simulation). It successfully measures deck potential by:
- Playing cards in intelligent order
- Avoiding common pitfalls (mana waste, hand clogging)
- Adapting to deck archetype
- Maximizing damage output

The system would benefit most from:
1. **Combo recognition** (integrate synergy engine data)
2. **Multi-turn planning** (game tree search)
3. **ML integration** (learn from simulation results)

These improvements would make the AI even more accurate at measuring true deck potential, which is the core goal of the goldfish simulation.

---

**Files Referenced:**
- `Simulation/win_metrics.py` (928 lines) - ImprovedAI implementation
- `Simulation/boardstate.py` (6,375 lines) - BoardState and GreedyAI
- `Simulation/simulate_game.py` (914 lines) - Game loop integration

**Analysis Completed:** 2025-12-26
