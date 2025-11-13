#!/usr/bin/env python3
"""Debug script to analyze Teval deck simulation in detail."""

import sys
import json
from pathlib import Path

# Add Simulation directory to path
sys.path.insert(0, str(Path(__file__).parent / "Simulation"))

from deck_loader import load_deck_from_local_database
from simulate_game import simulate_game
import random

# Teval deck list - just the key cards to test
DECK_LIST = """
1 Teval, the Balanced Scale
1 Sol Ring
1 Arcane Signet
1 Muldrotha, the Gravetide
1 Meren of Clan Nel Toth
1 Living Death
1 Eldrazi Monument
1 Syr Konrad, the Grim
1 Hedron Crab
1 Stitcher's Supplier
1 Sidisi, Brood Tyrant
1 Gravecrawler
1 Dread Return
1 Eternal Witness
1 Command Tower
10 Forest
10 Swamp
10 Island
"""

def parse_deck_list(deck_text):
    """Parse a deck list into card names."""
    cards = []
    for line in deck_text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        parts = line.split(' ', 1)
        if len(parts) == 2:
            count = int(parts[0])
            name = parts[1]
            for _ in range(count):
                cards.append(name)
    return cards

def main():
    print("="*80)
    print("TEVAL DECK DEBUG - SINGLE GAME ANALYSIS")
    print("="*80)

    # Parse deck list
    card_names = parse_deck_list(DECK_LIST)
    print(f"\nParsed {len(card_names)} cards from deck list")

    # Load from local database
    print("Loading cards from local database...")
    try:
        cards, commander = load_deck_from_local_database(
            card_names,
            "Teval, the Balanced Scale",
            str(Path(__file__).parent / "data" / "cards" / "cards-preprocessed.json")
        )
        print(f"✓ Loaded {len(cards)} cards + commander")
    except Exception as e:
        print(f"✗ Error loading cards: {e}")
        import traceback
        traceback.print_exc()
        return

    # Check what we loaded
    print("\nKey cards loaded:")
    key_cards = ['Muldrotha', 'Meren', 'Living Death', 'Eldrazi Monument',
                 'Syr Konrad', 'Hedron Crab', 'Gravecrawler', 'Sol Ring']
    for key in key_cards:
        found = [c for c in cards if key.lower() in c.name.lower()]
        if found:
            print(f"  ✓ {found[0].name}")
        else:
            print(f"  ✗ {key} NOT FOUND")

    # Run a single game with verbose output
    print("\n" + "="*80)
    print("RUNNING SINGLE GAME (VERBOSE)")
    print("="*80)

    random.seed(42)  # Deterministic
    result = simulate_game(cards, commander, max_turns=10, verbose=True)

    # Print summary
    print("\n" + "="*80)
    print("GAME SUMMARY")
    print("="*80)

    print(f"\nTotal Damage: {sum(result['total_damage']):.1f}")
    print(f"  Combat: {sum(result['combat_damage']):.1f}")
    print(f"  Drain: {sum(result['drain_damage']):.1f}")

    print(f"\nPeak Power: {max(result['total_power']):.1f}")
    print(f"Cards Played: {sum(result['cards_played']):.0f}")
    print(f"Graveyard Size (end): {result['graveyard_size'][-1]:.0f}")

    print("\nTurn-by-turn:")
    print("  Turn | Mana | Power | Combat | Drain | Total DMG")
    print("  -----|------|-------|--------|-------|----------")
    for i in range(1, 11):
        mana = result['total_mana'][i]
        power = result['total_power'][i]
        combat = result['combat_damage'][i]
        drain = result['drain_damage'][i]
        total = result['total_damage'][i]
        print(f"   {i:2d}  |  {mana:3.0f} |  {power:4.0f} |  {combat:5.1f} |  {drain:4.1f} |  {total:8.1f}")

if __name__ == "__main__":
    main()
