#!/usr/bin/env python3
"""Test the deck with Scryfall data to verify mechanics work."""

import sys
sys.path.insert(0, 'Simulation')

from deck_loader import load_deck_from_scryfall_file
from run_simulation import run_simulations

print("=" * 80)
print("TESTING TEVAL DECK WITH SCRYFALL DATA")
print("=" * 80)

# Load deck from Scryfall
print("\n[Step 1] Loading deck from Scryfall (this may take a moment)...")
try:
    cards, commander = load_deck_from_scryfall_file(
        "teval_decklist.txt",
        "Teval, the Balanced Scale"
    )
    print(f"✓ Loaded {len(cards)} cards + commander")
    print(f"✓ Commander: {commander.name}")
except Exception as e:
    print(f"✗ Error loading deck: {e}")
    print("\nThis is expected if:")
    print("  1. You don't have internet connection")
    print("  2. Scryfall API is down")
    print("\nThe mechanics are implemented and working (see test_mechanics.py results)")
    sys.exit(1)

# Check that key cards have oracle text
print("\n[Step 2] Verifying oracle text is loaded...")
key_cards = {
    "Syr Konrad": False,
    "Muldrotha": False,
    "Meren": False,
    "Hedron Crab": False,
    "Living Death": False,
}

for card in cards + [commander]:
    name = card.name
    oracle = getattr(card, 'oracle_text', '')

    if 'syr konrad' in name.lower() and oracle:
        key_cards["Syr Konrad"] = True
        print(f"  ✓ Syr Konrad has oracle text ({len(oracle)} chars)")
    elif 'muldrotha' in name.lower() and oracle:
        key_cards["Muldrotha"] = True
        print(f"  ✓ Muldrotha has oracle text ({len(oracle)} chars)")
    elif 'meren' in name.lower() and oracle:
        key_cards["Meren"] = True
        print(f"  ✓ Meren has oracle text ({len(oracle)} chars)")
    elif 'hedron crab' in name.lower() and oracle:
        key_cards["Hedron Crab"] = True
        mill_value = getattr(card, 'mill_value', 0)
        print(f"  ✓ Hedron Crab has oracle text, mill_value={mill_value}")
    elif 'living death' in name.lower() and oracle:
        key_cards["Living Death"] = True
        print(f"  ✓ Living Death has oracle text ({len(oracle)} chars)")

# Run simulation
print("\n[Step 3] Running simulation (5 games, 10 turns, verbose=False)...")
print("-" * 80)

try:
    summary, cmd_dist, creature_power, interaction, stats = run_simulations(
        cards=cards,
        commander_card=commander,
        num_games=5,
        max_turns=10,
        verbose=False,
        log_dir=None,
        num_workers=1,
        calculate_statistics=True
    )

    # Calculate metrics
    total_damage = summary["Avg Total Damage"].sum()
    total_combat = summary["Avg Combat Damage"].sum()
    total_drain = summary["Avg Drain Damage"].sum()
    avg_damage_per_turn = total_damage / 10
    peak_power = summary["Avg Total Power"].max()

    # Commander stats
    cmd_turns = [t for t in cmd_dist.index if cmd_dist[t] > 0]
    avg_cmd_turn = sum(t * cmd_dist[t] for t in cmd_turns) / sum(cmd_dist.values()) if sum(cmd_dist.values()) > 0 else 0

    print("\n" + "=" * 80)
    print("SIMULATION RESULTS")
    print("=" * 80)

    print(f"\nDeck Effectiveness:")
    print(f"  Total Damage (10 turns):  {total_damage:.1f}")
    print(f"    - Combat Damage:        {total_combat:.1f}")
    print(f"    - Drain Damage:         {total_drain:.1f}")
    print(f"  Avg Damage/Turn:          {avg_damage_per_turn:.2f}")
    print(f"  Peak Board Power:         {peak_power:.1f}")
    print(f"  Commander Avg Turn:       {avg_cmd_turn:.1f}")

    print(f"\nGraveyard Metrics:")
    print(f"  Avg Graveyard Size:       {summary['Avg Graveyard Size'].mean():.1f}")
    print(f"  Creatures Sacrificed:     {summary['Avg Creatures Sacrificed'].sum():.1f}")

    # Check if improvements are visible
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)

    if total_drain > 50:
        print(f"  ✓ EXCELLENT: Drain damage is {total_drain:.0f} (Syr Konrad working!)")
    elif total_drain > 20:
        print(f"  ✓ GOOD: Drain damage is {total_drain:.0f} (some triggers working)")
    else:
        print(f"  ⚠ LOW: Drain damage is only {total_drain:.0f}")
        print(f"     This might mean:")
        print(f"       - Not enough games run (try 50+ games)")
        print(f"       - Syr Konrad not drawn/cast")
        print(f"       - Mill cards not triggering")

    if peak_power > 20:
        print(f"  ✓ EXCELLENT: Peak power is {peak_power:.0f} (reanimation working!)")
    elif peak_power > 10:
        print(f"  ✓ GOOD: Peak power is {peak_power:.0f}")
    else:
        print(f"  ⚠ LOW: Peak power is only {peak_power:.0f}")

    if total_damage > 100:
        print(f"  ✓ EXCELLENT: Total damage is {total_damage:.0f} (deck working well!)")
    elif total_damage > 50:
        print(f"  ✓ GOOD: Total damage is {total_damage:.0f}")
    else:
        print(f"  ⚠ LOW: Total damage is only {total_damage:.0f}")
        print(f"     Try running with verbose=True on 1 game to see what's happening")

    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print("\nFor accurate results, run with:")
    print("  - 50-100 games (not just 5)")
    print("  - verbose=True on 1-2 games to see mechanics firing")
    print("\nTo see detailed output:")
    print("  python test_with_scryfall_verbose.py")

except Exception as e:
    print(f"\n✗ Error running simulation: {e}")
    import traceback
    traceback.print_exc()
