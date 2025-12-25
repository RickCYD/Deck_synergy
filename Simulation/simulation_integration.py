"""
Simulation Integration Module

This module integrates all extended mechanics and win metrics into a unified
interface for the dashboard and deck analysis.

Provides:
1. Enhanced simulation with extended mechanics
2. Statistical win probability analysis
3. Dashboard-ready metrics
4. Deck effectiveness scoring
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

# Import extended mechanics
from extended_mechanics import (
    initialize_extended_metrics,
    get_extended_metrics,
    detect_flicker_ability,
    detect_copy_ability,
    detect_modal_spell,
    detect_cascade,
    detect_suspend,
    detect_persist,
    detect_undying,
    detect_convoke,
    detect_delve,
    detect_flash,
    detect_flashback,
    detect_buyback,
    detect_retrace,
    flicker_permanent,
    resolve_cascade,
    process_suspended_cards,
    handle_creature_death_persist_undying,
    apply_convoke,
    apply_delve,
    cast_flashback,
    cast_with_buyback,
    process_end_of_turn_flicker_returns,
)

# Import win metrics
from win_metrics import (
    WinMetrics,
    ImprovedAI,
    run_goldfish_simulation_with_metrics,
    format_win_metrics_report,
    get_dashboard_metrics,
    calculate_confidence_interval,
    wilson_confidence_interval,
)

if TYPE_CHECKING:
    from boardstate import BoardState
    from simulate_game import Card


# =============================================================================
# DECK EFFECTIVENESS SCORE
# =============================================================================

@dataclass
class DeckEffectivenessScore:
    """
    Comprehensive deck effectiveness score for goldfish simulation.

    Combines multiple metrics into a single effectiveness rating.
    """
    # Overall score (0-100)
    overall_score: float = 0.0

    # Component scores (0-100 each)
    speed_score: float = 0.0  # How fast can the deck win?
    consistency_score: float = 0.0  # How consistent is the win speed?
    power_score: float = 0.0  # How much damage output?
    synergy_score: float = 0.0  # How well do mechanics interact?

    # Raw metrics
    avg_win_turn: float = 0.0
    win_rate: float = 0.0
    avg_damage_turn_6: float = 0.0
    avg_damage_turn_10: float = 0.0

    # Extended mechanics usage
    mechanics_used: Dict[str, int] = field(default_factory=dict)

    # Confidence
    confidence_level: float = 0.95


def calculate_deck_effectiveness(metrics: WinMetrics,
                                 extended_metrics: Dict[str, int]) -> DeckEffectivenessScore:
    """
    Calculate comprehensive deck effectiveness score.

    Args:
        metrics: Win metrics from simulation
        extended_metrics: Extended mechanics usage counts

    Returns:
        DeckEffectivenessScore with all components
    """
    score = DeckEffectivenessScore()

    # Speed score: Based on average win turn
    # Turn 6 win = 100, Turn 10 win = 60, Turn 15+ = 0
    if metrics.avg_win_turn != float('inf') and metrics.avg_win_turn > 0:
        speed_raw = max(0, 100 - (metrics.avg_win_turn - 6) * 10)
        score.speed_score = min(100, speed_raw)
        score.avg_win_turn = metrics.avg_win_turn
    else:
        score.speed_score = 0
        score.avg_win_turn = float('inf')

    # MODERATE FIX: Consistency score - Based on win rate variance and actual win rate
    # A deck that never wins should score 0, not 50
    if not metrics.win_turns:
        # No wins at all = 0 consistency
        score.consistency_score = 0
    elif len(metrics.win_turns) == 1:
        # Single win: score based on win rate (low win rate = low consistency)
        win_rate = metrics.total_wins / metrics.total_games if metrics.total_games > 0 else 0
        # Scale from 0-50 based on win rate (winning 100% of games = 50, 1% = 0.5)
        score.consistency_score = min(50, win_rate * 50)
    else:
        # Multiple wins: calculate variance-based consistency
        variance = statistics.stdev(metrics.win_turns)
        # Lower variance = higher consistency
        consistency_base = max(0, 100 - variance * 10)

        # Scale by win rate: deck needs reasonable win rate to be "consistent"
        # At 25% win rate or higher, use full score; below that, scale down
        win_rate = metrics.total_wins / metrics.total_games if metrics.total_games > 0 else 0
        win_rate_factor = min(1.0, win_rate / 0.25)  # 25% = 1.0x, 12.5% = 0.5x, etc.

        score.consistency_score = min(100, consistency_base * win_rate_factor)

    # Power score: Based on damage output
    if metrics.cumulative_damage_by_turn:
        # Damage by turn 6 (index 5)
        if len(metrics.cumulative_damage_by_turn) > 5:
            score.avg_damage_turn_6 = metrics.cumulative_damage_by_turn[5]
            power_6 = min(100, score.avg_damage_turn_6 / 1.2)  # 120 damage = 100
        else:
            power_6 = 0

        # Damage by turn 10 (index 9)
        if len(metrics.cumulative_damage_by_turn) > 9:
            score.avg_damage_turn_10 = metrics.cumulative_damage_by_turn[9]
            power_10 = min(100, score.avg_damage_turn_10 / 1.2)
        else:
            power_10 = 0

        score.power_score = (power_6 + power_10) / 2
    else:
        score.power_score = 0

    # Synergy score: Based on extended mechanics usage
    total_mechanics = sum(extended_metrics.values())
    if total_mechanics > 0:
        # More mechanics = more synergy potential
        # Cap at 20 uses for max score
        synergy_raw = min(100, total_mechanics * 5)
        score.synergy_score = synergy_raw
    else:
        score.synergy_score = 30  # Base score for deck without special mechanics

    score.mechanics_used = extended_metrics
    score.win_rate = metrics.total_wins / metrics.total_games if metrics.total_games > 0 else 0

    # Calculate overall score (weighted average)
    weights = {
        'speed': 0.35,
        'consistency': 0.25,
        'power': 0.25,
        'synergy': 0.15,
    }

    score.overall_score = (
        score.speed_score * weights['speed'] +
        score.consistency_score * weights['consistency'] +
        score.power_score * weights['power'] +
        score.synergy_score * weights['synergy']
    )

    return score


# =============================================================================
# ENHANCED SIMULATION RUNNER
# =============================================================================

def run_enhanced_simulation(
    deck_cards: List['Card'],
    commander_card: 'Card',
    num_simulations: int = 100,
    max_turns: int = 10,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Run enhanced goldfish simulation with all metrics.

    This is the main entry point for dashboard integration.

    Args:
        deck_cards: List of cards in deck
        commander_card: Commander card
        num_simulations: Number of games to simulate
        max_turns: Maximum turns per game
        verbose: Print detailed output

    Returns:
        Dict containing:
            - win_metrics: WinMetrics object
            - extended_metrics: Extended mechanics usage
            - effectiveness: DeckEffectivenessScore
            - dashboard_data: Dashboard-ready format
            - report: Human-readable report string
    """
    from boardstate import BoardState

    # Initialize dummy board to detect mechanics in deck
    dummy_board = BoardState(deck_cards, commander_card)
    initialize_extended_metrics(dummy_board)

    # Analyze deck for mechanics
    deck_mechanics = analyze_deck_mechanics(deck_cards)

    # Run simulations with win tracking
    win_metrics = run_goldfish_simulation_with_metrics(
        deck_cards,
        commander_card,
        num_simulations=num_simulations,
        max_turns=max_turns,
        verbose=verbose
    )

    # Get extended metrics (will be populated during simulation)
    extended_metrics = {
        'flicker_cards': deck_mechanics.get('flicker_count', 0),
        'cascade_cards': deck_mechanics.get('cascade_count', 0),
        'persist_undying_cards': deck_mechanics.get('persist_count', 0) + deck_mechanics.get('undying_count', 0),
        'flashback_cards': deck_mechanics.get('flashback_count', 0),
        'convoke_delve_cards': deck_mechanics.get('convoke_count', 0) + deck_mechanics.get('delve_count', 0),
        'modal_cards': deck_mechanics.get('modal_count', 0),
        'copy_cards': deck_mechanics.get('copy_count', 0),
        'flash_cards': deck_mechanics.get('flash_count', 0),
    }

    # Calculate effectiveness score
    effectiveness = calculate_deck_effectiveness(win_metrics, extended_metrics)

    # Generate report
    report = format_win_metrics_report(win_metrics)

    # Dashboard data
    dashboard_data = get_dashboard_metrics(win_metrics)
    dashboard_data['effectiveness_score'] = effectiveness.overall_score
    dashboard_data['speed_score'] = effectiveness.speed_score
    dashboard_data['consistency_score'] = effectiveness.consistency_score
    dashboard_data['power_score'] = effectiveness.power_score
    dashboard_data['synergy_score'] = effectiveness.synergy_score
    dashboard_data['mechanics_analysis'] = deck_mechanics

    return {
        'win_metrics': win_metrics,
        'extended_metrics': extended_metrics,
        'effectiveness': effectiveness,
        'dashboard_data': dashboard_data,
        'report': report,
    }


def analyze_deck_mechanics(deck_cards: List['Card']) -> Dict[str, Any]:
    """
    Analyze deck for extended mechanics presence.

    Args:
        deck_cards: List of cards in deck

    Returns:
        Dict with mechanic counts and card lists
    """
    mechanics = {
        'flicker_count': 0,
        'flicker_cards': [],
        'cascade_count': 0,
        'cascade_cards': [],
        'suspend_count': 0,
        'suspend_cards': [],
        'persist_count': 0,
        'persist_cards': [],
        'undying_count': 0,
        'undying_cards': [],
        'flashback_count': 0,
        'flashback_cards': [],
        'buyback_count': 0,
        'buyback_cards': [],
        'retrace_count': 0,
        'retrace_cards': [],
        'convoke_count': 0,
        'convoke_cards': [],
        'delve_count': 0,
        'delve_cards': [],
        'modal_count': 0,
        'modal_cards': [],
        'copy_count': 0,
        'copy_cards': [],
        'flash_count': 0,
        'flash_cards': [],
    }

    for card in deck_cards:
        oracle = getattr(card, 'oracle_text', '')
        name = getattr(card, 'name', 'Unknown')

        # Check each mechanic
        if detect_flicker_ability(oracle)['has_flicker']:
            mechanics['flicker_count'] += 1
            mechanics['flicker_cards'].append(name)

        if detect_cascade(oracle):
            mechanics['cascade_count'] += 1
            mechanics['cascade_cards'].append(name)

        if detect_suspend(oracle)['has_suspend']:
            mechanics['suspend_count'] += 1
            mechanics['suspend_cards'].append(name)

        if detect_persist(oracle):
            mechanics['persist_count'] += 1
            mechanics['persist_cards'].append(name)

        if detect_undying(oracle):
            mechanics['undying_count'] += 1
            mechanics['undying_cards'].append(name)

        if detect_flashback(oracle)['has_flashback']:
            mechanics['flashback_count'] += 1
            mechanics['flashback_cards'].append(name)

        if detect_buyback(oracle)['has_buyback']:
            mechanics['buyback_count'] += 1
            mechanics['buyback_cards'].append(name)

        if detect_retrace(oracle):
            mechanics['retrace_count'] += 1
            mechanics['retrace_cards'].append(name)

        if detect_convoke(oracle):
            mechanics['convoke_count'] += 1
            mechanics['convoke_cards'].append(name)

        if detect_delve(oracle):
            mechanics['delve_count'] += 1
            mechanics['delve_cards'].append(name)

        if detect_modal_spell(oracle)['is_modal']:
            mechanics['modal_count'] += 1
            mechanics['modal_cards'].append(name)

        if detect_copy_ability(oracle)['has_copy']:
            mechanics['copy_count'] += 1
            mechanics['copy_cards'].append(name)

        if detect_flash(oracle) or getattr(card, 'has_flash', False):
            mechanics['flash_count'] += 1
            mechanics['flash_cards'].append(name)

    # Calculate total unique mechanics
    total_mechanics = sum(1 for k, v in mechanics.items()
                         if k.endswith('_count') and v > 0)
    mechanics['total_unique_mechanics'] = total_mechanics

    return mechanics


# =============================================================================
# DASHBOARD COMPONENT DATA
# =============================================================================

def get_win_probability_chart_data(metrics: WinMetrics) -> Dict[str, Any]:
    """
    Get data formatted for win probability chart.

    Returns Plotly-compatible data structure.
    """
    turns = [6, 8, 10]
    probabilities = [
        metrics.win_by_turn_6,
        metrics.win_by_turn_8,
        metrics.win_by_turn_10,
    ]
    ci_lower = [
        metrics.win_by_turn_6_ci[0],
        metrics.win_by_turn_8_ci[0],
        metrics.win_by_turn_10_ci[0],
    ]
    ci_upper = [
        metrics.win_by_turn_6_ci[1],
        metrics.win_by_turn_8_ci[1],
        metrics.win_by_turn_10_ci[1],
    ]

    return {
        'x': turns,
        'y': probabilities,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'type': 'bar',
        'name': 'Win Probability',
        'error_y': {
            'type': 'data',
            'symmetric': False,
            'array': [u - p for p, u in zip(probabilities, ci_upper)],
            'arrayminus': [p - l for p, l in zip(probabilities, ci_lower)],
        }
    }


def get_damage_progression_chart_data(metrics: WinMetrics) -> Dict[str, Any]:
    """
    Get data formatted for damage progression chart.

    Returns Plotly-compatible data structure.
    """
    turns = list(range(1, len(metrics.cumulative_damage_by_turn) + 1))

    return {
        'x': turns,
        'y': metrics.cumulative_damage_by_turn,
        'type': 'scatter',
        'mode': 'lines+markers',
        'name': 'Cumulative Damage',
        'line': {'shape': 'spline'},
        # Add win threshold line
        'shapes': [{
            'type': 'line',
            'x0': 0,
            'y0': 120,
            'x1': max(turns) if turns else 10,
            'y1': 120,
            'line': {'color': 'red', 'width': 2, 'dash': 'dash'},
        }]
    }


def get_effectiveness_gauge_data(score: DeckEffectivenessScore) -> Dict[str, Any]:
    """
    Get data formatted for effectiveness gauge chart.

    Returns Plotly-compatible gauge data.
    """
    return {
        'value': score.overall_score,
        'title': {'text': 'Deck Effectiveness'},
        'gauge': {
            'axis': {'range': [0, 100]},
            'bar': {'color': _get_score_color(score.overall_score)},
            'steps': [
                {'range': [0, 40], 'color': '#ffcccc'},
                {'range': [40, 70], 'color': '#ffffcc'},
                {'range': [70, 100], 'color': '#ccffcc'},
            ],
            'threshold': {
                'line': {'color': 'red', 'width': 4},
                'thickness': 0.75,
                'value': 70,  # "Good" threshold
            }
        },
        'components': {
            'speed': score.speed_score,
            'consistency': score.consistency_score,
            'power': score.power_score,
            'synergy': score.synergy_score,
        }
    }


def _get_score_color(score: float) -> str:
    """Get color based on score value."""
    if score >= 70:
        return '#28a745'  # Green
    elif score >= 40:
        return '#ffc107'  # Yellow
    else:
        return '#dc3545'  # Red


# =============================================================================
# QUICK ANALYSIS FUNCTIONS
# =============================================================================

def quick_deck_analysis(deck_cards: List['Card'], commander_card: 'Card') -> str:
    """
    Perform quick analysis and return summary string.

    Useful for command-line or quick checks.
    """
    results = run_enhanced_simulation(
        deck_cards,
        commander_card,
        num_simulations=50,
        max_turns=10,
        verbose=False
    )

    effectiveness = results['effectiveness']
    metrics = results['win_metrics']

    lines = [
        "=" * 50,
        "QUICK DECK ANALYSIS",
        "=" * 50,
        "",
        f"Overall Effectiveness: {effectiveness.overall_score:.1f}/100",
        "",
        "Component Scores:",
        f"  Speed:       {effectiveness.speed_score:.1f}/100",
        f"  Consistency: {effectiveness.consistency_score:.1f}/100",
        f"  Power:       {effectiveness.power_score:.1f}/100",
        f"  Synergy:     {effectiveness.synergy_score:.1f}/100",
        "",
        f"Average Win Turn: {effectiveness.avg_win_turn:.1f}" if effectiveness.avg_win_turn != float('inf') else "Average Win Turn: N/A",
        f"Win Rate: {effectiveness.win_rate * 100:.1f}%",
        "",
        "Win Probability (95% CI):",
        f"  Turn 6:  {metrics.win_by_turn_6 * 100:.1f}%",
        f"  Turn 8:  {metrics.win_by_turn_8 * 100:.1f}%",
        f"  Turn 10: {metrics.win_by_turn_10 * 100:.1f}%",
        "=" * 50,
    ]

    return "\n".join(lines)
