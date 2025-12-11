"""
Tests for Win Metrics Module

Tests cover:
- Statistical functions (confidence intervals)
- Win condition detection
- AI decision making
- Metrics collection
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from win_metrics import (
    calculate_confidence_interval,
    wilson_confidence_interval,
    calculate_win_probability,
    WinMetrics,
    ImprovedAI,
    detect_combo_win,
    format_win_metrics_report,
    get_dashboard_metrics,
)
from simulate_game import Card
from boardstate import BoardState


def create_dummy_commander():
    """Create a dummy commander for testing."""
    return Card(
        name="Dummy Commander",
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


def create_test_creature(name: str, power: int = 2, toughness: int = 2,
                         mana_cost: str = "2", **kwargs) -> Card:
    """Helper to create test creatures."""
    return Card(
        name=name,
        type="Creature",
        mana_cost=mana_cost,
        power=power,
        toughness=toughness,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=kwargs.get('has_haste', False),
        has_flying=kwargs.get('has_flying', False),
        has_trample=kwargs.get('has_trample', False),
        oracle_text=kwargs.get('oracle_text', ''),
    )


class TestStatisticalFunctions:
    """Test statistical calculation functions."""

    def test_confidence_interval_basic(self):
        """Test basic confidence interval calculation."""
        data = [5, 6, 7, 8, 9, 10]
        lower, upper = calculate_confidence_interval(data)

        # Mean is 7.5, CI should contain it
        assert lower < 7.5 < upper
        assert lower > 0
        assert upper < 15

    def test_confidence_interval_empty(self):
        """Test confidence interval with empty data."""
        lower, upper = calculate_confidence_interval([])
        assert lower == 0.0
        assert upper == 0.0

    def test_confidence_interval_single_value(self):
        """Test confidence interval with single value."""
        lower, upper = calculate_confidence_interval([5])
        assert lower == 0.0
        assert upper == 0.0

    def test_wilson_ci_zero_wins(self):
        """Test Wilson CI with no wins."""
        lower, upper = wilson_confidence_interval(0, 100)
        assert lower == 0.0
        assert upper < 0.1  # Should be small

    def test_wilson_ci_all_wins(self):
        """Test Wilson CI with all wins."""
        lower, upper = wilson_confidence_interval(100, 100)
        assert lower > 0.9  # Should be high
        assert upper >= 0.99  # Allow for floating point

    def test_wilson_ci_half_wins(self):
        """Test Wilson CI with 50% win rate."""
        lower, upper = wilson_confidence_interval(50, 100)
        assert 0.3 < lower < 0.5
        assert 0.5 < upper < 0.7

    def test_win_probability(self):
        """Test basic win probability calculation."""
        assert calculate_win_probability(50, 100) == 0.5
        assert calculate_win_probability(0, 100) == 0.0
        assert calculate_win_probability(100, 100) == 1.0
        assert calculate_win_probability(0, 0) == 0.0


class TestWinConditionDetection:
    """Test win condition detection for goldfish."""

    def test_detect_combo_infinite_damage(self):
        """Test detection of infinite damage combo."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        board.drain_damage_this_turn = 150  # Infinite damage indicator

        result = detect_combo_win(board)

        assert result['is_combo'] is True
        assert result['combo_type'] == 'infinite_damage'

    def test_detect_combo_infinite_tokens(self):
        """Test detection of infinite token combo."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        board.tokens_created_this_turn = 60

        result = detect_combo_win(board)

        assert result['is_combo'] is True
        assert result['combo_type'] == 'infinite_tokens'

    def test_detect_no_combo(self):
        """Test that normal game state is not detected as combo."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        board.drain_damage_this_turn = 10
        board.tokens_created_this_turn = 3

        result = detect_combo_win(board)

        assert result['is_combo'] is False


class TestImprovedAI:
    """Test improved AI decision making."""

    def test_evaluate_haste_creature_priority(self):
        """Test that haste creatures are prioritized."""
        commander = create_dummy_commander()
        board = BoardState([], commander)

        ai = ImprovedAI(board)

        haste_creature = create_test_creature("Goblin Guide", power=2, toughness=2, has_haste=True)
        normal_creature = create_test_creature("Bear", power=2, toughness=2)

        haste_score = ai.evaluate_card_priority(haste_creature)
        normal_score = ai.evaluate_card_priority(normal_creature)

        assert haste_score > normal_score

    def test_evaluate_mana_producer_priority(self):
        """Test that mana producers are prioritized early."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        board.turn = 2  # Early game

        ai = ImprovedAI(board)

        mana_rock = Card(
            name="Sol Ring",
            type="Artifact",
            mana_cost="1",
            power=0,
            toughness=0,
            produces_colors=[],
            mana_production=2,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False,
        )

        creature = create_test_creature("Bear", power=2, toughness=2)

        rock_score = ai.evaluate_card_priority(mana_rock)
        creature_score = ai.evaluate_card_priority(creature)

        assert rock_score > creature_score

    def test_evaluate_flying_bonus(self):
        """Test that flying creatures get bonus."""
        commander = create_dummy_commander()
        board = BoardState([], commander)

        ai = ImprovedAI(board)

        flying_creature = create_test_creature("Bird", power=2, toughness=2, has_flying=True)
        ground_creature = create_test_creature("Bear", power=2, toughness=2)

        flying_score = ai.evaluate_card_priority(flying_creature)
        ground_score = ai.evaluate_card_priority(ground_creature)

        assert flying_score > ground_score

    def test_get_optimal_play_sequence(self):
        """Test that optimal play sequence puts mana first."""
        commander = create_dummy_commander()
        board = BoardState([], commander)

        ai = ImprovedAI(board)

        sol_ring = Card(
            name="Sol Ring",
            type="Artifact",
            mana_cost="1",
            power=0,
            toughness=0,
            produces_colors=[],
            mana_production=2,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False,
        )

        creature = create_test_creature("Big Guy", power=5, toughness=5, mana_cost="5")

        cards = [creature, sol_ring]
        sequence = ai.get_optimal_play_sequence(cards)

        # Sol Ring should be first
        assert sequence[0].name == "Sol Ring"


class TestWinMetrics:
    """Test WinMetrics dataclass and report formatting."""

    def test_win_metrics_initialization(self):
        """Test that WinMetrics initializes correctly."""
        metrics = WinMetrics()

        assert metrics.win_by_turn_6 == 0.0
        assert metrics.total_wins == 0
        assert metrics.total_games == 0
        assert len(metrics.win_turns) == 0

    def test_format_report(self):
        """Test report formatting."""
        metrics = WinMetrics()
        metrics.total_games = 100
        metrics.total_wins = 75
        metrics.win_by_turn_6 = 0.25
        metrics.win_by_turn_8 = 0.50
        metrics.win_by_turn_10 = 0.75
        metrics.win_by_turn_6_ci = (0.17, 0.35)
        metrics.win_by_turn_8_ci = (0.40, 0.60)
        metrics.win_by_turn_10_ci = (0.65, 0.83)
        metrics.avg_win_turn = 8.5
        metrics.avg_win_turn_ci = (7.8, 9.2)
        metrics.combat_damage_wins = 50
        metrics.drain_damage_wins = 20
        metrics.cumulative_damage_by_turn = [10, 25, 45, 70, 100, 130, 160, 190, 220, 250]

        report = format_win_metrics_report(metrics)

        assert "GOLDFISH SIMULATION RESULTS" in report
        assert "Turn 6" in report
        assert "Turn 8" in report
        assert "Turn 10" in report
        assert "Combat Damage" in report

    def test_get_dashboard_metrics(self):
        """Test dashboard metrics conversion."""
        metrics = WinMetrics()
        metrics.total_games = 100
        metrics.total_wins = 50
        metrics.win_by_turn_6 = 0.2
        metrics.win_by_turn_8 = 0.4
        metrics.win_by_turn_10 = 0.5
        metrics.win_by_turn_6_ci = (0.13, 0.29)
        metrics.win_by_turn_8_ci = (0.31, 0.50)
        metrics.win_by_turn_10_ci = (0.40, 0.60)
        metrics.avg_win_turn = 9.0
        metrics.avg_win_turn_ci = (8.0, 10.0)

        dashboard = get_dashboard_metrics(metrics)

        assert dashboard['win_probability_turn_6'] == 0.2
        assert dashboard['win_probability_turn_8'] == 0.4
        assert dashboard['win_rate'] == 0.5
        assert 'win_breakdown' in dashboard
        assert 'damage_by_turn' in dashboard


class TestGamePlanDetection:
    """Test game plan detection based on deck archetype."""

    def test_voltron_game_plan(self):
        """Test voltron deck detection."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        board.deck_archetype = 'voltron'

        ai = ImprovedAI(board)

        assert ai.game_plan == 'voltron'

    def test_aggro_game_plan(self):
        """Test aggro deck detection."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        board.deck_archetype = 'aggro'

        ai = ImprovedAI(board)

        assert ai.game_plan == 'aggro'

    def test_combo_game_plan(self):
        """Test combo deck detection."""
        commander = create_dummy_commander()
        board = BoardState([], commander)
        board.deck_archetype = 'combo_control'

        ai = ImprovedAI(board)

        assert ai.game_plan == 'combo'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
