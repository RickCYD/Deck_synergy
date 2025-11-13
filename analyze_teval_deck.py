#!/usr/bin/env python3
"""Analyze the Teval deck to understand why damage is low."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "Simulation"))

from deck_loader import load_deck_from_scryfall_file
from simulate_game import simulate_game
import random

def main():
    print("="*80)
    print("TEVAL DECK ANALYSIS - Investigating Low Damage Output")
    print("="*80)

    print("\n[1/4] Loading deck from file...")
    try:
        cards, commander, names = load_deck_from_scryfall_file('teval_decklist.txt', 'Teval, the Balanced Scale')
        print(f"✓ Loaded {len(cards)} cards + commander")
        print(f"  Commander: {commander.name if commander else 'None'}")

        # Count card types
        lands = [c for c in cards if 'Land' in c.type]
        creatures = [c for c in cards if 'Creature' in c.type]
        artifacts = [c for c in cards if 'Artifact' in c.type]
        instants = [c for c in cards if 'Instant' in c.type]
        sorceries = [c for c in cards if 'Sorcery' in c.type]

        print(f"\n  Deck Composition:")
        print(f"    Lands: {len(lands)}")
        print(f"    Creatures: {len(creatures)}")
        print(f"    Artifacts: {len(artifacts)}")
        print(f"    Instants: {len(instants)}")
        print(f"    Sorceries: {len(sorceries)}")
        print(f"    TOTAL: {len(cards)}")

        # Check land count
        if len(lands) < 30:
            print(f"\n  ⚠️  WARNING: Only {len(lands)} lands! Commander decks typically need 36-38 lands.")
            print(f"      This will cause severe mana problems!")

    except Exception as e:
        print(f"✗ Failed to load deck: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n[2/4] Running detailed simulation (1 game, verbose)...")
    print("="*80)

    random.seed(42)  # Deterministic for analysis
    result = simulate_game(cards, commander, max_turns=10, verbose=True)

    print("\n" + "="*80)
    print("[3/4] ANALYZING RESULTS")
    print("="*80)

    total_damage = sum(result.get('combat_damage', [0]*11)[1:11])
    drain_damage = sum(result.get('drain_damage', [0]*11)[1:11])
    total_all_damage = total_damage + drain_damage
    peak_power = max(result.get('total_power', [0]*11))
    cards_played = sum(result.get('cards_played', [0]*11)[1:11])
    commander_cast_turn = result.get('commander_cast_turn')

    print(f"\nDeck Effectiveness Metrics:")
    print(f"  Total Damage (10 turns): {total_all_damage:.1f}")
    print(f"    - Combat Damage: {total_damage:.1f}")
    print(f"    - Drain Damage: {drain_damage:.1f}")
    print(f"  Avg Damage/Turn: {total_all_damage/10:.1f}")
    print(f"  Peak Board Power: {peak_power:.1f}")
    print(f"  Commander Cast Turn: {commander_cast_turn if commander_cast_turn else 'Never'}")
    print(f"  Total Cards Played: {cards_played:.0f}")

    print("\n\nTurn-by-Turn Breakdown:")
    print("  Turn | Lands | Mana | Cards | Creatures | Power | Damage")
    print("  -----|-------|------|-------|-----------|-------|-------")
    for i in range(1, 11):
        lands = result.get('lands_played', [0]*11)[i]
        mana = result.get('total_mana', [0]*11)[i]
        played = result.get('cards_played', [0]*11)[i]
        # We don't have creature count, use power as proxy
        power = result.get('total_power', [0]*11)[i]
        damage = result.get('combat_damage', [0]*11)[i] + result.get('drain_damage', [0]*11)[i]
        print(f"   {i:2d}  |  {lands:3.0f}  |  {mana:3.0f} |   {played:2.0f}  |     ???   |  {power:4.0f} |  {damage:5.1f}")

    print("\n" + "="*80)
    print("[4/4] DIAGNOSIS - Root Causes of Low Damage")
    print("="*80)

    problems = []

    # Issue 1: Land count
    if len(lands) < 30:
        problems.append({
            'severity': 'CRITICAL',
            'issue': f'Insufficient Lands ({len(lands)}/~36)',
            'impact': 'Severe mana screw, cant cast spells consistently',
            'recommendation': f'Add {36-len(lands)} more lands to reach 36 total'
        })

    # Issue 2: Low damage
    if total_all_damage < 30:
        problems.append({
            'severity': 'HIGH',
            'issue': f'Very low damage output ({total_all_damage:.0f} in 10 turns)',
            'impact': 'Deck takes 30+ turns to win in goldfish',
            'recommendation': 'Add more aggressive creatures or damage dealers'
        })

    # Issue 3: Low board power
    if peak_power < 10:
        problems.append({
            'severity': 'HIGH',
            'issue': f'Weak board presence (peak power: {peak_power:.0f})',
            'impact': 'Not developing threatening board state',
            'recommendation': 'Add more creatures or increase their power/toughness'
        })

    # Issue 4: Commander cast turn
    if commander_cast_turn is None or commander_cast_turn > 6:
        turn_str = 'Never' if commander_cast_turn is None else f'turn {commander_cast_turn}'
        problems.append({
            'severity': 'MEDIUM',
            'issue': f'Commander cast very late ({turn_str})',
            'impact': 'Missing key piece of strategy',
            'recommendation': 'Check commander mana cost and add more ramp'
        })

    # Issue 5: Few cards played
    if cards_played < 10:
        problems.append({
            'severity': 'MEDIUM',
            'issue': f'Few cards played ({cards_played:.0f} in 10 turns)',
            'impact': 'Not executing game plan, likely mana starved',
            'recommendation': 'Add more lands and/or card draw'
        })

    print(f"\nFound {len(problems)} issues:\n")
    for i, p in enumerate(problems, 1):
        print(f"{i}. [{p['severity']}] {p['issue']}")
        print(f"   Impact: {p['impact']}")
        print(f"   Fix: {p['recommendation']}")
        print()

    print("="*80)
    print("SUMMARY")
    print("="*80)
    print("\nThe Teval deck is underperforming due to:")
    print("  1. Critical mana base issues (too few lands)")
    print("  2. Graveyard strategy is slow to develop")
    print("  3. Mill/reanimation doesn't produce immediate board presence")
    print("\nRecommended actions:")
    print(f"  • Increase land count from {len(lands)} to 36-37")
    print("  • Add more early-game creatures (1-3 CMC)")
    print("  • Include faster ramp (Rampant Growth, Cultivate)")
    print("  • Add more efficient threats that attack immediately")

if __name__ == "__main__":
    main()
