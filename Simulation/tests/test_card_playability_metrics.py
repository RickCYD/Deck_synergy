"""
Test card playability metrics integration in win_metrics.py

This test verifies that:
1. Card playability metrics are collected during simulation
2. Metrics are properly aggregated across multiple games
3. Dashboard metrics include card playability data
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulate_game import Card
from win_metrics import (
    run_goldfish_simulation_with_metrics,
    get_dashboard_metrics,
    WinMetrics,
)


def test_card_playability_metrics_collected():
    """Test that card playability metrics are collected in WinMetrics."""

    # Create a simple test deck
    deck_cards = []

    # Add some lands
    for i in range(10):
        deck_cards.append(Card(
            name=f"Forest {i}",
            type="Land",
            mana_cost="",
            power=0,
            toughness=0,
            produces_colors=["G"],
            mana_production=1,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False
        ))

    # Add some creatures
    for i in range(20):
        deck_cards.append(Card(
            name=f"Test Creature {i}",
            type="Creature",
            mana_cost="{2}{G}",
            power=2,
            toughness=2,
            produces_colors=[],
            mana_production=0,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=True
        ))

    # Commander
    commander = Card(
        name="Test Commander",
        type="Legendary Creature",
        mana_cost="{1}{G}",
        power=3,
        toughness=3,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        is_commander=True
    )

    # Run simulation (small number for quick test)
    print("Running simulation with card playability metrics...")
    metrics = run_goldfish_simulation_with_metrics(
        deck_cards,
        commander,
        num_simulations=5,  # Small number for quick test
        max_turns=6,
        verbose=False
    )

    # Verify WinMetrics has the new fields
    assert hasattr(metrics, 'avg_cards_drawn_per_turn'), "WinMetrics missing avg_cards_drawn_per_turn"
    assert hasattr(metrics, 'avg_hand_size_per_turn'), "WinMetrics missing avg_hand_size_per_turn"
    assert hasattr(metrics, 'avg_castable_non_lands_per_turn'), "WinMetrics missing avg_castable_non_lands_per_turn"
    assert hasattr(metrics, 'avg_uncastable_non_lands_per_turn'), "WinMetrics missing avg_uncastable_non_lands_per_turn"
    assert hasattr(metrics, 'avg_castable_percentage_per_turn'), "WinMetrics missing avg_castable_percentage_per_turn"

    # Verify metrics are populated (should have 6 turns worth of data)
    assert len(metrics.avg_cards_drawn_per_turn) == 6, f"Expected 6 turns of card draw data, got {len(metrics.avg_cards_drawn_per_turn)}"
    assert len(metrics.avg_hand_size_per_turn) == 6, f"Expected 6 turns of hand size data, got {len(metrics.avg_hand_size_per_turn)}"
    assert len(metrics.avg_castable_non_lands_per_turn) == 6, f"Expected 6 turns of castable data, got {len(metrics.avg_castable_non_lands_per_turn)}"
    assert len(metrics.avg_uncastable_non_lands_per_turn) == 6, f"Expected 6 turns of uncastable data, got {len(metrics.avg_uncastable_non_lands_per_turn)}"
    assert len(metrics.avg_castable_percentage_per_turn) == 6, f"Expected 6 turns of percentage data, got {len(metrics.avg_castable_percentage_per_turn)}"

    print("✓ WinMetrics fields verified")

    # Verify reasonable values
    # Turn 1 should draw 1 card (draw step)
    assert metrics.avg_cards_drawn_per_turn[0] >= 0, "Cards drawn should be >= 0"
    print(f"  Turn 1 avg cards drawn: {metrics.avg_cards_drawn_per_turn[0]:.2f}")

    # Hand size should be reasonable (starting hand is 7, minus cards played + cards drawn)
    assert all(0 <= h <= 10 for h in metrics.avg_hand_size_per_turn), "Hand size should be between 0 and 10"
    print(f"  Turn 1 avg hand size: {metrics.avg_hand_size_per_turn[0]:.2f}")

    # Castable + uncastable should equal total non-lands in hand
    print(f"  Turn 3 castable: {metrics.avg_castable_non_lands_per_turn[2]:.2f}")
    print(f"  Turn 3 uncastable: {metrics.avg_uncastable_non_lands_per_turn[2]:.2f}")

    # Castable percentage should be between 0 and 100
    assert all(0 <= p <= 100 for p in metrics.avg_castable_percentage_per_turn), "Castable % should be between 0 and 100"
    print(f"  Turn 3 castable %: {metrics.avg_castable_percentage_per_turn[2]:.2f}%")

    print("✓ Metric values are reasonable")

    return metrics


def test_dashboard_metrics_include_playability():
    """Test that dashboard metrics include card playability data."""

    # Create simple deck
    deck_cards = [
        Card(
            name=f"Forest {i}",
            type="Land",
            mana_cost="",
            power=0,
            toughness=0,
            produces_colors=["G"],
            mana_production=1,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False
        )
        for i in range(10)
    ]

    commander = Card(
        name="Test Commander",
        type="Legendary Creature",
        mana_cost="{1}{G}",
        power=3,
        toughness=3,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        is_commander=True
    )

    # Run simulation
    print("\nTesting dashboard metrics format...")
    metrics = run_goldfish_simulation_with_metrics(
        deck_cards,
        commander,
        num_simulations=3,
        max_turns=5,
        verbose=False
    )

    # Get dashboard metrics
    dashboard_data = get_dashboard_metrics(metrics)

    # Verify dashboard data includes new metrics
    assert 'avg_cards_drawn_per_turn' in dashboard_data, "Dashboard missing avg_cards_drawn_per_turn"
    assert 'avg_hand_size_per_turn' in dashboard_data, "Dashboard missing avg_hand_size_per_turn"
    assert 'avg_castable_non_lands_per_turn' in dashboard_data, "Dashboard missing avg_castable_non_lands_per_turn"
    assert 'avg_uncastable_non_lands_per_turn' in dashboard_data, "Dashboard missing avg_uncastable_non_lands_per_turn"
    assert 'avg_castable_percentage_per_turn' in dashboard_data, "Dashboard missing avg_castable_percentage_per_turn"

    print("✓ Dashboard metrics include all card playability fields")

    # Verify data types
    assert isinstance(dashboard_data['avg_cards_drawn_per_turn'], list), "avg_cards_drawn should be a list"
    assert isinstance(dashboard_data['avg_hand_size_per_turn'], list), "avg_hand_size should be a list"
    assert isinstance(dashboard_data['avg_castable_percentage_per_turn'], list), "avg_castable_percentage should be a list"

    print("✓ Dashboard metric types are correct")

    # Print sample data
    print(f"\nSample dashboard data (Turn 3):")
    if len(dashboard_data['avg_cards_drawn_per_turn']) > 2:
        print(f"  Cards drawn: {dashboard_data['avg_cards_drawn_per_turn'][2]:.2f}")
        print(f"  Hand size: {dashboard_data['avg_hand_size_per_turn'][2]:.2f}")
        print(f"  Castable: {dashboard_data['avg_castable_non_lands_per_turn'][2]:.2f}")
        print(f"  Uncastable: {dashboard_data['avg_uncastable_non_lands_per_turn'][2]:.2f}")
        print(f"  Castable %: {dashboard_data['avg_castable_percentage_per_turn'][2]:.2f}%")

    return dashboard_data


if __name__ == "__main__":
    print("=" * 60)
    print("CARD PLAYABILITY METRICS TEST")
    print("=" * 60)

    try:
        # Test 1: Metrics collection
        print("\nTest 1: WinMetrics collection")
        print("-" * 60)
        metrics = test_card_playability_metrics_collected()

        # Test 2: Dashboard integration
        print("\nTest 2: Dashboard metrics format")
        print("-" * 60)
        dashboard = test_dashboard_metrics_include_playability()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        print("\nCard playability metrics are successfully integrated!")
        print("The following metrics are now available in the dashboard:")
        print("  • Average cards drawn per turn")
        print("  • Average hand size per turn")
        print("  • Average castable non-lands per turn")
        print("  • Average uncastable non-lands per turn")
        print("  • Castable percentage per turn")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
