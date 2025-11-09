#!/usr/bin/env python3
"""
Diagnostic script to test simulation integration
Run this to check if the simulation module is working correctly
"""

import sys
from pathlib import Path

print("="*70)
print("DECK SYNERGY SIMULATION DIAGNOSTIC")
print("="*70)

# Test 1: Check if Simulation directory exists
print("\n1. Checking Simulation directory...")
sim_path = Path("Simulation")
if sim_path.exists():
    print(f"   ✓ Simulation directory found at: {sim_path.absolute()}")
    print(f"   Files: {list(sim_path.glob('*.py'))[:5]}...")
else:
    print(f"   ✗ Simulation directory not found!")
    sys.exit(1)

# Test 2: Check if dependencies are installed
print("\n2. Checking dependencies...")
try:
    import pandas as pd
    print(f"   ✓ pandas {pd.__version__} installed")
except ImportError as e:
    print(f"   ✗ pandas not installed: {e}")
    print("   → Run: pip install pandas")

try:
    import numpy as np
    print(f"   ✓ numpy {np.__version__} installed")
except ImportError as e:
    print(f"   ✗ numpy not installed: {e}")
    print("   → Run: pip install numpy")

# Test 3: Try importing simulation module
print("\n3. Testing simulation module import...")
try:
    sys.path.insert(0, str(sim_path))
    from simulate_game import Card, simulate_game
    print("   ✓ Successfully imported simulate_game module")
    print(f"   - Card class: {Card}")
    print(f"   - simulate_game function: {simulate_game}")
except Exception as e:
    print(f"   ✗ Failed to import: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Try importing deck_simulator integration
print("\n4. Testing deck_simulator integration...")
try:
    from src.simulation.deck_simulator import simulate_deck_effectiveness
    print("   ✓ Successfully imported deck_simulator module")
except Exception as e:
    print(f"   ✗ Failed to import: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Try creating a test card
print("\n5. Testing card creation...")
try:
    from src.simulation.deck_simulator import convert_card_to_simulation_format

    test_card = {
        'name': 'Test Card',
        'type_line': 'Creature — Human',
        'mana_cost': '{2}{G}',
        'power': '2',
        'toughness': '2',
        'oracle_text': 'When Test Card enters the battlefield, draw a card.',
        'is_commander': False
    }

    sim_card = convert_card_to_simulation_format(test_card)
    print(f"   ✓ Successfully converted test card")
    print(f"   - Name: {sim_card.name}")
    print(f"   - Type: {sim_card.type}")
    print(f"   - Power: {sim_card.power}")
except Exception as e:
    print(f"   ✗ Failed to convert card: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Try running a mini simulation
print("\n6. Testing mini simulation...")
try:
    from src.simulation.deck_simulator import simulate_deck_effectiveness

    # Create a minimal test deck
    test_cards = []
    for i in range(50):
        test_cards.append({
            'name': f'Test Card {i}',
            'type_line': 'Land',
            'mana_cost': '',
            'oracle_text': '{T}: Add {G}.',
            'produced_mana': ['G'],
            'is_commander': False
        })

    test_commander = {
        'name': 'Test Commander',
        'type_line': 'Legendary Creature — Human Warrior',
        'mana_cost': '{2}{G}{G}',
        'power': '4',
        'toughness': '4',
        'oracle_text': 'Trample',
        'is_commander': True
    }

    print("   Running 10 test games...")
    result = simulate_deck_effectiveness(
        cards=test_cards,
        commander=test_commander,
        num_games=10,
        max_turns=5,
        verbose=False
    )

    if 'error' in result.get('summary', {}):
        print(f"   ✗ Simulation failed: {result['summary']['error']}")
    else:
        print(f"   ✓ Simulation completed successfully!")
        print(f"   - Total damage: {result['summary']['total_damage_10_turns']}")
        print(f"   - Avg damage/turn: {result['summary']['avg_damage_per_turn']}")

except Exception as e:
    print(f"   ✗ Simulation test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("DIAGNOSTIC COMPLETE")
print("="*70)
print("\nIf all tests pass, the simulation should work when loading decks.")
print("If tests fail, check the error messages above for missing dependencies.")
