#!/usr/bin/env python3
"""
Test script to compare different sample sizes and validate statistical analysis.

This script runs simulations with varying sample sizes (50, 100, 300, 500)
and demonstrates:
1. How confidence intervals narrow with larger samples
2. How coefficient of variation reveals deck consistency
3. Multiple batches to show reproducibility
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from Simulation.run_simulation import run_simulations
from Simulation.simulate_game import Card
from parse_decklist import parse_decklist
import pandas as pd


def load_deck(deck_path: str):
    """Load a deck from file."""
    print(f"Loading deck from: {deck_path}")
    cards, commander = parse_decklist(deck_path)
    print(f"Loaded {len(cards)} cards with commander: {commander.name if commander else 'None'}")
    return cards, commander


def compare_sample_sizes(cards, commander, sample_sizes=[50, 100, 300, 500], max_turns=10):
    """Compare simulation results across different sample sizes.

    Parameters
    ----------
    cards
        Deck list
    commander
        Commander card
    sample_sizes
        List of sample sizes to test
    max_turns
        Turns per game

    Returns
    -------
    dict
        Results for each sample size
    """
    results = {}

    print("\n" + "=" * 80)
    print("SAMPLE SIZE COMPARISON ANALYSIS")
    print("=" * 80)
    print(f"\nTesting sample sizes: {sample_sizes}")
    print(f"Max turns per game: {max_turns}")
    print(f"Commander: {commander.name if commander else 'None'}")
    print()

    for n in sample_sizes:
        print(f"\n{'=' * 80}")
        print(f"Running {n} simulations...")
        print(f"{'=' * 80}")

        summary_df, distribution, creature_power, interaction, stats = run_simulations(
            cards=cards,
            commander_card=commander,
            num_games=n,
            max_turns=max_turns,
            verbose=False,
            log_dir=None,
            num_workers=4,
            calculate_statistics=True
        )

        results[n] = {
            "summary_df": summary_df,
            "distribution": distribution,
            "creature_power": creature_power,
            "interaction": interaction,
            "statistics": stats
        }

        # Print statistical report
        if stats:
            print("\n" + stats["formatted_report"])

        # Print key summary metrics
        total_damage = summary_df["Avg Total Damage"].sum()
        print(f"\n📊 SUMMARY FOR N={n}:")
        print(f"   Total Damage (10 turns): {total_damage:.2f}")
        if stats and "summary" in stats:
            print(f"   Overall Status: {stats['summary']['overall_status']}")
            print(f"   Recommended N: {stats['summary']['recommended_sample_size']}")

    return results


def run_multiple_batches(cards, commander, num_batches=3, games_per_batch=100, max_turns=10):
    """Run multiple batches to demonstrate reproducibility.

    Parameters
    ----------
    cards
        Deck list
    commander
        Commander card
    num_batches
        Number of independent batches to run
    games_per_batch
        Games per batch
    max_turns
        Turns per game

    Returns
    -------
    list
        Results for each batch
    """
    print("\n" + "=" * 80)
    print("REPRODUCIBILITY TEST - MULTIPLE BATCHES")
    print("=" * 80)
    print(f"\nRunning {num_batches} independent batches of {games_per_batch} games each")
    print(f"This tests if results are consistent across different random samples\n")

    batch_results = []
    batch_damages = []

    for batch_num in range(1, num_batches + 1):
        print(f"\n{'─' * 80}")
        print(f"BATCH {batch_num}/{num_batches}")
        print(f"{'─' * 80}")

        summary_df, distribution, creature_power, interaction, stats = run_simulations(
            cards=cards,
            commander_card=commander,
            num_games=games_per_batch,
            max_turns=max_turns,
            verbose=False,
            log_dir=None,
            num_workers=4,
            calculate_statistics=True
        )

        total_damage = summary_df["Avg Total Damage"].sum()
        batch_damages.append(total_damage)

        batch_results.append({
            "batch": batch_num,
            "summary_df": summary_df,
            "statistics": stats,
            "total_damage": total_damage
        })

        print(f"\nBatch {batch_num} Total Damage: {total_damage:.2f}")
        if stats and "summary" in stats:
            print(f"Status: {stats['summary']['overall_status']}")
            print(f"Avg CV: {stats['summary']['avg_coefficient_of_variation']:.3f}")

    # Analyze batch consistency
    print("\n" + "=" * 80)
    print("BATCH CONSISTENCY ANALYSIS")
    print("=" * 80)

    mean_damage = sum(batch_damages) / len(batch_damages)
    min_damage = min(batch_damages)
    max_damage = max(batch_damages)
    range_pct = ((max_damage - min_damage) / mean_damage * 100) if mean_damage > 0 else 0

    print(f"\nTotal Damage across {num_batches} batches:")
    print(f"   Mean: {mean_damage:.2f}")
    print(f"   Min: {min_damage:.2f}")
    print(f"   Max: {max_damage:.2f}")
    print(f"   Range: {max_damage - min_damage:.2f} ({range_pct:.1f}% of mean)")

    if range_pct < 5:
        print(f"\n✓ EXCELLENT: Batch variation < 5%. Results are highly reproducible.")
    elif range_pct < 10:
        print(f"\n✓ GOOD: Batch variation < 10%. Results are reasonably consistent.")
    elif range_pct < 15:
        print(f"\n⚠ FAIR: Batch variation < 15%. Consider more samples for precision.")
    else:
        print(f"\n⚠ HIGH VARIANCE: Batch variation > 15%. Deck may be inconsistent or needs more samples.")

    return batch_results


def main():
    """Main test function."""
    import argparse

    parser = argparse.ArgumentParser(description="Test simulation sample sizes and statistical validity")
    parser.add_argument(
        "deck_path",
        help="Path to deck file (TXT or CSV format)"
    )
    parser.add_argument(
        "--sample-sizes",
        nargs="+",
        type=int,
        default=[50, 100, 300, 500],
        help="Sample sizes to test (default: 50 100 300 500)"
    )
    parser.add_argument(
        "--batches",
        type=int,
        default=3,
        help="Number of batches for reproducibility test (default: 3)"
    )
    parser.add_argument(
        "--turns",
        type=int,
        default=10,
        help="Maximum turns per game (default: 10)"
    )
    parser.add_argument(
        "--skip-comparison",
        action="store_true",
        help="Skip sample size comparison test"
    )
    parser.add_argument(
        "--skip-batches",
        action="store_true",
        help="Skip multiple batch test"
    )

    args = parser.parse_args()

    # Load deck
    try:
        cards, commander = load_deck(args.deck_path)
    except Exception as e:
        print(f"ERROR: Failed to load deck: {e}")
        return 1

    if not commander:
        print("ERROR: No commander found in deck!")
        return 1

    # Run tests
    if not args.skip_comparison:
        print("\n" + "🔬" * 40)
        print("TEST 1: SAMPLE SIZE COMPARISON")
        print("🔬" * 40)
        comparison_results = compare_sample_sizes(
            cards,
            commander,
            sample_sizes=args.sample_sizes,
            max_turns=args.turns
        )

    if not args.skip_batches:
        print("\n" + "🔁" * 40)
        print("TEST 2: REPRODUCIBILITY TEST")
        print("🔁" * 40)
        batch_results = run_multiple_batches(
            cards,
            commander,
            num_batches=args.batches,
            games_per_batch=100,
            max_turns=args.turns
        )

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)
    print("\nKEY TAKEAWAYS:")
    print("  1. Check the 'coefficient of variation' (CV) to assess deck consistency")
    print("  2. Lower CV = more consistent deck = fewer samples needed")
    print("  3. Higher CV = more variance = need more samples for accuracy")
    print("  4. Look at 'Recommended N' for guidance on optimal sample size")
    print("  5. Compare batch results to verify reproducibility")
    print("\n" + "=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
