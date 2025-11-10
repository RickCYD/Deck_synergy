#!/usr/bin/env python3
"""
Minimal test to verify simulation is working correctly
"""

import sys
from pathlib import Path

# Add Simulation directory to path
simulation_path = Path(__file__).parent / "Simulation"
sys.path.insert(0, str(simulation_path))

from simulate_game import Card
from run_simulation import run_simulations

print("="*60)
print("TESTING SIMULATION WITH MINIMAL DECK")
print("="*60)

# Create a simple aggressive deck that should deal good damage
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
        has_haste=False  # required positional arg
    ))

# Add efficient creatures
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
        has_haste=True  # required positional arg - Give haste so they can attack immediately
    ))

# Add bigger creatures
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

# Add some big threats
for i in range(1, 6):
    cards.append(Card(
        name=f"Shivan Dragon {i}",
        type="Creature",
        mana_cost="{4}{R}{R}",
        power=5,
        toughness=5,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=True,
        has_trample=True
    ))

# Add some card draw
for i in range(1, 5):
    cards.append(Card(
        name=f"Divination {i}",
        type="Sorcery",
        mana_cost="{2}{U}",
        power=None,
        toughness=None,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False,  # required positional arg
        draw_cards=2
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

print(f"\nDeck composition:")
print(f"  - 35 lands")
print(f"  - 10 x 2/1 creatures with haste (1 mana)")
print(f"  - 10 x 3/3 creatures with haste (4 mana)")
print(f"  - 5 x 5/5 creatures with haste+trample (6 mana)")
print(f"  - 4 card draw spells")
print(f"  - 1 commander (3/3 haste)")
print(f"\nTotal: {len(cards)} cards")

print("\nRunning 100 simulations (10 turns each)...")
print("-"*60)

# Run simulations
summary_df, commander_dist, creature_power, interaction_summary = run_simulations(
    cards=cards,
    commander_card=commander,
    num_games=100,
    max_turns=10,
    verbose=False,
    log_dir=None,
    num_workers=1
)

# Calculate metrics
total_damage = [0] + summary_df['Avg Total Damage'].tolist()
combat_damage = [0] + summary_df['Avg Combat Damage'].tolist()
drain_damage = [0] + summary_df['Avg Drain Damage'].tolist()
total_power = [0] + summary_df['Avg Total Power'].tolist()

total_damage_10_turns = sum(total_damage[:11])
avg_damage_per_turn = total_damage_10_turns / 10
peak_power = max(total_power)

# Get commander cast turn
commander_avg_turn = None
if not commander_dist.empty:
    weighted_sum = sum(turn * count for turn, count in commander_dist.items())
    total_count = commander_dist.sum()
    if total_count > 0:
        commander_avg_turn = weighted_sum / total_count

print("\n" + "="*60)
print("RESULTS")
print("="*60)

print(f"\nTotal Damage (10 turns):     {total_damage_10_turns:.1f}")
print(f"  - Combat Damage:           {sum(combat_damage[:11]):.1f}")
print(f"  - Drain Damage:            {sum(drain_damage[:11]):.1f}")
print(f"\nAverage Damage per Turn:     {avg_damage_per_turn:.2f}")
print(f"Peak Board Power:            {peak_power:.1f}")
if commander_avg_turn:
    print(f"Commander Avg Cast Turn:     {commander_avg_turn:.1f}")
else:
    print(f"Commander Avg Cast Turn:     N/A")

print("\n" + "="*60)
print("VALIDATION")
print("="*60)

issues = []

# An aggressive deck with haste creatures should deal significant damage
if total_damage_10_turns < 30:
    issues.append(f"⚠️  Total damage is too low ({total_damage_10_turns:.1f}) - expected > 30 for aggressive deck")

# Peak power should be at least 10 with this many creatures
if peak_power < 10:
    issues.append(f"⚠️  Peak power is too low ({peak_power:.1f}) - expected > 10")

# Commander should be cast early-ish
if commander_avg_turn and commander_avg_turn > 6:
    issues.append(f"⚠️  Commander cast too late ({commander_avg_turn:.1f}) - expected < 6")

if issues:
    print("\n❌ ISSUES FOUND:")
    for issue in issues:
        print(issue)
    print("\nThe simulation may not be working correctly!")
    sys.exit(1)
else:
    print("\n✅ All metrics look reasonable!")
    print("Simulation is working correctly!")

print("\nTurn-by-turn breakdown:")
print(f"\n{'Turn':<6} {'Combat':<8} {'Power':<8}")
print("-" * 25)

for turn in range(1, 11):
    combat = combat_damage[turn] if turn < len(combat_damage) else 0
    power = total_power[turn] if turn < len(total_power) else 0
    print(f"{turn:<6} {combat:<8.2f} {power:<8.2f}")
