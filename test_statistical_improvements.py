#!/usr/bin/env python3
"""
Quick test script to verify statistical analysis improvements.
"""

import sys
from pathlib import Path

# Add Simulation directory to path
sys.path.insert(0, str(Path(__file__).parent / "Simulation"))

from run_simulation import run_simulations
from simulate_game import Card
import pandas as pd


def create_test_deck():
    """Create a simple test deck for validation."""
    cards = []

    # Add lands (40 cards)
    for i in range(20):
        cards.append(Card(
            name=f"Mountain {i}",
            type="Land",
            mana_cost="",
            power=0,
            toughness=0,
            produces_colors=["R"],
            mana_production={"R": 1},
            etb_tapped=False,
            etb_tapped_conditions=[],
            has_haste=False
        ))

    for i in range(20):
        cards.append(Card(
            name=f"Forest {i}",
            type="Land",
            mana_cost="",
            power=0,
            toughness=0,
            produces_colors=["G"],
            mana_production={"G": 1},
            etb_tapped=False,
            etb_tapped_conditions=[],
            has_haste=False
        ))

    # Add creatures (50 cards - varying power)
    for i in range(25):
        cards.append(Card(
            name=f"Small Creature {i}",
            type="Creature",
            mana_cost="{1}{R}",
            power=2,
            toughness=2,
            produces_colors=[],
            mana_production={},
            etb_tapped=False,
            etb_tapped_conditions=[],
            has_haste=True
        ))

    for i in range(25):
        cards.append(Card(
            name=f"Medium Creature {i}",
            type="Creature",
            mana_cost="{2}{G}{G}",
            power=4,
            toughness=4,
            produces_colors=[],
            mana_production={},
            etb_tapped=False,
            etb_tapped_conditions=[],
            has_haste=False
        ))

    # Add some ramp (10 cards)
    for i in range(10):
        cards.append(Card(
            name=f"Ramp Spell {i}",
            type="Artifact",
            mana_cost="{2}",
            power=0,
            toughness=0,
            produces_colors=["Any"],
            mana_production={"Any": 1},
            etb_tapped=False,
            etb_tapped_conditions=[],
            has_haste=False
        ))

    # Commander
    commander = Card(
        name="Test Commander",
        type="Legendary Creature",
        mana_cost="{2}{R}{G}",
        power=5,
        toughness=5,
        produces_colors=[],
        mana_production={},
        etb_tapped=False,
        etb_tapped_conditions=[],
        has_haste=True,
        is_commander=True,
        is_legendary=True
    )

    return cards, commander


def main():
    """Run test simulation with statistical analysis."""
    print("=" * 80)
    print("TESTING STATISTICAL ANALYSIS IMPROVEMENTS")
    print("=" * 80)
    print("\nCreating test deck...")

    cards, commander = create_test_deck()
    print(f"✓ Created deck with {len(cards)} cards")
    print(f"✓ Commander: {commander.name}")

    print("\n" + "=" * 80)
    print("Running 100 game simulation with statistical analysis...")
    print("=" * 80)

    try:
        summary_df, distribution, creature_power, interaction, stats = run_simulations(
            cards=cards,
            commander_card=commander,
            num_games=100,
            max_turns=10,
            verbose=False,
            log_dir=None,
            num_workers=4,
            calculate_statistics=True
        )

        print("\n✓ Simulation completed successfully!")

        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY METRICS")
        print("=" * 80)
        print(f"\nTotal Damage (10 turns): {summary_df['Avg Total Damage'].sum():.2f}")
        print(f"Peak Power: {summary_df['Avg Total Power'].max():.2f}")
        print(f"Avg Mana (Turn 10): {summary_df['Avg Total Mana'].iloc[-1]:.2f}")

        # Print statistical report
        if stats and "formatted_report" in stats:
            print("\n" + stats["formatted_report"])
        else:
            print("\n⚠ WARNING: Statistical report not generated!")
            return 1

        # Validate statistical metrics
        print("\n" + "=" * 80)
        print("VALIDATION CHECKS")
        print("=" * 80)

        if stats and "summary" in stats:
            summary = stats["summary"]
            print(f"\n✓ Overall Status: {summary['overall_status']}")
            print(f"✓ Average CV: {summary['avg_coefficient_of_variation']:.3f}")
            print(f"✓ Recommended N: {summary['recommended_sample_size']}")

            # Check each metric has required fields
            for metric_name, analysis in summary['metric_analyses'].items():
                if "error" in analysis:
                    print(f"\n❌ {metric_name}: {analysis['error']}")
                    return 1

                required_fields = ['mean', 'median', 'std_dev', 'ci_95_lower', 'ci_95_upper',
                                   'coefficient_of_variation', 'recommended_n']
                missing = [f for f in required_fields if f not in analysis]
                if missing:
                    print(f"\n❌ {metric_name}: Missing fields: {missing}")
                    return 1

            print(f"\n✓ All {len(summary['metric_analyses'])} metrics validated successfully!")
        else:
            print("\n❌ Statistical summary not found!")
            return 1

        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED!")
        print("=" * 80)
        print("\nStatistical analysis system is working correctly.")
        print("Users can now determine if 100 simulations is sufficient for their deck.")

        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
