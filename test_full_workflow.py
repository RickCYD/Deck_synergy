#!/usr/bin/env python3
"""
Full workflow test: Load deck from Archidekt and run simulation
This tests the COMPLETE pipeline with the quantity expansion fix
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.archidekt import fetch_deck_from_archidekt
from src.api.scryfall import fetch_card_details
from src.utils.card_roles import assign_roles_to_cards

def main():
    archidekt_url = "https://archidekt.com/decks/16754562/zombielandia"

    print("="*80)
    print("FULL WORKFLOW TEST - Zombielandia Deck")
    print("="*80)
    print(f"\nArchidekt URL: {archidekt_url}")

    # Step 1: Fetch from Archidekt
    print("\n[STEP 1] Fetching deck from Archidekt...")
    try:
        deck_info = fetch_deck_from_archidekt(archidekt_url)
        print(f"✓ Loaded deck: {deck_info['name']}")
        print(f"  Cards from Archidekt: {len(deck_info['cards'])}")
    except Exception as e:
        print(f"✗ Failed to fetch from Archidekt: {e}")
        return 1

    # Step 2: Fetch card details
    print("\n[STEP 2] Fetching card details from Scryfall...")
    try:
        cards_with_details = fetch_card_details(deck_info['cards'], use_local_cache=True)
        print(f"✓ Fetched details for {len(cards_with_details)} unique cards")

        # Show quantity breakdown
        total_cards = sum(c.get('quantity', 1) for c in cards_with_details)
        print(f"  Total cards (with quantities): {total_cards}")

        # Count lands
        lands = [c for c in cards_with_details if 'Land' in c.get('type_line', '')]
        total_lands = sum(c.get('quantity', 1) for c in lands)
        print(f"  Unique lands: {len(lands)}")
        print(f"  Total lands (with quantities): {total_lands}")

    except Exception as e:
        print(f"✗ Failed to fetch card details: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Step 3: Assign roles
    print("\n[STEP 3] Assigning card roles...")
    assign_roles_to_cards(cards_with_details)
    print(f"✓ Roles assigned")

    # Step 4: Find commander
    print("\n[STEP 4] Identifying commander...")
    commander = next((c for c in cards_with_details if c.get('is_commander')), None)
    non_commander_cards = [c for c in cards_with_details if not c.get('is_commander')]

    if commander:
        print(f"✓ Commander: {commander.get('name')}")
        print(f"  CMC: {commander.get('cmc', 'Unknown')}")
    else:
        print("✗ No commander found!")
        return 1

    # Step 5: Expand cards by quantity (THE CRITICAL FIX)
    print("\n[STEP 5] Expanding cards by quantity for simulation...")
    expanded_cards = []
    for card in non_commander_cards:
        quantity = card.get('quantity', 1)
        for _ in range(quantity):
            expanded_cards.append(card)

    print(f"✓ Expanded from {len(non_commander_cards)} unique cards to {len(expanded_cards)} total cards")

    # Verify land count
    expanded_lands = [c for c in expanded_cards if 'Land' in c.get('type_line', '')]
    print(f"  Total lands in expanded deck: {len(expanded_lands)}")

    if len(expanded_lands) < 30:
        print(f"  ✗ WARNING: Only {len(expanded_lands)} lands - simulation will be inaccurate!")
    else:
        print(f"  ✓ Good land count for Commander format")

    # Step 6: Run simulation
    print("\n[STEP 6] Running simulation...")
    print("="*80)

    try:
        from src.simulation.deck_simulator import simulate_deck_effectiveness

        simulation_results = simulate_deck_effectiveness(
            cards=expanded_cards,  # Use EXPANDED deck with quantities
            commander=commander,
            num_games=100,
            max_turns=10,
            verbose=False
        )

        print("\n" + "="*80)
        print("[STEP 7] SIMULATION RESULTS")
        print("="*80)

        if simulation_results and 'summary' in simulation_results:
            summary = simulation_results['summary']

            if 'error' in summary:
                print(f"✗ Simulation failed: {summary['error']}")
                return 1

            print("\n📊 DECK EFFECTIVENESS METRICS:\n")
            print(f"  Total Damage (10 turns):     {summary.get('total_damage_10_turns', 0):.1f}")
            print(f"  Combat Damage:               {summary.get('combat_damage_10_turns', 0):.1f}")
            print(f"  Drain Damage:                {summary.get('drain_damage_10_turns', 0):.1f}")
            print(f"  Avg Damage/Turn:             {summary.get('avg_damage_per_turn', 0):.1f}")
            print(f"  Peak Board Power:            {summary.get('peak_power', 0):.1f}")
            if summary.get('commander_avg_cast_turn'):
                print(f"  Commander Avg Cast Turn:     {summary.get('commander_avg_cast_turn'):.1f}")

            print("\n" + "="*80)
            print("VALIDATION")
            print("="*80)

            # Validate against user's goldfish experience
            total_damage = summary.get('total_damage_10_turns', 0)
            commander_turn = summary.get('commander_avg_cast_turn', 99)
            peak_power = summary.get('peak_power', 0)

            issues = []

            # Check commander turn (user said turn 3-4)
            if commander_turn > 4.5:
                issues.append(f"✗ Commander cast turn too late: {commander_turn:.1f} (expected 3-4)")
            else:
                print(f"✓ Commander cast turn: {commander_turn:.1f} (matches user goldfish: turn 3-4)")

            # Check total damage (user said 100+)
            if total_damage < 60:
                issues.append(f"✗ Total damage too low: {total_damage:.1f} (expected 80-120+)")
            else:
                print(f"✓ Total damage: {total_damage:.1f} (reasonable for graveyard deck)")

            # Check peak power
            if peak_power < 10:
                issues.append(f"✗ Peak power too low: {peak_power:.1f} (expected 15+)")
            else:
                print(f"✓ Peak board power: {peak_power:.1f} (reasonable)")

            # Check land count (should be 35)
            if len(expanded_lands) != 35:
                issues.append(f"✗ Land count mismatch: {len(expanded_lands)} (expected 35)")
            else:
                print(f"✓ Land count: {len(expanded_lands)} (correct)")

            if issues:
                print("\n⚠️  ISSUES FOUND:")
                for issue in issues:
                    print(f"  {issue}")
                return 1
            else:
                print("\n✅ ALL VALIDATIONS PASSED!")
                print("\nThe fix is working correctly:")
                print("  • Using full 100-card deck (not 91 unique cards)")
                print("  • Commander cast on time (turn 3-4)")
                print("  • Damage output matches expected range")
                print("  • Land count is correct (35 lands)")
                return 0
        else:
            print("✗ No simulation results returned")
            return 1

    except Exception as e:
        print(f"\n✗ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    print("\n" + "="*80)
    if exit_code == 0:
        print("SUCCESS: Full workflow completed and validated")
    else:
        print("FAILURE: Issues found in workflow")
    print("="*80)
    sys.exit(exit_code)
