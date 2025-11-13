#!/usr/bin/env python3
"""
Debug why creatures aren't being cast in the simulation.
"""

import sys
sys.path.insert(0, 'Simulation')

from deck_loader import load_deck_from_csv
from simulate_game import Card, Mana_utils
import random

# Load deck
cards, commander, _ = load_deck_from_csv("zurgo_deck.csv")

print("="*100)
print("DEBUGGING CREATURE CASTING")
print("="*100)

# Get sample creatures from deck
creatures = [c for c in cards if 'Creature' in c.type][:5]

print(f"\nFound {len(creatures)} creatures in deck. Testing first 5:")

for creature in creatures:
    print(f"\n{creature.name}:")
    print(f"  Type: {creature.type}")
    print(f"  Mana cost: {creature.mana_cost}")
    print(f"  Power/Toughness: {creature.power}/{creature.toughness}")

    # Test if we can parse the mana cost
    try:
        cols, gen = Mana_utils.parse_req(creature.mana_cost)
        total_cost = gen + len(cols)
        print(f"  Parsed cost: {gen} generic + {cols} colored = {total_cost} total")
    except Exception as e:
        print(f"  ERROR parsing cost: {e}")

    # Test if castable with different mana pools
    for mana_count in [1, 2, 3, 4, 5]:
        mana_pool = [("Any",)] * mana_count
        try:
            castable = Mana_utils.can_pay(creature.mana_cost, mana_pool)
            if castable:
                print(f"  ✓ Castable with {mana_count} mana")
                break
        except Exception as e:
            print(f"  ERROR checking castability with {mana_count} mana: {e}")

print("\n" + "="*100)
print("TESTING SPECIFIC SCENARIO FROM VERBOSE OUTPUT")
print("="*100)

# Test the specific Turn 3 scenario where Elas il-Kor wasn't cast
# Turn 3: 3 lands producing mana
print("\nTurn 3 scenario:")
print("  Mana available: 3 (from Plains, Nomad Outpost, Canyon Slough)")

# Find Elas il-Kor
elas = next((c for c in cards if "Elas il-Kor" in c.name), None)
if elas:
    print(f"\n  Card in hand: {elas.name}")
    print(f"    Mana cost: {elas.mana_cost}")
    print(f"    Type: {elas.type}")

    # Test with 3 mana
    mana_pool = [("Any",)] * 3
    try:
        castable = Mana_utils.can_pay(elas.mana_cost, mana_pool)
        print(f"    Can pay with 3 'Any' mana? {castable}")

        if not castable:
            # Try to understand WHY
            cols, gen = Mana_utils.parse_req(elas.mana_cost)
            print(f"    Required: {gen} generic + {cols} colored")
            print(f"    Available: 3 Any")
            print(f"    ERROR: Should be castable but can_pay returned False!")
    except Exception as e:
        print(f"    ERROR: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*100)
print("TESTING MANA PRODUCTION FROM LANDS")
print("="*100)

# Test if lands are producing mana correctly
test_lands = ["Plains", "Nomad Outpost", "Canyon Slough"]
for land_name in test_lands:
    land = next((c for c in cards if c.name == land_name), None)
    if land:
        print(f"\n{land.name}:")
        print(f"  Type: {land.type}")
        print(f"  Mana production: {land.mana_production}")
        print(f"  Produces colors: {land.produces_colors}")
        print(f"  ETB tapped: {land.etb_tapped}")
    else:
        print(f"\n{land_name}: NOT FOUND IN DECK")

EOF
