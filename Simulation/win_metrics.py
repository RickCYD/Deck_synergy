"""
Win Metrics Module for MTG Goldfish Simulation

This module provides:
1. Win condition detection for goldfish simulation
2. Statistical analysis with 95% confidence intervals
3. Turn-by-turn win probability metrics
4. Improved AI decision-making for optimal play sequencing

Goldfish metrics focus on:
- How fast can the deck win (uncontested)?
- What is the probability of winning by turn X?
- What is the average damage output per turn?
"""

from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from boardstate import BoardState
    from simulate_game import Card


# =============================================================================
# WIN CONDITION CONSTANTS
# =============================================================================

# Commander damage threshold (one opponent)
COMMANDER_DAMAGE_KILL = 21

# Starting life total for Commander
STARTING_LIFE = 40

# Mill win (cards in library to deck opponent)
MILL_THRESHOLD = 99  # Typical Commander deck

# Poison counters for win
POISON_THRESHOLD = 10


# =============================================================================
# DATA CLASSES FOR METRICS
# =============================================================================

@dataclass
class WinMetrics:
    """Statistical metrics for deck win potential.

    Note: All win probabilities are CUMULATIVE. For example:
    - win_by_turn_6 = Probability of winning ON OR BEFORE turn 6
    - win_by_turn_8 = Probability of winning ON OR BEFORE turn 8
    This means win_by_turn_8 >= win_by_turn_6 always.
    """
    # Turn-based win probabilities (CUMULATIVE)
    win_by_turn_6: float = 0.0
    win_by_turn_8: float = 0.0
    win_by_turn_10: float = 0.0

    # Confidence intervals (95%) for cumulative probabilities
    win_by_turn_6_ci: Tuple[float, float] = (0.0, 0.0)
    win_by_turn_8_ci: Tuple[float, float] = (0.0, 0.0)
    win_by_turn_10_ci: Tuple[float, float] = (0.0, 0.0)

    # Average metrics
    avg_win_turn: float = 0.0
    avg_win_turn_ci: Tuple[float, float] = (0.0, 0.0)

    # Damage output
    avg_damage_per_turn: List[float] = field(default_factory=list)
    cumulative_damage_by_turn: List[float] = field(default_factory=list)

    # Win condition breakdown
    combat_damage_wins: int = 0
    commander_damage_wins: int = 0
    drain_damage_wins: int = 0
    combo_wins: int = 0
    total_wins: int = 0
    total_games: int = 0

    # Sample data for statistical analysis
    win_turns: List[int] = field(default_factory=list)
    damage_per_turn_samples: List[List[int]] = field(default_factory=list)

    # =========================================================================
    # HAND AND CARD DRAW METRICS
    # =========================================================================

    # Hand size metrics (average cards in hand per turn)
    avg_hand_size_by_turn: List[float] = field(default_factory=list)
    avg_hand_size_overall: float = 0.0
    avg_hand_size_ci: Tuple[float, float] = (0.0, 0.0)

    # Maximum hand size reached across all games
    max_hand_size: int = 0
    avg_max_hand_size: float = 0.0

    # Minimum hand size (detecting topdeck mode)
    min_hand_size: int = 0
    empty_hand_turns: int = 0  # Total turns spent with 0 cards in hand
    avg_empty_hand_turns_per_game: float = 0.0

    # Card draw metrics
    total_cards_drawn: int = 0  # Total cards drawn across all games
    avg_cards_drawn_per_game: float = 0.0
    avg_cards_drawn_per_turn: List[float] = field(default_factory=list)

    # Starting hand metrics
    avg_starting_hand_size: float = 7.0  # Usually 7, but accounts for mulligans
    avg_starting_hand_quality: float = 0.0
    mulligan_count: int = 0
    mulligan_rate: float = 0.0  # Percentage of games that mulligan

    # Hand size when winning
    avg_hand_size_on_win: float = 0.0
    hand_sizes_on_win: List[int] = field(default_factory=list)

    # Cards played per turn
    avg_cards_played_per_turn: List[float] = field(default_factory=list)
    total_cards_played: int = 0

    # Card velocity (cards drawn - cards played = hand accumulation/depletion)
    avg_card_velocity_by_turn: List[float] = field(default_factory=list)  # Positive = gaining cards, negative = losing cards

    # Hand samples for statistical analysis
    hand_size_samples: List[List[int]] = field(default_factory=list)  # Hand size per turn per game
    cards_drawn_samples: List[List[int]] = field(default_factory=list)  # Cards drawn per turn per game


@dataclass
class TurnMetrics:
    """Metrics tracked per turn for win condition analysis."""
    turn: int = 0
    combat_damage: int = 0
    drain_damage: int = 0
    commander_damage: int = 0
    total_damage: int = 0
    cumulative_damage: int = 0
    board_power: int = 0
    cards_drawn: int = 0
    mana_available: int = 0
    creatures_count: int = 0

    # Hand and card draw metrics
    hand_size: int = 0  # Cards in hand at end of turn
    cards_drawn_this_turn: int = 0  # Cards drawn this specific turn
    cards_played_this_turn: int = 0  # Cards played/cast this turn
    hand_quality_score: float = 0.0  # Quality score of current hand


# =============================================================================
# STATISTICAL FUNCTIONS
# =============================================================================

def calculate_confidence_interval(data: List[float], confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate confidence interval for a list of values.

    Uses t-distribution for small samples, normal approximation for large samples.

    Args:
        data: List of sample values
        confidence: Confidence level (default 0.95 for 95% CI)

    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if not data or len(data) < 2:
        return (0.0, 0.0)

    n = len(data)
    mean = statistics.mean(data)
    stdev = statistics.stdev(data)

    # Standard error
    se = stdev / math.sqrt(n)

    # Z-score for 95% confidence
    z = 1.96 if n >= 30 else _t_score(n - 1, confidence)

    margin = z * se
    return (mean - margin, mean + margin)


def _t_score(df: int, confidence: float) -> float:
    """
    Approximate t-score for given degrees of freedom and confidence level.

    This is a simplified approximation. For production, use scipy.stats.t.ppf
    """
    # Simplified t-distribution approximation for common cases
    t_table = {
        1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57,
        6: 2.45, 7: 2.36, 8: 2.31, 9: 2.26, 10: 2.23,
        15: 2.13, 20: 2.09, 25: 2.06, 30: 2.04
    }

    # Find closest match
    closest = min(t_table.keys(), key=lambda k: abs(k - df))
    return t_table.get(closest, 1.96)


def calculate_win_probability(wins: int, total: int) -> float:
    """Calculate win probability with Wilson score interval."""
    if total == 0:
        return 0.0
    return wins / total


def wilson_confidence_interval(wins: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate Wilson score confidence interval for proportions.

    This is more accurate than normal approximation for proportions,
    especially for extreme values (near 0 or 1).
    """
    if total == 0:
        return (0.0, 0.0)

    z = 1.96  # 95% confidence
    p = wins / total
    n = total

    denominator = 1 + z * z / n

    center = (p + z * z / (2 * n)) / denominator
    offset = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denominator

    lower = max(0.0, center - offset)
    upper = min(1.0, center + offset)

    return (lower, upper)


# =============================================================================
# WIN CONDITION DETECTION
# =============================================================================

def check_goldfish_win(board: 'BoardState', cumulative_damage: int,
                       cumulative_commander_damage: int = 0,
                       cumulative_drain: int = 0) -> Dict[str, Any]:
    """
    Check if the deck has achieved a goldfish win condition.

    Win conditions in goldfish:
    1. Total damage >= 120 (3 opponents × 40 life)
    2. Commander damage >= 21 to any single opponent
    3. Combo win (infinite damage, infinite tokens, etc.)

    Args:
        board: Current board state
        cumulative_damage: Total combat + drain damage dealt
        cumulative_commander_damage: Commander damage to highest target
        cumulative_drain: Non-combat damage dealt

    Returns:
        Dict with:
            - won: bool
            - win_type: str ('combat', 'commander', 'drain', 'combo', None)
            - turn: int (turn won, or None)
    """
    # Total damage needed to kill 3 opponents in goldfish
    TOTAL_DAMAGE_NEEDED = 120  # 3 × 40 life

    result = {
        'won': False,
        'win_type': None,
        'turn': None,
        'damage_dealt': cumulative_damage,
    }

    # Check commander damage win (21+ to one opponent)
    if cumulative_commander_damage >= COMMANDER_DAMAGE_KILL:
        result['won'] = True
        result['win_type'] = 'commander'
        result['turn'] = board.turn
        return result

    # Check total damage win
    if cumulative_damage >= TOTAL_DAMAGE_NEEDED:
        # Determine primary damage source
        if cumulative_drain > cumulative_damage * 0.5:
            result['win_type'] = 'drain'
        else:
            result['win_type'] = 'combat'
        result['won'] = True
        result['turn'] = board.turn
        return result

    # Check for combo indicators
    combo_indicators = detect_combo_win(board)
    if combo_indicators['is_combo']:
        result['won'] = True
        result['win_type'] = 'combo'
        result['turn'] = board.turn
        return result

    return result


def detect_combo_win(board: 'BoardState') -> Dict[str, Any]:
    """
    Detect if a combo has been assembled that wins the game.

    Looks for:
    - Infinite damage indicators (very high drain in one turn)
    - Infinite token indicators (token count explosion)
    - Infinite mana + win condition
    """
    result = {
        'is_combo': False,
        'combo_type': None,
    }

    # Check for infinite damage indicator (100+ damage in one turn)
    drain_this_turn = getattr(board, 'drain_damage_this_turn', 0)
    if drain_this_turn >= 100:
        result['is_combo'] = True
        result['combo_type'] = 'infinite_damage'
        return result

    # Check for token explosion (50+ tokens created in one turn)
    tokens_this_turn = getattr(board, 'tokens_created_this_turn', 0)
    if tokens_this_turn >= 50:
        result['is_combo'] = True
        result['combo_type'] = 'infinite_tokens'
        return result

    # Check for persist/undying loops (5+ triggers in one turn)
    persist_triggers = getattr(board, 'persist_triggers', 0)
    undying_triggers = getattr(board, 'undying_triggers', 0)
    if persist_triggers + undying_triggers >= 5:
        result['is_combo'] = True
        result['combo_type'] = 'aristocrat_loop'
        return result

    return result


# =============================================================================
# IMPROVED AI DECISION MAKING
# =============================================================================

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

    def _determine_game_plan(self) -> str:
        """
        Analyze deck to determine optimal game plan.

        Returns one of: 'aggro', 'combo', 'midrange', 'voltron'
        """
        archetype = getattr(self.board, 'deck_archetype', 'unknown')

        # Map detected archetype to game plan
        plan_map = {
            'voltron': 'voltron',
            'aggro': 'aggro',
            'go_wide': 'aggro',
            'combo_control': 'combo',
            'midrange': 'midrange',
        }

        return plan_map.get(archetype, 'midrange')

    def evaluate_card_priority(self, card: 'Card') -> float:
        """
        Evaluate card priority for casting order.

        Higher score = cast sooner.

        Args:
            card: Card to evaluate

        Returns:
            Priority score (0-100)
        """
        score = 0.0
        oracle = getattr(card, 'oracle_text', '').lower()
        card_type = getattr(card, 'type', '')

        # Base scores by type
        if 'creature' in card_type.lower():
            power = getattr(card, 'power', 0) or 0
            toughness = getattr(card, 'toughness', 0) or 0
            score += power * 5 + toughness * 2

            # Haste bonus (immediate damage)
            if getattr(card, 'has_haste', False) or 'haste' in oracle:
                score += 15

            # Evasion bonus
            if getattr(card, 'has_flying', False) or 'flying' in oracle:
                score += 8
            if 'unblockable' in oracle or "can't be blocked" in oracle:
                score += 12
            if getattr(card, 'has_trample', False) or 'trample' in oracle:
                score += 5

        # Mana production priority (especially early game)
        mana_prod = getattr(card, 'mana_production', 0) or 0
        if mana_prod > 0:
            # Higher priority early, lower late
            turn_factor = max(1, 6 - self.board.turn)
            score += mana_prod * 10 * turn_factor

        # Card draw
        draw = getattr(card, 'draw_cards', 0) or 0
        if draw > 0:
            score += draw * 8

        # Direct damage
        damage = getattr(card, 'deals_damage', 0) or 0
        if damage > 0:
            score += damage * 3

        # ETB effects (flicker value)
        if 'when' in oracle and 'enters' in oracle:
            score += 10

        # Cascade (free spells)
        if 'cascade' in oracle:
            score += 20

        # Combo pieces
        if 'infinite' in oracle or 'combo' in str(getattr(card, 'tags', [])):
            score += 25

        # Game plan specific bonuses
        if self.game_plan == 'voltron':
            if 'equipment' in card_type.lower():
                score += 15
            if getattr(card, 'is_commander', False):
                score += 30

        elif self.game_plan == 'aggro':
            if 'creature' in card_type.lower():
                score += 10

        elif self.game_plan == 'combo':
            if 'tutor' in oracle or 'search' in oracle:
                score += 20

        return score

    def get_optimal_play_sequence(self, castable_cards: List['Card']) -> List['Card']:
        """
        Determine optimal order to cast available cards.

        Args:
            castable_cards: List of cards that can be cast this turn

        Returns:
            Ordered list of cards (cast first to last)
        """
        if not castable_cards:
            return []

        # Score all cards
        scored = [(self.evaluate_card_priority(c), c) for c in castable_cards]

        # Sort by priority (highest first)
        scored.sort(reverse=True, key=lambda x: x[0])

        # Special rule: Always cast mana producers before expensive spells
        mana_producers = []
        other_cards = []

        for score, card in scored:
            mana_prod = getattr(card, 'mana_production', 0) or 0
            if mana_prod > 0:
                mana_producers.append(card)
            else:
                other_cards.append(card)

        # Mana producers first, then by priority
        return mana_producers + other_cards

    def should_hold_card(self, card: 'Card') -> bool:
        """
        Determine if we should hold a card for later.

        In goldfish, we almost never hold cards - maximize damage.

        Args:
            card: Card to evaluate

        Returns:
            True if card should be held
        """
        # In goldfish, very rarely hold cards
        # Only hold if we're about to win anyway

        # Check if we're close to winning
        cumulative_damage = sum(
            getattr(self.board, f'combat_damage_turn_{t}', 0)
            for t in range(1, self.board.turn + 1)
        )

        # If we're about to win, hold expensive cards
        if cumulative_damage >= 100:
            cmc = self._get_cmc(card)
            if cmc >= 6:
                return True

        return False

    def _get_cmc(self, card: 'Card') -> int:
        """Get converted mana cost of a card."""
        from convert_dataframe_deck import parse_mana_cost
        return parse_mana_cost(getattr(card, 'mana_cost', ''))


# =============================================================================
# SIMULATION METRICS COLLECTION
# =============================================================================

def run_goldfish_simulation_with_metrics(
    deck_cards: List['Card'],
    commander_card: 'Card',
    num_simulations: int = 100,
    max_turns: int = 10,
    verbose: bool = False
) -> WinMetrics:
    """
    Run multiple goldfish simulations and collect statistical metrics.

    Args:
        deck_cards: List of cards in deck
        commander_card: Commander card
        num_simulations: Number of games to simulate
        max_turns: Maximum turns per game
        verbose: Print detailed output

    Returns:
        WinMetrics with statistical analysis
    """
    from simulate_game import simulate_game

    metrics = WinMetrics()
    metrics.total_games = num_simulations

    # Track wins by turn
    wins_by_turn = {t: 0 for t in range(1, max_turns + 1)}
    damage_by_turn = {t: [] for t in range(1, max_turns + 1)}  # Cumulative damage
    per_turn_damage = {t: [] for t in range(1, max_turns + 1)}  # Per-turn damage

    # Track hand and card draw metrics across all simulations
    hand_size_by_turn = {t: [] for t in range(1, max_turns + 1)}
    cards_drawn_by_turn = {t: [] for t in range(1, max_turns + 1)}
    cards_played_by_turn = {t: [] for t in range(1, max_turns + 1)}
    starting_hand_sizes = []
    max_hand_sizes = []
    empty_hand_turn_counts = []

    for sim in range(num_simulations):
        # Run simulation
        game_metrics = simulate_game(
            deck_cards.copy(),
            commander_card,
            max_turns=max_turns,
            verbose=False
        )

        # CRITICAL FIX: Validate game_metrics structure before use
        if not game_metrics or not isinstance(game_metrics, dict):
            if verbose:
                print(f"Warning: Simulation {sim} returned invalid metrics, skipping")
            continue

        # Get damage arrays with validation
        combat_damage_array = game_metrics.get('combat_damage', [])
        drain_damage_array = game_metrics.get('drain_damage', [])

        # Get hand and draw metrics from game_metrics
        hand_size_array = game_metrics.get('hand_size', [])
        cards_drawn_array = game_metrics.get('cards_drawn', [])
        cards_played_array = game_metrics.get('cards_played', [])

        # Ensure arrays are properly sized
        if len(combat_damage_array) < max_turns + 1:
            combat_damage_array = combat_damage_array + [0] * (max_turns + 1 - len(combat_damage_array))
        if len(drain_damage_array) < max_turns + 1:
            drain_damage_array = drain_damage_array + [0] * (max_turns + 1 - len(drain_damage_array))
        if len(hand_size_array) < max_turns + 1:
            hand_size_array = hand_size_array + [0] * (max_turns + 1 - len(hand_size_array))
        if len(cards_drawn_array) < max_turns + 1:
            cards_drawn_array = cards_drawn_array + [0] * (max_turns + 1 - len(cards_drawn_array))
        if len(cards_played_array) < max_turns + 1:
            cards_played_array = cards_played_array + [0] * (max_turns + 1 - len(cards_played_array))

        # Calculate cumulative damage per turn
        cumulative = 0
        cumulative_combat = 0  # Track cumulative combat damage
        cumulative_drain = 0   # Track cumulative drain damage
        game_damage = []
        game_won = False  # Track if THIS simulation has won

        for turn in range(1, max_turns + 1):
            combat = combat_damage_array[turn]
            drain = drain_damage_array[turn]
            turn_damage = combat + drain
            cumulative += turn_damage
            cumulative_combat += combat
            cumulative_drain += drain
            game_damage.append(turn_damage)
            damage_by_turn[turn].append(cumulative)
            per_turn_damage[turn].append(turn_damage)

            # Check win condition - only record first win turn for this simulation
            if cumulative >= 120 and not game_won:
                game_won = True
                # Increment wins for this turn and all later turns
                for t in range(turn, max_turns + 1):
                    wins_by_turn[t] += 1
                metrics.win_turns.append(turn)
                metrics.total_wins += 1

                # CRITICAL FIX: Track win type based on CUMULATIVE damage sources
                # Compare total drain damage to total combat damage across all turns
                if cumulative_drain > cumulative_combat * 0.5:
                    metrics.drain_damage_wins += 1
                else:
                    metrics.combat_damage_wins += 1

        metrics.damage_per_turn_samples.append(game_damage)

        # =====================================================================
        # HAND AND CARD DRAW METRICS TRACKING
        # =====================================================================

        # Track hand size and draw metrics for this game
        game_hand_sizes = []
        game_cards_drawn = []
        game_cards_played = []
        game_empty_hand_turns = 0
        game_max_hand_size = 0

        # Starting hand (turn 0 or 1)
        starting_hand = hand_size_array[0] if len(hand_size_array) > 0 and hand_size_array[0] > 0 else hand_size_array[1] if len(hand_size_array) > 1 else 7
        starting_hand_sizes.append(starting_hand)

        for turn in range(1, max_turns + 1):
            hand_size = hand_size_array[turn] if turn < len(hand_size_array) else 0
            cards_drawn = cards_drawn_array[turn] if turn < len(cards_drawn_array) else 0
            cards_played = cards_played_array[turn] if turn < len(cards_played_array) else 0

            # Record for this turn across all games
            hand_size_by_turn[turn].append(hand_size)
            cards_drawn_by_turn[turn].append(cards_drawn)
            cards_played_by_turn[turn].append(cards_played)

            # Record for this specific game
            game_hand_sizes.append(hand_size)
            game_cards_drawn.append(cards_drawn)
            game_cards_played.append(cards_played)

            # Track empty hand turns
            if hand_size == 0:
                game_empty_hand_turns += 1

            # Track max hand size
            game_max_hand_size = max(game_max_hand_size, hand_size)

        # Store game-level hand metrics
        metrics.hand_size_samples.append(game_hand_sizes)
        metrics.cards_drawn_samples.append(game_cards_drawn)
        empty_hand_turn_counts.append(game_empty_hand_turns)
        max_hand_sizes.append(game_max_hand_size)

        # Track hand size when winning
        if game_won and len(game_hand_sizes) > 0:
            # Get hand size at the turn they won
            win_turn_idx = metrics.win_turns[-1] - 1  # Convert to 0-indexed
            if win_turn_idx < len(game_hand_sizes):
                metrics.hand_sizes_on_win.append(game_hand_sizes[win_turn_idx])

        # Track total cards drawn and played
        metrics.total_cards_drawn += sum(game_cards_drawn)
        metrics.total_cards_played += sum(game_cards_played)

    # Calculate statistics
    metrics.win_by_turn_6 = wins_by_turn.get(6, 0) / num_simulations if num_simulations > 0 else 0
    metrics.win_by_turn_8 = wins_by_turn.get(8, 0) / num_simulations if num_simulations > 0 else 0
    metrics.win_by_turn_10 = wins_by_turn.get(10, 0) / num_simulations if num_simulations > 0 else 0

    # Calculate confidence intervals for win probabilities
    metrics.win_by_turn_6_ci = wilson_confidence_interval(wins_by_turn.get(6, 0), num_simulations)
    metrics.win_by_turn_8_ci = wilson_confidence_interval(wins_by_turn.get(8, 0), num_simulations)
    metrics.win_by_turn_10_ci = wilson_confidence_interval(wins_by_turn.get(10, 0), num_simulations)

    # Calculate average win turn
    if metrics.win_turns:
        metrics.avg_win_turn = statistics.mean(metrics.win_turns)
        metrics.avg_win_turn_ci = calculate_confidence_interval(metrics.win_turns)
    else:
        metrics.avg_win_turn = float('inf')
        metrics.avg_win_turn_ci = (float('inf'), float('inf'))

    # CRITICAL FIX: Calculate average damage per turn
    # Always append values to maintain index alignment (turn 1 = index 0, etc.)
    for turn in range(1, max_turns + 1):
        if per_turn_damage[turn]:
            metrics.avg_damage_per_turn.append(statistics.mean(per_turn_damage[turn]))
        else:
            metrics.avg_damage_per_turn.append(0.0)

        if damage_by_turn[turn]:
            metrics.cumulative_damage_by_turn.append(statistics.mean(damage_by_turn[turn]))
        else:
            metrics.cumulative_damage_by_turn.append(0.0)

    # =========================================================================
    # CALCULATE HAND AND CARD DRAW STATISTICS
    # =========================================================================

    # Average hand size per turn
    for turn in range(1, max_turns + 1):
        if hand_size_by_turn[turn]:
            metrics.avg_hand_size_by_turn.append(statistics.mean(hand_size_by_turn[turn]))
        else:
            metrics.avg_hand_size_by_turn.append(0.0)

    # Overall average hand size (across all turns and games)
    all_hand_sizes = [hs for game_hands in metrics.hand_size_samples for hs in game_hands]
    if all_hand_sizes:
        metrics.avg_hand_size_overall = statistics.mean(all_hand_sizes)
        metrics.avg_hand_size_ci = calculate_confidence_interval(all_hand_sizes)
    else:
        metrics.avg_hand_size_overall = 0.0
        metrics.avg_hand_size_ci = (0.0, 0.0)

    # Average cards drawn per turn
    for turn in range(1, max_turns + 1):
        if cards_drawn_by_turn[turn]:
            metrics.avg_cards_drawn_per_turn.append(statistics.mean(cards_drawn_by_turn[turn]))
        else:
            metrics.avg_cards_drawn_per_turn.append(0.0)

    # Average cards played per turn
    for turn in range(1, max_turns + 1):
        if cards_played_by_turn[turn]:
            metrics.avg_cards_played_per_turn.append(statistics.mean(cards_played_by_turn[turn]))
        else:
            metrics.avg_cards_played_per_turn.append(0.0)

    # Card velocity per turn (drawn - played)
    for turn in range(1, max_turns + 1):
        if cards_drawn_by_turn[turn] and cards_played_by_turn[turn]:
            avg_drawn = statistics.mean(cards_drawn_by_turn[turn])
            avg_played = statistics.mean(cards_played_by_turn[turn])
            metrics.avg_card_velocity_by_turn.append(avg_drawn - avg_played)
        else:
            metrics.avg_card_velocity_by_turn.append(0.0)

    # Starting hand metrics
    if starting_hand_sizes:
        metrics.avg_starting_hand_size = statistics.mean(starting_hand_sizes)
        # Mulligan detection: if average starting hand < 7, some mulligans occurred
        metrics.mulligan_rate = sum(1 for h in starting_hand_sizes if h < 7) / len(starting_hand_sizes) if starting_hand_sizes else 0.0
        metrics.mulligan_count = sum(1 for h in starting_hand_sizes if h < 7)

    # Maximum hand size metrics
    if max_hand_sizes:
        metrics.max_hand_size = max(max_hand_sizes)
        metrics.avg_max_hand_size = statistics.mean(max_hand_sizes)

    # Minimum hand size (always 0 when running out of cards)
    metrics.min_hand_size = 0

    # Empty hand turns
    if empty_hand_turn_counts:
        metrics.empty_hand_turns = sum(empty_hand_turn_counts)
        metrics.avg_empty_hand_turns_per_game = statistics.mean(empty_hand_turn_counts)

    # Average cards drawn/played per game
    if num_simulations > 0:
        metrics.avg_cards_drawn_per_game = metrics.total_cards_drawn / num_simulations
        # Note: total_cards_played is already accumulated above

    # Average hand size when winning
    if metrics.hand_sizes_on_win:
        metrics.avg_hand_size_on_win = statistics.mean(metrics.hand_sizes_on_win)

    return metrics


def format_win_metrics_report(metrics: WinMetrics) -> str:
    """
    Format win metrics as a human-readable report.

    Args:
        metrics: WinMetrics data

    Returns:
        Formatted string report
    """
    lines = [
        "=" * 60,
        "GOLDFISH SIMULATION RESULTS",
        "=" * 60,
        "",
        f"Total Simulations: {metrics.total_games}",
        f"Total Wins: {metrics.total_wins}",
        "",
        "WIN PROBABILITY BY TURN (95% CI)",
        "-" * 40,
        f"  Turn 6:  {metrics.win_by_turn_6 * 100:5.1f}%  ({metrics.win_by_turn_6_ci[0] * 100:5.1f}% - {metrics.win_by_turn_6_ci[1] * 100:5.1f}%)",
        f"  Turn 8:  {metrics.win_by_turn_8 * 100:5.1f}%  ({metrics.win_by_turn_8_ci[0] * 100:5.1f}% - {metrics.win_by_turn_8_ci[1] * 100:5.1f}%)",
        f"  Turn 10: {metrics.win_by_turn_10 * 100:5.1f}%  ({metrics.win_by_turn_10_ci[0] * 100:5.1f}% - {metrics.win_by_turn_10_ci[1] * 100:5.1f}%)",
        "",
        "AVERAGE WIN TURN",
        "-" * 40,
    ]

    if metrics.avg_win_turn != float('inf'):
        lines.append(f"  Mean: Turn {metrics.avg_win_turn:.1f}  ({metrics.avg_win_turn_ci[0]:.1f} - {metrics.avg_win_turn_ci[1]:.1f})")
    else:
        lines.append("  Mean: Did not win within max turns")

    lines.extend([
        "",
        "WIN CONDITION BREAKDOWN",
        "-" * 40,
        f"  Combat Damage: {metrics.combat_damage_wins}",
        f"  Drain Damage:  {metrics.drain_damage_wins}",
        f"  Commander:     {metrics.commander_damage_wins}",
        f"  Combo:         {metrics.combo_wins}",
        "",
        "CUMULATIVE DAMAGE BY TURN",
        "-" * 40,
    ])

    for i, dmg in enumerate(metrics.cumulative_damage_by_turn[:10], 1):
        bar = "█" * int(dmg / 10)
        lines.append(f"  Turn {i:2d}: {dmg:6.1f} {bar}")

    # Add hand and card draw metrics section
    lines.extend([
        "",
        "HAND SIZE AND CARD DRAW METRICS",
        "-" * 40,
        f"  Average Hand Size:     {metrics.avg_hand_size_overall:.1f} cards ({metrics.avg_hand_size_ci[0]:.1f} - {metrics.avg_hand_size_ci[1]:.1f})",
        f"  Average Starting Hand: {metrics.avg_starting_hand_size:.1f} cards",
        f"  Mulligan Rate:         {metrics.mulligan_rate * 100:.1f}%",
        "",
        f"  Max Hand Size Reached: {metrics.max_hand_size} cards",
        f"  Avg Max Hand Size:     {metrics.avg_max_hand_size:.1f} cards",
        f"  Empty Hand Turns/Game: {metrics.avg_empty_hand_turns_per_game:.1f}",
        "",
        f"  Total Cards Drawn:     {metrics.total_cards_drawn}",
        f"  Avg Cards/Game:        {metrics.avg_cards_drawn_per_game:.1f}",
        f"  Avg Hand Size on Win:  {metrics.avg_hand_size_on_win:.1f} cards" if metrics.avg_hand_size_on_win > 0 else "  Avg Hand Size on Win:  N/A",
        "",
        "AVERAGE HAND SIZE BY TURN",
        "-" * 40,
    ])

    for i, hand_size in enumerate(metrics.avg_hand_size_by_turn[:10], 1):
        bar = "■" * int(hand_size)
        lines.append(f"  Turn {i:2d}: {hand_size:4.1f} {bar}")

    lines.extend([
        "",
        "CARD VELOCITY BY TURN (Drawn - Played)",
        "-" * 40,
    ])

    for i, velocity in enumerate(metrics.avg_card_velocity_by_turn[:10], 1):
        indicator = "+" if velocity >= 0 else ""
        bar = "▲" * int(abs(velocity)) if velocity >= 0 else "▼" * int(abs(velocity))
        lines.append(f"  Turn {i:2d}: {indicator}{velocity:+4.1f} {bar}")

    lines.append("=" * 60)

    return "\n".join(lines)


# =============================================================================
# DASHBOARD INTEGRATION
# =============================================================================

def get_dashboard_metrics(metrics: WinMetrics) -> Dict[str, Any]:
    """
    Convert WinMetrics to dashboard-friendly format.

    Returns dict suitable for Dash/Plotly visualization.
    """
    return {
        # Win probabilities
        'win_probability_turn_6': metrics.win_by_turn_6,
        'win_probability_turn_8': metrics.win_by_turn_8,
        'win_probability_turn_10': metrics.win_by_turn_10,

        # Confidence intervals
        'win_ci_turn_6': {
            'lower': metrics.win_by_turn_6_ci[0],
            'upper': metrics.win_by_turn_6_ci[1],
        },
        'win_ci_turn_8': {
            'lower': metrics.win_by_turn_8_ci[0],
            'upper': metrics.win_by_turn_8_ci[1],
        },
        'win_ci_turn_10': {
            'lower': metrics.win_by_turn_10_ci[0],
            'upper': metrics.win_by_turn_10_ci[1],
        },

        # Average win turn
        'avg_win_turn': metrics.avg_win_turn if metrics.avg_win_turn != float('inf') else None,
        'avg_win_turn_ci': {
            'lower': metrics.avg_win_turn_ci[0] if metrics.avg_win_turn_ci[0] != float('inf') else None,
            'upper': metrics.avg_win_turn_ci[1] if metrics.avg_win_turn_ci[1] != float('inf') else None,
        },

        # Win type breakdown
        'win_breakdown': {
            'combat': metrics.combat_damage_wins,
            'drain': metrics.drain_damage_wins,
            'commander': metrics.commander_damage_wins,
            'combo': metrics.combo_wins,
        },

        # Damage progression
        'damage_by_turn': metrics.cumulative_damage_by_turn,

        # Summary stats
        'total_games': metrics.total_games,
        'total_wins': metrics.total_wins,
        'win_rate': metrics.total_wins / metrics.total_games if metrics.total_games > 0 else 0,

        # =====================================================================
        # HAND AND CARD DRAW METRICS
        # =====================================================================

        # Hand size metrics
        'avg_hand_size_by_turn': metrics.avg_hand_size_by_turn,
        'avg_hand_size_overall': metrics.avg_hand_size_overall,
        'avg_hand_size_ci': {
            'lower': metrics.avg_hand_size_ci[0],
            'upper': metrics.avg_hand_size_ci[1],
        },
        'max_hand_size': metrics.max_hand_size,
        'avg_max_hand_size': metrics.avg_max_hand_size,
        'min_hand_size': metrics.min_hand_size,

        # Empty hand tracking (topdeck mode)
        'empty_hand_turns': metrics.empty_hand_turns,
        'avg_empty_hand_turns_per_game': metrics.avg_empty_hand_turns_per_game,

        # Card draw metrics
        'total_cards_drawn': metrics.total_cards_drawn,
        'avg_cards_drawn_per_game': metrics.avg_cards_drawn_per_game,
        'avg_cards_drawn_per_turn': metrics.avg_cards_drawn_per_turn,

        # Starting hand
        'avg_starting_hand_size': metrics.avg_starting_hand_size,
        'avg_starting_hand_quality': metrics.avg_starting_hand_quality,
        'mulligan_count': metrics.mulligan_count,
        'mulligan_rate': metrics.mulligan_rate,

        # Hand when winning
        'avg_hand_size_on_win': metrics.avg_hand_size_on_win,

        # Cards played
        'avg_cards_played_per_turn': metrics.avg_cards_played_per_turn,
        'total_cards_played': metrics.total_cards_played,

        # Card velocity (draw rate - play rate)
        'avg_card_velocity_by_turn': metrics.avg_card_velocity_by_turn,
    }
