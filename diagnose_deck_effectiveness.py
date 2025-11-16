#!/usr/bin/env python3
"""
Comprehensive diagnostic for deck effectiveness issues
This script helps identify why deck effectiveness might not be showing
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("="*80)
    print("DEPENDENCY CHECK")
    print("="*80)

    required_modules = {
        'pandas': 'pandas',
        'numpy': 'numpy',
        'requests': 'requests',
        # 'dash': 'dash',  # Only needed for web UI, not simulation
    }

    missing = []
    for display_name, module_name in required_modules.items():
        try:
            __import__(module_name)
            print(f"  ✓ {display_name} is installed")
        except ImportError:
            print(f"  ✗ {display_name} is NOT installed")
            missing.append(display_name)

    if missing:
        print(f"\n  ERROR: Missing dependencies: {', '.join(missing)}")
        print(f"  Run: pip install {' '.join(missing)}")
        return False

    return True

def check_simulation_imports():
    """Check if simulation modules can be imported"""
    print("\n" + "="*80)
    print("SIMULATION MODULE CHECK")
    print("="*80)

    try:
        from simulation.deck_simulator import simulate_deck_effectiveness, convert_card_to_simulation_format
        print("  ✓ Simulation modules can be imported")
        return True
    except ImportError as e:
        print(f"  ✗ Cannot import simulation modules: {e}")
        print("\n  This will cause deck effectiveness to fail!")
        print("  Check that the Simulation/ directory exists and has all required files")
        return False
    except Exception as e:
        print(f"  ✗ Unexpected error importing simulation: {e}")
        return False

def diagnose_archidekt_access(deck_url):
    """Check if we can access Archidekt API"""
    print("\n" + "="*80)
    print("ARCHIDEKT API ACCESS CHECK")
    print("="*80)

    try:
        from api.archidekt import fetch_deck_from_archidekt, extract_deck_id

        deck_id = extract_deck_id(deck_url)
        print(f"  Deck ID: {deck_id}")

        print(f"  Attempting to fetch deck from Archidekt API...")
        deck_data = fetch_deck_from_archidekt(deck_url)

        print(f"  ✓ Successfully fetched deck!")
        print(f"    Name: {deck_data['name']}")
        print(f"    Cards: {len(deck_data['cards'])}")

        return deck_data

    except Exception as e:
        error_str = str(e)
        print(f"  ✗ FAILED to fetch deck: {e}")

        if '403' in error_str or 'Forbidden' in error_str:
            print("\n  ROOT CAUSE: Deck is PRIVATE or API is blocking requests")
            print("  SOLUTION:")
            print("    1. Make sure the deck is PUBLIC on Archidekt")
            print("    2. Check if the deck exists at the URL")
            print("    3. Try loading a different deck to test if the API works")
        elif '404' in error_str or 'Not Found' in error_str:
            print("\n  ROOT CAUSE: Deck NOT FOUND")
            print("  SOLUTION: Check that the deck URL is correct")
        else:
            print("\n  ROOT CAUSE: Network or API error")
            print("  SOLUTION: Check your internet connection")

        return None

def diagnose_card_fetching(deck_data):
    """Check if cards can be fetched from Scryfall"""
    print("\n" + "="*80)
    print("CARD DATA FETCHING CHECK")
    print("="*80)

    if not deck_data:
        print("  Skipping (no deck data)")
        return None

    try:
        from api.scryfall import get_card_by_name

        cards = deck_data['cards']
        print(f"  Fetching details for {len(cards)} cards from Scryfall...")

        enriched_cards = []
        failed_cards = []
        missing_oracle_text = []

        for i, card in enumerate(cards[:5]):  # Test first 5 cards
            card_name = card['name']
            print(f"    [{i+1}/5] {card_name}...", end=' ')

            try:
                scryfall_card = get_card_by_name(card_name)

                # Merge data
                enriched_card = {
                    **scryfall_card,
                    'quantity': card.get('quantity', 1),
                    'is_commander': card.get('is_commander', False),
                }

                # Check for oracle text
                if not enriched_card.get('oracle_text'):
                    print(f"⚠ (missing oracle_text)")
                    missing_oracle_text.append(card_name)
                else:
                    print(f"✓")

                enriched_cards.append(enriched_card)

            except Exception as e:
                print(f"✗ {e}")
                failed_cards.append((card_name, str(e)))

        if failed_cards:
            print(f"\n  ⚠ WARNING: {len(failed_cards)} cards failed to fetch")
            print("  This may cause simulation issues")

        if missing_oracle_text:
            print(f"\n  ⚠ WARNING: {len(missing_oracle_text)} cards missing oracle_text")
            print("  Simulation may not work properly for these cards")

        return enriched_cards

    except Exception as e:
        print(f"  ✗ Card fetching failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def diagnose_simulation(cards, deck_data):
    """Check if simulation runs successfully"""
    print("\n" + "="*80)
    print("SIMULATION EXECUTION CHECK")
    print("="*80)

    if not cards:
        print("  Skipping (no cards)")
        return None

    try:
        from simulation.deck_simulator import simulate_deck_effectiveness

        # Find commander
        commander = next((c for c in deck_data['cards'] if c.get('is_commander')), None)

        if not commander:
            print("  ⚠ WARNING: No commander found")
            print("  Using dummy commander for simulation")
        else:
            print(f"  Commander: {commander['name']}")

        # Expand cards by quantity
        expanded_cards = []
        non_commander_cards = [c for c in cards if not c.get('is_commander')]
        for card in non_commander_cards:
            quantity = card.get('quantity', 1)
            for _ in range(quantity):
                expanded_cards.append(card)

        print(f"  Deck size: {len(expanded_cards)} cards")

        if len(expanded_cards) < 30:
            print(f"  ⚠ WARNING: Deck has only {len(expanded_cards)} cards")
            print("  This is unusually small and may affect simulation")

        # Run simulation
        print(f"  Running simulation (10 games)...")
        simulation_results = simulate_deck_effectiveness(
            cards=expanded_cards,
            commander=commander,
            num_games=10,
            max_turns=10,
            verbose=False
        )

        # Check results structure
        print("\n  Checking simulation results...")

        if not simulation_results:
            print("  ✗ SIMULATION RETURNED None OR EMPTY DICT")
            print("\n  ROOT CAUSE: Simulation failed to return any results")
            print("  SOLUTION: Check simulation logs for errors")
            return None

        print(f"  Result keys: {list(simulation_results.keys())}")

        if 'summary' not in simulation_results:
            print("  ✗ MISSING 'summary' KEY")
            print("\n  ROOT CAUSE: Simulation results missing summary")
            print("  SOLUTION: This is a bug in the simulation code")
            return None

        summary = simulation_results['summary']
        print(f"  Summary keys: {list(summary.keys())}")

        if 'error' in summary:
            print(f"  ✗ ERROR IN SUMMARY: {summary['error']}")
            print("\n  ROOT CAUSE: Simulation encountered an error")
            print(f"  Error message: {summary['error']}")
            print("\n  SOLUTION:")
            if 'module' in summary['error'].lower() or 'import' in summary['error'].lower():
                print("    - Install missing dependencies")
                print("    - Run: pip install -r requirements.txt")
            else:
                print("    - Check simulation logs for details")
                print("    - Try with a simpler deck to test")
            return None

        # SUCCESS!
        print("  ✓ SIMULATION SUCCESSFUL!")
        print(f"\n  Results:")
        print(f"    Total damage (10 turns): {summary.get('total_damage_10_turns', 0):.1f}")
        print(f"    Avg damage/turn: {summary.get('avg_damage_per_turn', 0):.1f}")
        print(f"    Peak board power: {summary.get('peak_power', 0):.1f}")
        if summary.get('commander_avg_cast_turn'):
            print(f"    Commander avg cast turn: {summary.get('commander_avg_cast_turn'):.1f}")

        print("\n  ✅ DECK EFFECTIVENESS SHOULD BE SHOWING!")
        print("  If it's not showing in the UI, there may be a frontend issue.")

        return simulation_results

    except Exception as e:
        print(f"  ✗ SIMULATION EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        print("\n  ROOT CAUSE: Exception during simulation")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python diagnose_deck_effectiveness.py <archidekt_deck_url>")
        print("\nExample:")
        print("  python diagnose_deck_effectiveness.py https://archidekt.com/decks/12345/my-deck")
        sys.exit(1)

    deck_url = sys.argv[1]

    print("="*80)
    print("DECK EFFECTIVENESS DIAGNOSTIC")
    print("="*80)
    print(f"Deck URL: {deck_url}")
    print()

    # Run diagnostics
    deps_ok = check_dependencies()
    if not deps_ok:
        print("\n❌ CRITICAL: Missing dependencies. Install them first.")
        return

    sim_ok = check_simulation_imports()
    if not sim_ok:
        print("\n❌ CRITICAL: Simulation modules unavailable.")
        return

    deck_data = diagnose_archidekt_access(deck_url)
    if not deck_data:
        print("\n❌ CRITICAL: Cannot fetch deck from Archidekt.")
        print("\nCOMMON CAUSES:")
        print("  1. Deck is PRIVATE - make it PUBLIC on Archidekt")
        print("  2. Deck doesn't exist - check the URL")
        print("  3. Network issues - check your connection")
        return

    cards = diagnose_card_fetching(deck_data)
    if not cards:
        print("\n❌ CRITICAL: Cannot fetch card details.")
        return

    sim_results = diagnose_simulation(cards, deck_data)

    print("\n" + "="*80)
    print("DIAGNOSTIC SUMMARY")
    print("="*80)

    if sim_results and 'summary' in sim_results and 'error' not in sim_results['summary']:
        print("✅ ALL CHECKS PASSED!")
        print("\nDeck effectiveness should be showing correctly.")
        print("If it's still not showing, the issue is likely in the frontend/UI code.")
    else:
        print("❌ ISSUES DETECTED!")
        print("\nDeck effectiveness will NOT show because simulation failed.")
        print("Review the diagnostic output above to identify the root cause.")

if __name__ == "__main__":
    main()
