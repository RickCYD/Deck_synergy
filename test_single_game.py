#!/usr/bin/env python3
"""
Test a single game with verbose output to debug token/drain issues
"""

import sys
from pathlib import Path

# Add Simulation directory to path
simulation_path = Path(__file__).parent / "Simulation"
sys.path.insert(0, str(simulation_path))

from src.api.local_cards import get_card_by_name, load_local_database
from simulate_game import simulate_game, Card
from src.simulation.deck_simulator import convert_card_to_simulation_format

print("Loading database...")
load_local_database()

# Key cards to test
test_cards = [
    "Kykar, Wind's Fury",      # Creates tokens on noncreature spell cast
    "Storm-Kiln Artist",        # Creates Treasure on instant/sorcery cast
    "Impact Tremors",           # Deals damage when creature enters
    "Warleader's Call",         # +1/+1 anthem + damage on creature enter
    "Lightning Bolt",           # Instant spell (should trigger Kykar/Storm-Kiln)
    "Sol Ring",                 # Mana rock
    "Island", "Mountain", "Plains",  # Lands
]

# Load and convert cards
sim_cards = []
for card_name in test_cards:
    card_data = get_card_by_name(card_name)
    if card_data:
        sim_card = convert_card_to_simulation_format(card_data)
        sim_cards.append(sim_card)
        print(f"✓ Loaded: {card_name}")

        # Show triggers
        if hasattr(sim_card, 'triggered_abilities') and sim_card.triggered_abilities:
            print(f"  Triggers: {[t.description for t in sim_card.triggered_abilities]}")
    else:
        print(f"✗ Not found: {card_name}")

# Create a simple commander
commander = Card(
    name="Test Commander",
    type="Legendary Creature",
    mana_cost="{2}{U}{R}{W}",
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

# Add more lands to ensure we can cast spells
for _ in range(15):
    sim_cards.append(convert_card_to_simulation_format(get_card_by_name("Island")))
    sim_cards.append(convert_card_to_simulation_format(get_card_by_name("Mountain")))

print(f"\n{'='*70}")
print("RUNNING SINGLE GAME (VERBOSE)")
print(f"{'='*70}\n")

# Run one game with verbose output
metrics = simulate_game(
    deck_cards=sim_cards,
    commander_card=commander,
    max_turns=10,
    verbose=True  # Enable verbose output
)

print(f"\n{'='*70}")
print("FINAL METRICS")
print(f"{'='*70}")
print(f"Available metrics: {metrics.keys()}")
for key, value in metrics.items():
    if isinstance(value, list):
        print(f"{key}: {sum(value)} (total of {len(value)} turns)")
    else:
        print(f"{key}: {value}")
