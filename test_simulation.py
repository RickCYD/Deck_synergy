#!/usr/bin/env python3
"""
Test simulation directly with a deck
"""

from src.api.local_cards import get_card_by_name, load_local_database
from src.synergy_engine.analyzer import analyze_deck_synergies
import sys

# Load database
print("Loading card database...")
if not load_local_database():
    print("ERROR: Could not load card database")
    sys.exit(1)

# Load the deck from file
deck_file = "/tmp/sokka_deck.txt"
print(f"\nLoading deck from {deck_file}...")

with open(deck_file, 'r') as f:
    deck_text = f.read()

# Parse cards
lines = deck_text.strip().split('\n')
cards = []

category_headers = {
    'commander', 'anthem', 'artifact', 'burn', 'copy', 'creature', 'draw',
    'evasion', 'finisher', 'instant', 'land', 'lifegain', 'protection',
    'pump', 'ramp', 'recursion', 'removal', 'sorcery', 'tokens',
    'enchantment', 'planeswalker', 'utility', 'tribal', 'combo'
}

import re
for line in lines:
    line = line.strip()
    if not line or line.startswith('#') or line.startswith('//'):
        continue

    if not re.match(r'^\d+', line):
        if line.lower() in category_headers:
            continue

    match = re.match(r'(\d+)x?\s+(.+)', line)
    if match:
        quantity = int(match.group(1))
        card_name = match.group(2).strip()

        card = get_card_by_name(card_name)
        if card:
            if quantity == 1 and not cards:
                card['is_commander'] = True

            for _ in range(quantity):
                cards.append(card)

print(f"✓ Loaded {len(cards)} cards")
commander = next((c for c in cards if c.get('is_commander')), None)
if commander:
    print(f"✓ Commander: {commander['name']}")

# Run simulation
print("\n" + "="*70)
print("RUNNING SIMULATION")
print("="*70)

results = analyze_deck_synergies(
    cards,
    run_simulation=True,
    num_simulation_games=100,
    include_three_way=False
)

# Extract simulation results
if 'simulation' in results and results['simulation']:
    sim = results['simulation']
    print("\n" + "="*70)
    print("SIMULATION RESULTS")
    print("="*70)

    # Print summary
    if 'summary' in sim:
        summary = sim['summary']
        print(f"\nTotal Damage (all games): {summary.get('total_damage', 'N/A')}")
        print(f"Average Damage per Game: {summary.get('avg_damage_per_game', 'N/A'):.2f}")
        print(f"Peak Damage: {summary.get('peak_damage', 'N/A')}")
        print(f"Average Mana Generated: {summary.get('avg_mana_generated', 'N/A'):.2f}")
        print(f"Commander Cast Success Rate: {summary.get('commander_cast_rate', 'N/A'):.1f}%")

    # Print turn-by-turn data
    if 'summary_df' in sim:
        df = sim['summary_df']
        print("\n📊 Turn-by-Turn Averages:")
        print(df.to_string(index=False))

else:
    print("\n⚠️ No simulation results found")
    print("Results keys:", results.keys() if isinstance(results, dict) else "Not a dict")

print("\n" + "="*70)
