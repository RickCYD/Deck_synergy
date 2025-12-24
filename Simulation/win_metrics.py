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
    """Statistical metrics for deck win potential."""
    # Turn-based win probabilities
    win_by_turn_6: float = 0.0
    win_by_turn_8: float = 0.0
    win_by_turn_10: float = 0.0

    # Confidence intervals (95%)
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

    for sim in range(num_simulations):
        # Run simulation
        game_metrics = simulate_game(
            deck_cards.copy(),
            commander_card,
            max_turns=max_turns,
            verbose=False
        )

        # Calculate cumulative damage per turn
        cumulative = 0
        game_damage = []
        game_won = False  # Track if THIS simulation has won

        for turn in range(1, max_turns + 1):
            combat = game_metrics.get('combat_damage', [0] * (max_turns + 1))[turn]
            drain = game_metrics.get('drain_damage', [0] * (max_turns + 1))[turn]
            turn_damage = combat + drain
            cumulative += turn_damage
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

                # Track win type based on damage sources
                if drain > combat * 0.5:
                    metrics.drain_damage_wins += 1
                else:
                    metrics.combat_damage_wins += 1

        metrics.damage_per_turn_samples.append(game_damage)

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

    # Calculate average damage per turn
    for turn in range(1, max_turns + 1):
        if per_turn_damage[turn]:
            metrics.avg_damage_per_turn.append(statistics.mean(per_turn_damage[turn]))
        if damage_by_turn[turn]:
            metrics.cumulative_damage_by_turn.append(statistics.mean(damage_by_turn[turn]))

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
    }
