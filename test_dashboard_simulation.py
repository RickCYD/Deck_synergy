#!/usr/bin/env python3
"""
Test the exact flow the dashboard uses: analyze_deck_synergies with run_simulation=True
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.scryfall import fetch_card_details
from src.utils.card_roles import assign_roles_to_cards
from src.synergy_engine.analyzer import analyze_deck_synergies

def main():
    print("="*80)
    print("TESTING DASHBOARD SIMULATION FLOW")
    print("="*80)

    # Create a minimal test deck (just enough to run simulation)
    test_cards = [
        {'name': 'Zurgo and Ojutai', 'quantity': 1, 'is_commander': True, 'categories': ['Commander']},
        {'name': 'Sol Ring', 'quantity': 1},
        {'name': 'Plains', 'quantity': 20},
        {'name': 'Mountain', 'quantity': 15},
        {'name': 'Swamp', 'quantity': 15},
        {'name': 'Lightning Bolt', 'quantity': 1},
        {'name': 'Swords to Plowshares', 'quantity': 1},
    ]

    print("\n[STEP 1] Fetching card details from Scryfall...")
    try:
        cards_with_details = fetch_card_details(test_cards, use_local_cache=True)
        print(f"✓ Fetched details for {len(cards_with_details)} cards")
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n[STEP 2] Assigning roles...")
    assign_roles_to_cards(cards_with_details)
    print("✓ Roles assigned")

    print("\n[STEP 3] Running analyze_deck_synergies with run_simulation=True...")
    print("="*80)

    try:
        synergy_result = analyze_deck_synergies(
            cards_with_details,
            include_three_way=True,
            run_simulation=True,
            num_simulation_games=10  # Just 10 games for quick test
        )

        print("\n" + "="*80)
        print("[STEP 4] CHECKING RESULTS")
        print("="*80)

        print(f"\nsynergy_result type: {type(synergy_result)}")
        print(f"synergy_result keys: {list(synergy_result.keys()) if isinstance(synergy_result, dict) else 'N/A'}")

        if isinstance(synergy_result, dict):
            if 'two_way' in synergy_result:
                print(f"✓ Has 'two_way' synergies: {len(synergy_result['two_way'])} found")
            else:
                print("✗ Missing 'two_way' key")

            if 'three_way' in synergy_result:
                print(f"✓ Has 'three_way' synergies: {len(synergy_result['three_way'])} found")
            else:
                print("✗ Missing 'three_way' key")

            if 'simulation' in synergy_result:
                print(f"✓ Has 'simulation' key!")
                sim_results = synergy_result['simulation']
                print(f"  simulation type: {type(sim_results)}")
                print(f"  simulation keys: {list(sim_results.keys()) if isinstance(sim_results, dict) else 'N/A'}")

                if 'summary' in sim_results:
                    print(f"✓ Has 'summary' in simulation results!")
                    summary = sim_results['summary']
                    print(f"\n  📊 SUMMARY METRICS:")
                    print(f"    Total Damage (10 turns): {summary.get('total_damage_10_turns', 'N/A')}")
                    print(f"    Avg Damage/Turn: {summary.get('avg_damage_per_turn', 'N/A')}")
                    print(f"    Peak Power: {summary.get('peak_power', 'N/A')}")
                    print(f"    Commander Avg Turn: {summary.get('commander_avg_cast_turn', 'N/A')}")

                    if 'error' in summary:
                        print(f"\n  ✗ ERROR in summary: {summary['error']}")
                        return 1
                    else:
                        print("\n✅ SIMULATION DATA IS COMPLETE!")
                        return 0
                else:
                    print("✗ Missing 'summary' in simulation results")
                    return 1
            else:
                print("✗ Missing 'simulation' key - THIS IS THE PROBLEM!")
                print("\nThis means the dashboard won't show the effectiveness panel.")
                return 1
        else:
            print("✗ synergy_result is not a dict!")
            return 1

    except Exception as e:
        print(f"\n✗ analyze_deck_synergies failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    print("\n" + "="*80)
    if exit_code == 0:
        print("✅ SUCCESS: Dashboard simulation flow works correctly")
    else:
        print("❌ FAILURE: Dashboard simulation flow is broken")
    print("="*80)
    sys.exit(exit_code)
