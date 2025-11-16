#!/usr/bin/env python3
"""
Test script to investigate why deck effectiveness is not showing for Zombielandia deck
"""

import sys
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def main():
    print("="*80)
    print("ZOMBIELANDIA DECK INVESTIGATION")
    print("="*80)

    # Step 1: Fetch the deck from Archidekt
    print("\n[Step 1] Fetching deck from Archidekt...")
    try:
        from api.archidekt import fetch_deck_from_archidekt

        deck_url = "https://archidekt.com/decks/16754562/zombielandia"
        deck_data = fetch_deck_from_archidekt(deck_url)

        print(f"✓ Successfully fetched deck: {deck_data['name']}")
        print(f"  Deck ID: {deck_data['id']}")
        print(f"  Total cards in response: {len(deck_data['cards'])}")

        # Analyze deck structure
        commanders = [c for c in deck_data['cards'] if c.get('is_commander')]
        non_commanders = [c for c in deck_data['cards'] if not c.get('is_commander')]

        print(f"  Commanders: {len(commanders)}")
        for cmd in commanders:
            print(f"    - {cmd['name']}")

        print(f"  Non-commander cards: {len(non_commanders)}")

        # Count total cards by quantity
        total_quantity = sum(c.get('quantity', 1) for c in deck_data['cards'])
        print(f"  Total card quantity (including duplicates): {total_quantity}")

    except Exception as e:
        print(f"✗ Failed to fetch deck: {e}")
        traceback.print_exc()
        return

    # Step 2: Enrich cards with Scryfall data
    print("\n[Step 2] Enriching cards with Scryfall data...")
    try:
        from api.scryfall import get_card_by_name

        enriched_cards = []
        failed_cards = []

        for i, card in enumerate(deck_data['cards']):
            card_name = card['name']
            print(f"  [{i+1}/{len(deck_data['cards'])}] Fetching {card_name}...", end=' ')

            try:
                scryfall_card = get_card_by_name(card_name)

                # Merge Archidekt and Scryfall data
                enriched_card = {
                    **scryfall_card,
                    'quantity': card.get('quantity', 1),
                    'is_commander': card.get('is_commander', False),
                    'categories': card.get('categories', [])
                }
                enriched_cards.append(enriched_card)
                print("✓")

            except Exception as e:
                print(f"✗ {e}")
                failed_cards.append((card_name, str(e)))
                # Add a minimal card entry to continue
                enriched_cards.append({
                    'name': card_name,
                    'quantity': card.get('quantity', 1),
                    'is_commander': card.get('is_commander', False),
                    'error': str(e)
                })

        print(f"\n  Successfully enriched: {len(enriched_cards) - len(failed_cards)}/{len(deck_data['cards'])}")
        if failed_cards:
            print(f"  Failed cards: {len(failed_cards)}")
            for name, error in failed_cards[:5]:  # Show first 5 failures
                print(f"    - {name}: {error}")

    except Exception as e:
        print(f"✗ Failed to enrich cards: {e}")
        traceback.print_exc()
        return

    # Step 3: Try to run simulation
    print("\n[Step 3] Running simulation...")
    try:
        from simulation.deck_simulator import simulate_deck_effectiveness

        # Find commander
        commander = next((c for c in enriched_cards if c.get('is_commander')), None)
        non_commander_cards = [c for c in enriched_cards if not c.get('is_commander')]

        print(f"  Commander: {commander['name'] if commander else 'None'}")
        print(f"  Non-commander cards: {len(non_commander_cards)}")

        # Expand cards by quantity
        expanded_cards = []
        for card in non_commander_cards:
            quantity = card.get('quantity', 1)
            for _ in range(quantity):
                expanded_cards.append(card)

        print(f"  Expanded to {len(expanded_cards)} total cards")

        # Check for cards with errors
        error_cards = [c for c in expanded_cards if 'error' in c]
        if error_cards:
            print(f"  WARNING: {len(error_cards)} cards have errors (may affect simulation)")

        # Run simulation
        print(f"  Running 100 games, 10 turns each...")
        simulation_results = simulate_deck_effectiveness(
            cards=expanded_cards,
            commander=commander,
            num_games=100,
            max_turns=10,
            verbose=False
        )

        # Check results
        print("\n[Step 4] Analyzing simulation results...")
        if simulation_results:
            print(f"  Result keys: {list(simulation_results.keys())}")

            if 'summary' in simulation_results:
                summary = simulation_results['summary']
                print(f"  Summary keys: {list(summary.keys())}")

                if 'error' in summary:
                    print(f"\n✗ SIMULATION ERROR FOUND:")
                    print(f"  Error: {summary['error']}")
                    print(f"\n  This is why deck effectiveness is not showing!")
                    print(f"  The UI only displays effectiveness when:")
                    print(f"    - simulation_results has a 'summary' key")
                    print(f"    - AND summary does NOT have an 'error' key")
                else:
                    print(f"\n✓ SIMULATION SUCCESSFUL:")
                    print(f"  Total damage (10 turns): {summary.get('total_damage_10_turns', 0)}")
                    print(f"  Average damage/turn: {summary.get('avg_damage_per_turn', 0)}")
                    print(f"  Peak board power: {summary.get('peak_power', 0)}")
                    if summary.get('commander_avg_cast_turn'):
                        print(f"  Commander avg cast turn: {summary.get('commander_avg_cast_turn')}")
            else:
                print(f"\n✗ MISSING 'summary' KEY:")
                print(f"  The simulation results don't have a 'summary' key")
                print(f"  This is why deck effectiveness is not showing!")
        else:
            print(f"\n✗ SIMULATION RETURNED None")
            print(f"  This is why deck effectiveness is not showing!")

    except ImportError as e:
        print(f"\n✗ IMPORT ERROR:")
        print(f"  Cannot import simulation module: {e}")
        print(f"\n  This is likely why deck effectiveness is not showing!")
        print(f"  The simulation module may be missing dependencies.")
        traceback.print_exc()

    except Exception as e:
        print(f"\n✗ SIMULATION FAILED:")
        print(f"  Error: {e}")
        print(f"\n  This is why deck effectiveness is not showing!")
        traceback.print_exc()

    print("\n" + "="*80)
    print("INVESTIGATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
