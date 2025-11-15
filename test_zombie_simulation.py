#!/usr/bin/env python3
"""
Test zombie deck simulation to identify potential issues
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def create_mock_zombie_deck():
    """Create a mock zombie tribal deck for testing"""

    # Typical zombie tribal cards
    mock_cards = [
        {
            'name': 'Gravecrawler',
            'type_line': 'Creature — Zombie',
            'mana_cost': '{B}',
            'power': '2',
            'toughness': '1',
            'oracle_text': 'Gravecrawler can\'t block. You may cast Gravecrawler from your graveyard as long as you control a Zombie.',
            'quantity': 1
        },
        {
            'name': 'Diregraf Ghoul',
            'type_line': 'Creature — Zombie',
            'mana_cost': '{B}',
            'power': '2',
            'toughness': '2',
            'oracle_text': 'Diregraf Ghoul enters the battlefield tapped.',
            'quantity': 1
        },
        {
            'name': 'Lord of the Undead',
            'type_line': 'Creature — Zombie',
            'mana_cost': '{1}{B}{B}',
            'power': '2',
            'toughness': '2',
            'oracle_text': 'Other Zombie creatures get +1/+1.\n{1}{B}, {T}: Return target Zombie card from your graveyard to your hand.',
            'quantity': 1
        },
        {
            'name': 'Cemetery Reaper',
            'type_line': 'Creature — Zombie',
            'mana_cost': '{1}{B}{B}',
            'power': '2',
            'toughness': '2',
            'oracle_text': 'Other Zombie creatures you control get +1/+1.\n{2}{B}, {T}: Exile target creature card from a graveyard. Create a 2/2 black Zombie creature token.',
            'quantity': 1
        },
        {
            'name': 'Wilhelt, the Rotcleaver',
            'type_line': 'Legendary Creature — Zombie Warrior',
            'mana_cost': '{2}{U}{B}',
            'power': '3',
            'toughness': '3',
            'oracle_text': 'Whenever a Zombie you control dies, create a 2/2 black Zombie creature token with decayed.\nAt the beginning of your end step, if a Zombie died this turn, draw a card.',
            'quantity': 1,
            'is_commander': True
        },
    ]

    # Add basic lands
    for i in range(20):
        mock_cards.append({
            'name': 'Swamp',
            'type_line': 'Basic Land — Swamp',
            'oracle_text': '({T}: Add {B}.)',
            'quantity': 1
        })

    # Add more zombies to reach ~40 cards
    filler_zombies = [
        {'name': 'Undead Augur', 'type_line': 'Creature — Zombie Wizard', 'mana_cost': '{B}{B}', 'power': '2', 'toughness': '2',
         'oracle_text': 'Whenever Undead Augur or another Zombie you control dies, you draw a card and you lose 1 life.', 'quantity': 1},
        {'name': 'Carrion Feeder', 'type_line': 'Creature — Zombie', 'mana_cost': '{B}', 'power': '1', 'toughness': '1',
         'oracle_text': 'Carrion Feeder can\'t block.\nSacrifice a creature: Put a +1/+1 counter on Carrion Feeder.', 'quantity': 1},
        {'name': 'Gray Merchant of Asphodel', 'type_line': 'Creature — Zombie', 'mana_cost': '{3}{B}{B}', 'power': '2', 'toughness': '4',
         'oracle_text': 'When Gray Merchant of Asphodel enters the battlefield, each opponent loses X life, where X is your devotion to black.', 'quantity': 1},
    ]

    for zombie in filler_zombies * 5:  # Duplicate to get more cards
        mock_cards.append(zombie.copy())

    return mock_cards[:60]  # Keep it manageable

def main():
    print("="*80)
    print("ZOMBIE DECK SIMULATION TEST")
    print("="*80)

    # Create mock zombie deck
    print("\n[Step 1] Creating mock zombie deck...")
    cards = create_mock_zombie_deck()
    print(f"  Created deck with {len(cards)} cards")

    commander = next((c for c in cards if c.get('is_commander')), None)
    print(f"  Commander: {commander['name'] if commander else 'None'}")

    # Try to import simulation module
    print("\n[Step 2] Testing simulation import...")
    try:
        from simulation.deck_simulator import simulate_deck_effectiveness, convert_card_to_simulation_format
        print("  ✓ Simulation module imported successfully")
    except ImportError as e:
        print(f"  ✗ Failed to import simulation module: {e}")
        import traceback
        traceback.print_exc()
        return

    # Try to convert cards
    print("\n[Step 3] Testing card conversion...")
    converted_cards = []
    conversion_errors = []

    for i, card in enumerate(cards):
        if card.get('is_commander'):
            continue

        try:
            converted = convert_card_to_simulation_format(card)
            converted_cards.append(converted)
        except Exception as e:
            conversion_errors.append((card['name'], str(e)))
            print(f"  ✗ Failed to convert {card['name']}: {e}")

    print(f"  Converted {len(converted_cards)}/{len(cards)-1} cards")
    if conversion_errors:
        print(f"  Conversion errors: {len(conversion_errors)}")
        for name, error in conversion_errors[:3]:
            print(f"    - {name}: {error}")

    # Try to run simulation
    print("\n[Step 4] Running simulation...")
    try:
        # Expand cards by quantity
        expanded = []
        non_commander_cards = [c for c in cards if not c.get('is_commander')]
        for card in non_commander_cards:
            quantity = card.get('quantity', 1)
            for _ in range(quantity):
                expanded.append(card)

        print(f"  Expanded to {len(expanded)} total cards")

        simulation_results = simulate_deck_effectiveness(
            cards=expanded,
            commander=commander,
            num_games=10,  # Just 10 games for quick test
            max_turns=10,
            verbose=True
        )

        # Check results
        print("\n[Step 5] Analyzing results...")
        if simulation_results:
            print(f"  Result keys: {list(simulation_results.keys())}")

            if 'summary' in simulation_results:
                summary = simulation_results['summary']
                print(f"  Summary keys: {list(summary.keys())}")

                if 'error' in summary:
                    print(f"\n  ✗ ERROR IN SUMMARY:")
                    print(f"    {summary['error']}")
                    print(f"\n  ROOT CAUSE: Simulation failed with error")
                else:
                    print(f"\n  ✓ SIMULATION SUCCESSFUL!")
                    print(f"    Total damage (10 turns): {summary.get('total_damage_10_turns', 0)}")
                    print(f"    Avg damage/turn: {summary.get('avg_damage_per_turn', 0)}")
            else:
                print(f"\n  ✗ MISSING 'summary' KEY")
                print(f"  ROOT CAUSE: Simulation returned results without summary")
        else:
            print(f"\n  ✗ SIMULATION RETURNED None OR EMPTY")
            print(f"  ROOT CAUSE: Simulation failed to return any results")

    except Exception as e:
        print(f"\n  ✗ SIMULATION EXCEPTION:")
        print(f"    {e}")
        import traceback
        traceback.print_exc()
        print(f"\n  ROOT CAUSE: Exception during simulation")

    print("\n" + "="*80)

if __name__ == "__main__":
    main()
