#!/usr/bin/env python3
"""Test Teval with verbose output to see abilities trigger"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "Simulation"))

from src.api.local_cards import load_local_database, get_card_by_name
from Simulation.simulate_game import simulate_game, Card
import random

# Load database
load_local_database()

# Get Teval
teval_data = get_card_by_name("Teval, the Balanced Scale")
teval_card = Card(
    name=teval_data['name'],
    type=teval_data['type_line'],
    mana_cost=teval_data['mana_cost'],
    power=teval_data.get('power', 4),
    toughness=teval_data.get('toughness', 4),
    produces_colors=[],
    mana_production=0,
    etb_tapped=False,
    etb_tapped_conditions={},
    has_haste=False,
    oracle_text=teval_data['oracle_text'],
    is_commander=True
)

# Create a simple deck
deck = []

# 20 Forests
for _ in range(20):
    deck.append(Card(
        name="Forest",
        type="Basic Land — Forest",
        mana_cost="",
        power=None,
        toughness=None,
        produces_colors=['G'],
        mana_production=1,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False
    ))

# 10 Swamps
for _ in range(10):
    deck.append(Card(
        name="Swamp",
        type="Basic Land — Swamp",
        mana_cost="",
        power=None,
        toughness=None,
        produces_colors=['B'],
        mana_production=1,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False
    ))

# 5 Islands
for _ in range(5):
    deck.append(Card(
        name="Island",
        type="Basic Land — Island",
        mana_cost="",
        power=None,
        toughness=None,
        produces_colors=['U'],
        mana_production=1,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False
    ))

# Sol Ring
sol_ring_data = get_card_by_name("Sol Ring")
deck.append(Card(
    name="Sol Ring",
    type="Artifact",
    mana_cost="{1}",
    power=None,
    toughness=None,
    produces_colors=['C'],
    mana_production=2,
    etb_tapped=False,
    etb_tapped_conditions={},
    has_haste=False,
    oracle_text=sol_ring_data['oracle_text']
))

# Ob Nixilis
ob_data = get_card_by_name("Ob Nixilis, the Fallen")
deck.append(Card(
    name="Ob Nixilis, the Fallen",
    type="Legendary Creature — Demon",
    mana_cost="{3}{B}{B}",
    power=3,
    toughness=3,
    produces_colors=[],
    mana_production=0,
    etb_tapped=False,
    etb_tapped_conditions={},
    has_haste=False,
    oracle_text=ob_data['oracle_text']
))

# Syr Konrad
konrad_data = get_card_by_name("Syr Konrad, the Grim")
deck.append(Card(
    name="Syr Konrad, the Grim",
    type="Legendary Creature — Human Knight",
    mana_cost="{3}{B}{B}",
    power=5,
    toughness=4,
    produces_colors=[],
    mana_production=0,
    etb_tapped=False,
    etb_tapped_conditions={},
    has_haste=False,
    oracle_text=konrad_data['oracle_text']
))

# Add some filler creatures
for i in range(60):
    deck.append(Card(
        name=f"Grizzly Bears {i}",
        type="Creature — Bear",
        mana_cost="{1}{G}",
        power=2,
        toughness=2,
        produces_colors=[],
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions={},
        has_haste=False
    ))

print("="*80)
print("TESTING TEVAL ABILITIES - VERBOSE MODE")
print("="*80)
print(f"Deck: {len(deck)} cards")
print(f"Commander: {teval_card.name}")
print("\n" + "="*80)
print("RUNNING ONE GAME - VERBOSE OUTPUT")
print("="*80 + "\n")

random.seed(42)
result = simulate_game(deck, teval_card, max_turns=10, verbose=True)

print("\n" + "="*80)
print("FINAL RESULTS")
print("="*80)

total_damage = sum(result['combat_damage'][1:])
total_drain = sum(result.get('drain_damage', [0]*11)[1:])
total_all = total_damage + total_drain
peak_power = max(result['total_power'])
commander_turn = result.get('commander_cast_turn')
tokens_created = sum(result.get('tokens_created', [0]*11)[1:])

print(f"\nTotal Damage: {total_all:.1f}")
print(f"  Combat: {total_damage:.1f}")
print(f"  Drain: {total_drain:.1f}")
print(f"Peak Power: {peak_power:.1f}")
print(f"Commander Turn: {commander_turn}")
print(f"Tokens Created: {tokens_created:.0f}")
