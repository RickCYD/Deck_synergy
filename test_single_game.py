#!/usr/bin/env python3
"""
Run a single game with verbose output to debug simulation
"""

import sys
from pathlib import Path

# Add Simulation directory to path
simulation_path = Path(__file__).parent / "Simulation"
sys.path.insert(0, str(simulation_path))

from simulate_game import Card, simulate_game

print("="*60)
print("SINGLE GAME DEBUG TEST")
print("="*60)

# Create simple deck
cards = []

# Add 35 lands
for i in range(35):
    cards.append(Card(
        name=f"Mountain {i+1}",
        type="Basic Land",
        mana_cost="",
        power=None,
        toughness=None,
        produces_colors=["R"],
        mana_production=1,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False
    ))

# Add 10 efficient 2/1 haste creatures for 1 mana
for i in range(1, 11):
    cards.append(Card(
        name=f"Savannah Lions {i}",
        type="Creature",
        mana_cost="{W}",
        power=2,
        toughness=1,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True
    ))

# Add 10 bigger creatures
for i in range(1, 11):
    cards.append(Card(
        name=f"Hill Giant {i}",
        type="Creature",
        mana_cost="{3}{R}",
        power=3,
        toughness=3,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True
    ))

# Create commander
commander = Card(
    name="Zurgo Stormrender",
    type="Creature",
    mana_cost="{2}{R}{W}",
    power=3,
    toughness=3,
    produces_colors=[],
    mana_production=0,
    etb_tapped=False,
    etb_tapped_conditions={},
    has_haste=True,
    is_commander=True,
    is_legendary=True
)

print("\nRunning 1 game with verbose output...")
print("-"*60)

# Run single game with verbose output
result = simulate_game(cards, commander, max_turns=10, verbose=True)

print("\n" + "="*60)
print("GAME RESULTS")
print("="*60)

combat_damage = result.get('combat_damage', [])
total_power = result.get('total_power', [])

print(f"\nTotal combat damage over 10 turns: {sum(combat_damage[1:11]):.1f}")
print(f"Peak power: {max(total_power):.1f}")

print("\nTurn-by-turn:")
print(f"{'Turn':<6} {'Damage':<10} {'Power':<10}")
print("-" * 30)
for turn in range(1, 11):
    dmg = combat_damage[turn] if turn < len(combat_damage) else 0
    pwr = total_power[turn] if turn < len(total_power) else 0
    print(f"{turn:<6} {dmg:<10.1f} {pwr:<10.1f}")
