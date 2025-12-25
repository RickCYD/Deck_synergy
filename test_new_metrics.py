#!/usr/bin/env python
"""
Simple test script to validate the new deck effectiveness metrics.
Tests: card velocity, total cards drawn, playable %, land drop %, avg lands per turn
"""

import sys
import os

# Add Simulation directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Simulation'))

from simulate_game import Card
from win_metrics import run_goldfish_simulation_with_metrics, format_win_metrics_report


def create_test_deck():
    """Create a simple test deck for validation."""
    # Simple lands
    lands = []
    for i in range(35):
        lands.append(Card(
            name=f"Forest {i}",
            type="Land",
            mana_cost="",
            power=0,
            toughness=0,
            produces_colors=["G"],
            mana_production=1,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False,
            oracle_text="",
        ))

    # Simple creatures
    creatures = []
    for i in range(30):
        creatures.append(Card(
            name=f"Grizzly Bears {i}",
            type="Creature — Bear",
            mana_cost="{1}{G}",
            power=2,
            toughness=2,
            produces_colors=[],
            mana_production=0,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False,
            oracle_text="",
        ))

    # Mana rocks
    rocks = []
    for i in range(10):
        rocks.append(Card(
            name=f"Sol Ring {i}",
            type="Artifact",
            mana_cost="{1}",
            power=0,
            toughness=0,
            produces_colors=["C"],
            mana_production=2,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False,
            oracle_text="",
        ))

    # Card draw spells
    draw_spells = []
    for i in range(10):
        draw_spells.append(Card(
            name=f"Divination {i}",
            type="Sorcery",
            mana_cost="{2}{G}",
            power=0,
            toughness=0,
            produces_colors=[],
            mana_production=0,
            etb_tapped=False,
            etb_tapped_conditions={},
            has_haste=False,
            draw_cards=2,
            oracle_text="Draw two cards.",
        ))

    return lands + creatures + rocks + draw_spells


def create_commander():
    """Create a simple commander for testing."""
    return Card(
        name="Test Commander",
        type="Legendary Creature — Human",
        mana_cost="{2}{G}",
        power=3,
        toughness=3,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,
        is_commander=True,
        oracle_text="",
    )


def main():
    print("=" * 60)
    print("Testing New Deck Effectiveness Metrics")
    print("=" * 60)
    print()

    # Create test deck
    print("Creating test deck...")
    deck = create_test_deck()
    commander = create_commander()
    print(f"  - Deck size: {len(deck)} cards")
    print(f"  - Commander: {commander.name}")
    print()

    # Run simulation with small sample for quick test
    print("Running simulations (10 games, 10 turns max)...")
    metrics = run_goldfish_simulation_with_metrics(
        deck,
        commander,
        num_simulations=10,
        max_turns=10,
        verbose=False
    )
    print("  - Simulations complete!")
    print()

    # Validate new metrics exist and are reasonable
    print("Validating New Metrics:")
    print("-" * 60)

    # Check card velocity
    print(f"✓ Avg Card Velocity: {metrics.avg_card_velocity:.2f} cards/turn")
    assert hasattr(metrics, 'avg_card_velocity'), "Missing avg_card_velocity"
    assert metrics.avg_card_velocity >= 0, "Card velocity should be non-negative"

    # Check total cards drawn
    print(f"✓ Total Cards Drawn: {metrics.total_cards_drawn}")
    assert hasattr(metrics, 'total_cards_drawn'), "Missing total_cards_drawn"
    assert metrics.total_cards_drawn >= 0, "Total cards drawn should be non-negative"

    # Check avg cards drawn per game
    print(f"✓ Avg Cards Drawn per Game: {metrics.avg_cards_drawn_per_game:.1f}")
    assert hasattr(metrics, 'avg_cards_drawn_per_game'), "Missing avg_cards_drawn_per_game"
    assert metrics.avg_cards_drawn_per_game >= 0, "Avg cards drawn should be non-negative"

    # Check playable percentage
    print(f"✓ Avg % Non-Land Playable: {metrics.avg_playable_percentage:.1f}%")
    assert hasattr(metrics, 'avg_playable_percentage'), "Missing avg_playable_percentage"
    assert 0 <= metrics.avg_playable_percentage <= 100, "Playable % should be between 0-100"

    # Check land drop percentage
    print(f"✓ Avg % Land Drop: {metrics.avg_land_drop_percentage:.1f}%")
    assert hasattr(metrics, 'avg_land_drop_percentage'), "Missing avg_land_drop_percentage"
    assert 0 <= metrics.avg_land_drop_percentage <= 100, "Land drop % should be between 0-100"

    # Check avg lands per turn
    print(f"✓ Avg Lands per Turn: {metrics.avg_lands_per_turn:.2f}")
    assert hasattr(metrics, 'avg_lands_per_turn'), "Missing avg_lands_per_turn"
    assert metrics.avg_lands_per_turn >= 0, "Avg lands per turn should be non-negative"

    print()
    print("=" * 60)
    print("All New Metrics Validated Successfully!")
    print("=" * 60)
    print()

    # Print full report
    print("Full Metrics Report:")
    print(format_win_metrics_report(metrics))
    print()

    print("✓ Test completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
