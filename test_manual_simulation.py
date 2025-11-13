#!/usr/bin/env python3
"""Manually create a test deck to see what simulation does."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "Simulation"))

from simulate_game import Card, simulate_game
import random

def create_test_deck():
    """Create a minimal test deck manually."""
    cards = []

    # Add 35 basic lands
    for i in range(20):
        cards.append(Card(
            name="Forest",
            type="Basic Land",
            mana_cost="",
            power=0,
            toughness=0,
            produces_colors="G",
            mana_production=1,
            etb_tapped=False,
            etb_tapped_conditions=[],
            has_haste=False
        ))

    for i in range(15):
        cards.append(Card(
            name="Swamp",
            type="Basic Land",
            mana_cost="",
            power=0,
            toughness=0,
            produces_colors="B",
            mana_production=1,
            etb_tapped=False,
            etb_tapped_conditions=[],
            has_haste=False
        ))

    # Add Sol Ring
    cards.append(Card(
        name="Sol Ring",
        type="Artifact",
        mana_cost="{1}",
        power=0,
        toughness=0,
        produces_colors="",
        mana_production=2,
        etb_tapped=False,
        etb_tapped_conditions=[],
        has_haste=False
    ))

    # Add some 2-mana 2/2 creatures
    for i in range(20):
        cards.append(Card(
            name=f"Bear {i}",
            type="Creature — Bear",
            mana_cost="{1}{G}",
            power=2,
            toughness=2,
            produces_colors="",
            mana_production=0,
            etb_tapped=False,
            etb_tapped_conditions=[],
            has_haste=False
        ))

    # Add some 3-mana 3/3 creatures
    for i in range(10):
        cards.append(Card(
            name=f"Beast {i}",
            type="Creature — Beast",
            mana_cost="{2}{G}",
            power=3,
            toughness=3,
            produces_colors="",
            mana_production=0,
            etb_tapped=False,
            etb_tapped_conditions=[],
            has_haste=False
        ))

    # Add a 4-mana commander
    commander = Card(
        name="Test Commander",
        type="Legendary Creature",
        mana_cost="{2}{G}{G}",
        power=4,
        toughness=4,
        produces_colors="",
        mana_production=0,
        etb_tapped=False,
        etb_tapped_conditions=[],
        has_haste=False,
        is_commander=True
    )

    return cards, commander

def main():
    print("="*80)
    print("MANUAL TEST - BASIC CREATURE DECK")
    print("="*80)

    cards, commander = create_test_deck()
    print(f"\nCreated deck with {len(cards)} cards + commander")
    print(f"  35 lands")
    print(f"  1 Sol Ring")
    print(f"  20 2/2 creatures for 2 mana")
    print(f"  10 3/3 creatures for 3 mana")
    print(f"  Commander: 4/4 for 4 mana")

    print("\n" + "="*80)
    print("RUNNING SINGLE GAME (VERBOSE)")
    print("="*80 + "\n")

    random.seed(42)
    result = simulate_game(cards, commander, max_turns=10, verbose=True)

    print("\n" + "="*80)
    print("GAME SUMMARY")
    print("="*80)

    total_damage = sum(result['total_damage'])
    combat_damage = sum(result['combat_damage'])
    peak_power = max(result['total_power'])
    cards_played = sum(result['cards_played'])

    print(f"\nTotal Damage (10 turns): {total_damage:.1f}")
    print(f"  Combat Damage: {combat_damage:.1f}")
    print(f"Peak Board Power: {peak_power:.1f}")
    print(f"Total Cards Played: {cards_played:.0f}")

    print("\nTurn-by-turn:")
    print("  Turn | Mana | Cards | Power | Damage")
    print("  -----|------|-------|-------|-------")
    for i in range(1, 11):
        mana = result['total_mana'][i]
        played = result['cards_played'][i]
        power = result['total_power'][i]
        damage = result['combat_damage'][i]
        print(f"   {i:2d}  |  {mana:3.0f} |   {played:2.0f}  |  {power:4.0f} |  {damage:5.1f}")

    print("\n" + "="*80)
    print("EXPECTED vs ACTUAL")
    print("="*80)
    print("\nA basic green deck with ramp and efficient creatures should:")
    print(f"  - Play 1-2 cards per turn → Actual: {cards_played/10:.1f} avg")
    print(f"  - Build 15-30+ power by turn 10 → Actual: {peak_power:.0f}")
    print(f"  - Deal 30-60+ damage in 10 turns → Actual: {total_damage:.0f}")
    print(f"  - Have 4-6 mana by turn 5 → Actual: {result['total_mana'][5]:.0f}")

    if total_damage < 30:
        print("\n✗ PROBLEM: Damage is too low!")
        print("  This indicates the simulation is not playing creatures or attacking properly.")
    elif peak_power < 15:
        print("\n✗ PROBLEM: Board presence is too low!")
        print("  This indicates creatures aren't being played or staying on board.")
    else:
        print("\n✓ Numbers look reasonable for a basic deck!")

if __name__ == "__main__":
    main()
